"""Unit tests for Ruby Parser adapter (Ruby refactoring)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.ruby_parser_adapter import (
    RubyDependencyRule,
    RubyDependencyViolation,
    RubyParserAdapter,
)
from rice_factor.domain.ports.refactor import RefactorOperation, RefactorRequest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def adapter(tmp_project: Path) -> RubyParserAdapter:
    """Create a Ruby parser adapter for testing."""
    return RubyParserAdapter(tmp_project)


class TestRubyParserAdapter:
    """Tests for RubyParserAdapter basic functionality."""

    def test_supported_languages(self, adapter: RubyParserAdapter) -> None:
        """Test that Ruby languages are supported."""
        languages = adapter.get_supported_languages()
        assert "ruby" in languages
        assert "rb" in languages

    def test_supported_operations(self, adapter: RubyParserAdapter) -> None:
        """Test that expected operations are supported."""
        operations = adapter.get_supported_operations()
        assert RefactorOperation.RENAME in operations
        assert RefactorOperation.MOVE in operations
        assert RefactorOperation.EXTRACT_INTERFACE in operations

    def test_not_available_without_ruby(self, adapter: RubyParserAdapter) -> None:
        """Test that adapter is not available without Ruby CLI."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ruby not found")
            assert adapter.is_available() is False

    @patch("subprocess.run")
    def test_available_with_ruby_and_gemfile(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: RubyParserAdapter,
    ) -> None:
        """Test that adapter is available with Ruby and Gemfile."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ruby 3.2.0")

        # Create a Gemfile
        gemfile = tmp_project / "Gemfile"
        gemfile.write_text("source 'https://rubygems.org'\n")

        assert adapter.is_available() is True

    @patch("subprocess.run")
    def test_available_with_ruby_and_rakefile(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: RubyParserAdapter,
    ) -> None:
        """Test that adapter is available with Ruby and Rakefile."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ruby 3.2.0")

        # Create a Rakefile
        rakefile = tmp_project / "Rakefile"
        rakefile.write_text("task :default do\nend\n")

        assert adapter.is_available() is True

    @patch("subprocess.run")
    def test_available_with_ruby_files(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: RubyParserAdapter,
    ) -> None:
        """Test that adapter is available with .rb files."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ruby 3.2.0")

        # Create a Ruby file
        rb_file = tmp_project / "app.rb"
        rb_file.write_text("puts 'hello'\n")

        assert adapter.is_available() is True

    def test_execute_not_available(self, adapter: RubyParserAdapter) -> None:
        """Test execute when Ruby is not available."""
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
        adapter: RubyParserAdapter,
    ) -> None:
        """Test version detection."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ruby 3.2.0 (2022-12-25 revision a528908271)\n")

        version = adapter.get_version()
        assert "ruby 3.2.0" in version

    def test_get_capability(
        self, tmp_project: Path, adapter: RubyParserAdapter
    ) -> None:
        """Test capability reporting."""
        cap = adapter.get_capability()
        assert cap.tool_name == "RubyParserAdapter"
        assert "ruby" in cap.languages
        assert RefactorOperation.RENAME in cap.operations


class TestRubyRename:
    """Tests for rename operations."""

    @patch("subprocess.run")
    def test_rename_manual(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test manual rename in Ruby files."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ruby 3.2.0")

        # Create test files
        gemfile = tmp_path / "Gemfile"
        gemfile.write_text("source 'https://rubygems.org'\n")

        rb_file = tmp_path / "service.rb"
        rb_file.write_text(
            """class OldClass
  def initialize
    @name = "test"
  end

  def greet
    puts "Hello from OldClass"
  end
end
"""
        )

        adapter = RubyParserAdapter(tmp_path)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="OldClass",
            new_value="NewClass",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert len(result.changes) == 1

        # Check file was modified
        new_content = rb_file.read_text()
        assert "NewClass" in new_content
        assert "OldClass" not in new_content


