"""Unit tests for Roslyn adapter (C# refactoring)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.roslyn_adapter import (
    CSharpDependencyRule,
    CSharpDependencyViolation,
    RoslynAdapter,
)
from rice_factor.domain.ports.refactor import RefactorOperation, RefactorRequest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def adapter(tmp_project: Path) -> RoslynAdapter:
    """Create a Roslyn adapter for testing."""
    return RoslynAdapter(tmp_project)


class TestRoslynAdapter:
    """Tests for RoslynAdapter basic functionality."""

    def test_supported_languages(self, adapter: RoslynAdapter) -> None:
        """Test that C# languages are supported."""
        languages = adapter.get_supported_languages()
        assert "csharp" in languages
        assert "cs" in languages

    def test_supported_operations(self, adapter: RoslynAdapter) -> None:
        """Test that expected operations are supported."""
        operations = adapter.get_supported_operations()
        assert RefactorOperation.RENAME in operations
        assert RefactorOperation.MOVE in operations
        assert RefactorOperation.EXTRACT_INTERFACE in operations

    def test_not_available_without_dotnet(self, adapter: RoslynAdapter) -> None:
        """Test that adapter is not available without dotnet CLI."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("dotnet not found")
            assert adapter.is_available() is False

    @patch("subprocess.run")
    def test_available_with_dotnet_and_csproj(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: RoslynAdapter,
    ) -> None:
        """Test that adapter is available with dotnet and .csproj file."""
        mock_run.return_value = MagicMock(returncode=0, stdout="8.0.100")

        # Create a .csproj file
        csproj = tmp_project / "MyProject.csproj"
        csproj.write_text("<Project></Project>")

        assert adapter.is_available() is True

    @patch("subprocess.run")
    def test_available_with_dotnet_and_sln(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: RoslynAdapter,
    ) -> None:
        """Test that adapter is available with dotnet and .sln file."""
        mock_run.return_value = MagicMock(returncode=0, stdout="8.0.100")

        # Create a .sln file
        sln = tmp_project / "MySolution.sln"
        sln.write_text("Microsoft Visual Studio Solution File")

        assert adapter.is_available() is True

    def test_execute_not_available(self, adapter: RoslynAdapter) -> None:
        """Test execute when dotnet is not available."""
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
        adapter: RoslynAdapter,
    ) -> None:
        """Test version detection."""
        mock_run.return_value = MagicMock(returncode=0, stdout="8.0.100\n")

        version = adapter.get_version()
        assert version == "8.0.100"

    def test_get_capability(
        self, tmp_project: Path, adapter: RoslynAdapter
    ) -> None:
        """Test capability reporting."""
        cap = adapter.get_capability()
        assert cap.tool_name == "RoslynAdapter"
        assert "csharp" in cap.languages
        assert RefactorOperation.RENAME in cap.operations


class TestRoslynRename:
    """Tests for rename operations."""

    @patch("subprocess.run")
    def test_rename_manual_fallback(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test manual rename when Roslynator is not available."""
        # Setup dotnet available but no Roslynator
        def run_side_effect(cmd, **kwargs):
            if cmd[0] == "dotnet" and "--version" in cmd:
                return MagicMock(returncode=0, stdout="8.0.100")
            if cmd[0] == "dotnet" and "tool" in cmd:
                return MagicMock(returncode=0, stdout="")  # No Roslynator
            raise FileNotFoundError()

        mock_run.side_effect = run_side_effect

        # Create test files
        csproj = tmp_path / "Test.csproj"
        csproj.write_text("<Project></Project>")

        cs_file = tmp_path / "Service.cs"
        cs_file.write_text(
            """namespace MyApp
{
    public class OldClass
    {
        public void DoWork() { }
    }
}
"""
        )

        adapter = RoslynAdapter(tmp_path)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="OldClass",
            new_value="NewClass",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert len(result.changes) == 1

        # Check file was modified
        new_content = cs_file.read_text()
        assert "NewClass" in new_content
        assert "OldClass" not in new_content


