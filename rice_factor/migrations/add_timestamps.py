"""Migration script to add timestamp fields to existing artifacts.

This migration adds the `updated_at` field to artifacts that don't have it,
using the file modification time as a fallback. It also ensures `created_at`
is present, using file modification time if missing.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ArtifactMigrationResult:
    """Result of a migration operation.

    Attributes:
        migrated: Number of artifacts that were migrated.
        skipped: Number of artifacts that were already up-to-date.
        failed: Number of artifacts that failed to migrate.
        errors: List of error messages.
    """

    def __init__(self) -> None:
        self.migrated: int = 0
        self.skipped: int = 0
        self.failed: int = 0
        self.errors: list[str] = []

    @property
    def total(self) -> int:
        """Total number of artifacts processed."""
        return self.migrated + self.skipped + self.failed


def migrate_artifact(artifact_path: Path, dry_run: bool = False) -> bool:
    """Add timestamps to an artifact if missing.

    This migration is idempotent - calling it multiple times on the same
    artifact will not change it after the first migration.

    Args:
        artifact_path: Path to the artifact JSON file.
        dry_run: If True, don't write changes to disk.

    Returns:
        True if the artifact was migrated, False if skipped.

    Raises:
        json.JSONDecodeError: If the artifact file is not valid JSON.
        OSError: If the file cannot be read or written.
    """
    content = artifact_path.read_text(encoding="utf-8")
    data = json.loads(content)

    # Check if migration is needed
    needs_migration = False

    # Get file modification time as fallback
    stat = artifact_path.stat()
    file_mtime = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
    file_mtime_iso = file_mtime.isoformat()

    # Add created_at if missing
    if "created_at" not in data or data["created_at"] is None:
        data["created_at"] = file_mtime_iso
        needs_migration = True
        logger.debug(f"Adding created_at to {artifact_path}")

    # Add updated_at if missing
    if "updated_at" not in data or data["updated_at"] is None:
        # Default to created_at if available, otherwise file mtime
        data["updated_at"] = data.get("created_at") or file_mtime_iso
        needs_migration = True
        logger.debug(f"Adding updated_at to {artifact_path}")

    if not needs_migration:
        logger.debug(f"Skipping {artifact_path} - already has timestamps")
        return False

    if not dry_run:
        # Preserve existing formatting
        artifact_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.info(f"Migrated {artifact_path}")

    return True


def migrate_artifacts_directory(
    artifacts_dir: Path, dry_run: bool = False
) -> ArtifactMigrationResult:
    """Migrate all artifacts in a directory.

    Recursively finds all JSON files in the artifacts directory and
    migrates them to add timestamp fields.

    Args:
        artifacts_dir: Path to the artifacts directory.
        dry_run: If True, don't write changes to disk.

    Returns:
        ArtifactMigrationResult with counts and errors.
    """
    result = ArtifactMigrationResult()

    if not artifacts_dir.exists():
        logger.warning(f"Artifacts directory does not exist: {artifacts_dir}")
        return result

    # Find all JSON files except metadata files
    for artifact_path in artifacts_dir.rglob("*.json"):
        # Skip metadata files
        if artifact_path.parent.name == "_meta":
            continue

        try:
            was_migrated = migrate_artifact(artifact_path, dry_run=dry_run)
            if was_migrated:
                result.migrated += 1
            else:
                result.skipped += 1
        except json.JSONDecodeError as e:
            result.failed += 1
            error_msg = f"Invalid JSON in {artifact_path}: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)
        except OSError as e:
            result.failed += 1
            error_msg = f"Cannot access {artifact_path}: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)

    return result


def run_migration(
    repo_root: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> ArtifactMigrationResult:
    """Run the timestamp migration on a repository.

    This is the main entry point for the migration.

    Args:
        repo_root: Path to the repository root.
        dry_run: If True, don't write changes to disk.
        verbose: If True, enable debug logging.

    Returns:
        ArtifactMigrationResult with counts and errors.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    artifacts_dir = repo_root / "artifacts"

    if dry_run:
        logger.info("DRY RUN - no changes will be made")

    logger.info(f"Migrating artifacts in {artifacts_dir}")
    result = migrate_artifacts_directory(artifacts_dir, dry_run=dry_run)

    logger.info(
        f"Migration complete: {result.migrated} migrated, "
        f"{result.skipped} skipped, {result.failed} failed"
    )

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Add timestamp fields to existing artifacts"
    )
    parser.add_argument(
        "repo_root",
        type=Path,
        help="Path to the repository root",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write changes to disk",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    result = run_migration(
        repo_root=args.repo_root,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    # Exit with error code if any failures
    exit(1 if result.failed > 0 else 0)
