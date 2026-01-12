"""Roslyn adapter for C# refactoring.

Roslyn is the .NET Compiler Platform that provides rich code analysis APIs
for C# and Visual Basic. This adapter uses the dotnet CLI with Roslynator
or other Roslyn-based tools to perform AST-based refactoring.

Now enhanced with tree-sitter AST for method extraction.

Documentation:
- Roslyn: https://github.com/dotnet/roslyn
- Roslynator: https://github.com/dotnet/roslynator
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from rice_factor.adapters.parsing.treesitter_adapter import TreeSitterAdapter
from rice_factor.domain.ports.ast import ParseResult, SymbolKind, Visibility
from rice_factor.domain.ports.refactor import (
    RefactorChange,
    RefactorOperation,
    RefactorRequest,
    RefactorResult,
    RefactorToolPort,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


@dataclass
class CSharpDependencyRule:
    """Rule for C# dependency enforcement.

    Attributes:
        source_namespace: Namespace that should not depend on target.
        target_namespace: Namespace that should not be referenced by source.
        description: Human-readable description of the rule.
    """

    source_namespace: str
    target_namespace: str
    description: str = ""


@dataclass
class CSharpDependencyViolation:
    """A dependency violation found during analysis.

    Attributes:
        file_path: Path to the file with the violation.
        line: Line number of the violation.
        using_statement: The using statement that violates the rule.
        source_class: Class/namespace doing the referencing.
        target_namespace: Namespace being referenced.
    """

    file_path: str
    line: int
    using_statement: str
    source_class: str
    target_namespace: str


class RoslynAdapter(RefactorToolPort):
    """Adapter for Roslyn (C# refactoring).

    This adapter uses the dotnet CLI with Roslynator or other Roslyn-based
    tools to perform AST-based refactoring for C# projects.

    Attributes:
        project_root: Root directory of the project.
    """

    LANGUAGES: ClassVar[list[str]] = ["csharp", "cs"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
        RefactorOperation.MOVE,
        RefactorOperation.EXTRACT_INTERFACE,
    ]

    def __init__(self, project_root: Path) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the .NET project.
        """
        self.project_root = project_root
        self._dotnet_version: str | None = None
        self._has_roslynator: bool | None = None
        self._ast_adapter: TreeSitterAdapter | None = None

    def _get_ast_adapter(self) -> TreeSitterAdapter | None:
        """Get or create tree-sitter adapter for AST parsing."""
        if self._ast_adapter is not None:
            return self._ast_adapter
        try:
            self._ast_adapter = TreeSitterAdapter()
            return self._ast_adapter
        except (ImportError, RuntimeError):
            logger.warning("tree-sitter not available for AST parsing")
            return None

    def _parse_file(self, file_path: Path, content: str | None = None) -> ParseResult | None:
        """Parse a C# file using tree-sitter."""
        ast_adapter = self._get_ast_adapter()
        if not ast_adapter:
            return None
        try:
            if content is None:
                content = file_path.read_text(encoding="utf-8")
            result = ast_adapter.parse_file(str(file_path), content)
            return result if result.success else None
        except (OSError, ValueError) as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None

    def get_supported_languages(self) -> list[str]:
        """Return supported languages."""
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return supported refactoring operations."""
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if dotnet CLI is available.

        Returns:
            True if dotnet is installed and a C# project exists.
        """
        # Check for dotnet CLI
        if not self._check_dotnet():
            return False

        # Check for C# project files
        csproj_files = list(self.project_root.glob("**/*.csproj"))
        sln_files = list(self.project_root.glob("*.sln"))

        return bool(csproj_files or sln_files)

    def _check_dotnet(self) -> bool:
        """Check if dotnet CLI is installed.

        Returns:
            True if dotnet is available.
        """
        try:
            result = subprocess.run(
                ["dotnet", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                self._dotnet_version = result.stdout.strip()
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    def _check_roslynator(self) -> bool:
        """Check if Roslynator is installed.

        Returns:
            True if Roslynator tool is available.
        """
        if self._has_roslynator is not None:
            return self._has_roslynator

        try:
            result = subprocess.run(
                ["dotnet", "tool", "list", "-g"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self._has_roslynator = "roslynator" in result.stdout.lower()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._has_roslynator = False

        return self._has_roslynator

    def get_version(self) -> str | None:
        """Get dotnet version.

        Returns:
            Version string if available.
        """
        if self._dotnet_version is None:
            self._check_dotnet()
        return self._dotnet_version

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
                errors=["Roslyn/dotnet is not available"],
                tool_used="Roslyn",
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
            tool_used="Roslyn",
            dry_run=dry_run,
        )

    def _execute_rename(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Execute rename operation using Roslynator or manual refactoring.

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
                tool_used="Roslyn",
                dry_run=dry_run,
            )

        # Try Roslynator if available
        if self._check_roslynator():
            return self._rename_with_roslynator(request, dry_run)

        # Fallback to manual text-based rename
        return self._rename_manual(request, dry_run)

    def _rename_with_roslynator(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Rename using Roslynator CLI.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        cmd = [
            "dotnet",
            "roslynator",
            "rename",
            request.target,
            request.new_value or "",
        ]

        if dry_run:
            cmd.append("--dry-run")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["Roslynator command timed out"],
                tool_used="Roslyn",
                dry_run=dry_run,
            )

        if result.returncode != 0:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[result.stderr or result.stdout or "Unknown error"],
                tool_used="Roslyn",
                dry_run=dry_run,
            )

        changes = self._parse_roslynator_output(result.stdout)

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="Roslyn",
            dry_run=dry_run,
        )

    def _rename_manual(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Manual text-based rename (simplified fallback).

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        changes: list[RefactorChange] = []
        old_name = request.target
        new_name = request.new_value or ""

        # Find all C# files
        cs_files = list(self.project_root.rglob("*.cs"))

        for cs_file in cs_files:
            try:
                content = cs_file.read_text(encoding="utf-8")
                if old_name in content:
                    new_content = content.replace(old_name, new_name)

                    if not dry_run:
                        cs_file.write_text(new_content, encoding="utf-8")

                    changes.append(
                        RefactorChange(
                            file_path=str(cs_file.relative_to(self.project_root)),
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
            tool_used="Roslyn",
            dry_run=dry_run,
            warnings=["Used text-based rename (Roslynator not available)"],
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
                tool_used="Roslyn",
                dry_run=dry_run,
            )

        old_namespace = request.target
        new_namespace = request.new_value

        changes: list[RefactorChange] = []
        cs_files = list(self.project_root.rglob("*.cs"))

        for cs_file in cs_files:
            try:
                content = cs_file.read_text(encoding="utf-8")

                # Change namespace declaration
                new_content = re.sub(
                    rf"namespace\s+{re.escape(old_namespace)}(\s*[\{{\n])",
                    rf"namespace {new_namespace}\1",
                    content,
                )

                # Change using statements (both exact and sub-namespaces)
                # Handle "using OldNamespace;" and "using OldNamespace.Sub;"
                new_content = re.sub(
                    rf"using\s+{re.escape(old_namespace)}(\s*;)",
                    rf"using {new_namespace}\1",
                    new_content,
                )
                new_content = re.sub(
                    rf"using\s+{re.escape(old_namespace)}\.(\w+)",
                    rf"using {new_namespace}.\1",
                    new_content,
                )

                if new_content != content:
                    if not dry_run:
                        cs_file.write_text(new_content, encoding="utf-8")

                    changes.append(
                        RefactorChange(
                            file_path=str(cs_file.relative_to(self.project_root)),
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
            tool_used="Roslyn",
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
                tool_used="Roslyn",
                dry_run=dry_run,
            )

        file_path = self.project_root / request.file_path
        if not file_path.exists():
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"File not found: {file_path}"],
                tool_used="Roslyn",
                dry_run=dry_run,
            )

        return self.extract_interface(
            file_path=file_path,
            class_name=request.target,
            interface_name=request.new_value or f"I{request.target}",
        )

    def _parse_roslynator_output(self, output: str) -> list[RefactorChange]:
        """Parse Roslynator CLI output.

        Args:
            output: Command stdout.

        Returns:
            List of RefactorChange objects.
        """
        changes: list[RefactorChange] = []

        for line in output.split("\n"):
            if ".cs" in line and ("modified" in line.lower() or "changed" in line.lower()):
                # Extract file path
                parts = line.strip().split()
                for part in parts:
                    if part.endswith(".cs"):
                        changes.append(
                            RefactorChange(
                                file_path=part,
                                original_content="",
                                new_content="",
                                description="Modified by Roslynator",
                            )
                        )
                        break

        return changes

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
        """Extract an interface from a C# class.

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
                    tool_used="Roslyn",
                    dry_run=True,
                )

            content = file_path.read_text(encoding="utf-8")

            method_sigs = self._extract_csharp_methods(content, class_name, methods)

            if not method_sigs:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"No public methods found in class '{class_name}'"],
                    tool_used="Roslyn",
                    dry_run=True,
                )

            interface_code = self._generate_csharp_interface(
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
                tool_used="Roslyn",
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
                tool_used="Roslyn",
                dry_run=True,
            )

    def _extract_csharp_methods(
        self,
        content: str,
        class_name: str,
        filter_methods: Sequence[str] | None,
        file_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Extract method signatures from a C# class using tree-sitter AST.

        Args:
            content: C# source code.
            class_name: Name of the class to extract from.
            filter_methods: Optional list of method names to include.
            file_path: Optional file path for AST parsing.

        Returns:
            List of method signature dictionaries.
        """
        signatures: list[dict[str, Any]] = []

        # Try tree-sitter first
        parse_result = self._parse_file(file_path or Path("temp.cs"), content)

        if parse_result:
            for symbol in parse_result.symbols:
                # Find methods in the target class
                if symbol.parent_name != class_name:
                    continue
                if symbol.kind != SymbolKind.METHOD:
                    continue
                if symbol.visibility != Visibility.PUBLIC:
                    continue

                # Filter if specified
                if filter_methods and symbol.name not in filter_methods:
                    continue

                # Build params string (C# style: Type name)
                params_parts = []
                for p in symbol.parameters:
                    if p.type_annotation:
                        params_parts.append(f"{p.type_annotation} {p.name}")
                    else:
                        params_parts.append(p.name)

                signatures.append({
                    "name": symbol.name,
                    "return_type": symbol.return_type or "void",
                    "params": ", ".join(params_parts),
                    "is_async": "async" in (symbol.modifiers or []),
                })

            return signatures

        # Fallback to regex if tree-sitter fails
        logger.warning("Tree-sitter not available, falling back to regex")
        return self._extract_csharp_methods_regex(content, class_name, filter_methods)

    def _extract_csharp_methods_regex(
        self,
        content: str,
        class_name: str,
        filter_methods: Sequence[str] | None,
    ) -> list[dict[str, Any]]:
        """Fallback regex-based method extraction for C#."""
        signatures: list[dict[str, Any]] = []

        # Find the class
        class_pattern = rf"class\s+{re.escape(class_name)}\s*(?::\s*[\w\s,<>]+)?{{"
        class_match = re.search(class_pattern, content)
        if not class_match:
            return signatures

        class_start = class_match.end()

        # Pattern: public [modifiers] ReturnType MethodName(params)
        method_pattern = (
            r"public\s+(?:(?:static|virtual|override|async)\s+)*"
            r"([\w<>\[\]?,\s]+?)\s+"  # Return type
            r"(\w+)\s*"  # Method name
            r"\(([^)]*)\)"  # Parameters
        )

        for match in re.finditer(method_pattern, content[class_start:]):
            return_type = match.group(1).strip()
            method_name = match.group(2)
            params = match.group(3).strip()

            # Skip constructors
            if method_name == class_name:
                continue

            # Filter if specified
            if filter_methods and method_name not in filter_methods:
                continue

            # Check if it's async
            is_async = "async" in content[class_start + match.start() - 20:class_start + match.start()]

            signatures.append({
                "name": method_name,
                "return_type": return_type,
                "params": params,
                "is_async": is_async,
            })

        return signatures

    def _generate_csharp_interface(
        self,
        interface_name: str,
        method_sigs: list[dict[str, Any]],
        original_content: str,
    ) -> str:
        """Generate a C# interface definition.

        Args:
            interface_name: Name for the interface.
            method_sigs: List of method signature dictionaries.
            original_content: Original source for namespace detection.

        Returns:
            C# code for the interface.
        """
        lines = []

        # Extract namespace from original file
        namespace_match = re.search(r"namespace\s+([\w.]+)", original_content)
        if namespace_match:
            lines.append(f"namespace {namespace_match.group(1)}")
            lines.append("{")

        lines.append(f"    public interface {interface_name}")
        lines.append("    {")

        for sig in method_sigs:
            params = sig["params"]
            return_type = sig["return_type"]

            # Handle async methods - interface should use Task return type
            # but we keep it as-is since the class already has proper return type
            lines.append(f"        {return_type} {sig['name']}({params});")

        lines.append("    }")

        if namespace_match:
            lines.append("}")

        return "\n".join(lines)

    def enforce_dependency(
        self,
        rule: CSharpDependencyRule,
        fix: bool = False,
    ) -> RefactorResult:
        """Check and report dependency violations in C# code.

        Analyzes using statements to find violations of dependency rules.

        Args:
            rule: The dependency rule to enforce.
            fix: If True, attempt to remove violating usings.

        Returns:
            RefactorResult with violations found.
        """
        try:
            violations = self._find_csharp_dependency_violations(rule)

            if not violations:
                return RefactorResult(
                    success=True,
                    changes=[],
                    errors=[],
                    tool_used="Roslyn",
                    dry_run=not fix,
                )

            changes: list[RefactorChange] = []
            errors: list[str] = []

            for violation in violations:
                if fix:
                    result = self._remove_csharp_using(violation)
                    if result.success:
                        changes.extend(result.changes)
                    else:
                        errors.extend(result.errors)
                else:
                    changes.append(
                        RefactorChange(
                            file_path=violation.file_path,
                            original_content=violation.using_statement,
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
                tool_used="Roslyn",
                dry_run=not fix,
                warnings=[f"Found {len(violations)} dependency violation(s)"],
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Enforce dependency failed: {e}"],
                tool_used="Roslyn",
                dry_run=not fix,
            )

    def _find_csharp_dependency_violations(
        self,
        rule: CSharpDependencyRule,
    ) -> list[CSharpDependencyViolation]:
        """Find all violations of a dependency rule in C# source files.

        Args:
            rule: The dependency rule to check.

        Returns:
            List of dependency violations.
        """
        violations: list[CSharpDependencyViolation] = []

        # Find all C# files that might be in the source namespace
        cs_files = list(self.project_root.rglob("*.cs"))

        for cs_file in cs_files:
            try:
                content = cs_file.read_text(encoding="utf-8")

                # Check if file is in source namespace
                in_source_namespace = (
                    f"namespace {rule.source_namespace}" in content
                    or re.search(
                        rf"namespace\s+{re.escape(rule.source_namespace)}[\.\s{{]",
                        content,
                    )
                )
                if not in_source_namespace:
                    continue

                file_violations = self._check_csharp_file_violations(
                    cs_file, content, rule
                )
                violations.extend(file_violations)

            except OSError:
                continue

        return violations

    def _check_csharp_file_violations(
        self,
        file_path: Path,
        content: str,
        rule: CSharpDependencyRule,
    ) -> list[CSharpDependencyViolation]:
        """Check a single C# file for dependency violations.

        Args:
            file_path: Path to the source file.
            content: File content.
            rule: The dependency rule to check.

        Returns:
            List of violations in this file.
        """
        violations: list[CSharpDependencyViolation] = []
        lines = content.split("\n")

        source_class = file_path.stem

        for i, line in enumerate(lines, 1):
            # Check for using statements that violate the rule
            # C#: using Company.Forbidden.Namespace;
            using_match = re.match(r"using\s+([\w.]+)\s*;", line)
            if using_match:
                namespace = using_match.group(1)
                if namespace.startswith(rule.target_namespace):
                    violations.append(
                        CSharpDependencyViolation(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line=i,
                            using_statement=line.strip(),
                            source_class=source_class,
                            target_namespace=namespace,
                        )
                    )

        return violations

    def _remove_csharp_using(
        self, violation: CSharpDependencyViolation
    ) -> RefactorResult:
        """Remove a using statement that violates dependency rules.

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
                            description=f"Removed using at line {violation.line}",
                            line_start=violation.line,
                            line_end=violation.line,
                        )
                    ],
                    errors=[],
                    tool_used="Roslyn",
                    dry_run=False,
                )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Failed to remove using: {e}"],
                tool_used="Roslyn",
                dry_run=False,
            )

        return RefactorResult(
            success=False,
            changes=[],
            errors=["Could not find line to remove"],
            tool_used="Roslyn",
            dry_run=False,
        )
