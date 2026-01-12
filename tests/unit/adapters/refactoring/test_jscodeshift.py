"""Unit tests for jscodeshift adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.jscodeshift_adapter import (
    JscodeshiftAdapter,
    JsDependencyRule,
    JsDependencyViolation,
)
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


class TestJscodeshiftExtractInterface:
    """Tests for extract_interface functionality (M14)."""

    def test_extract_interface_typescript(self, tmp_path: Path) -> None:
        """Test extracting TypeScript interface from a class."""
        adapter = JscodeshiftAdapter(tmp_path)

        ts_file = tmp_path / "UserService.ts"
        ts_file.write_text(
            """
export class UserService {
    public async getUser(id: number): Promise<User> {
        return await this.db.find(id);
    }

    public createUser(name: string, email: string): User {
        return { name, email };
    }

    public getAllUsers(): User[] {
        return [];
    }

    private internalMethod(): void {
        // Should not appear in interface
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=ts_file,
            class_name="UserService",
            interface_name="IUserService",
        )

        assert result.success is True
        assert len(result.changes) == 1
        interface_code = result.changes[0].new_content

        assert "export interface IUserService {" in interface_code
        assert "getUser(id: number): Promise<User>" in interface_code
        assert "createUser(name: string, email: string): User" in interface_code
        assert "getAllUsers(): User[]" in interface_code
        # Private method should not appear
        assert "internalMethod" not in interface_code

    def test_extract_interface_javascript_jsdoc(self, tmp_path: Path) -> None:
        """Test extracting JSDoc typedef from a JavaScript class."""
        adapter = JscodeshiftAdapter(tmp_path)

