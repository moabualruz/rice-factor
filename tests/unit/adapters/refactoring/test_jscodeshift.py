"""Unit tests for jscodeshift adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.jscodeshift_adapter import JscodeshiftAdapter
from rice_factor.domain.ports.refactor import (
    RefactorOperation,
    RefactorRequest,
)


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary JS/TS project directory."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "index.ts").write_text("export function oldFunc() {}\n")
    (src_dir / "app.tsx").write_text("import { oldFunc } from './index';\n")
    return tmp_path


@pytest.fixture
def adapter(tmp_project: Path) -> JscodeshiftAdapter:
    """Create a jscodeshift adapter for testing."""
    return JscodeshiftAdapter(tmp_project)


class TestJscodeshiftAdapter:
    """Tests for JscodeshiftAdapter."""

    def test_supported_languages(self, adapter: JscodeshiftAdapter) -> None:
        """Test that JS/TS languages are supported."""
        languages = adapter.get_supported_languages()
        assert "javascript" in languages
        assert "typescript" in languages
        assert "jsx" in languages
        assert "tsx" in languages

    def test_supported_operations(self, adapter: JscodeshiftAdapter) -> None:
        """Test that expected operations are supported."""
        operations = adapter.get_supported_operations()
        assert RefactorOperation.RENAME in operations
        assert RefactorOperation.EXTRACT_METHOD in operations
        assert RefactorOperation.MOVE in operations

    @patch("subprocess.run")
    def test_is_available_when_installed(
        self, mock_run: MagicMock, adapter: JscodeshiftAdapter
    ) -> None:
        """Test availability when jscodeshift is installed."""
        mock_run.return_value = MagicMock(returncode=0, stdout="0.15.0")
        assert adapter.is_available() is True

    @patch("subprocess.run")
    def test_is_not_available_when_not_installed(
        self, mock_run: MagicMock, adapter: JscodeshiftAdapter
    ) -> None:
        """Test availability when jscodeshift is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert adapter.is_available() is False

    @patch("subprocess.run")
    def test_get_version(
        self, mock_run: MagicMock, adapter: JscodeshiftAdapter
    ) -> None:
        """Test version extraction."""
        mock_run.return_value = MagicMock(returncode=0, stdout="0.15.2")
        version = adapter.get_version()
        assert version == "0.15.2"

    @patch("subprocess.run")
    def test_execute_not_available(
        self, mock_run: MagicMock, adapter: JscodeshiftAdapter
    ) -> None:
        """Test execute when jscodeshift is not available."""
        mock_run.side_effect = FileNotFoundError()

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="oldFunc",
            new_value="newFunc",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "not installed" in result.errors[0]

    @patch("subprocess.run")
    def test_rename_missing_new_value(
        self, mock_run: MagicMock, adapter: JscodeshiftAdapter
    ) -> None:
        """Test rename without new_value."""
        mock_run.return_value = MagicMock(returncode=0)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="oldFunc",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "new_value is required" in result.errors[0]

    @patch("subprocess.run")
    def test_rename_dry_run(
        self, mock_run: MagicMock, tmp_project: Path
    ) -> None:
        """Test rename in dry-run mode."""
        adapter = JscodeshiftAdapter(tmp_project)

        # Mock jscodeshift availability and execution
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="0.15.0"),  # version check
            MagicMock(returncode=0, stdout="Modified: src/index.ts", stderr=""),
        ]

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="oldFunc",
            new_value="newFunc",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        assert result.tool_used == "jscodeshift"
        assert result.dry_run is True

        # Check that dry-run flag was passed
        calls = mock_run.call_args_list
        transform_call = calls[-1]
        args = transform_call[0][0] if transform_call[0] else []
        assert "--dry" in args

    @patch("subprocess.run")
    def test_rename_apply(
        self, mock_run: MagicMock, tmp_project: Path
    ) -> None:
        """Test rename with apply."""
        adapter = JscodeshiftAdapter(tmp_project)

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="0.15.0"),
            MagicMock(returncode=0, stdout="Modified files", stderr=""),
        ]

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="oldFunc",
            new_value="newFunc",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert result.dry_run is False

        # Check that dry-run flag was NOT passed
        calls = mock_run.call_args_list
        transform_call = calls[-1]
        args = transform_call[0][0] if transform_call[0] else []
        assert "--dry" not in args

    @patch("subprocess.run")
    def test_rename_transform_code(
        self, mock_run: MagicMock, adapter: JscodeshiftAdapter
    ) -> None:
        """Test that rename generates correct transform code."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="oldFunc",
            new_value="newFunc",
        )

        adapter.execute(request, dry_run=True)

        # Check the input (transform code) passed to subprocess
        calls = mock_run.call_args_list
        transform_call = calls[-1]
        input_code = transform_call[1].get("input", "")

        assert "oldFunc" in input_code
        assert "newFunc" in input_code
        assert "j.Identifier" in input_code

    @patch("subprocess.run")
    def test_rename_error_handling(
        self, mock_run: MagicMock, adapter: JscodeshiftAdapter
    ) -> None:
        """Test error handling during rename."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="0.15.0"),
            MagicMock(returncode=0, stdout="", stderr="ERR: syntax error"),
        ]

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="oldFunc",
            new_value="newFunc",
        )

        result = adapter.execute(request)

        assert result.success is False
        assert len(result.errors) > 0

    @patch("subprocess.run")
    def test_rename_timeout(
        self, mock_run: MagicMock, adapter: JscodeshiftAdapter
    ) -> None:
        """Test timeout handling."""
        import subprocess

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="0.15.0"),
            subprocess.TimeoutExpired("npx", 120),
        ]

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="oldFunc",
            new_value="newFunc",
        )

        result = adapter.execute(request)

        assert result.success is False
        assert "timed out" in result.errors[0]

    def test_extract_method_not_supported(
        self, adapter: JscodeshiftAdapter
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
            assert "selection context" in result.errors[0]

    @patch("subprocess.run")
    def test_rollback(
        self, mock_run: MagicMock, adapter: JscodeshiftAdapter
    ) -> None:
        """Test rollback functionality."""
        mock_run.return_value = MagicMock(returncode=0)

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True,
            changes=[],
            errors=[],
            tool_used="jscodeshift",
            dry_run=False,
        )

        assert adapter.rollback(result) is True
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "checkout" in call_args

    def test_get_capability(self, adapter: JscodeshiftAdapter) -> None:
        """Test capability reporting."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="0.15.0")
            cap = adapter.get_capability()
            assert cap.tool_name == "JscodeshiftAdapter"
            assert "typescript" in cap.languages
            assert RefactorOperation.RENAME in cap.operations


class TestJscodeshiftMoveOperation:
    """Tests for move/file rename operations."""

    @patch("subprocess.run")
    def test_move_missing_new_value(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test move without new_value."""
        adapter = JscodeshiftAdapter(tmp_path)
        mock_run.return_value = MagicMock(returncode=0)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/old.ts",
        )

        result = adapter.execute(request)
        assert result.success is False
        assert "new_value" in result.errors[0]

    @patch("subprocess.run")
    def test_move_file_not_found(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test move with non-existent source file."""
        adapter = JscodeshiftAdapter(tmp_path)
        mock_run.return_value = MagicMock(returncode=0)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="nonexistent.ts",
            new_value="new.ts",
        )

        result = adapter.execute(request)
        assert result.success is False
        assert "not found" in result.errors[0]

    @patch("subprocess.run")
    def test_move_dry_run(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test move in dry-run mode."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        old_file = src_dir / "old.ts"
        old_file.write_text("export const x = 1;")

        adapter = JscodeshiftAdapter(tmp_path)

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="0.15.0"),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/old.ts",
            new_value="src/new.ts",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        assert result.dry_run is True
        # File should NOT be moved in dry-run
        assert old_file.exists()

    @patch("subprocess.run")
    def test_move_apply(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test move with apply."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        old_file = src_dir / "old.ts"
        old_file.write_text("export const x = 1;")

        adapter = JscodeshiftAdapter(tmp_path)

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="0.15.0"),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/old.ts",
            new_value="src/new.ts",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        # File should be moved
        assert not old_file.exists()
        assert (src_dir / "new.ts").exists()


class TestJscodeshiftParserDetection:
    """Tests for parser detection."""

    def test_detect_tsx_parser(self, tmp_path: Path) -> None:
        """Test that TSX parser is detected for TSX files."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "app.tsx").write_text("const App = () => <div />;")

        adapter = JscodeshiftAdapter(tmp_path)
        files = [str(src_dir / "app.tsx")]

        parser = adapter._detect_parser(files)
        assert parser == "tsx"

    def test_detect_ts_parser(self, tmp_path: Path) -> None:
        """Test that TS parser is detected for TS files."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "util.ts").write_text("export function foo(): void {}")

        adapter = JscodeshiftAdapter(tmp_path)
        files = [str(src_dir / "util.ts")]

        parser = adapter._detect_parser(files)
        assert parser == "ts"

    def test_detect_babel_parser(self, tmp_path: Path) -> None:
        """Test that Babel parser is detected for JS files."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "index.js").write_text("export function foo() {}")

        adapter = JscodeshiftAdapter(tmp_path)
        files = [str(src_dir / "index.js")]

        parser = adapter._detect_parser(files)
        assert parser == "babel"


class TestJscodeshiftFileDiscovery:
    """Tests for file discovery."""

    def test_excludes_node_modules(self, tmp_path: Path) -> None:
        """Test that node_modules is excluded."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "index.ts").write_text("export const x = 1;")

        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "pkg.js").write_text("module.exports = {};")

        adapter = JscodeshiftAdapter(tmp_path)
        files = adapter._get_all_js_files()

        # Convert to Path for cross-platform checking
        file_paths = [Path(f) for f in files]
        assert any(f.name == "index.ts" for f in file_paths)
        assert not any("node_modules" in f.parts for f in file_paths)

    def test_excludes_dist(self, tmp_path: Path) -> None:
        """Test that dist directory is excluded."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "index.ts").write_text("export const x = 1;")

        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        (dist_dir / "index.js").write_text("exports.x = 1;")

        adapter = JscodeshiftAdapter(tmp_path)
        files = adapter._get_all_js_files()

        # Convert to Path for cross-platform checking
        file_paths = [Path(f) for f in files]
        assert any("src" in f.parts for f in file_paths)
        assert not any("dist" in f.parts for f in file_paths)
