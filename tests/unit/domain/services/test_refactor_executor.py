"""Unit tests for RefactorExecutor."""

from pathlib import Path

from rice_factor.domain.artifacts.payloads.refactor_plan import (
    RefactorOperation,
    RefactorOperationType,
    RefactorPlanPayload,
)
from rice_factor.domain.services.refactor_executor import (
    RefactorDiff,
    RefactorExecutor,
    RefactorResult,
)


class TestRefactorExecutorInitialization:
    """Tests for RefactorExecutor initialization."""

    def test_initialization_with_path(self, tmp_path: Path) -> None:
        """Executor should initialize with project path."""
        executor = RefactorExecutor(project_path=tmp_path)
        assert executor.project_path == tmp_path

    def test_executed_operations_starts_empty(self, tmp_path: Path) -> None:
        """Executed operations should start empty."""
        executor = RefactorExecutor(project_path=tmp_path)
        assert len(executor.executed_operations) == 0


class TestPreview:
    """Tests for preview method."""

    def test_preview_generates_diffs(self, tmp_path: Path) -> None:
        """Preview should generate diffs for all operations."""
        executor = RefactorExecutor(project_path=tmp_path)

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(
                    type=RefactorOperationType.MOVE_FILE,
                    from_path="src/old.py",
                    to_path="src/new.py",
                ),
                RefactorOperation(
                    type=RefactorOperationType.RENAME_SYMBOL,
                    symbol="old_function",
                    from_path="src/module.py",
                    to_path="new_function",
                ),
            ],
        )

        diffs = executor.preview(plan)

        assert len(diffs) == 2
        assert all(isinstance(d, RefactorDiff) for d in diffs)

    def test_preview_move_file(self, tmp_path: Path) -> None:
        """Preview should generate diff for move file operation."""
        executor = RefactorExecutor(project_path=tmp_path)

        plan = RefactorPlanPayload(
            goal="Move file",
            operations=[
                RefactorOperation(
                    type=RefactorOperationType.MOVE_FILE,
                    from_path="src/old.py",
                    to_path="src/new.py",
                ),
            ],
        )

        diffs = executor.preview(plan)

        assert len(diffs) == 1
        assert diffs[0].operation.type == RefactorOperationType.MOVE_FILE
        assert diffs[0].file_path == "src/old.py"

    def test_preview_rename_symbol(self, tmp_path: Path) -> None:
        """Preview should generate diff for rename symbol operation."""
        executor = RefactorExecutor(project_path=tmp_path)

        plan = RefactorPlanPayload(
            goal="Rename symbol",
            operations=[
                RefactorOperation(
                    type=RefactorOperationType.RENAME_SYMBOL,
                    symbol="old_name",
                    from_path="src/module.py",
                    to_path="new_name",
                ),
            ],
        )

        diffs = executor.preview(plan)

        assert len(diffs) == 1
        assert diffs[0].operation.type == RefactorOperationType.RENAME_SYMBOL
        assert "old_name" in diffs[0].before

    def test_preview_extract_interface(self, tmp_path: Path) -> None:
        """Preview should generate diff for extract interface operation."""
        executor = RefactorExecutor(project_path=tmp_path)

        plan = RefactorPlanPayload(
            goal="Extract interface",
            operations=[
                RefactorOperation(
                    type=RefactorOperationType.EXTRACT_INTERFACE,
                    symbol="MyClass",
                    from_path="src/module.py",
                ),
            ],
        )

        diffs = executor.preview(plan)

        assert len(diffs) == 1
        assert diffs[0].operation.type == RefactorOperationType.EXTRACT_INTERFACE
        assert "Protocol" in diffs[0].after

    def test_preview_enforce_dependency(self, tmp_path: Path) -> None:
        """Preview should generate diff for enforce dependency operation."""
        executor = RefactorExecutor(project_path=tmp_path)

        plan = RefactorPlanPayload(
            goal="Enforce dependency",
            operations=[
                RefactorOperation(
                    type=RefactorOperationType.ENFORCE_DEPENDENCY,
                    from_path="src/consumer.py",
                    to_path="src/provider.py",
                ),
            ],
        )

        diffs = executor.preview(plan)

        assert len(diffs) == 1
        assert diffs[0].operation.type == RefactorOperationType.ENFORCE_DEPENDENCY


