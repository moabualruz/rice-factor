"""Tests for OpenCode CLI adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from rice_factor.adapters.llm.cli.opencode_adapter import (
    OpenCodeAdapter,
    create_opencode_adapter_from_config,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestOpenCodeAdapter:
    """Tests for OpenCodeAdapter."""

    def test_default_values(self) -> None:
        """Test default adapter configuration."""
        adapter = OpenCodeAdapter()

        assert adapter.command == "opencode"
        assert adapter.default_args == ["run"]
        assert adapter.default_timeout == 300.0
        assert adapter.model is None
        assert adapter.attach_url is None
        assert adapter.session_id is None
        assert adapter.continue_session is False
        assert adapter.output_format == "json"
        assert adapter._priority == 15

    def test_custom_values(self) -> None:
        """Test custom adapter configuration."""
        adapter = OpenCodeAdapter(
            command="custom-opencode",
            model="anthropic/claude-4-sonnet",
            attach_url="http://localhost:4096",
            default_timeout=600.0,
            session_id="abc123",
            output_format="default",
        )

        assert adapter.command == "custom-opencode"
        assert adapter.model == "anthropic/claude-4-sonnet"
        assert adapter.attach_url == "http://localhost:4096"
        assert adapter.default_timeout == 600.0
        assert adapter.session_id == "abc123"
        assert adapter.output_format == "default"

    def test_name_property(self) -> None:
        """Test name property returns correct value."""
        adapter = OpenCodeAdapter()
        assert adapter.name == "opencode"

    def test_priority_property(self) -> None:
        """Test priority property returns correct value."""
        adapter = OpenCodeAdapter()
        assert adapter.priority == 15

        adapter2 = OpenCodeAdapter(_priority=20)
        assert adapter2.priority == 20

    def test_get_capabilities(self) -> None:
        """Test capabilities list."""
        adapter = OpenCodeAdapter()
        capabilities = adapter.get_capabilities()

        assert "code_generation" in capabilities
        assert "refactoring" in capabilities
        assert "file_manipulation" in capabilities
        assert "command_execution" in capabilities
        assert "multi_file" in capabilities
        assert "testing" in capabilities

    @pytest.mark.asyncio
    async def test_is_available_when_installed(self) -> None:
        """Test availability check when OpenCode is installed."""
        adapter = OpenCodeAdapter()

        with patch("shutil.which", return_value="/usr/bin/opencode"):
            result = await adapter.is_available()
            assert result is True

    @pytest.mark.asyncio
    async def test_is_available_when_not_installed(self) -> None:
        """Test availability check when OpenCode is not installed."""
        adapter = OpenCodeAdapter()

        with patch("shutil.which", return_value=None):
            result = await adapter.is_available()
            assert result is False


class TestOpenCodeAdapterCommandBuilding:
    """Tests for command building."""

    def test_build_basic_command(self) -> None:
        """Test basic command building."""
        adapter = OpenCodeAdapter()
        cmd = adapter._build_command("Test prompt")

        assert cmd[0] == "opencode"
        assert "run" in cmd
        assert "--format" in cmd
        assert "json" in cmd
        assert "Test prompt" in cmd

    def test_build_command_with_model(self) -> None:
        """Test command with model selection."""
        adapter = OpenCodeAdapter(model="openai/gpt-4o")
        cmd = adapter._build_command("Test prompt")

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "openai/gpt-4o"

    def test_build_command_with_attach_url(self) -> None:
        """Test command with server attach mode."""
        adapter = OpenCodeAdapter(attach_url="http://localhost:4096")
        cmd = adapter._build_command("Test prompt")

        assert "--attach" in cmd
        attach_idx = cmd.index("--attach")
        assert cmd[attach_idx + 1] == "http://localhost:4096"

    def test_build_command_with_session_id(self) -> None:
        """Test command with session ID."""
        adapter = OpenCodeAdapter(session_id="session-123")
        cmd = adapter._build_command("Test prompt")

        assert "--session" in cmd
        session_idx = cmd.index("--session")
        assert cmd[session_idx + 1] == "session-123"

    def test_build_command_with_continue(self) -> None:
        """Test command with continue session flag."""
        adapter = OpenCodeAdapter(continue_session=True)
        cmd = adapter._build_command("Test prompt")

        assert "--continue" in cmd

    def test_session_id_takes_precedence_over_continue(self) -> None:
        """Test that session_id takes precedence over continue_session."""
        adapter = OpenCodeAdapter(session_id="abc", continue_session=True)
        cmd = adapter._build_command("Test prompt")

        # Should have --session, not --continue
        assert "--session" in cmd
        assert "--continue" not in cmd


class TestOpenCodeAdapterExecution:
    """Tests for task execution."""

    @pytest.mark.asyncio
    async def test_execute_task_success(self, tmp_path: Path) -> None:
        """Test successful task execution."""
        adapter = OpenCodeAdapter()

        json_output = json.dumps({
            "success": True,
            "files_modified": ["src/main.py"],
            "files_created": ["tests/test_main.py"],
            "session_id": "sess-123",
        })

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(json_output.encode(), b"")
        )

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_process,
        ):
            result = await adapter.execute_task(
                "Add tests for main.py",
                tmp_path,
                timeout_seconds=60.0,
            )

        assert result.success is True
        assert result.agent_name == "opencode"
        assert "src/main.py" in result.files_modified
        assert "tests/test_main.py" in result.files_created
        assert result.exit_code == 0
        assert result.metadata.get("session_id") == "sess-123"

    @pytest.mark.asyncio
    async def test_execute_task_failure(self, tmp_path: Path) -> None:
        """Test failed task execution."""
        adapter = OpenCodeAdapter()

        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"Error: Task failed")
        )

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_process,
        ):
            result = await adapter.execute_task(
                "Invalid task",
                tmp_path,
            )

        assert result.success is False
        assert result.exit_code == 1
        assert result.error == "Error: Task failed"

    @pytest.mark.asyncio
    async def test_execute_task_timeout(self, tmp_path: Path) -> None:
        """Test task execution timeout."""
        adapter = OpenCodeAdapter()

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            side_effect=TimeoutError()
        )

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_process,
        ):
            result = await adapter.execute_task(
                "Long running task",
                tmp_path,
                timeout_seconds=1.0,
            )

        assert result.success is False
        assert "Timeout" in result.error

    @pytest.mark.asyncio
    async def test_execute_task_not_found(self, tmp_path: Path) -> None:
        """Test when OpenCode CLI is not found."""
        adapter = OpenCodeAdapter()

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError(),
        ):
            result = await adapter.execute_task(
                "Some task",
                tmp_path,
            )

        assert result.success is False
        assert "not found" in result.error.lower()


class TestOpenCodeAdapterOutputParsing:
    """Tests for output parsing."""

    def test_parse_modified_files_json(self) -> None:
        """Test parsing modified files from JSON output."""
        adapter = OpenCodeAdapter()
        output = json.dumps({
            "files_modified": ["a.py", "b.py"],
        })

        files = adapter._parse_modified_files(output)
        assert files == ["a.py", "b.py"]

    def test_parse_modified_files_text(self) -> None:
        """Test parsing modified files from text output."""
        adapter = OpenCodeAdapter()
        output = """Modified src/main.py
