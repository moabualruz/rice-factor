"""Ollama LLM adapter implementing LLMPort.

This module provides the OllamaAdapter class that implements the LLMPort
protocol for generating artifacts using Ollama local LLM server.

Ollama is a simple local LLM deployment tool that provides a REST API
at localhost:11434 for model inference.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.failures.llm_errors import (
    LLMAPIError,
    LLMError,
    LLMTimeoutError,
)
from rice_factor.domain.prompts import PromptManager
from rice_factor.domain.services.json_extractor import JSONExtractor

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class OllamaClientError(Exception):
    """Exception raised when Ollama client operations fail."""

    pass


class OllamaClient:
    """HTTP client for Ollama REST API.

    Uses httpx for async HTTP operations. Falls back to requests for sync
    operations if httpx is not available.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        """Initialize the Ollama client.

        Args:
            base_url: Base URL of the Ollama server.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._httpx_available = self._check_httpx()

    def _check_httpx(self) -> bool:
        """Check if httpx is available."""
        try:
            import httpx  # noqa: F401

            return True
        except ImportError:
            return False

    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Generate completion from Ollama.

        Args:
            model: Model name (e.g., "codestral", "llama3.2").
            prompt: The prompt to send.
            temperature: Temperature for generation.
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream responses (not supported in sync mode).

        Returns:
            Response dict with 'response' key containing generated text.

        Raises:
            OllamaClientError: If request fails.
            LLMTimeoutError: If request times out.
        """
        if stream:
            raise OllamaClientError("Streaming not supported in synchronous mode")

        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        if self._httpx_available:
            return self._generate_httpx(payload)
        else:
            return self._generate_requests(payload)

    def _generate_httpx(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate using httpx."""
        import httpx

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Ollama request timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            raise OllamaClientError(f"Ollama API error: {e}") from e
        except httpx.RequestError as e:
            raise OllamaClientError(f"Ollama request failed: {e}") from e

    def _generate_requests(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate using requests (fallback)."""
        try:
            import requests
        except ImportError as e:
            raise OllamaClientError(
                "Neither httpx nor requests is available. "
                "Install with: pip install httpx"
            ) from e

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except requests.Timeout as e:
            raise LLMTimeoutError(f"Ollama request timed out: {e}") from e
        except requests.RequestException as e:
            raise OllamaClientError(f"Ollama request failed: {e}") from e

    async def generate_async(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[str]:
        """Generate completion from Ollama asynchronously.

        Args:
            model: Model name.
            prompt: The prompt to send.
            temperature: Temperature for generation.
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream responses.

        Returns:
            Response dict or async iterator of response chunks.

        Raises:
            OllamaClientError: If httpx is not available or request fails.
        """
        if not self._httpx_available:
            raise OllamaClientError(
                "Async mode requires httpx. Install with: pip install httpx"
            )

        import httpx

        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": stream,
        }

        if stream:
            return self._stream_response_async(payload)
        else:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload,
                    )
                    response.raise_for_status()
                    result: dict[str, Any] = response.json()
                    return result
            except httpx.TimeoutException as e:
                raise LLMTimeoutError(f"Ollama request timed out: {e}") from e
            except httpx.HTTPStatusError as e:
                raise OllamaClientError(f"Ollama API error: {e}") from e
            except httpx.RequestError as e:
                raise OllamaClientError(f"Ollama request failed: {e}") from e

    async def _stream_response_async(
        self, payload: dict[str, Any]
    ) -> AsyncIterator[str]:
        """Stream response from Ollama asynchronously.

        Args:
            payload: Request payload.

        Yields:
            Response chunks as strings.
        """
        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client, client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue

    def list_models(self) -> list[str]:
        """List available models on Ollama server.

        Returns:
            List of model names.

        Raises:
            OllamaClientError: If request fails.
        """
        if self._httpx_available:
            import httpx

            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{self.base_url}/api/tags")
                    response.raise_for_status()
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
            except httpx.RequestError as e:
                raise OllamaClientError(f"Failed to list models: {e}") from e
        else:
            try:
                import requests

                response = requests.get(
                    f"{self.base_url}/api/tags",
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            except Exception as e:
                raise OllamaClientError(f"Failed to list models: {e}") from e

    def is_available(self) -> bool:
        """Check if Ollama server is running and accessible.

        Returns:
            True if Ollama is available, False otherwise.
        """
        if self._httpx_available:
            import httpx

            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"{self.base_url}/")
                    return bool(response.status_code == 200)
            except httpx.RequestError:
                return False
        else:
            try:
                import requests

                response = requests.get(
                    f"{self.base_url}/",
                    timeout=5.0,
                )
                return bool(response.status_code == 200)
            except Exception:
                return False

    async def is_available_async(self) -> bool:
        """Check if Ollama server is running and accessible (async).

        Returns:
            True if Ollama is available, False otherwise.
        """
        if not self._httpx_available:
            return self.is_available()

        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/")
                return bool(response.status_code == 200)
        except httpx.RequestError:
            return False


