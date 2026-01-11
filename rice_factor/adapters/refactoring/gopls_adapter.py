"""gopls adapter for Go refactoring.

gopls is the official Go language server that provides refactoring
capabilities through LSP. This adapter uses gorename for CLI-based
renames and gopls for other operations.
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


class GoplsAdapter(RefactorToolPort):
    """Adapter for gopls (Go Language Server).

    Uses gorename for rename operations and gopls for other refactoring.
    Requires Go tools to be installed.

    Attributes:
        project_root: Root directory of the Go project.
    """

    LANGUAGES: ClassVar[list[str]] = ["go"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
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
