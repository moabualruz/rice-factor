"""Incremental validation service for efficient change detection.

This module provides the IncrementalValidator service that skips unchanged
files during validation using hash-based change detection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ChangeType(Enum):
    """Type of change detected."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class FileChange:
    """A detected file change.

    Attributes:
        path: Path to the file.
        change_type: Type of change.
        old_hash: Hash before change (None if added).
        new_hash: Hash after change (None if deleted).
    """

    path: str
    change_type: ChangeType
    old_hash: str | None = None
    new_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "change_type": self.change_type.value,
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
        }


@dataclass
class HashRecord:
    """A stored hash record for a file.

    Attributes:
        path: File path.
        hash: Content hash.
        size: File size in bytes.
        modified_at: File modification time.
        recorded_at: When the hash was recorded.
    """

    path: str
    hash: str
    size: int
    modified_at: float
    recorded_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "hash": self.hash,
            "size": self.size,
            "modified_at": self.modified_at,
            "recorded_at": self.recorded_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HashRecord:
        """Create from dictionary."""
        return cls(
            path=data["path"],
            hash=data["hash"],
            size=data["size"],
            modified_at=data["modified_at"],
            recorded_at=datetime.fromisoformat(data["recorded_at"]),
        )


@dataclass
class ValidationResult:
    """Result of incremental validation.

    Attributes:
        total_files: Total files examined.
        changed_count: Number of changed files.
        unchanged_count: Number of unchanged files.
        changes: List of detected changes.
        validated_at: When validation completed.
    """

    total_files: int
    changed_count: int
    unchanged_count: int
    changes: list[FileChange]
    validated_at: datetime

    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return self.changed_count > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_files": self.total_files,
            "changed_count": self.changed_count,
            "unchanged_count": self.unchanged_count,
            "has_changes": self.has_changes,
            "validated_at": self.validated_at.isoformat(),
            "changes": [c.to_dict() for c in self.changes],
        }


