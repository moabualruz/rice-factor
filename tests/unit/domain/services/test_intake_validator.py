"""Unit tests for IntakeValidator service."""

from pathlib import Path

import pytest

from rice_factor.domain.services.intake_validator import (
    IntakeError,
    IntakeErrorType,
    IntakeValidationResult,
    IntakeValidator,
)


class TestIntakeValidatorInit:
    """Tests for IntakeValidator initialization."""

    def test_init_with_project_dir(self, tmp_path: Path) -> None:
        """IntakeValidator should accept project directory path."""
        validator = IntakeValidator(project_dir=tmp_path)
        assert validator.project_dir == tmp_path

    def test_init_without_project_dir_uses_cwd_project(self) -> None:
        """IntakeValidator should default to .project/ in current directory."""
        validator = IntakeValidator()
        assert validator.project_dir == Path.cwd() / ".project"


class TestFileExistenceCheck:
    """Tests for file existence validation."""

    def test_all_files_present_passes(self, tmp_path: Path) -> None:
        """Validation should pass when all 6 files exist with content."""
        # Create all required files with content
        for filename in IntakeValidator.REQUIRED_FILES:
            (tmp_path / filename).write_text(f"# {filename}\n\nReal content here.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_file_fails(self, tmp_path: Path) -> None:
        """Validation should fail when a required file is missing."""
        # Create all but one file
        for filename in IntakeValidator.REQUIRED_FILES[:-1]:
            (tmp_path / filename).write_text(f"# {filename}\n\nReal content here.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is False
        missing_errors = [
            e for e in result.errors if e.error_type == IntakeErrorType.FILE_MISSING
        ]
        assert len(missing_errors) == 1
        assert missing_errors[0].file == "decisions.md"

    def test_multiple_missing_files_reported(self, tmp_path: Path) -> None:
        """Validation should report all missing files."""
        # Don't create any files
        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is False
        missing_errors = [
            e for e in result.errors if e.error_type == IntakeErrorType.FILE_MISSING
        ]
        assert len(missing_errors) == 6


class TestEmptyFileCheck:
    """Tests for empty file validation."""

    def test_empty_blocking_file_fails(self, tmp_path: Path) -> None:
        """Validation should fail when a blocking file is empty."""
        # Create all files, but make requirements.md empty
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "requirements.md":
                (tmp_path / filename).write_text("")
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is False
        empty_errors = [
            e for e in result.errors if e.error_type == IntakeErrorType.FILE_EMPTY
        ]
        assert len(empty_errors) == 1
        assert empty_errors[0].file == "requirements.md"

    def test_empty_non_blocking_file_passes(self, tmp_path: Path) -> None:
        """Validation should pass when a non-blocking file is empty."""
        # Create all files with content, but make decisions.md empty
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "decisions.md":
                (tmp_path / filename).write_text("")
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        # decisions.md is not in BLOCKING_FILES, so empty is OK
        assert result.valid is True

    def test_whitespace_only_file_is_empty(self, tmp_path: Path) -> None:
        """Validation should treat whitespace-only files as empty."""
        # Create all files, but make requirements.md whitespace only
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "requirements.md":
                (tmp_path / filename).write_text("   \n\t\n   ")
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is False
        empty_errors = [
            e for e in result.errors if e.error_type == IntakeErrorType.FILE_EMPTY
        ]
        assert len(empty_errors) == 1


class TestVaguePatternCheck:
    """Tests for vague content validation."""

    def test_vague_pattern_in_blocking_file_fails(self, tmp_path: Path) -> None:
        """Validation should fail when blocking file contains vague patterns."""
        # Create all files, but requirements.md has vague content
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "requirements.md":
                (tmp_path / filename).write_text("# Requirements\n\n[Not provided]")
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is False
        vague_errors = [
            e for e in result.errors if e.error_type == IntakeErrorType.VAGUE_CONTENT
        ]
        assert len(vague_errors) == 1
        assert vague_errors[0].pattern == "[Not provided]"

    def test_vague_pattern_in_non_blocking_file_passes(self, tmp_path: Path) -> None:
        """Validation should pass when non-blocking file has vague patterns."""
        # Create all files with real content, but decisions.md has placeholder
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "decisions.md":
                (tmp_path / filename).write_text("# Decisions\n\n[Decision 1]")
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        # decisions.md is not in BLOCKING_FILES, so placeholders are OK
        assert result.valid is True

    def test_multiple_vague_patterns_report_first_only(self, tmp_path: Path) -> None:
        """Validation should report only first vague pattern per file."""
        # Create files with multiple vague patterns
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "requirements.md":
                (tmp_path / filename).write_text(
                    "# Requirements\n\n[Not provided]\n[TODO]\nTBD"
                )
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        vague_errors = [
            e for e in result.errors if e.error_type == IntakeErrorType.VAGUE_CONTENT
        ]
        # Only first pattern per file should be reported
        assert len(vague_errors) == 1


class TestMultipleErrors:
    """Tests for collecting multiple errors."""

    def test_multiple_error_types_collected(self, tmp_path: Path) -> None:
        """Validation should collect all error types."""
        # Missing decisions.md, empty glossary.md, vague requirements.md
        (tmp_path / "requirements.md").write_text("# Requirements\n\n[Not provided]")
        (tmp_path / "constraints.md").write_text("# Constraints\n\nReal content.")
        (tmp_path / "glossary.md").write_text("")  # Empty
        (tmp_path / "non_goals.md").write_text("# Non Goals\n\nReal content.")
        (tmp_path / "risks.md").write_text("# Risks\n\nReal content.")
        # decisions.md is missing

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is False

        # Should have all three error types
        error_types = {e.error_type for e in result.errors}
        assert IntakeErrorType.FILE_MISSING in error_types
        assert IntakeErrorType.FILE_EMPTY in error_types
        assert IntakeErrorType.VAGUE_CONTENT in error_types


class TestIntakeValidationResult:
    """Tests for IntakeValidationResult class."""

    def test_format_errors_when_valid(self) -> None:
        """format_errors should indicate success when valid."""
        result = IntakeValidationResult(valid=True, errors=[])
        formatted = result.format_errors()
        assert "All intake files are valid" in formatted

    def test_format_errors_groups_by_type(self) -> None:
        """format_errors should group errors by type."""
        result = IntakeValidationResult(
            valid=False,
            errors=[
                IntakeError(
                    error_type=IntakeErrorType.FILE_MISSING,
                    file="a.md",
                    message="Missing a.md",
                ),
                IntakeError(
                    error_type=IntakeErrorType.FILE_MISSING,
                    file="b.md",
                    message="Missing b.md",
                ),
                IntakeError(
                    error_type=IntakeErrorType.FILE_EMPTY,
                    file="c.md",
                    message="Empty c.md",
                ),
            ],
        )
        formatted = result.format_errors()

        assert "file_missing:" in formatted
        assert "file_empty:" in formatted
        assert "a.md" in formatted
        assert "b.md" in formatted
        assert "c.md" in formatted

    def test_format_errors_includes_remediation(self) -> None:
        """format_errors should include remediation hints."""
        result = IntakeValidationResult(
            valid=False,
            errors=[
                IntakeError(
                    error_type=IntakeErrorType.FILE_MISSING,
                    file="a.md",
                    message="Missing",
                ),
            ],
        )
        formatted = result.format_errors()

        assert "Remediation:" in formatted
        assert "rice-factor init" in formatted


class TestRequiredFilesConstant:
    """Tests for REQUIRED_FILES constant."""

    def test_contains_all_six_files(self) -> None:
        """REQUIRED_FILES should contain all 6 intake files."""
        expected = [
            "requirements.md",
            "constraints.md",
            "glossary.md",
            "non_goals.md",
            "risks.md",
            "decisions.md",
        ]
        assert IntakeValidator.REQUIRED_FILES == expected

    def test_blocking_files_is_subset_of_required(self) -> None:
        """BLOCKING_FILES should be a subset of REQUIRED_FILES."""
        for filename in IntakeValidator.BLOCKING_FILES:
            assert filename in IntakeValidator.REQUIRED_FILES


class TestLineNumberTracking:
    """Tests for line number tracking in vague pattern detection."""

    def test_vague_pattern_includes_line_number(self, tmp_path: Path) -> None:
        """Vague pattern error should include line number."""
        # Create file with vague pattern on line 3
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "requirements.md":
                (tmp_path / filename).write_text(
                    "# Requirements\n\nSome intro text\n\n[Not provided]\n"
                )
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        vague_errors = [
            e for e in result.errors if e.error_type == IntakeErrorType.VAGUE_CONTENT
        ]
        assert len(vague_errors) == 1
        assert vague_errors[0].line_number == 5  # [Not provided] is on line 5

    def test_format_errors_shows_line_number(self) -> None:
        """format_errors should include line number in output."""
        result = IntakeValidationResult(
            valid=False,
            errors=[
                IntakeError(
                    error_type=IntakeErrorType.VAGUE_CONTENT,
                    file="requirements.md",
                    message="Vague content detected: 'TBD'",
                    pattern="TBD",
                    line_number=15,
                ),
            ],
        )
        formatted = result.format_errors()

        assert "requirements.md:15:" in formatted


class TestVaguePatterns:
    """Tests for comprehensive vague pattern detection."""

    def test_tbd_detected(self, tmp_path: Path) -> None:
        """TBD pattern should be detected."""
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "requirements.md":
                (tmp_path / filename).write_text("# Requirements\n\nStatus: TBD")
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is False
        assert any(e.pattern == "TBD" for e in result.errors)

    def test_template_markers_detected(self, tmp_path: Path) -> None:
        """Template markers like [TODO] should be detected."""
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "requirements.md":
                (tmp_path / filename).write_text("# Requirements\n\n[TODO]")
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is False
        assert any(e.pattern == "[TODO]" for e in result.errors)

    def test_decisions_template_markers_detected(self, tmp_path: Path) -> None:
        """Decisions.md template markers should be detected in blocking files."""
        for filename in IntakeValidator.REQUIRED_FILES:
            if filename == "requirements.md":
                # Put decisions template marker in requirements.md (blocking file)
                (tmp_path / filename).write_text("# Requirements\n\n[Why this choice]")
            else:
                (tmp_path / filename).write_text(f"# {filename}\n\nReal content.")

        validator = IntakeValidator(project_dir=tmp_path)
        result = validator.validate()

        assert result.valid is False
        assert any(e.pattern == "[Why this choice]" for e in result.errors)
