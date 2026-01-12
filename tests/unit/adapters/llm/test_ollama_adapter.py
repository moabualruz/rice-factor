"""Unit tests for OllamaAdapter."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.llm.ollama_adapter import (
    OllamaAdapter,
    OllamaClient,
    OllamaClientError,
)
from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
)
from rice_factor.domain.failures.llm_errors import LLMTimeoutError


class TestOllamaClientInit:
    """Tests for OllamaClient initialization."""

    def test_default_url(self) -> None:
        """OllamaClient should use default localhost URL."""
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"

    def test_custom_url(self) -> None:
        """OllamaClient should accept custom URL."""
        client = OllamaClient(base_url="http://192.168.1.100:11434")
        assert client.base_url == "http://192.168.1.100:11434"

    def test_strips_trailing_slash(self) -> None:
        """OllamaClient should strip trailing slash from URL."""
        client = OllamaClient(base_url="http://localhost:11434/")
        assert client.base_url == "http://localhost:11434"

    def test_default_timeout(self) -> None:
        """OllamaClient should use default timeout."""
        client = OllamaClient()
        assert client.timeout == 120.0

    def test_custom_timeout(self) -> None:
        """OllamaClient should accept custom timeout."""
        client = OllamaClient(timeout=60.0)
        assert client.timeout == 60.0


class TestOllamaClientGenerate:
    """Tests for OllamaClient generate method."""

    def test_streaming_not_supported_sync(self) -> None:
        """OllamaClient should raise error for streaming in sync mode."""
        client = OllamaClient()
        with pytest.raises(OllamaClientError, match="Streaming not supported"):
            client.generate(model="codestral", prompt="test", stream=True)

    @patch.object(OllamaClient, "_generate_httpx")
    def test_generate_calls_httpx_when_available(self, mock_httpx: MagicMock) -> None:
        """OllamaClient should use httpx when available."""
        mock_httpx.return_value = {"response": "test output"}
        client = OllamaClient()
        client._httpx_available = True

        result = client.generate(model="codestral", prompt="test prompt")

        mock_httpx.assert_called_once()
        assert result == {"response": "test output"}

    @patch.object(OllamaClient, "_generate_requests")
    def test_generate_falls_back_to_requests(self, mock_requests: MagicMock) -> None:
        """OllamaClient should fall back to requests when httpx unavailable."""
        mock_requests.return_value = {"response": "test output"}
        client = OllamaClient()
        client._httpx_available = False

        result = client.generate(model="codestral", prompt="test prompt")

        mock_requests.assert_called_once()
        assert result == {"response": "test output"}


class TestOllamaClientIsAvailable:
    """Tests for OllamaClient is_available method."""

    def test_is_available_returns_true_on_success(self) -> None:
        """is_available should return True when server responds with 200."""
        client = OllamaClient()
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
        client = OllamaClient()
        client._httpx_available = False

        # Create a fake requests module that raises
        fake_requests = MagicMock()
        fake_requests.get.side_effect = Exception("Connection refused")

        with patch.dict(sys.modules, {"requests": fake_requests}):
            result = client.is_available()

        assert result is False


class TestOllamaClientListModels:
    """Tests for OllamaClient list_models method."""

    def test_list_models_returns_model_names(self) -> None:
        """list_models should return list of model names."""
        client = OllamaClient()
        client._httpx_available = False

        # Create a fake requests module
        fake_requests = MagicMock()
        fake_response = MagicMock()
        fake_response.json.return_value = {
            "models": [
                {"name": "codestral"},
                {"name": "llama3.2"},
            ]
        }
        fake_requests.get.return_value = fake_response

        with patch.dict(sys.modules, {"requests": fake_requests}):
            models = client.list_models()

        assert models == ["codestral", "llama3.2"]

    def test_list_models_returns_empty_on_no_models(self) -> None:
        """list_models should return empty list when no models."""
        client = OllamaClient()
        client._httpx_available = False

        fake_requests = MagicMock()
        fake_response = MagicMock()
        fake_response.json.return_value = {"models": []}
        fake_requests.get.return_value = fake_response

        with patch.dict(sys.modules, {"requests": fake_requests}):
            models = client.list_models()

        assert models == []


class TestOllamaAdapterInit:
    """Tests for OllamaAdapter initialization."""

    def test_default_model(self) -> None:
        """OllamaAdapter should use default model."""
        adapter = OllamaAdapter()
        assert adapter.model == "codestral"

    def test_custom_model(self) -> None:
        """OllamaAdapter should accept custom model."""
        adapter = OllamaAdapter(model="llama3.2")
        assert adapter.model == "llama3.2"

    def test_default_temperature(self) -> None:
        """OllamaAdapter should use default temperature."""
        adapter = OllamaAdapter()
        assert adapter.temperature == 0.0

    def test_temperature_capped_at_max(self) -> None:
        """OllamaAdapter should cap temperature at 0.2."""
        adapter = OllamaAdapter(temperature=0.5)
        assert adapter.temperature == 0.2

    def test_temperature_below_max(self) -> None:
        """OllamaAdapter should allow temperature below max."""
        adapter = OllamaAdapter(temperature=0.1)
        assert adapter.temperature == 0.1

    def test_base_url_property(self) -> None:
        """OllamaAdapter should expose base_url property."""
        adapter = OllamaAdapter(base_url="http://192.168.1.100:11434")
        assert adapter.base_url == "http://192.168.1.100:11434"


class TestOllamaAdapterGenerate:
    """Tests for OllamaAdapter generate method."""

    @patch.object(OllamaClient, "generate")
    def test_generate_returns_success_on_valid_json(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return success CompilerResult on valid JSON."""
        mock_generate.return_value = {
            "response": '{"goals": [], "milestones": []}'
        }

        adapter = OllamaAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        result = adapter.generate(CompilerPassType.PROJECT, context, schema)

        assert result.success is True
        assert result.payload == {"goals": [], "milestones": []}

    @patch.object(OllamaClient, "generate")
    def test_generate_returns_failure_on_invalid_json(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return failure CompilerResult on invalid JSON."""
        mock_generate.return_value = {"response": "not valid json"}

        adapter = OllamaAdapter()
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

    @patch.object(OllamaClient, "generate")
    def test_generate_returns_failure_on_llm_error_response(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return failure when LLM returns error."""
        mock_generate.return_value = {
            "response": '{"error": "missing_information", "details": "No domain specified"}'
        }

        adapter = OllamaAdapter()
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

    @patch.object(OllamaClient, "generate")
    def test_generate_raises_on_timeout(self, mock_generate: MagicMock) -> None:
        """generate should raise LLMTimeoutError on timeout."""
        mock_generate.side_effect = LLMTimeoutError("Request timed out")

        adapter = OllamaAdapter()
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )
        schema = {"type": "object"}

        with pytest.raises(LLMTimeoutError):
            adapter.generate(CompilerPassType.PROJECT, context, schema)

    @patch.object(OllamaClient, "generate")
    def test_generate_returns_failure_on_client_error(
        self, mock_generate: MagicMock
    ) -> None:
        """generate should return failure on OllamaClientError."""
        mock_generate.side_effect = OllamaClientError("Connection refused")

        adapter = OllamaAdapter()
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


