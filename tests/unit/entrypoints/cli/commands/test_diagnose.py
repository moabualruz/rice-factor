"""Unit tests for diagnose command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestDiagnoseCommandHelp:
    """Tests for diagnose command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["diagnose", "--help"])
        assert result.exit_code == 0
        assert "diagnose" in result.stdout.lower() or "analyze" in result.stdout.lower()

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["diagnose", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout


class TestDiagnoseRequiresInit:
    """Tests for diagnose phase requirements."""

    def test_diagnose_requires_init(self, tmp_path: Path) -> None:
        """diagnose should fail if project not initialized."""
        result = runner.invoke(app, ["diagnose", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestDiagnoseNoValidationResults:
    """Tests for diagnose when no validation results exist."""

    def test_diagnose_shows_no_results(self, tmp_path: Path) -> None:
        """diagnose should show message when no validation results."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.diagnose._check_phase"
        ):
            result = runner.invoke(app, ["diagnose", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "no validation" in result.stdout.lower() or "no result" in result.stdout.lower()


class TestDiagnoseWithValidationResults:
    """Tests for diagnose with validation results."""

    def test_diagnose_shows_summary(self, tmp_path: Path) -> None:
        """diagnose should show summary of validation results."""
        (tmp_path / ".project").mkdir()

        # First run tests to create a ValidationResult
        with patch(
            "rice_factor.entrypoints.cli.commands.test._check_phase"
        ):
            runner.invoke(app, ["test", "--path", str(tmp_path)])

        # Now run diagnose
        with patch(
            "rice_factor.entrypoints.cli.commands.diagnose._check_phase"
        ):
            result = runner.invoke(app, ["diagnose", "--path", str(tmp_path)])

        assert result.exit_code == 0
        # Should show some analysis
        assert "pass" in result.stdout.lower() or "result" in result.stdout.lower()

    def test_diagnose_shows_failure_analysis(self, tmp_path: Path) -> None:
        """diagnose should analyze failures when present."""
        (tmp_path / ".project").mkdir()

        # Create a ValidationResult artifact with failures directly
        from typing import TYPE_CHECKING, Any, cast

        if TYPE_CHECKING:
            from pydantic import BaseModel

        from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
        from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
        from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
        from rice_factor.domain.artifacts.payloads.validation_result import (
            ValidationResultPayload,
            ValidationStatus,
        )

        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        payload = ValidationResultPayload(
            target="test_suite",
            status=ValidationStatus.FAILED,
            errors=["Error 1", "Error 2"],
        )

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.VALIDATION_RESULT,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.SYSTEM,
            payload=payload,
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        # Now run diagnose
        with patch(
            "rice_factor.entrypoints.cli.commands.diagnose._check_phase"
        ):
            result = runner.invoke(app, ["diagnose", "--path", str(tmp_path)])

        assert result.exit_code == 0
        # Should show failure analysis - the diagnose command shows "failed"
        assert "fail" in result.stdout.lower() or "error" in result.stdout.lower()


class TestDiagnoseOutput:
    """Tests for diagnose output formatting."""

    def test_diagnose_shows_structured_output(self, tmp_path: Path) -> None:
        """diagnose should show well-structured output."""
        (tmp_path / ".project").mkdir()

        # Run tests first
        with patch(
            "rice_factor.entrypoints.cli.commands.test._check_phase"
        ):
            runner.invoke(app, ["test", "--path", str(tmp_path)])

        with patch(
            "rice_factor.entrypoints.cli.commands.diagnose._check_phase"
        ):
            result = runner.invoke(app, ["diagnose", "--path", str(tmp_path)])

        assert result.exit_code == 0
        # Output should be readable
        assert len(result.stdout) > 0