@dataclass
class IncrementalValidator:
    """Service for incremental validation with change detection.

    Uses content hashing to track file changes and skip validation
    for unchanged files.

    Attributes:
        repo_root: Root directory of the repository.
        hash_store_path: Path to store hash records.
    """

    repo_root: Path
    hash_store_path: Path | None = None
    _hash_records: dict[str, HashRecord] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Initialize paths and load existing records."""
        if self.hash_store_path is None:
            self.hash_store_path = self.repo_root / ".rice_factor" / "file_hashes.json"
        self._load_records()

    def _load_records(self) -> None:
        """Load hash records from store."""
        if self.hash_store_path.exists():
            try:
                data = json.loads(self.hash_store_path.read_text(encoding="utf-8"))
                self._hash_records = {
                    path: HashRecord.from_dict(record)
                    for path, record in data.get("records", {}).items()
                }
            except (json.JSONDecodeError, OSError):
                self._hash_records = {}

    def _save_records(self) -> None:
        """Save hash records to store."""
        self.hash_store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "updated_at": datetime.now(UTC).isoformat(),
            "records": {path: rec.to_dict() for path, rec in self._hash_records.items()},
        }
        self.hash_store_path.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def compute_hash(self, file_path: Path) -> str:
        """Compute hash for a file.

        Args:
            file_path: Path to the file.

        Returns:
            SHA256 hash of file contents.
        """
        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except OSError:
            return ""

    def check_file(self, file_path: Path) -> FileChange:
        """Check a single file for changes.

        Args:
            file_path: Path to the file.

        Returns:
            FileChange describing the change.
        """
        relative_path = str(file_path.relative_to(self.repo_root))

        if not file_path.exists():
            # File was deleted
            old_record = self._hash_records.get(relative_path)
            return FileChange(
                path=relative_path,
                change_type=ChangeType.DELETED,
                old_hash=old_record.hash if old_record else None,
                new_hash=None,
            )

        new_hash = self.compute_hash(file_path)
        old_record = self._hash_records.get(relative_path)

        if old_record is None:
            # New file
            return FileChange(
                path=relative_path,
                change_type=ChangeType.ADDED,
                old_hash=None,
                new_hash=new_hash,
            )

        if old_record.hash != new_hash:
            # Modified file
            return FileChange(
                path=relative_path,
                change_type=ChangeType.MODIFIED,
                old_hash=old_record.hash,
                new_hash=new_hash,
            )

        # Unchanged
        return FileChange(
            path=relative_path,
            change_type=ChangeType.UNCHANGED,
            old_hash=old_record.hash,
            new_hash=new_hash,
        )

    def validate(
        self,
        paths: list[Path],
        update_records: bool = True,
    ) -> ValidationResult:
        """Validate files for changes.

        Args:
            paths: List of file paths to check.
            update_records: Whether to update stored hashes.

        Returns:
            ValidationResult with detected changes.
        """
        changes: list[FileChange] = []
        changed_count = 0
        unchanged_count = 0

        for file_path in paths:
            if not file_path.is_absolute():
                file_path = self.repo_root / file_path

            change = self.check_file(file_path)
            changes.append(change)

            if change.change_type == ChangeType.UNCHANGED:
                unchanged_count += 1
            else:
                changed_count += 1

            # Update records if requested
            if update_records:
                relative_path = str(file_path.relative_to(self.repo_root))
                if change.change_type == ChangeType.DELETED:
                    self._hash_records.pop(relative_path, None)
                elif change.new_hash:
                    stat = file_path.stat() if file_path.exists() else None
                    self._hash_records[relative_path] = HashRecord(
                        path=relative_path,
                        hash=change.new_hash,
                        size=stat.st_size if stat else 0,
                        modified_at=stat.st_mtime if stat else 0,
                        recorded_at=datetime.now(UTC),
                    )

        if update_records:
            self._save_records()

        return ValidationResult(
            total_files=len(paths),
            changed_count=changed_count,
            unchanged_count=unchanged_count,
            changes=changes,
            validated_at=datetime.now(UTC),
        )

    def validate_directory(
        self,
        directory: Path,
        pattern: str = "*",
        recursive: bool = True,
        update_records: bool = True,
    ) -> ValidationResult:
        """Validate all files in a directory.

        Args:
            directory: Directory to validate.
            pattern: Glob pattern for files.
            recursive: Search recursively.
            update_records: Whether to update stored hashes.

        Returns:
            ValidationResult with detected changes.
        """
        if not directory.is_absolute():
            directory = self.repo_root / directory

        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))

        # Filter to only files
        files = [f for f in files if f.is_file()]

        return self.validate(files, update_records)

    def get_changed_files(
        self,
        paths: list[Path],
    ) -> list[Path]:
        """Get only the changed files from a list.

        Args:
            paths: List of file paths to check.

        Returns:
            List of changed file paths.
        """
        result = self.validate(paths, update_records=False)
        return [
            self.repo_root / change.path
            for change in result.changes
            if change.change_type != ChangeType.UNCHANGED
        ]

    def invalidate(self, path: str | Path) -> bool:
        """Invalidate the hash record for a file.

        Args:
            path: File path to invalidate.

        Returns:
            True if record was invalidated.
        """
        if isinstance(path, Path):
            if path.is_absolute():
                path = str(path.relative_to(self.repo_root))
            else:
                path = str(path)

        if path in self._hash_records:
            del self._hash_records[path]
            self._save_records()
            return True
        return False

    def invalidate_all(self) -> int:
        """Invalidate all hash records.

        Returns:
            Number of records invalidated.
        """
        count = len(self._hash_records)
        self._hash_records.clear()
        self._save_records()
        return count

    def get_record(self, path: str | Path) -> HashRecord | None:
        """Get the hash record for a file.

        Args:
            path: File path.

        Returns:
            HashRecord if exists.
        """
        if isinstance(path, Path):
            if path.is_absolute():
                path = str(path.relative_to(self.repo_root))
            else:
                path = str(path)

        return self._hash_records.get(path)

    def get_all_records(self) -> dict[str, HashRecord]:
        """Get all hash records.

        Returns:
            Dictionary of path to HashRecord.
        """
        return dict(self._hash_records)
