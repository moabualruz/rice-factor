"""Unit tests for Rope adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.rope_adapter import (
    ROPE_AVAILABLE,
    DependencyRule,
    DependencyViolation,
    RopeAdapter,
)
from rice_factor.domain.ports.refactor import (
    RefactorOperation,
    RefactorRequest,
)


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary Python project directory."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Create a simple Python module
    (src_dir / "__init__.py").write_text("")
    (src_dir / "main.py").write_text(
        '''"""Main module."""


def old_func(x: int) -> int:
    """A simple function."""
    return x * 2


class OldClass:
    """A sample class."""

    def method_one(self, value: str) -> str:
        """First method."""
        return value.upper()

    def method_two(self, count: int) -> list[int]:
        """Second method."""
        return list(range(count))

    def _private_method(self) -> None:
        """Private method."""
        pass
'''
    )

    (src_dir / "utils.py").write_text(
        '''"""Utility module."""

from src.main import old_func


def helper() -> int:
    """Use old_func."""
    return old_func(5)
'''
    )

    # Create a module that violates dependency rules
    (src_dir / "adapters.py").write_text(
        '''"""Adapters module - should not import from domain."""

from src.domain import internal_func  # Violation!

def adapter_func():
    return internal_func()
'''
    )

    domain_dir = src_dir / "domain"
    domain_dir.mkdir()
    (domain_dir / "__init__.py").write_text("")
    (domain_dir / "internal.py").write_text(
        '''"""Domain internal module."""

def internal_func():
    return "internal"
'''
    )
    # Add the import to domain __init__
    (domain_dir / "__init__.py").write_text("from src.domain.internal import internal_func\n")

    return tmp_path


@pytest.fixture
def adapter(tmp_project: Path) -> RopeAdapter:
    """Create a Rope adapter for testing."""
    return RopeAdapter(tmp_project)


class TestRopeAdapterBasics:
    """Basic tests for RopeAdapter."""

    def test_supported_languages(self, adapter: RopeAdapter) -> None:
        """Test that Python is supported."""
        languages = adapter.get_supported_languages()
        assert "python" in languages

    def test_supported_operations(self, adapter: RopeAdapter) -> None:
        """Test that expected operations are supported."""
        operations = adapter.get_supported_operations()
        assert RefactorOperation.RENAME in operations
        assert RefactorOperation.MOVE in operations
        assert RefactorOperation.EXTRACT_METHOD in operations
        assert RefactorOperation.EXTRACT_VARIABLE in operations

    def test_availability(self, adapter: RopeAdapter) -> None:
        """Test availability check."""
        # This depends on whether rope is installed
        assert adapter.is_available() == ROPE_AVAILABLE

    def test_get_version(self, adapter: RopeAdapter) -> None:
        """Test version retrieval."""
        if ROPE_AVAILABLE:
            version = adapter.get_version()
            assert version is not None
        else:
            assert adapter.get_version() is None

    def test_get_capability(self, adapter: RopeAdapter) -> None:
        """Test capability reporting."""
        cap = adapter.get_capability()
        assert cap.tool_name == "RopeAdapter"
        assert "python" in cap.languages
        assert cap.is_available == ROPE_AVAILABLE


class TestRopeAdapterRename:
    """Tests for rename operations."""

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_rename_missing_new_value(self, adapter: RopeAdapter) -> None:
        """Test rename without new_value."""
        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            file_path="src/main.py",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "new_value is required" in result.errors[0]

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_rename_missing_file_path(self, adapter: RopeAdapter) -> None:
        """Test rename without file_path."""
        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "file_path is required" in result.errors[0]

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_rename_symbol_not_found(self, adapter: RopeAdapter) -> None:
        """Test rename when symbol not found."""
        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="nonexistent_func",
            new_value="new_name",
            file_path="src/main.py",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "not found" in result.errors[0].lower()

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_rename_dry_run(self, tmp_project: Path) -> None:
        """Test rename in dry-run mode."""
        adapter = RopeAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
            file_path="src/main.py",
            line=4,  # Line where old_func is defined
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        assert result.dry_run is True
        assert result.tool_used == "rope"

        # File should NOT be modified in dry-run
        main_py = (tmp_project / "src" / "main.py").read_text()
        assert "old_func" in main_py


class TestRopeAdapterMove:
    """Tests for move operations."""

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_move_missing_new_value(self, adapter: RopeAdapter) -> None:
        """Test move without new_value."""
        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="src/main.py",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "new_value" in result.errors[0].lower()

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_move_file_not_found(self, adapter: RopeAdapter) -> None:
        """Test move with non-existent source file."""
        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="nonexistent.py",
            new_value="new.py",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "not found" in result.errors[0].lower()


class TestRopeAdapterExtractMethod:
    """Tests for extract method operations."""

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_extract_method_missing_name(self, adapter: RopeAdapter) -> None:
        """Test extract method without new method name."""
        request = RefactorRequest(
            operation=RefactorOperation.EXTRACT_METHOD,
            target="some_code",
            file_path="src/main.py",
            line=5,
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "new_value" in result.errors[0].lower()

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_extract_method_missing_file(self, adapter: RopeAdapter) -> None:
        """Test extract method without file_path."""
        request = RefactorRequest(
            operation=RefactorOperation.EXTRACT_METHOD,
            target="some_code",
            new_value="extracted_method",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "file_path" in result.errors[0].lower()

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_extract_method_missing_line(self, adapter: RopeAdapter) -> None:
        """Test extract method without line number."""
        request = RefactorRequest(
            operation=RefactorOperation.EXTRACT_METHOD,
            target="some_code",
            new_value="extracted_method",
            file_path="src/main.py",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "line" in result.errors[0].lower()


class TestRopeAdapterExtractVariable:
    """Tests for extract variable operations."""

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_extract_variable_missing_name(self, adapter: RopeAdapter) -> None:
        """Test extract variable without new variable name."""
        request = RefactorRequest(
            operation=RefactorOperation.EXTRACT_VARIABLE,
            target="x * 2",
            file_path="src/main.py",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "new_value" in result.errors[0].lower()

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_extract_variable_missing_file(self, adapter: RopeAdapter) -> None:
        """Test extract variable without file_path."""
        request = RefactorRequest(
            operation=RefactorOperation.EXTRACT_VARIABLE,
            target="x * 2",
            new_value="result",
        )
        result = adapter.execute(request)
        assert result.success is False
        assert "file_path" in result.errors[0].lower()


class TestRopeAdapterExtractInterface:
    """Tests for extract interface operation."""

    def test_extract_interface_success(self, tmp_project: Path) -> None:
        """Test extracting a Protocol from a class."""
        adapter = RopeAdapter(tmp_project)

        result = adapter.extract_interface(
            file_path=Path("src/main.py"),
            class_name="OldClass",
            interface_name="OldClassProtocol",
        )

        assert result.success is True
        assert len(result.changes) == 1

        # Check generated protocol code
        protocol_code = result.changes[0].new_content
        assert "class OldClassProtocol(Protocol):" in protocol_code
        assert "def method_one" in protocol_code
        assert "def method_two" in protocol_code
        # Private methods should not be included
        assert "_private_method" not in protocol_code

    def test_extract_interface_with_method_filter(self, tmp_project: Path) -> None:
        """Test extracting interface with specific methods."""
        adapter = RopeAdapter(tmp_project)

        result = adapter.extract_interface(
            file_path=Path("src/main.py"),
            class_name="OldClass",
            interface_name="PartialProtocol",
            methods=["method_one"],
        )

        assert result.success is True
        protocol_code = result.changes[0].new_content
        assert "def method_one" in protocol_code
        assert "def method_two" not in protocol_code

    def test_extract_interface_class_not_found(self, tmp_project: Path) -> None:
        """Test extract interface when class not found."""
        adapter = RopeAdapter(tmp_project)

        result = adapter.extract_interface(
            file_path=Path("src/main.py"),
            class_name="NonexistentClass",
            interface_name="Protocol",
        )

        assert result.success is False
        assert "not found" in result.errors[0].lower()

    def test_extract_interface_file_not_found(self, tmp_project: Path) -> None:
        """Test extract interface when file not found."""
        adapter = RopeAdapter(tmp_project)

        result = adapter.extract_interface(
            file_path=Path("nonexistent.py"),
            class_name="SomeClass",
            interface_name="Protocol",
        )

        assert result.success is False


class TestRopeAdapterEnforceDependency:
    """Tests for enforce dependency operation."""

    def test_find_dependency_violations(self, tmp_project: Path) -> None:
        """Test finding dependency violations."""
        adapter = RopeAdapter(tmp_project)

        rule = DependencyRule(
            source_module="src.adapters",
            target_module="src.domain",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        # Should find the violation in adapters.py
        assert len(result.changes) > 0 or len(result.warnings) > 0

    def test_enforce_dependency_no_violations(self, tmp_project: Path) -> None:
        """Test when no violations exist."""
        adapter = RopeAdapter(tmp_project)

        rule = DependencyRule(
            source_module="src.main",
            target_module="src.nonexistent",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 0


class TestDependencyViolation:
    """Tests for DependencyViolation dataclass."""

    def test_create_violation(self) -> None:
        """Test creating a dependency violation."""
        violation = DependencyViolation(
            file_path="src/adapters.py",
            line=3,
            import_statement="from src.domain import internal_func",
            source_module="src.adapters",
            target_module="src.domain",
        )

        assert violation.file_path == "src/adapters.py"
        assert violation.line == 3
        assert violation.source_module == "src.adapters"
        assert violation.target_module == "src.domain"


class TestDependencyRule:
    """Tests for DependencyRule dataclass."""

    def test_create_rule(self) -> None:
        """Test creating a dependency rule."""
        rule = DependencyRule(
            source_module="adapters",
            target_module="domain",
            allow_transitive=False,
        )

        assert rule.source_module == "adapters"
        assert rule.target_module == "domain"
        assert rule.allow_transitive is False

    def test_default_transitive(self) -> None:
        """Test default transitive value."""
        rule = DependencyRule(
            source_module="a",
            target_module="b",
        )
        assert rule.allow_transitive is False


class TestRopeAdapterRollback:
    """Tests for rollback functionality."""

    @patch("subprocess.run")
    def test_rollback_success(
        self, mock_run: MagicMock, adapter: RopeAdapter
    ) -> None:
        """Test successful rollback."""
        mock_run.return_value = MagicMock(returncode=0)

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True,
            changes=[],
            errors=[],
            tool_used="rope",
            dry_run=False,
        )

        assert adapter.rollback(result) is True
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "checkout" in call_args

    @patch("subprocess.run")
    def test_rollback_failure(
        self, mock_run: MagicMock, adapter: RopeAdapter
    ) -> None:
        """Test rollback failure."""
        mock_run.side_effect = FileNotFoundError("git not found")

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True,
            changes=[],
            errors=[],
            tool_used="rope",
            dry_run=False,
        )

        assert adapter.rollback(result) is False


class TestRopeAdapterClose:
    """Tests for cleanup functionality."""

    def test_close(self, adapter: RopeAdapter) -> None:
        """Test closing the adapter."""
        # Should not raise even when project not initialized
        adapter.close()
        assert adapter._project is None

    @pytest.mark.skipif(not ROPE_AVAILABLE, reason="Rope not installed")
    def test_close_after_use(self, tmp_project: Path) -> None:
        """Test closing after using the adapter."""
        adapter = RopeAdapter(tmp_project)

        # Initialize the project
        _ = adapter._get_project()
        assert adapter._project is not None

        # Close should cleanup
        adapter.close()
        assert adapter._project is None


class TestRopeAdapterSymbolFinding:
    """Tests for symbol finding functionality."""

    def test_find_symbol_offset_simple(self, adapter: RopeAdapter) -> None:
        """Test finding symbol offset in content."""
        content = "def old_func():\n    pass\n"
        offset = adapter._find_symbol_offset(content, "old_func")
        assert offset == 4  # Position after "def "

    def test_find_symbol_offset_with_line(self, adapter: RopeAdapter) -> None:
        """Test finding symbol offset on specific line."""
        content = "x = 1\ndef old_func():\n    pass\n"
        # old_func is on line 2
        offset = adapter._find_symbol_offset(content, "old_func", line=2)
        assert offset > 0
        assert content[offset:offset + 8] == "old_func"

    def test_find_symbol_not_found(self, adapter: RopeAdapter) -> None:
        """Test when symbol not found."""
        content = "def some_func():\n    pass\n"
        offset = adapter._find_symbol_offset(content, "nonexistent")
        assert offset == -1


class TestRopeNotAvailable:
    """Tests for when Rope is not available."""

    @patch("rice_factor.adapters.refactoring.rope_adapter.ROPE_AVAILABLE", False)
    def test_execute_when_not_available(self, tmp_project: Path) -> None:
        """Test that execute returns error when Rope not available."""
        # Need to reimport to get patched value
        from rice_factor.adapters.refactoring.rope_adapter import RopeAdapter

        adapter = RopeAdapter(tmp_project)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="old_func",
            new_value="new_func",
            file_path="src/main.py",
        )

        result = adapter.execute(request)

        assert result.success is False
        assert "not installed" in result.errors[0].lower()
        assert result.tool_used == "rope"
