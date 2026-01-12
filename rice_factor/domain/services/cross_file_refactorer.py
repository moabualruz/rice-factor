"""Cross-file refactoring service with atomic operations and rollback support.

This module provides the CrossFileRefactorer that enables atomic multi-file
transformations with transaction-like rollback capabilities.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4


class OperationType(Enum):
    """Type of file operation."""

    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"
    MOVE = "move"


class TransactionState(Enum):
    """State of a transaction."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class FileOperation:
    """A single file operation within a transaction.

    Attributes:
        id: Unique operation ID.
        type: Type of operation.
        target_path: Target file path.
        source_path: Source path (for rename/move).
        content: New content (for create/modify).
        original_content: Original content (for rollback).
        backup_path: Path to backup file.
        completed: Whether operation completed.
    """

    id: str
    type: OperationType
    target_path: Path
    source_path: Path | None = None
    content: str | None = None
    original_content: str | None = None
    backup_path: Path | None = None
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "target_path": str(self.target_path),
            "source_path": str(self.source_path) if self.source_path else None,
            "completed": self.completed,
        }


@dataclass
class OperationResult:
    """Result of a single operation.

    Attributes:
        operation_id: ID of the operation.
        success: Whether operation succeeded.
        error: Error message if failed.
    """

    operation_id: str
    success: bool
    error: str | None = None


@dataclass
class Transaction:
    """A transaction containing multiple file operations.

    Attributes:
        id: Unique transaction ID.
        operations: List of file operations.
        state: Current transaction state.
        backup_dir: Directory for backups.
        created_at: When transaction was created.
        completed_at: When transaction completed.
    """

    id: str
    operations: list[FileOperation] = field(default_factory=list)
    state: TransactionState = TransactionState.PENDING
    backup_dir: Path | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "operations": [op.to_dict() for op in self.operations],
            "state": self.state.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


@dataclass
class TransactionResult:
    """Result of a transaction execution.

    Attributes:
        transaction_id: ID of the transaction.
        success: Whether transaction succeeded.
        operations_completed: Number of operations completed.
        operations_total: Total number of operations.
        results: Results of individual operations.
        error: Error message if failed.
        rolled_back: Whether transaction was rolled back.
    """

    transaction_id: str
    success: bool
    operations_completed: int = 0
    operations_total: int = 0
    results: list[OperationResult] = field(default_factory=list)
    error: str | None = None
    rolled_back: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "success": self.success,
            "operations_completed": self.operations_completed,
            "operations_total": self.operations_total,
            "error": self.error,
            "rolled_back": self.rolled_back,
        }


