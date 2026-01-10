"""Unit tests for refactor commands."""

from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel
from typer.testing import CliRunner

from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.refactor_plan import (
    RefactorOperation,
    RefactorOperationType,
    RefactorPlanPayload,
)
from rice_factor.domain.artifacts.payloads.test_plan import (
    TestDefinition,
    TestPlanPayload,
)
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


def _create_refactor_plan_payload() -> RefactorPlanPayload:
    """Create a valid RefactorPlanPayload for testing."""
    return RefactorPlanPayload(
        goal="Test refactoring",
        operations=[
            RefactorOperation(
                type=RefactorOperationType.MOVE_FILE,
                from_path="src/old.py",
                to_path="src/new.py",
            ),
        ],
    )


def _create_test_plan_payload() -> TestPlanPayload:
    """Create a valid TestPlanPayload for testing."""
    return TestPlanPayload(
        tests=[
            TestDefinition(
                id="test_1",
                target="main_function",
                assertions=["result == expected"],
            )
        ],
    )


def _setup_test_locked_project(tmp_path: Path) -> None:
    """Set up a project in TEST_LOCKED phase with a locked TestPlan."""
    (tmp_path / ".project").mkdir()

    # Create a locked TestPlan to reach TEST_LOCKED phase
    artifacts_dir = tmp_path / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

    artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
        artifact_type=ArtifactType.TEST_PLAN,
        status=ArtifactStatus.LOCKED,
        created_by=CreatedBy.LLM,
        payload=_create_test_plan_payload(),
    )
    storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))


def _create_refactor_plan_artifact(
    tmp_path: Path, status: ArtifactStatus = ArtifactStatus.DRAFT
) -> ArtifactEnvelope[Any]:
    """Create and save a RefactorPlan artifact."""
    artifacts_dir = tmp_path / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

    artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
        artifact_type=ArtifactType.REFACTOR_PLAN,
        status=status,
        created_by=CreatedBy.LLM,
        payload=_create_refactor_plan_payload(),
    )
    storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))
    return artifact


class TestRefactorHelpCommand:
    """Tests for refactor --help."""

    def test_refactor_help_shows_subcommands(self) -> None:
        """refactor --help should show available subcommands."""
        result = runner.invoke(app, ["refactor", "--help"])
        assert result.exit_code == 0
        assert "check" in result.stdout
        assert "dry-run" in result.stdout
        assert "apply" in result.stdout


