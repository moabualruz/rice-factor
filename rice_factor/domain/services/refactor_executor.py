"""Refactor executor service (stub implementation).

This service executes refactoring operations defined in a RefactorPlan.
Currently a stub that simulates execution for testing purposes.
"""

from dataclasses import dataclass, field
from pathlib import Path

from rice_factor.domain.artifacts.payloads.refactor_plan import (
    RefactorOperation,
    RefactorOperationType,
    RefactorPlanPayload,
)


@dataclass
class RefactorDiff:
    """Represents a diff for a refactor operation.

    Attributes:
        operation: The refactor operation.
        file_path: The file path affected.
        before: Content before the change.
        after: Content after the change.
        lines_added: Number of lines added.
        lines_removed: Number of lines removed.
    """

    operation: RefactorOperation
    file_path: str
    before: str
    after: str
    lines_added: int = 0
    lines_removed: int = 0


@dataclass
class RefactorResult:
    """Result of a refactor execution.

    Attributes:
        success: Whether the execution succeeded.
        operations_applied: Number of operations applied.
        operations_failed: Number of operations that failed.
        diffs: List of diffs generated.
        error_message: Error message if failed.
    """

    success: bool
    operations_applied: int = 0
    operations_failed: int = 0
    diffs: list[RefactorDiff] = field(default_factory=list)
    error_message: str | None = None


class RefactorExecutor:
    """Executor for refactoring operations.

    This is a stub implementation that simulates refactoring
    for testing purposes. Real implementation would integrate
    with language-specific tooling.
    """

    def __init__(self, project_path: Path) -> None:
        """Initialize the refactor executor.

        Args:
            project_path: Path to the project root.
        """
        self._project_path = project_path
        self._executed_operations: list[RefactorOperation] = []

    @property
    def project_path(self) -> Path:
        """Get the project path."""
        return self._project_path

    @property
    def executed_operations(self) -> list[RefactorOperation]:
        """Get the list of executed operations (for testing)."""
        return self._executed_operations.copy()

    def preview(self, plan: RefactorPlanPayload) -> list[RefactorDiff]:
        """Generate preview diffs for a refactor plan.

        This generates diffs showing what would change without
        actually modifying any files.

        Args:
            plan: The refactor plan to preview.

        Returns:
            List of diffs for each operation.
        """
        diffs = []

        for operation in plan.operations:
            diff = self._preview_operation(operation)
            if diff:
                diffs.append(diff)

        return diffs

    def _preview_operation(self, operation: RefactorOperation) -> RefactorDiff | None:
        """Generate a preview diff for a single operation.

        Args:
            operation: The operation to preview.

        Returns:
            A diff for the operation, or None if not applicable.
        """
        if operation.type == RefactorOperationType.MOVE_FILE:
            return self._preview_move_file(operation)
        elif operation.type == RefactorOperationType.RENAME_SYMBOL:
            return self._preview_rename_symbol(operation)
        elif operation.type == RefactorOperationType.EXTRACT_INTERFACE:
            return self._preview_extract_interface(operation)
        elif operation.type == RefactorOperationType.ENFORCE_DEPENDENCY:
            return self._preview_enforce_dependency(operation)

        return None

    def _preview_move_file(self, operation: RefactorOperation) -> RefactorDiff:
        """Preview a file move operation."""
        from_path = operation.from_path or "unknown"
        to_path = operation.to_path or "unknown"

        return RefactorDiff(
            operation=operation,
            file_path=from_path,
            before=f"# File at {from_path}",
            after=f"# File moved to {to_path}",
            lines_added=0,
            lines_removed=0,
        )

    def _preview_rename_symbol(self, operation: RefactorOperation) -> RefactorDiff:
        """Preview a symbol rename operation."""
        symbol = operation.symbol or "unknown"
        file_path = operation.from_path or "unknown"

        return RefactorDiff(
            operation=operation,
            file_path=file_path,
            before=f"def {symbol}():",
            after=f"def {operation.to_path or 'new_name'}():  # renamed from {symbol}",
            lines_added=0,
            lines_removed=0,
        )

    def _preview_extract_interface(self, operation: RefactorOperation) -> RefactorDiff:
        """Preview an interface extraction operation."""
        symbol = operation.symbol or "unknown"
        file_path = operation.from_path or "unknown"

        return RefactorDiff(
            operation=operation,
            file_path=file_path,
            before=f"class {symbol}:\n    def method(self): ...",
            after=f"class {symbol}Protocol(Protocol):\n    def method(self): ...\n\nclass {symbol}({symbol}Protocol):\n    def method(self): ...",
            lines_added=3,
            lines_removed=0,
        )

    def _preview_enforce_dependency(self, operation: RefactorOperation) -> RefactorDiff:
        """Preview a dependency enforcement operation."""
        from_path = operation.from_path or "unknown"
        to_path = operation.to_path or "unknown"

        return RefactorDiff(
            operation=operation,
            file_path=from_path,
            before=f"# Direct import from {to_path}",
            after="# Import via dependency injection",
            lines_added=2,
            lines_removed=1,
        )

    def execute(self, plan: RefactorPlanPayload) -> RefactorResult:
        """Execute a refactor plan (stub implementation).

        This is a stub that simulates execution without actually
        modifying any files.

        Args:
            plan: The refactor plan to execute.

        Returns:
            Result of the execution.
        """
        diffs = []
        operations_applied = 0

        for operation in plan.operations:
            diff = self._preview_operation(operation)
            if diff:
                diffs.append(diff)
                operations_applied += 1
                self._executed_operations.append(operation)

        return RefactorResult(
            success=True,
            operations_applied=operations_applied,
            operations_failed=0,
            diffs=diffs,
        )

    def execute_operation(self, operation: RefactorOperation) -> bool:
        """Execute a single refactor operation (stub).

        Args:
            operation: The operation to execute.

        Returns:
            True if successful, False otherwise.
        """
        self._executed_operations.append(operation)
        return True
