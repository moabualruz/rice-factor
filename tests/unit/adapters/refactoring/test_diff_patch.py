"""Unit tests for diff/patch adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.diff_patch_adapter import DiffPatchAdapter
from rice_factor.domain.ports.refactor import (
    RefactorOperation,
    RefactorRequest,
)


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("def old_func():\n    pass\n")
    (src_dir / "utils.py").write_text("from main import old_func\n")
    return tmp_path


@pytest.fixture
def adapter(tmp_project: Path) -> DiffPatchAdapter:
    """Create a diff/patch adapter for testing."""
    return DiffPatchAdapter(tmp_project)


class TestDiffPatchAdapter:
    """Tests for DiffPatchAdapter."""

    def test_supported_languages(self, adapter: DiffPatchAdapter) -> None:
        """Test that all languages are supported (wildcard)."""
        languages = adapter.get_supported_languages()
        assert "*" in languages

    def test_supported_operations(self, adapter: DiffPatchAdapter) -> None:
        """Test that expected operations are supported."""
        operations = adapter.get_supported_operations()
        assert RefactorOperation.RENAME in operations
        assert RefactorOperation.MOVE in operations

    def test_always_available(self, adapter: DiffPatchAdapter) -> None:
        """Test that adapter is always available."""
        assert adapter.is_available() is True

    def test_get_version(self, adapter: DiffPatchAdapter) -> None:
        """Test version reporting."""
        assert adapter.get_version() == "1.0.0"

    def test_rename_missing_new_value(self, adapter: DiffPatchAdapter) -> None:
        """Test rename without new_value."""
        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "new_value is required" in result.errors[0]

    def test_rename_dry_run(self, tmp_project: Path) -> None:
        """Test rename in dry-run mode."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        assert result.dry_run is True
        assert len(result.changes) == 2  # main.py and utils.py

        # Files should NOT be modified
        main_py = (tmp_project / "src" / "main.py").read_text()
        assert "old_func" in main_py

    def test_rename_apply(self, tmp_project: Path) -> None:
        """Test rename with apply."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert result.dry_run is False

        # Files should be modified
        main_py = (tmp_project / "src" / "main.py").read_text()
        assert "new_func" in main_py
        assert "old_func" not in main_py

        utils_py = (tmp_project / "src" / "utils.py").read_text()
        assert "new_func" in utils_py

    def test_rename_specific_file(self, tmp_project: Path) -> None:
        """Test rename targeting a specific file."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
            file_path="src/main.py",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        # Should only change main.py, not utils.py
        assert len(result.changes) == 1
        assert "main.py" in result.changes[0].file_path

    def test_rename_word_boundary(self, tmp_project: Path) -> None:
        """Test that rename respects word boundaries."""
        # Create file with similar names
        src = tmp_project / "src" / "test.py"
        src.write_text("old_func\nold_func_helper\nmy_old_func\n")

        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
            file_path="src/test.py",
        )

        result = adapter.execute(request, dry_run=False)

        content = src.read_text()
        assert "new_func\n" in content
        # These should NOT be changed (partial matches)
        assert "old_func_helper" in content
        assert "my_old_func" in content

    def test_rename_no_occurrences(self, tmp_project: Path) -> None:
        """Test rename when no occurrences found."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="nonexistent",
            new_value="new_name",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True  # Not an error, just no changes
        assert len(result.changes) == 0

    def test_rename_warnings(self, tmp_project: Path) -> None:
        """Test that rename includes appropriate warnings."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
        )

        result = adapter.execute(request, dry_run=True)

        assert len(result.warnings) > 0
        assert any("text-based" in w.lower() for w in result.warnings)

    def test_move_missing_new_value(self, adapter: DiffPatchAdapter) -> None:
        """Test move without new_value."""
        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/main.py",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "new_value" in result.errors[0]

    def test_move_file_not_found(self, adapter: DiffPatchAdapter) -> None:
        """Test move with non-existent source file."""
        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="nonexistent.py",
            new_value="new.py",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "not found" in result.errors[0]

    def test_move_destination_exists(self, tmp_project: Path) -> None:
        """Test move when destination already exists."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/main.py",
            new_value="src/utils.py",  # Already exists
        )

        result = adapter.execute(request)
        assert result.success is False
        assert "already exists" in result.errors[0]

    def test_move_dry_run(self, tmp_project: Path) -> None:
        """Test move in dry-run mode."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/main.py",
            new_value="src/new_main.py",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        assert result.dry_run is True
        # File should NOT be moved
        assert (tmp_project / "src" / "main.py").exists()
        assert not (tmp_project / "src" / "new_main.py").exists()

    def test_move_apply(self, tmp_project: Path) -> None:
        """Test move with apply."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/main.py",
            new_value="src/new_main.py",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert result.dry_run is False
        # File should be moved
        assert not (tmp_project / "src" / "main.py").exists()
        assert (tmp_project / "src" / "new_main.py").exists()

    def test_move_creates_directory(self, tmp_project: Path) -> None:
        """Test that move creates destination directory if needed."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/main.py",
            new_value="new_dir/main.py",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert (tmp_project / "new_dir" / "main.py").exists()

    def test_move_warnings(self, tmp_project: Path) -> None:
        """Test that move includes appropriate warnings."""
        adapter = DiffPatchAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/main.py",
            new_value="src/new_main.py",
        )

        result = adapter.execute(request, dry_run=True)

        assert len(result.warnings) > 0
        assert any("import" in w.lower() for w in result.warnings)

    @patch("subprocess.run")
    def test_rollback(
        self, mock_run: MagicMock, adapter: DiffPatchAdapter
    ) -> None:
        """Test rollback functionality."""
        mock_run.return_value = MagicMock(returncode=0)

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True,
            changes=[],
            errors=[],
            tool_used="diff-patch",
            dry_run=False,
        )

        assert adapter.rollback(result) is True
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "checkout" in call_args

    def test_unsupported_operation(self, adapter: DiffPatchAdapter) -> None:
        """Test unsupported operation handling."""
        request = RefactorRequest(
            operation=RefactorOperation.EXTRACT_METHOD,
            target="some_code",
        )

        result = adapter.execute(request)
        assert result.success is False
        assert "not supported" in result.errors[0]

    def test_get_capability(self, adapter: DiffPatchAdapter) -> None:
        """Test capability reporting."""
        cap = adapter.get_capability()
        assert cap.tool_name == "DiffPatchAdapter"
        assert "*" in cap.languages
        assert cap.is_available is True