Updated lib/utils.py
Some other text"""

        files = adapter._parse_modified_files(output)
        assert "src/main.py" in files
        assert "lib/utils.py" in files

    def test_parse_created_files_json(self) -> None:
        """Test parsing created files from JSON output."""
        adapter = OpenCodeAdapter()
        output = json.dumps({
            "files_created": ["new_file.py", "another.py"],
        })

        files = adapter._parse_created_files(output)
        assert files == ["new_file.py", "another.py"]

    def test_parse_created_files_text(self) -> None:
        """Test parsing created files from text output."""
        adapter = OpenCodeAdapter()
        output = """Created tests/test_new.py
Wrote docs/README.md"""

        files = adapter._parse_created_files(output)
        assert "tests/test_new.py" in files
        assert "docs/README.md" in files

    def test_extract_metadata_json(self) -> None:
        """Test extracting metadata from JSON output."""
        adapter = OpenCodeAdapter()
        output = json.dumps({
            "session_id": "sess-456",
            "model": "claude-4-sonnet",
            "provider": "anthropic",
        })

        metadata = adapter._extract_metadata(output)
        assert metadata["session_id"] == "sess-456"
        assert metadata["model"] == "claude-4-sonnet"
        assert metadata["provider"] == "anthropic"

    def test_extract_metadata_invalid_json(self) -> None:
        """Test metadata extraction with invalid JSON."""
        adapter = OpenCodeAdapter()
        output = "Not valid JSON"

        metadata = adapter._extract_metadata(output)
        assert metadata == {}


class TestCreateOpenCodeAdapterFromConfig:
    """Tests for factory function."""

    def test_create_with_defaults(self) -> None:
        """Test creating adapter with default config."""
        config: dict[str, object] = {}
        adapter = create_opencode_adapter_from_config(config)

        assert adapter.command == "opencode"
        assert adapter.model is None
        assert adapter.attach_url is None
        assert adapter.default_timeout == 300.0

    def test_create_with_full_config(self) -> None:
        """Test creating adapter with full config."""
        config: dict[str, object] = {
            "command": "my-opencode",
            "model": "google/gemini-2.0-flash",
            "attach_url": "http://localhost:8080",
            "timeout_seconds": 600,
            "session_id": "test-session",
            "continue_session": False,
            "output_format": "default",
        }
        adapter = create_opencode_adapter_from_config(config)

        assert adapter.command == "my-opencode"
        assert adapter.model == "google/gemini-2.0-flash"
        assert adapter.attach_url == "http://localhost:8080"
        assert adapter.default_timeout == 600.0
        assert adapter.session_id == "test-session"
        assert adapter.continue_session is False
        assert adapter.output_format == "default"

    def test_create_with_continue_session(self) -> None:
        """Test creating adapter with continue session enabled."""
        config: dict[str, object] = {
            "continue_session": True,
        }
        adapter = create_opencode_adapter_from_config(config)

        assert adapter.continue_session is True
        assert adapter.session_id is None
