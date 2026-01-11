"""Rector adapter for PHP refactoring.

Rector is a PHP tool for instant code upgrades and refactoring.
This adapter uses the Rector CLI for AST-based refactoring operations.

Documentation:
- Rector: https://getrector.org/
- GitHub: https://github.com/rectorphp/rector
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 - Path used at runtime
from typing import TYPE_CHECKING, Any, ClassVar

from rice_factor.domain.ports.refactor import (
    RefactorChange,
    RefactorOperation,
    RefactorRequest,
    RefactorResult,
    RefactorToolPort,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class PhpDependencyRule:
    """Rule for PHP dependency enforcement.

    Attributes:
        source_namespace: Namespace that should not depend on target.
        target_namespace: Namespace that should not be used by source.
        description: Human-readable description of the rule.
    """

    source_namespace: str
    target_namespace: str
    description: str = ""


@dataclass
class PhpDependencyViolation:
    """A dependency violation found during analysis.

    Attributes:
        file_path: Path to the file with the violation.
        line: Line number of the violation.
        use_statement: The use statement that violates the rule.
        source_class: Class/namespace doing the referencing.
        target_namespace: Namespace being referenced.
    """

    file_path: str
    line: int
    use_statement: str
    source_class: str
    target_namespace: str


class RectorAdapter(RefactorToolPort):
    """Adapter for Rector (PHP refactoring).

    This adapter uses the Rector CLI to perform AST-based refactoring
    for PHP projects.

    Attributes:
        project_root: Root directory of the project.
    """

    LANGUAGES: ClassVar[list[str]] = ["php"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
        RefactorOperation.MOVE,
        RefactorOperation.EXTRACT_INTERFACE,
    ]

    def __init__(self, project_root: Path) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the PHP project.
        """
        self.project_root = project_root
        self._php_version: str | None = None
        self._has_rector: bool | None = None

    def get_supported_languages(self) -> list[str]:
        """Return supported languages."""
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return supported refactoring operations."""
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if PHP and Rector are available.

        Returns:
            True if PHP is installed and a PHP project exists.
        """
        # Check for PHP CLI
        if not self._check_php():
            return False

        # Check for PHP project files
        composer_json = self.project_root / "composer.json"
        php_files = list(self.project_root.glob("**/*.php"))

        return composer_json.exists() or bool(php_files)

    def _check_php(self) -> bool:
        """Check if PHP is installed.

        Returns:
            True if PHP is available.
        """
        try:
            result = subprocess.run(
                ["php", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                self._php_version = result.stdout.strip().split("\n")[0]
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    def _check_rector(self) -> bool:
        """Check if Rector is installed.

        Returns:
            True if Rector is available.
        """
        if self._has_rector is not None:
            return self._has_rector

        # Check for local vendor/bin/rector
        local_rector = self.project_root / "vendor" / "bin" / "rector"
        if local_rector.exists():
            self._has_rector = True
            return True

        # Check for global rector command
        try:
            result = subprocess.run(
                ["rector", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self._has_rector = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._has_rector = False

        return self._has_rector

    def get_version(self) -> str | None:
        """Get PHP version.

        Returns:
            Version string if available.
        """
        if self._php_version is None:
            self._check_php()
        return self._php_version

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring operation.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes and status.
        """
        if not self.is_available():
            return RefactorResult(
                success=False,
                changes=[],
                errors=["PHP is not available"],
                tool_used="Rector",
                dry_run=dry_run,
            )

        if request.operation == RefactorOperation.RENAME:
            return self._execute_rename(request, dry_run)
        elif request.operation == RefactorOperation.MOVE:
            return self._execute_move(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_INTERFACE:
            return self._execute_extract_interface(request, dry_run)

        return RefactorResult(
            success=False,
            changes=[],
            errors=[f"Unsupported operation: {request.operation}"],
            tool_used="Rector",
            dry_run=dry_run,
        )

    def _execute_rename(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Execute rename operation using Rector or manual refactoring.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        if not request.new_value:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["new_value required for rename operation"],
                tool_used="Rector",
                dry_run=dry_run,
            )

        # Try Rector if available
        if self._check_rector():
            return self._rename_with_rector(request, dry_run)

        # Fallback to manual text-based rename
        return self._rename_manual(request, dry_run)

    def _rename_with_rector(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Rename using Rector CLI.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        # Rector uses rector.php config for rename rules
        # For now, fall back to manual rename
        return self._rename_manual(request, dry_run)

    def _rename_manual(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Manual text-based rename.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        changes: list[RefactorChange] = []
        old_name = request.target
        new_name = request.new_value or ""

        # Find all PHP files
        php_files = list(self.project_root.rglob("*.php"))

        for php_file in php_files:
            try:
                content = php_file.read_text(encoding="utf-8")
                if old_name in content:
                    new_content = content.replace(old_name, new_name)

                    if not dry_run:
                        php_file.write_text(new_content, encoding="utf-8")

                    changes.append(
                        RefactorChange(
                            file_path=str(php_file.relative_to(self.project_root)),
                            original_content=content,
                            new_content=new_content,
                            description=f"Renamed '{old_name}' to '{new_name}'",
                        )
                    )
            except OSError:
                continue

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="Rector",
            dry_run=dry_run,
            warnings=["Used text-based rename (Rector config not available)"],
        )

    def _execute_move(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Execute move/namespace change operation.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        if not request.new_value:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["new_value (target namespace) required for move"],
                tool_used="Rector",
                dry_run=dry_run,
            )

        old_namespace = request.target
        new_namespace = request.new_value

        # Escape backslashes for replacement strings
        new_ns_escaped = new_namespace.replace("\\", "\\\\")

        changes: list[RefactorChange] = []
        php_files = list(self.project_root.rglob("*.php"))

        for php_file in php_files:
            try:
                content = php_file.read_text(encoding="utf-8")

                # Change namespace declaration
                # PHP: namespace App\OldNamespace;
                new_content = re.sub(
                    rf"namespace\s+{re.escape(old_namespace)}(\s*[;\{{])",
                    rf"namespace {new_ns_escaped}\1",
                    content,
                )

                # Change use statements (exact and sub-namespaces)
                # PHP: use App\OldNamespace\ClassName;
                new_content = re.sub(
                    rf"use\s+{re.escape(old_namespace)}(\s*;)",
                    rf"use {new_ns_escaped}\1",
                    new_content,
                )
                new_content = re.sub(
                    rf"use\s+{re.escape(old_namespace)}\\(\w+)",
                    rf"use {new_ns_escaped}\\\1",
                    new_content,
                )

                # Change fully qualified class names
                new_content = re.sub(
                    rf"\\{re.escape(old_namespace)}\\",
                    rf"\\{new_ns_escaped}\\",
                    new_content,
                )

                if new_content != content:
                    if not dry_run:
                        php_file.write_text(new_content, encoding="utf-8")

                    changes.append(
                        RefactorChange(
                            file_path=str(php_file.relative_to(self.project_root)),
                            original_content=content,
                            new_content=new_content,
                            description=f"Changed namespace from '{old_namespace}' to '{new_namespace}'",
                        )
                    )
            except OSError:
                continue

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="Rector",
            dry_run=dry_run,
        )

    def _execute_extract_interface(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Execute extract interface operation.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with generated interface.
        """
        if not request.file_path:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["file_path required for extract_interface"],
                tool_used="Rector",
                dry_run=dry_run,
            )

        file_path = self.project_root / request.file_path
        if not file_path.exists():
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"File not found: {file_path}"],
                tool_used="Rector",
                dry_run=dry_run,
            )

        return self.extract_interface(
            file_path=file_path,
            class_name=request.target,
            interface_name=request.new_value or f"{request.target}Interface",
        )

    def rollback(self, _result: RefactorResult) -> bool:
        """Rollback changes using git.

        Args:
            _result: Result from previous execute() call.

        Returns:
            True if rollback succeeded.
        """
        try:
            subprocess.run(
                ["git", "checkout", "."],
                cwd=self.project_root,
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    # ========================================================================
    # M14 Enhanced Methods: extract_interface and enforce_dependency
    # ========================================================================

    def extract_interface(
        self,
        file_path: Path,
        class_name: str,
        interface_name: str,
        methods: Sequence[str] | None = None,
    ) -> RefactorResult:
        """Extract an interface from a PHP class.

        Args:
            file_path: Path to the file containing the class.
            class_name: Name of the concrete class.
            interface_name: Name for the generated interface.
            methods: Optional list of method names to include.

        Returns:
            RefactorResult with the generated interface code.
        """
        try:
            if not file_path.is_absolute():
                file_path = self.project_root / file_path

            if not file_path.exists():
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"File not found: {file_path}"],
                    tool_used="Rector",
                    dry_run=True,
                )

            content = file_path.read_text(encoding="utf-8")

            method_sigs = self._extract_php_methods(content, class_name, methods)

            if not method_sigs:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"No public methods found in class '{class_name}'"],
                    tool_used="Rector",
                    dry_run=True,
                )

            interface_code = self._generate_php_interface(
                interface_name, method_sigs, content
            )

            change = RefactorChange(
                file_path=str(file_path.relative_to(self.project_root)),
                original_content="",
                new_content=interface_code,
                description=f"Generated interface '{interface_name}' from class '{class_name}'",
            )

            return RefactorResult(
                success=True,
                changes=[change],
                errors=[],
                tool_used="Rector",
                dry_run=True,
                warnings=[
                    "Interface generated but not automatically inserted into file",
                    "Review and add to appropriate location",
                ],
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Extract interface failed: {e}"],
                tool_used="Rector",
                dry_run=True,
            )

    def _extract_php_methods(
        self,
        content: str,
        class_name: str,
        filter_methods: Sequence[str] | None,
    ) -> list[dict[str, Any]]:
        """Extract method signatures from a PHP class.

        Args:
            content: PHP source code.
            class_name: Name of the class to extract from.
            filter_methods: Optional list of method names to include.

        Returns:
            List of method signature dictionaries.
        """
        signatures: list[dict[str, Any]] = []

        # Find the class
        class_pattern = rf"class\s+{re.escape(class_name)}(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*{{"
        class_match = re.search(class_pattern, content)
        if not class_match:
            return signatures

        # Extract class body
        class_start = class_match.end()

        # Find public methods
        # Pattern: public [static] function methodName(params): ReturnType
        method_pattern = (
            r"public\s+(?:(?:static|final|abstract)\s+)*"
            r"function\s+"
            r"(\w+)\s*"  # Method name
            r"\(([^)]*)\)"  # Parameters
            r"(?:\s*:\s*([\w\|\\?]+))?"  # Return type (optional)
        )

        for match in re.finditer(method_pattern, content[class_start:]):
            method_name = match.group(1)
            params = match.group(2).strip()
            return_type = match.group(3)

            # Skip constructor
            if method_name == "__construct":
                continue

            # Filter if specified
            if filter_methods and method_name not in filter_methods:
                continue

            signatures.append(
                {
                    "name": method_name,
                    "params": params,
                    "return_type": return_type,
                }
            )

        return signatures

    def _generate_php_interface(
        self,
        interface_name: str,
        method_sigs: list[dict[str, Any]],
        original_content: str,
    ) -> str:
        """Generate a PHP interface definition.

        Args:
            interface_name: Name for the interface.
            method_sigs: List of method signature dictionaries.
            original_content: Original source for namespace detection.

        Returns:
            PHP code for the interface.
        """
        lines = ["<?php", ""]

        # Extract namespace from original file
        namespace_match = re.search(r"namespace\s+([\w\\]+)\s*;", original_content)
        if namespace_match:
            lines.append(f"namespace {namespace_match.group(1)};")
            lines.append("")

        lines.append(f"interface {interface_name}")
        lines.append("{")

        for sig in method_sigs:
            params = sig["params"]
            return_type = sig.get("return_type")

            if return_type:
                lines.append(f"    public function {sig['name']}({params}): {return_type};")
            else:
                lines.append(f"    public function {sig['name']}({params});")

        lines.append("}")

        return "\n".join(lines)

    def enforce_dependency(
        self,
        rule: PhpDependencyRule,
        fix: bool = False,
    ) -> RefactorResult:
        """Check and report dependency violations in PHP code.

        Analyzes use statements to find violations of dependency rules.

        Args:
            rule: The dependency rule to enforce.
            fix: If True, attempt to remove violating use statements.

        Returns:
            RefactorResult with violations found.
        """
        try:
            violations = self._find_php_dependency_violations(rule)

            if not violations:
                return RefactorResult(
                    success=True,
                    changes=[],
                    errors=[],
                    tool_used="Rector",
                    dry_run=not fix,
                )

            changes: list[RefactorChange] = []
            errors: list[str] = []

            for violation in violations:
                if fix:
                    result = self._remove_php_use(violation)
                    if result.success:
                        changes.extend(result.changes)
                    else:
                        errors.extend(result.errors)
                else:
                    changes.append(
                        RefactorChange(
                            file_path=violation.file_path,
                            original_content=violation.use_statement,
                            new_content="",
                            description=(
                                f"Dependency violation: {violation.source_class} "
                                f"uses {violation.target_namespace} at line {violation.line}"
                            ),
                        )
                    )

            return RefactorResult(
                success=len(errors) == 0,
                changes=changes,
                errors=errors,
                tool_used="Rector",
                dry_run=not fix,
                warnings=[f"Found {len(violations)} dependency violation(s)"],
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Enforce dependency failed: {e}"],
                tool_used="Rector",
                dry_run=not fix,
            )

    def _find_php_dependency_violations(
        self,
        rule: PhpDependencyRule,
    ) -> list[PhpDependencyViolation]:
        """Find all violations of a dependency rule in PHP source files.

        Args:
            rule: The dependency rule to check.

        Returns:
            List of dependency violations.
        """
        violations: list[PhpDependencyViolation] = []

        # Find all PHP files
        php_files = list(self.project_root.rglob("*.php"))

        for php_file in php_files:
            try:
                content = php_file.read_text(encoding="utf-8")

                # Check if file is in source namespace
                in_source = (
                    f"namespace {rule.source_namespace}" in content
                    or re.search(
                        rf"namespace\s+{re.escape(rule.source_namespace)}[\\\s;]",
                        content,
                    )
                )

                if not in_source:
                    continue

                file_violations = self._check_php_file_violations(
                    php_file, content, rule
                )
                violations.extend(file_violations)

            except OSError:
                continue

        return violations

    def _check_php_file_violations(
        self,
        file_path: Path,
        content: str,
        rule: PhpDependencyRule,
    ) -> list[PhpDependencyViolation]:
        """Check a single PHP file for dependency violations.

        Args:
            file_path: Path to the source file.
            content: File content.
            rule: The dependency rule to check.

        Returns:
            List of violations in this file.
        """
        violations: list[PhpDependencyViolation] = []
        lines = content.split("\n")

        source_class = file_path.stem

        for i, line in enumerate(lines, 1):
            # Check for use statements
            # PHP: use App\Forbidden\ClassName;
            use_match = re.match(r"use\s+([\w\\]+)\s*;", line)
            if use_match:
                namespace = use_match.group(1)
                # Check if this uses the forbidden namespace
                if namespace.startswith(rule.target_namespace):
                    violations.append(
                        PhpDependencyViolation(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line=i,
                            use_statement=line.strip(),
                            source_class=source_class,
                            target_namespace=namespace,
                        )
                    )

        return violations

    def _remove_php_use(
        self, violation: PhpDependencyViolation
    ) -> RefactorResult:
        """Remove a use statement that violates dependency rules.

        Args:
            violation: The violation to fix.

        Returns:
            RefactorResult indicating success/failure.
        """
        try:
            file_path = self.project_root / violation.file_path
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            if 0 < violation.line <= len(lines):
                removed_line = lines[violation.line - 1]
                lines[violation.line - 1] = ""

                new_content = "\n".join(lines)
                file_path.write_text(new_content, encoding="utf-8")

                return RefactorResult(
                    success=True,
                    changes=[
                        RefactorChange(
                            file_path=violation.file_path,
                            original_content=removed_line,
                            new_content="",
                            description=f"Removed use statement at line {violation.line}",
                            line_start=violation.line,
                            line_end=violation.line,
                        )
                    ],
                    errors=[],
                    tool_used="Rector",
                    dry_run=False,
                )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Failed to remove use statement: {e}"],
                tool_used="Rector",
                dry_run=False,
            )

        return RefactorResult(
            success=False,
            changes=[],
            errors=["Could not find line to remove"],
            tool_used="Rector",
            dry_run=False,
        )