class TestRubyMove:
    """Tests for move/module operations."""

    @patch("subprocess.run")
    def test_move_module(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test module change operation."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ruby 3.2.0")

        # Create test files
        gemfile = tmp_path / "Gemfile"
        gemfile.write_text("source 'https://rubygems.org'\n")

        rb_file = tmp_path / "service.rb"
        rb_file.write_text(
            """require 'oldmodule/utils'

module OldModule
  class Service
    def work
      OldModule::Helper.call
    end
  end
end
"""
        )

        adapter = RubyParserAdapter(tmp_path)

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="OldModule",
            new_value="NewModule",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert len(result.changes) == 1

        new_content = rb_file.read_text()
        assert "module NewModule" in new_content
        assert "NewModule::Helper" in new_content


class TestRubyExtractInterface:
    """Tests for extract_interface functionality."""

    def test_extract_interface_basic(self, tmp_path: Path) -> None:
        """Test extracting interface from a Ruby class."""
        adapter = RubyParserAdapter(tmp_path)

        rb_file = tmp_path / "user_service.rb"
        rb_file.write_text(
            """class UserService
  def get_user_name(id)
    "User #{id}"
  end

  def create_user(name, email)
    # Implementation
  end

  def get_all_users
    []
  end

  private

  def internal_method
    # Should not appear in interface
  end
end
"""
        )

        result = adapter.extract_interface(
            file_path=rb_file,
            class_name="UserService",
            interface_name="UserServiceInterface",
        )

        assert result.success is True
        assert len(result.changes) == 2  # Module and RBS

        module_code = result.changes[0].new_content
        assert "module UserServiceInterface" in module_code
        assert "def get_user_name" in module_code
        assert "def create_user" in module_code
        assert "def get_all_users" in module_code
        # Private method should not appear
        assert "internal_method" not in module_code

        # Check RBS was generated
        rbs_code = result.changes[1].new_content
        assert "interface _UserServiceInterface" in rbs_code

    def test_extract_interface_filter_methods(self, tmp_path: Path) -> None:
        """Test extracting interface with filtered methods."""
        adapter = RubyParserAdapter(tmp_path)

        rb_file = tmp_path / "calculator.rb"
        rb_file.write_text(
            """class Calculator
  def add(a, b)
    a + b
  end

  def subtract(a, b)
    a - b
  end

  def multiply(a, b)
    a * b
  end
end
"""
        )

        result = adapter.extract_interface(
            file_path=rb_file,
            class_name="Calculator",
            interface_name="CalculatorInterface",
            methods=["add", "subtract"],
        )

        assert result.success is True
        module_code = result.changes[0].new_content

        assert "def add" in module_code
        assert "def subtract" in module_code
        assert "multiply" not in module_code

    def test_extract_interface_file_not_found(self, tmp_path: Path) -> None:
        """Test extract_interface with non-existent file."""
        adapter = RubyParserAdapter(tmp_path)

        result = adapter.extract_interface(
            file_path=Path("nonexistent.rb"),
            class_name="SomeClass",
            interface_name="SomeInterface",
        )

        assert result.success is False
        assert "not found" in result.errors[0].lower()

    def test_extract_interface_class_not_found(self, tmp_path: Path) -> None:
        """Test extract_interface with non-existent class."""
        adapter = RubyParserAdapter(tmp_path)

        rb_file = tmp_path / "service.rb"
        rb_file.write_text(
            """class OtherClass
  def some_method
    # do something
  end
end
"""
        )

        result = adapter.extract_interface(
            file_path=rb_file,
            class_name="NonExistentClass",
            interface_name="ServiceInterface",
        )

        assert result.success is False
        assert "No public methods found" in result.errors[0]

    def test_extract_interface_predicate_methods(self, tmp_path: Path) -> None:
        """Test extracting methods with ? and ! suffixes."""
        adapter = RubyParserAdapter(tmp_path)

        rb_file = tmp_path / "validator.rb"
        rb_file.write_text(
            """class Validator
  def valid?
    true
  end

  def validate!
    raise "Invalid" unless valid?
  end

  def reset
    # reset state
  end
end
"""
        )

        result = adapter.extract_interface(
            file_path=rb_file,
            class_name="Validator",
            interface_name="ValidatorInterface",
        )

        assert result.success is True
        module_code = result.changes[0].new_content

        assert "def valid?" in module_code
        assert "def validate!" in module_code
        assert "def reset" in module_code


