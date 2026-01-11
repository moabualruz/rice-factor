"""Unit tests for Rector adapter (PHP refactoring)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.rector_adapter import (
    PhpDependencyRule,
    PhpDependencyViolation,
    RectorAdapter,
)
from rice_factor.domain.ports.refactor import RefactorOperation, RefactorRequest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def adapter(tmp_project: Path) -> RectorAdapter:
    """Create a Rector adapter for testing."""
    return RectorAdapter(tmp_project)


class TestRectorAdapter:
    """Tests for RectorAdapter basic functionality."""

    def test_supported_languages(self, adapter: RectorAdapter) -> None:
        """Test that PHP is supported."""
        languages = adapter.get_supported_languages()
        assert "php" in languages

    def test_supported_operations(self, adapter: RectorAdapter) -> None:
        """Test that expected operations are supported."""
        operations = adapter.get_supported_operations()
        assert RefactorOperation.RENAME in operations
        assert RefactorOperation.MOVE in operations
        assert RefactorOperation.EXTRACT_INTERFACE in operations

    def test_not_available_without_php(self, adapter: RectorAdapter) -> None:
        """Test that adapter is not available without PHP CLI."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("php not found")
            assert adapter.is_available() is False

    @patch("subprocess.run")
    def test_available_with_php_and_composer_json(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: RectorAdapter,
    ) -> None:
        """Test that adapter is available with PHP and composer.json."""
        mock_run.return_value = MagicMock(returncode=0, stdout="PHP 8.2.0\n")

        # Create a composer.json
        composer = tmp_project / "composer.json"
        composer.write_text('{"name": "test/project"}')

        assert adapter.is_available() is True

    @patch("subprocess.run")
    def test_available_with_php_files(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: RectorAdapter,
    ) -> None:
        """Test that adapter is available with .php files."""
        mock_run.return_value = MagicMock(returncode=0, stdout="PHP 8.2.0\n")

        # Create a PHP file
        php_file = tmp_project / "index.php"
        php_file.write_text("<?php echo 'hello'; ?>")

        assert adapter.is_available() is True

    def test_execute_not_available(self, adapter: RectorAdapter) -> None:
        """Test execute when PHP is not available."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            request = RefactorRequest(
                operation=RefactorOperation.RENAME,
                target="OldClass",
                new_value="NewClass",
            )
            result = adapter.execute(request, dry_run=True)

            assert result.success is False
            assert "not available" in result.errors[0]

    @patch("subprocess.run")
    def test_get_version(
        self,
        mock_run: MagicMock,
        adapter: RectorAdapter,
    ) -> None:
        """Test version detection."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="PHP 8.2.0 (cli) (built: Dec  6 2022 15:31:23)\n"
        )

        version = adapter.get_version()
        assert "PHP 8.2.0" in version

    def test_get_capability(
        self, tmp_project: Path, adapter: RectorAdapter
    ) -> None:
        """Test capability reporting."""
        cap = adapter.get_capability()
        assert cap.tool_name == "RectorAdapter"
        assert "php" in cap.languages
        assert RefactorOperation.RENAME in cap.operations


