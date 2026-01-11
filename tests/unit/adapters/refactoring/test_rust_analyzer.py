"""Unit tests for rust-analyzer adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.rust_analyzer_adapter import RustAnalyzerAdapter
from rice_factor.domain.ports.refactor import (
    RefactorOperation,
    RefactorRequest,
)


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary Rust project directory."""
    # Create src directory with Rust files
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.rs").write_text("fn main() { old_func(); }\n")
    (src_dir / "lib.rs").write_text("pub fn old_func() {}\n")
    return tmp_path


@pytest.fixture
def adapter(tmp_project: Path) -> RustAnalyzerAdapter:
    """Create a rust-analyzer adapter for testing."""
    return RustAnalyzerAdapter(tmp_project)


class TestRustAnalyzerAdapter:
    """Tests for RustAnalyzerAdapter."""

    def test_supported_languages(self, adapter: RustAnalyzerAdapter) -> None:
        """Test that Rust is supported."""
        languages = adapter.get_supported_languages()
        assert languages == ["rust"]

    def test_supported_operations(self, adapter: RustAnalyzerAdapter) -> None:
        """Test that expected operations are supported."""
        operations = adapter.get_supported_operations()
        assert RefactorOperation.RENAME in operations
        assert RefactorOperation.EXTRACT_METHOD in operations
        assert RefactorOperation.INLINE in operations

    @patch("subprocess.run")
    def test_is_available_when_installed(
        self, mock_run: MagicMock, adapter: RustAnalyzerAdapter
    ) -> None:
        """Test availability when rust-analyzer is installed."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="rust-analyzer 2024-01-15"
        )
        assert adapter.is_available() is True

    @patch("subprocess.run")
    def test_is_not_available_when_not_installed(
        self, mock_run: MagicMock, adapter: RustAnalyzerAdapter
    ) -> None:
        """Test availability when rust-analyzer is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert adapter.is_available() is False

    @patch("subprocess.run")
    def test_get_version(
        self, mock_run: MagicMock, adapter: RustAnalyzerAdapter
    ) -> None:
        """Test version extraction."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="rust-analyzer 2024-01-15"
        )
        version = adapter.get_version()
        assert version == "2024-01-15"

    @patch("subprocess.run")
    def test_execute_not_available(
        self, mock_run: MagicMock, adapter: RustAnalyzerAdapter
    ) -> None:
        """Test execute when rust-analyzer is not available."""
        mock_run.side_effect = FileNotFoundError()

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "not installed" in result.errors[0]

    @patch("subprocess.run")
    def test_rename_missing_new_value(
        self, mock_run: MagicMock, adapter: RustAnalyzerAdapter
    ) -> None:
        """Test rename without new_value."""
        mock_run.return_value = MagicMock(returncode=0)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "new_value is required" in result.errors[0]

    @patch("subprocess.run")
    def test_rename_dry_run(
        self, mock_run: MagicMock, tmp_project: Path
    ) -> None:
        """Test rename in dry-run mode."""
        adapter = RustAnalyzerAdapter(tmp_project)

        # Mock rust-analyzer availability and grep returning absolute paths
        main_rs = str(tmp_project / "src" / "main.rs")
        lib_rs = str(tmp_project / "src" / "lib.rs")
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="rust-analyzer 2024-01-15"),
            MagicMock(returncode=0, stdout=f"{main_rs}\n{lib_rs}"),
        ]

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
        )

        result = adapter.execute(request, dry_run=True)

        # Should find occurrences in the Rust files
        assert result.tool_used == "rust-analyzer"
        assert result.dry_run is True
        # Changes should be populated from the files containing old_func
        assert len(result.changes) >= 1

    @patch("subprocess.run")
    def test_rename_apply(
        self, mock_run: MagicMock, tmp_project: Path
    ) -> None:
        """Test rename with apply (not dry-run)."""
        adapter = RustAnalyzerAdapter(tmp_project)

        # Mock rust-analyzer availability and grep
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="rust-analyzer 2024-01-15"),
            MagicMock(
                returncode=0,
                stdout=f"{tmp_project}/src/main.rs\n{tmp_project}/src/lib.rs",
            ),
            MagicMock(returncode=0),  # cargo check
        ]

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert result.dry_run is False

        # Files should be modified
        main_rs = (tmp_project / "src" / "main.rs").read_text()
        assert "new_func" in main_rs

    @patch("subprocess.run")
    def test_rename_validation_failure(
        self, mock_run: MagicMock, tmp_project: Path
    ) -> None:
        """Test rename with validation failure (cargo check fails)."""
        adapter = RustAnalyzerAdapter(tmp_project)

        # Mock rust-analyzer availability, grep, and failed cargo check
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="rust-analyzer 2024-01-15"),
            MagicMock(
                returncode=0,
                stdout=f"{tmp_project}/src/main.rs\n{tmp_project}/src/lib.rs",
            ),
            MagicMock(returncode=1, stderr="error[E0425]: cannot find value"),
            MagicMock(returncode=0),  # git checkout for rollback
        ]

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is False
        assert "compilation errors" in result.errors[0]

    def test_extract_method_not_supported(
        self, adapter: RustAnalyzerAdapter
    ) -> None:
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

    def test_inline_not_supported(self, adapter: RustAnalyzerAdapter) -> None:
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
    def test_rollback(
        self, mock_run: MagicMock, adapter: RustAnalyzerAdapter
    ) -> None:
        """Test rollback functionality."""
        mock_run.return_value = MagicMock(returncode=0)

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True,
            changes=[],
            errors=[],
            tool_used="rust-analyzer",
            dry_run=False,
        )

        assert adapter.rollback(result) is True
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "checkout" in call_args

    def test_get_capability(self, adapter: RustAnalyzerAdapter) -> None:
        """Test capability reporting."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="rust-analyzer 2024-01-15"
            )
            cap = adapter.get_capability()
            assert cap.tool_name == "RustAnalyzerAdapter"
            assert cap.languages == ["rust"]
            assert RefactorOperation.RENAME in cap.operations


class TestRustAnalyzerFindAndReplace:
    """Tests for the find-and-replace functionality."""

    @patch("subprocess.run")
    def test_no_occurrences_found(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test when no occurrences are found."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.rs").write_text("fn main() {}\n")

        adapter = RustAnalyzerAdapter(tmp_path)

        # Mock rust-analyzer availability
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="rust-analyzer 2024-01-15"),
            MagicMock(returncode=1, stdout=""),  # grep finds nothing
        ]

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="nonexistent_func",
            new_value="new_func",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is False
        assert "No occurrences found" in result.errors[0]

    @patch("subprocess.run")
    def test_rename_warnings(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test that rename includes appropriate warnings."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.rs").write_text("fn old_func() {}\n")

        adapter = RustAnalyzerAdapter(tmp_path)

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="rust-analyzer 2024-01-15"),
            MagicMock(returncode=0, stdout=f"{tmp_path}/src/main.rs"),
        ]

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        # The adapter warns that CLI rename may miss some references
        assert any("may miss some references" in w for w in result.warnings)