class TestRubyEnforceDependency:
    """Tests for enforce_dependency functionality."""

    def test_dependency_rule_dataclass(self) -> None:
        """Test RubyDependencyRule dataclass."""
        rule = RubyDependencyRule(
            source_module="Domain",
            target_module="Infrastructure",
            description="Domain should not depend on infrastructure",
        )

        assert rule.source_module == "Domain"
        assert rule.target_module == "Infrastructure"
        assert rule.description == "Domain should not depend on infrastructure"

    def test_dependency_violation_dataclass(self) -> None:
        """Test RubyDependencyViolation dataclass."""
        violation = RubyDependencyViolation(
            file_path="service.rb",
            line=5,
            require_statement="require 'forbidden/helper'",
            source_class="Service",
            target_module="forbidden/helper",
        )

        assert violation.file_path == "service.rb"
        assert violation.line == 5
        assert "forbidden" in violation.require_statement

    def test_enforce_dependency_no_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency with no violations."""
        adapter = RubyParserAdapter(tmp_path)

        (tmp_path / "domain").mkdir()
        rb_file = tmp_path / "domain" / "user_service.rb"
        rb_file.write_text(
            """require 'domain/models/user'

module Domain
  class UserService
    def get_user
      nil
    end
  end
end
"""
        )

        rule = RubyDependencyRule(
            source_module="Domain",
            target_module="Infrastructure",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 0

    def test_enforce_dependency_finds_violations(self, tmp_path: Path) -> None:
        """Test enforce_dependency finding violations."""
        adapter = RubyParserAdapter(tmp_path)

        (tmp_path / "domain").mkdir()
        rb_file = tmp_path / "domain" / "user_service.rb"
        rb_file.write_text(
            """require 'infrastructure/database'
require 'infrastructure/cache'

module Domain
  class UserService
    # Violating domain-infrastructure boundary
  end
end
"""
        )

        rule = RubyDependencyRule(
            source_module="Domain",
            target_module="Infrastructure",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True  # Operation succeeded
        assert len(result.changes) == 2  # Two violations
        assert any("database" in c.description.lower() for c in result.changes)
        assert any("cache" in c.description.lower() for c in result.changes)

    def test_enforce_dependency_fix_mode(self, tmp_path: Path) -> None:
        """Test enforce_dependency with fix=True removes requires."""
        adapter = RubyParserAdapter(tmp_path)

        (tmp_path / "domain").mkdir()
        rb_file = tmp_path / "domain" / "bad_service.rb"
        original_content = """require 'json'
require 'forbidden/bad_class'
require 'active_support'

module Domain
  class BadService
  end
end
"""
        rb_file.write_text(original_content)

        rule = RubyDependencyRule(
            source_module="Domain",
            target_module="Forbidden",
        )

        result = adapter.enforce_dependency(rule, fix=True)

        assert result.success is True
        assert result.dry_run is False

        # Check file was modified
        new_content = rb_file.read_text()
        assert "require 'forbidden/bad_class'" not in new_content
        # Other requires should remain
        assert "require 'json'" in new_content

    def test_enforce_dependency_empty_project(self, tmp_path: Path) -> None:
        """Test enforce_dependency with no matching files."""
        adapter = RubyParserAdapter(tmp_path)

        rule = RubyDependencyRule(
            source_module="NonExistent",
            target_module="Other",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 0

    def test_enforce_dependency_module_reference(self, tmp_path: Path) -> None:
        """Test enforce_dependency finds direct module references."""
        adapter = RubyParserAdapter(tmp_path)

        (tmp_path / "domain").mkdir()
        rb_file = tmp_path / "domain" / "service.rb"
        rb_file.write_text(
            """module Domain
  class Service
    def call
      Forbidden::Helper.do_something
    end
  end
