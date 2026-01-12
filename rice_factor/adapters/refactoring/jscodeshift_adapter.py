"""jscodeshift adapter for JavaScript/TypeScript refactoring.

jscodeshift is a toolkit for running codemods over JavaScript/TypeScript.
This adapter uses jscodeshift to perform AST-based refactoring.

M14 Enhanced: Added extract_interface and enforce_dependency operations.
Now uses tree-sitter AST for method extraction.
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
class JsDependencyRule:
    """Rule for JavaScript/TypeScript dependency enforcement.

    Attributes:
        source_path: Path pattern that should not depend on target.
        target_path: Path pattern that should not be imported by source.
        description: Human-readable description of the rule.
    """

    source_path: str
    target_path: str
    description: str = ""


@dataclass
class JsDependencyViolation:
    """A dependency violation found during analysis.

    Attributes:
        file_path: Path to the file with the violation.
        line: Line number of the violation.
        import_statement: The import/require statement that violates the rule.
        source_module: Module doing the importing.
        target_module: Module being imported.
    """

    file_path: str
    line: int
    import_statement: str
    source_module: str
    target_module: str


class JscodeshiftAdapter(RefactorToolPort):
    """Adapter for jscodeshift (JavaScript/TypeScript).

    Uses jscodeshift transforms to perform AST-based refactoring.
    Requires Node.js and jscodeshift to be installed.

    Attributes:
        project_root: Root directory of the JS/TS project.
        transforms_dir: Directory containing transform scripts.
    """

    LANGUAGES: ClassVar[list[str]] = ["javascript", "typescript", "jsx", "tsx"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
        RefactorOperation.EXTRACT_METHOD,
        RefactorOperation.MOVE,
        RefactorOperation.EXTRACT_INTERFACE,
    ]

    def __init__(
        self,
        project_root: Path,
        transforms_dir: Path | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the JS/TS project.
            transforms_dir: Optional custom transforms directory.
        """
        self.project_root = project_root
        self.transforms_dir = transforms_dir or (
            Path(__file__).parent / "transforms"
        )
        self._version: str | None = None
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
        """Parse a JS/TS file using tree-sitter."""
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
        """Check if jscodeshift is installed.

        Returns:
            True if jscodeshift is available via npx.
        """
        try:
            result = subprocess.run(
                ["npx", "jscodeshift", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_version(self) -> str | None:
        """Get jscodeshift version.

        Returns:
            Version string or None.
        """
        if self._version:
            return self._version

        try:
            result = subprocess.run(
                ["npx", "jscodeshift", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                # Output is usually just the version number
                self._version = result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return self._version

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring via jscodeshift.

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
                errors=["jscodeshift is not installed (try: npm install -g jscodeshift)"],
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        if request.operation == RefactorOperation.RENAME:
            return self._rename(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_METHOD:
            return self._extract_method(request, dry_run)
        elif request.operation == RefactorOperation.MOVE:
            return self._move(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_INTERFACE:
            return self._execute_extract_interface(request, dry_run)

        return RefactorResult(
            success=False,
            changes=[],
            errors=[f"Operation {request.operation} not supported"],
            tool_used="jscodeshift",
            dry_run=dry_run,
        )

    def _rename(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Perform rename refactoring.

        Uses a custom transform or the built-in rename functionality.

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
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        # Use inline transform for rename
        transform_code = self._get_rename_transform(request.target, request.new_value)

        # Get target files
        target_files = self._get_target_files(request)
        if not target_files:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["No matching files found"],
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        # Build command
        cmd = [
            "npx",
            "jscodeshift",
            "--parser",
            self._detect_parser(target_files),
            "-t",
            "-",  # Read transform from stdin
        ]

        if dry_run:
            cmd.append("--dry")
            cmd.append("--print")

        cmd.extend(target_files)

        try:
            result = subprocess.run(
                cmd,
                input=transform_code,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["jscodeshift command timed out"],
                tool_used="jscodeshift",
                dry_run=dry_run,
            )
        except FileNotFoundError as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Command not found: {e}"],
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        # jscodeshift returns 0 even if some files fail
        changes = self._parse_output(result.stdout, result.stderr, request)

        # Check for actual errors
        errors: list[str] = []
        if "ERR" in result.stderr:
            errors.append(result.stderr)

        return RefactorResult(
            success=len(errors) == 0,
            changes=changes,
            errors=errors,
            tool_used="jscodeshift",
            dry_run=dry_run,
        )

    def _get_rename_transform(self, old_name: str, new_name: str) -> str:
        """Generate inline transform for renaming.

        Args:
            old_name: Current symbol name.
            new_name: New symbol name.

        Returns:
            JavaScript transform code.
        """
        # Simple rename transform that handles identifiers
        return f"""
module.exports = function(fileInfo, api) {{
    const j = api.jscodeshift;
    const root = j(fileInfo.source);

    // Rename identifiers
    root.find(j.Identifier, {{ name: '{old_name}' }})
        .forEach(path => {{
            path.node.name = '{new_name}';
        }});

    // Rename JSX identifiers
    root.find(j.JSXIdentifier, {{ name: '{old_name}' }})
        .forEach(path => {{
            path.node.name = '{new_name}';
        }});

    return root.toSource();
}};
"""

    def _extract_method(
        self,
        _request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Extract method refactoring.

        This is a complex operation that requires selection context,
        typically better handled by IDE integration.

        Args:
            _request: The extract method request (unused, not supported).
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult indicating limited support.
        """
        return RefactorResult(
            success=False,
            changes=[],
            errors=[
                "Extract method requires selection context",
                "Consider using VS Code with the TypeScript language service",
            ],
            tool_used="jscodeshift",
            dry_run=dry_run,
        )

    def _move(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Move/rename file or module.

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
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        # For move, we need to:
        # 1. Update imports in all files referencing the moved file
        # 2. Move the actual file

        old_path = Path(request.target)
        new_path = Path(request.new_value)

        if not (self.project_root / old_path).exists():
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Source file not found: {old_path}"],
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        # Generate transform to update imports
        transform_code = self._get_move_transform(str(old_path), str(new_path))

        # Find all JS/TS files
        target_files = self._get_all_js_files()

        cmd = [
            "npx",
            "jscodeshift",
            "--parser",
            "tsx",  # tsx parser handles all variants
            "-t",
            "-",
        ]

        if dry_run:
            cmd.append("--dry")
            cmd.append("--print")

        cmd.extend(target_files)

        try:
            result = subprocess.run(
                cmd,
                input=transform_code,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[str(e)],
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        changes = self._parse_output(result.stdout, result.stderr, request)

        # Add file move to changes
        if not dry_run:
            # Actually move the file
            source = self.project_root / old_path
            dest = self.project_root / new_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            source.rename(dest)

        changes.append(
            RefactorChange(
                file_path=str(old_path),
                original_content=str(old_path),
                new_content=str(new_path),
                description=f"Moved file from {old_path} to {new_path}",
            )
        )

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="jscodeshift",
            dry_run=dry_run,
        )

    def _get_move_transform(self, old_path: str, new_path: str) -> str:
        """Generate transform for updating imports after a move.

        Args:
            old_path: Original file path.
            new_path: New file path.

        Returns:
            JavaScript transform code.
        """
        # Remove extensions for import matching
        old_import = old_path.replace(".ts", "").replace(".tsx", "").replace(".js", "").replace(".jsx", "")
        new_import = new_path.replace(".ts", "").replace(".tsx", "").replace(".js", "").replace(".jsx", "")

        return f"""
module.exports = function(fileInfo, api) {{
    const j = api.jscodeshift;
    const root = j(fileInfo.source);

    // Update import declarations
    root.find(j.ImportDeclaration)
        .filter(path => {{
            const source = path.node.source.value;
            return source.includes('{old_import}') ||
                   source.endsWith('/{old_import.split("/")[-1]}');
        }})
        .forEach(path => {{
            path.node.source.value = path.node.source.value
                .replace('{old_import}', '{new_import}');
        }});

    // Update require calls
    root.find(j.CallExpression, {{ callee: {{ name: 'require' }} }})
        .filter(path => {{
            const arg = path.node.arguments[0];
            return arg && arg.value && arg.value.includes('{old_import}');
        }})
        .forEach(path => {{
            path.node.arguments[0].value = path.node.arguments[0].value
                .replace('{old_import}', '{new_import}');
        }});

    return root.toSource();
}};
"""

    def _get_target_files(self, request: RefactorRequest) -> list[str]:
        """Get target files for the refactoring operation.

        Args:
            request: The refactoring request.

        Returns:
            List of file paths.
        """
        if request.file_path:
            return [request.file_path]

        return self._get_all_js_files()

    def _get_all_js_files(self) -> list[str]:
        """Get all JavaScript/TypeScript files in the project.

        Returns:
            List of file paths.
        """
        files: list[Path] = []
        extensions = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
        exclude_dirs = {"node_modules", "dist", ".next"}

        for ext in extensions:
            files.extend(self.project_root.rglob(f"*{ext}"))

        # Exclude node_modules, dist, and .next directories
        # Use Path.parts for accurate directory matching
        filtered = [
            str(f)
            for f in files
            if not any(part in exclude_dirs for part in f.parts)
        ]

        return filtered

    def _detect_parser(self, files: list[str]) -> str:
        """Detect the appropriate parser based on file extensions.

        Args:
            files: List of file paths.

        Returns:
            Parser name ("tsx", "ts", "babel", etc.).
        """
        has_tsx = any(f.endswith(".tsx") for f in files)
        has_ts = any(f.endswith(".ts") for f in files)

        if has_tsx:
            return "tsx"
        elif has_ts:
            return "ts"
        else:
            return "babel"

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        request: RefactorRequest,
    ) -> list[RefactorChange]:
        """Parse jscodeshift output to extract changes.

        Args:
            stdout: Command stdout.
            stderr: Command stderr.
            request: Original request.

        Returns:
            List of RefactorChange objects.
        """
        changes: list[RefactorChange] = []

        # jscodeshift output format varies
        # Look for "Modified" or file paths in output
        for line in (stdout + stderr).split("\n"):
            line = line.strip()

            # Look for modification indicators
            if "modified" in line.lower() or "changed" in line.lower():
                # Extract file path
                parts = line.split()
                for part in parts:
                    if any(
                        part.endswith(ext)
                        for ext in [".js", ".jsx", ".ts", ".tsx"]
                    ):
                        changes.append(
                            RefactorChange(
                                file_path=part,
                                original_content="",
                                new_content="",
                                description=f"Modified by {request.operation.value}",
                            )
                        )
                        break

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

    # ========================================================================
    # M14 Enhanced Methods: extract_interface and enforce_dependency
    # ========================================================================

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
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        file_path = self.project_root / request.file_path
        if not file_path.exists():
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"File not found: {file_path}"],
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        return self.extract_interface(
            file_path=file_path,
            class_name=request.target,
            interface_name=request.new_value or f"I{request.target}",
        )

    def extract_interface(
        self,
        file_path: Path,
        class_name: str,
        interface_name: str,
        methods: Sequence[str] | None = None,
    ) -> RefactorResult:
        """Extract a TypeScript interface or JSDoc typedef from a class.

        For TypeScript files, generates a proper interface.
        For JavaScript files, generates a JSDoc @typedef.

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
                    tool_used="jscodeshift",
                    dry_run=True,
                )

            content = file_path.read_text(encoding="utf-8")
            is_typescript = file_path.suffix in [".ts", ".tsx"]

            method_sigs = self._extract_js_methods(content, class_name, methods, is_typescript)

            if not method_sigs:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"No public methods found in class '{class_name}'"],
                    tool_used="jscodeshift",
                    dry_run=True,
                )

            if is_typescript:
                interface_code = self._generate_ts_interface(interface_name, method_sigs)
            else:
                interface_code = self._generate_jsdoc_typedef(interface_name, method_sigs)

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
                tool_used="jscodeshift",
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
                tool_used="jscodeshift",
                dry_run=True,
            )

    def _extract_js_methods(
        self,
        content: str,
        class_name: str,
        filter_methods: Sequence[str] | None,
        is_typescript: bool,
        file_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Extract method signatures from a JavaScript/TypeScript class using tree-sitter AST.

        Args:
            content: Source code.
            class_name: Name of the class to extract from.
            filter_methods: Optional list of method names to include.
            is_typescript: Whether the file is TypeScript.
            file_path: Optional file path for AST parsing.

        Returns:
            List of method signature dictionaries.
        """
        signatures: list[dict[str, Any]] = []

        # Determine file extension for parsing
        ext = ".ts" if is_typescript else ".js"
        parse_result = self._parse_file(file_path or Path(f"temp{ext}"), content)

        if parse_result:
            for symbol in parse_result.symbols:
                # Find methods in the target class
                if symbol.parent_name != class_name:
                    continue
                if symbol.kind != SymbolKind.METHOD:
                    continue

                # Skip private/protected for TypeScript
                if is_typescript and symbol.visibility in (Visibility.PRIVATE, Visibility.PROTECTED):
                    continue

                # Skip constructor and private methods (starting with _)
                if symbol.name in ["constructor", "render"] or symbol.name.startswith("_"):
                    continue

                # Filter if specified
                if filter_methods and symbol.name not in filter_methods:
                    continue

                # Build params string
                params_parts = []
                for p in symbol.parameters:
                    if p.type_annotation and is_typescript:
                        params_parts.append(f"{p.name}: {p.type_annotation}")
                    else:
                        params_parts.append(p.name)

                signatures.append({
                    "name": symbol.name,
                    "params": ", ".join(params_parts),
                    "return_type": symbol.return_type,
                    "is_async": "async" in (symbol.modifiers or []),
                })

            return signatures

        # Fallback to regex if tree-sitter fails
        logger.warning("Tree-sitter not available, falling back to regex")
        return self._extract_js_methods_regex(content, class_name, filter_methods, is_typescript)

    def _extract_js_methods_regex(
        self,
        content: str,
        class_name: str,
        filter_methods: Sequence[str] | None,
        is_typescript: bool,
    ) -> list[dict[str, Any]]:
        """Fallback regex-based method extraction for JS/TS."""
        signatures: list[dict[str, Any]] = []

        # Find the class
        class_pattern = rf"class\s+{re.escape(class_name)}(?:\s+extends\s+[\w.<>]+)?(?:\s+implements\s+[\w,\s.<>]+)?\s*{{"
        class_match = re.search(class_pattern, content)
        if not class_match:
            return signatures

        class_start = class_match.end()

        if is_typescript:
            method_pattern = (
                r"(public|private|protected)?\s*(?:async\s+)?"
                r"(\w+)\s*"
                r"\(([^)]*)\)"
                r"(?:\s*:\s*([\w<>\[\]|&\s]+))?"
            )
        else:
            method_pattern = (
                r"(?:async\s+)?"
                r"(\w+)\s*"
                r"\(([^)]*)\)"
            )

        for match in re.finditer(method_pattern, content[class_start:]):
            if is_typescript:
                visibility = match.group(1)
                method_name = match.group(2)
                params = match.group(3).strip()
                return_type = None
                if match.lastindex is not None and match.lastindex >= 4:
                    group4 = match.group(4)
                    if group4:
                        return_type = group4.strip()

                if visibility in ["private", "protected"]:
                    continue
            else:
                method_name = match.group(1)
                params = match.group(2).strip()
                return_type = None

            if method_name in ["constructor", "render"] or method_name.startswith("_"):
                continue

            if filter_methods and method_name not in filter_methods:
                continue

            signatures.append({
                "name": method_name,
                "params": params,
                "return_type": return_type,
                "is_async": "async" in content[class_start + match.start() - 10:class_start + match.start()],
            })

        return signatures

    def _generate_ts_interface(
        self,
        interface_name: str,
        method_sigs: list[dict[str, Any]],
    ) -> str:
        """Generate a TypeScript interface definition.

        Args:
            interface_name: Name for the interface.
            method_sigs: List of method signature dictionaries.

        Returns:
            TypeScript code for the interface.
        """
        lines = [f"export interface {interface_name} {{"]

        for sig in method_sigs:
            params = sig["params"]
            return_type = sig.get("return_type") or "void"
            is_async = sig.get("is_async", False)

            # Wrap async methods in Promise if not already
            if is_async and not return_type.startswith("Promise"):
                return_type = f"Promise<{return_type}>"

            lines.append(f"  {sig['name']}({params}): {return_type};")

        lines.append("}")

        return "\n".join(lines)

    def _generate_jsdoc_typedef(
        self,
        interface_name: str,
        method_sigs: list[dict[str, Any]],
    ) -> str:
        """Generate a JSDoc @typedef for JavaScript files.

        Args:
            interface_name: Name for the typedef.
            method_sigs: List of method signature dictionaries.

        Returns:
            JSDoc typedef comment.
        """
        lines = ["/**", f" * @typedef {{{interface_name}}}"]

        for sig in method_sigs:
            # Convert params to JSDoc format
            param_types = self._parse_js_params_to_jsdoc(sig["params"])
            lines.append(f" * @property {{function({param_types}): *}} {sig['name']}")

        lines.append(" */")

        return "\n".join(lines)

    def _parse_js_params_to_jsdoc(self, params: str) -> str:
        """Convert JavaScript parameters to JSDoc type format.

        Args:
            params: Parameter string from method signature.

        Returns:
            JSDoc type string.
        """
        if not params:
            return ""

        # Split params and extract names
        param_parts = [p.strip().split(":")[0].split("=")[0].strip() for p in params.split(",")]
        return ", ".join(["*"] * len(param_parts))

    def enforce_dependency(
        self,
        rule: JsDependencyRule,
        fix: bool = False,
    ) -> RefactorResult:
        """Check and report dependency violations in JS/TS code.

        Analyzes import/require statements to find violations of dependency rules.

        Args:
            rule: The dependency rule to enforce.
            fix: If True, attempt to remove violating imports.

        Returns:
            RefactorResult with violations found.
        """
        try:
            violations = self._find_js_dependency_violations(rule)

            if not violations:
                return RefactorResult(
                    success=True,
                    changes=[],
                    errors=[],
                    tool_used="jscodeshift",
                    dry_run=not fix,
                )

            changes: list[RefactorChange] = []
            errors: list[str] = []

            for violation in violations:
                if fix:
                    result = self._remove_js_import(violation)
                    if result.success:
                        changes.extend(result.changes)
                    else:
                        errors.extend(result.errors)
                else:
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
                tool_used="jscodeshift",
                dry_run=not fix,
                warnings=[f"Found {len(violations)} dependency violation(s)"],
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Enforce dependency failed: {e}"],
                tool_used="jscodeshift",
                dry_run=not fix,
            )

    def _find_js_dependency_violations(
        self,
        rule: JsDependencyRule,
    ) -> list[JsDependencyViolation]:
        """Find all violations of a dependency rule in JS/TS source files.

        Args:
            rule: The dependency rule to check.

        Returns:
            List of dependency violations.
        """
        violations: list[JsDependencyViolation] = []

        # Get all JS/TS files
        js_files = self._get_all_js_files()

        for file_path_str in js_files:
            file_path = Path(file_path_str)
            try:
                # Check if file is in source path
                # Normalize to forward slashes for cross-platform compatibility
                rel_path = str(file_path.relative_to(self.project_root)).replace("\\", "/")
                source_pattern = rule.source_path.replace("\\", "/")
                if source_pattern not in rel_path:
                    continue

                content = file_path.read_text(encoding="utf-8")

                file_violations = self._check_js_file_violations(
                    file_path, content, rule
                )
                violations.extend(file_violations)

            except (OSError, ValueError):
                continue

        return violations

    def _check_js_file_violations(
        self,
        file_path: Path,
        content: str,
        rule: JsDependencyRule,
    ) -> list[JsDependencyViolation]:
        """Check a single JS/TS file for dependency violations.

        Args:
            file_path: Path to the source file.
            content: File content.
            rule: The dependency rule to check.

        Returns:
            List of violations in this file.
        """
        violations: list[JsDependencyViolation] = []
        lines = content.split("\n")

        source_module = file_path.stem
        # Normalize target path for cross-platform matching
        target_pattern = rule.target_path.replace("\\", "/")
        # Normalize file path for output
        rel_file_path = str(file_path.relative_to(self.project_root)).replace("\\", "/")

        for i, line in enumerate(lines, 1):
            # Check for ES module imports
            # import { Foo } from './forbidden/module';
            import_match = re.match(r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]", line)
            if import_match:
                imported_path = import_match.group(1)
                if target_pattern in imported_path:
                    violations.append(
                        JsDependencyViolation(
                            file_path=rel_file_path,
                            line=i,
                            import_statement=line.strip(),
                            source_module=source_module,
                            target_module=imported_path,
                        )
                    )

            # Check for CommonJS require
            # const foo = require('./forbidden/module');
            require_match = re.match(r"(?:const|let|var)\s+\w+\s*=\s*require\s*\(['\"]([^'\"]+)['\"]\)", line)
            if require_match:
                required_path = require_match.group(1)
                if target_pattern in required_path:
                    violations.append(
                        JsDependencyViolation(
                            file_path=rel_file_path,
                            line=i,
                            import_statement=line.strip(),
                            source_module=source_module,
                            target_module=required_path,
                        )
                    )

            # Check for dynamic imports
            # const foo = await import('./forbidden/module');
            dynamic_import_match = re.search(r"import\s*\(['\"]([^'\"]+)['\"]\)", line)
            if dynamic_import_match:
                imported_path = dynamic_import_match.group(1)
                if target_pattern in imported_path:
                    violations.append(
                        JsDependencyViolation(
                            file_path=rel_file_path,
                            line=i,
                            import_statement=line.strip(),
                            source_module=source_module,
                            target_module=imported_path,
                        )
                    )

        return violations

    def _remove_js_import(
        self, violation: JsDependencyViolation
    ) -> RefactorResult:
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
                    tool_used="jscodeshift",
                    dry_run=False,
                )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Failed to remove import: {e}"],
                tool_used="jscodeshift",
                dry_run=False,
            )

        return RefactorResult(
            success=False,
            changes=[],
            errors=["Could not find line to remove"],
            tool_used="jscodeshift",
            dry_run=False,
        )
