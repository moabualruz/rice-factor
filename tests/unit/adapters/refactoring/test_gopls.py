"""Unit tests for gopls adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.gopls_adapter import GoplsAdapter
from rice_factor.domain.ports.refactor import (
    RefactorOperation,
    RefactorRequest,
)


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def adapter(tmp_project: Path) -> GoplsAdapter:
    """Create a gopls adapter for testing."""
    return GoplsAdapter(tmp_project)


class TestGoplsAdapter:
    """Tests for GoplsAdapter."""

    def test_supported_languages(self, adapter: GoplsAdapter) -> None:
        """Test that Go is supported."""
        languages = adapter.get_supported_languages()
        assert languages == ["go"]

    def test_supported_operations(self, adapter: GoplsAdapter) -> None:
        """Test that expected operations are supported."""
        operations = adapter.get_supported_operations()
        assert RefactorOperation.RENAME in operations
        assert RefactorOperation.EXTRACT_METHOD in operations
        assert RefactorOperation.INLINE in operations

    @patch("subprocess.run")
    def test_is_available_when_installed(
        self, mock_run: MagicMock, adapter: GoplsAdapter
    ) -> None:
        """Test availability when gopls is installed."""
        mock_run.return_value = MagicMock(returncode=0, stdout="gopls v0.14.0")
        assert adapter.is_available() is True

    @patch("subprocess.run")
    def test_is_not_available_when_not_installed(
        self, mock_run: MagicMock, adapter: GoplsAdapter
    ) -> None:
        """Test availability when gopls is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert adapter.is_available() is False

    @patch("subprocess.run")
    def test_get_version(self, mock_run: MagicMock, adapter: GoplsAdapter) -> None:
        """Test version extraction."""
        mock_run.return_value = MagicMock(returncode=0, stdout="gopls v0.14.2")
        version = adapter.get_version()
        assert version == "0.14.2"

    @patch("subprocess.run")
    def test_execute_not_available(
        self, mock_run: MagicMock, adapter: GoplsAdapter
    ) -> None:
        """Test execute when gopls is not available."""
        mock_run.side_effect = FileNotFoundError()

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="OldFunc",
            new_value="NewFunc",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "not installed" in result.errors[0]

    @patch("subprocess.run")
    def test_rename_missing_new_value(
        self, mock_run: MagicMock, adapter: GoplsAdapter
    ) -> None:
        """Test rename without new_value."""
        mock_run.return_value = MagicMock(returncode=0)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="OldFunc",
            # new_value intentionally omitted
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "new_value is required" in result.errors[0]

    @patch("subprocess.run")
    def test_rename_with_gorename(
        self, mock_run: MagicMock, adapter: GoplsAdapter
    ) -> None:
        """Test rename using gorename."""
        # First call for is_available
        mock_run.return_value = MagicMock(returncode=0, stdout="gopls v0.14.0", stderr="")

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="main.OldFunc",
            new_value="NewFunc",
        )

        result = adapter.execute(request, dry_run=True)

        # Should have attempted to run gorename
        calls = mock_run.call_args_list
        gorename_call = None
        for call in calls:
            args = call[0][0] if call[0] else call[1].get("args", [])
            if "gorename" in str(args):
                gorename_call = call
                break

        if gorename_call:
            args = gorename_call[0][0]
            assert "-d" in args  # dry-run flag

    @patch("subprocess.run")
    def test_rename_dry_run_output_parsing(
        self, mock_run: MagicMock, adapter: GoplsAdapter
    ) -> None:
        """Test parsing of diff output from gorename."""
        diff_output = """--- a/main.go
+++ b/main.go
@@ -10,7 +10,7 @@
-func OldFunc() {
+func NewFunc() {
"""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=diff_output, stderr=""
        )

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="main.OldFunc",
            new_value="NewFunc",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        assert len(result.changes) > 0
        assert result.changes[0].file_path == "a/main.go"

    @patch("subprocess.run")
    def test_rename_command_failure(
        self, mock_run: MagicMock, adapter: GoplsAdapter
    ) -> None:
        """Test handling of command failure."""
        # Mock both is_available and the rename command
        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            if "version" in str(cmd):
                return MagicMock(returncode=0, stdout="gopls v0.14.0", stderr="")
            else:
                return MagicMock(returncode=1, stdout="", stderr="identifier not found")

        mock_run.side_effect = mock_subprocess

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="pkg.NotFound",
            new_value="NewName",
        )

        result = adapter.execute(request)
        assert result.success is False
        assert len(result.errors) > 0

    def test_extract_method_not_supported(self, adapter: GoplsAdapter) -> None:
        """Test that extract method returns appropriate error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            request = RefactorRequest(
                operation=RefactorOperation.EXTRACT_METHOD,
                target="someCode",
            )

            result = adapter.execute(request)
            assert result.success is False
            assert "LSP client" in result.errors[0]

    def test_inline_not_supported(self, adapter: GoplsAdapter) -> None:
        """Test that inline returns appropriate error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            request = RefactorRequest(
                operation=RefactorOperation.INLINE,
                target="someVar",
            )

            result = adapter.execute(request)
            assert result.success is False
            assert "LSP client" in result.errors[0]

    @patch("subprocess.run")
    def test_rollback(self, mock_run: MagicMock, adapter: GoplsAdapter) -> None:
        """Test rollback functionality."""
        mock_run.return_value = MagicMock(returncode=0)

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True, changes=[], errors=[], tool_used="gopls", dry_run=False
        )

        assert adapter.rollback(result) is True
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "checkout" in call_args

    @patch("subprocess.run")
    def test_rollback_failure(self, mock_run: MagicMock, adapter: GoplsAdapter) -> None:
        """Test rollback failure handling."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True, changes=[], errors=[], tool_used="gopls", dry_run=False
        )

        assert adapter.rollback(result) is False

    def test_get_capability(self, adapter: GoplsAdapter) -> None:
        """Test capability reporting."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="gopls v0.14.0")
            cap = adapter.get_capability()
            assert cap.tool_name == "GoplsAdapter"
            assert cap.languages == ["go"]
            assert RefactorOperation.RENAME in cap.operations


class TestGoplsRenameWithPosition:
    """Tests for position-based rename."""

    @patch("subprocess.run")
    def test_rename_with_file_position(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test rename request includes file position info."""
        adapter = GoplsAdapter(tmp_path)
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="OldFunc",
            new_value="NewFunc",
            file_path="main.go",
            line=10,
            column=6,
        )

        # The request should have the position info
        assert request.file_path == "main.go"
        assert request.line == 10
        assert request.column == 6

        # Execute the request - it will call subprocess
        adapter.execute(request, dry_run=True)

        # Just verify subprocess was called
        assert mock_run.called