end
"""
        )

        rule = RubyDependencyRule(
            source_module="Domain",
            target_module="Forbidden",
        )

        result = adapter.enforce_dependency(rule, fix=False)

        assert result.success is True
        assert len(result.changes) == 1
        assert "Forbidden" in result.changes[0].description


class TestRubyMethodExtraction:
    """Tests for Ruby method extraction helper methods."""

    def test_extract_methods_with_defaults(self, tmp_path: Path) -> None:
        """Test extracting methods with default parameters."""
        adapter = RubyParserAdapter(tmp_path)

        content = """
class Service
  def call(name, options = {})
    # implementation
  end

  def process(data, format = 'json', validate = true)
    # implementation
  end
end
"""
        methods = adapter._extract_ruby_methods(content, "Service", None)

        assert len(methods) == 2
        params = [m["params"] for m in methods]
        assert any("options = {}" in p for p in params)
        assert any("format = 'json'" in p for p in params)

    def test_extract_methods_skips_initialize(self, tmp_path: Path) -> None:
        """Test that initialize is not extracted."""
        adapter = RubyParserAdapter(tmp_path)

        content = """
class MyClass
  def initialize(name)
    @name = name
  end

  def greet
    puts "Hello #{@name}"
  end
end
"""
        methods = adapter._extract_ruby_methods(content, "MyClass", None)

        assert len(methods) == 1
        assert methods[0]["name"] == "greet"

    def test_extract_methods_respects_visibility(self, tmp_path: Path) -> None:
        """Test that private/protected methods are not extracted."""
        adapter = RubyParserAdapter(tmp_path)

        content = """
class Service
  def public_method
    # public
  end

  private

  def private_method
    # private
  end

  protected

  def protected_method
    # protected
  end
end
"""
        methods = adapter._extract_ruby_methods(content, "Service", None)

        assert len(methods) == 1
        assert methods[0]["name"] == "public_method"


class TestRubyRollback:
    """Tests for rollback functionality."""

    @patch("subprocess.run")
    def test_rollback(self, mock_run: MagicMock, adapter: RubyParserAdapter) -> None:
        """Test rollback functionality."""
        mock_run.return_value = MagicMock(returncode=0)

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True, changes=[], errors=[], tool_used="RubyParser", dry_run=False
        )

        assert adapter.rollback(result) is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "checkout" in call_args


class TestRubyRbsGeneration:
    """Tests for RBS (Ruby Signature) generation."""

    def test_convert_params_to_rbs_empty(self, tmp_path: Path) -> None:
        """Test converting empty params to RBS."""
        adapter = RubyParserAdapter(tmp_path)
        result = adapter._convert_params_to_rbs("")
        assert result == "()"

    def test_convert_params_to_rbs_simple(self, tmp_path: Path) -> None:
        """Test converting simple params to RBS."""
        adapter = RubyParserAdapter(tmp_path)
        result = adapter._convert_params_to_rbs("name, age")
        assert "untyped name" in result
        assert "untyped age" in result

    def test_convert_params_to_rbs_with_defaults(self, tmp_path: Path) -> None:
        """Test converting params with defaults to RBS."""
        adapter = RubyParserAdapter(tmp_path)
        result = adapter._convert_params_to_rbs("name, format = 'json'")
        assert "untyped name" in result
        assert "?untyped format" in result

    def test_convert_params_to_rbs_with_splat(self, tmp_path: Path) -> None:
        """Test converting splat params to RBS."""
        adapter = RubyParserAdapter(tmp_path)
        result = adapter._convert_params_to_rbs("*args")
        assert "*untyped args" in result

    def test_convert_params_to_rbs_with_double_splat(self, tmp_path: Path) -> None:
        """Test converting double splat params to RBS."""
        adapter = RubyParserAdapter(tmp_path)
        result = adapter._convert_params_to_rbs("**kwargs")
        assert "**untyped kwargs" in result

    def test_generate_rbs_interface(self, tmp_path: Path) -> None:
        """Test generating RBS interface."""
        adapter = RubyParserAdapter(tmp_path)
        method_sigs = [
            {"name": "call", "params": "input"},
            {"name": "validate", "params": ""},
        ]
        result = adapter._generate_rbs_interface("MyInterface", method_sigs)

        assert "interface _MyInterface" in result
        assert "def call:" in result
        assert "def validate:" in result
        assert "-> untyped" in result
