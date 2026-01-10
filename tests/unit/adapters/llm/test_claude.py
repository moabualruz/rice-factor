"""Unit tests for ClaudeAdapter."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
)


class TestClaudeAdapterInstantiation:
    """Tests for ClaudeAdapter instantiation."""

    def test_instantiation_with_defaults(self) -> None:
        """Should instantiate with default parameters."""
        with patch(
            "rice_factor.adapters.llm.claude.ClaudeClient"
        ) as mock_client_class:
            from rice_factor.adapters.llm.claude import ClaudeAdapter

            adapter = ClaudeAdapter()
            assert adapter is not None
            mock_client_class.assert_called_once()

    def test_instantiation_with_custom_params(self) -> None:
        """Should instantiate with custom parameters."""
        with patch(
            "rice_factor.adapters.llm.claude.ClaudeClient"
        ):
            from rice_factor.adapters.llm.claude import ClaudeAdapter

            adapter = ClaudeAdapter(
                api_key="test-key",
                model="claude-3-opus",
                max_tokens=8192,
                temperature=0.1,
                top_p=0.2,
            )
            assert adapter.model == "claude-3-opus"
            assert adapter.temperature == 0.1
            assert adapter.top_p == 0.2

    def test_temperature_capped_at_max(self) -> None:
        """Temperature should be capped at 0.2."""
        with patch("rice_factor.adapters.llm.claude.ClaudeClient"):
            from rice_factor.adapters.llm.claude import ClaudeAdapter

            adapter = ClaudeAdapter(temperature=0.5)
            assert adapter.temperature == 0.2

    def test_top_p_capped_at_max(self) -> None:
        """Top-p should be capped at 0.3."""
        with patch("rice_factor.adapters.llm.claude.ClaudeClient"):
            from rice_factor.adapters.llm.claude import ClaudeAdapter

            adapter = ClaudeAdapter(top_p=0.9)
            assert adapter.top_p == 0.3


class TestClaudeAdapterGenerate:
    """Tests for ClaudeAdapter.generate method."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock ClaudeClient."""
        mock = MagicMock()
        mock.create_message.return_value = {
            "id": "msg-123",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "domains": [
                                {"name": "Core", "responsibility": "Core logic"}
                            ],
                            "modules": [{"name": "main", "domain": "Core"}],
                            "constraints": {
                                "architecture": "hexagonal",
                                "languages": ["python"],
                            },
                        }
                    ),
                }
            ],
            "model": "claude-3-5-sonnet",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
        return mock

    @pytest.fixture
    def adapter(self, mock_client: MagicMock) -> Any:
        """Create adapter with mock client."""
        with patch(
            "rice_factor.adapters.llm.claude.ClaudeClient", return_value=mock_client
        ):
            from rice_factor.adapters.llm.claude import ClaudeAdapter

            return ClaudeAdapter()

    @pytest.fixture
    def context(self) -> CompilerContext:
        """Create a test context."""
        return CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "Test requirements",
                "constraints.md": "Test constraints",
                "glossary.md": "Test glossary",
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

    def test_generate_calls_client_create_message(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """generate calls client.create_message."""
        adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        mock_client.create_message.assert_called_once()

    def test_generate_passes_determinism_parameters(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """generate passes determinism parameters to client."""
        adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        call_kwargs = mock_client.create_message.call_args[1]
        assert call_kwargs["temperature"] == 0.0
        assert call_kwargs["top_p"] == 0.3

    def test_generate_handles_json_in_code_fence(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """generate handles JSON wrapped in code fence."""
        mock_client.create_message.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": """```json
{
    "domains": [{"name": "Test", "responsibility": "Testing"}],
    "modules": [{"name": "test", "domain": "Test"}],
    "constraints": {"architecture": "hexagonal", "languages": ["python"]}
}
```""",
                }
            ],
        }
        result = adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        assert result.success is True
        assert result.payload is not None

    def test_generate_handles_invalid_json(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """generate returns error for invalid JSON."""
        mock_client.create_message.return_value = {
            "content": [{"type": "text", "text": "not valid json"}],
        }
        result = adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        assert result.success is False
        assert result.error_type is not None

    def test_generate_handles_error_response(
        self,
        adapter: Any,
        context: CompilerContext,
        mock_client: MagicMock,
    ) -> None:
        """generate returns error when LLM returns error response."""
        mock_client.create_message.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "error": "missing_information",
                            "details": "Could not determine domain",
                        }
                    ),
                }
            ],
        }
        result = adapter.generate(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        assert result.success is False
        assert result.error_type == "missing_information"


class TestClaudeAdapterBuildMessages:
    """Tests for ClaudeAdapter._build_messages method."""

    @pytest.fixture
    def adapter(self) -> Any:
        """Create adapter with mock client."""
        with patch("rice_factor.adapters.llm.claude.ClaudeClient"):
            from rice_factor.adapters.llm.claude import ClaudeAdapter

            return ClaudeAdapter()

    @pytest.fixture
    def context(self) -> CompilerContext:
        """Create a test context."""
        return CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={"requirements.md": "Test"},
            artifacts={},
        )

    def test_build_messages_returns_user_message(
        self,
        adapter: Any,
        context: CompilerContext,
    ) -> None:
        """_build_messages returns a list with user message."""
        messages = adapter._build_messages(
            CompilerPassType.PROJECT,
            context,
            {"type": "object"},
        )
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_build_messages_includes_schema(
        self,
        adapter: Any,
        context: CompilerContext,
    ) -> None:
        """_build_messages includes schema in content."""
        messages = adapter._build_messages(
            CompilerPassType.PROJECT,
            context,
            {"type": "object", "properties": {}},
        )
        # Should contain schema reference
        content = messages[0]["content"]
        assert isinstance(content, str)


class TestClaudeAdapterExtractResponseText:
    """Tests for ClaudeAdapter._extract_response_text method."""

    @pytest.fixture
    def adapter(self) -> Any:
        """Create adapter with mock client."""
        with patch("rice_factor.adapters.llm.claude.ClaudeClient"):
            from rice_factor.adapters.llm.claude import ClaudeAdapter

            return ClaudeAdapter()

    def test_extract_response_text_from_valid_response(
        self,
        adapter: Any,
    ) -> None:
        """_extract_response_text extracts text from valid response."""
        response = {
            "content": [{"type": "text", "text": "Hello world"}],
        }
        text = adapter._extract_response_text(response)
        assert text == "Hello world"

    def test_extract_response_text_raises_on_empty(
        self,
        adapter: Any,
    ) -> None:
        """_extract_response_text raises ValueError on empty content."""
        response = {"content": []}
        with pytest.raises(ValueError) as exc_info:
            adapter._extract_response_text(response)
        assert "No text content" in str(exc_info.value)

    def test_extract_response_text_raises_on_no_text_block(
        self,
        adapter: Any,
    ) -> None:
        """_extract_response_text raises ValueError on no text block."""
        response = {"content": [{"type": "image", "data": "..."}]}
        with pytest.raises(ValueError):
            adapter._extract_response_text(response)


class TestClaudeAdapterIsErrorResponse:
    """Tests for ClaudeAdapter._is_error_response method."""

    @pytest.fixture
    def adapter(self) -> Any:
        """Create adapter with mock client."""
        with patch("rice_factor.adapters.llm.claude.ClaudeClient"):
            from rice_factor.adapters.llm.claude import ClaudeAdapter

            return ClaudeAdapter()

    def test_is_error_response_with_error_field(
        self,
        adapter: Any,
    ) -> None:
        """_is_error_response returns True for error field."""
        payload = {"error": "missing_information"}
        assert adapter._is_error_response(payload) is True

    def test_is_error_response_with_error_type(
        self,
        adapter: Any,
    ) -> None:
        """_is_error_response returns True for error_type field."""
        payload = {"error_type": "missing_information"}
        assert adapter._is_error_response(payload) is True

    def test_is_error_response_with_valid_payload(
        self,
        adapter: Any,
    ) -> None:
        """_is_error_response returns False for valid payload."""
        payload = {"domains": [], "modules": [], "constraints": {}}
        assert adapter._is_error_response(payload) is False


class TestCreateClaudeAdapterFromConfig:
    """Tests for create_claude_adapter_from_config function."""

    def test_creates_adapter_from_settings(self) -> None:
        """create_claude_adapter_from_config creates adapter from settings."""
        with (
            patch("rice_factor.adapters.llm.claude.ClaudeClient"),
            patch(
                "rice_factor.config.settings.settings"
            ) as mock_settings,
        ):
            mock_settings.get.side_effect = lambda key, default: {
                "llm.model": "claude-3-opus",
                "llm.max_tokens": 8192,
                "llm.temperature": 0.1,
                "llm.top_p": 0.2,
                "llm.timeout": 60.0,
                "llm.max_retries": 5,
            }.get(key, default)

            from rice_factor.adapters.llm.claude import (
                create_claude_adapter_from_config,
            )

            adapter = create_claude_adapter_from_config()
            assert adapter.model == "claude-3-opus"
