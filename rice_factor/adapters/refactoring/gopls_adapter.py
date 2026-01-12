"""gopls adapter for Go refactoring.

gopls is the official Go language server that provides refactoring
capabilities through LSP. This adapter uses:
- Tree-sitter for AST-based operations (extract_interface, enforce_dependency)
- gorename/gopls for semantic operations (rename)
"""

import logging
import subprocess
from pathlib import Path
from typing import ClassVar

from rice_factor.domain.ports.refactor import (
    RefactorChange,
    RefactorOperation,
    RefactorRequest,
    RefactorResult,
    RefactorToolPort,
)

logger = logging.getLogger(__name__)


class GoplsAdapter(RefactorToolPort):
    """Adapter for Go refactoring with tree-sitter AST and gopls LSP.

    Uses tree-sitter for structural operations (extract_interface, enforce_dependency)
    and gopls/gorename for semantic operations (rename).

    Attributes:
        project_root: Root directory of the Go project.
    """

    LANGUAGES: ClassVar[list[str]] = ["go"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
        RefactorOperation.EXTRACT_INTERFACE,
        RefactorOperation.ENFORCE_DEPENDENCY,
        RefactorOperation.EXTRACT_METHOD,
        RefactorOperation.INLINE,
    ]

    def __init__(self, project_root: Path) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the Go project.
        """
        self.project_root = project_root
        self._version: str | None = None

    def get_supported_languages(self) -> list[str]:
        """Return supported languages (Go only)."""
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return supported refactoring operations."""
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if gopls is installed.

        Returns:
            True if gopls is available.
        """
        try:
            result = subprocess.run(
                ["gopls", "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_version(self) -> str | None:
        """Get gopls version.

        Returns:
            Version string or None.
        """
        if self._version:
            return self._version

        try:
            result = subprocess.run(
                ["gopls", "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Parse version from output like "gopls v0.14.0"
                output = result.stdout.strip()
                if "v" in output:
                    self._version = output.split("v")[-1].split()[0]
                else:
                    self._version = output.split()[-1] if output else None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return self._version

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring via gopls/gorename.

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
                errors=["gopls is not installed"],
                tool_used="gopls",
                dry_run=dry_run,
            )

        if request.operation == RefactorOperation.RENAME:
            return self._rename(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_INTERFACE:
            return self._extract_interface(request, dry_run)
        elif request.operation == RefactorOperation.ENFORCE_DEPENDENCY:
            return self._enforce_dependency(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_METHOD:
            return self._extract_method(request, dry_run)
        elif request.operation == RefactorOperation.INLINE:
            return self._inline(request, dry_run)

        return RefactorResult(
            success=False,
            changes=[],
            errors=[f"Operation {request.operation} not supported"],
            tool_used="gopls",
            dry_run=dry_run,
        )

    def _rename(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Perform rename refactoring using gorename.

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
                tool_used="gorename",
                dry_run=dry_run,
            )

        # Build the target identifier
        # gorename expects format: "package.Symbol" or "file.go:#offset"
        target = request.target
        if request.file_path and request.line and request.column:
            # Use offset-based targeting
            target = f"{request.file_path}:#{request.line}:{request.column}"

        cmd = ["gorename", "-from", target, "-to", request.new_value]

        if dry_run:
            cmd.append("-d")  # Dry-run flag for gorename

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["gorename command timed out"],
                tool_used="gorename",
                dry_run=dry_run,
            )
        except FileNotFoundError:
            # gorename might not be installed, try gopls rename
            return self._gopls_rename(request, dry_run)

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            # If gorename fails, it might not be installed
            if "not found" in error_msg.lower():
                return self._gopls_rename(request, dry_run)
            return RefactorResult(
                success=False,
                changes=[],
                errors=[error_msg],
                tool_used="gorename",
                dry_run=dry_run,
            )

        changes = self._parse_diff_output(result.stdout, request)

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="gorename",
            dry_run=dry_run,
        )

    def _gopls_rename(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Fallback rename using gopls directly.

        Args:
            request: The rename request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        # gopls rename requires LSP protocol
        # For CLI usage, we can use gopls rename command if available
        cmd = [
            "gopls",
            "rename",
            "-w" if not dry_run else "-d",
        ]

        if request.file_path:
            cmd.append(f"{request.file_path}:{request.line or 1}:{request.column or 1}")
        else:
            cmd.append(request.target)

        if request.new_value:
            cmd.append(request.new_value)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[str(e)],
                tool_used="gopls",
                dry_run=dry_run,
            )

        if result.returncode != 0:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[result.stderr or result.stdout or "Unknown error"],
                tool_used="gopls",
                dry_run=dry_run,
            )

        changes = self._parse_diff_output(result.stdout, request)

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="gopls",
            dry_run=dry_run,
        )

    def _extract_interface(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Extract interface from a Go struct using tree-sitter AST.

        Parses the struct and its methods, generates an interface definition.

        Args:
            request: The extract interface request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with the generated interface.
        """
        if not request.file_path:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["file_path is required for extract_interface"],
                tool_used="tree-sitter",
                dry_run=dry_run,
            )

        try:
            from rice_factor.adapters.parsing import TreeSitterAdapter
            from rice_factor.domain.ports.ast import SymbolKind, Visibility

            parser = TreeSitterAdapter()
            if not parser.is_available():
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[
                        "tree-sitter not available. Install: pip install tree-sitter-language-pack"
                    ],
                    tool_used="tree-sitter",
                    dry_run=dry_run,
                )

            # Parse the file
            result = parser.parse_file(request.file_path)
            if not result.success:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=result.errors,
                    tool_used="tree-sitter",
                    dry_run=dry_run,
                )

            # Find the target struct
            target_struct = None
            for symbol in result.symbols:
                if symbol.kind == SymbolKind.STRUCT and symbol.name == request.target:
                    target_struct = symbol
                    break

            if not target_struct:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"Struct '{request.target}' not found in {request.file_path}"],
                    tool_used="tree-sitter",
                    dry_run=dry_run,
                )

            # Find all public methods with this struct as receiver
            methods = [
                s
                for s in result.symbols
                if s.kind == SymbolKind.METHOD
                and s.parent_name == request.target
                and s.visibility == Visibility.PUBLIC
            ]

            if not methods:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"No public methods found for struct '{request.target}'"],
                    tool_used="tree-sitter",
                    dry_run=dry_run,
                )

            # Generate interface name
            interface_name = request.new_value or f"{request.target}er"

            # Generate interface definition
            interface_lines = [f"type {interface_name} interface {{"]
            for method in methods:
                # Build method signature
                params = ", ".join(
                    f"{p.name} {p.type_annotation}" if p.type_annotation else p.name
                    for p in method.parameters
                    if p.name != "self"  # Skip receiver
                )
                return_type = method.return_type or ""
                if return_type:
                    interface_lines.append(f"\t{method.name}({params}) {return_type}")
                else:
                    interface_lines.append(f"\t{method.name}({params})")
            interface_lines.append("}")
            interface_code = "\n".join(interface_lines)

            # Read original file
            file_path = Path(request.file_path)
            original_content = file_path.read_text(encoding="utf-8")

            # Insert interface after struct definition
            insert_position = target_struct.line_end
            lines = original_content.split("\n")
            new_lines = [
                *lines[:insert_position],
                "",
                interface_code,
                "",
                *lines[insert_position:],
            ]
            new_content = "\n".join(new_lines)

            changes = [
                RefactorChange(
                    file_path=str(file_path),
                    original_content=original_content,
                    new_content=new_content,
                    description=f"Extracted interface {interface_name} from {request.target}",
                )
            ]

            if not dry_run:
                file_path.write_text(new_content, encoding="utf-8")

            return RefactorResult(
                success=True,
                changes=changes,
                errors=[],
                tool_used="tree-sitter",
                dry_run=dry_run,
            )

        except Exception as e:
            logger.error(f"Error in extract_interface: {e}")
            return RefactorResult(
                success=False,
                changes=[],
                errors=[str(e)],
                tool_used="tree-sitter",
                dry_run=dry_run,
            )

    def _enforce_dependency(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Analyze and enforce dependency rules using tree-sitter AST.

        Parses imports and checks against dependency rules.

        Args:
            request: The enforce dependency request.
            dry_run: If True, only report violations.

        Returns:
            RefactorResult with dependency violations.
        """
        if not request.file_path:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["file_path is required for enforce_dependency"],
                tool_used="tree-sitter",
                dry_run=dry_run,
            )

        try:
            from rice_factor.adapters.parsing import TreeSitterAdapter

            parser = TreeSitterAdapter()
            if not parser.is_available():
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[
                        "tree-sitter not available. Install: pip install tree-sitter-language-pack"
                    ],
                    tool_used="tree-sitter",
                    dry_run=dry_run,
                )

            # Parse the file
            result = parser.parse_file(request.file_path)
            if not result.success:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=result.errors,
                    tool_used="tree-sitter",
                    dry_run=dry_run,
                )

            # Get imports
            imports = result.imports

            # Parse dependency rules from request.dependency_rules
            rules = request.dependency_rules or {}
            forbidden = rules.get("forbidden", [])
            allowed = rules.get("allowed", [])

            violations: list[str] = []
            for imp in imports:
                # Check forbidden imports
                for pattern in forbidden:
                    if pattern in imp.module:
                        violations.append(
                            f"Line {imp.line}: Forbidden import '{imp.module}' (matches '{pattern}')"
                        )

                # Check if import is in allowed list (if allowed list is specified)
                if allowed and not any(pattern in imp.module for pattern in allowed):
                    violations.append(
                        f"Line {imp.line}: Import '{imp.module}' not in allowed list"
                    )

            if violations:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=violations,
                    tool_used="tree-sitter",
                    dry_run=dry_run,
                    warnings=[f"Found {len(violations)} dependency violations"],
                )

            return RefactorResult(
                success=True,
                changes=[],
                errors=[],
                tool_used="tree-sitter",
                dry_run=dry_run,
            )

        except Exception as e:
            logger.error(f"Error in enforce_dependency: {e}")
            return RefactorResult(
                success=False,
                changes=[],
                errors=[str(e)],
                tool_used="tree-sitter",
                dry_run=dry_run,
            )

    def _extract_method(
        self,
        _request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Extract method refactoring (not yet fully supported via CLI).

        Args:
            _request: The extract method request (unused, not supported).
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult indicating not supported.
        """
        return RefactorResult(
            success=False,
            changes=[],
            errors=["Extract method requires LSP client (IDE integration)"],
            tool_used="gopls",
            dry_run=dry_run,
            warnings=["Consider using an IDE with gopls for this operation"],
        )

    def _inline(
        self,
        _request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Inline refactoring (not yet fully supported via CLI).

        Args:
            _request: The inline request (unused, not supported).
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult indicating not supported.
        """
        return RefactorResult(
            success=False,
            changes=[],
            errors=["Inline requires LSP client (IDE integration)"],
            tool_used="gopls",
            dry_run=dry_run,
            warnings=["Consider using an IDE with gopls for this operation"],
        )

    def _parse_diff_output(
        self,
        output: str,
        request: RefactorRequest,
    ) -> list[RefactorChange]:
        """Parse diff output from gorename/gopls.

        Args:
            output: Command output (usually unified diff).
            request: Original request for context.

        Returns:
            List of RefactorChange objects.
        """
        changes: list[RefactorChange] = []
        current_file: str | None = None
        original_lines: list[str] = []
        new_lines: list[str] = []

        for line in output.split("\n"):
            if line.startswith("--- "):
                # Start of new file diff
                if current_file and (original_lines or new_lines):
                    changes.append(
                        RefactorChange(
                            file_path=current_file,
                            original_content="\n".join(original_lines),
                            new_content="\n".join(new_lines),
                            description=f"Renamed {request.target} to {request.new_value}",
                        )
                    )
                current_file = line[4:].split("\t")[0]
                original_lines = []
                new_lines = []
            elif line.startswith("+++ "):
                # New file path (usually same as ---)
                pass
            elif line.startswith("-") and not line.startswith("---"):
                original_lines.append(line[1:])
            elif line.startswith("+") and not line.startswith("+++"):
                new_lines.append(line[1:])

        # Don't forget the last file
        if current_file and (original_lines or new_lines):
            changes.append(
                RefactorChange(
                    file_path=current_file,
                    original_content="\n".join(original_lines),
                    new_content="\n".join(new_lines),
                    description=f"Renamed {request.target} to {request.new_value}",
                )
            )

        return changes

    def rollback(self, _result: RefactorResult) -> bool:
        """Rollback changes using git.

        Args:
            _result: Result from previous execute() call (unused, git restores all).

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
