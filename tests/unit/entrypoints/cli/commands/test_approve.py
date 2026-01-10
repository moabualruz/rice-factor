"""Unit tests for approve command."""

from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from pydantic import BaseModel
from typer.testing import CliRunner

from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.project_plan import (
    Architecture,
    Constraints,
    Domain,
    Module,
    ProjectPlanPayload,
)
from rice_factor.domain.artifacts.payloads.test_plan import (
    TestDefinition,
    TestPlanPayload,
)
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


def _create_project_plan_payload() -> ProjectPlanPayload:
    """Create a valid ProjectPlanPayload for testing."""
    return ProjectPlanPayload(
        domains=[Domain(name="core", responsibility="Core functionality")],
        modules=[Module(name="main", domain="core")],
        constraints=Constraints(architecture=Architecture.HEXAGONAL, languages=["python"]),
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


class TestApproveCommandHelp:
    """Tests for approve command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["approve", "--help"])
        assert result.exit_code == 0
        assert "approve" in result.stdout.lower()

    def test_help_shows_artifact_argument(self) -> None:
        """--help should show artifact argument."""
        result = runner.invoke(app, ["approve", "--help"])
        assert result.exit_code == 0
        assert "ARTIFACT" in result.stdout or "artifact" in result.stdout.lower()

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["approve", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout

    def test_help_shows_yes_option(self) -> None:
        """--help should show --yes option."""
        result = runner.invoke(app, ["approve", "--help"])
        assert result.exit_code == 0
        assert "--yes" in result.stdout


class TestApproveRequiresInit:
    """Tests for approve phase requirements."""

    def test_approve_requires_init(self, tmp_path: Path) -> None:
        """approve should fail if project not initialized."""
        result = runner.invoke(
            app, ["approve", "some-artifact", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestApproveWithArtifact:
    """Tests for approve with valid artifact."""

    def test_approve_by_uuid(self, tmp_path: Path) -> None:
        """approve should work with UUID."""
        (tmp_path / ".project").mkdir()

        # Create artifact
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=_create_project_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.approve._check_phase"
        ):
            result = runner.invoke(
                app,
                ["approve", str(artifact.id), "--path", str(tmp_path), "--yes"],
            )

        assert result.exit_code == 0
        assert "approved" in result.stdout.lower()

    def test_approve_by_path(self, tmp_path: Path) -> None:
        """approve should work with file path."""
        (tmp_path / ".project").mkdir()

        # Create artifact
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=_create_project_plan_payload(),
        )
        path = storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.approve._check_phase"
        ):
            result = runner.invoke(
                app,
                ["approve", str(path), "--path", str(tmp_path), "--yes"],
            )

        assert result.exit_code == 0
        assert "approved" in result.stdout.lower()

    def test_approve_requires_confirmation(self, tmp_path: Path) -> None:
        """approve should require confirmation without --yes."""
        (tmp_path / ".project").mkdir()

        # Create artifact
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=_create_project_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.approve._check_phase"
        ):
            # Decline confirmation
            result = runner.invoke(
                app,
                ["approve", str(artifact.id), "--path", str(tmp_path)],
                input="n\n",
            )

        assert result.exit_code == 0
        assert "cancelled" in result.stdout.lower()

    def test_approve_updates_status(self, tmp_path: Path) -> None:
        """approve should update artifact status."""
        (tmp_path / ".project").mkdir()

        # Create artifact
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=_create_project_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.approve._check_phase"
        ):
            runner.invoke(
                app,
                ["approve", str(artifact.id), "--path", str(tmp_path), "--yes"],
            )

        # Reload and check status
        updated = storage.load_by_id(artifact.id)
        assert updated.status == ArtifactStatus.APPROVED


class TestApproveAlreadyApproved:
    """Tests for approve with already approved artifact."""

    def test_approve_already_approved_warns(self, tmp_path: Path) -> None:
        """approve should warn if artifact already approved."""
        (tmp_path / ".project").mkdir()

        # Create approved artifact
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.APPROVED,
            created_by=CreatedBy.LLM,
            payload=_create_project_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.approve._check_phase"
        ):
            result = runner.invoke(
                app,
                ["approve", str(artifact.id), "--path", str(tmp_path)],
            )

        assert result.exit_code == 0
        assert "already approved" in result.stdout.lower()


class TestApproveLockedArtifact:
    """Tests for approve with locked artifact."""

    def test_approve_locked_fails(self, tmp_path: Path) -> None:
        """approve should fail if artifact is locked."""
        (tmp_path / ".project").mkdir()

        # Create locked artifact
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.TEST_PLAN,
            status=ArtifactStatus.LOCKED,
            created_by=CreatedBy.LLM,
            payload=_create_test_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.approve._check_phase"
        ):
            result = runner.invoke(
                app,
                ["approve", str(artifact.id), "--path", str(tmp_path)],
            )

        assert result.exit_code == 1
        assert "locked" in result.stdout.lower()


class TestApproveInvalidArtifact:
    """Tests for approve with invalid artifact."""

    def test_approve_invalid_uuid_fails(self, tmp_path: Path) -> None:
        """approve should fail with invalid UUID."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.approve._check_phase"
        ):
            result = runner.invoke(
                app,
                ["approve", "not-a-valid-uuid", "--path", str(tmp_path)],
            )

        assert result.exit_code == 1
        assert "could not resolve" in result.stdout.lower()


class TestApproveCreatesAuditEntry:
    """Tests for approve audit trail."""

    def test_approve_creates_audit_entry(self, tmp_path: Path) -> None:
        """Approving an artifact should create an audit entry."""
        (tmp_path / ".project").mkdir()

        # Create artifact
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=_create_project_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.approve._check_phase"
        ):
            runner.invoke(
                app,
                ["approve", str(artifact.id), "--path", str(tmp_path), "--yes"],
            )

        # Audit trail should exist
        trail_file = tmp_path / "audit" / "trail.json"
        assert trail_file.exists()
