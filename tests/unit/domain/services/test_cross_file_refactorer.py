"""Tests for CrossFileRefactorer."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rice_factor.domain.services.cross_file_refactorer import (
    CrossFileRefactorer,
    FileOperation,
    OperationResult,
    OperationType,
    Transaction,
    TransactionResult,
    TransactionState,
)

if TYPE_CHECKING:
    pass


class TestOperationType:
    """Tests for OperationType enum."""

    def test_all_types_exist(self) -> None:
        """Test all operation types are defined."""
        assert OperationType.CREATE
        assert OperationType.MODIFY
        assert OperationType.DELETE
        assert OperationType.RENAME
        assert OperationType.MOVE


class TestTransactionState:
    """Tests for TransactionState enum."""

    def test_all_states_exist(self) -> None:
        """Test all transaction states are defined."""
        assert TransactionState.PENDING
        assert TransactionState.IN_PROGRESS
        assert TransactionState.COMMITTED
        assert TransactionState.ROLLED_BACK
        assert TransactionState.FAILED


class TestFileOperation:
    """Tests for FileOperation model."""

    def test_creation(self) -> None:
        """Test operation creation."""
        op = FileOperation(
            id="op1",
            type=OperationType.CREATE,
            target_path=Path("/test/file.py"),
        )
        assert op.id == "op1"
        assert op.type == OperationType.CREATE
        assert op.completed is False

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        op = FileOperation(
            id="op1",
            type=OperationType.RENAME,
            target_path=Path("/test/new.py"),
            source_path=Path("/test/old.py"),
            completed=True,
        )
        d = op.to_dict()
        assert d["id"] == "op1"
        assert d["type"] == "rename"
        assert d["completed"] is True


class TestOperationResult:
    """Tests for OperationResult model."""

    def test_creation_success(self) -> None:
        """Test successful result."""
        result = OperationResult(operation_id="op1", success=True)
        assert result.success is True
        assert result.error is None

    def test_creation_failure(self) -> None:
        """Test failed result."""
        result = OperationResult(
            operation_id="op1", success=False, error="File not found"
        )
        assert result.success is False
        assert result.error == "File not found"


class TestTransaction:
    """Tests for Transaction model."""

    def test_creation(self) -> None:
        """Test transaction creation."""
        txn = Transaction(id="txn1")
        assert txn.id == "txn1"
        assert txn.state == TransactionState.PENDING
        assert txn.operations == []

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        txn = Transaction(
            id="txn1",
            state=TransactionState.COMMITTED,
        )
        d = txn.to_dict()
        assert d["id"] == "txn1"
        assert d["state"] == "committed"


class TestTransactionResult:
    """Tests for TransactionResult model."""

    def test_creation_success(self) -> None:
        """Test successful result."""
        result = TransactionResult(
            transaction_id="txn1",
            success=True,
            operations_completed=3,
            operations_total=3,
        )
        assert result.success is True
        assert result.operations_completed == 3

    def test_creation_failure(self) -> None:
        """Test failed result."""
        result = TransactionResult(
            transaction_id="txn1",
            success=False,
            error="Operation failed",
            rolled_back=True,
        )
        assert result.success is False
        assert result.rolled_back is True

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        result = TransactionResult(
            transaction_id="txn1",
            success=True,
            operations_completed=2,
            operations_total=2,
        )
        d = result.to_dict()
        assert d["transaction_id"] == "txn1"
        assert d["success"] is True


class TestCrossFileRefactorer:
    """Tests for CrossFileRefactorer."""

    def test_creation(self, tmp_path: Path) -> None:
        """Test refactorer creation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        assert refactorer.repo_root == tmp_path
        assert refactorer.backup_root == tmp_path / ".refactor_backups"

    def test_begin_transaction(self, tmp_path: Path) -> None:
        """Test beginning a transaction."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        assert txn.id is not None
        assert txn.state == TransactionState.PENDING
        assert txn.created_at is not None

    def test_add_create(self, tmp_path: Path) -> None:
        """Test adding create operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        op = refactorer.add_create(txn, tmp_path / "new.py", "content")

        assert op.type == OperationType.CREATE
        assert op.content == "content"
        assert len(txn.operations) == 1

    def test_add_modify(self, tmp_path: Path) -> None:
        """Test adding modify operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        op = refactorer.add_modify(txn, tmp_path / "existing.py", "new content")

        assert op.type == OperationType.MODIFY
        assert len(txn.operations) == 1

    def test_add_delete(self, tmp_path: Path) -> None:
        """Test adding delete operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        op = refactorer.add_delete(txn, tmp_path / "to_delete.py")

        assert op.type == OperationType.DELETE
        assert len(txn.operations) == 1

    def test_add_rename(self, tmp_path: Path) -> None:
        """Test adding rename operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        op = refactorer.add_rename(
            txn, tmp_path / "old.py", tmp_path / "new.py"
        )

        assert op.type == OperationType.RENAME
        assert op.source_path == tmp_path / "old.py"
        assert len(txn.operations) == 1

    def test_add_move(self, tmp_path: Path) -> None:
        """Test adding move operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        op = refactorer.add_move(
            txn, tmp_path / "old.py", tmp_path / "subdir" / "old.py"
        )

        assert op.type == OperationType.MOVE
        assert len(txn.operations) == 1

    def test_commit_create(self, tmp_path: Path) -> None:
        """Test committing a create operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        target = tmp_path / "new_file.py"
        refactorer.add_create(txn, target, "# New file content")

        result = refactorer.commit(txn)

        assert result.success is True
        assert target.exists()
        assert target.read_text() == "# New file content"

    def test_commit_modify(self, tmp_path: Path) -> None:
        """Test committing a modify operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        # Create existing file
        target = tmp_path / "existing.py"
        target.write_text("# Original content")

        txn = refactorer.begin_transaction()
        refactorer.add_modify(txn, target, "# Modified content")

        result = refactorer.commit(txn)

        assert result.success is True
        assert target.read_text() == "# Modified content"

    def test_commit_delete(self, tmp_path: Path) -> None:
        """Test committing a delete operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        # Create file to delete
        target = tmp_path / "to_delete.py"
        target.write_text("# To be deleted")

        txn = refactorer.begin_transaction()
        refactorer.add_delete(txn, target)

        result = refactorer.commit(txn)

        assert result.success is True
        assert not target.exists()

    def test_commit_rename(self, tmp_path: Path) -> None:
        """Test committing a rename operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        # Create source file
        source = tmp_path / "old_name.py"
        source.write_text("# Content")
        target = tmp_path / "new_name.py"

        txn = refactorer.begin_transaction()
        refactorer.add_rename(txn, source, target)

        result = refactorer.commit(txn)

        assert result.success is True
        assert not source.exists()
        assert target.exists()

    def test_commit_move(self, tmp_path: Path) -> None:
        """Test committing a move operation."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        # Create source file
        source = tmp_path / "file.py"
        source.write_text("# Content")
        subdir = tmp_path / "subdir"
        target = subdir / "file.py"

        txn = refactorer.begin_transaction()
        refactorer.add_move(txn, source, target)

        result = refactorer.commit(txn)

        assert result.success is True
        assert not source.exists()
        assert target.exists()

    def test_commit_multiple_operations(self, tmp_path: Path) -> None:
        """Test committing multiple operations."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        # Create existing file
        existing = tmp_path / "existing.py"
        existing.write_text("# Original")

        txn = refactorer.begin_transaction()
        refactorer.add_create(txn, tmp_path / "new1.py", "# New 1")
        refactorer.add_create(txn, tmp_path / "new2.py", "# New 2")
        refactorer.add_modify(txn, existing, "# Modified")

        result = refactorer.commit(txn)

        assert result.success is True
        assert result.operations_completed == 3
        assert (tmp_path / "new1.py").exists()
        assert (tmp_path / "new2.py").exists()
        assert existing.read_text() == "# Modified"

    def test_rollback_on_failure(self, tmp_path: Path) -> None:
        """Test automatic rollback on failure."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        # Create a file to modify
        existing = tmp_path / "existing.py"
        existing.write_text("# Original content")

        txn = refactorer.begin_transaction()
        refactorer.add_modify(txn, existing, "# Modified content")
        # This should fail because file doesn't exist
        refactorer.add_modify(txn, tmp_path / "nonexistent.py", "content")

        result = refactorer.commit(txn)

        assert result.success is False
        assert result.rolled_back is True
        # First file should be rolled back to original
        assert existing.read_text() == "# Original content"

    def test_manual_rollback(self, tmp_path: Path) -> None:
        """Test manual rollback."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        target = tmp_path / "file.py"
        refactorer.add_create(txn, target, "content")

        # Commit first
        refactorer.commit(txn)
        assert target.exists()

        # Manual rollback
        result = refactorer.rollback(txn)
        assert result.rolled_back is True

    def test_commit_invalid_state(self, tmp_path: Path) -> None:
        """Test committing transaction in invalid state."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()
        txn.state = TransactionState.COMMITTED  # Force invalid state

        result = refactorer.commit(txn)

        assert result.success is False
        assert "invalid state" in result.error

    def test_get_transaction(self, tmp_path: Path) -> None:
        """Test getting transaction by ID."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        retrieved = refactorer.get_transaction(txn.id)
        assert retrieved is not None
        assert retrieved.id == txn.id

    def test_get_transaction_not_found(self, tmp_path: Path) -> None:
        """Test getting non-existent transaction."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        retrieved = refactorer.get_transaction("nonexistent")
        assert retrieved is None

    def test_refactor_with_callback(self, tmp_path: Path) -> None:
        """Test refactoring with callback function."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        # Create test files
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("old_name = 1")
        file2.write_text("old_name = 2")

        def transform(path: Path, content: str) -> str:
            return content.replace("old_name", "new_name")

        result = refactorer.refactor_with_callback([file1, file2], transform)

        assert result.success is True
        assert "new_name" in file1.read_text()
        assert "new_name" in file2.read_text()

    def test_refactor_with_callback_no_changes(self, tmp_path: Path) -> None:
        """Test refactoring with callback when no changes needed."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        file1 = tmp_path / "file1.py"
        file1.write_text("content")

        def transform(path: Path, content: str) -> str:
            return content  # No change

        result = refactorer.refactor_with_callback([file1], transform)

        assert result.success is True
        assert result.operations_completed == 0

    def test_rename_symbol_across_files(self, tmp_path: Path) -> None:
        """Test renaming symbol across multiple files."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("def old_func():\n    pass\n")
        file2.write_text("from file1 import old_func\n")

        result = refactorer.rename_symbol_across_files(
            [file1, file2], "old_func", "new_func"
        )

        assert result.success is True
        assert "new_func" in file1.read_text()
        assert "new_func" in file2.read_text()
        assert "old_func" not in file1.read_text()
        assert "old_func" not in file2.read_text()

    def test_move_class_to_file(self, tmp_path: Path) -> None:
        """Test moving a class to a new file."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        source = tmp_path / "source.py"
        source.write_text(
            "class MyClass:\n"
            "    def method(self):\n"
            "        pass\n"
            "\n"
            "other_code = 1\n"
        )
        target = tmp_path / "target.py"

        result = refactorer.move_class_to_file(source, "MyClass", target)

        assert result.success is True
        assert target.exists()
        assert "class MyClass" in target.read_text()
        assert "other_code" in source.read_text()

    def test_move_class_not_found(self, tmp_path: Path) -> None:
        """Test moving non-existent class."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        source = tmp_path / "source.py"
        source.write_text("x = 1\n")
        target = tmp_path / "target.py"

        result = refactorer.move_class_to_file(source, "NonExistent", target)

        assert result.success is False
        assert "not found" in result.error

    def test_move_class_source_not_exists(self, tmp_path: Path) -> None:
        """Test moving class from non-existent file."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        result = refactorer.move_class_to_file(
            tmp_path / "nonexistent.py", "MyClass", tmp_path / "target.py"
        )

        assert result.success is False
        assert "does not exist" in result.error

    def test_create_fails_if_exists(self, tmp_path: Path) -> None:
        """Test create fails if file already exists."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        target = tmp_path / "existing.py"
        target.write_text("content")

        txn = refactorer.begin_transaction()
        refactorer.add_create(txn, target, "new content")

        result = refactorer.commit(txn)

        assert result.success is False
        assert "already exists" in result.results[0].error

    def test_modify_fails_if_not_exists(self, tmp_path: Path) -> None:
        """Test modify fails if file doesn't exist."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        txn = refactorer.begin_transaction()
        refactorer.add_modify(txn, tmp_path / "nonexistent.py", "content")

        result = refactorer.commit(txn)

        assert result.success is False
        assert "does not exist" in result.results[0].error

    def test_delete_fails_if_not_exists(self, tmp_path: Path) -> None:
        """Test delete fails if file doesn't exist."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        txn = refactorer.begin_transaction()
        refactorer.add_delete(txn, tmp_path / "nonexistent.py")

        result = refactorer.commit(txn)

        assert result.success is False
        assert "does not exist" in result.results[0].error

    def test_rename_fails_if_target_exists(self, tmp_path: Path) -> None:
        """Test rename fails if target already exists."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)

        source = tmp_path / "source.py"
        target = tmp_path / "target.py"
        source.write_text("source")
        target.write_text("target")

        txn = refactorer.begin_transaction()
        refactorer.add_rename(txn, source, target)

        result = refactorer.commit(txn)

        assert result.success is False
        assert "already exists" in result.results[0].error

    def test_transaction_completed_timestamp(self, tmp_path: Path) -> None:
        """Test transaction completed timestamp is set."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        refactorer.add_create(txn, tmp_path / "file.py", "content")
        refactorer.commit(txn)

        assert txn.completed_at is not None

    def test_backup_cleanup_on_success(self, tmp_path: Path) -> None:
        """Test backup directory is cleaned up on successful commit."""
        refactorer = CrossFileRefactorer(repo_root=tmp_path)
        txn = refactorer.begin_transaction()

        refactorer.add_create(txn, tmp_path / "file.py", "content")
        refactorer.commit(txn)

        # Backup directory should not exist after successful commit
        assert not txn.backup_dir.exists()
