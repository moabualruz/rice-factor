"""Tests for ArchitectureValidator."""

from pathlib import Path

import pytest

from rice_factor.adapters.validators.architecture_validator import (
    ArchitectureValidator,
    ImportInfo,
)
from rice_factor.domain.artifacts.validation_types import ValidationContext


@pytest.fixture
def validator() -> ArchitectureValidator:
    """Create an ArchitectureValidator instance."""
    return ArchitectureValidator()


@pytest.fixture
def context() -> ValidationContext:
    """Create a validation context."""
    return ValidationContext(
        repo_root=Path("/test/repo"),
        language="python",
        config={},
    )


def create_python_file(path: Path, content: str) -> None:
    """Create a Python file with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class TestArchitectureValidator:
    """Tests for ArchitectureValidator."""

    def test_name_property(self, validator: ArchitectureValidator) -> None:
        """Test that name returns 'architecture_validator'."""
        assert validator.name == "architecture_validator"

    def test_validate_no_domain_dir(
        self, validator: ArchitectureValidator, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation when domain directory doesn't exist."""
        # No domain directory
        result = validator.validate(tmp_path, context)

        assert result.passed
        assert result.status == "passed"

    def test_validate_empty_domain_dir(
        self, validator: ArchitectureValidator, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation with empty domain directory."""
        domain_dir = tmp_path / "rice_factor" / "domain"
        domain_dir.mkdir(parents=True)

        result = validator.validate(tmp_path, context)

        assert result.passed

    def test_validate_skip_architecture(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test that architecture validation can be skipped via config."""
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={"skip_architecture": True},
        )

        # Create a file with forbidden import
        domain_dir = tmp_path / "rice_factor" / "domain"
        create_python_file(
            domain_dir / "test.py",
            "from rice_factor.adapters.foo import bar",
        )

        result = validator.validate(tmp_path, context)

        # Should pass - validation is skipped
        assert result.passed

    def test_validate_valid_imports(
        self, validator: ArchitectureValidator, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation with valid imports only."""
        domain_dir = tmp_path / "rice_factor" / "domain"
        create_python_file(
            domain_dir / "services" / "test.py",
            """
import os
from pathlib import Path
from typing import Any
from rice_factor.domain.models import Foo
""",
        )

        result = validator.validate(tmp_path, context)

        assert result.passed
        assert result.errors == []

    def test_validate_forbidden_adapters_import(
        self, validator: ArchitectureValidator, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation catches forbidden adapters import."""
        domain_dir = tmp_path / "rice_factor" / "domain"
        create_python_file(
            domain_dir / "services" / "test.py",
            "from rice_factor.adapters.storage import FilesystemStorage",
        )

        result = validator.validate(tmp_path, context)

        assert result.failed
        assert len(result.errors) == 1
        assert "adapters" in result.errors[0]

    def test_validate_forbidden_entrypoints_import(
        self, validator: ArchitectureValidator, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation catches forbidden entrypoints import."""
        domain_dir = tmp_path / "rice_factor" / "domain"
        create_python_file(
            domain_dir / "services" / "test.py",
            "from rice_factor.entrypoints.cli import main",
        )

        result = validator.validate(tmp_path, context)

        assert result.failed
        assert len(result.errors) == 1
        assert "entrypoints" in result.errors[0]

    def test_validate_multiple_violations(
        self, validator: ArchitectureValidator, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation with multiple violations."""
        domain_dir = tmp_path / "rice_factor" / "domain"

        # File 1 with adapters import
        create_python_file(
            domain_dir / "services" / "foo.py",
            "from rice_factor.adapters.llm import Claude",
        )

        # File 2 with entrypoints import
        create_python_file(
            domain_dir / "services" / "bar.py",
            "import rice_factor.entrypoints.cli",
        )

        result = validator.validate(tmp_path, context)

        assert result.failed
        assert len(result.errors) == 2

    def test_validate_syntax_error_handling(
        self, validator: ArchitectureValidator, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation handles syntax errors gracefully."""
        domain_dir = tmp_path / "rice_factor" / "domain"
        create_python_file(
            domain_dir / "test.py",
            "def broken(",  # Syntax error
        )

        result = validator.validate(tmp_path, context)

        # Should fail with syntax error message
        assert result.failed
        assert any("syntax" in e.lower() for e in result.errors)


class TestImportExtraction:
    """Tests for import extraction."""

    @pytest.fixture
    def validator(self) -> ArchitectureValidator:
        """Create validator."""
        return ArchitectureValidator()

    def test_extract_import_statement(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test extracting 'import' statement."""
        py_file = tmp_path / "test.py"
        create_python_file(py_file, "import os")

        imports = validator.extract_imports(py_file)

        assert len(imports) == 1
        assert imports[0].module == "os"
        assert imports[0].line == 1

    def test_extract_from_import_statement(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test extracting 'from ... import' statement."""
        py_file = tmp_path / "test.py"
        create_python_file(py_file, "from pathlib import Path")

        imports = validator.extract_imports(py_file)

        assert len(imports) == 1
        assert imports[0].module == "pathlib"
        assert imports[0].line == 1

    def test_extract_multiple_imports(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test extracting multiple imports."""
        py_file = tmp_path / "test.py"
        create_python_file(
            py_file,
            """
import os
import sys
from pathlib import Path
from typing import Any, Optional
""",
        )

        imports = validator.extract_imports(py_file)

        assert len(imports) == 4
        modules = [imp.module for imp in imports]
        assert "os" in modules
        assert "sys" in modules
        assert "pathlib" in modules
        assert "typing" in modules

    def test_extract_nested_imports(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test extracting nested module imports."""
        py_file = tmp_path / "test.py"
        create_python_file(
            py_file,
            "from rice_factor.domain.services.context import build",
        )

        imports = validator.extract_imports(py_file)

        assert len(imports) == 1
        assert imports[0].module == "rice_factor.domain.services.context"

    def test_extract_import_preserves_line_numbers(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test that line numbers are preserved."""
        py_file = tmp_path / "test.py"
        create_python_file(
            py_file,
            """
# Comment line 1
# Comment line 2
import os  # Line 4
""",
        )

        imports = validator.extract_imports(py_file)

        assert len(imports) == 1
        assert imports[0].line == 4


class TestLayerRules:
    """Tests for layer rule checking."""

    @pytest.fixture
    def validator(self) -> ArchitectureValidator:
        """Create validator."""
        return ArchitectureValidator()

    def test_check_valid_import(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test that valid imports pass."""
        imports = [
            ImportInfo(module="os", line=1, file=tmp_path / "test.py"),
            ImportInfo(module="pathlib", line=2, file=tmp_path / "test.py"),
            ImportInfo(
                module="rice_factor.domain.models", line=3, file=tmp_path / "test.py"
            ),
        ]

        violations = validator.check_layer_rules(imports, tmp_path / "test.py", "rice_factor")

        assert len(violations) == 0

    def test_check_adapters_import_violation(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test that adapters import is caught."""
        imports = [
            ImportInfo(
                module="rice_factor.adapters.storage", line=5, file=tmp_path / "test.py"
            ),
        ]

        violations = validator.check_layer_rules(imports, tmp_path / "test.py", "rice_factor")

        assert len(violations) == 1
        assert "adapters" in violations[0]
        assert ":5:" in violations[0]

    def test_check_entrypoints_import_violation(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test that entrypoints import is caught."""
        imports = [
            ImportInfo(
                module="rice_factor.entrypoints.cli.main",
                line=10,
                file=tmp_path / "test.py",
            ),
        ]

        violations = validator.check_layer_rules(imports, tmp_path / "test.py", "rice_factor")

        assert len(violations) == 1
        assert "entrypoints" in violations[0]
        assert ":10:" in violations[0]

    def test_check_custom_package_name(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test checking with custom package name."""
        imports = [
            ImportInfo(
                module="my_package.adapters.foo", line=1, file=tmp_path / "test.py"
            ),
        ]

        violations = validator.check_layer_rules(imports, tmp_path / "test.py", "my_package")

        assert len(violations) == 1
        assert "adapters" in violations[0]


class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.fixture
    def validator(self) -> ArchitectureValidator:
        """Create validator."""
        return ArchitectureValidator()

    def test_is_domain_file_true(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test is_domain_file returns True for domain files."""
        domain_file = tmp_path / "rice_factor" / "domain" / "services" / "foo.py"

        assert validator.is_domain_file(domain_file)

    def test_is_domain_file_false(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test is_domain_file returns False for non-domain files."""
        adapter_file = tmp_path / "rice_factor" / "adapters" / "storage.py"

        assert not validator.is_domain_file(adapter_file)

    def test_check_single_file(
        self, validator: ArchitectureValidator, tmp_path: Path
    ) -> None:
        """Test checking a single file."""
        py_file = tmp_path / "test.py"
        create_python_file(
            py_file,
            "from rice_factor.adapters.storage import Foo",
        )

        violations = validator.check_single_file(py_file)

        assert len(violations) == 1
        assert "adapters" in violations[0]
