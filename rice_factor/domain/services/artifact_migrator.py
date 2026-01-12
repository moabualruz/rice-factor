"""Artifact migrator service for batch schema migrations.

This module provides the ArtifactMigrator service that performs batch
migrations of artifacts on disk, with backup support and reporting.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class MigrationStatus(Enum):
    """Status of a migration operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ArtifactMigrationResult:
    """Result of migrating a single artifact."""

    artifact_path: str
    artifact_type: str
    from_version: str
    to_version: str
    status: MigrationStatus
    error: str | None = None
    backup_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "artifact_path": self.artifact_path,
            "artifact_type": self.artifact_type,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "status": self.status.value,
            "error": self.error,
            "backup_path": self.backup_path,
        }


@dataclass
class MigrationBatchResult:
    """Result of a batch migration operation."""

    started_at: datetime
    completed_at: datetime | None
    total_artifacts: int
    migrated_count: int
    failed_count: int
    skipped_count: int
    results: list[ArtifactMigrationResult]
    backup_directory: str | None = None

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_artifacts == 0:
            return 100.0
        return (self.migrated_count / self.total_artifacts) * 100

    @property
    def all_succeeded(self) -> bool:
        """Check if all migrations succeeded."""
        return self.failed_count == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "total_artifacts": self.total_artifacts,
            "migrated_count": self.migrated_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "success_rate": round(self.success_rate, 2),
            "backup_directory": self.backup_directory,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class MigrationPlan:
    """Plan for artifact migrations."""

    artifacts_to_migrate: list[dict[str, Any]]
    target_version: str
    dry_run: bool = True
    create_backup: bool = True

    @property
    def artifact_count(self) -> int:
        """Get number of artifacts to migrate."""
        return len(self.artifacts_to_migrate)


