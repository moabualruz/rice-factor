"""Rope adapter for Python refactoring.

Rope is a Python library that provides automated refactoring capabilities.
This adapter uses Rope to perform AST-based refactoring for Python code.

Documentation: https://github.com/python-rope/rope
"""

from __future__ import annotations

import ast
import contextlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
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


# Check for rope availability
try:
    import rope.base.project
    import rope.refactor.extract
    import rope.refactor.move
    import rope.refactor.rename

    # Verify imports are usable (prevents false positives in type checking)
    _PROJECT_CLASS = rope.base.project.Project
    _RENAME_CLASS = rope.refactor.rename.Rename
    _MOVE_CLASS = rope.refactor.move.MoveModule
    _EXTRACT_METHOD_CLASS = rope.refactor.extract.ExtractMethod
    _EXTRACT_VAR_CLASS = rope.refactor.extract.ExtractVariable

    ROPE_AVAILABLE = True
except ImportError:
    ROPE_AVAILABLE = False


@dataclass
class DependencyRule:
    """Rule for dependency enforcement.

    Attributes:
        source_module: The module that should not depend on target.
        target_module: The module that should not be imported by source.
        allow_transitive: Whether transitive dependencies are allowed.
    """

    source_module: str
    target_module: str
    allow_transitive: bool = False


@dataclass
class DependencyViolation:
    """A dependency violation found during analysis.

    Attributes:
        file_path: Path to the file with the violation.
        line: Line number of the violation.
        import_statement: The import statement that violates the rule.
        source_module: Module doing the importing.
        target_module: Module being imported.
    """

    file_path: str
    line: int
    import_statement: str
    source_module: str
    target_module: str