class TestRectorRename:
    """Tests for rename operations."""

    @patch("subprocess.run")
    def test_rename_manual(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test manual rename in PHP files."""
        mock_run.return_value = MagicMock(returncode=0, stdout="PHP 8.2.0")

        # Create test files
        composer = tmp_path / "composer.json"
        composer.write_text('{"name": "test"}')

        php_file = tmp_path / "Service.php"
        php_file.write_text(
            """<?php

namespace App;

class OldClass
{
    public function doWork()
    {
        return 'OldClass working';
    }
}
"""
        )

        adapter = RectorAdapter(tmp_path)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="OldClass",
            new_value="NewClass",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert len(result.changes) == 1

        # Check file was modified
        new_content = php_file.read_text()
        assert "NewClass" in new_content
        assert "OldClass" not in new_content


class TestRectorMove:
    """Tests for move/namespace operations."""

    @patch("subprocess.run")
    def test_move_namespace(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test namespace change operation."""
        mock_run.return_value = MagicMock(returncode=0, stdout="PHP 8.2.0")

        # Create test files
        composer = tmp_path / "composer.json"
        composer.write_text('{"name": "test"}')

        php_file = tmp_path / "Service.php"
        php_file.write_text(
            """<?php

namespace App\\OldNamespace;

use App\\OldNamespace\\Helper;

class Service
{
    public function work()
    {
        return new \\App\\OldNamespace\\Other();
    }
}
"""
        )

        adapter = RectorAdapter(tmp_path)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="App\\OldNamespace",
            new_value="App\\NewNamespace",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert len(result.changes) == 1

        new_content = php_file.read_text()
        assert "namespace App\\NewNamespace;" in new_content
        assert "use App\\NewNamespace\\Helper;" in new_content


class TestRectorExtractInterface:
    """Tests for extract_interface functionality."""

    def test_extract_interface_basic(self, tmp_path: Path) -> None:
        """Test extracting interface from a PHP class."""
        adapter = RectorAdapter(tmp_path)

        php_file = tmp_path / "UserService.php"
        php_file.write_text(
            """<?php

namespace App\\Services;

class UserService
{
    public function getUserName(int $id): string
    {
        return "User " . $id;
    }

    public function createUser(string $name, string $email): void
    {
        // Implementation
    }

    public function getAllUsers(): array
    {
        return [];
    }

    private function internalMethod(): void
    {
        // Should not appear in interface
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=php_file,
            class_name="UserService",
            interface_name="UserServiceInterface",
        )

        assert result.success is True
        assert len(result.changes) == 1
        interface_code = result.changes[0].new_content

        assert "namespace App\\Services;" in interface_code
        assert "interface UserServiceInterface" in interface_code
        assert "public function getUserName(int $id): string;" in interface_code
        assert "public function createUser(string $name, string $email): void;" in interface_code
        assert "public function getAllUsers(): array;" in interface_code
        # Private method should not appear
        assert "internalMethod" not in interface_code

    def test_extract_interface_filter_methods(self, tmp_path: Path) -> None:
        """Test extracting interface with filtered methods."""
        adapter = RectorAdapter(tmp_path)

        php_file = tmp_path / "Calculator.php"
        php_file.write_text(
            """<?php

namespace Math;

class Calculator
{
    public function add(int $a, int $b): int
    {
        return $a + $b;
    }

    public function subtract(int $a, int $b): int
    {
        return $a - $b;
    }

    public function multiply(int $a, int $b): int
    {
        return $a * $b;
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=php_file,
            class_name="Calculator",
            interface_name="CalculatorInterface",
            methods=["add", "subtract"],
        )

        assert result.success is True
        interface_code = result.changes[0].new_content

        assert "public function add(int $a, int $b): int;" in interface_code
        assert "public function subtract(int $a, int $b): int;" in interface_code
        assert "multiply" not in interface_code

    def test_extract_interface_file_not_found(self, tmp_path: Path) -> None:
        """Test extract_interface with non-existent file."""
        adapter = RectorAdapter(tmp_path)

        result = adapter.extract_interface(
            file_path=Path("nonexistent.php"),
            class_name="SomeClass",
            interface_name="SomeInterface",
        )

        assert result.success is False
        assert "not found" in result.errors[0].lower()

    def test_extract_interface_class_not_found(self, tmp_path: Path) -> None:
        """Test extract_interface with non-existent class."""
        adapter = RectorAdapter(tmp_path)

        php_file = tmp_path / "Service.php"
        php_file.write_text(
            """<?php

namespace App;

class OtherClass
{
    public function someMethod(): void
    {
        // do something
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=php_file,
            class_name="NonExistentClass",
            interface_name="ServiceInterface",
        )

        assert result.success is False
        assert "No public methods found" in result.errors[0]

    def test_extract_interface_no_return_type(self, tmp_path: Path) -> None:
        """Test extracting methods without return types."""
        adapter = RectorAdapter(tmp_path)

        php_file = tmp_path / "LegacyService.php"
        php_file.write_text(
            """<?php

namespace App;

class LegacyService
{
    public function legacyMethod($param)
    {
        return $param;
    }

    public function typedMethod(string $name): string
    {
        return $name;
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=php_file,
            class_name="LegacyService",
            interface_name="LegacyServiceInterface",
        )

        assert result.success is True
        interface_code = result.changes[0].new_content

        # Both methods should appear
        assert "public function legacyMethod($param);" in interface_code
        assert "public function typedMethod(string $name): string;" in interface_code


class TestRectorEnforceDependency:
    """Tests for enforce_dependency functionality."""

    def test_dependency_rule_dataclass(self) -> None:
        """Test PhpDependencyRule dataclass."""
        rule = PhpDependencyRule(
            source_namespace="App\\Domain",
            target_namespace="App\\Infrastructure",
            description="Domain should not depend on infrastructure",
        )

        assert rule.source_namespace == "App\\Domain"
        assert rule.target_namespace == "App\\Infrastructure"
        assert rule.description == "Domain should not depend on infrastructure"

    def test_dependency_violation_dataclass(self) -> None:
        """Test PhpDependencyViolation dataclass."""
        violation = PhpDependencyViolation(
            file_path="Service.php",
            line=5,
            use_statement="use App\\Forbidden\\Helper;",
            source_class="Service",
            target_namespace="App\\Forbidden\\Helper",
        )

        assert violation.file_path == "Service.php"
        assert violation.line == 5
        assert "Forbidden" in violation.use_statement

    def test_enforce_dependency_no_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency with no violations."""
        adapter = RectorAdapter(tmp_path)

        (tmp_path / "Domain").mkdir()
        php_file = tmp_path / "Domain" / "UserService.php"
        php_file.write_text(
            """<?php

namespace App\\Domain;

use App\\Domain\\Models\\User;

class UserService
{
    public function getUser(): ?User
    {
        return null;
    }
}
"""
        )

        rule = PhpDependencyRule(
            source_namespace="App\\Domain",
            target_namespace="App\\Infrastructure",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 0

    def test_enforce_dependency_finds_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency finding violations."""
        adapter = RectorAdapter(tmp_path)

        (tmp_path / "Domain").mkdir()
        php_file = tmp_path / "Domain" / "UserService.php"
        php_file.write_text(
            """<?php

namespace App\\Domain;

use App\\Infrastructure\\Database;
use App\\Infrastructure\\Cache;

class UserService
{
    // Violating domain-infrastructure boundary
}
"""
        )

        rule = PhpDependencyRule(
            source_namespace="App\\Domain",
            target_namespace="App\\Infrastructure",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True  # Operation succeeded
        assert len(result.changes) == 2  # Two violations
        assert any("Database" in c.description for c in result.changes)
        assert any("Cache" in c.description for c in result.changes)

    def test_enforce_dependency_fix_mode(self, tmp_path: Path) -> None:
        """Test enforce_dependency with fix=True removes use statements."""
        adapter = RectorAdapter(tmp_path)

        (tmp_path / "Domain").mkdir()
        php_file = tmp_path / "Domain" / "BadService.php"
        original_content = """<?php

namespace App\\Domain;

use JsonSerializable;
use App\\Forbidden\\BadClass;
use App\\Domain\\Models\\User;

class BadService
{
}
"""
        php_file.write_text(original_content)

        rule = PhpDependencyRule(
            source_namespace="App\\Domain",
            target_namespace="App\\Forbidden",
        )

        result = adapter.enforce_dependency(rule, fix=True)

        assert result.success is True
        assert result.dry_run is False

        # Check file was modified
        new_content = php_file.read_text()
        assert "use App\\Forbidden\\BadClass;" not in new_content
        # Other use statements should remain
        assert "use JsonSerializable;" in new_content

    def test_enforce_dependency_empty_project(self, tmp_path: Path) -> None:
        """Test enforce_dependency with no matching files."""
        adapter = RectorAdapter(tmp_path)

        rule = PhpDependencyRule(
            source_namespace="NonExistent\\Namespace",
            target_namespace="Other\\Namespace",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 0


class TestRectorMethodExtraction:
    """Tests for PHP method extraction helper methods."""

    def test_extract_methods_with_modifiers(self, tmp_path: Path) -> None:
        """Test extracting methods with various modifiers."""
        adapter = RectorAdapter(tmp_path)

        content = """<?php

namespace App;

class Service
{
    public static function staticMethod(): void {}

    public final function finalMethod(): string {}

    public function normalMethod(int $id): array {}
}
"""
        methods = adapter._extract_php_methods(content, "Service", None)

        assert len(methods) == 3
        names = [m["name"] for m in methods]
        assert "staticMethod" in names
        assert "finalMethod" in names
        assert "normalMethod" in names

    def test_extract_methods_skips_constructor(self, tmp_path: Path) -> None:
        """Test that __construct is not extracted."""
        adapter = RectorAdapter(tmp_path)

        content = """<?php

namespace App;

class MyClass
{
    public function __construct(string $name)
    {
        $this->name = $name;
    }

    public function greet(): string
    {
        return "Hello " . $this->name;
    }
}
"""
        methods = adapter._extract_php_methods(content, "MyClass", None)

        assert len(methods) == 1
        assert methods[0]["name"] == "greet"

    def test_extract_methods_nullable_return_type(self, tmp_path: Path) -> None:
        """Test extracting methods with nullable return types."""
        adapter = RectorAdapter(tmp_path)

        content = """<?php

namespace App;

class Repository
{
    public function find(int $id): ?User {}

    public function findAll(): array {}
}
"""
        methods = adapter._extract_php_methods(content, "Repository", None)

        assert len(methods) == 2
        return_types = [m["return_type"] for m in methods]
        assert "?User" in return_types
        assert "array" in return_types


class TestRectorRollback:
    """Tests for rollback functionality."""

    @patch("subprocess.run")
    def test_rollback(self, mock_run: MagicMock, adapter: RectorAdapter) -> None:
        """Test rollback functionality."""
        mock_run.return_value = MagicMock(returncode=0)

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True, changes=[], errors=[], tool_used="Rector", dry_run=False
        )

        assert adapter.rollback(result) is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "checkout" in call_args