class OllamaAdapter:
    """Ollama LLM adapter implementing LLMPort protocol.

    This adapter translates Rice-Factor compilation requests into Ollama
    API calls and processes the responses into structured artifacts.

    Enforces determinism controls:
    - Temperature: 0.0-0.2
    - No streaming for deterministic output

    Attributes:
        model: The Ollama model to use.
        max_tokens: Maximum tokens per response.
        temperature: Temperature for generation.
    """

    # Determinism limits
    MAX_TEMPERATURE = 0.2

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        *,
        model: str = "codestral",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        timeout: float = 120.0,
    ) -> None:
        """Initialize the Ollama adapter.

        Args:
            base_url: Ollama server URL (default: http://localhost:11434).
            model: Ollama model identifier (e.g., "codestral", "llama3.2").
            max_tokens: Maximum tokens in response.
            temperature: Temperature for generation (capped at 0.2).
            timeout: Request timeout in seconds.
        """
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = min(temperature, self.MAX_TEMPERATURE)
        self._timeout = timeout

        self._client = OllamaClient(
            base_url=base_url,
            timeout=timeout,
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
    def base_url(self) -> str:
        """Return the Ollama server URL."""
        return self._client.base_url

    def generate(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> CompilerResult:
        """Generate an artifact using Ollama.

        Args:
            pass_type: The compiler pass type.
            context: The compilation context.
            schema: JSON Schema for the expected output.

        Returns:
            CompilerResult with payload on success or error details on failure.
        """
        try:
            # Build prompt
            user_prompt = self._build_prompt(pass_type, context, schema)

            # Get system prompt
            system_prompt = self._prompt_manager.get_system_prompt(pass_type)

            # Combine system and user prompts for Ollama
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Call Ollama API
            response = self._client.generate(
                model=self._model,
                prompt=full_prompt,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )

            # Extract response text
            response_text = response.get("response", "")

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

        except LLMTimeoutError:
            raise

        except LLMAPIError:
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

        except OllamaClientError as e:
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

    def _build_prompt(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> str:
        """Build the prompt for Ollama.

        Args:
            pass_type: The compiler pass type.
            context: The compilation context.
            schema: JSON Schema for the expected output.

        Returns:
            Full prompt string.
        """
        # Get the full prompt with schema injection
        user_prompt = self._prompt_manager.get_full_prompt(
            pass_type, context, include_schema=True
        )

        # Add schema details if not already included
        schema_json = json.dumps(schema, indent=2)
        if "JSON SCHEMA" not in user_prompt:
            user_prompt += f"\n\n## Required Output Schema\n\n```json\n{schema_json}\n```"

        return user_prompt

    def _is_error_response(self, payload: dict[str, Any]) -> bool:
        """Check if the payload is an error response from the LLM.

        Args:
            payload: The parsed JSON payload.

        Returns:
            True if this is an error response.
        """
        if "error" in payload:
            return True
        return payload.get("error_type") == "missing_information"

    def list_models(self) -> list[str]:
        """List available models on the Ollama server.

        Returns:
            List of model names.
        """
        return self._client.list_models()

    def is_available(self) -> bool:
        """Check if Ollama server is running and accessible.

        Returns:
            True if Ollama is available, False otherwise.
        """
        return self._client.is_available()


def create_ollama_adapter_from_config() -> OllamaAdapter:
    """Create an OllamaAdapter from application configuration.

    Reads configuration from Rice-Factor settings (dynaconf).

    Returns:
        Configured OllamaAdapter instance.
    """
    from rice_factor.config.settings import settings

    return OllamaAdapter(
        base_url=settings.get("llm.ollama.base_url", "http://localhost:11434"),
        model=settings.get("llm.ollama.model", "codestral"),
        max_tokens=settings.get("llm.ollama.max_tokens", 4096),
        temperature=settings.get("llm.ollama.temperature", 0.0),
        timeout=settings.get("llm.ollama.timeout", 120.0),
    )