class RopeAdapter(RefactorToolPort):
    """Adapter for Rope (Python refactoring library).

    Uses Rope to perform AST-based refactoring for Python code.
    Supports move_file, rename_symbol, extract_interface, and enforce_dependency.

    Attributes:
        project_root: Root directory of the Python project.
    """

    LANGUAGES: ClassVar[list[str]] = ["python"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
        RefactorOperation.MOVE,
        RefactorOperation.EXTRACT_METHOD,
        RefactorOperation.EXTRACT_VARIABLE,
    ]

    def __init__(
        self,
        project_root: Path,
        ropefolder: str | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the Python project.
            ropefolder: Optional name for the rope project folder.
                        Defaults to None (uses .ropeproject).
        """
        self.project_root = project_root
        self._ropefolder = ropefolder
        self._version: str | None = None
        self._project: Any = None

    def _get_project(self) -> Any:
        """Get or create the Rope project.

        Returns:
            Rope Project instance.

        Raises:
            RuntimeError: If rope is not available.
        """
        if not ROPE_AVAILABLE:
            raise RuntimeError("Rope is not installed")

        if self._project is None:
            import rope.base.project

            self._project = rope.base.project.Project(
                str(self.project_root),
                ropefolder=self._ropefolder,
            )
        return self._project

    def get_supported_languages(self) -> list[str]:
        """Return supported languages."""
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return supported refactoring operations."""
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if Rope is installed.

        Returns:
            True if rope is available.
        """
        return ROPE_AVAILABLE

    def get_version(self) -> str | None:
        """Get Rope version.

        Returns:
            Version string or None.
        """
        if not ROPE_AVAILABLE:
            return None

        if self._version:
            return self._version

        try:
            import rope

            self._version = getattr(rope, "__version__", "unknown")
        except (ImportError, AttributeError):
            pass

        return self._version

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring via Rope.

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
                errors=["Rope is not installed (try: pip install rope)"],
                tool_used="rope",
                dry_run=dry_run,
            )

        if request.operation == RefactorOperation.RENAME:
            return self._rename(request, dry_run)
        elif request.operation == RefactorOperation.MOVE:
            return self._move(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_METHOD:
            return self._extract_method(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_VARIABLE:
            return self._extract_variable(request, dry_run)

        return RefactorResult(
            success=False,
            changes=[],
            errors=[f"Operation {request.operation} not supported by Rope adapter"],
            tool_used="rope",
            dry_run=dry_run,
        )

    def _rename(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Perform rename refactoring using Rope.

        Args:
            request: The rename request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        if not request.new_value:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["new_value is required for rename operation"],
                tool_used="rope",
                dry_run=dry_run,
            )

        try:
            import rope.refactor.rename

            project = self._get_project()

            # Determine file and offset
            if request.file_path:
                file_path = Path(request.file_path)
                if not file_path.is_absolute():
                    file_path = self.project_root / file_path
            else:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=["file_path is required for rename operation"],
                    tool_used="rope",
                    dry_run=dry_run,
                )

            # Get rope resource
            resource = project.get_resource(str(file_path.relative_to(self.project_root)))
            # Find offset of the symbol
            content = file_path.read_text(encoding="utf-8")
            offset = self._find_symbol_offset(content, request.target, request.line)

            if offset < 0:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"Symbol '{request.target}' not found in {file_path}"],
                    tool_used="rope",
                    dry_run=dry_run,
                )

            # Create rename refactoring
            rename = rope.refactor.rename.Rename(project, resource, offset)
            changes = rename.get_changes(request.new_value)

            # Convert to RefactorChange list
            change_list = self._convert_changes(changes, project)

            if not dry_run:
                project.do(changes)
            return RefactorResult(
                success=True,
                changes=change_list,
                errors=[],
                tool_used="rope",
                dry_run=dry_run,
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Rename failed: {e}"],
                tool_used="rope",
                dry_run=dry_run,
            )

    def _move(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Move file and update all references.

        Args:
            request: The move request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        if not request.new_value:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["new_value (new path) is required for move operation"],
                tool_used="rope",
                dry_run=dry_run,
            )

        try:
            import rope.refactor.move

            project = self._get_project()

            source_path = Path(request.target)
            if not source_path.is_absolute():
                source_path = self.project_root / source_path

            if not source_path.exists():
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"Source file not found: {request.target}"],
                    tool_used="rope",
                    dry_run=dry_run,
                )

            dest_path = Path(request.new_value)
            if not dest_path.is_absolute():
                dest_path = self.project_root / dest_path

            # Get rope resources
            source_resource = project.get_resource(
                str(source_path.relative_to(self.project_root))
            )

            # Destination folder
            dest_folder_str = str(dest_path.parent.relative_to(self.project_root))
            if dest_folder_str == ".":
                dest_folder = project.root
            else:
                dest_folder = project.get_resource(dest_folder_str)

            # Create move refactoring
            mover = rope.refactor.move.MoveModule(project, source_resource)
            changes = mover.get_changes(dest_folder)

            # Convert to RefactorChange list
            change_list = self._convert_changes(changes, project)

            # Add the file move itself
            change_list.append(
                RefactorChange(
                    file_path=str(source_path.relative_to(self.project_root)),
                    original_content=str(source_path.relative_to(self.project_root)),
                    new_content=str(dest_path.relative_to(self.project_root)),
                    description=f"Moved file from {request.target} to {request.new_value}",
                )
            )

            if not dry_run:
                project.do(changes)
            return RefactorResult(
                success=True,
                changes=change_list,
                errors=[],
                tool_used="rope",
                dry_run=dry_run,
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Move failed: {e}"],
                tool_used="rope",
                dry_run=dry_run,
            )

    def _extract_method(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Extract method from selected code.

        Args:
            request: The extract method request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        if not request.new_value:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["new_value (method name) is required for extract_method"],
                tool_used="rope",
                dry_run=dry_run,
            )

        if not request.file_path:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["file_path is required for extract_method"],
                tool_used="rope",
                dry_run=dry_run,
            )

        if request.line is None:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["line is required for extract_method (start line of code)"],
                tool_used="rope",
                dry_run=dry_run,
            )

        try:
            import rope.refactor.extract

            project = self._get_project()

            file_path = Path(request.file_path)
            if not file_path.is_absolute():
                file_path = self.project_root / file_path

            resource = project.get_resource(str(file_path.relative_to(self.project_root)))
            # Read file content
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Get the start and end offset from line numbers
            # request.parameters can contain 'end_line' for the selection
            end_line = request.line
            if request.parameters and "end_line" in request.parameters:
                end_line = int(request.parameters["end_line"])

            start_offset = sum(len(line) + 1 for line in lines[: request.line - 1])
            end_offset = sum(len(line) + 1 for line in lines[:end_line])

            # Create extract method refactoring
            extractor = rope.refactor.extract.ExtractMethod(
                project,                  resource,
                start_offset,
                end_offset,
            )
            changes = extractor.get_changes(request.new_value)

            # Convert to RefactorChange list
            change_list = self._convert_changes(changes, project)

            if not dry_run:
                project.do(changes)
            return RefactorResult(
                success=True,
                changes=change_list,
                errors=[],
                tool_used="rope",
                dry_run=dry_run,
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Extract method failed: {e}"],
                tool_used="rope",
                dry_run=dry_run,
            )

    def _extract_variable(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Extract variable from selected expression.

        Args:
            request: The extract variable request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        if not request.new_value:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["new_value (variable name) is required for extract_variable"],
                tool_used="rope",
                dry_run=dry_run,
            )

        if not request.file_path:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["file_path is required for extract_variable"],
                tool_used="rope",
                dry_run=dry_run,
            )

        try:
            import rope.refactor.extract

            project = self._get_project()

            file_path = Path(request.file_path)
            if not file_path.is_absolute():
                file_path = self.project_root / file_path

            resource = project.get_resource(str(file_path.relative_to(self.project_root)))
            # Read file content
            content = file_path.read_text(encoding="utf-8")

            # Find the expression offset
            offset = content.find(request.target)
            if offset < 0:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"Expression '{request.target}' not found in {file_path}"],
                    tool_used="rope",
                    dry_run=dry_run,
                )

            end_offset = offset + len(request.target)

            # Create extract variable refactoring
            extractor = rope.refactor.extract.ExtractVariable(
                project,                  resource,
                offset,
                end_offset,
            )
            changes = extractor.get_changes(request.new_value)

            # Convert to RefactorChange list
            change_list = self._convert_changes(changes, project)

            if not dry_run:
                project.do(changes)
            return RefactorResult(
                success=True,
                changes=change_list,
                errors=[],
                tool_used="rope",
                dry_run=dry_run,
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Extract variable failed: {e}"],
                tool_used="rope",
                dry_run=dry_run,
            )

    def extract_interface(
        self,
        file_path: Path,
        class_name: str,
        interface_name: str,
        methods: Sequence[str] | None = None,
    ) -> RefactorResult:
        """Extract a Protocol/ABC interface from a concrete class.

        This creates a typing.Protocol or abc.ABC from the public methods
        of a concrete class.

        Args:
            file_path: Path to the file containing the class.
            class_name: Name of the concrete class.
            interface_name: Name for the generated interface/protocol.
            methods: Optional list of method names to include.
                     If None, includes all public methods.

        Returns:
            RefactorResult with the generated protocol code.
        """
        try:
            # Read the file
            if not file_path.is_absolute():
                file_path = self.project_root / file_path

            content = file_path.read_text(encoding="utf-8")

            # Parse the AST
            tree = ast.parse(content)

            # Find the class
            class_def = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    class_def = node
                    break

            if class_def is None:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"Class '{class_name}' not found in {file_path}"],
                    tool_used="rope",
                    dry_run=True,
                )

            # Extract method signatures
            method_sigs = self._extract_method_signatures(class_def, methods)

            if not method_sigs:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"No public methods found in class '{class_name}'"],
                    tool_used="rope",
                    dry_run=True,
                )

            # Generate Protocol definition
            protocol_code = self._generate_protocol(interface_name, method_sigs)

            # Create the change
            change = RefactorChange(
                file_path=str(file_path.relative_to(self.project_root)),
                original_content="",
                new_content=protocol_code,
                description=f"Generated Protocol '{interface_name}' from class '{class_name}'",
            )

            return RefactorResult(
                success=True,
                changes=[change],
                errors=[],
                tool_used="rope",
                dry_run=True,
                warnings=[
                    "Protocol generated but not automatically inserted into file",
                    "Review and add to appropriate location",
                ],
            )

        except SyntaxError as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Syntax error in {file_path}: {e}"],
                tool_used="rope",
                dry_run=True,
            )
        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Extract interface failed: {e}"],
                tool_used="rope",
                dry_run=True,
            )

    def _extract_method_signatures(
        self,
        class_def: ast.ClassDef,
        filter_methods: Sequence[str] | None,
    ) -> list[dict[str, str]]:
        """Extract method signatures from a class definition.

        Args:
            class_def: The AST ClassDef node.
            filter_methods: Optional list of method names to include.

        Returns:
            List of method signature dictionaries.
        """
        signatures = []

        for node in class_def.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Skip private/dunder methods
            if node.name.startswith("_"):
                continue

            # Filter if specified
            if filter_methods and node.name not in filter_methods:
                continue

            sig = self._get_method_signature(node)
            signatures.append(sig)

        return signatures

    def _get_method_signature(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> dict[str, str]:
        """Get the signature of a method.

        Args:
            func: The function/method AST node.

        Returns:
            Dictionary with name, args, and return_type.
        """
        # Get arguments (excluding self)
        args = []
        for arg in func.args.args[1:]:  # Skip self
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # Get return type
        return_type = "None"
        if func.returns:
            return_type = ast.unparse(func.returns)

        is_async = isinstance(func, ast.AsyncFunctionDef)

        return {
            "name": func.name,
            "args": ", ".join(args),
            "return_type": return_type,
            "is_async": "async " if is_async else "",
        }

    def _generate_protocol(
        self,
        interface_name: str,
        method_sigs: list[dict[str, str]],
    ) -> str:
        """Generate a Protocol class definition.

        Args:
            interface_name: Name for the protocol.
            method_sigs: List of method signature dictionaries.

        Returns:
            Python code for the protocol.
        """
        lines = [
            "from typing import Protocol",
            "",
            "",
            f"class {interface_name}(Protocol):",
            f'    """Protocol interface for {interface_name}."""',
            "",
        ]

        for sig in method_sigs:
            args = sig["args"]
            args = f"self, {args}" if args else "self"

            lines.append(
                f"    {sig['is_async']}def {sig['name']}({args}) -> {sig['return_type']}:"
            )
            lines.append("        ...")
            lines.append("")

        return "\n".join(lines)

    def enforce_dependency(
        self,
        rule: DependencyRule,
        fix: bool = False,
    ) -> RefactorResult:
        """Check and optionally fix dependency violations.

        Analyzes import statements to find violations of dependency rules.

        Args:
            rule: The dependency rule to enforce.
            fix: If True, attempt to remove violating imports.

        Returns:
            RefactorResult with violations found and changes made.
        """
        try:
            violations = self._find_dependency_violations(rule)

            if not violations:
                return RefactorResult(
                    success=True,
                    changes=[],
                    errors=[],
                    tool_used="rope",
                    dry_run=not fix,
                )

            changes: list[RefactorChange] = []
            errors: list[str] = []

            for violation in violations:
                if fix:
                    # Try to remove the violating import
                    result = self._remove_import(violation)
                    if result.success:
                        changes.extend(result.changes)
                    else:
                        errors.extend(result.errors)
                else:
                    # Just report the violation
                    changes.append(
                        RefactorChange(
                            file_path=violation.file_path,
                            original_content=violation.import_statement,
                            new_content="",
                            description=(
                                f"Dependency violation: {violation.source_module} "
                                f"imports {violation.target_module} at line {violation.line}"
                            ),
                        )
                    )

            return RefactorResult(
                success=len(errors) == 0,
                changes=changes,
                errors=errors,
                tool_used="rope",
                dry_run=not fix,
                warnings=[f"Found {len(violations)} dependency violation(s)"],
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Enforce dependency failed: {e}"],
                tool_used="rope",
                dry_run=not fix,
            )

    def _find_dependency_violations(
        self,
        rule: DependencyRule,
    ) -> list[DependencyViolation]:
        """Find all violations of a dependency rule.

        Args:
            rule: The dependency rule to check.

        Returns:
            List of dependency violations.
        """
        violations: list[DependencyViolation] = []

        # Find all Python files in the source module
        source_path = self.project_root / rule.source_module.replace(".", "/")

        if source_path.is_file():
            files = [source_path.with_suffix(".py")]
        elif source_path.is_dir():
            files = list(source_path.rglob("*.py"))
        else:
            # Try as a file
            source_path = source_path.with_suffix(".py")
            files = [source_path] if source_path.exists() else []

        for py_file in files:
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith(rule.target_module):
                                violations.append(
                                    DependencyViolation(
                                        file_path=str(
                                            py_file.relative_to(self.project_root)
                                        ),
                                        line=node.lineno,
                                        import_statement=f"import {alias.name}",
                                        source_module=rule.source_module,
                                        target_module=alias.name,
                                    )
                                )

                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        if module.startswith(rule.target_module):
                            names = ", ".join(a.name for a in node.names)
                            violations.append(
                                DependencyViolation(
                                    file_path=str(
                                        py_file.relative_to(self.project_root)
                                    ),
                                    line=node.lineno,
                                    import_statement=f"from {module} import {names}",
                                    source_module=rule.source_module,
                                    target_module=module,
                                )
                            )

            except (SyntaxError, OSError):
                continue

        return violations

    def _remove_import(self, violation: DependencyViolation) -> RefactorResult:
        """Remove an import statement that violates dependency rules.

        Args:
            violation: The violation to fix.

        Returns:
            RefactorResult indicating success/failure.
        """
        try:
            file_path = self.project_root / violation.file_path
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Remove the import line
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
                            description=f"Removed import at line {violation.line}",
                            line_start=violation.line,
                            line_end=violation.line,
                        )
                    ],
                    errors=[],
                    tool_used="rope",
                    dry_run=False,
                )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Failed to remove import: {e}"],
                tool_used="rope",
                dry_run=False,
            )

        return RefactorResult(
            success=False,
            changes=[],
            errors=["Could not find line to remove"],
            tool_used="rope",
            dry_run=False,
        )

    def _find_symbol_offset(
        self,
        content: str,
        symbol: str,
        line: int | None = None,
    ) -> int:
        """Find the byte offset of a symbol in content.

        Args:
            content: The file content.
            symbol: The symbol to find.
            line: Optional line number to search at.

        Returns:
            Byte offset or -1 if not found.
        """
        if line is not None:
            # Search only on the specified line
            lines = content.split("\n")
            if 0 < line <= len(lines):
                line_content = lines[line - 1]
                col = line_content.find(symbol)
                if col >= 0:
                    # Calculate offset
                    offset = sum(len(lines[i]) + 1 for i in range(line - 1))
                    return offset + col

        # Search entire content
        import re

        # Use word boundary for identifier search
        pattern = rf"\b{re.escape(symbol)}\b"
        match = re.search(pattern, content)
        if match:
            return match.start()

        return -1

    def _convert_changes(
        self,
        rope_changes: Any,
        _project: Any,
    ) -> list[RefactorChange]:
        """Convert Rope ChangeSet to RefactorChange list.

        Args:
            rope_changes: Rope ChangeSet object.
            project: Rope Project object.

        Returns:
            List of RefactorChange objects.
        """
        changes: list[RefactorChange] = []

        try:
            # Get changed files from rope changes
            description = str(rope_changes)
            resources: list[Any] = getattr(rope_changes, "get_changed_resources", lambda: [])()

            for resource in resources:
                path = getattr(resource, "path", str(resource))
                changes.append(
                    RefactorChange(
                        file_path=path,
                        original_content="",
                        new_content="",
                        description=description,
                    )
                )

        except Exception:
            # Fallback: create a generic change entry
            changes.append(
                RefactorChange(
                    file_path="(multiple files)",
                    original_content="",
                    new_content="",
                    description=str(rope_changes),
                )
            )

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

    def close(self) -> None:
        """Close the Rope project and cleanup resources."""
        if self._project is not None:
            with contextlib.suppress(Exception):
                self._project.close()
            self._project = None