class TestRoslynMove:
    """Tests for move/namespace operations."""

    @patch("subprocess.run")
    def test_move_namespace(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test namespace change operation."""
        mock_run.return_value = MagicMock(returncode=0, stdout="8.0.100")

        # Create test files
        csproj = tmp_path / "Test.csproj"
        csproj.write_text("<Project></Project>")

        cs_file = tmp_path / "Service.cs"
        cs_file.write_text(
            """using System;
using OldNamespace.Utils;

namespace OldNamespace
{
    public class Service { }
}
"""
        )

        adapter = RoslynAdapter(tmp_path)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="OldNamespace",
            new_value="NewNamespace",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert len(result.changes) == 1

        new_content = cs_file.read_text()
        assert "namespace NewNamespace" in new_content
        assert "using NewNamespace.Utils" in new_content


class TestRoslynExtractInterface:
    """Tests for extract_interface functionality."""

    def test_extract_interface_basic(self, tmp_path: Path) -> None:
        """Test extracting interface from a C# class."""
        adapter = RoslynAdapter(tmp_path)

        cs_file = tmp_path / "UserService.cs"
        cs_file.write_text(
            """namespace MyApp.Services
{
    public class UserService
    {
        public string GetUserName(int id)
        {
            return "User " + id;
        }

        public void CreateUser(string name, string email)
        {
            // Implementation
        }

        public List<User> GetAllUsers()
        {
            return new List<User>();
        }

        private void InternalMethod()
        {
            // Should not appear in interface
        }
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=cs_file,
            class_name="UserService",
            interface_name="IUserService",
        )

        assert result.success is True
        assert len(result.changes) == 1
        interface_code = result.changes[0].new_content

        assert "namespace MyApp.Services" in interface_code
        assert "public interface IUserService" in interface_code
        assert "string GetUserName(int id);" in interface_code
        assert "void CreateUser(string name, string email);" in interface_code
        assert "List<User> GetAllUsers();" in interface_code
        # Private method should not appear
        assert "InternalMethod" not in interface_code

    def test_extract_interface_filter_methods(self, tmp_path: Path) -> None:
        """Test extracting interface with filtered methods."""
        adapter = RoslynAdapter(tmp_path)

        cs_file = tmp_path / "Calculator.cs"
        cs_file.write_text(
            """namespace Math
{
    public class Calculator
    {
        public int Add(int a, int b) { return a + b; }
        public int Subtract(int a, int b) { return a - b; }
        public int Multiply(int a, int b) { return a * b; }
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=cs_file,
            class_name="Calculator",
            interface_name="ICalculator",
            methods=["Add", "Subtract"],
        )

        assert result.success is True
        interface_code = result.changes[0].new_content

        assert "int Add(int a, int b);" in interface_code
        assert "int Subtract(int a, int b);" in interface_code
        assert "Multiply" not in interface_code

    def test_extract_interface_file_not_found(self, tmp_path: Path) -> None:
        """Test extract_interface with non-existent file."""
        adapter = RoslynAdapter(tmp_path)

        result = adapter.extract_interface(
            file_path=Path("nonexistent.cs"),
            class_name="SomeClass",
            interface_name="ISomeClass",
        )

        assert result.success is False
        assert "not found" in result.errors[0].lower()

    def test_extract_interface_class_not_found(self, tmp_path: Path) -> None:
        """Test extract_interface with non-existent class."""
        adapter = RoslynAdapter(tmp_path)

        cs_file = tmp_path / "Service.cs"
        cs_file.write_text(
            """namespace MyApp
{
    public class OtherClass
    {
        public void Method() { }
    }
}
"""
        )

        result = adapter.extract_interface(
            file_path=cs_file,
            class_name="NonExistentClass",
            interface_name="IService",
        )

        assert result.success is False
        assert "No public methods found" in result.errors[0]


class TestRoslynEnforceDependency:
    """Tests for enforce_dependency functionality."""

    def test_dependency_rule_dataclass(self) -> None:
        """Test CSharpDependencyRule dataclass."""
        rule = CSharpDependencyRule(
            source_namespace="MyApp.Domain",
            target_namespace="MyApp.Infrastructure",
            description="Domain should not depend on infrastructure",
        )

        assert rule.source_namespace == "MyApp.Domain"
        assert rule.target_namespace == "MyApp.Infrastructure"
        assert rule.description == "Domain should not depend on infrastructure"

    def test_dependency_violation_dataclass(self) -> None:
        """Test CSharpDependencyViolation dataclass."""
        violation = CSharpDependencyViolation(
            file_path="Service.cs",
            line=5,
            using_statement="using MyApp.Forbidden;",
            source_class="Service",
            target_namespace="MyApp.Forbidden",
        )

        assert violation.file_path == "Service.cs"
        assert violation.line == 5
        assert "Forbidden" in violation.using_statement

    def test_enforce_dependency_no_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency with no violations."""
        adapter = RoslynAdapter(tmp_path)

        cs_file = tmp_path / "UserService.cs"
        cs_file.write_text(
            """using System;
using MyApp.Domain.Models;

namespace MyApp.Domain
{
    public class UserService
    {
        public User GetUser() { return null; }
    }
}
"""
        )

        rule = CSharpDependencyRule(
            source_namespace="MyApp.Domain",
            target_namespace="MyApp.Infrastructure",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 0

    def test_enforce_dependency_finds_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency finding violations."""
        adapter = RoslynAdapter(tmp_path)

        cs_file = tmp_path / "UserService.cs"
        cs_file.write_text(
            """using System;
using MyApp.Infrastructure.Database;
using MyApp.Infrastructure.Cache;

namespace MyApp.Domain
{
    public class UserService
    {
        // Violating domain-infrastructure boundary
    }
}
"""
        )

        rule = CSharpDependencyRule(
            source_namespace="MyApp.Domain",
            target_namespace="MyApp.Infrastructure",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True  # Operation succeeded
        assert len(result.changes) == 2  # Two violations
        assert any("Database" in c.description for c in result.changes)
        assert any("Cache" in c.description for c in result.changes)

    def test_enforce_dependency_fix_mode(self, tmp_path: Path) -> None:
        """Test enforce_dependency with fix=True removes usings."""
        adapter = RoslynAdapter(tmp_path)

        cs_file = tmp_path / "BadService.cs"
        original_content = """using System;
using MyApp.Forbidden.BadClass;
using System.Collections.Generic;

namespace MyApp.Domain
{
    public class BadService { }
}
"""
        cs_file.write_text(original_content)

        rule = CSharpDependencyRule(
            source_namespace="MyApp.Domain",
            target_namespace="MyApp.Forbidden",
        )

        result = adapter.enforce_dependency(rule, fix=True)

        assert result.success is True
        assert result.dry_run is False

        # Check file was modified
        new_content = cs_file.read_text()
        assert "using MyApp.Forbidden.BadClass;" not in new_content
        # Other usings should remain
        assert "using System;" in new_content

    def test_enforce_dependency_empty_project(self, tmp_path: Path) -> None:
        """Test enforce_dependency with no matching files."""
        adapter = RoslynAdapter(tmp_path)

        rule = CSharpDependencyRule(
            source_namespace="NonExistent.Namespace",
            target_namespace="Other.Namespace",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 0


class TestRoslynMethodExtraction:
    """Tests for C# method extraction helper methods."""

    def test_extract_methods_with_generics(self, tmp_path: Path) -> None:
        """Test extracting methods with generic return types."""
        adapter = RoslynAdapter(tmp_path)

        content = """
namespace MyApp
{
    public class GenericService
    {
        public List<string> GetNames() { return null; }
        public Dictionary<string, int> GetCounts() { return null; }
        public Task<User> FindUserAsync(int id) { return null; }
    }
}
"""
        methods = adapter._extract_csharp_methods(content, "GenericService", None)

        assert len(methods) == 3
        return_types = [m["return_type"] for m in methods]
        assert "List<string>" in return_types
        assert "Dictionary<string, int>" in return_types
        assert "Task<User>" in return_types

    def test_extract_methods_skips_constructors(self, tmp_path: Path) -> None:
        """Test that constructors are not extracted."""
        adapter = RoslynAdapter(tmp_path)

        content = """
namespace MyApp
{
    public class MyClass
    {
        public MyClass() { }
        public MyClass(string name) { }
        public void DoSomething() { }
    }
}
"""
        methods = adapter._extract_csharp_methods(content, "MyClass", None)

        assert len(methods) == 1
        assert methods[0]["name"] == "DoSomething"


class TestRoslynRollback:
    """Tests for rollback functionality."""

    @patch("subprocess.run")
    def test_rollback(self, mock_run: MagicMock, adapter: RoslynAdapter) -> None:
        """Test rollback functionality."""
        mock_run.return_value = MagicMock(returncode=0)

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True, changes=[], errors=[], tool_used="Roslyn", dry_run=False
        )

        assert adapter.rollback(result) is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "checkout" in call_args
