"""vLLM LLM adapter implementing LLMPort.

This module provides the VLLMAdapter class that implements the LLMPort
protocol for generating artifacts using vLLM server.

vLLM is a high-throughput LLM serving framework that provides an
OpenAI-compatible API for model inference.
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


class VLLMClientError(Exception):
    """Exception raised when vLLM client operations fail."""

    pass


class VLLMClient:
    """HTTP client for vLLM OpenAI-compatible API.

    vLLM serves an OpenAI-compatible API at /v1 by default.
    Uses httpx for async HTTP operations.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "EMPTY",
        timeout: float = 120.0,
    ) -> None:
        """Initialize the vLLM client.

        Args:
            base_url: Base URL of the vLLM server (e.g., http://localhost:8000/v1).
            api_key: API key (vLLM doesn't require one by default, use "EMPTY").
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._httpx_available = self._check_httpx()

    def _check_httpx(self) -> bool:
        """Check if httpx is available."""
        try:
            import httpx  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Generate completion from vLLM.

        Uses the /completions endpoint (OpenAI-compatible).

        Args:
            model: Model name served by vLLM.
            prompt: The prompt to send.
            temperature: Temperature for generation.
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream responses (not supported in sync mode).

        Returns:
            Response dict with generated text.

        Raises:
            VLLMClientError: If request fails.
            LLMTimeoutError: If request times out.
        """
        if stream:
            raise VLLMClientError("Streaming not supported in synchronous mode")

        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
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
                    f"{self.base_url}/completions",
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"vLLM request timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            raise VLLMClientError(f"vLLM API error: {e}") from e
        except httpx.RequestError as e:
            raise VLLMClientError(f"vLLM request failed: {e}") from e

    def _generate_requests(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate using requests (fallback)."""
        try:
            import requests
        except ImportError as e:
            raise VLLMClientError(
                "Neither httpx nor requests is available. "
                "Install with: pip install httpx"
            ) from e

        try:
            response = requests.post(
                f"{self.base_url}/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except requests.Timeout as e:
            raise LLMTimeoutError(f"vLLM request timed out: {e}") from e
        except requests.RequestException as e:
            raise VLLMClientError(f"vLLM request failed: {e}") from e

    def generate_chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Generate chat completion from vLLM.

        Uses the /chat/completions endpoint (OpenAI-compatible).

        Args:
            model: Model name served by vLLM.
            messages: List of message dicts with "role" and "content".
            temperature: Temperature for generation.
            max_tokens: Maximum tokens to generate.

        Returns:
            Response dict with generated text.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if self._httpx_available:
            import httpx

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._get_headers(),
                        json=payload,
                    )
                    response.raise_for_status()
                    result: dict[str, Any] = response.json()
                    return result
            except httpx.TimeoutException as e:
                raise LLMTimeoutError(f"vLLM request timed out: {e}") from e
            except httpx.HTTPStatusError as e:
                raise VLLMClientError(f"vLLM API error: {e}") from e
            except httpx.RequestError as e:
                raise VLLMClientError(f"vLLM request failed: {e}") from e
        else:
            import requests

            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                result = response.json()
                return result
            except requests.Timeout as e:
                raise LLMTimeoutError(f"vLLM request timed out: {e}") from e
            except requests.RequestException as e:
                raise VLLMClientError(f"vLLM request failed: {e}") from e

    async def generate_async(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[str]:
        """Generate completion from vLLM asynchronously.

        Args:
            model: Model name.
            prompt: The prompt to send.
            temperature: Temperature for generation.
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream responses.

        Returns:
            Response dict or async iterator of response chunks.
        """
        if not self._httpx_available:
            raise VLLMClientError(
                "Async mode requires httpx. Install with: pip install httpx"
            )

        import httpx

        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if stream:
            return self._stream_response_async(payload)
        else:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/completions",
                        headers=self._get_headers(),
                        json=payload,
                    )
                    response.raise_for_status()
                    result: dict[str, Any] = response.json()
                    return result
            except httpx.TimeoutException as e:
                raise LLMTimeoutError(f"vLLM request timed out: {e}") from e
            except httpx.HTTPStatusError as e:
                raise VLLMClientError(f"vLLM API error: {e}") from e
            except httpx.RequestError as e:
                raise VLLMClientError(f"vLLM request failed: {e}") from e

    async def _stream_response_async(
        self, payload: dict[str, Any]
    ) -> AsyncIterator[str]:
        """Stream response from vLLM asynchronously.

        Args:
            payload: Request payload.

        Yields:
            Response chunks as strings.
        """
        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client, client.stream(
            "POST",
            f"{self.base_url}/completions",
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
                        if data.get("choices"):
                            text = data["choices"][0].get("text", "")
                            if text:
                                yield text
                    except json.JSONDecodeError:
                        continue

    def list_models(self) -> list[str]:
        """List available models on vLLM server.

        Returns:
            List of model names.

        Raises:
            VLLMClientError: If request fails.
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
                raise VLLMClientError(f"Failed to list models: {e}") from e
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
                raise VLLMClientError(f"Failed to list models: {e}") from e

    def is_available(self) -> bool:
        """Check if vLLM server is running and accessible.

        Returns:
            True if vLLM is available, False otherwise.
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
        """Check if vLLM server is running and accessible (async).

        Returns:
            True if vLLM is available, False otherwise.
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


class VLLMAdapter:
    """vLLM LLM adapter implementing LLMPort protocol.

    This adapter translates Rice-Factor compilation requests into vLLM
    API calls and processes the responses into structured artifacts.

    vLLM uses an OpenAI-compatible API, making it straightforward to
    integrate with production deployments.

    Enforces determinism controls:
    - Temperature: 0.0-0.2

    Attributes:
        model: The vLLM model to use.
        max_tokens: Maximum tokens per response.
        temperature: Temperature for generation.
    """

    # Determinism limits
    MAX_TEMPERATURE = 0.2

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        *,
        model: str = "codestral-22b",
        api_key: str = "EMPTY",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        timeout: float = 120.0,
    ) -> None:
        """Initialize the vLLM adapter.

        Args:
            base_url: vLLM server URL (default: http://localhost:8000/v1).
            model: Model identifier.
            api_key: API key (vLLM default is "EMPTY").
            max_tokens: Maximum tokens in response.
            temperature: Temperature for generation (capped at 0.2).
            timeout: Request timeout in seconds.
        """
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = min(temperature, self.MAX_TEMPERATURE)
        self._timeout = timeout

        self._client = VLLMClient(
            base_url=base_url,
            api_key=api_key,
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
        """Return the vLLM server URL."""
        return self._client.base_url

    def generate(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> CompilerResult:
        """Generate an artifact using vLLM.

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

            # Combine system and user prompts for completion API
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Call vLLM API
            response = self._client.generate(
                model=self._model,
                prompt=full_prompt,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )

            # Extract response text from OpenAI format
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

        except VLLMClientError as e:
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
        """Build the prompt for vLLM.

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

    def _extract_response_text(self, response: dict[str, Any]) -> str:
        """Extract the text content from vLLM response.

        Args:
            response: The vLLM API response dict (OpenAI format).

        Returns:
            The text content from the response.

        Raises:
            ValueError: If no text content found.
        """
        choices = response.get("choices", [])
        if choices:
            # For completion API
            if "text" in choices[0]:
                return str(choices[0]["text"])
            # For chat completion API
            if "message" in choices[0]:
                return str(choices[0]["message"].get("content", ""))

        raise ValueError("No text content in vLLM response")

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
        """List available models on the vLLM server.

        Returns:
            List of model names.
        """
        return self._client.list_models()

    def is_available(self) -> bool:
        """Check if vLLM server is running and accessible.

        Returns:
            True if vLLM is available, False otherwise.
        """
        return self._client.is_available()


def create_vllm_adapter_from_config() -> VLLMAdapter:
    """Create a VLLMAdapter from application configuration.

    Reads configuration from Rice-Factor settings (dynaconf).

    Returns:
        Configured VLLMAdapter instance.
    """
    from rice_factor.config.settings import settings

    return VLLMAdapter(
        base_url=settings.get("llm.vllm.base_url", "http://localhost:8000/v1"),
        model=settings.get("llm.vllm.model", "codestral-22b"),
        api_key=settings.get("llm.vllm.api_key", "EMPTY"),
        max_tokens=settings.get("llm.vllm.max_tokens", 4096),
        temperature=settings.get("llm.vllm.temperature", 0.0),
        timeout=settings.get("llm.vllm.timeout", 120.0),
    )
