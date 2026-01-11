"""Diff/Patch adapter for fallback refactoring.

This adapter provides basic text-based refactoring using search and replace.
It serves as a fallback when no language-specific tool is available.
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


class DiffPatchAdapter(RefactorToolPort):
    """Fallback adapter using basic text operations.

    This adapter provides simple search-and-replace refactoring
    when no language-specific tool is available. It's less accurate
    than AST-based tools but works for any text file.

    Attributes:
        project_root: Root directory of the project.
    """

    # Supports all languages as fallback
    LANGUAGES: ClassVar[list[str]] = ["*"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
        RefactorOperation.MOVE,
    ]

    def __init__(self, project_root: Path) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the project.
        """
        self.project_root = project_root

    def get_supported_languages(self) -> list[str]:
        """Return supported languages (all as fallback)."""
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return supported operations."""
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Always available as fallback.

        Returns:
            Always True.
        """
        return True

    def get_version(self) -> str | None:
        """Get version (returns internal version).

        Returns:
            Version string.
        """
        return "1.0.0"

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring via text replacement.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes and status.
        """
        if request.operation == RefactorOperation.RENAME:
            return self._rename(request, dry_run)
        elif request.operation == RefactorOperation.MOVE:
            return self._move(request, dry_run)

        return RefactorResult(
            success=False,
            changes=[],
            errors=[f"Operation {request.operation} not supported by fallback adapter"],
            tool_used="diff-patch",
            dry_run=dry_run,
        )

    def _rename(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Perform rename via text replacement.

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
                tool_used="diff-patch",
                dry_run=dry_run,
            )

        changes: list[RefactorChange] = []
        errors: list[str] = []

        # Determine files to search
        if request.file_path:
            files = [self.project_root / request.file_path]
        else:
            files = self._find_files_containing(request.target)

        for file_path in files:
            try:
                if not file_path.exists():
                    continue

                content = file_path.read_text(encoding="utf-8")
                if request.target not in content:
                    continue

                # Perform word-boundary-aware replacement
                new_content = self._replace_with_boundaries(
                    content, request.target, request.new_value
                )

                if content != new_content:
                    changes.append(
                        RefactorChange(
                            file_path=str(file_path.relative_to(self.project_root)),
                            original_content=content,
                            new_content=new_content,
                            description=f"Renamed '{request.target}' to '{request.new_value}'",
                        )
                    )

                    if not dry_run:
                        file_path.write_text(new_content, encoding="utf-8")

            except OSError as e:
                errors.append(f"Error processing {file_path}: {e}")

        warnings = []
        if changes:
            warnings.append(
                "Text-based replacement may not be as accurate as AST-based refactoring"
            )
            warnings.append("Consider verifying the changes manually")

        return RefactorResult(
            success=len(errors) == 0 or len(changes) > 0,
            changes=changes,
            errors=errors,
            tool_used="diff-patch",
            dry_run=dry_run,
            warnings=warnings,
        )

    def _replace_with_boundaries(
        self,
        content: str,
        old: str,
        new: str,
    ) -> str:
        """Replace text with word boundary awareness.

        This prevents replacing partial matches (e.g., "foo" in "foobar").

        Args:
            content: Original content.
            old: Text to find.
            new: Replacement text.

        Returns:
            Modified content.
        """
        import re

        # Escape special regex characters in the search term
        escaped = re.escape(old)

        # Use word boundaries for identifier-like patterns
        pattern = rf"\b{escaped}\b" if old.isidentifier() else escaped

        return re.sub(pattern, new, content)

    def _move(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Move/rename a file.

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
                tool_used="diff-patch",
                dry_run=dry_run,
            )

        source = self.project_root / request.target
        dest = self.project_root / request.new_value

        if not source.exists():
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Source file not found: {request.target}"],
                tool_used="diff-patch",
                dry_run=dry_run,
            )

        if dest.exists():
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Destination already exists: {request.new_value}"],
                tool_used="diff-patch",
                dry_run=dry_run,
            )

        changes = [
            RefactorChange(
                file_path=request.target,
                original_content=request.target,
                new_content=request.new_value,
                description=f"Moved '{request.target}' to '{request.new_value}'",
            )
        ]

        if not dry_run:
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                source.rename(dest)
            except OSError as e:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"Failed to move file: {e}"],
                    tool_used="diff-patch",
                    dry_run=dry_run,
                )

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="diff-patch",
            dry_run=dry_run,
            warnings=[
                "File move does not update imports/references",
                "Manual import updates may be required",
            ],
        )

    def _find_files_containing(self, text: str) -> list[Path]:
        """Find files containing the given text.

        Args:
            text: Text to search for.

        Returns:
            List of file paths containing the text.
        """
        files: list[Path] = []

        # Common source code extensions
        extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".kt",
            ".go",
            ".rs",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".rb",
            ".php",
            ".swift",
            ".scala",
            ".clj",
            ".ex",
            ".exs",
        }

        # Directories to exclude
        exclude_dirs = {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            "target",
            ".next",
            ".nuxt",
        }

        for path in self.project_root.rglob("*"):
            # Skip excluded directories
            if any(excluded in path.parts for excluded in exclude_dirs):
                continue

            # Only check files with known extensions
            if path.is_file() and path.suffix in extensions:
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    if text in content:
                        files.append(path)
                except OSError:
                    continue

        return files

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