class TestExecute:
    """Tests for execute method."""

    def test_execute_returns_result(self, tmp_path: Path) -> None:
        """Execute should return RefactorResult."""
        executor = RefactorExecutor(project_path=tmp_path)

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.MOVE_FILE),
            ],
        )

        result = executor.execute(plan)

        assert isinstance(result, RefactorResult)
        assert result.success is True

    def test_execute_tracks_operations(self, tmp_path: Path) -> None:
        """Execute should track executed operations."""
        executor = RefactorExecutor(project_path=tmp_path)

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.MOVE_FILE),
                RefactorOperation(type=RefactorOperationType.RENAME_SYMBOL),
            ],
        )

        executor.execute(plan)

        assert len(executor.executed_operations) == 2

    def test_execute_counts_applied_operations(self, tmp_path: Path) -> None:
        """Execute should count applied operations."""
        executor = RefactorExecutor(project_path=tmp_path)

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.MOVE_FILE),
                RefactorOperation(type=RefactorOperationType.RENAME_SYMBOL),
            ],
        )

        result = executor.execute(plan)

        assert result.operations_applied == 2
        assert result.operations_failed == 0

    def test_execute_includes_diffs(self, tmp_path: Path) -> None:
        """Execute should include diffs in result."""
        executor = RefactorExecutor(project_path=tmp_path)

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.MOVE_FILE),
            ],
        )

        result = executor.execute(plan)

        assert len(result.diffs) == 1


class TestExecuteOperation:
    """Tests for execute_operation method."""

    def test_execute_operation_returns_true(self, tmp_path: Path) -> None:
        """Execute operation should return True for stub."""
        executor = RefactorExecutor(project_path=tmp_path)

        operation = RefactorOperation(type=RefactorOperationType.MOVE_FILE)
        result = executor.execute_operation(operation)

        assert result is True

    def test_execute_operation_tracks_operation(self, tmp_path: Path) -> None:
        """Execute operation should track the operation."""
        executor = RefactorExecutor(project_path=tmp_path)

        operation = RefactorOperation(type=RefactorOperationType.MOVE_FILE)
        executor.execute_operation(operation)

        assert len(executor.executed_operations) == 1
        assert executor.executed_operations[0] == operation


class TestRefactorDiff:
    """Tests for RefactorDiff dataclass."""

    def test_diff_has_required_fields(self) -> None:
        """RefactorDiff should have all required fields."""
        operation = RefactorOperation(type=RefactorOperationType.MOVE_FILE)

        diff = RefactorDiff(
            operation=operation,
            file_path="src/file.py",
            before="old content",
            after="new content",
        )

        assert diff.operation == operation
        assert diff.file_path == "src/file.py"
        assert diff.before == "old content"
        assert diff.after == "new content"
        assert diff.lines_added == 0
        assert diff.lines_removed == 0


class TestRefactorResult:
    """Tests for RefactorResult dataclass."""

    def test_result_has_required_fields(self) -> None:
        """RefactorResult should have all required fields."""
        result = RefactorResult(
            success=True,
            operations_applied=3,
            operations_failed=0,
        )

        assert result.success is True
        assert result.operations_applied == 3
        assert result.operations_failed == 0
        assert result.diffs == []
        assert result.error_message is None

    def test_result_with_error(self) -> None:
        """RefactorResult should support error message."""
        result = RefactorResult(
            success=False,
            operations_applied=1,
            operations_failed=2,
            error_message="Something went wrong",
        )

        assert result.success is False
        assert result.error_message == "Something went wrong"
