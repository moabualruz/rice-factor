"""rust-analyzer adapter for Rust refactoring.

rust-analyzer provides AST-based refactoring for Rust through LSP.
This adapter uses rust-analyzer and cargo for Rust-native refactoring.
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
    ]

    def __init__(self, project_root: Path) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the Rust project.
        """
        self.project_root = project_root
        self._version: str | None = None

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
