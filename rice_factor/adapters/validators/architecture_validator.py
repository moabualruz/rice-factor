"""Architecture validator for hexagonal layer import rules.

This adapter implements the ValidationRunnerPort protocol to check
that domain layer code does not import from adapters or entrypoints,
enforcing the hexagonal architecture pattern.
"""

import ast
import time
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from rice_factor.domain.artifacts.validation_types import (
    ValidationContext,
    ValidationResult,
)


@dataclass
class ImportInfo:
    """Information about an import statement.

    Attributes:
        module: The full module path being imported.
        line: Line number of the import.
        file: Path to the file containing the import.
    """

    module: str
    line: int
    file: Path


class ArchitectureValidator:
    """Validator for hexagonal architecture layer rules.

    Checks that domain layer code does not import from adapters or
    entrypoints layers, enforcing proper dependency direction.

    Implements the ValidationRunnerPort protocol.

    Layer Rules:
    - domain/ cannot import from adapters/
    - domain/ cannot import from entrypoints/
    - domain/ should only use stdlib and domain types
    """

    # Modules that domain layer is forbidden from importing
    FORBIDDEN_IMPORTS_FOR_DOMAIN: ClassVar[list[str]] = [
        "rice_factor.adapters",
        "rice_factor.entrypoints",
    ]

    # Package name to check (can be configured)
    DEFAULT_PACKAGE_NAME: ClassVar[str] = "rice_factor"

    @property
    def name(self) -> str:
        """Get the validator name.

        Returns:
            The identifier "architecture_validator".
        """
        return "architecture_validator"

    def validate(
        self,
        target: Path,
        context: ValidationContext,
    ) -> ValidationResult:
        """Check architecture rules and return validation result.

        Args:
            target: Path to the repository root.
            context: Validation context with config.

        Returns:
            ValidationResult with architecture status and any violations.
        """
        start_time = time.time()

        # Check if architecture validation is disabled
        if context.get_config("skip_architecture", False):
            return ValidationResult.passed_result(
                target="architecture",
                validator=self.name,
                duration_ms=0,
            )

        # Get package name from config or use default
        package_name = context.get_config("package_name", self.DEFAULT_PACKAGE_NAME)

        # Find domain directory
        domain_dir = target / package_name / "domain"
        if not domain_dir.exists():
            # No domain directory - nothing to check
            return ValidationResult.passed_result(
                target="architecture",
                validator=self.name,
                duration_ms=0,
            )

        violations: list[str] = []

        # Check all Python files in domain
        for py_file in domain_dir.rglob("*.py"):
            try:
                imports = self.extract_imports(py_file)
                file_violations = self.check_layer_rules(imports, py_file, package_name)
                violations.extend(file_violations)
            except SyntaxError as e:
                violations.append(f"Syntax error in {py_file}: {e}")
            except Exception as e:
                violations.append(f"Error processing {py_file}: {e}")

        duration_ms = int((time.time() - start_time) * 1000)

        if violations:
            return ValidationResult.failed_result(
                target="architecture",
                errors=violations,
                validator=self.name,
                duration_ms=duration_ms,
            )

        return ValidationResult.passed_result(
            target="architecture",
            validator=self.name,
            duration_ms=duration_ms,
        )

    def extract_imports(self, file_path: Path) -> list[ImportInfo]:
        """Extract all imports from a Python file.

        Args:
            file_path: Path to the Python file.

        Returns:
            List of ImportInfo objects for all imports.

        Raises:
            SyntaxError: If the file has syntax errors.
        """
        imports: list[ImportInfo] = []

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=alias.name,
                            line=node.lineno,
                            file=file_path,
                        )
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(
                    ImportInfo(
                        module=node.module,
                        line=node.lineno,
                        file=file_path,
                    )
                )

        return imports

    def check_layer_rules(
        self,
        imports: list[ImportInfo],
        file_path: Path,
        package_name: str,
    ) -> list[str]:
        """Check imports against layer rules.

        Args:
            imports: List of imports from the file.
            file_path: Path to the source file.
            package_name: The main package name.

        Returns:
            List of violation messages.
        """
        violations: list[str] = []

        # Build forbidden import prefixes
        forbidden_prefixes = [
            f"{package_name}.adapters",
            f"{package_name}.entrypoints",
        ]

        for imp in imports:
            for forbidden in forbidden_prefixes:
                if imp.module.startswith(forbidden) or imp.module == forbidden.rstrip("."):
                    # Get relative path for cleaner output
                    try:
                        rel_path = file_path.relative_to(file_path.parent.parent.parent.parent)
                    except ValueError:
                        rel_path = file_path

                    violations.append(
                        f"{rel_path}:{imp.line}: domain imports from "
                        f"forbidden layer: {imp.module}"
                    )

        return violations

    def check_single_file(
        self,
        file_path: Path,
        package_name: str | None = None,
    ) -> list[str]:
        """Check a single file for architecture violations.

        Args:
            file_path: Path to the Python file.
            package_name: Optional package name override.

        Returns:
            List of violation messages.

        Raises:
            SyntaxError: If the file has syntax errors.
        """
        pkg = package_name or self.DEFAULT_PACKAGE_NAME
        imports = self.extract_imports(file_path)
        return self.check_layer_rules(imports, file_path, pkg)

    def is_domain_file(self, file_path: Path, package_name: str | None = None) -> bool:
        """Check if a file is in the domain layer.

        Args:
            file_path: Path to check.
            package_name: Optional package name override.

        Returns:
            True if file is in domain layer.
        """
        pkg = package_name or self.DEFAULT_PACKAGE_NAME
        path_str = str(file_path)
        return f"{pkg}/domain/" in path_str or f"{pkg}\\domain\\" in path_str
