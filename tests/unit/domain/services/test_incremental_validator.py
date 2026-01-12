"""Unit tests for IncrementalValidator service."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from rice_factor.domain.services.incremental_validator import (
    ChangeType,
    FileChange,
    HashRecord,
    IncrementalValidator,
    ValidationResult,
)


class TestChangeType:
    """Tests for ChangeType enum."""

    def test_all_types_exist(self) -> None:
        """All expected types should exist."""
        assert ChangeType.ADDED.value == "added"
        assert ChangeType.MODIFIED.value == "modified"
        assert ChangeType.DELETED.value == "deleted"
        assert ChangeType.UNCHANGED.value == "unchanged"


class TestFileChange:
    """Tests for FileChange dataclass."""

    def test_creation(self) -> None:
        """FileChange should be creatable."""
        change = FileChange(
            path="src/main.py",
            change_type=ChangeType.MODIFIED,
            old_hash="abc123",
            new_hash="def456",
        )
        assert change.path == "src/main.py"
        assert change.change_type == ChangeType.MODIFIED

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        change = FileChange(
            path="test.py",
            change_type=ChangeType.ADDED,
            new_hash="hash123",
        )
        data = change.to_dict()
        assert data["path"] == "test.py"
        assert data["change_type"] == "added"


class TestHashRecord:
    """Tests for HashRecord dataclass."""

    def test_creation(self) -> None:
        """HashRecord should be creatable."""
        now = datetime.now(UTC)
        record = HashRecord(
            path="file.py",
            hash="abc123",
            size=100,
            modified_at=1234567890.0,
            recorded_at=now,
        )
        assert record.path == "file.py"
        assert record.hash == "abc123"

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        record = HashRecord(
            path="file.py",
            hash="hash",
            size=50,
            modified_at=1000.0,
            recorded_at=now,
        )
        data = record.to_dict()
        assert data["path"] == "file.py"
        assert data["size"] == 50

    def test_from_dict(self) -> None:
        """should deserialize from dictionary."""
        now = datetime.now(UTC)
        data = {
            "path": "test.py",
            "hash": "abc",
            "size": 100,
            "modified_at": 1234.0,
            "recorded_at": now.isoformat(),
        }
        record = HashRecord.from_dict(data)
        assert record.path == "test.py"
        assert record.hash == "abc"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_creation(self) -> None:
        """ValidationResult should be creatable."""
        now = datetime.now(UTC)
        result = ValidationResult(
            total_files=10,
            changed_count=3,
            unchanged_count=7,
            changes=[],
            validated_at=now,
        )
        assert result.total_files == 10
        assert result.has_changes is True

    def test_has_changes_false(self) -> None:
        """should detect no changes."""
        now = datetime.now(UTC)
        result = ValidationResult(
            total_files=5,
            changed_count=0,
            unchanged_count=5,
            changes=[],
            validated_at=now,
        )
        assert result.has_changes is False

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        result = ValidationResult(
            total_files=3,
            changed_count=1,
            unchanged_count=2,
            changes=[],
            validated_at=now,
        )
        data = result.to_dict()
        assert data["total_files"] == 3
        assert data["has_changes"] is True


class TestIncrementalValidator:
    """Tests for IncrementalValidator service."""

    def test_creation(self, tmp_path: Path) -> None:
        """IncrementalValidator should be creatable."""
        validator = IncrementalValidator(repo_root=tmp_path)
        assert validator.repo_root == tmp_path

    def test_custom_store_path(self, tmp_path: Path) -> None:
        """should accept custom store path."""
        store = tmp_path / "custom" / "hashes.json"
        validator = IncrementalValidator(
            repo_root=tmp_path,
            hash_store_path=store,
        )
        assert validator.hash_store_path == store

    def test_compute_hash(self, tmp_path: Path) -> None:
        """should compute consistent hash."""
        validator = IncrementalValidator(repo_root=tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        hash1 = validator.compute_hash(test_file)
        hash2 = validator.compute_hash(test_file)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_compute_hash_different_content(self, tmp_path: Path) -> None:
        """should compute different hashes for different content."""
        validator = IncrementalValidator(repo_root=tmp_path)

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        hash1 = validator.compute_hash(file1)
        hash2 = validator.compute_hash(file2)
        assert hash1 != hash2

    def test_check_file_new(self, tmp_path: Path) -> None:
        """should detect new file."""
        validator = IncrementalValidator(repo_root=tmp_path)

        new_file = tmp_path / "new.txt"
        new_file.write_text("new content")

        change = validator.check_file(new_file)
        assert change.change_type == ChangeType.ADDED
        assert change.new_hash is not None

    def test_check_file_unchanged(self, tmp_path: Path) -> None:
        """should detect unchanged file."""
        validator = IncrementalValidator(repo_root=tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # First check - adds record
        validator.validate([test_file])

        # Second check - unchanged
        change = validator.check_file(test_file)
        assert change.change_type == ChangeType.UNCHANGED

    def test_check_file_modified(self, tmp_path: Path) -> None:
        """should detect modified file."""
        validator = IncrementalValidator(repo_root=tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("original")

        # First validation
        validator.validate([test_file])

        # Modify file
        test_file.write_text("modified")

        # Check for modification
        change = validator.check_file(test_file)
        assert change.change_type == ChangeType.MODIFIED
        assert change.old_hash != change.new_hash

    def test_check_file_deleted(self, tmp_path: Path) -> None:
        """should detect deleted file."""
        validator = IncrementalValidator(repo_root=tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # First validation
        validator.validate([test_file])

        # Delete file
        test_file.unlink()

        # Check for deletion
        change = validator.check_file(test_file)
        assert change.change_type == ChangeType.DELETED
        assert change.old_hash is not None
        assert change.new_hash is None

    def test_validate_multiple_files(self, tmp_path: Path) -> None:
        """should validate multiple files."""
        validator = IncrementalValidator(repo_root=tmp_path)

        files = []
        for i in range(5):
            f = tmp_path / f"file{i}.txt"
            f.write_text(f"content {i}")
            files.append(f)

        result = validator.validate(files)
        assert result.total_files == 5
        assert result.changed_count == 5  # All new
        assert result.unchanged_count == 0

    def test_validate_updates_records(self, tmp_path: Path) -> None:
        """should update records after validation."""
        validator = IncrementalValidator(repo_root=tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # First validation
        result1 = validator.validate([test_file])
        assert result1.changed_count == 1

        # Second validation - no changes
        result2 = validator.validate([test_file])
        assert result2.changed_count == 0
        assert result2.unchanged_count == 1

    def test_validate_without_update(self, tmp_path: Path) -> None:
        """should not update records when requested."""
        validator = IncrementalValidator(repo_root=tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # Validate without updating
        result1 = validator.validate([test_file], update_records=False)
        assert result1.changed_count == 1

        # Should still be new
        result2 = validator.validate([test_file], update_records=False)
        assert result2.changed_count == 1

    def test_validate_directory(self, tmp_path: Path) -> None:
        """should validate entire directory."""
        validator = IncrementalValidator(repo_root=tmp_path)

        # Create directory structure
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "a.py").write_text("a")
        (subdir / "b.py").write_text("b")
        (tmp_path / "c.py").write_text("c")

        result = validator.validate_directory(subdir, pattern="*.py")
        assert result.total_files == 2

    def test_validate_directory_recursive(self, tmp_path: Path) -> None:
        """should validate recursively."""
        validator = IncrementalValidator(repo_root=tmp_path)

        # Create nested structure
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("nested")
        (tmp_path / "a" / "file.txt").write_text("level 1")

        result = validator.validate_directory(
            tmp_path / "a", pattern="*.txt", recursive=True
        )
        assert result.total_files == 2

    def test_get_changed_files(self, tmp_path: Path) -> None:
        """should return only changed files."""
        validator = IncrementalValidator(repo_root=tmp_path)

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        # Validate first file only
        validator.validate([file1])

        # Check both - file2 should be changed
        changed = validator.get_changed_files([file1, file2])
        assert len(changed) == 1
        assert changed[0] == file2

    def test_invalidate(self, tmp_path: Path) -> None:
        """should invalidate a record."""
        validator = IncrementalValidator(repo_root=tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        validator.validate([test_file])
        assert validator.get_record("test.txt") is not None

        result = validator.invalidate("test.txt")
        assert result is True
        assert validator.get_record("test.txt") is None

    def test_invalidate_nonexistent(self, tmp_path: Path) -> None:
        """should return False for nonexistent record."""
        validator = IncrementalValidator(repo_root=tmp_path)
        result = validator.invalidate("nonexistent.txt")
        assert result is False

    def test_invalidate_with_path(self, tmp_path: Path) -> None:
        """should invalidate using Path object."""
        validator = IncrementalValidator(repo_root=tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        validator.validate([test_file])

        result = validator.invalidate(test_file)
        assert result is True

    def test_invalidate_all(self, tmp_path: Path) -> None:
        """should invalidate all records."""
        validator = IncrementalValidator(repo_root=tmp_path)

        for i in range(3):
            f = tmp_path / f"file{i}.txt"
            f.write_text(f"content {i}")
            validator.validate([f])

        count = validator.invalidate_all()
        assert count == 3
        assert len(validator.get_all_records()) == 0

    def test_get_record(self, tmp_path: Path) -> None:
        """should get a specific record."""
        validator = IncrementalValidator(repo_root=tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        validator.validate([test_file])

        record = validator.get_record("test.txt")
        assert record is not None
        assert record.path == "test.txt"

    def test_get_all_records(self, tmp_path: Path) -> None:
        """should get all records."""
        validator = IncrementalValidator(repo_root=tmp_path)

        for i in range(3):
            f = tmp_path / f"file{i}.txt"
            f.write_text(f"content {i}")
            validator.validate([f])

        records = validator.get_all_records()
        assert len(records) == 3

    def test_persistence(self, tmp_path: Path) -> None:
        """should persist records across instances."""
        store = tmp_path / ".rice_factor" / "hashes.json"

        # First validator
        validator1 = IncrementalValidator(
            repo_root=tmp_path,
            hash_store_path=store,
        )
        test_file = tmp_path / "test.txt"
        test_file.write_text("persistent")
        validator1.validate([test_file])

        # Second validator - should load records
        validator2 = IncrementalValidator(
            repo_root=tmp_path,
            hash_store_path=store,
        )
        record = validator2.get_record("test.txt")
        assert record is not None

        # File should be unchanged
        result = validator2.validate([test_file])
        assert result.unchanged_count == 1
