"""Unit tests for add_timestamps migration."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from rice_factor.migrations.add_timestamps import (
    ArtifactMigrationResult,
    migrate_artifact,
    migrate_artifacts_directory,
    run_migration,
)


def _create_artifact(path: Path, data: dict) -> Path:
    """Create an artifact file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


class TestMigrateArtifact:
    """Tests for migrate_artifact function."""

    def test_adds_missing_timestamps(self, tmp_path: Path) -> None:
        """Should add created_at and updated_at if missing."""
        artifact_path = tmp_path / "artifacts" / "plan.json"
        _create_artifact(artifact_path, {
            "id": "test-001",
            "artifact_type": "ProjectPlan",
            "status": "draft",
        })

        was_migrated = migrate_artifact(artifact_path)

        assert was_migrated is True
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert "created_at" in data
        assert "updated_at" in data

    def test_preserves_existing_timestamps(self, tmp_path: Path) -> None:
        """Should not modify existing timestamps."""
        artifact_path = tmp_path / "artifacts" / "plan.json"
        existing_time = "2026-01-01T00:00:00+00:00"
        _create_artifact(artifact_path, {
            "id": "test-001",
            "artifact_type": "ProjectPlan",
            "status": "draft",
            "created_at": existing_time,
            "updated_at": existing_time,
        })

        was_migrated = migrate_artifact(artifact_path)

        assert was_migrated is False
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert data["created_at"] == existing_time
        assert data["updated_at"] == existing_time

    def test_adds_updated_at_when_only_created_at_exists(self, tmp_path: Path) -> None:
        """Should add updated_at using created_at when only created_at exists."""
        artifact_path = tmp_path / "artifacts" / "plan.json"
        existing_time = "2026-01-01T00:00:00+00:00"
        _create_artifact(artifact_path, {
            "id": "test-001",
            "artifact_type": "ProjectPlan",
            "created_at": existing_time,
        })

        was_migrated = migrate_artifact(artifact_path)

        assert was_migrated is True
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert data["created_at"] == existing_time
        assert data["updated_at"] == existing_time

    def test_dry_run_does_not_modify(self, tmp_path: Path) -> None:
        """Dry run should not modify the file."""
        artifact_path = tmp_path / "artifacts" / "plan.json"
        original_data = {
            "id": "test-001",
            "artifact_type": "ProjectPlan",
        }
        _create_artifact(artifact_path, original_data)

        was_migrated = migrate_artifact(artifact_path, dry_run=True)

        assert was_migrated is True
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert "created_at" not in data

    def test_idempotent(self, tmp_path: Path) -> None:
        """Running migration multiple times should not change result."""
        artifact_path = tmp_path / "artifacts" / "plan.json"
        _create_artifact(artifact_path, {
            "id": "test-001",
            "artifact_type": "ProjectPlan",
        })

        # First run
        first_result = migrate_artifact(artifact_path)
        first_data = json.loads(artifact_path.read_text(encoding="utf-8"))

        # Second run
        second_result = migrate_artifact(artifact_path)
        second_data = json.loads(artifact_path.read_text(encoding="utf-8"))

        assert first_result is True
        assert second_result is False
        assert first_data == second_data

    def test_preserves_existing_data(self, tmp_path: Path) -> None:
        """Should preserve all existing artifact data."""
        artifact_path = tmp_path / "artifacts" / "plan.json"
        original_data = {
            "id": "test-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "Test Project"},
            "custom_field": "custom_value",
        }
        _create_artifact(artifact_path, original_data)

        migrate_artifact(artifact_path)

        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert data["id"] == "test-001"
        assert data["artifact_type"] == "ProjectPlan"
        assert data["status"] == "approved"
        assert data["payload"] == {"name": "Test Project"}
        assert data["custom_field"] == "custom_value"

    def test_uses_file_mtime_as_fallback(self, tmp_path: Path) -> None:
        """Should use file modification time when no timestamps exist."""
        artifact_path = tmp_path / "artifacts" / "plan.json"
        _create_artifact(artifact_path, {"id": "test-001"})

        # Get file mtime
        stat = artifact_path.stat()
        expected_mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

        migrate_artifact(artifact_path)

        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        created_at = datetime.fromisoformat(data["created_at"])
        # Should be within 1 second of file mtime
        diff = abs((created_at - expected_mtime).total_seconds())
        assert diff < 1


