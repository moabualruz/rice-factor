"""Lock manager for TestPlan hash-based locking.

This adapter manages the .project/.lock file that stores SHA-256 hashes
of test files. When TestPlan is locked, the hashes are computed and stored.
Subsequent operations verify that test files haven't been modified.

Lock File Format:
{
    "test_plan_id": "uuid-xxx",
    "locked_at": "2026-01-10T12:00:00Z",
    "test_files": {
        "tests/test_user.rs": "sha256:abc123...",
        "tests/test_email.rs": "sha256:def456..."
    }
}
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID


@dataclass
class LockFile:
    """Represents the lock file contents.

    Attributes:
        test_plan_id: ID of the locked TestPlan.
        locked_at: Timestamp when lock was created.
        test_files: Dict mapping file paths to their SHA-256 hashes.
    """

    test_plan_id: str
    locked_at: datetime
    test_files: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_plan_id": self.test_plan_id,
            "locked_at": self.locked_at.isoformat(),
            "test_files": self.test_files,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LockFile":
        """Create from dictionary.

        Args:
            data: Dictionary with lock file data.

        Returns:
            LockFile instance.
        """
        locked_at = data.get("locked_at", "")
        if isinstance(locked_at, str):
            # Parse ISO format datetime
            if locked_at.endswith("Z"):
                locked_at = locked_at[:-1] + "+00:00"
            locked_at = datetime.fromisoformat(locked_at)
        elif not isinstance(locked_at, datetime):
            locked_at = datetime.now(UTC)

        return cls(
            test_plan_id=data.get("test_plan_id", ""),
            locked_at=locked_at,
            test_files=data.get("test_files", {}),
        )


@dataclass
class LockVerificationResult:
    """Result of lock verification.

    Attributes:
        is_valid: Whether all files match their locked hashes.
        modified_files: List of files that have been modified.
        missing_files: List of files that are missing.
        expected_hashes: Original hashes from lock file.
        actual_hashes: Current computed hashes.
    """

    is_valid: bool
    modified_files: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    expected_hashes: dict[str, str] = field(default_factory=dict)
    actual_hashes: dict[str, str] = field(default_factory=dict)


class LockManager:
    """Manager for TestPlan lock files.

    Handles creation, loading, and verification of lock files that
    ensure test file immutability after TestPlan is locked.

    Attributes:
        project_root: Root directory of the project.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the lock manager.

        Args:
            project_root: Root directory of the project.
        """
        self._project_root = project_root

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    @property
    def lock_file_path(self) -> Path:
        """Get the path to the lock file."""
        return self._project_root / ".project" / ".lock"

    def lock_test_plan(
        self,
        test_plan_id: str | UUID,
        test_files: list[str],
    ) -> LockFile:
        """Create a lock file for a TestPlan.

        Computes SHA-256 hashes for all test files and saves
        them to the lock file.

        Args:
            test_plan_id: ID of the TestPlan being locked.
            test_files: List of test file paths (relative to project root).

        Returns:
            The created LockFile.

        Raises:
            FileNotFoundError: If any test file doesn't exist.
            OSError: If lock file cannot be written.
        """
        # Convert UUID to string if needed
        if isinstance(test_plan_id, UUID):
            test_plan_id = str(test_plan_id)

        # Compute hashes for all test files
        file_hashes: dict[str, str] = {}
        for file_path in test_files:
            full_path = self._project_root / file_path
            hash_value = self._compute_file_hash(full_path)
            file_hashes[file_path] = hash_value

        # Create lock file
        lock_file = LockFile(
            test_plan_id=test_plan_id,
            locked_at=datetime.now(UTC),
            test_files=file_hashes,
        )

        # Save lock file
        self._save_lock_file(lock_file)

        return lock_file

    def get_lock(self) -> LockFile | None:
        """Get the current lock file if it exists.

        Returns:
            LockFile if exists, None otherwise.
        """
        if not self.lock_file_path.exists():
            return None

        try:
            data = json.loads(self.lock_file_path.read_text())
            return LockFile.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError):
            return None

    def is_locked(self) -> bool:
        """Check if a lock file exists.

        Returns:
            True if lock file exists.
        """
        return self.lock_file_path.exists()

    def verify_lock(self) -> LockVerificationResult:
        """Verify that all locked files are unchanged.

        Compares current file hashes against stored hashes.

        Returns:
            LockVerificationResult with verification details.
        """
        lock_file = self.get_lock()
        if lock_file is None:
            # No lock means nothing to verify - valid state
            return LockVerificationResult(is_valid=True)

        modified_files: list[str] = []
        missing_files: list[str] = []
        actual_hashes: dict[str, str] = {}

        for file_path, expected_hash in lock_file.test_files.items():
            full_path = self._project_root / file_path

            if not full_path.exists():
                missing_files.append(file_path)
                actual_hashes[file_path] = "<missing>"
                continue

            actual_hash = self._compute_file_hash(full_path)
            actual_hashes[file_path] = actual_hash

            if actual_hash != expected_hash:
                modified_files.append(file_path)

        is_valid = len(modified_files) == 0 and len(missing_files) == 0

        return LockVerificationResult(
            is_valid=is_valid,
            modified_files=modified_files,
            missing_files=missing_files,
            expected_hashes=lock_file.test_files,
            actual_hashes=actual_hashes,
        )

    def remove_lock(self) -> bool:
        """Remove the lock file.

        Returns:
            True if lock was removed, False if it didn't exist.
        """
        if not self.lock_file_path.exists():
            return False

        self.lock_file_path.unlink()
        return True

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file.

        Args:
            file_path: Path to the file.

        Returns:
            Hash string prefixed with 'sha256:'.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_bytes()
        hash_value = hashlib.sha256(content).hexdigest()
        return f"sha256:{hash_value}"

    def _save_lock_file(self, lock_file: LockFile) -> None:
        """Save lock file to disk.

        Args:
            lock_file: The lock file to save.

        Raises:
            OSError: If file cannot be written.
        """
        # Ensure .project directory exists
        self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write lock file
        content = json.dumps(lock_file.to_dict(), indent=2)
        self.lock_file_path.write_text(content)
