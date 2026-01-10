"""Low-level Claude API client with retry and error handling.

This module provides the ClaudeClient class that wraps the Anthropic SDK
with retry logic, timeout handling, and rate limit management.
"""

import contextlib
import time
from typing import Any

try:
    import anthropic
    from anthropic import (
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
    )

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from rice_factor.domain.failures.llm_errors import (
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
)


class ClaudeClientError(Exception):
    """Error raised by ClaudeClient operations."""

    pass


class ClaudeClient:
    """Low-level Claude API client with retry and error handling.

    Provides:
    - Retry logic with exponential backoff for transient errors
    - Rate limit handling with Retry-After header support
    - Timeout handling
    - Consistent error wrapping

    Attributes:
        model: The Claude model to use.
        max_retries: Maximum number of retry attempts.
        timeout: Request timeout in seconds.
    """

    # Retry configuration
    BASE_DELAY = 1.0  # Starting delay in seconds
    MAX_DELAY = 16.0  # Maximum delay between retries
    BACKOFF_FACTOR = 2.0  # Exponential backoff multiplier

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the Claude client.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.

        Raises:
            ClaudeClientError: If anthropic SDK is not installed.
        """
        if not ANTHROPIC_AVAILABLE:
            raise ClaudeClientError(
                "anthropic SDK is not installed. "
                "Install with: pip install anthropic"
            )

        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> "anthropic.Anthropic":
        """Get or create the Anthropic client instance.

        Returns:
            Anthropic client instance.

        Raises:
            ClaudeClientError: If client cannot be created.
        """
        if self._client is None:
            try:
                self._client = anthropic.Anthropic(
                    api_key=self._api_key,
                    timeout=self._timeout,
                )
            except Exception as e:
                raise ClaudeClientError(f"Failed to create Anthropic client: {e}") from e
        return self._client

    def create_message(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.3,
    ) -> dict[str, Any]:
        """Create a message using the Claude API with retry logic.

        Args:
            model: The model to use (e.g., "claude-3-5-sonnet-20241022").
            messages: List of message dicts with "role" and "content".
            system: Optional system message.
            max_tokens: Maximum tokens in response.
            temperature: Temperature for generation (0.0-0.2 for determinism).
            top_p: Top-p sampling (<=0.3 for determinism).

        Returns:
            The API response as a dictionary.

        Raises:
            LLMAPIError: On API errors after retries exhausted.
            LLMTimeoutError: On timeout after retries exhausted.
            LLMRateLimitError: On rate limit (includes retry_after if available).
        """
        last_error: Exception | None = None
        delay = self.BASE_DELAY

        for attempt in range(self._max_retries + 1):
            try:
                return self._call_api(
                    model=model,
                    messages=messages,
                    system=system,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                )
            except LLMRateLimitError:
                # Don't retry rate limits, let caller handle
                raise
            except LLMTimeoutError as e:
                last_error = e
                if attempt < self._max_retries:
                    time.sleep(delay)
                    delay = min(delay * self.BACKOFF_FACTOR, self.MAX_DELAY)
            except LLMAPIError as e:
                # Only retry on 5xx errors (server errors)
                if e.status_code is not None and e.status_code >= 500:
                    last_error = e
                    if attempt < self._max_retries:
                        time.sleep(delay)
                        delay = min(delay * self.BACKOFF_FACTOR, self.MAX_DELAY)
                else:
                    # 4xx errors are not retryable
                    raise

        # All retries exhausted
        if last_error is not None:
            raise last_error
        raise LLMAPIError("Unknown error after retries", provider="anthropic")

    def _call_api(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.3,
    ) -> dict[str, Any]:
        """Make a single API call without retry logic.

        Args:
            model: The model to use.
            messages: List of message dicts.
            system: Optional system message.
            max_tokens: Maximum tokens in response.
            temperature: Temperature for generation.
            top_p: Top-p sampling.

        Returns:
            The API response as a dictionary.

        Raises:
            LLMAPIError: On API errors.
            LLMTimeoutError: On timeout.
            LLMRateLimitError: On rate limit.
        """
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }
            if system:
                kwargs["system"] = system

            response = self.client.messages.create(**kwargs)

            # Convert response to dict
            return {
                "id": response.id,
                "type": response.type,
                "role": response.role,
                "content": [
                    {"type": block.type, "text": block.text}
                    for block in response.content
                    if hasattr(block, "text")
                ],
                "model": response.model,
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            }

        except APITimeoutError as e:
            raise LLMTimeoutError(
                f"Claude API timeout after {self._timeout}s",
                timeout_seconds=int(self._timeout),
            ) from e

        except RateLimitError as e:
            # Try to extract retry_after from response headers
            retry_after: int | None = None
            if hasattr(e, "response") and e.response is not None:
                retry_header = e.response.headers.get("retry-after")
                if retry_header:
                    with contextlib.suppress(ValueError):
                        retry_after = int(float(retry_header))

            raise LLMRateLimitError(
                "Claude API rate limit exceeded",
                retry_after=retry_after,
                provider="anthropic",
            ) from e

        except APIConnectionError as e:
            raise LLMAPIError(
                f"Claude API connection error: {e}",
                provider="anthropic",
            ) from e

        except anthropic.APIStatusError as e:
            raise LLMAPIError(
                f"Claude API error: {e.message}",
                status_code=e.status_code,
                provider="anthropic",
            ) from e

        except Exception as e:
            raise LLMAPIError(
                f"Unexpected Claude API error: {e}",
                provider="anthropic",
            ) from e
