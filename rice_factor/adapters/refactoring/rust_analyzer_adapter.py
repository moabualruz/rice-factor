"""rust-analyzer adapter for Rust refactoring.

rust-analyzer provides AST-based refactoring for Rust through LSP.
This adapter uses rust-analyzer and cargo for Rust-native refactoring.

Now enhanced with tree-sitter AST for:
- extract_interface: Parse struct/impl to generate trait definition
- enforce_dependency: Parse use statements and check against rules
"""

import logging
import subprocess
from pathlib import Path
from typing import ClassVar

from rice_factor.adapters.parsing.treesitter_adapter import TreeSitterAdapter
from rice_factor.domain.ports.ast import ParseResult, SymbolKind, Visibility
from rice_factor.domain.ports.refactor import (
    RefactorChange,
    RefactorOperation,
    RefactorRequest,
    RefactorResult,
    RefactorToolPort,
)

logger = logging.getLogger(__name__)


class RustAnalyzerAdapter(RefactorToolPort):
    """Adapter for rust-analyzer.

    Provides Rust refactoring capabilities through rust-analyzer
    and cargo. Some operations require LSP client support.

    Attributes:
        project_root: Root directory of the Rust project.
    """

    LANGUAGES: ClassVar[list[str]] = ["rust"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
        RefactorOperation.EXTRACT_METHOD,
        RefactorOperation.INLINE,
        RefactorOperation.EXTRACT_INTERFACE,
        RefactorOperation.ENFORCE_DEPENDENCY,
    ]

    def __init__(self, project_root: Path) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the Rust project.
        """
        self.project_root = project_root
        self._version: str | None = None
        self._ast_adapter: TreeSitterAdapter | None = None

    def get_supported_languages(self) -> list[str]:
        """Return supported languages (Rust only)."""
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return supported refactoring operations."""
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if rust-analyzer is installed.

        Returns:
            True if rust-analyzer is available.
        """
        try:
            result = subprocess.run(
                ["rust-analyzer", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_version(self) -> str | None:
        """Get rust-analyzer version.

        Returns:
            Version string or None.
        """
        if self._version:
            return self._version

        try:
            result = subprocess.run(
                ["rust-analyzer", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Parse version from output like "rust-analyzer 2024-01-15"
                output = result.stdout.strip()
                parts = output.split()
                if len(parts) >= 2:
                    self._version = parts[-1]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return self._version

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring via rust-analyzer.

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
                errors=["rust-analyzer is not installed"],
                tool_used="rust-analyzer",
                dry_run=dry_run,
            )

        if request.operation == RefactorOperation.RENAME:
            return self._rename(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_METHOD:
            return self._extract_method(request, dry_run)
        elif request.operation == RefactorOperation.INLINE:
            return self._inline(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_INTERFACE:
            return self._extract_interface(request, dry_run)
        elif request.operation == RefactorOperation.ENFORCE_DEPENDENCY:
            return self._enforce_dependency(request, dry_run)

        return RefactorResult(
            success=False,
            changes=[],
            errors=[f"Operation {request.operation} not supported"],
            tool_used="rust-analyzer",
            dry_run=dry_run,
        )

    def _rename(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Perform rename refactoring.

        rust-analyzer rename is primarily available via LSP protocol.
        For CLI, we attempt to use ra-multiplex or similar tools if available,
        otherwise fall back to sed-based replacement with cargo check validation.

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
                tool_used="rust-analyzer",
                dry_run=dry_run,
            )

        # Try rust-analyzer analysis command for LSP-based rename
        # Note: This requires rust-analyzer to be running as a server
        # For CLI-based rename, we use a safer approach

        # First, find all occurrences
        changes = self._find_and_replace(request, dry_run)

        if not changes:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[
                    "No occurrences found or rename requires LSP client",
                    "Consider using an IDE with rust-analyzer for complex renames",
                ],
                tool_used="rust-analyzer",
                dry_run=dry_run,
            )

        # If not dry run, apply changes and validate with cargo check
        if not dry_run:
            validation_result = self._validate_changes()
            if not validation_result:
                self.rollback(
                    RefactorResult(
                        success=False,
                        changes=changes,
                        errors=[],
                        tool_used="rust-analyzer",
                        dry_run=False,
                    )
                )
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=["Rename caused compilation errors, rolled back"],
                    tool_used="rust-analyzer",
                    dry_run=dry_run,
                )

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="rust-analyzer",
            dry_run=dry_run,
            warnings=[
                "Rename via CLI may miss some references",
                "Consider verifying with cargo check",
            ]
            if changes
            else [],
        )

    def _find_and_replace(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> list[RefactorChange]:
        """Find occurrences and perform replacement.

        This is a simplified approach that uses grep to find occurrences
        and optionally replaces them. Real rust-analyzer rename via LSP
        is more accurate.

        Args:
            request: The rename request.
            dry_run: If True, only preview changes.

        Returns:
            List of changes made or to be made.
        """
        changes: list[RefactorChange] = []

        # Find Rust files containing the target symbol
        try:
            grep_result = subprocess.run(
                [
                    "grep",
                    "-r",
                    "-l",
                    "--include=*.rs",
                    request.target,
                    str(self.project_root / "src"),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return changes

        if grep_result.returncode != 0:
            return changes

        files = grep_result.stdout.strip().split("\n")
        files = [f for f in files if f]  # Remove empty strings

        for file_path in files:
            try:
                path = Path(file_path)
                if not path.exists():
                    continue

                content = path.read_text(encoding="utf-8")
                if request.target not in content:
                    continue

                new_content = content.replace(request.target, request.new_value or "")

                if content != new_content:
                    changes.append(
                        RefactorChange(
                            file_path=str(path),
                            original_content=content,
                            new_content=new_content,
                            description=f"Renamed {request.target} to {request.new_value}",
                        )
                    )

                    if not dry_run:
                        path.write_text(new_content, encoding="utf-8")

            except OSError:
                continue

        return changes

    def _validate_changes(self) -> bool:
        """Validate changes with cargo check.

        Returns:
            True if code compiles successfully.
        """
        try:
            result = subprocess.run(
                ["cargo", "check"],
                cwd=self.project_root,
                capture_output=True,
                timeout=120,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _extract_method(
        self,
        _request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Extract method refactoring.

        This operation requires LSP client support.

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
            tool_used="rust-analyzer",
            dry_run=dry_run,
            warnings=["Consider using an IDE with rust-analyzer for this operation"],
        )

    def _inline(
        self,
        _request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Inline refactoring.

        This operation requires LSP client support.

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
            tool_used="rust-analyzer",
            dry_run=dry_run,
            warnings=["Consider using an IDE with rust-analyzer for this operation"],
        )

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

    def _get_ast_adapter(self) -> TreeSitterAdapter | None:
        """Get or create tree-sitter adapter for AST parsing.

        Returns:
            TreeSitterAdapter instance or None if unavailable.
        """
        if self._ast_adapter is not None:
            return self._ast_adapter

        try:
            self._ast_adapter = TreeSitterAdapter()
            return self._ast_adapter
        except (ImportError, RuntimeError):
            logger.warning("tree-sitter not available for AST parsing")
            return None

    def _parse_file(self, file_path: Path) -> ParseResult | None:
        """Parse a Rust file using tree-sitter.

        Args:
            file_path: Path to the Rust file.

        Returns:
            ParseResult or None if parsing failed.
        """
        ast_adapter = self._get_ast_adapter()
        if not ast_adapter:
            return None

        try:
            source = file_path.read_text(encoding="utf-8")
            result = ast_adapter.parse_file(str(file_path), source)
            return result if result.success else None
        except (OSError, ValueError) as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None

    def _extract_interface(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Extract trait from struct/impl using tree-sitter AST.

        In Rust, this extracts public methods from an impl block or struct
        and generates a trait definition.

        Args:
            request: Request containing target struct/type name.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with generated trait.
        """
        if not request.file_path:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["file_path is required for extract_interface"],
                tool_used="rust-analyzer+tree-sitter",
                dry_run=dry_run,
            )

        file_path = Path(request.file_path)
        if not file_path.exists():
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"File not found: {file_path}"],
                tool_used="rust-analyzer+tree-sitter",
                dry_run=dry_run,
            )

        parse_result = self._parse_file(file_path)
        if not parse_result:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["Failed to parse file - tree-sitter not available"],
                tool_used="rust-analyzer+tree-sitter",
                dry_run=dry_run,
            )

        # Find the target struct/impl
        target_type = request.target
        methods_to_extract = []

        for symbol in parse_result.symbols:
            # Find public methods in impl blocks for this type
            is_target_method = (
                symbol.parent_name == target_type
                and symbol.kind == SymbolKind.FUNCTION
                and symbol.visibility == Visibility.PUBLIC
            )
            if is_target_method:
                methods_to_extract.append(symbol)

        if not methods_to_extract:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"No public methods found for type '{target_type}'"],
                tool_used="rust-analyzer+tree-sitter",
                dry_run=dry_run,
            )

        # Generate trait name
        trait_name = request.interface_name or f"{target_type}Trait"

        # Generate trait definition
        trait_lines = [f"pub trait {trait_name} {{"]
        for method in methods_to_extract:
            # Build method signature for trait
            params = []
            has_self = False
            for p in method.parameters:
                if p.name == "self":
                    has_self = True
                    if p.type_annotation:
                        params.append(p.type_annotation)
                    else:
                        params.append("&self")
                else:
                    type_ann = p.type_annotation or "impl Any"
                    params.append(f"{p.name}: {type_ann}")

            if not has_self:
                params.insert(0, "&self")

            return_type = f" -> {method.return_type}" if method.return_type else ""
            trait_lines.append(f"    fn {method.name}({', '.join(params)}){return_type};")

        trait_lines.append("}")
        trait_content = "\n".join(trait_lines)

        # Read original content
        original_content = file_path.read_text(encoding="utf-8")

        # Find insertion point (after use statements, before first item)
        lines = original_content.split("\n")
        insert_line = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("use ") or line.strip().startswith("mod "):
                insert_line = i + 1

        # Insert trait definition
        new_lines = [*lines[:insert_line], "", trait_content, "", *lines[insert_line:]]
        new_content = "\n".join(new_lines)

        change = RefactorChange(
            file_path=str(file_path),
            original_content=original_content,
            new_content=new_content,
            description=f"Extracted trait {trait_name} from {target_type}",
            line_start=insert_line + 1,
            line_end=insert_line + len(trait_lines) + 2,
        )

        if not dry_run:
            file_path.write_text(new_content, encoding="utf-8")

        return RefactorResult(
            success=True,
            changes=[change],
            errors=[],
            tool_used="rust-analyzer+tree-sitter",
            dry_run=dry_run,
            warnings=[
                f"Generated trait with {len(methods_to_extract)} methods",
                "You may need to add `impl Trait for Type` block manually",
            ],
        )

    def _enforce_dependency(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Enforce dependency rules using tree-sitter AST.

        Analyzes use statements and checks against forbidden/allowed rules.

        Args:
            request: Request with dependency_rules specifying forbidden/allowed crates.
            dry_run: If True, only report violations.

        Returns:
            RefactorResult with violations found.
        """
        if not request.file_path:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["file_path is required for enforce_dependency"],
                tool_used="rust-analyzer+tree-sitter",
                dry_run=dry_run,
            )

        file_path = Path(request.file_path)
        if not file_path.exists():
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"File not found: {file_path}"],
                tool_used="rust-analyzer+tree-sitter",
                dry_run=dry_run,
            )

        parse_result = self._parse_file(file_path)
        if not parse_result:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["Failed to parse file - tree-sitter not available"],
                tool_used="rust-analyzer+tree-sitter",
                dry_run=dry_run,
            )

        # Parse dependency rules from request
        rules = request.dependency_rules or {}
        forbidden = rules.get("forbidden", [])
        allowed = rules.get("allowed", [])

        violations: list[str] = []
        changes: list[RefactorChange] = []

        for imp in parse_result.imports:
            # Extract crate name (first part of module path)
            module_parts = imp.module.replace("::", ".").split(".")
            crate_name = module_parts[0] if module_parts else imp.module

            # Skip std, self, super, crate
            if crate_name in ("std", "self", "super", "crate", "core", "alloc"):
                continue

            # Check forbidden
            if crate_name in forbidden:
                violations.append(
                    f"Line {imp.line}: Forbidden crate '{crate_name}' "
                    f"used in '{imp.module}'"
                )

            # Check allowed (if specified, only these are allowed)
            if allowed and crate_name not in allowed:
                violations.append(
                    f"Line {imp.line}: Crate '{crate_name}' is not in allowed list"
                )

        if violations:
            # Read original for change record
            original_content = file_path.read_text(encoding="utf-8")
            changes.append(
                RefactorChange(
                    file_path=str(file_path),
                    original_content=original_content,
                    new_content=original_content,  # No modification
                    description="Dependency violations found:\n" + "\n".join(violations),
                )
            )

            return RefactorResult(
                success=False,
                changes=changes,
                errors=violations,
                tool_used="rust-analyzer+tree-sitter",
                dry_run=dry_run,
            )

        return RefactorResult(
            success=True,
            changes=[],
            errors=[],
            tool_used="rust-analyzer+tree-sitter",
            dry_run=dry_run,
            warnings=[f"Checked {len(parse_result.imports)} use statements"],
        )