@dataclass
class CrossFileRefactorer:
    """Service for atomic multi-file refactoring operations.

    Provides transaction-like semantics with rollback support for
    multi-file transformations.

    Attributes:
        repo_root: Root directory of the repository.
        backup_root: Root directory for backups.
    """

    repo_root: Path
    backup_root: Path | None = None
    _active_transactions: dict[str, Transaction] = field(
        default_factory=dict, init=False
    )

    def __post_init__(self) -> None:
        """Initialize backup directory."""
        if self.backup_root is None:
            self.backup_root = self.repo_root / ".refactor_backups"

    def begin_transaction(self) -> Transaction:
        """Begin a new transaction.

        Returns:
            New Transaction object.
        """
        txn_id = str(uuid4())[:8]
        backup_dir = self.backup_root / txn_id

        transaction = Transaction(
            id=txn_id,
            backup_dir=backup_dir,
            created_at=datetime.now(UTC),
        )

        self._active_transactions[txn_id] = transaction
        return transaction

    def add_create(
        self,
        transaction: Transaction,
        target_path: Path,
        content: str,
    ) -> FileOperation:
        """Add a create operation to the transaction.

        Args:
            transaction: Transaction to add to.
            target_path: Path to create.
            content: Content to write.

        Returns:
            FileOperation object.
        """
        op = FileOperation(
            id=str(uuid4())[:8],
            type=OperationType.CREATE,
            target_path=target_path,
            content=content,
        )
        transaction.operations.append(op)
        return op

    def add_modify(
        self,
        transaction: Transaction,
        target_path: Path,
        content: str,
    ) -> FileOperation:
        """Add a modify operation to the transaction.

        Args:
            transaction: Transaction to add to.
            target_path: Path to modify.
            content: New content.

        Returns:
            FileOperation object.
        """
        op = FileOperation(
            id=str(uuid4())[:8],
            type=OperationType.MODIFY,
            target_path=target_path,
            content=content,
        )
        transaction.operations.append(op)
        return op

    def add_delete(
        self,
        transaction: Transaction,
        target_path: Path,
    ) -> FileOperation:
        """Add a delete operation to the transaction.

        Args:
            transaction: Transaction to add to.
            target_path: Path to delete.

        Returns:
            FileOperation object.
        """
        op = FileOperation(
            id=str(uuid4())[:8],
            type=OperationType.DELETE,
            target_path=target_path,
        )
        transaction.operations.append(op)
        return op

    def add_rename(
        self,
        transaction: Transaction,
        source_path: Path,
        target_path: Path,
    ) -> FileOperation:
        """Add a rename operation to the transaction.

        Args:
            transaction: Transaction to add to.
            source_path: Original path.
            target_path: New path.

        Returns:
            FileOperation object.
        """
        op = FileOperation(
            id=str(uuid4())[:8],
            type=OperationType.RENAME,
            target_path=target_path,
            source_path=source_path,
        )
        transaction.operations.append(op)
        return op

    def add_move(
        self,
        transaction: Transaction,
        source_path: Path,
        target_path: Path,
    ) -> FileOperation:
        """Add a move operation to the transaction.

        Args:
            transaction: Transaction to add to.
            source_path: Original path.
            target_path: New path.

        Returns:
            FileOperation object.
        """
        op = FileOperation(
            id=str(uuid4())[:8],
            type=OperationType.MOVE,
            target_path=target_path,
            source_path=source_path,
        )
        transaction.operations.append(op)
        return op

    def commit(self, transaction: Transaction) -> TransactionResult:
        """Commit a transaction, executing all operations.

        If any operation fails, all completed operations are rolled back.

        Args:
            transaction: Transaction to commit.

        Returns:
            TransactionResult with execution details.
        """
        if transaction.state != TransactionState.PENDING:
            return TransactionResult(
                transaction_id=transaction.id,
                success=False,
                error=f"Transaction in invalid state: {transaction.state.value}",
            )

        transaction.state = TransactionState.IN_PROGRESS
        results: list[OperationResult] = []
        completed_ops: list[FileOperation] = []

        # Create backup directory
        if transaction.backup_dir:
            transaction.backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            for op in transaction.operations:
                result = self._execute_operation(op, transaction)
                results.append(result)

                if result.success:
                    op.completed = True
                    completed_ops.append(op)
                else:
                    # Rollback completed operations
                    self._rollback_operations(completed_ops, transaction)
                    transaction.state = TransactionState.FAILED

                    return TransactionResult(
                        transaction_id=transaction.id,
                        success=False,
                        operations_completed=len(completed_ops),
                        operations_total=len(transaction.operations),
                        results=results,
                        error=result.error,
                        rolled_back=True,
                    )

            transaction.state = TransactionState.COMMITTED
            transaction.completed_at = datetime.now(UTC)

            # Clean up backups on successful commit
            if transaction.backup_dir and transaction.backup_dir.exists():
                shutil.rmtree(transaction.backup_dir)

            return TransactionResult(
                transaction_id=transaction.id,
                success=True,
                operations_completed=len(completed_ops),
                operations_total=len(transaction.operations),
                results=results,
            )

        except Exception as e:
            # Emergency rollback
            self._rollback_operations(completed_ops, transaction)
            transaction.state = TransactionState.FAILED

            return TransactionResult(
                transaction_id=transaction.id,
                success=False,
                operations_completed=len(completed_ops),
                operations_total=len(transaction.operations),
                results=results,
                error=str(e),
                rolled_back=True,
            )

    def _execute_operation(
        self,
        op: FileOperation,
        transaction: Transaction,
    ) -> OperationResult:
        """Execute a single file operation.

        Args:
            op: Operation to execute.
            transaction: Parent transaction.

        Returns:
            OperationResult.
        """
        try:
            if op.type == OperationType.CREATE:
                return self._execute_create(op, transaction)
            elif op.type == OperationType.MODIFY:
                return self._execute_modify(op, transaction)
            elif op.type == OperationType.DELETE:
                return self._execute_delete(op, transaction)
            elif op.type == OperationType.RENAME:
                return self._execute_rename(op, transaction)
            elif op.type == OperationType.MOVE:
                return self._execute_move(op, transaction)
            else:
                return OperationResult(
                    operation_id=op.id,
                    success=False,
                    error=f"Unknown operation type: {op.type}",
                )
        except Exception as e:
            return OperationResult(
                operation_id=op.id,
                success=False,
                error=str(e),
            )

    def _execute_create(
        self,
        op: FileOperation,
        transaction: Transaction,
    ) -> OperationResult:
        """Execute create operation."""
        if op.target_path.exists():
            return OperationResult(
                operation_id=op.id,
                success=False,
                error=f"File already exists: {op.target_path}",
            )

        op.target_path.parent.mkdir(parents=True, exist_ok=True)
        op.target_path.write_text(op.content or "", encoding="utf-8")

        return OperationResult(operation_id=op.id, success=True)

    def _execute_modify(
        self,
        op: FileOperation,
        transaction: Transaction,
    ) -> OperationResult:
        """Execute modify operation."""
        if not op.target_path.exists():
            return OperationResult(
                operation_id=op.id,
                success=False,
                error=f"File does not exist: {op.target_path}",
            )

        # Backup original content
        op.original_content = op.target_path.read_text(encoding="utf-8")

        if transaction.backup_dir:
            backup_path = transaction.backup_dir / f"{op.id}_{op.target_path.name}"
            backup_path.write_text(op.original_content, encoding="utf-8")
            op.backup_path = backup_path

        # Write new content
        op.target_path.write_text(op.content or "", encoding="utf-8")

        return OperationResult(operation_id=op.id, success=True)

    def _execute_delete(
        self,
        op: FileOperation,
        transaction: Transaction,
    ) -> OperationResult:
        """Execute delete operation."""
        if not op.target_path.exists():
            return OperationResult(
                operation_id=op.id,
                success=False,
                error=f"File does not exist: {op.target_path}",
            )

        # Backup before delete
        op.original_content = op.target_path.read_text(encoding="utf-8")

        if transaction.backup_dir:
            backup_path = transaction.backup_dir / f"{op.id}_{op.target_path.name}"
            backup_path.write_text(op.original_content, encoding="utf-8")
            op.backup_path = backup_path

        op.target_path.unlink()

        return OperationResult(operation_id=op.id, success=True)

    def _execute_rename(
        self,
        op: FileOperation,
        transaction: Transaction,
    ) -> OperationResult:
        """Execute rename operation."""
        if not op.source_path or not op.source_path.exists():
            return OperationResult(
                operation_id=op.id,
                success=False,
                error=f"Source file does not exist: {op.source_path}",
            )

        if op.target_path.exists():
            return OperationResult(
                operation_id=op.id,
                success=False,
                error=f"Target file already exists: {op.target_path}",
            )

        op.source_path.rename(op.target_path)

        return OperationResult(operation_id=op.id, success=True)

    def _execute_move(
        self,
        op: FileOperation,
        transaction: Transaction,
    ) -> OperationResult:
        """Execute move operation."""
        if not op.source_path or not op.source_path.exists():
            return OperationResult(
                operation_id=op.id,
                success=False,
                error=f"Source file does not exist: {op.source_path}",
            )

        op.target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(op.source_path), str(op.target_path))

        return OperationResult(operation_id=op.id, success=True)

    def _rollback_operations(
        self,
        operations: list[FileOperation],
        transaction: Transaction,
    ) -> None:
        """Rollback completed operations.

        Args:
            operations: Operations to rollback.
            transaction: Parent transaction.
        """
        # Rollback in reverse order
        for op in reversed(operations):
            try:
                if op.type == OperationType.CREATE:
                    if op.target_path.exists():
                        op.target_path.unlink()

                elif op.type == OperationType.MODIFY:
                    if op.original_content is not None:
                        op.target_path.write_text(
                            op.original_content, encoding="utf-8"
                        )

                elif op.type == OperationType.DELETE:
                    if op.original_content is not None:
                        op.target_path.write_text(
                            op.original_content, encoding="utf-8"
                        )

                elif op.type == OperationType.RENAME:
                    if op.source_path and op.target_path.exists():
                        op.target_path.rename(op.source_path)

                elif op.type == OperationType.MOVE:
                    if op.source_path and op.target_path.exists():
                        shutil.move(str(op.target_path), str(op.source_path))

            except Exception:
                # Log but continue with rollback
                pass

    def rollback(self, transaction: Transaction) -> TransactionResult:
        """Manually rollback a transaction.

        Args:
            transaction: Transaction to rollback.

        Returns:
            TransactionResult.
        """
        if transaction.state == TransactionState.ROLLED_BACK:
            return TransactionResult(
                transaction_id=transaction.id,
                success=True,
                error="Transaction already rolled back",
            )

        completed_ops = [op for op in transaction.operations if op.completed]
        self._rollback_operations(completed_ops, transaction)
        transaction.state = TransactionState.ROLLED_BACK

        return TransactionResult(
            transaction_id=transaction.id,
            success=True,
            rolled_back=True,
        )

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        """Get a transaction by ID.

        Args:
            transaction_id: Transaction ID.

        Returns:
            Transaction or None if not found.
        """
        return self._active_transactions.get(transaction_id)

    def refactor_with_callback(
        self,
        files: list[Path],
        transform: Callable[[Path, str], str],
    ) -> TransactionResult:
        """Refactor multiple files using a callback function.

        Args:
            files: List of files to transform.
            transform: Function taking (path, content) and returning new content.

        Returns:
            TransactionResult.
        """
        transaction = self.begin_transaction()

        for file_path in files:
            if file_path.exists():
                original_content = file_path.read_text(encoding="utf-8")
                new_content = transform(file_path, original_content)

                if new_content != original_content:
                    self.add_modify(transaction, file_path, new_content)

        return self.commit(transaction)

    def rename_symbol_across_files(
        self,
        files: list[Path],
        old_name: str,
        new_name: str,
    ) -> TransactionResult:
        """Rename a symbol across multiple files.

        Args:
            files: Files to search.
            old_name: Old symbol name.
            new_name: New symbol name.

        Returns:
            TransactionResult.
        """

        def transform(path: Path, content: str) -> str:
            import re

            # Use word boundaries to avoid partial matches
            pattern = r"\b" + re.escape(old_name) + r"\b"
            return re.sub(pattern, new_name, content)

        return self.refactor_with_callback(files, transform)

    def move_class_to_file(
        self,
        source_file: Path,
        class_name: str,
        target_file: Path,
    ) -> TransactionResult:
        """Move a class definition to a new file.

        Args:
            source_file: Source file containing the class.
            class_name: Name of the class to move.
            target_file: Target file to create.

        Returns:
            TransactionResult.
        """
        import ast

        if not source_file.exists():
            return TransactionResult(
                transaction_id="none",
                success=False,
                error=f"Source file does not exist: {source_file}",
            )

        source_content = source_file.read_text(encoding="utf-8")

        try:
            tree = ast.parse(source_content)
        except SyntaxError as e:
            return TransactionResult(
                transaction_id="none",
                success=False,
                error=f"Syntax error in source file: {e}",
            )

        # Find the class definition
        class_node = None
        class_start = 0
        class_end = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_node = node
                class_start = node.lineno - 1  # 0-indexed
                class_end = node.end_lineno or node.lineno
                break

        if class_node is None:
            return TransactionResult(
                transaction_id="none",
                success=False,
                error=f"Class '{class_name}' not found in {source_file}",
            )

        # Extract class code
        lines = source_content.split("\n")
        class_lines = lines[class_start:class_end]
        class_code = "\n".join(class_lines)

        # Create new source without the class
        new_source_lines = lines[:class_start] + lines[class_end:]
        new_source = "\n".join(new_source_lines)

        # Build transaction
        transaction = self.begin_transaction()
        self.add_modify(transaction, source_file, new_source)
        self.add_create(transaction, target_file, class_code)

        return self.commit(transaction)
