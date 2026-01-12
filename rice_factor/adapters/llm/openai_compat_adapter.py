"""Generic OpenAI-Compatible LLM adapter implementing LLMPort.

This module provides the OpenAICompatAdapter class that implements the LLMPort
protocol for any server that exposes an OpenAI-compatible API.

Supports:
- LocalAI (http://localhost:8080/v1)
- LM Studio (http://localhost:1234/v1)
- Text Generation Inference (http://localhost:8080/v1)
- Any other OpenAI-compatible endpoint
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


class OpenAICompatClientError(Exception):
    """Exception raised when OpenAI-compatible client operations fail."""

    pass


# Known provider configurations
KNOWN_PROVIDERS = {
    "localai": {
        "default_url": "http://localhost:8080/v1",
        "default_model": "gpt-3.5-turbo",
        "supports_chat": True,
        "supports_completions": True,
    },
    "lmstudio": {
        "default_url": "http://localhost:1234/v1",
        "default_model": "local-model",
        "supports_chat": True,
        "supports_completions": True,
    },
    "tgi": {
        "default_url": "http://localhost:8080/v1",
        "default_model": "tgi",
        "supports_chat": True,
        "supports_completions": False,
    },
    "generic": {
        "default_url": "http://localhost:8000/v1",
        "default_model": "default",
        "supports_chat": True,
        "supports_completions": True,
    },
}


class OpenAICompatClient:
    """HTTP client for OpenAI-compatible APIs.

    Works with any server that implements the OpenAI API specification.
    Uses httpx for async HTTP operations.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080/v1",
        api_key: str = "EMPTY",
        timeout: float = 120.0,
        provider: str = "generic",
    ) -> None:
        """Initialize the OpenAI-compatible client.

        Args:
            base_url: Base URL of the API server.
            api_key: API key (often not required for local servers).
            timeout: Request timeout in seconds.
            provider: Provider hint for configuration (localai, lmstudio, tgi, generic).
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.provider = provider
        self._httpx_available = self._check_httpx()

        # Get provider config
        self._provider_config = KNOWN_PROVIDERS.get(
            provider.lower(), KNOWN_PROVIDERS["generic"]
        )

    def _check_httpx(self) -> bool:
        """Check if httpx is available."""
        try:
            import httpx  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "EMPTY":
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @property
    def supports_chat(self) -> bool:
        """Check if this provider supports the chat completions API."""
        return bool(self._provider_config.get("supports_chat", True))

    @property
    def supports_completions(self) -> bool:
        """Check if this provider supports the completions API."""
        return bool(self._provider_config.get("supports_completions", True))

    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
        use_chat: bool | None = None,
    ) -> dict[str, Any]:
        """Generate completion from the API.

        Args:
            model: Model name.
            prompt: The prompt to send.
            temperature: Temperature for generation.
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream responses (not supported in sync mode).
            use_chat: Force chat or completion API. Auto-selects if None.

        Returns:
            Response dict with generated text.

        Raises:
            OpenAICompatClientError: If request fails.
            LLMTimeoutError: If request times out.
        """
        if stream:
            raise OpenAICompatClientError("Streaming not supported in synchronous mode")

        # Auto-select API based on provider capabilities
        if use_chat is None:
            use_chat = self.supports_chat

        if use_chat:
            return self._generate_chat(model, prompt, temperature, max_tokens)
        else:
            return self._generate_completion(model, prompt, temperature, max_tokens)

    def _generate_completion(
        self,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Generate using the completions API."""
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if self._httpx_available:
            return self._post_httpx("/completions", payload)
        else:
            return self._post_requests("/completions", payload)

    def _generate_chat(
        self,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Generate using the chat completions API."""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if self._httpx_available:
            return self._post_httpx("/chat/completions", payload)
        else:
            return self._post_requests("/chat/completions", payload)

    def _post_httpx(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST using httpx."""
        import httpx

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}{endpoint}",
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Request timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            raise OpenAICompatClientError(f"API error: {e}") from e
        except httpx.RequestError as e:
            raise OpenAICompatClientError(f"Request failed: {e}") from e

    def _post_requests(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST using requests (fallback)."""
        try:
            import requests
        except ImportError as e:
            raise OpenAICompatClientError(
                "Neither httpx nor requests is available. "
                "Install with: pip install httpx"
            ) from e

        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except requests.Timeout as e:
            raise LLMTimeoutError(f"Request timed out: {e}") from e
        except requests.RequestException as e:
            raise OpenAICompatClientError(f"Request failed: {e}") from e

    async def generate_async(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
        use_chat: bool | None = None,
    ) -> dict[str, Any] | AsyncIterator[str]:
        """Generate completion asynchronously.

        Args:
            model: Model name.
            prompt: The prompt to send.
            temperature: Temperature for generation.
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream responses.
            use_chat: Force chat or completion API. Auto-selects if None.

        Returns:
            Response dict or async iterator of response chunks.
        """
        if not self._httpx_available:
            raise OpenAICompatClientError(
                "Async mode requires httpx. Install with: pip install httpx"
            )

        if use_chat is None:
            use_chat = self.supports_chat

        import httpx

        if use_chat:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            }
            endpoint = "/chat/completions"
        else:
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            }
            endpoint = "/completions"

        if stream:
            return self._stream_response_async(endpoint, payload, use_chat)
        else:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        headers=self._get_headers(),
                        json=payload,
                    )
                    response.raise_for_status()
                    result: dict[str, Any] = response.json()
                    return result
            except httpx.TimeoutException as e:
                raise LLMTimeoutError(f"Request timed out: {e}") from e
            except httpx.HTTPStatusError as e:
                raise OpenAICompatClientError(f"API error: {e}") from e
            except httpx.RequestError as e:
                raise OpenAICompatClientError(f"Request failed: {e}") from e

    async def _stream_response_async(
        self,
        endpoint: str,
        payload: dict[str, Any],
        is_chat: bool,
    ) -> AsyncIterator[str]:
        """Stream response asynchronously.

        Args:
            endpoint: API endpoint.
            payload: Request payload.
            is_chat: Whether using chat completions API.

        Yields:
            Response chunks as strings.
        """
        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client, client.stream(
            "POST",
            f"{self.base_url}{endpoint}",
            headers=self._get_headers(),
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            if is_chat:
                                # Chat completions format
                                delta = choices[0].get("delta", {})
                                text = delta.get("content", "")
                            else:
                                # Completions format
                                text = choices[0].get("text", "")
                            if text:
                                yield text
                    except json.JSONDecodeError:
                        continue

    def list_models(self) -> list[str]:
        """List available models on the server.

        Returns:
            List of model names.

        Raises:
            OpenAICompatClientError: If request fails.
        """
        if self._httpx_available:
            import httpx

            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(
                        f"{self.base_url}/models",
                        headers=self._get_headers(),
                    )
                    response.raise_for_status()
                    data = response.json()
                    return [m["id"] for m in data.get("data", [])]
            except httpx.RequestError as e:
                raise OpenAICompatClientError(f"Failed to list models: {e}") from e
        else:
            try:
                import requests

                response = requests.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers(),
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                return [m["id"] for m in data.get("data", [])]
            except Exception as e:
                raise OpenAICompatClientError(f"Failed to list models: {e}") from e

    def is_available(self) -> bool:
        """Check if server is running and accessible.

        Returns:
            True if server is available, False otherwise.
        """
        if self._httpx_available:
            import httpx

            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(
                        f"{self.base_url}/models",
                        headers=self._get_headers(),
                    )
                    return bool(response.status_code == 200)
            except httpx.RequestError:
                return False
        else:
            try:
                import requests

                response = requests.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers(),
                    timeout=5.0,
                )
                return bool(response.status_code == 200)
            except Exception:
                return False

    async def is_available_async(self) -> bool:
        """Check if server is running and accessible (async).

        Returns:
            True if server is available, False otherwise.
        """
        if not self._httpx_available:
            return self.is_available()

        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers(),
                )
                return bool(response.status_code == 200)
        except httpx.RequestError:
            return False


class OpenAICompatAdapter:
    """Generic OpenAI-compatible LLM adapter implementing LLMPort protocol.

    This adapter works with any server that implements the OpenAI API,
    including LocalAI, LM Studio, Text Generation Inference, etc.

    Enforces determinism controls:
    - Temperature: 0.0-0.2

    Attributes:
        model: The model to use.
        max_tokens: Maximum tokens per response.
        temperature: Temperature for generation.
        provider: Provider type (localai, lmstudio, tgi, generic).
    """

    # Determinism limits
    MAX_TEMPERATURE = 0.2

    def __init__(
        self,
        base_url: str = "http://localhost:8080/v1",
        *,
        model: str | None = None,
        api_key: str = "EMPTY",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        timeout: float = 120.0,
        provider: str = "generic",
    ) -> None:
        """Initialize the OpenAI-compatible adapter.

        Args:
            base_url: API server URL.
            model: Model identifier (auto-detects from provider if None).
            api_key: API key (often not required for local servers).
            max_tokens: Maximum tokens in response.
            temperature: Temperature for generation (capped at 0.2).
            timeout: Request timeout in seconds.
            provider: Provider type hint (localai, lmstudio, tgi, generic).
        """
        provider_config = KNOWN_PROVIDERS.get(provider.lower(), KNOWN_PROVIDERS["generic"])
        self._model = model or str(provider_config.get("default_model", "default"))
        self._max_tokens = max_tokens
        self._temperature = min(temperature, self.MAX_TEMPERATURE)
        self._timeout = timeout
        self._provider = provider

        self._client = OpenAICompatClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            provider=provider,
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
        """Return the server URL."""
        return self._client.base_url

    @property
    def provider(self) -> str:
        """Return the provider type."""
        return self._provider

    def generate(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> CompilerResult:
        """Generate an artifact using the OpenAI-compatible API.

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

            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Call API
            response = self._client.generate(
                model=self._model,
                prompt=full_prompt,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
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

        except OpenAICompatClientError as e:
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
        """Build the prompt.

        Args:
            pass_type: The compiler pass type.
            context: The compilation context.
            schema: JSON Schema for the expected output.

        Returns:
            Full prompt string.
        """
        user_prompt = self._prompt_manager.get_full_prompt(
            pass_type, context, include_schema=True
        )

        schema_json = json.dumps(schema, indent=2)
        if "JSON SCHEMA" not in user_prompt:
            user_prompt += f"\n\n## Required Output Schema\n\n```json\n{schema_json}\n```"

        return user_prompt

    def _extract_response_text(self, response: dict[str, Any]) -> str:
        """Extract the text content from response.

        Args:
            response: The API response dict.

        Returns:
            The text content from the response.

        Raises:
            ValueError: If no text content found.
        """
        choices = response.get("choices", [])
        if choices:
            # Completion API format
            if "text" in choices[0]:
                return str(choices[0]["text"])
            # Chat completion API format
            if "message" in choices[0]:
                return str(choices[0]["message"].get("content", ""))

        raise ValueError("No text content in response")

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
        """List available models on the server.

        Returns:
            List of model names.
        """
        return self._client.list_models()

    def is_available(self) -> bool:
        """Check if server is running and accessible.

        Returns:
            True if server is available, False otherwise.
        """
        return self._client.is_available()


def create_openai_compat_adapter_from_config() -> OpenAICompatAdapter:
    """Create an OpenAICompatAdapter from application configuration.

    Reads configuration from Rice-Factor settings (dynaconf).

    Returns:
        Configured OpenAICompatAdapter instance.
    """
    from rice_factor.config.settings import settings

    return OpenAICompatAdapter(
        base_url=settings.get("llm.openai_compat.base_url", "http://localhost:8080/v1"),
        model=settings.get("llm.openai_compat.model"),  # None = auto-detect
        api_key=settings.get("llm.openai_compat.api_key", "EMPTY"),
        max_tokens=settings.get("llm.openai_compat.max_tokens", 4096),
        temperature=settings.get("llm.openai_compat.temperature", 0.0),
        timeout=settings.get("llm.openai_compat.timeout", 120.0),
        provider=settings.get("llm.openai_compat.provider", "generic"),
    )
