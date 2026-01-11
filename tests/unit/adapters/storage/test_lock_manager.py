"""Unit tests for LockManager adapter."""

import json
from datetime import UTC, datetime
from pathlib import Path

from rice_factor.adapters.storage.lock_manager import (
    LockFile,
    LockManager,
)


class TestLockFile:
    """Tests for LockFile dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        lock = LockFile(
            test_plan_id="test-123",
            locked_at=datetime(2026, 1, 10, 12, 0, 0, tzinfo=UTC),
            test_files={"tests/test_user.py": "sha256:abc123"},
        )
        result = lock.to_dict()
        assert result["test_plan_id"] == "test-123"
        assert result["locked_at"] == "2026-01-10T12:00:00+00:00"
        assert result["test_files"] == {"tests/test_user.py": "sha256:abc123"}

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        data = {
            "test_plan_id": "test-123",
            "locked_at": "2026-01-10T12:00:00Z",
            "test_files": {"tests/test_user.py": "sha256:abc123"},
        }
        lock = LockFile.from_dict(data)
        assert lock.test_plan_id == "test-123"
        assert lock.test_files == {"tests/test_user.py": "sha256:abc123"}

    def test_from_dict_with_offset(self) -> None:
        """Test deserialization with timezone offset."""
        data = {
            "test_plan_id": "test-123",
            "locked_at": "2026-01-10T12:00:00+00:00",
            "test_files": {},
        }
        lock = LockFile.from_dict(data)
        assert lock.test_plan_id == "test-123"


class TestLockManager:
    """Tests for LockManager."""

    def test_lock_file_path(self, tmp_path: Path) -> None:
        """Test lock file path property."""
        manager = LockManager(project_root=tmp_path)
        assert manager.lock_file_path == tmp_path / ".project" / ".lock"

    def test_is_locked_no_file(self, tmp_path: Path) -> None:
        """is_locked returns False when no lock file."""
        manager = LockManager(project_root=tmp_path)
        assert not manager.is_locked()

    def test_is_locked_with_file(self, tmp_path: Path) -> None:
        """is_locked returns True when lock file exists."""
        (tmp_path / ".project").mkdir()
        (tmp_path / ".project" / ".lock").write_text("{}")
        manager = LockManager(project_root=tmp_path)
        assert manager.is_locked()

    def test_lock_test_plan_creates_file(self, tmp_path: Path) -> None:
        """lock_test_plan creates lock file with hashes."""
        # Create test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_user.py"
        test_file.write_text("def test_user(): pass")

        manager = LockManager(project_root=tmp_path)
        lock = manager.lock_test_plan(
            test_plan_id="test-123",
            test_files=["tests/test_user.py"],
        )

        assert lock.test_plan_id == "test-123"
        assert "tests/test_user.py" in lock.test_files
        assert lock.test_files["tests/test_user.py"].startswith("sha256:")

        # Verify file was created
        assert manager.lock_file_path.exists()

    def test_lock_test_plan_with_uuid(self, tmp_path: Path) -> None:
        """lock_test_plan accepts UUID for test_plan_id."""
        from uuid import uuid4

        # Create test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_user.py"
        test_file.write_text("def test_user(): pass")

        test_uuid = uuid4()
        manager = LockManager(project_root=tmp_path)
        lock = manager.lock_test_plan(
            test_plan_id=test_uuid,
            test_files=["tests/test_user.py"],
        )

        assert lock.test_plan_id == str(test_uuid)

    def test_get_lock_returns_none_when_no_file(self, tmp_path: Path) -> None:
        """get_lock returns None when no lock file."""
        manager = LockManager(project_root=tmp_path)
        assert manager.get_lock() is None

    def test_get_lock_returns_lock(self, tmp_path: Path) -> None:
        """get_lock returns LockFile when exists."""
        (tmp_path / ".project").mkdir()
        lock_data = {
            "test_plan_id": "test-123",
            "locked_at": "2026-01-10T12:00:00Z",
            "test_files": {"tests/test_user.py": "sha256:abc123"},
        }
        (tmp_path / ".project" / ".lock").write_text(json.dumps(lock_data))

        manager = LockManager(project_root=tmp_path)
        lock = manager.get_lock()
        assert lock is not None
        assert lock.test_plan_id == "test-123"

    def test_verify_lock_no_lock(self, tmp_path: Path) -> None:
        """verify_lock returns valid when no lock file."""
        manager = LockManager(project_root=tmp_path)
        result = manager.verify_lock()
        assert result.is_valid

    def test_verify_lock_unchanged_files(self, tmp_path: Path) -> None:
        """verify_lock passes for unchanged files."""
        # Create test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_user.py"
        test_file.write_text("def test_user(): pass")

        # Create lock
        manager = LockManager(project_root=tmp_path)
        manager.lock_test_plan(
            test_plan_id="test-123",
            test_files=["tests/test_user.py"],
        )

        # Verify
        result = manager.verify_lock()
        assert result.is_valid
        assert result.modified_files == []
        assert result.missing_files == []

    def test_verify_lock_modified_file(self, tmp_path: Path) -> None:
        """verify_lock fails for modified files."""
        # Create test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_user.py"
        test_file.write_text("def test_user(): pass")

        # Create lock
        manager = LockManager(project_root=tmp_path)
        manager.lock_test_plan(
            test_plan_id="test-123",
            test_files=["tests/test_user.py"],
        )

        # Modify file
        test_file.write_text("def test_user_modified(): pass")

        # Verify
        result = manager.verify_lock()
        assert not result.is_valid
        assert "tests/test_user.py" in result.modified_files

    def test_verify_lock_missing_file(self, tmp_path: Path) -> None:
        """verify_lock fails for missing files."""
        # Create test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_user.py"
        test_file.write_text("def test_user(): pass")

        # Create lock
        manager = LockManager(project_root=tmp_path)
        manager.lock_test_plan(
            test_plan_id="test-123",
            test_files=["tests/test_user.py"],
        )

        # Delete file
        test_file.unlink()

        # Verify
        result = manager.verify_lock()
        assert not result.is_valid
        assert "tests/test_user.py" in result.missing_files

    def test_verify_lock_multiple_files(self, tmp_path: Path) -> None:
        """verify_lock handles multiple files."""
        # Create test files
        (tmp_path / "tests").mkdir()
        test1 = tmp_path / "tests" / "test_user.py"
        test2 = tmp_path / "tests" / "test_email.py"
        test1.write_text("def test_user(): pass")
        test2.write_text("def test_email(): pass")

        # Create lock
        manager = LockManager(project_root=tmp_path)
        manager.lock_test_plan(
            test_plan_id="test-123",
            test_files=["tests/test_user.py", "tests/test_email.py"],
        )

        # Modify one file
        test1.write_text("def test_user_modified(): pass")

        # Verify
        result = manager.verify_lock()
        assert not result.is_valid
        assert "tests/test_user.py" in result.modified_files
        assert "tests/test_email.py" not in result.modified_files

    def test_remove_lock(self, tmp_path: Path) -> None:
        """remove_lock removes the lock file."""
        (tmp_path / ".project").mkdir()
        (tmp_path / ".project" / ".lock").write_text("{}")

        manager = LockManager(project_root=tmp_path)
        assert manager.is_locked()

        result = manager.remove_lock()
        assert result is True
        assert not manager.is_locked()

    def test_remove_lock_no_file(self, tmp_path: Path) -> None:
        """remove_lock returns False when no lock file."""
        manager = LockManager(project_root=tmp_path)
        result = manager.remove_lock()
        assert result is False

    def test_lock_creates_project_dir(self, tmp_path: Path) -> None:
        """lock_test_plan creates .project dir if needed."""
        # Create test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_user.py"
        test_file.write_text("def test_user(): pass")

        manager = LockManager(project_root=tmp_path)
        manager.lock_test_plan(
            test_plan_id="test-123",
            test_files=["tests/test_user.py"],
        )

        assert (tmp_path / ".project").exists()
        assert manager.lock_file_path.exists()
