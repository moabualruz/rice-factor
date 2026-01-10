"""OpenAI adapter implementing the LLMPort protocol.

This module provides the OpenAIAdapter class that uses the OpenAI API
to generate structured JSON artifacts for compiler passes.
Supports both OpenAI and Azure OpenAI endpoints.
"""

import json
from typing import Any

from rice_factor.adapters.llm.openai_client import OpenAIClient, OpenAIClientError
from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.failures.llm_errors import (
    InvalidJSONError,
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from rice_factor.domain.prompts import PromptManager
from rice_factor.domain.services.json_extractor import JSONExtractor


class OpenAIAdapter:
    """Adapter for OpenAI API implementing LLMPort protocol.

    This adapter:
    - Uses PromptManager for system prompts
    - Enforces determinism via low temperature and top_p
    - Extracts JSON from responses
    - Maps API errors to domain errors
    - Supports JSON mode for structured output
    - Supports Azure OpenAI endpoints

    Attributes:
        model: The OpenAI model to use.
        temperature: Sampling temperature (capped at MAX_TEMPERATURE).
        top_p: Top-p sampling parameter (capped at MAX_TOP_P).
        is_azure: Whether using Azure OpenAI endpoint.
    """

    # Determinism constraints
    MAX_TEMPERATURE = 0.2
    MAX_TOP_P = 0.3

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4-turbo",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.3,
        timeout: float = 120.0,
        max_retries: int = 3,
        azure_endpoint: str | None = None,
        azure_api_version: str | None = None,
    ) -> None:
        """Initialize the OpenAI adapter.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            model: Model to use (default: gpt-4-turbo).
            max_tokens: Maximum tokens for response.
            temperature: Sampling temperature (capped at 0.2 for determinism).
            top_p: Top-p sampling (capped at 0.3 for determinism).
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
            azure_endpoint: Azure OpenAI endpoint URL (optional).
            azure_api_version: Azure OpenAI API version (optional).
        """
        self._model = model
        self._max_tokens = max_tokens
        # Enforce determinism constraints
        self._temperature = min(temperature, self.MAX_TEMPERATURE)
        self._top_p = min(top_p, self.MAX_TOP_P)
        self._timeout = timeout
        self._max_retries = max_retries

        self._client = OpenAIClient(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            azure_endpoint=azure_endpoint,
            azure_api_version=azure_api_version,
        )
        self._prompt_manager = PromptManager()
        self._json_extractor = JSONExtractor()

    @property
    def model(self) -> str:
        """Get the model name."""
        return self._model

    @property
    def temperature(self) -> float:
        """Get the temperature setting."""
        return self._temperature

    @property
    def top_p(self) -> float:
        """Get the top_p setting."""
        return self._top_p

    @property
    def is_azure(self) -> bool:
        """Check if this adapter is configured for Azure OpenAI."""
        return self._client.is_azure

    def generate(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> CompilerResult:
        """Generate a structured artifact using OpenAI.

        Args:
            pass_type: The type of compiler pass.
            context: Compilation context with project files and artifacts.
            schema: JSON schema for the expected output.

        Returns:
            CompilerResult with success status and payload or error.
        """
        try:
            # Build messages
            messages = self._build_messages(pass_type, context, schema)
            system_prompt = self._prompt_manager.get_system_prompt(pass_type)

            # Call OpenAI API with JSON mode
            response = self._client.create_chat_completion(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages,
                ],
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                top_p=self._top_p,
                response_format={"type": "json_object"},
            )

            # Extract text from response
            response_text = self._extract_response_text(response)

            # Extract JSON (handles code fences if present)
            json_str = self._json_extractor.extract(response_text)

            # Parse JSON
            payload = json.loads(json_str)

            # Check for LLM-signaled error
            if self._is_error_response(payload):
                return CompilerResult(
                    success=False,
                    error_type=payload.get("error_type", "llm_error"),
                    error_details=payload.get("error_message", "LLM returned error response"),
                )

            return CompilerResult(success=True, payload=payload)

        except OpenAIClientError as e:
            return CompilerResult(
                success=False,
                error_type="client_error",
                error_details=f"OpenAI client error: {e}",
            )
        except LLMTimeoutError as e:
            return CompilerResult(
                success=False,
                error_type="timeout",
                error_details=f"Request timed out: {e}",
            )
        except LLMRateLimitError as e:
            return CompilerResult(
                success=False,
                error_type="rate_limit",
                error_details=f"Rate limit exceeded: {e}",
            )
        except LLMAPIError as e:
            return CompilerResult(
                success=False,
                error_type="api_error",
                error_details=f"API error: {e}",
            )
        except InvalidJSONError as e:
            return CompilerResult(
                success=False,
                error_type="invalid_json",
                error_details=f"Failed to extract JSON: {e}",
            )
        except json.JSONDecodeError as e:
            return CompilerResult(
                success=False,
                error_type="invalid_json",
                error_details=f"Invalid JSON in response: {e}",
            )

    def _build_messages(
        self,
        pass_type: CompilerPassType,  # noqa: ARG002
        context: CompilerContext,
        schema: dict[str, object],
    ) -> list[dict[str, Any]]:
        """Build the message list for the API call.

        Args:
            pass_type: The type of compiler pass.
            context: Compilation context.
            schema: JSON schema for expected output.

        Returns:
            List of message dicts for the API.
        """
        # Build user message content
        content_parts = []

        # Add schema
        schema_json = json.dumps(schema, indent=2)
        content_parts.append(f"OUTPUT SCHEMA:\n```json\n{schema_json}\n```")

        # Add project files
        if context.project_files:
            content_parts.append("\nPROJECT FILES:")
            for path, file_content in context.project_files.items():
                content_parts.append(f"\n--- {path} ---\n{file_content}")

        # Add artifacts
        if context.artifacts:
            content_parts.append("\nARTIFACTS:")
            for artifact_id, artifact in context.artifacts.items():
                if isinstance(artifact, dict):
                    artifact_json = json.dumps(artifact, indent=2)
                else:
                    artifact_json = str(artifact)
                content_parts.append(f"\n--- {artifact_id} ---\n{artifact_json}")

        # Add target file if present
        if context.target_file:
            content_parts.append(f"\nTARGET FILE: {context.target_file}")

        # Add instructions
        content_parts.append(
            "\nGenerate a JSON artifact that conforms exactly to the schema. "
            "Output ONLY valid JSON, no explanation."
        )

        return [{"role": "user", "content": "\n".join(content_parts)}]

    def _extract_response_text(self, response: dict[str, Any]) -> str:
        """Extract text content from API response.

        Args:
            response: The API response dict.

        Returns:
            The text content from the response.

        Raises:
            LLMAPIError: If response format is unexpected.
        """
        try:
            choices = response.get("choices", [])
            if not choices:
                raise LLMAPIError(
                    message="No choices in response",
                    status_code=None,
                )
            message = choices[0].get("message", {})
            content: str | None = message.get("content")
            if content is None:
                raise LLMAPIError(
                    message="No content in response message",
                    status_code=None,
                )
            return content
        except (KeyError, IndexError, TypeError) as e:
            raise LLMAPIError(
                message=f"Unexpected response format: {e}",
                status_code=None,
            ) from e

    def _is_error_response(self, payload: dict[str, Any]) -> bool:
        """Check if the payload represents an error from the LLM.

        The LLM may signal errors in its response (e.g., missing information).

        Args:
            payload: The parsed JSON payload.

        Returns:
            True if the payload indicates an error.
        """
        return payload.get("error_type") == "missing_information"


def create_openai_adapter_from_config() -> OpenAIAdapter:
    """Create an OpenAIAdapter from application configuration.

    Reads configuration from Rice-Factor settings (dynaconf).

    Returns:
        Configured OpenAIAdapter instance.
    """
    from rice_factor.config.settings import settings

    return OpenAIAdapter(
        model=settings.get("openai.model", "gpt-4-turbo"),
        max_tokens=settings.get("llm.max_tokens", 4096),
        temperature=settings.get("llm.temperature", 0.0),
        top_p=settings.get("llm.top_p", 0.3),
        timeout=settings.get("llm.timeout", 120.0),
        max_retries=settings.get("llm.max_retries", 3),
        azure_endpoint=settings.get("azure.openai_endpoint", None),
        azure_api_version=settings.get("azure.openai_api_version", None),
    )
