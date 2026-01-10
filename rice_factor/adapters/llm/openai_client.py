"""Low-level OpenAI API client with retry and error handling.

This module provides the OpenAIClient class that wraps the OpenAI SDK
with retry logic, timeout handling, and rate limit management.
Supports both OpenAI and Azure OpenAI endpoints.
"""

import contextlib
import time
from typing import Any

try:
    import openai
    from openai import (
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
    )

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from rice_factor.domain.failures.llm_errors import (
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
)


class OpenAIClientError(Exception):
    """Error raised by OpenAIClient operations."""

    pass


class OpenAIClient:
    """Low-level OpenAI API client with retry and error handling.

    Provides:
    - Retry logic with exponential backoff for transient errors
    - Rate limit handling with Retry-After header support
    - Timeout handling
    - Consistent error wrapping
    - Support for both OpenAI and Azure OpenAI endpoints

    Attributes:
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
        azure_endpoint: str | None = None,
        azure_api_version: str | None = None,
    ) -> None:
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for transient errors.
            azure_endpoint: Azure OpenAI endpoint URL (optional).
            azure_api_version: Azure OpenAI API version (optional).

        Raises:
            OpenAIClientError: If openai SDK is not installed.
        """
        if not OPENAI_AVAILABLE:
            raise OpenAIClientError(
                "openai SDK is not installed. Install with: pip install openai"
            )

        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._azure_endpoint = azure_endpoint
        self._azure_api_version = azure_api_version or "2024-02-15-preview"
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        """Get or create the OpenAI client instance.

        Returns:
            OpenAI or AzureOpenAI client instance.
        """
        if self._client is None:
            if self._azure_endpoint:
                self._client = openai.AzureOpenAI(
                    api_key=self._api_key,
                    azure_endpoint=self._azure_endpoint,
                    api_version=self._azure_api_version,
                    timeout=self._timeout,
                )
            else:
                self._client = openai.OpenAI(
                    api_key=self._api_key,
                    timeout=self._timeout,
                )
        return self._client

    @property
    def is_azure(self) -> bool:
        """Check if this client is configured for Azure OpenAI."""
        return self._azure_endpoint is not None

    def create_chat_completion(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.3,
        response_format: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a chat completion using the OpenAI API.

        Args:
            model: The model to use (e.g., gpt-4-turbo).
            messages: List of message dicts with role and content.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0 for determinism).
            top_p: Top-p sampling parameter.
            response_format: Response format (e.g., {"type": "json_object"}).

        Returns:
            Response dict with id, role, content, usage, etc.

        Raises:
            LLMTimeoutError: If request times out after retries.
            LLMRateLimitError: If rate limit is hit.
            LLMAPIError: For other API errors.
        """
        delay = self.BASE_DELAY

        for attempt in range(self._max_retries + 1):
            try:
                return self._call_api(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    response_format=response_format,
                )
            except LLMRateLimitError:
                # Don't retry rate limits - let caller handle
                raise
            except LLMTimeoutError as e:
                if attempt < self._max_retries:
                    time.sleep(delay)
                    delay = min(delay * self.BACKOFF_FACTOR, self.MAX_DELAY)
                    continue
                raise LLMTimeoutError(
                    message=f"Request timed out after {self._max_retries} retries",
                    timeout_seconds=int(self._timeout),
                ) from e
            except LLMAPIError as e:
                # Retry on 5xx errors
                if e.status_code and e.status_code >= 500 and attempt < self._max_retries:
                    time.sleep(delay)
                    delay = min(delay * self.BACKOFF_FACTOR, self.MAX_DELAY)
                    continue
                raise

        # Should not reach here, but just in case
        raise LLMAPIError(
            message="Max retries exceeded",
            status_code=None,
        )

    def _call_api(
        self,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
        top_p: float,
        response_format: dict[str, str] | None,
    ) -> dict[str, Any]:
        """Make the actual API call.

        Args:
            model: The model to use.
            messages: List of message dicts.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            top_p: Top-p sampling parameter.
            response_format: Response format option.

        Returns:
            Response dict from API.

        Raises:
            LLMTimeoutError: If request times out.
            LLMRateLimitError: If rate limit is hit.
            LLMAPIError: For other API errors.
        """
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = self.client.chat.completions.create(**kwargs)

            # Convert response to dict
            return {
                "id": response.id,
                "object": response.object,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content,
                        },
                        "finish_reason": choice.finish_reason,
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": (
                        response.usage.completion_tokens if response.usage else 0
                    ),
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
            }

        except APITimeoutError as e:
            raise LLMTimeoutError(
                message=f"OpenAI API request timed out: {e}",
                timeout_seconds=int(self._timeout),
            ) from e

        except RateLimitError as e:
            retry_after: int | None = None
            if hasattr(e, "response") and e.response is not None:
                retry_header = e.response.headers.get("retry-after")
                if retry_header:
                    with contextlib.suppress(ValueError):
                        retry_after = int(float(retry_header))

            raise LLMRateLimitError(
                message=f"OpenAI API rate limit exceeded: {e}",
                retry_after=retry_after,
            ) from e

        except APIConnectionError as e:
            raise LLMAPIError(
                message=f"OpenAI API connection error: {e}",
                status_code=None,
            ) from e

        except openai.APIStatusError as e:
            raise LLMAPIError(
                message=f"OpenAI API error: {e.message}",
                status_code=e.status_code,
            ) from e
