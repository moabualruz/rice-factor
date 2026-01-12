"""Tests for other CLI adapters (Codex, Gemini, Qwen, Aider)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rice_factor.adapters.llm.cli.aider_adapter import (
    AiderAdapter,
    create_aider_adapter_from_config,
)
from rice_factor.adapters.llm.cli.codex_adapter import (
    CodexAdapter,
    create_codex_adapter_from_config,
)
from rice_factor.adapters.llm.cli.gemini_cli_adapter import (
    GeminiCLIAdapter,
    create_gemini_cli_adapter_from_config,
)
from rice_factor.adapters.llm.cli.qwen_code_adapter import (
    QwenCodeAdapter,
    create_qwen_code_adapter_from_config,
)


class TestCodexAdapter:
    """Tests for CodexAdapter."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        adapter = CodexAdapter()

        assert adapter.command == "codex"
        assert adapter.approval_mode == "suggest"
        assert adapter.default_timeout == 300.0

    def test_name_property(self) -> None:
        """Test name property."""
        adapter = CodexAdapter()
        assert adapter.name == "codex"

    def test_priority_property(self) -> None:
        """Test priority property."""
        adapter = CodexAdapter()
        assert adapter.priority == 11

    @patch("shutil.which")
    def test_is_available(self, mock_which: MagicMock) -> None:
        """Test is_available."""
        mock_which.return_value = "/usr/bin/codex"
        adapter = CodexAdapter()

        result = asyncio.get_event_loop().run_until_complete(adapter.is_available())

        assert result is True

    def test_get_capabilities(self) -> None:
        """Test get_capabilities."""
        adapter = CodexAdapter()
        caps = adapter.get_capabilities()

        assert "code_generation" in caps
        assert "refactoring" in caps
        assert "code_review" in caps

    @pytest.mark.asyncio
    async def test_execute_task_success(self) -> None:
        """Test successful task execution."""
        adapter = CodexAdapter()

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(
            json.dumps({"files_modified": ["test.py"]}).encode(),
            b"",
        ))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await adapter.execute_task(
                prompt="Generate tests",
                working_dir=Path("/project"),
            )

        assert result.success is True
        assert result.agent_name == "codex"

    def test_create_from_config(self) -> None:
        """Test creating adapter from config."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: default

            adapter = create_codex_adapter_from_config()

            assert adapter.command == "codex"
            assert adapter.approval_mode == "suggest"


class TestGeminiCLIAdapter:
    """Tests for GeminiCLIAdapter."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        adapter = GeminiCLIAdapter()

        assert adapter.command == "gemini"
        assert adapter.default_timeout == 300.0
        assert adapter.model is None

    def test_name_property(self) -> None:
        """Test name property."""
        adapter = GeminiCLIAdapter()
        assert adapter.name == "gemini_cli"

    def test_priority_property(self) -> None:
        """Test priority property."""
        adapter = GeminiCLIAdapter()
        assert adapter.priority == 12

    @patch("shutil.which")
    def test_is_available(self, mock_which: MagicMock) -> None:
        """Test is_available."""
        mock_which.return_value = "/usr/bin/gemini"
        adapter = GeminiCLIAdapter()

        result = asyncio.get_event_loop().run_until_complete(adapter.is_available())

        assert result is True

    def test_get_capabilities(self) -> None:
        """Test get_capabilities."""
        adapter = GeminiCLIAdapter()
        caps = adapter.get_capabilities()

        assert "code_generation" in caps
        assert "file_operations" in caps
        assert "multi_file" in caps

    @pytest.mark.asyncio
    async def test_execute_task_success(self) -> None:
        """Test successful task execution."""
        adapter = GeminiCLIAdapter()

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(
            json.dumps({"files_modified": ["api.py"]}).encode(),
            b"",
        ))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await adapter.execute_task(
                prompt="Create API",
                working_dir=Path("/project"),
            )

        assert result.success is True
        assert result.agent_name == "gemini_cli"

    def test_create_from_config(self) -> None:
        """Test creating adapter from config."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: default

            adapter = create_gemini_cli_adapter_from_config()

            assert adapter.command == "gemini"


class TestQwenCodeAdapter:
    """Tests for QwenCodeAdapter."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        adapter = QwenCodeAdapter()

        assert adapter.command == "qwen-code"
        assert adapter.default_timeout == 300.0
        assert adapter.model is None

    def test_name_property(self) -> None:
        """Test name property."""
        adapter = QwenCodeAdapter()
        assert adapter.name == "qwen_code"

    def test_priority_property(self) -> None:
        """Test priority property."""
        adapter = QwenCodeAdapter()
        assert adapter.priority == 13

    @patch("shutil.which")
    def test_is_available(self, mock_which: MagicMock) -> None:
        """Test is_available."""
        mock_which.return_value = "/usr/bin/qwen-code"
        adapter = QwenCodeAdapter()

        result = asyncio.get_event_loop().run_until_complete(adapter.is_available())

        assert result is True

    def test_get_capabilities(self) -> None:
        """Test get_capabilities."""
        adapter = QwenCodeAdapter()
        caps = adapter.get_capabilities()

        assert "code_generation" in caps
        assert "refactoring" in caps
        assert "multi_language" in caps

    @pytest.mark.asyncio
    async def test_execute_task_success(self) -> None:
        """Test successful task execution."""
        adapter = QwenCodeAdapter()

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(
            json.dumps({"files_modified": ["algo.py"]}).encode(),
            b"",
        ))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await adapter.execute_task(
                prompt="Implement algorithm",
                working_dir=Path("/project"),
            )

        assert result.success is True
        assert result.agent_name == "qwen_code"

    def test_create_from_config(self) -> None:
        """Test creating adapter from config."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: default

            adapter = create_qwen_code_adapter_from_config()

            assert adapter.command == "qwen-code"


class TestAiderAdapter:
    """Tests for AiderAdapter."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        adapter = AiderAdapter()

        assert adapter.command == "aider"
        assert adapter.model == "claude-sonnet-4-20250514"
        assert adapter.auto_commits is False
        assert adapter.default_timeout == 600.0

    def test_name_property(self) -> None:
        """Test name property."""
        adapter = AiderAdapter()
        assert adapter.name == "aider"

    def test_priority_property(self) -> None:
        """Test priority property."""
        adapter = AiderAdapter()
        assert adapter.priority == 14

    @patch("shutil.which")
    def test_is_available(self, mock_which: MagicMock) -> None:
        """Test is_available."""
        mock_which.return_value = "/usr/bin/aider"
        adapter = AiderAdapter()

        result = asyncio.get_event_loop().run_until_complete(adapter.is_available())

        assert result is True

    def test_get_capabilities(self) -> None:
        """Test get_capabilities."""
        adapter = AiderAdapter()
        caps = adapter.get_capabilities()

        assert "code_generation" in caps
        assert "refactoring" in caps
        assert "git_integration" in caps
        assert "multi_file" in caps
        assert "testing" in caps

    def test_parse_modified_files(self) -> None:
        """Test parsing modified files from Aider output."""
        adapter = AiderAdapter()
        output = """
        Added database.py to the chat
        Wrote database.py
        Applied edit to models.py
        Wrote utils.py
        """

        files = adapter._parse_modified_files(output)

        assert "database.py" in files
        assert "models.py" in files
        assert "utils.py" in files
        # Should not have duplicates
        assert files.count("database.py") == 1

    @pytest.mark.asyncio
    async def test_execute_task_success(self) -> None:
        """Test successful task execution."""
        adapter = AiderAdapter()

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(
            b"Wrote database.py\nApplied edit to models.py\n",
            b"",
        ))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await adapter.execute_task(
                prompt="Add database layer",
                working_dir=Path("/project"),
            )

        assert result.success is True
        assert result.agent_name == "aider"
        assert "database.py" in result.files_modified
        assert "models.py" in result.files_modified

    @pytest.mark.asyncio
    async def test_execute_task_no_auto_commits(self) -> None:
        """Test task execution includes --no-auto-commits flag."""
        adapter = AiderAdapter(auto_commits=False)

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_process,
        ) as mock_exec:
            await adapter.execute_task(
                prompt="Test",
                working_dir=Path("/project"),
            )

        call_args = mock_exec.call_args[0]
        assert "--no-auto-commits" in call_args

    @pytest.mark.asyncio
    async def test_execute_task_with_auto_commits(self) -> None:
        """Test task execution without --no-auto-commits flag."""
        adapter = AiderAdapter(auto_commits=True)

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_process,
        ) as mock_exec:
            await adapter.execute_task(
                prompt="Test",
                working_dir=Path("/project"),
            )

        call_args = mock_exec.call_args[0]
        assert "--no-auto-commits" not in call_args

    def test_create_from_config(self) -> None:
        """Test creating adapter from config."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: default

            adapter = create_aider_adapter_from_config()

            assert adapter.command == "aider"
            assert adapter.model == "claude-sonnet-4-20250514"
            assert adapter.auto_commits is False
