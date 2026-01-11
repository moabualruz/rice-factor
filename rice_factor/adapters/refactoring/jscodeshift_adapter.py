"""jscodeshift adapter for JavaScript/TypeScript refactoring.

jscodeshift is a toolkit for running codemods over JavaScript/TypeScript.
This adapter uses jscodeshift to perform AST-based refactoring.
"""

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