class TestMigrateArtifactsDirectory:
    """Tests for migrate_artifacts_directory function."""

    def test_migrates_all_artifacts(self, tmp_path: Path) -> None:
        """Should migrate all artifacts in directory."""
        artifacts_dir = tmp_path / "artifacts"
        _create_artifact(artifacts_dir / "plans" / "plan1.json", {"id": "1"})
        _create_artifact(artifacts_dir / "plans" / "plan2.json", {"id": "2"})
        _create_artifact(artifacts_dir / "tests" / "test1.json", {"id": "3"})

        result = migrate_artifacts_directory(artifacts_dir)

        assert result.migrated == 3
        assert result.skipped == 0
        assert result.failed == 0
        assert result.total == 3

    def test_skips_already_migrated(self, tmp_path: Path) -> None:
        """Should skip artifacts that already have timestamps."""
        artifacts_dir = tmp_path / "artifacts"
        _create_artifact(artifacts_dir / "plan.json", {
            "id": "1",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })

        result = migrate_artifacts_directory(artifacts_dir)

        assert result.migrated == 0
        assert result.skipped == 1

    def test_handles_invalid_json(self, tmp_path: Path) -> None:
        """Should handle files with invalid JSON."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir(parents=True)
        (artifacts_dir / "invalid.json").write_text("not valid json")

        result = migrate_artifacts_directory(artifacts_dir)

        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Invalid JSON" in result.errors[0]

    def test_skips_meta_directory(self, tmp_path: Path) -> None:
        """Should skip files in _meta directory."""
        artifacts_dir = tmp_path / "artifacts"
        _create_artifact(artifacts_dir / "_meta" / "hashes.json", {"hash": "abc"})
        _create_artifact(artifacts_dir / "plan.json", {"id": "1"})

        result = migrate_artifacts_directory(artifacts_dir)

        assert result.total == 1
        assert result.migrated == 1

    def test_handles_missing_directory(self, tmp_path: Path) -> None:
        """Should handle non-existent artifacts directory."""
        artifacts_dir = tmp_path / "nonexistent"

        result = migrate_artifacts_directory(artifacts_dir)

        assert result.total == 0


class TestRunMigration:
    """Tests for run_migration function."""

    def test_migrates_repo_artifacts(self, tmp_path: Path) -> None:
        """Should migrate artifacts in repo root."""
        artifacts_dir = tmp_path / "artifacts"
        _create_artifact(artifacts_dir / "plan.json", {"id": "1"})

        result = run_migration(tmp_path)

        assert result.migrated == 1

    def test_dry_run_no_changes(self, tmp_path: Path) -> None:
        """Dry run should not modify files."""
        artifacts_dir = tmp_path / "artifacts"
        _create_artifact(artifacts_dir / "plan.json", {"id": "1"})

        result = run_migration(tmp_path, dry_run=True)

        assert result.migrated == 1
        # Check file was not actually modified
        data = json.loads((artifacts_dir / "plan.json").read_text(encoding="utf-8"))
        assert "created_at" not in data


class TestArtifactMigrationResult:
    """Tests for ArtifactMigrationResult class."""

    def test_total_calculation(self) -> None:
        """Should calculate total from migrated, skipped, failed."""
        result = ArtifactMigrationResult()
        result.migrated = 5
        result.skipped = 3
        result.failed = 2

        assert result.total == 10

    def test_initial_values(self) -> None:
        """Should initialize with zero values."""
        result = ArtifactMigrationResult()

        assert result.migrated == 0
        assert result.skipped == 0
        assert result.failed == 0
        assert result.errors == []
        assert result.total == 0
