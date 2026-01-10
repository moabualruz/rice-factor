"""Unit tests for lock command."""

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


class TestLockCommandHelp:
    """Tests for lock command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["lock", "--help"])
        assert result.exit_code == 0
        assert "lock" in result.stdout.lower()

    def test_help_shows_artifact_argument(self) -> None:
        """--help should show artifact argument."""
        result = runner.invoke(app, ["lock", "--help"])
        assert result.exit_code == 0
        assert "ARTIFACT" in result.stdout or "artifact" in result.stdout.lower()

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["lock", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout


class TestLockRequiresInit:
    """Tests for lock phase requirements."""

    def test_lock_requires_init(self, tmp_path: Path) -> None:
        """lock should fail if project not initialized."""
        result = runner.invoke(
            app, ["lock", "tests", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestLockTestsShorthand:
    """Tests for 'lock tests' shorthand."""

    def test_lock_tests_finds_latest_testplan(self, tmp_path: Path) -> None:
        """lock tests should find latest TestPlan."""
        (tmp_path / ".project").mkdir()

        # Create approved TestPlan
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.TEST_PLAN,
            status=ArtifactStatus.APPROVED,
            created_by=CreatedBy.LLM,
            payload=_create_test_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.lock._check_phase"
        ):
            result = runner.invoke(
                app,
                ["lock", "tests", "--path", str(tmp_path)],
                input="LOCK\n",
            )

        assert result.exit_code == 0
        assert "locked" in result.stdout.lower()

    def test_lock_tests_fails_when_no_testplan(self, tmp_path: Path) -> None:
        """lock tests should fail when no TestPlan exists."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.lock._check_phase"
        ):
            result = runner.invoke(
                app,
                ["lock", "tests", "--path", str(tmp_path)],
            )

        assert result.exit_code == 1
        assert "no testplan" in result.stdout.lower()


class TestLockRequiresTestPlan:
    """Tests for lock requiring TestPlan."""

    def test_lock_non_testplan_fails(self, tmp_path: Path) -> None:
        """lock should fail for non-TestPlan artifacts."""
        (tmp_path / ".project").mkdir()

        # Create ProjectPlan (not TestPlan)
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
            "rice_factor.entrypoints.cli.commands.lock._check_phase"
        ):
            result = runner.invoke(
                app,
                ["lock", str(artifact.id), "--path", str(tmp_path)],
            )

        assert result.exit_code == 1
        assert "only testplan" in result.stdout.lower()


class TestLockRequiresApproved:
    """Tests for lock requiring approved status."""

    def test_lock_draft_fails(self, tmp_path: Path) -> None:
        """lock should fail for draft artifacts."""
        (tmp_path / ".project").mkdir()

        # Create draft TestPlan
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.TEST_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=_create_test_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.lock._check_phase"
        ):
            result = runner.invoke(
                app,
                ["lock", str(artifact.id), "--path", str(tmp_path)],
            )

        assert result.exit_code == 1
        assert "approved before locking" in result.stdout.lower()


class TestLockConfirmation:
    """Tests for lock confirmation."""

    def test_lock_requires_explicit_confirmation(self, tmp_path: Path) -> None:
        """lock should require typing 'LOCK' to confirm."""
        (tmp_path / ".project").mkdir()

        # Create approved TestPlan
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.TEST_PLAN,
            status=ArtifactStatus.APPROVED,
            created_by=CreatedBy.LLM,
            payload=_create_test_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.lock._check_phase"
        ):
            # Type something other than LOCK
            result = runner.invoke(
                app,
                ["lock", str(artifact.id), "--path", str(tmp_path)],
                input="cancel\n",
            )

        assert result.exit_code == 0
        assert "cancelled" in result.stdout.lower()

        # Verify not locked
        updated = storage.load_by_id(artifact.id)
        assert updated.status == ArtifactStatus.APPROVED

    def test_lock_with_correct_confirmation(self, tmp_path: Path) -> None:
        """lock should succeed with 'LOCK' confirmation."""
        (tmp_path / ".project").mkdir()

        # Create approved TestPlan
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.TEST_PLAN,
            status=ArtifactStatus.APPROVED,
            created_by=CreatedBy.LLM,
            payload=_create_test_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.lock._check_phase"
        ):
            result = runner.invoke(
                app,
                ["lock", str(artifact.id), "--path", str(tmp_path)],
                input="LOCK\n",
            )

        assert result.exit_code == 0
        assert "locked" in result.stdout.lower()

        # Verify locked
        updated = storage.load_by_id(artifact.id)
        assert updated.status == ArtifactStatus.LOCKED


class TestLockAlreadyLocked:
    """Tests for lock with already locked artifact."""

    def test_lock_already_locked_warns(self, tmp_path: Path) -> None:
        """lock should warn if artifact already locked."""
        (tmp_path / ".project").mkdir()

        # Create locked TestPlan
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
            "rice_factor.entrypoints.cli.commands.lock._check_phase"
        ):
            result = runner.invoke(
                app,
                ["lock", str(artifact.id), "--path", str(tmp_path)],
            )

        assert result.exit_code == 0
        assert "already locked" in result.stdout.lower()


class TestLockCreatesAuditEntry:
    """Tests for lock audit trail."""

    def test_lock_creates_audit_entry(self, tmp_path: Path) -> None:
        """Locking an artifact should create an audit entry."""
        (tmp_path / ".project").mkdir()

        # Create approved TestPlan
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.TEST_PLAN,
            status=ArtifactStatus.APPROVED,
            created_by=CreatedBy.LLM,
            payload=_create_test_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        with patch(
            "rice_factor.entrypoints.cli.commands.lock._check_phase"
        ):
            runner.invoke(
                app,
                ["lock", str(artifact.id), "--path", str(tmp_path)],
                input="LOCK\n",
            )

        # Audit trail should exist
        trail_file = tmp_path / "audit" / "trail.json"
        assert trail_file.exists()
