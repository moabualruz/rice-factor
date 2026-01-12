"""Unit tests for ArtifactMigrator service."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from rice_factor.domain.services.artifact_migrator import (
    ArtifactMigrationResult,
    ArtifactMigrator,
    MigrationBatchResult,
    MigrationPlan,
    MigrationStatus,
)


class TestMigrationStatus:
    """Tests for MigrationStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """All expected statuses should exist."""
        assert MigrationStatus.PENDING.value == "pending"
        assert MigrationStatus.IN_PROGRESS.value == "in_progress"
        assert MigrationStatus.COMPLETED.value == "completed"
        assert MigrationStatus.FAILED.value == "failed"
        assert MigrationStatus.SKIPPED.value == "skipped"


class TestArtifactMigrationResult:
    """Tests for ArtifactMigrationResult dataclass."""

    def test_creation(self) -> None:
        """ArtifactMigrationResult should be creatable."""
        result = ArtifactMigrationResult(
            artifact_path="artifacts/test.json",
            artifact_type="ProjectPlan",
            from_version="1.0",
            to_version="1.1",
            status=MigrationStatus.COMPLETED,
        )
        assert result.artifact_path == "artifacts/test.json"
        assert result.status == MigrationStatus.COMPLETED

    def test_with_error(self) -> None:
        """should include error details."""
        result = ArtifactMigrationResult(
            artifact_path="artifacts/test.json",
            artifact_type="ProjectPlan",
            from_version="1.0",
            to_version="1.1",
            status=MigrationStatus.FAILED,
            error="Migration failed: invalid data",
        )
        assert result.error is not None
        assert "failed" in result.error.lower()

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        result = ArtifactMigrationResult(
            artifact_path="test.json",
            artifact_type="TestPlan",
            from_version="1.0",
            to_version="2.0",
            status=MigrationStatus.COMPLETED,
            backup_path="/backup/test.json",
        )
        data = result.to_dict()
        assert data["artifact_path"] == "test.json"
        assert data["status"] == "completed"
        assert data["backup_path"] == "/backup/test.json"


class TestMigrationBatchResult:
    """Tests for MigrationBatchResult dataclass."""

    def test_creation(self) -> None:
        """MigrationBatchResult should be creatable."""
        now = datetime.now(UTC)
        result = MigrationBatchResult(
            started_at=now,
            completed_at=now,
            total_artifacts=10,
            migrated_count=8,
            failed_count=2,
            skipped_count=0,
            results=[],
        )
        assert result.total_artifacts == 10
        assert result.success_rate == 80.0

    def test_success_rate_zero_total(self) -> None:
        """should handle zero total artifacts."""
        now = datetime.now(UTC)
        result = MigrationBatchResult(
            started_at=now,
            completed_at=now,
            total_artifacts=0,
            migrated_count=0,
            failed_count=0,
            skipped_count=0,
            results=[],
        )
        assert result.success_rate == 100.0

    def test_all_succeeded(self) -> None:
        """should detect all succeeded."""
        now = datetime.now(UTC)
        result = MigrationBatchResult(
            started_at=now,
            completed_at=now,
            total_artifacts=5,
            migrated_count=5,
            failed_count=0,
            skipped_count=0,
            results=[],
        )
        assert result.all_succeeded is True

    def test_not_all_succeeded(self) -> None:
        """should detect failures."""
        now = datetime.now(UTC)
        result = MigrationBatchResult(
            started_at=now,
            completed_at=now,
            total_artifacts=5,
            migrated_count=4,
            failed_count=1,
            skipped_count=0,
            results=[],
        )
        assert result.all_succeeded is False

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        result = MigrationBatchResult(
            started_at=now,
            completed_at=now,
            total_artifacts=3,
            migrated_count=3,
            failed_count=0,
            skipped_count=0,
            results=[],
            backup_directory="/backup",
        )
        data = result.to_dict()
        assert data["total_artifacts"] == 3
        assert data["success_rate"] == 100.0
        assert data["backup_directory"] == "/backup"