class TestDiffPatchFileDiscovery:
    """Tests for file discovery."""

    def test_finds_python_files(self, tmp_path: Path) -> None:
        """Test that Python files are found."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("target_text")
        (src / "other.txt").write_text("target_text")

        adapter = DiffPatchAdapter(tmp_path)
        files = adapter._find_files_containing("target_text")

        paths = [str(f) for f in files]
        assert any("main.py" in p for p in paths)
        # .txt is not in the extension list
        assert not any("other.txt" in p for p in paths)

    def test_excludes_node_modules(self, tmp_path: Path) -> None:
        """Test that node_modules is excluded."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.js").write_text("target_text")

        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "pkg.js").write_text("target_text")

        adapter = DiffPatchAdapter(tmp_path)
        files = adapter._find_files_containing("target_text")

        # Check using Path.parts to be cross-platform
        assert any(f.name == "main.js" for f in files)
        assert not any("node_modules" in f.parts for f in files)

    def test_excludes_venv(self, tmp_path: Path) -> None:
        """Test that venv directories are excluded."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("target_text")

        venv = tmp_path / ".venv"
        venv.mkdir()
        venv_lib = venv / "lib"
        venv_lib.mkdir()
        (venv_lib / "pkg.py").write_text("target_text")

        adapter = DiffPatchAdapter(tmp_path)
        files = adapter._find_files_containing("target_text")

        paths = [str(f) for f in files]
        assert any("main.py" in p for p in paths)
        assert not any(".venv" in p for p in paths)
