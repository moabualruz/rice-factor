"""Claude LLM adapter implementing LLMPort.

This module provides the ClaudeAdapter class that implements the LLMPort
protocol for generating artifacts using Claude (Anthropic API).
"""

import json
from typing import Any

from rice_factor.adapters.llm.claude_client import ClaudeClient, ClaudeClientError
from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.failures.llm_errors import (
    LLMAPIError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from rice_factor.domain.prompts import PromptManager
from rice_factor.domain.services.json_extractor import JSONExtractor


class ClaudeAdapter:
    """Claude LLM adapter implementing LLMPort protocol.

    This adapter translates Rice-Factor compilation requests into Claude
    API calls and processes the responses into structured artifacts.

    Enforces determinism controls:
    - Temperature: 0.0-0.2
    - Top-p: <= 0.3
    - No streaming

    Attributes:
        model: The Claude model to use.
        max_tokens: Maximum tokens per response.
        temperature: Temperature for generation.
        top_p: Top-p sampling parameter.
    """

    # Determinism limits
    MAX_TEMPERATURE = 0.2
    MAX_TOP_P = 0.3

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.3,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the Claude adapter.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
            model: Claude model identifier.
            max_tokens: Maximum tokens in response.
            temperature: Temperature for generation (capped at 0.2).
            top_p: Top-p sampling (capped at 0.3).
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.

        Raises:
            ClaudeClientError: If anthropic SDK is not available.
        """
        # Enforce determinism limits
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = min(temperature, self.MAX_TEMPERATURE)
        self._top_p = min(top_p, self.MAX_TOP_P)

        self._client = ClaudeClient(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._prompt_manager = PromptManager()
        self._json_extractor = JSONExtractor()

    @property
    def model(self) -> str:
        """Return the model identifier."""
        return self._model

    @property
    def temperature(self) -> float:
        """Return the temperature setting."""
        return self._temperature

    @property
    def top_p(self) -> float:
        """Return the top-p setting."""
        return self._top_p

    def generate(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> CompilerResult:
        """Generate an artifact using Claude.

        Args:
            pass_type: The compiler pass type.
            context: The compilation context.
            schema: JSON Schema for the expected output.

        Returns:
            CompilerResult with payload on success or error details on failure.
        """
        try:
            # Build messages
            messages = self._build_messages(pass_type, context, schema)

            # Get system prompt
            system_prompt = self._prompt_manager.get_system_prompt(pass_type)

            # Call Claude API
            response = self._client.create_message(
                model=self._model,
                messages=messages,
                system=system_prompt,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                top_p=self._top_p,
            )

            # Extract response text
            response_text = self._extract_response_text(response)

            # Extract JSON from response
            json_str = self._json_extractor.extract(response_text)

            # Parse JSON
            payload = json.loads(json_str)

            # Check for explicit error response from LLM
            if self._is_error_response(payload):
                return CompilerResult(
                    success=False,
                    error_type=payload.get("error", "llm_error"),
                    error_details=payload.get("details", "LLM returned error response"),
                )

            return CompilerResult(success=True, payload=payload)

        except (LLMAPIError, LLMTimeoutError, LLMRateLimitError):
            # Re-raise LLM-specific errors
            raise

        except json.JSONDecodeError as e:
            return CompilerResult(
                success=False,
                error_type="invalid_json",
                error_details=f"Failed to parse JSON from response: {e}",
            )

        except LLMError as e:
            return CompilerResult(
                success=False,
                error_type=e.__class__.__name__,
                error_details=str(e),
            )

        except ClaudeClientError as e:
            return CompilerResult(
                success=False,
                error_type="client_error",
                error_details=str(e),
            )

        except Exception as e:
            return CompilerResult(
                success=False,
                error_type="unexpected_error",
                error_details=f"Unexpected error: {e}",
            )

    def _build_messages(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> list[dict[str, Any]]:
        """Build the message list for Claude API.

        Args:
            pass_type: The compiler pass type.
            context: The compilation context.
            schema: JSON Schema for the expected output.

        Returns:
            List of message dicts with "role" and "content".
        """
        # Get the full prompt with schema injection
        user_prompt = self._prompt_manager.get_full_prompt(
            pass_type, context, include_schema=True
        )

        # Add schema details if not already included
        schema_json = json.dumps(schema, indent=2)
        if "JSON SCHEMA" not in user_prompt:
            user_prompt += f"\n\n## Required Output Schema\n\n```json\n{schema_json}\n```"

        return [{"role": "user", "content": user_prompt}]

    def _extract_response_text(self, response: dict[str, Any]) -> str:
        """Extract the text content from Claude response.

        Args:
            response: The Claude API response dict.

        Returns:
            The text content from the response.

        Raises:
            ValueError: If no text content found.
        """
        content = response.get("content", [])
        for block in content:
            if block.get("type") == "text" and "text" in block:
                text: str = block["text"]
                return text

        raise ValueError("No text content in Claude response")

    def _is_error_response(self, payload: dict[str, Any]) -> bool:
        """Check if the payload is an error response from the LLM.

        Args:
            payload: The parsed JSON payload.

        Returns:
            True if this is an error response.
        """
        # Check for explicit error field
        if "error" in payload:
            return True

        # Check for missing_information pattern
        return payload.get("error_type") == "missing_information"


def create_claude_adapter_from_config() -> ClaudeAdapter:
    """Create a ClaudeAdapter from application configuration.

    Reads configuration from Rice-Factor settings (dynaconf).

    Returns:
        Configured ClaudeAdapter instance.
    """
    from rice_factor.config.settings import settings

    return ClaudeAdapter(
        model=settings.get("llm.model", "claude-3-5-sonnet-20241022"),
        max_tokens=settings.get("llm.max_tokens", 4096),
        temperature=settings.get("llm.temperature", 0.0),
        top_p=settings.get("llm.top_p", 0.3),
        timeout=settings.get("llm.timeout", 120.0),
        max_retries=settings.get("llm.max_retries", 3),
    )
