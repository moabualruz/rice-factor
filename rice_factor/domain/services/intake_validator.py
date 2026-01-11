"""Intake file validation service.

This module provides the IntakeValidator class for validating that all required
intake files exist and have meaningful content before planning begins.

The validator enforces the "clarity before intelligence" principle - the LLM
cannot proceed without well-defined inputs.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import ClassVar


class IntakeErrorType(str, Enum):
    """Types of intake validation errors."""

    FILE_MISSING = "file_missing"
    FILE_EMPTY = "file_empty"
    VAGUE_CONTENT = "vague_content"
    UNDEFINED_TERM = "undefined_term"


@dataclass
class IntakeError:
    """A single intake validation error.

    Attributes:
        error_type: The type of error encountered.
        file: The filename that caused the error.
        message: Human-readable error description.
        pattern: Optional pattern that was detected (for vague content).
        line_number: Optional line number where error was found.
    """

    error_type: IntakeErrorType
    file: str
    message: str
    pattern: str | None = None
    line_number: int | None = None


@dataclass
class IntakeValidationResult:
    """Result of intake file validation.

    Attributes:
        valid: Whether all validation checks passed.
        errors: List of validation errors found.
    """

    valid: bool
    errors: list[IntakeError] = field(default_factory=list)

    def format_errors(self) -> str:
        """Format errors for CLI display.

        Returns:
            Formatted string with all errors grouped by type.
        """
        if self.valid:
            return "All intake files are valid."

        lines = ["Intake validation failed:", ""]

        # Group errors by type
        by_type: dict[IntakeErrorType, list[IntakeError]] = {}
        for error in self.errors:
            if error.error_type not in by_type:
                by_type[error.error_type] = []
            by_type[error.error_type].append(error)

        # Format each group
        for error_type, type_errors in by_type.items():
            lines.append(f"  {error_type.value}:")
            for error in type_errors:
                if error.line_number is not None:
                    lines.append(
                        f"    - {error.file}:{error.line_number}: {error.message}"
                    )
                else:
                    lines.append(f"    - {error.file}: {error.message}")

        lines.append("")
        lines.append("Remediation:")
        if IntakeErrorType.FILE_MISSING in by_type:
            lines.append("  - Run 'rice-factor init' to create missing files")
        if IntakeErrorType.FILE_EMPTY in by_type:
            lines.append("  - Add content to empty files before planning")
        if IntakeErrorType.VAGUE_CONTENT in by_type:
            lines.append("  - Replace placeholder text with actual requirements")

        return "\n".join(lines)


class IntakeValidator:
    """Validates intake files are complete and not vague.

    This validator enforces the "clarity before intelligence" principle.
    Planning commands will not proceed until intake validation passes.

    Attributes:
        REQUIRED_FILES: All 6 files that must exist in .project/
        BLOCKING_FILES: Files that must have meaningful content (not empty).
        VAGUE_PATTERNS: Patterns indicating unfilled template content.
    """

    REQUIRED_FILES: ClassVar[list[str]] = [
        "requirements.md",
        "constraints.md",
        "glossary.md",
        "non_goals.md",
        "risks.md",
        "decisions.md",
    ]

    BLOCKING_FILES: ClassVar[list[str]] = [
        "requirements.md",
        "constraints.md",
        "glossary.md",
    ]

    VAGUE_PATTERNS: ClassVar[list[str]] = [
        # Explicit deferral
        "TBD",
        "To be determined",
        "We'll decide later",
        "Not sure",
        "Maybe",
        "Possibly",
        # Template markers
        "[TODO]",
        "[Not provided]",
        "[Not specified]",
        # From decisions.md template
        "[Decision 1]",
        "[Alt A, Alt B]",
        "[Why this choice]",
        "[Approach 1]",
        "[Reason]",
        "[Tradeoff 1]",
        "[Benefit]",
        "[Cost]",
        # From requirements.md template
        "[Requirement description]",
        # From glossary.md template
        "[Term 1]",
        "[Definition]",
        # From risks.md template
        "[Risk description]",
        # From non_goals.md template
        "[Non-goal 1]",
    ]

    def __init__(self, project_dir: Path | None = None) -> None:
        """Initialize the validator.

        Args:
            project_dir: Path to .project/ directory. Defaults to .project/ in CWD.
        """
        if project_dir is None:
            self.project_dir = Path.cwd() / ".project"
        else:
            self.project_dir = project_dir

    def validate(self) -> IntakeValidationResult:
        """Validate all intake files.

        Performs three checks:
        1. File existence - all 6 files must exist
        2. Empty file check - blocking files must have content
        3. Vague pattern check - blocking files must not contain placeholders

        Returns:
            IntakeValidationResult with validation status and errors.
        """
        errors: list[IntakeError] = []

        # Check 1: File existence
        errors.extend(self._check_file_existence())

        # Check 2: Empty files (blocking files only)
        errors.extend(self._check_empty_files())

        # Check 3: Vague patterns (blocking files only)
        errors.extend(self._check_vague_patterns())

        return IntakeValidationResult(
            valid=len(errors) == 0,
            errors=errors,
        )

    def _check_file_existence(self) -> list[IntakeError]:
        """Check that all required files exist.

        Returns:
            List of FILE_MISSING errors for missing files.
        """
        errors: list[IntakeError] = []

        for filename in self.REQUIRED_FILES:
            file_path = self.project_dir / filename
            if not file_path.exists():
                errors.append(
                    IntakeError(
                        error_type=IntakeErrorType.FILE_MISSING,
                        file=filename,
                        message=f"Required file missing: {filename}",
                    )
                )

        return errors

    def _check_empty_files(self) -> list[IntakeError]:
        """Check that blocking files are not empty.

        Returns:
            List of FILE_EMPTY errors for empty blocking files.
        """
        errors: list[IntakeError] = []

        for filename in self.BLOCKING_FILES:
            file_path = self.project_dir / filename
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8").strip()
                if not content:
                    errors.append(
                        IntakeError(
                            error_type=IntakeErrorType.FILE_EMPTY,
                            file=filename,
                            message=f"Required file is empty: {filename}",
                        )
                    )

        return errors

    def _check_vague_patterns(self) -> list[IntakeError]:
        """Check that blocking files don't contain vague placeholder text.

        Returns:
            List of VAGUE_CONTENT errors for files with placeholders.
        """
        errors: list[IntakeError] = []

        for filename in self.BLOCKING_FILES:
            file_path = self.project_dir / filename
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                for pattern in self.VAGUE_PATTERNS:
                    if pattern in content:
                        # Find line number where pattern appears
                        line_number = self._find_pattern_line(lines, pattern)
                        errors.append(
                            IntakeError(
                                error_type=IntakeErrorType.VAGUE_CONTENT,
                                file=filename,
                                message=f"Vague content detected: '{pattern}'",
                                pattern=pattern,
                                line_number=line_number,
                            )
                        )
                        # Only report first vague pattern per file
                        break

        return errors

    def _find_pattern_line(self, lines: list[str], pattern: str) -> int | None:
        """Find the line number where a pattern first appears.

        Args:
            lines: List of file lines.
            pattern: Pattern to search for.

        Returns:
            1-indexed line number, or None if not found.
        """
        for i, line in enumerate(lines):
            if pattern in line:
                return i + 1  # 1-indexed
        return None
