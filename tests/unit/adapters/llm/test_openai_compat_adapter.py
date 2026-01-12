"""Unit tests for OpenAICompatAdapter."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.llm.openai_compat_adapter import (
    KNOWN_PROVIDERS,
    OpenAICompatAdapter,
    OpenAICompatClient,
    OpenAICompatClientError,
)
from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
)
from rice_factor.domain.failures.llm_errors import LLMTimeoutError


class TestKnownProviders:
    """Tests for known provider configurations."""

    def test_localai_config_exists(self) -> None:
        """KNOWN_PROVIDERS should have localai config."""
        assert "localai" in KNOWN_PROVIDERS
        assert KNOWN_PROVIDERS["localai"]["default_url"] == "http://localhost:8080/v1"

    def test_lmstudio_config_exists(self) -> None:
        """KNOWN_PROVIDERS should have lmstudio config."""
        assert "lmstudio" in KNOWN_PROVIDERS
        assert KNOWN_PROVIDERS["lmstudio"]["default_url"] == "http://localhost:1234/v1"

    def test_tgi_config_exists(self) -> None:
        """KNOWN_PROVIDERS should have tgi config."""
        assert "tgi" in KNOWN_PROVIDERS
        assert KNOWN_PROVIDERS["tgi"]["supports_chat"] is True
        assert KNOWN_PROVIDERS["tgi"]["supports_completions"] is False

    def test_generic_config_exists(self) -> None:
        """KNOWN_PROVIDERS should have generic config."""
        assert "generic" in KNOWN_PROVIDERS


class TestOpenAICompatClientInit:
    """Tests for OpenAICompatClient initialization."""

    def test_default_url(self) -> None:
        """OpenAICompatClient should use default localhost URL."""
        client = OpenAICompatClient()
        assert client.base_url == "http://localhost:8080/v1"

    def test_custom_url(self) -> None:
        """OpenAICompatClient should accept custom URL."""
        client = OpenAICompatClient(base_url="http://192.168.1.100:8080/v1")
        assert client.base_url == "http://192.168.1.100:8080/v1"

    def test_strips_trailing_slash(self) -> None:
        """OpenAICompatClient should strip trailing slash from URL."""
        client = OpenAICompatClient(base_url="http://localhost:8080/v1/")
        assert client.base_url == "http://localhost:8080/v1"

    def test_default_api_key(self) -> None:
        """OpenAICompatClient should use default EMPTY api key."""
        client = OpenAICompatClient()
        assert client.api_key == "EMPTY"

    def test_custom_api_key(self) -> None:
        """OpenAICompatClient should accept custom api key."""
        client = OpenAICompatClient(api_key="sk-test-key")
        assert client.api_key == "sk-test-key"

    def test_default_timeout(self) -> None:
        """OpenAICompatClient should use default timeout."""
        client = OpenAICompatClient()
        assert client.timeout == 120.0

    def test_provider_config_localai(self) -> None:
        """OpenAICompatClient should use localai provider config."""
        client = OpenAICompatClient(provider="localai")
        assert client.supports_chat is True
        assert client.supports_completions is True

    def test_provider_config_tgi(self) -> None:
        """OpenAICompatClient should use tgi provider config."""
        client = OpenAICompatClient(provider="tgi")
        assert client.supports_chat is True
        assert client.supports_completions is False


class TestOpenAICompatClientGenerate:
    """Tests for OpenAICompatClient generate method."""

    def test_streaming_not_supported_sync(self) -> None:
        """OpenAICompatClient should raise error for streaming in sync mode."""
        client = OpenAICompatClient()
        with pytest.raises(OpenAICompatClientError, match="Streaming not supported"):
            client.generate(model="test", prompt="test", stream=True)

    @patch.object(OpenAICompatClient, "_generate_chat")
    def test_generate_uses_chat_by_default(self, mock_chat: MagicMock) -> None:
        """OpenAICompatClient should use chat API by default."""
        mock_chat.return_value = {"choices": [{"message": {"content": "test"}}]}
        client = OpenAICompatClient()

        result = client.generate(model="test", prompt="test prompt")

        mock_chat.assert_called_once()
        assert result == {"choices": [{"message": {"content": "test"}}]}

    @patch.object(OpenAICompatClient, "_generate_completion")
    def test_generate_can_force_completions(self, mock_completion: MagicMock) -> None:
        """OpenAICompatClient should be able to force completions API."""
        mock_completion.return_value = {"choices": [{"text": "test"}]}
        client = OpenAICompatClient()

        result = client.generate(model="test", prompt="test", use_chat=False)

        mock_completion.assert_called_once()
        assert result == {"choices": [{"text": "test"}]}


class TestOpenAICompatClientGetHeaders:
    """Tests for OpenAICompatClient _get_headers method."""

    def test_headers_with_empty_key(self) -> None:
        """_get_headers should not include auth header for EMPTY key."""
        client = OpenAICompatClient(api_key="EMPTY")
        headers = client._get_headers()
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

    def test_headers_with_api_key(self) -> None:
        """_get_headers should include auth header when api_key provided."""
        client = OpenAICompatClient(api_key="sk-test-123")
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer sk-test-123"


class TestOpenAICompatClientIsAvailable:
    """Tests for OpenAICompatClient is_available method."""

    def test_is_available_returns_true_on_success(self) -> None:
        """is_available should return True when server responds with 200."""
        client = OpenAICompatClient()
        client._httpx_available = False

        fake_requests = MagicMock()
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_requests.get.return_value = fake_response

        with patch.dict(sys.modules, {"requests": fake_requests}):
            result = client.is_available()

        assert result is True

    def test_is_available_returns_false_on_error(self) -> None:
        """is_available should return False when server unavailable."""
        client = OpenAICompatClient()
        client._httpx_available = False

        fake_requests = MagicMock()
        fake_requests.get.side_effect = Exception("Connection refused")

        with patch.dict(sys.modules, {"requests": fake_requests}):
            result = client.is_available()

        assert result is False


class TestOpenAICompatClientListModels:
    """Tests for OpenAICompatClient list_models method."""

    def test_list_models_returns_model_names(self) -> None:
        """list_models should return list of model names."""
        client = OpenAICompatClient()
        client._httpx_available = False

        fake_requests = MagicMock()
        fake_response = MagicMock()
        fake_response.json.return_value = {
            "data": [
                {"id": "gpt-3.5-turbo"},
                {"id": "gpt-4"},
            ]
        }
        fake_requests.get.return_value = fake_response

        with patch.dict(sys.modules, {"requests": fake_requests}):
            models = client.list_models()

        assert models == ["gpt-3.5-turbo", "gpt-4"]


class TestOpenAICompatAdapterInit:
    """Tests for OpenAICompatAdapter initialization."""

    def test_default_model_from_generic(self) -> None:
        """OpenAICompatAdapter should use generic default model."""
        adapter = OpenAICompatAdapter()
        assert adapter.model == "default"

    def test_default_model_from_localai(self) -> None:
        """OpenAICompatAdapter should use localai default model."""
        adapter = OpenAICompatAdapter(provider="localai")
        assert adapter.model == "gpt-3.5-turbo"

    def test_custom_model(self) -> None:
        """OpenAICompatAdapter should accept custom model."""
        adapter = OpenAICompatAdapter(model="custom-model")
        assert adapter.model == "custom-model"

    def test_default_temperature(self) -> None:
        """OpenAICompatAdapter should use default temperature."""
        adapter = OpenAICompatAdapter()
        assert adapter.temperature == 0.0

    def test_temperature_capped_at_max(self) -> None:
        """OpenAICompatAdapter should cap temperature at 0.2."""
        adapter = OpenAICompatAdapter(temperature=0.5)
        assert adapter.temperature == 0.2

    def test_provider_property(self) -> None:
        """OpenAICompatAdapter should expose provider property."""
        adapter = OpenAICompatAdapter(provider="lmstudio")
        assert adapter.provider == "lmstudio"


class TestOpenAICompatAdapterGenerate:
    """Tests for OpenAICompatAdapter generate method."""

    @patch.object(OpenAICompatClient, "generate")
    def test_generate_returns_success_on_valid_json(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return success CompilerResult on valid JSON."""
        mock_generate.return_value = {
            "choices": [{"message": {"content": '{"goals": [], "milestones": []}'}}]
        }

        adapter = OpenAICompatAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        result = adapter.generate(CompilerPassType.PROJECT, context, schema)

        assert result.success is True
        assert result.payload == {"goals": [], "milestones": []}

    @patch.object(OpenAICompatClient, "generate")
    def test_generate_returns_failure_on_invalid_json(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return failure CompilerResult on invalid JSON."""
        mock_generate.return_value = {"choices": [{"message": {"content": "not valid"}}]}

        adapter = OpenAICompatAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        result = adapter.generate(CompilerPassType.PROJECT, context, schema)

        assert result.success is False

    @patch.object(OpenAICompatClient, "generate")
    def test_generate_raises_on_timeout(self, mock_generate: MagicMock) -> None:
        """generate should raise LLMTimeoutError on timeout."""
        mock_generate.side_effect = LLMTimeoutError("Request timed out")

        adapter = OpenAICompatAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        with pytest.raises(LLMTimeoutError):
            adapter.generate(CompilerPassType.PROJECT, context, schema)

    @patch.object(OpenAICompatClient, "generate")
    def test_generate_returns_failure_on_client_error(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return failure on OpenAICompatClientError."""
        mock_generate.side_effect = OpenAICompatClientError("Connection refused")

        adapter = OpenAICompatAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        result = adapter.generate(CompilerPassType.PROJECT, context, schema)

        assert result.success is False
        assert result.error_type == "client_error"


class TestOpenAICompatAdapterExtractResponseText:
    """Tests for OpenAICompatAdapter _extract_response_text method."""

    def test_extracts_from_completion_response(self) -> None:
        """_extract_response_text should extract from completion format."""
        adapter = OpenAICompatAdapter()
        response = {"choices": [{"text": "generated text"}]}

        result = adapter._extract_response_text(response)

        assert result == "generated text"

    def test_extracts_from_chat_completion_response(self) -> None:
        """_extract_response_text should extract from chat completion format."""
        adapter = OpenAICompatAdapter()
        response = {"choices": [{"message": {"content": "chat response"}}]}

        result = adapter._extract_response_text(response)

        assert result == "chat response"

    def test_raises_on_empty_response(self) -> None:
        """_extract_response_text should raise on empty response."""
        adapter = OpenAICompatAdapter()
        response: dict[str, list[str]] = {"choices": []}

        with pytest.raises(ValueError, match="No text content"):
            adapter._extract_response_text(response)


class TestOpenAICompatAdapterListModels:
    """Tests for OpenAICompatAdapter list_models method."""

    @patch.object(OpenAICompatClient, "list_models")
    def test_list_models_delegates_to_client(self, mock_list: MagicMock) -> None:
        """list_models should delegate to client."""
        mock_list.return_value = ["gpt-3.5-turbo", "gpt-4"]

        adapter = OpenAICompatAdapter()
        models = adapter.list_models()

        mock_list.assert_called_once()
        assert models == ["gpt-3.5-turbo", "gpt-4"]


class TestOpenAICompatAdapterIsAvailable:
    """Tests for OpenAICompatAdapter is_available method."""

    @patch.object(OpenAICompatClient, "is_available")
    def test_is_available_delegates_to_client(self, mock_available: MagicMock) -> None:
        """is_available should delegate to client."""
        mock_available.return_value = True

        adapter = OpenAICompatAdapter()
        result = adapter.is_available()

        mock_available.assert_called_once()
        assert result is True


class TestCreateOpenAICompatAdapterFromConfig:
    """Tests for create_openai_compat_adapter_from_config function."""

    def test_creates_adapter_with_defaults(self) -> None:
        """create_openai_compat_adapter_from_config should use defaults."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default=None: default

            from rice_factor.adapters.llm.openai_compat_adapter import (
                create_openai_compat_adapter_from_config,
            )

            adapter = create_openai_compat_adapter_from_config()

        assert adapter.base_url == "http://localhost:8080/v1"
        assert adapter.temperature == 0.0
        assert adapter.provider == "generic"

    def test_creates_adapter_with_custom_config(self) -> None:
        """create_openai_compat_adapter_from_config should use custom settings."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default=None: {
                "llm.openai_compat.base_url": "http://192.168.1.100:1234/v1",
                "llm.openai_compat.model": "local-llama",
                "llm.openai_compat.api_key": "sk-test",
                "llm.openai_compat.provider": "lmstudio",
                "llm.openai_compat.temperature": 0.1,
            }.get(key, default)

            from rice_factor.adapters.llm.openai_compat_adapter import (
                create_openai_compat_adapter_from_config,
            )

            adapter = create_openai_compat_adapter_from_config()

        assert adapter.model == "local-llama"
        assert adapter.base_url == "http://192.168.1.100:1234/v1"
        assert adapter.provider == "lmstudio"