class TestRefactorCheckCommand:
    """Tests for refactor check command."""

    def test_check_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["refactor", "check", "--help"])
        assert result.exit_code == 0
        assert "check" in result.stdout.lower() or "capability" in result.stdout.lower()

    def test_check_requires_init(self, tmp_path: Path) -> None:
        """refactor check should fail if project not initialized."""
        result = runner.invoke(
            app, ["refactor", "check", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    def test_check_requires_refactor_plan(self, tmp_path: Path) -> None:
        """refactor check should fail if no RefactorPlan exists."""
        _setup_test_locked_project(tmp_path)

        result = runner.invoke(
            app, ["refactor", "check", "--path", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "no refactorplan" in result.stdout.lower()

    def test_check_shows_supported_operations(self, tmp_path: Path) -> None:
        """refactor check should show supported operations."""
        _setup_test_locked_project(tmp_path)
        _create_refactor_plan_artifact(tmp_path)

        result = runner.invoke(
            app, ["refactor", "check", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "supported" in result.stdout.lower()


class TestRefactorDryRunCommand:
    """Tests for refactor dry-run command."""

    def test_dry_run_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["refactor", "dry-run", "--help"])
        assert result.exit_code == 0
        assert "preview" in result.stdout.lower() or "dry" in result.stdout.lower()

    def test_dry_run_requires_init(self, tmp_path: Path) -> None:
        """refactor dry-run should fail if project not initialized."""
        result = runner.invoke(
            app, ["refactor", "dry-run", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    def test_dry_run_requires_refactor_plan(self, tmp_path: Path) -> None:
        """refactor dry-run should fail if no RefactorPlan exists."""
        _setup_test_locked_project(tmp_path)

        result = runner.invoke(
            app, ["refactor", "dry-run", "--path", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "no refactorplan" in result.stdout.lower()

    def test_dry_run_shows_preview(self, tmp_path: Path) -> None:
        """refactor dry-run should show preview of changes."""
        _setup_test_locked_project(tmp_path)
        _create_refactor_plan_artifact(tmp_path)

        result = runner.invoke(
            app, ["refactor", "dry-run", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "preview" in result.stdout.lower()


class TestRefactorApplyCommand:
    """Tests for refactor apply command."""

    def test_apply_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["refactor", "apply", "--help"])
        assert result.exit_code == 0
        assert "apply" in result.stdout.lower()

    def test_apply_help_shows_dry_run_option(self) -> None:
        """--help should show --dry-run option."""
        result = runner.invoke(app, ["refactor", "apply", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.stdout

    def test_apply_requires_init(self, tmp_path: Path) -> None:
        """refactor apply should fail if project not initialized."""
        result = runner.invoke(
            app, ["refactor", "apply", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    def test_apply_requires_refactor_plan(self, tmp_path: Path) -> None:
        """refactor apply should fail if no RefactorPlan exists."""
        _setup_test_locked_project(tmp_path)

        result = runner.invoke(
            app, ["refactor", "apply", "--path", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "no refactorplan" in result.stdout.lower()

    def test_apply_requires_approved_plan(self, tmp_path: Path) -> None:
        """refactor apply should fail if RefactorPlan is not approved."""
        _setup_test_locked_project(tmp_path)
        _create_refactor_plan_artifact(tmp_path, status=ArtifactStatus.DRAFT)

        result = runner.invoke(
            app, ["refactor", "apply", "--path", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "approved" in result.stdout.lower()

    def test_apply_requires_confirmation(self, tmp_path: Path) -> None:
        """refactor apply should require confirmation."""
        _setup_test_locked_project(tmp_path)
        _create_refactor_plan_artifact(tmp_path, status=ArtifactStatus.APPROVED)

        result = runner.invoke(
            app,
            ["refactor", "apply", "--path", str(tmp_path)],
            input="n\n",
        )

        assert result.exit_code == 0
        assert "cancelled" in result.stdout.lower()

    def test_apply_dry_run_does_not_execute(self, tmp_path: Path) -> None:
        """refactor apply --dry-run should not execute changes."""
        _setup_test_locked_project(tmp_path)
        _create_refactor_plan_artifact(tmp_path, status=ArtifactStatus.APPROVED)

        result = runner.invoke(
            app,
            ["refactor", "apply", "--path", str(tmp_path), "--dry-run"],
        )

        assert result.exit_code == 0
        assert "dry run" in result.stdout.lower()

    def test_apply_with_yes_skips_confirmation(self, tmp_path: Path) -> None:
        """refactor apply --yes should skip confirmation."""
        _setup_test_locked_project(tmp_path)
        _create_refactor_plan_artifact(tmp_path, status=ArtifactStatus.APPROVED)

        result = runner.invoke(
            app,
            ["refactor", "apply", "--path", str(tmp_path), "--yes"],
        )

        assert result.exit_code == 0
        assert "successfully" in result.stdout.lower()


class TestRefactorPhaseGating:
    """Tests for refactor phase gating."""

    def test_check_requires_test_locked_phase(self, tmp_path: Path) -> None:
        """refactor check should require TEST_LOCKED phase."""
        # Just create .project but no locked TestPlan
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["refactor", "check", "--path", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "test_locked" in result.stdout.lower()

    def test_dry_run_requires_test_locked_phase(self, tmp_path: Path) -> None:
        """refactor dry-run should require TEST_LOCKED phase."""
        # Just create .project but no locked TestPlan
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["refactor", "dry-run", "--path", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "test_locked" in result.stdout.lower()

    def test_apply_requires_test_locked_phase(self, tmp_path: Path) -> None:
        """refactor apply should require TEST_LOCKED phase."""
        # Just create .project but no locked TestPlan
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["refactor", "apply", "--path", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "test_locked" in result.stdout.lower()