@dataclass
class ArtifactMigrator:
    """Service for batch artifact migrations.

    This service scans artifacts on disk, identifies those needing migration,
    creates backups, and performs batch migrations with detailed reporting.

    Attributes:
        repo_root: Root directory of the repository.
        artifacts_dir: Directory containing artifacts.
        backup_dir: Directory for migration backups.
    """

    repo_root: Path
    artifacts_dir: Path | None = None
    backup_dir: Path | None = None
    _version_manager: Any = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Initialize paths."""
        if self.artifacts_dir is None:
            self.artifacts_dir = self.repo_root / "artifacts"
        if self.backup_dir is None:
            self.backup_dir = self.repo_root / "audit" / "migration_backups"

    def _get_version_manager(self) -> Any:
        """Get schema version manager (lazy load)."""
        if self._version_manager is None:
            from rice_factor.domain.services.schema_version_manager import (
                get_schema_version_manager,
            )
            self._version_manager = get_schema_version_manager()
        return self._version_manager

    def scan_for_migrations(self) -> list[dict[str, Any]]:
        """Scan artifacts directory for artifacts needing migration.

        Returns:
            List of artifact info dicts with path, type, and version.
        """
        needs_migration: list[dict[str, Any]] = []

        if not self.artifacts_dir.exists():
            return needs_migration

        version_manager = self._get_version_manager()

        for json_path in self.artifacts_dir.rglob("*.json"):
            if "_meta" in str(json_path):
                continue

            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                artifact_type = data.get("artifact_type", "")
                artifact_version = data.get("artifact_version", "1.0")

                if version_manager.needs_migration(data, artifact_type):
                    current_version = version_manager.get_current_version(artifact_type)
                    needs_migration.append({
                        "path": str(json_path),
                        "relative_path": str(json_path.relative_to(self.repo_root)),
                        "artifact_type": artifact_type,
                        "current_version": artifact_version,
                        "target_version": str(current_version) if current_version else "1.0",
                        "artifact_id": data.get("id", ""),
                    })

            except (json.JSONDecodeError, OSError):
                # Skip malformed files
                continue

        return needs_migration

    def create_migration_plan(
        self,
        target_version: str | None = None,
        artifact_type: str | None = None,
        dry_run: bool = True,
        create_backup: bool = True,
    ) -> MigrationPlan:
        """Create a migration plan.

        Args:
            target_version: Target version (uses current if None).
            artifact_type: Filter by artifact type.
            dry_run: If True, don't actually migrate.
            create_backup: If True, create backups.

        Returns:
            MigrationPlan with artifacts to migrate.
        """
        artifacts = self.scan_for_migrations()

        if artifact_type:
            artifacts = [a for a in artifacts if a["artifact_type"] == artifact_type]

        if target_version:
            # Filter to only those needing this specific version
            artifacts = [
                a for a in artifacts
                if self._needs_version(a, target_version)
            ]

        return MigrationPlan(
            artifacts_to_migrate=artifacts,
            target_version=target_version or "current",
            dry_run=dry_run,
            create_backup=create_backup,
        )

    def _needs_version(self, artifact_info: dict[str, Any], target: str) -> bool:
        """Check if artifact needs migration to target version.

        Args:
            artifact_info: Artifact information dict.
            target: Target version string.

        Returns:
            True if migration is needed.
        """
        current = artifact_info.get("current_version", "1.0")
        return current != target

    def execute_migration(
        self,
        plan: MigrationPlan,
    ) -> MigrationBatchResult:
        """Execute a migration plan.

        Args:
            plan: Migration plan to execute.

        Returns:
            MigrationBatchResult with details.
        """
        started_at = datetime.now(UTC)
        results: list[ArtifactMigrationResult] = []
        migrated_count = 0
        failed_count = 0
        skipped_count = 0
        backup_directory: str | None = None

        # Create backup directory if needed
        if plan.create_backup and not plan.dry_run:
            backup_directory = self._create_backup_directory()

        version_manager = self._get_version_manager()

        for artifact_info in plan.artifacts_to_migrate:
            artifact_path = Path(artifact_info["path"])
            artifact_type = artifact_info["artifact_type"]
            from_version = artifact_info["current_version"]
            target_version = artifact_info.get("target_version", plan.target_version)

            if plan.dry_run:
                # Dry run - just report what would happen
                result = ArtifactMigrationResult(
                    artifact_path=artifact_info["relative_path"],
                    artifact_type=artifact_type,
                    from_version=from_version,
                    to_version=target_version,
                    status=MigrationStatus.SKIPPED,
                )
                skipped_count += 1
                results.append(result)
                continue

            try:
                # Create backup if requested
                backup_path: str | None = None
                if plan.create_backup and backup_directory:
                    backup_path = self._backup_artifact(
                        artifact_path, backup_directory
                    )

                # Load artifact
                data = json.loads(artifact_path.read_text(encoding="utf-8"))

                # Perform migration
                if target_version == "current":
                    migrated_data = version_manager.migrate(
                        data, artifact_type, from_version
                    )
                else:
                    migrated_data = version_manager.migrate(
                        data, artifact_type, from_version, target_version
                    )

                # Write migrated artifact
                artifact_path.write_text(
                    json.dumps(migrated_data, indent=2),
                    encoding="utf-8",
                )

                result = ArtifactMigrationResult(
                    artifact_path=artifact_info["relative_path"],
                    artifact_type=artifact_type,
                    from_version=from_version,
                    to_version=migrated_data.get("artifact_version", target_version),
                    status=MigrationStatus.COMPLETED,
                    backup_path=backup_path,
                )
                migrated_count += 1

            except Exception as e:
                result = ArtifactMigrationResult(
                    artifact_path=artifact_info["relative_path"],
                    artifact_type=artifact_type,
                    from_version=from_version,
                    to_version=target_version,
                    status=MigrationStatus.FAILED,
                    error=str(e),
                )
                failed_count += 1

            results.append(result)

        completed_at = datetime.now(UTC)

        return MigrationBatchResult(
            started_at=started_at,
            completed_at=completed_at,
            total_artifacts=len(plan.artifacts_to_migrate),
            migrated_count=migrated_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            results=results,
            backup_directory=backup_directory,
        )

    def _create_backup_directory(self) -> str:
        """Create a backup directory for this migration.

        Returns:
            Path to backup directory.
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"migration_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        return str(backup_path)

    def _backup_artifact(
        self, artifact_path: Path, backup_directory: str
    ) -> str:
        """Backup a single artifact.

        Args:
            artifact_path: Path to artifact.
            backup_directory: Directory for backup.

        Returns:
            Path to backup file.
        """
        backup_dir_path = Path(backup_directory)
        relative = artifact_path.relative_to(self.repo_root)
        backup_path = backup_dir_path / relative
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact_path, backup_path)
        return str(backup_path)

    def rollback_migration(self, backup_directory: str) -> MigrationBatchResult:
        """Rollback a migration from backup.

        Args:
            backup_directory: Path to backup directory.

        Returns:
            MigrationBatchResult with rollback details.
        """
        started_at = datetime.now(UTC)
        results: list[ArtifactMigrationResult] = []
        migrated_count = 0
        failed_count = 0

        backup_path = Path(backup_directory)
        if not backup_path.exists():
            return MigrationBatchResult(
                started_at=started_at,
                completed_at=datetime.now(UTC),
                total_artifacts=0,
                migrated_count=0,
                failed_count=0,
                skipped_count=0,
                results=[],
            )

        for json_path in backup_path.rglob("*.json"):
            try:
                relative = json_path.relative_to(backup_path)
                target_path = self.repo_root / relative

                # Restore from backup
                shutil.copy2(json_path, target_path)

                # Get version info
                data = json.loads(json_path.read_text(encoding="utf-8"))

                result = ArtifactMigrationResult(
                    artifact_path=str(relative),
                    artifact_type=data.get("artifact_type", "unknown"),
                    from_version="migrated",
                    to_version=data.get("artifact_version", "1.0"),
                    status=MigrationStatus.COMPLETED,
                )
                migrated_count += 1

            except Exception as e:
                result = ArtifactMigrationResult(
                    artifact_path=str(relative) if 'relative' in dir() else str(json_path),
                    artifact_type="unknown",
                    from_version="migrated",
                    to_version="unknown",
                    status=MigrationStatus.FAILED,
                    error=str(e),
                )
                failed_count += 1

            results.append(result)

        return MigrationBatchResult(
            started_at=started_at,
            completed_at=datetime.now(UTC),
            total_artifacts=len(results),
            migrated_count=migrated_count,
            failed_count=failed_count,
            skipped_count=0,
            results=results,
            backup_directory=backup_directory,
        )

    def list_backups(self) -> list[dict[str, Any]]:
        """List available backup directories.

        Returns:
            List of backup info dicts.
        """
        backups: list[dict[str, Any]] = []

        if not self.backup_dir.exists():
            return backups

        for backup_path in sorted(self.backup_dir.iterdir(), reverse=True):
            if backup_path.is_dir() and backup_path.name.startswith("migration_"):
                artifact_count = sum(1 for _ in backup_path.rglob("*.json"))
                backups.append({
                    "path": str(backup_path),
                    "name": backup_path.name,
                    "artifact_count": artifact_count,
                    "created_at": backup_path.stat().st_mtime,
                })

        return backups

    def delete_backup(self, backup_directory: str) -> bool:
        """Delete a backup directory.

        Args:
            backup_directory: Path to backup directory.

        Returns:
            True if deleted, False if not found.
        """
        backup_path = Path(backup_directory)
        if not backup_path.exists():
            return False

        shutil.rmtree(backup_path)
        return True

    def get_migration_summary(self) -> dict[str, Any]:
        """Get a summary of pending migrations.

        Returns:
            Summary dict with counts by type and version.
        """
        pending = self.scan_for_migrations()

        by_type: dict[str, int] = {}
        by_version: dict[str, int] = {}

        for artifact in pending:
            atype = artifact["artifact_type"]
            version = artifact["current_version"]
            by_type[atype] = by_type.get(atype, 0) + 1
            by_version[version] = by_version.get(version, 0) + 1

        return {
            "total_pending": len(pending),
            "by_type": by_type,
            "by_version": by_version,
            "backups_available": len(self.list_backups()),
        }
