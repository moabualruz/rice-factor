"""Tests for Claude Code CLI adapter."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rice_factor.adapters.llm.cli.claude_code_adapter import (
    ClaudeCodeAdapter,
    create_claude_code_adapter_from_config,
)


class TestClaudeCodeAdapter:
    """Tests for ClaudeCodeAdapter."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        adapter = ClaudeCodeAdapter()

        assert adapter.command == "claude"
        assert adapter.default_timeout == 300.0
        assert adapter.model is None
        assert "--print" in adapter.default_args
        assert "--output-format" in adapter.default_args

    def test_init_custom_values(self) -> None:
        """Test initialization with custom values."""
        adapter = ClaudeCodeAdapter(
            command="custom-claude",
            default_timeout=600.0,
            model="claude-opus",
        )

        assert adapter.command == "custom-claude"
        assert adapter.default_timeout == 600.0
        assert adapter.model == "claude-opus"

    def test_name_property(self) -> None:
        """Test name property."""
        adapter = ClaudeCodeAdapter()
        assert adapter.name == "claude_code"

    def test_priority_property(self) -> None:
        """Test priority property."""
        adapter = ClaudeCodeAdapter()
        assert adapter.priority == 10

        adapter = ClaudeCodeAdapter(_priority=5)
        assert adapter.priority == 5

    @patch("shutil.which")
    def test_is_available_true(self, mock_which: MagicMock) -> None:
        """Test is_available when command exists."""
        mock_which.return_value = "/usr/bin/claude"
        adapter = ClaudeCodeAdapter()

        result = asyncio.get_event_loop().run_until_complete(adapter.is_available())

        assert result is True
        mock_which.assert_called_once_with("claude")

    @patch("shutil.which")
    def test_is_available_false(self, mock_which: MagicMock) -> None:
        """Test is_available when command doesn't exist."""
        mock_which.return_value = None
        adapter = ClaudeCodeAdapter()

        result = asyncio.get_event_loop().run_until_complete(adapter.is_available())

        assert result is False

    def test_get_capabilities(self) -> None:
        """Test get_capabilities returns expected capabilities."""
        adapter = ClaudeCodeAdapter()
        caps = adapter.get_capabilities()

        assert "code_generation" in caps
        assert "refactoring" in caps
        assert "testing" in caps
        assert "git_integration" in caps
        assert "multi_file" in caps

    def test_parse_output_json(self) -> None:
        """Test parsing JSON output."""
        adapter = ClaudeCodeAdapter()
        output = json.dumps({
            "files_modified": ["src/main.py"],
            "files_created": ["src/utils.py"],
            "tokens_used": 1500,
        })

        result = adapter._parse_output(output)

        assert result["files_modified"] == ["src/main.py"]
        assert result["files_created"] == ["src/utils.py"]
        assert "tokens_used" in result["metadata"]

    def test_parse_output_invalid_json(self) -> None:
        """Test parsing non-JSON output."""
        adapter = ClaudeCodeAdapter()
        output = "Modified: src/main.py\nCreated: src/utils.py"

        result = adapter._parse_output(output)

        assert result["files_modified"] == ["src/main.py"]
        assert result["files_created"] == ["src/utils.py"]

    def test_parse_text_output(self) -> None:
        """Test parsing text output for file lists."""
        adapter = ClaudeCodeAdapter()
        output = """
        Starting task...
        Modified: src/main.py
        Updated: src/config.py
        Created: tests/test_main.py
        Done.
        """

        result = adapter._parse_text_output(output)

        assert "src/main.py" in result["files_modified"]
        assert "src/config.py" in result["files_modified"]
        assert "tests/test_main.py" in result["files_created"]

    @pytest.mark.asyncio
    async def test_execute_task_success(self) -> None:
        """Test successful task execution."""
        adapter = ClaudeCodeAdapter()

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(
            json.dumps({"files_modified": ["test.py"]}).encode(),
            b"",
        ))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await adapter.execute_task(
                prompt="Add tests",
                working_dir=Path("/project"),
            )

        assert result.success is True
        assert result.agent_name == "claude_code"
        assert "test.py" in result.files_modified
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_execute_task_failure(self) -> None:
        """Test failed task execution."""
        adapter = ClaudeCodeAdapter()

        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(
            b"",
            b"Error: Invalid prompt",
        ))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await adapter.execute_task(
                prompt="Invalid",
                working_dir=Path("/project"),
            )

        assert result.success is False
        assert result.exit_code == 1
        assert "Error: Invalid prompt" in result.error

    @pytest.mark.asyncio
    async def test_execute_task_timeout(self) -> None:
        """Test task execution timeout."""
        adapter = ClaudeCodeAdapter(default_timeout=0.1)

        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("asyncio.wait_for", side_effect=TimeoutError()):
                result = await adapter.execute_task(
                    prompt="Long task",
                    working_dir=Path("/project"),
                )

        assert result.success is False
        assert "Timeout" in result.error
        assert result.exit_code == -1

    @pytest.mark.asyncio
    async def test_execute_task_command_not_found(self) -> None:
        """Test task execution with missing command."""
        adapter = ClaudeCodeAdapter(command="nonexistent")

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError(),
        ):
            result = await adapter.execute_task(
                prompt="Test",
                working_dir=Path("/project"),
            )

        assert result.success is False
        assert "Command not found" in result.error
        assert result.exit_code == -1

    @pytest.mark.asyncio
    async def test_execute_task_with_model(self) -> None:
        """Test task execution with custom model."""
        adapter = ClaudeCodeAdapter(model="claude-opus")

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"{}", b""))

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_process,
        ) as mock_exec:
            await adapter.execute_task(
                prompt="Test",
                working_dir=Path("/project"),
            )

        # Check that --model flag was included
        call_args = mock_exec.call_args[0]
        assert "--model" in call_args
        assert "claude-opus" in call_args


class TestCreateClaudeCodeAdapterFromConfig:
    """Tests for create_claude_code_adapter_from_config."""

    def test_create_from_default_config(self) -> None:
        """Test creating adapter with default config."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: default

            adapter = create_claude_code_adapter_from_config()

            assert adapter.command == "claude"
            assert adapter.default_timeout == 300.0
            assert adapter.model is None

    def test_create_from_custom_config(self) -> None:
        """Test creating adapter with custom config."""
        config_values = {
            "cli_agents.claude_code.command": "custom-claude",
            "cli_agents.claude_code.timeout": 600.0,
            "cli_agents.claude_code.model": "claude-opus",
            "cli_agents.claude_code.priority": 5,
        }

        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: config_values.get(
                key, default
            )

            adapter = create_claude_code_adapter_from_config()

            assert adapter.command == "custom-claude"
            assert adapter.default_timeout == 600.0
            assert adapter.model == "claude-opus"
            assert adapter.priority == 5