class TestMigrationPlan:
    """Tests for MigrationPlan dataclass."""

    def test_creation(self) -> None:
        """MigrationPlan should be creatable."""
        plan = MigrationPlan(
            artifacts_to_migrate=[{"path": "a.json"}, {"path": "b.json"}],
            target_version="1.1",
        )
        assert plan.artifact_count == 2
        assert plan.dry_run is True
        assert plan.create_backup is True


class TestArtifactMigrator:
    """Tests for ArtifactMigrator service."""

    def test_creation(self, tmp_path: Path) -> None:
        """ArtifactMigrator should be creatable."""
        migrator = ArtifactMigrator(repo_root=tmp_path)
        assert migrator.repo_root == tmp_path
        assert migrator.artifacts_dir == tmp_path / "artifacts"

    def test_custom_paths(self, tmp_path: Path) -> None:
        """should accept custom paths."""
        custom_artifacts = tmp_path / "custom_artifacts"
        custom_backup = tmp_path / "custom_backup"

        migrator = ArtifactMigrator(
            repo_root=tmp_path,
            artifacts_dir=custom_artifacts,
            backup_dir=custom_backup,
        )
        assert migrator.artifacts_dir == custom_artifacts
        assert migrator.backup_dir == custom_backup

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        """should handle empty artifacts directory."""
        migrator = ArtifactMigrator(repo_root=tmp_path)
        pending = migrator.scan_for_migrations()
        assert pending == []

    def test_scan_with_artifacts(self, tmp_path: Path) -> None:
        """should scan for artifacts needing migration."""
        # Create artifacts directory
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        # Create an artifact with old version
        artifact = {
            "id": "test-123",
            "artifact_type": "ProjectPlan",
            "artifact_version": "0.9",
            "status": "draft",
            "payload": {},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(artifact))

        migrator = ArtifactMigrator(repo_root=tmp_path)
        pending = migrator.scan_for_migrations()

        # Should find the artifact needing migration
        assert len(pending) >= 1

    def test_create_migration_plan(self, tmp_path: Path) -> None:
        """should create migration plan."""
        artifacts_dir = tmp_path / "artifacts" / "test_plans"
        artifacts_dir.mkdir(parents=True)

        artifact = {
            "id": "plan-1",
            "artifact_type": "TestPlan",
            "artifact_version": "0.8",
            "status": "approved",
            "payload": {},
        }
        (artifacts_dir / "plan1.json").write_text(json.dumps(artifact))

        migrator = ArtifactMigrator(repo_root=tmp_path)
        plan = migrator.create_migration_plan(dry_run=True)

        assert plan.dry_run is True
        assert plan.create_backup is True

    def test_create_migration_plan_filter_by_type(self, tmp_path: Path) -> None:
        """should filter by artifact type."""
        # Create two different artifact types
        project_dir = tmp_path / "artifacts" / "project_plans"
        project_dir.mkdir(parents=True)
        test_dir = tmp_path / "artifacts" / "test_plans"
        test_dir.mkdir(parents=True)

        (project_dir / "proj.json").write_text(json.dumps({
            "id": "p1",
            "artifact_type": "ProjectPlan",
            "artifact_version": "0.9",
            "payload": {},
        }))
        (test_dir / "test.json").write_text(json.dumps({
            "id": "t1",
            "artifact_type": "TestPlan",
            "artifact_version": "0.9",
            "payload": {},
        }))

        migrator = ArtifactMigrator(repo_root=tmp_path)
        plan = migrator.create_migration_plan(artifact_type="ProjectPlan")

        # Should only include ProjectPlan
        for artifact in plan.artifacts_to_migrate:
            assert artifact["artifact_type"] == "ProjectPlan"

    def test_execute_dry_run(self, tmp_path: Path) -> None:
        """should skip actual migration in dry run mode."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact = {
            "id": "dry-1",
            "artifact_type": "ProjectPlan",
            "artifact_version": "0.9",
            "payload": {},
        }
        artifact_path = artifacts_dir / "dry.json"
        artifact_path.write_text(json.dumps(artifact))

        migrator = ArtifactMigrator(repo_root=tmp_path)
        plan = migrator.create_migration_plan(dry_run=True)
        result = migrator.execute_migration(plan)

        assert result.skipped_count == result.total_artifacts
        assert result.migrated_count == 0

        # Original file should be unchanged
        original = json.loads(artifact_path.read_text())
        assert original["artifact_version"] == "0.9"

    def test_list_backups_empty(self, tmp_path: Path) -> None:
        """should return empty list when no backups."""
        migrator = ArtifactMigrator(repo_root=tmp_path)
        backups = migrator.list_backups()
        assert backups == []

    def test_list_backups(self, tmp_path: Path) -> None:
        """should list available backups."""
        # Create backup directory
        backup_base = tmp_path / "audit" / "migration_backups"
        backup_dir = backup_base / "migration_20260101_120000"
        backup_dir.mkdir(parents=True)

        # Create a backup artifact
        (backup_dir / "test.json").write_text("{}")

        migrator = ArtifactMigrator(repo_root=tmp_path)
        backups = migrator.list_backups()

        assert len(backups) == 1
        assert backups[0]["artifact_count"] == 1

    def test_delete_backup(self, tmp_path: Path) -> None:
        """should delete backup directory."""
        backup_base = tmp_path / "audit" / "migration_backups"
        backup_dir = backup_base / "migration_test"
        backup_dir.mkdir(parents=True)
        (backup_dir / "test.json").write_text("{}")

        migrator = ArtifactMigrator(repo_root=tmp_path)

        assert migrator.delete_backup(str(backup_dir)) is True
        assert not backup_dir.exists()

    def test_delete_backup_nonexistent(self, tmp_path: Path) -> None:
        """should return False for nonexistent backup."""
        migrator = ArtifactMigrator(repo_root=tmp_path)
        result = migrator.delete_backup("/nonexistent/path")
        assert result is False

    def test_get_migration_summary(self, tmp_path: Path) -> None:
        """should generate migration summary."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        # Create two artifacts needing migration
        for i in range(2):
            artifact = {
                "id": f"sum-{i}",
                "artifact_type": "ProjectPlan",
                "artifact_version": "0.8",
                "payload": {},
            }
            (artifacts_dir / f"art{i}.json").write_text(json.dumps(artifact))

        migrator = ArtifactMigrator(repo_root=tmp_path)
        summary = migrator.get_migration_summary()

        assert summary["total_pending"] >= 2
        assert "ProjectPlan" in summary["by_type"]
        assert "0.8" in summary["by_version"]

    def test_rollback_migration(self, tmp_path: Path) -> None:
        """should rollback from backup."""
        # Create backup structure
        backup_dir = tmp_path / "audit" / "migration_backups" / "migration_test"
        backup_artifact_dir = backup_dir / "artifacts" / "project_plans"
        backup_artifact_dir.mkdir(parents=True)

        # Create original artifact
        original = {
            "id": "rollback-1",
            "artifact_type": "ProjectPlan",
            "artifact_version": "0.9",
            "payload": {"original": True},
        }
        (backup_artifact_dir / "rb.json").write_text(json.dumps(original))

        # Create current (migrated) artifact
        current_dir = tmp_path / "artifacts" / "project_plans"
        current_dir.mkdir(parents=True)
        current = {
            "id": "rollback-1",
            "artifact_type": "ProjectPlan",
            "artifact_version": "1.0",
            "payload": {"migrated": True},
        }
        current_path = current_dir / "rb.json"
        current_path.write_text(json.dumps(current))

        migrator = ArtifactMigrator(repo_root=tmp_path)
        result = migrator.rollback_migration(str(backup_dir))

        assert result.migrated_count == 1
        assert result.failed_count == 0

        # Verify file was restored
        restored = json.loads(current_path.read_text())
        assert restored["artifact_version"] == "0.9"
        assert restored["payload"]["original"] is True

    def test_rollback_nonexistent_backup(self, tmp_path: Path) -> None:
        """should handle nonexistent backup directory."""
        migrator = ArtifactMigrator(repo_root=tmp_path)
        result = migrator.rollback_migration("/nonexistent/backup")

        assert result.total_artifacts == 0
        assert result.migrated_count == 0
