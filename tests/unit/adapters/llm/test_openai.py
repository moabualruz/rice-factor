"""Unit tests for OpenAIAdapter."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
)


class TestOpenAIAdapterInstantiation:
    """Tests for OpenAIAdapter instantiation."""

    def test_instantiation_with_defaults(self) -> None:
        """Should instantiate with default parameters."""
        with patch(
            "rice_factor.adapters.llm.openai_adapter.OpenAIClient"
        ) as mock_client_class:
            from rice_factor.adapters.llm.openai_adapter import OpenAIAdapter

            adapter = OpenAIAdapter()
            assert adapter is not None
            mock_client_class.assert_called_once()

    def test_instantiation_with_custom_params(self) -> None:
        """Should instantiate with custom parameters."""
        with patch(
            "rice_factor.adapters.llm.openai_adapter.OpenAIClient"
        ):
            from rice_factor.adapters.llm.openai_adapter import OpenAIAdapter

            adapter = OpenAIAdapter(
                api_key="test-key",
                model="gpt-4o",
                max_tokens=8192,
                temperature=0.1,
                top_p=0.2,
            )
            assert adapter.model == "gpt-4o"
            assert adapter.temperature == 0.1
            assert adapter.top_p == 0.2

    def test_temperature_capped_at_max(self) -> None:
        """Temperature should be capped at 0.2."""
        with patch("rice_factor.adapters.llm.openai_adapter.OpenAIClient"):
            from rice_factor.adapters.llm.openai_adapter import OpenAIAdapter

            adapter = OpenAIAdapter(temperature=0.5)
            assert adapter.temperature == 0.2

    def test_top_p_capped_at_max(self) -> None:
        """Top_p should be capped at 0.3."""
        with patch("rice_factor.adapters.llm.openai_adapter.OpenAIClient"):
            from rice_factor.adapters.llm.openai_adapter import OpenAIAdapter

            adapter = OpenAIAdapter(top_p=0.8)
            assert adapter.top_p == 0.3

    def test_instantiation_with_azure_config(self) -> None:
        """Should instantiate with Azure OpenAI configuration."""
        with patch(
            "rice_factor.adapters.llm.openai_adapter.OpenAIClient"
        ) as mock_client_class:
            from rice_factor.adapters.llm.openai_adapter import OpenAIAdapter

            adapter = OpenAIAdapter(
                api_key="test-key",
                azure_endpoint="https://myresource.openai.azure.com/",
                azure_api_version="2024-02-15-preview",
            )

            mock_client_class.assert_called_once_with(
                api_key="test-key",
                timeout=120.0,
                max_retries=3,
                azure_endpoint="https://myresource.openai.azure.com/",
                azure_api_version="2024-02-15-preview",
            )
            assert adapter is not None


class TestOpenAIAdapterGenerate:
    """Tests for OpenAIAdapter.generate method."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock OpenAIClient."""
        mock = MagicMock()
        mock.create_chat_completion.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": "gpt-4-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "domains": [{"name": "Core", "responsibility": "Core"}],
                            "modules": [{"name": "auth", "domain": "Core"}],
                            "constraints": {
                                "architecture": "hexagonal",
                                "languages": ["python"],
                            },
                        }),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        }
        mock.is_azure = False
        return mock

    @pytest.fixture
    def adapter(self, mock_client: MagicMock) -> Any:
        """Create OpenAIAdapter with mock client."""
        with patch("rice_factor.adapters.llm.openai_adapter.OpenAIClient"):
            from rice_factor.adapters.llm.openai_adapter import OpenAIAdapter

            a = OpenAIAdapter()
            a._client = mock_client
            return a

    @pytest.fixture
    def context(self) -> CompilerContext:
        """Create test context."""
        return CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "README.md": "# Test Project",
            },
            artifacts={},
        )

    def test_generate_returns_success_with_payload(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,  # noqa: ARG002
    ) -> None:
        """generate returns success with parsed payload."""
        result = adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        assert result.success is True
        assert result.payload is not None
        assert "domains" in result.payload

    def test_generate_calls_client_create_chat_completion(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """generate calls client.create_chat_completion."""
        adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        mock_client.create_chat_completion.assert_called_once()

    def test_generate_uses_json_mode(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """generate should use JSON mode for structured output."""
        adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        call_kwargs = mock_client.create_chat_completion.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}

    def test_generate_includes_schema_in_messages(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """generate should include schema in user message."""
        test_schema = {"type": "object", "properties": {"foo": {"type": "string"}}}
        adapter.generate(
            CompilerPassType.PROJECT,
            context,
            test_schema,
        )
        call_kwargs = mock_client.create_chat_completion.call_args[1]
        messages = call_kwargs["messages"]

        # Find user message
        user_message = None
        for msg in messages:
            if msg["role"] == "user":
                user_message = msg
                break

        assert user_message is not None
        assert "OUTPUT SCHEMA:" in user_message["content"]
        assert '"foo"' in user_message["content"]


class TestOpenAIAdapterErrorHandling:
    """Tests for OpenAIAdapter error handling."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock OpenAIClient."""
        return MagicMock()

    @pytest.fixture
    def adapter(self, mock_client: MagicMock) -> Any:
        """Create OpenAIAdapter with mock client."""
        with patch("rice_factor.adapters.llm.openai_adapter.OpenAIClient"):
            from rice_factor.adapters.llm.openai_adapter import OpenAIAdapter

            a = OpenAIAdapter()
            a._client = mock_client
            return a

    @pytest.fixture
    def context(self) -> CompilerContext:
        """Create test context."""
        return CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={},
            artifacts={},
        )

    def test_handles_timeout_error(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """Should handle timeout error gracefully."""
        from rice_factor.domain.failures.llm_errors import LLMTimeoutError

        mock_client.create_chat_completion.side_effect = LLMTimeoutError(
            message="Request timed out",
            timeout_seconds=120,
        )

        result = adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        assert result.success is False
        assert result.error_type == "timeout"
        assert result.error_details is not None
        assert "timed out" in result.error_details.lower()

    def test_handles_rate_limit_error(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """Should handle rate limit error gracefully."""
        from rice_factor.domain.failures.llm_errors import LLMRateLimitError

        mock_client.create_chat_completion.side_effect = LLMRateLimitError(
            message="Rate limit exceeded",
            retry_after=30,
        )

        result = adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        assert result.success is False
        assert result.error_type == "rate_limit"
        assert result.error_details is not None
        assert "rate limit" in result.error_details.lower()

    def test_handles_api_error(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """Should handle API error gracefully."""
        from rice_factor.domain.failures.llm_errors import LLMAPIError

        mock_client.create_chat_completion.side_effect = LLMAPIError(
            message="API error occurred",
            status_code=500,
        )

        result = adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        assert result.success is False
        assert result.error_type == "api_error"
        assert result.error_details is not None
        assert "api error" in result.error_details.lower()

    def test_handles_invalid_json_response(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """Should handle invalid JSON in response."""
        mock_client.create_chat_completion.return_value = {
            "id": "chatcmpl-123",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is not JSON",
                    },
                    "finish_reason": "stop",
                }
            ],
        }

        result = adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        assert result.success is False
        assert result.error_type == "invalid_json"
        assert result.error_details is not None


class TestOpenAIAdapterBuildMessages:
    """Tests for OpenAIAdapter._build_messages method."""

    @pytest.fixture
    def adapter(self) -> Any:
        """Create OpenAIAdapter."""
        with patch("rice_factor.adapters.llm.openai_adapter.OpenAIClient"):
            from rice_factor.adapters.llm.openai_adapter import OpenAIAdapter

            return OpenAIAdapter()

    def test_build_messages_includes_project_files(
        self,
        adapter: Any,
    ) -> None:
        """Should include project files in messages."""
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "main.py": "print('hello')",
                "config.yaml": "key: value",
            },
            artifacts={},
        )
        messages = adapter._build_messages(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )

        assert len(messages) == 1
        content = messages[0]["content"]
        assert "PROJECT FILES:" in content
        assert "main.py" in content
        assert "print('hello')" in content

    def test_build_messages_includes_artifacts(
        self,
        adapter: Any,
    ) -> None:
        """Should include artifacts in messages."""
        context = CompilerContext(
            pass_type=CompilerPassType.ARCHITECTURE,
            project_files={},
            artifacts={
                "project-plan": {"domains": [{"name": "Core"}]},
            },
        )
        messages = adapter._build_messages(
            CompilerPassType.ARCHITECTURE,
            context,
            {"type": "object"},
        )

        content = messages[0]["content"]
        assert "ARTIFACTS:" in content
        assert "project-plan" in content
        assert "Core" in content

    def test_build_messages_includes_target_file(
        self,
        adapter: Any,
    ) -> None:
        """Should include target file when present."""
        context = CompilerContext(
            pass_type=CompilerPassType.IMPLEMENTATION,
            project_files={},
            artifacts={},
            target_file="src/auth.py",
        )
        messages = adapter._build_messages(
            CompilerPassType.IMPLEMENTATION,
            context,
            {"type": "object"},
        )

        content = messages[0]["content"]
        assert "TARGET FILE:" in content
        assert "src/auth.py" in content