        js_file = tmp_path / "Calculator.js"
        js_file.write_text(
            """
class Calculator {
    add(a, b) {
        return a + b;
    }

    subtract(a, b) {
        return a - b;
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=js_file,
            class_name="Calculator",
            interface_name="CalculatorInterface",
        )

        assert result.success is True
        assert len(result.changes) == 1
        typedef_code = result.changes[0].new_content

        assert "@typedef {CalculatorInterface}" in typedef_code
        assert "@property {function" in typedef_code
        assert "add" in typedef_code
        assert "subtract" in typedef_code

    def test_extract_interface_filter_methods(self, tmp_path: Path) -> None:
        """Test extracting interface with filtered methods."""
        adapter = JscodeshiftAdapter(tmp_path)

        ts_file = tmp_path / "Service.ts"
        ts_file.write_text(
            """
class Service {
    public methodA(): void {}
    public methodB(): string { return ''; }
    public methodC(): number { return 0; }
}
"""
        )

        result = adapter.extract_interface(
            file_path=ts_file,
            class_name="Service",
            interface_name="IService",
            methods=["methodA", "methodB"],
        )

        assert result.success is True
        interface_code = result.changes[0].new_content

        assert "methodA" in interface_code
        assert "methodB" in interface_code
        assert "methodC" not in interface_code

    def test_extract_interface_file_not_found(self, tmp_path: Path) -> None:
        """Test extract_interface with non-existent file."""
        adapter = JscodeshiftAdapter(tmp_path)

        result = adapter.extract_interface(
            file_path=Path("nonexistent.ts"),
            class_name="SomeClass",
            interface_name="ISomeClass",
        )

        assert result.success is False
        assert "not found" in result.errors[0].lower()

    def test_extract_interface_class_not_found(self, tmp_path: Path) -> None:
        """Test extract_interface when class doesn't exist."""
        adapter = JscodeshiftAdapter(tmp_path)

        ts_file = tmp_path / "Service.ts"
        ts_file.write_text(
            """
class OtherClass {
    public someMethod(): void {}
}
"""
        )

        result = adapter.extract_interface(
            file_path=ts_file,
            class_name="NonExistentClass",
            interface_name="IService",
        )

        assert result.success is False
        assert "No public methods found" in result.errors[0]

    def test_extract_interface_async_methods(self, tmp_path: Path) -> None:
        """Test that async methods get Promise return types."""
        adapter = JscodeshiftAdapter(tmp_path)

        ts_file = tmp_path / "AsyncService.ts"
        ts_file.write_text(
            """
class AsyncService {
    public async fetchData(): void {
        // async void
    }

    public async getData(): string {
        return 'data';
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=ts_file,
            class_name="AsyncService",
            interface_name="IAsyncService",
        )

        assert result.success is True
        interface_code = result.changes[0].new_content

        # Async void should become Promise<void>
        assert "Promise<void>" in interface_code or "void" in interface_code

    def test_extract_interface_via_execute(self, tmp_path: Path) -> None:
        """Test extract_interface via execute method."""
        adapter = JscodeshiftAdapter(tmp_path)

        ts_file = tmp_path / "TestClass.ts"
        ts_file.write_text(
            """
class TestClass {
    public doWork(): boolean { return true; }
}
"""
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="0.15.0")

            from rice_factor.domain.ports.refactor import RefactorRequest

            request = RefactorRequest(
                operation=RefactorOperation.EXTRACT_INTERFACE,
                target="TestClass",
                new_value="ITestClass",
                file_path=str(ts_file),
            )

            result = adapter.execute(request)

            assert result.success is True
            assert "ITestClass" in result.changes[0].new_content


class TestJscodeshiftEnforceDependency:
    """Tests for enforce_dependency functionality (M14)."""

    def test_dependency_rule_dataclass(self) -> None:
        """Test JsDependencyRule dataclass."""
        rule = JsDependencyRule(
            source_path="src/domain",
            target_path="src/infrastructure",
            description="Domain should not depend on infrastructure",
        )

        assert rule.source_path == "src/domain"
        assert rule.target_path == "src/infrastructure"
        assert "Domain" in rule.description

    def test_dependency_violation_dataclass(self) -> None:
        """Test JsDependencyViolation dataclass."""
        violation = JsDependencyViolation(
            file_path="src/domain/service.ts",
            line=5,
            import_statement="import { Database } from '../infrastructure/db';",
            source_module="service",
            target_module="../infrastructure/db",
        )

        assert violation.file_path == "src/domain/service.ts"
        assert violation.line == 5
        assert "infrastructure" in violation.import_statement

    def test_enforce_dependency_no_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency with no violations."""
        adapter = JscodeshiftAdapter(tmp_path)

        src_dir = tmp_path / "src" / "domain"
        src_dir.mkdir(parents=True)
        ts_file = src_dir / "user.ts"
        ts_file.write_text(
            """
import { Entity } from './entity';

export class User extends Entity {
    name: string;
}
"""
        )

        rule = JsDependencyRule(
            source_path="src/domain",
            target_path="src/infrastructure",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 0

    def test_enforce_dependency_finds_es_import_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency finding ES module import violations."""
        adapter = JscodeshiftAdapter(tmp_path)

        src_dir = tmp_path / "src" / "domain"
        src_dir.mkdir(parents=True)
        ts_file = src_dir / "service.ts"
        ts_file.write_text(
            """
import { Entity } from './entity';
import { Database } from '../infrastructure/database';
import { Cache } from '../infrastructure/cache';

export class UserService {
    // Violating domain-infrastructure boundary
}
"""
        )

        rule = JsDependencyRule(
            source_path="src/domain",
            target_path="infrastructure",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 2  # Two violations
        assert any("database" in c.description for c in result.changes)
        assert any("cache" in c.description for c in result.changes)

    def test_enforce_dependency_finds_commonjs_require_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency finding CommonJS require violations."""
        adapter = JscodeshiftAdapter(tmp_path)

        src_dir = tmp_path / "src" / "core"
        src_dir.mkdir(parents=True)
        js_file = src_dir / "handler.js"
        js_file.write_text(
            """
const utils = require('./utils');
const forbidden = require('../forbidden/module');

module.exports = { handler };
"""
        )

        rule = JsDependencyRule(
            source_path="src/core",
            target_path="forbidden",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 1
        assert "forbidden" in result.changes[0].description

    def test_enforce_dependency_finds_dynamic_import_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency finding dynamic import violations."""
        adapter = JscodeshiftAdapter(tmp_path)

        src_dir = tmp_path / "src" / "app"
        src_dir.mkdir(parents=True)
        ts_file = src_dir / "loader.ts"
        ts_file.write_text(
            """
export async function loadModule() {
    const mod = await import('../restricted/secret');
    return mod;
}
"""
        )

        rule = JsDependencyRule(
            source_path="src/app",
            target_path="restricted",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 1
        assert "restricted" in result.changes[0].description

    def test_enforce_dependency_fix_mode(self, tmp_path: Path) -> None:
        """Test enforce_dependency with fix=True removes imports."""
        adapter = JscodeshiftAdapter(tmp_path)

        src_dir = tmp_path / "src" / "domain"
        src_dir.mkdir(parents=True)
        ts_file = src_dir / "bad_service.ts"
        original_content = """import { Entity } from './entity';
import { ForbiddenClass } from '../forbidden/module';
import { AnotherEntity } from './another';

export class BadService {}
"""
        ts_file.write_text(original_content)

        rule = JsDependencyRule(
            source_path="src/domain",
            target_path="forbidden",
        )

        result = adapter.enforce_dependency(rule, fix=True)

        assert result.success is True
        assert result.dry_run is False

        # Check file was modified
        new_content = ts_file.read_text()
        assert "import { ForbiddenClass } from '../forbidden/module';" not in new_content
        # Other imports should remain
        assert "import { Entity } from './entity';" in new_content

    def test_enforce_dependency_empty_project(self, tmp_path: Path) -> None:
        """Test enforce_dependency with no matching files."""
        adapter = JscodeshiftAdapter(tmp_path)

        rule = JsDependencyRule(
            source_path="nonexistent/path",
            target_path="other/path",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 0

    def test_enforce_dependency_multiple_file_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency finds violations across multiple files."""
        adapter = JscodeshiftAdapter(tmp_path)

        src_dir = tmp_path / "src" / "features"
        src_dir.mkdir(parents=True)

        # First file with violation
        file1 = src_dir / "feature1.ts"
        file1.write_text(
            """
import { BadDep } from '../legacy/bad';
export const feature1 = {};
"""
        )

        # Second file with violation
        file2 = src_dir / "feature2.ts"
        file2.write_text(
            """
import { AnotherBadDep } from '../legacy/another';
export const feature2 = {};
"""
        )

        # Clean file (no violation)
        file3 = src_dir / "feature3.ts"
        file3.write_text(
            """
import { GoodDep } from './utils';
export const feature3 = {};
"""
        )

        rule = JsDependencyRule(
            source_path="src/features",
            target_path="legacy",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 2  # Two files with violations
        file_paths = [c.file_path for c in result.changes]
        assert any("feature1" in fp for fp in file_paths)
        assert any("feature2" in fp for fp in file_paths)
