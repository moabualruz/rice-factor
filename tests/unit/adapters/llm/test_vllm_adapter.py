"""Unit tests for VLLMAdapter."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.llm.vllm_adapter import (
    VLLMAdapter,
    VLLMClient,
    VLLMClientError,
)
from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
)
from rice_factor.domain.failures.llm_errors import LLMTimeoutError


class TestVLLMClientInit:
    """Tests for VLLMClient initialization."""

    def test_default_url(self) -> None:
        """VLLMClient should use default localhost URL."""
        client = VLLMClient()
        assert client.base_url == "http://localhost:8000/v1"

    def test_custom_url(self) -> None:
        """VLLMClient should accept custom URL."""
        client = VLLMClient(base_url="http://192.168.1.100:8000/v1")
        assert client.base_url == "http://192.168.1.100:8000/v1"

    def test_strips_trailing_slash(self) -> None:
        """VLLMClient should strip trailing slash from URL."""
        client = VLLMClient(base_url="http://localhost:8000/v1/")
        assert client.base_url == "http://localhost:8000/v1"

    def test_default_api_key(self) -> None:
        """VLLMClient should use default EMPTY api key."""
        client = VLLMClient()
        assert client.api_key == "EMPTY"

    def test_custom_api_key(self) -> None:
        """VLLMClient should accept custom api key."""
        client = VLLMClient(api_key="sk-test-key")
        assert client.api_key == "sk-test-key"

    def test_default_timeout(self) -> None:
        """VLLMClient should use default timeout."""
        client = VLLMClient()
        assert client.timeout == 120.0

    def test_custom_timeout(self) -> None:
        """VLLMClient should accept custom timeout."""
        client = VLLMClient(timeout=60.0)
        assert client.timeout == 60.0


class TestVLLMClientGenerate:
    """Tests for VLLMClient generate method."""

    def test_streaming_not_supported_sync(self) -> None:
        """VLLMClient should raise error for streaming in sync mode."""
        client = VLLMClient()
        with pytest.raises(VLLMClientError, match="Streaming not supported"):
            client.generate(model="codestral", prompt="test", stream=True)

    @patch.object(VLLMClient, "_generate_httpx")
    def test_generate_calls_httpx_when_available(self, mock_httpx: MagicMock) -> None:
        """VLLMClient should use httpx when available."""
        mock_httpx.return_value = {"choices": [{"text": "test output"}]}
        client = VLLMClient()
        client._httpx_available = True

        result = client.generate(model="codestral", prompt="test prompt")

        mock_httpx.assert_called_once()
        assert result == {"choices": [{"text": "test output"}]}

    @patch.object(VLLMClient, "_generate_requests")
    def test_generate_falls_back_to_requests(self, mock_requests: MagicMock) -> None:
        """VLLMClient should fall back to requests when httpx unavailable."""
        mock_requests.return_value = {"choices": [{"text": "test output"}]}
        client = VLLMClient()
        client._httpx_available = False

        result = client.generate(model="codestral", prompt="test prompt")

        mock_requests.assert_called_once()
        assert result == {"choices": [{"text": "test output"}]}


class TestVLLMClientIsAvailable:
    """Tests for VLLMClient is_available method."""

    def test_is_available_returns_true_on_success(self) -> None:
        """is_available should return True when server responds with 200."""
        client = VLLMClient()
        client._httpx_available = False  # Force fallback

        # Create a fake requests module
        fake_requests = MagicMock()
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_requests.get.return_value = fake_response

        with patch.dict(sys.modules, {"requests": fake_requests}):
            result = client.is_available()

        assert result is True

    def test_is_available_returns_false_on_error(self) -> None:
        """is_available should return False when server unavailable."""
        client = VLLMClient()
        client._httpx_available = False

        # Create a fake requests module that raises
        fake_requests = MagicMock()
        fake_requests.get.side_effect = Exception("Connection refused")

        with patch.dict(sys.modules, {"requests": fake_requests}):
            result = client.is_available()

        assert result is False


class TestVLLMClientListModels:
    """Tests for VLLMClient list_models method."""

    def test_list_models_returns_model_names(self) -> None:
        """list_models should return list of model names."""
        client = VLLMClient()
        client._httpx_available = False

        # Create a fake requests module
        fake_requests = MagicMock()
        fake_response = MagicMock()
        fake_response.json.return_value = {
            "data": [
                {"id": "codestral-22b"},
                {"id": "llama-70b"},
            ]
        }
        fake_requests.get.return_value = fake_response

        with patch.dict(sys.modules, {"requests": fake_requests}):
            models = client.list_models()

        assert models == ["codestral-22b", "llama-70b"]

    def test_list_models_returns_empty_on_no_models(self) -> None:
        """list_models should return empty list when no models."""
        client = VLLMClient()
        client._httpx_available = False

        fake_requests = MagicMock()
        fake_response = MagicMock()
        fake_response.json.return_value = {"data": []}
        fake_requests.get.return_value = fake_response

        with patch.dict(sys.modules, {"requests": fake_requests}):
            models = client.list_models()

        assert models == []


class TestVLLMAdapterInit:
    """Tests for VLLMAdapter initialization."""

    def test_default_model(self) -> None:
        """VLLMAdapter should use default model."""
        adapter = VLLMAdapter()
        assert adapter.model == "codestral-22b"

    def test_custom_model(self) -> None:
        """VLLMAdapter should accept custom model."""
        adapter = VLLMAdapter(model="llama-70b")
        assert adapter.model == "llama-70b"

    def test_default_temperature(self) -> None:
        """VLLMAdapter should use default temperature."""
        adapter = VLLMAdapter()
        assert adapter.temperature == 0.0

    def test_temperature_capped_at_max(self) -> None:
        """VLLMAdapter should cap temperature at 0.2."""
        adapter = VLLMAdapter(temperature=0.5)
        assert adapter.temperature == 0.2

    def test_temperature_below_max(self) -> None:
        """VLLMAdapter should allow temperature below max."""
        adapter = VLLMAdapter(temperature=0.1)
        assert adapter.temperature == 0.1

    def test_base_url_property(self) -> None:
        """VLLMAdapter should expose base_url property."""
        adapter = VLLMAdapter(base_url="http://192.168.1.100:8000/v1")
        assert adapter.base_url == "http://192.168.1.100:8000/v1"


class TestVLLMAdapterGenerate:
    """Tests for VLLMAdapter generate method."""

    @patch.object(VLLMClient, "generate")
    def test_generate_returns_success_on_valid_json(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return success CompilerResult on valid JSON."""
        mock_generate.return_value = {
            "choices": [{"text": '{"goals": [], "milestones": []}'}]
        }

        adapter = VLLMAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        result = adapter.generate(CompilerPassType.PROJECT, context, schema)

        assert result.success is True
        assert result.payload == {"goals": [], "milestones": []}

    @patch.object(VLLMClient, "generate")
    def test_generate_returns_failure_on_invalid_json(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return failure CompilerResult on invalid JSON."""
        mock_generate.return_value = {"choices": [{"text": "not valid json"}]}

        adapter = VLLMAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        result = adapter.generate(CompilerPassType.PROJECT, context, schema)

        assert result.success is False
        # error_type can be InvalidJSONError (from extractor) or invalid_json
        assert "json" in result.error_type.lower() or "invalid" in result.error_type.lower()

    @patch.object(VLLMClient, "generate")
    def test_generate_returns_failure_on_llm_error_response(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return failure when LLM returns error."""
        mock_generate.return_value = {
            "choices": [
                {"text": '{"error": "missing_information", "details": "No domain specified"}'}
            ]
        }

        adapter = VLLMAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        result = adapter.generate(CompilerPassType.PROJECT, context, schema)

        assert result.success is False
        assert result.error_type == "missing_information"
        assert "No domain specified" in str(result.error_details)

    @patch.object(VLLMClient, "generate")
    def test_generate_raises_on_timeout(self, mock_generate: MagicMock) -> None:
        """generate should raise LLMTimeoutError on timeout."""
        mock_generate.side_effect = LLMTimeoutError("Request timed out")

        adapter = VLLMAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        with pytest.raises(LLMTimeoutError):
            adapter.generate(CompilerPassType.PROJECT, context, schema)

    @patch.object(VLLMClient, "generate")
    def test_generate_returns_failure_on_client_error(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return failure on VLLMClientError."""
        mock_generate.side_effect = VLLMClientError("Connection refused")

        adapter = VLLMAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        result = adapter.generate(CompilerPassType.PROJECT, context, schema)

        assert result.success is False
        assert result.error_type == "client_error"
        assert "Connection refused" in str(result.error_details)


class TestVLLMAdapterListModels:
    """Tests for VLLMAdapter list_models method."""

    @patch.object(VLLMClient, "list_models")
    def test_list_models_delegates_to_client(self, mock_list: MagicMock) -> None:
        """list_models should delegate to client."""
        mock_list.return_value = ["codestral-22b", "llama-70b"]

        adapter = VLLMAdapter()
        models = adapter.list_models()

        mock_list.assert_called_once()
        assert models == ["codestral-22b", "llama-70b"]


class TestVLLMAdapterIsAvailable:
    """Tests for VLLMAdapter is_available method."""

    @patch.object(VLLMClient, "is_available")
    def test_is_available_delegates_to_client(self, mock_available: MagicMock) -> None:
        """is_available should delegate to client."""
        mock_available.return_value = True

        adapter = VLLMAdapter()
        result = adapter.is_available()

        mock_available.assert_called_once()
        assert result is True

    @patch.object(VLLMClient, "is_available")
    def test_is_available_returns_false_when_unavailable(
        self, mock_available: MagicMock
    ) -> None:
        """is_available should return False when server unavailable."""
        mock_available.return_value = False

        adapter = VLLMAdapter()
        result = adapter.is_available()

        assert result is False


class TestVLLMAdapterExtractResponseText:
    """Tests for VLLMAdapter _extract_response_text method."""

    def test_extracts_from_completion_response(self) -> None:
        """_extract_response_text should extract from completion format."""
        adapter = VLLMAdapter()
        response = {"choices": [{"text": "generated text"}]}

        result = adapter._extract_response_text(response)

        assert result == "generated text"

    def test_extracts_from_chat_completion_response(self) -> None:
        """_extract_response_text should extract from chat completion format."""
        adapter = VLLMAdapter()
        response = {"choices": [{"message": {"content": "chat response"}}]}

        result = adapter._extract_response_text(response)

        assert result == "chat response"

    def test_raises_on_empty_response(self) -> None:
        """_extract_response_text should raise on empty response."""
        adapter = VLLMAdapter()
        response: dict[str, list[str]] = {"choices": []}

        with pytest.raises(ValueError, match="No text content"):
            adapter._extract_response_text(response)


class TestCreateVLLMAdapterFromConfig:
    """Tests for create_vllm_adapter_from_config function."""

    def test_creates_adapter_with_defaults(self) -> None:
        """create_vllm_adapter_from_config should use defaults."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: default

            from rice_factor.adapters.llm.vllm_adapter import (
                create_vllm_adapter_from_config,
            )

            adapter = create_vllm_adapter_from_config()

        assert adapter.model == "codestral-22b"
        assert adapter.base_url == "http://localhost:8000/v1"
        assert adapter.temperature == 0.0

    def test_creates_adapter_with_custom_config(self) -> None:
        """create_vllm_adapter_from_config should use custom settings."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: {
                "llm.vllm.base_url": "http://192.168.1.100:8000/v1",
                "llm.vllm.model": "llama-70b",
                "llm.vllm.api_key": "sk-test",
                "llm.vllm.max_tokens": 8192,
                "llm.vllm.temperature": 0.1,
                "llm.vllm.timeout": 60.0,
            }.get(key, default)

            from rice_factor.adapters.llm.vllm_adapter import (
                create_vllm_adapter_from_config,
            )

            adapter = create_vllm_adapter_from_config()

        assert adapter.model == "llama-70b"
        assert adapter.base_url == "http://192.168.1.100:8000/v1"
        assert adapter.temperature == 0.1