class TestOllamaAdapterListModels:
    """Tests for OllamaAdapter list_models method."""

    @patch.object(OllamaClient, "list_models")
    def test_list_models_delegates_to_client(self, mock_list: MagicMock) -> None:
        """list_models should delegate to client."""
        mock_list.return_value = ["codestral", "llama3.2"]

        adapter = OllamaAdapter()
        models = adapter.list_models()

        mock_list.assert_called_once()
        assert models == ["codestral", "llama3.2"]


class TestOllamaAdapterIsAvailable:
    """Tests for OllamaAdapter is_available method."""

    @patch.object(OllamaClient, "is_available")
    def test_is_available_delegates_to_client(self, mock_available: MagicMock) -> None:
        """is_available should delegate to client."""
        mock_available.return_value = True

        adapter = OllamaAdapter()
        result = adapter.is_available()

        mock_available.assert_called_once()
        assert result is True

    @patch.object(OllamaClient, "is_available")
    def test_is_available_returns_false_when_unavailable(
        self, mock_available: MagicMock
    ) -> None:
        """is_available should return False when server unavailable."""
        mock_available.return_value = False

        adapter = OllamaAdapter()
        result = adapter.is_available()

        assert result is False


class TestCreateOllamaAdapterFromConfig:
    """Tests for create_ollama_adapter_from_config function."""

    def test_creates_adapter_with_defaults(self) -> None:
        """create_ollama_adapter_from_config should use defaults."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: default

            from rice_factor.adapters.llm.ollama_adapter import (
                create_ollama_adapter_from_config,
            )

            adapter = create_ollama_adapter_from_config()

        assert adapter.model == "codestral"
        assert adapter.base_url == "http://localhost:11434"
        assert adapter.temperature == 0.0

    def test_creates_adapter_with_custom_config(self) -> None:
        """create_ollama_adapter_from_config should use custom settings."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: {
                "llm.ollama.base_url": "http://192.168.1.100:11434",
                "llm.ollama.model": "llama3.2",
                "llm.ollama.max_tokens": 8192,
                "llm.ollama.temperature": 0.1,
                "llm.ollama.timeout": 60.0,
            }.get(key, default)

            from rice_factor.adapters.llm.ollama_adapter import (
                create_ollama_adapter_from_config,
            )

            adapter = create_ollama_adapter_from_config()

        assert adapter.model == "llama3.2"
        assert adapter.base_url == "http://192.168.1.100:11434"
        assert adapter.temperature == 0.1