class TestOpenAIAdapterIsErrorResponse:
    """Tests for OpenAIAdapter._is_error_response method."""

    @pytest.fixture
    def adapter(self) -> Any:
        """Create OpenAIAdapter."""
        with patch("rice_factor.adapters.llm.openai_adapter.OpenAIClient"):
            from rice_factor.adapters.llm.openai_adapter import OpenAIAdapter

            return OpenAIAdapter()

    def test_detects_missing_information_error(self, adapter: Any) -> None:
        """Should detect missing information error type."""
        payload = {
            "error_type": "missing_information",
            "error_message": "Need more details",
        }
        assert adapter._is_error_response(payload) is True

    def test_normal_payload_not_error(self, adapter: Any) -> None:
        """Normal payload should not be detected as error."""
        payload = {"domains": [], "modules": [], "constraints": {}}
        assert adapter._is_error_response(payload) is False


class TestCreateOpenAIAdapterFromConfig:
    """Tests for create_openai_adapter_from_config function."""

    def test_creates_adapter_from_settings(self) -> None:
        """create_openai_adapter_from_config creates adapter from settings."""
        with (
            patch("rice_factor.adapters.llm.openai_adapter.OpenAIClient"),
            patch(
                "rice_factor.config.settings.settings"
            ) as mock_settings,
        ):
            mock_settings.get.side_effect = lambda key, default: {
                "openai.model": "gpt-4o",
                "llm.max_tokens": 8192,
                "llm.temperature": 0.1,
                "llm.top_p": 0.2,
                "llm.timeout": 60.0,
                "llm.max_retries": 5,
                "azure.openai_endpoint": None,
                "azure.openai_api_version": None,
            }.get(key, default)

            from rice_factor.adapters.llm.openai_adapter import (
                create_openai_adapter_from_config,
            )

            adapter = create_openai_adapter_from_config()
            assert adapter.model == "gpt-4o"
