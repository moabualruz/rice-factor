"""Unit tests for ParallelExecutor service."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

import pytest

from rice_factor.domain.services.parallel_executor import (
    BatchExecutionResult,
    ExecutionResult,
    ExecutionStatus,
    ExecutionTask,
    ParallelExecutor,
    ParallelismConfig,
    create_executor,
)


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """All expected statuses should exist."""
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.COMPLETED.value == "completed"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.CANCELLED.value == "cancelled"


class TestExecutionTask:
    """Tests for ExecutionTask dataclass."""

    def test_creation(self) -> None:
        """ExecutionTask should be creatable."""
        task = ExecutionTask(
            task_id="task-1",
            artifact_id="artifact-1",
            artifact_type="ImplementationPlan",
            payload={"file": "test.py"},
        )
        assert task.task_id == "task-1"
        assert task.artifact_id == "artifact-1"
        assert task.priority == 0

    def test_with_priority(self) -> None:
        """should accept priority."""
        task = ExecutionTask(
            task_id="t1",
            artifact_id="a1",
            artifact_type="TestPlan",
            payload={},
            priority=5,
        )
        assert task.priority == 5


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_creation(self) -> None:
        """ExecutionResult should be creatable."""
        result = ExecutionResult(
            task_id="task-1",
            artifact_id="artifact-1",
            status=ExecutionStatus.COMPLETED,
            result={"output": "success"},
        )
        assert result.task_id == "task-1"
        assert result.status == ExecutionStatus.COMPLETED

    def test_with_error(self) -> None:
        """should include error details."""
        result = ExecutionResult(
            task_id="task-1",
            artifact_id="artifact-1",
            status=ExecutionStatus.FAILED,
            error="Something went wrong",
        )
        assert result.error is not None
        assert "wrong" in result.error.lower()

    def test_duration_ms(self) -> None:
        """should calculate duration."""
        now = datetime.now(UTC)
        later = datetime.now(UTC)
        result = ExecutionResult(
            task_id="t1",
            artifact_id="a1",
            status=ExecutionStatus.COMPLETED,
            started_at=now,
            completed_at=later,
        )
        assert result.duration_ms is not None
        assert result.duration_ms >= 0

    def test_duration_ms_none_when_incomplete(self) -> None:
        """should return None when no timestamps."""
        result = ExecutionResult(
            task_id="t1",
            artifact_id="a1",
            status=ExecutionStatus.PENDING,
        )
        assert result.duration_ms is None

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        result = ExecutionResult(
            task_id="task-1",
            artifact_id="artifact-1",
            status=ExecutionStatus.COMPLETED,
            result={"data": "test"},
            started_at=now,
            completed_at=now,
        )
        data = result.to_dict()
        assert data["task_id"] == "task-1"
        assert data["status"] == "completed"
        assert data["result"] == {"data": "test"}


class TestBatchExecutionResult:
    """Tests for BatchExecutionResult dataclass."""

    def test_creation(self) -> None:
        """BatchExecutionResult should be creatable."""
        now = datetime.now(UTC)
        result = BatchExecutionResult(
            total_tasks=10,
            completed_count=8,
            failed_count=2,
            cancelled_count=0,
            results=[],
            started_at=now,
            completed_at=now,
        )
        assert result.total_tasks == 10
        assert result.success_rate == 80.0

    def test_success_rate_zero_total(self) -> None:
        """should handle zero total tasks."""
        now = datetime.now(UTC)
        result = BatchExecutionResult(
            total_tasks=0,
            completed_count=0,
            failed_count=0,
            cancelled_count=0,
            results=[],
            started_at=now,
        )
        assert result.success_rate == 100.0

    def test_all_succeeded(self) -> None:
        """should detect all succeeded."""
        now = datetime.now(UTC)
        result = BatchExecutionResult(
            total_tasks=5,
            completed_count=5,
            failed_count=0,
            cancelled_count=0,
            results=[],
            started_at=now,
        )
        assert result.all_succeeded is True

    def test_not_all_succeeded_failures(self) -> None:
        """should detect failures."""
        now = datetime.now(UTC)
        result = BatchExecutionResult(
            total_tasks=5,
            completed_count=4,
            failed_count=1,
            cancelled_count=0,
            results=[],
            started_at=now,
        )
        assert result.all_succeeded is False

    def test_not_all_succeeded_cancellations(self) -> None:
        """should detect cancellations."""
        now = datetime.now(UTC)
        result = BatchExecutionResult(
            total_tasks=5,
            completed_count=4,
            failed_count=0,
            cancelled_count=1,
            results=[],
            started_at=now,
        )
        assert result.all_succeeded is False

    def test_duration_ms(self) -> None:
        """should calculate duration."""
        now = datetime.now(UTC)
        result = BatchExecutionResult(
            total_tasks=1,
            completed_count=1,
            failed_count=0,
            cancelled_count=0,
            results=[],
            started_at=now,
            completed_at=now,
        )
        assert result.duration_ms is not None

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        result = BatchExecutionResult(
            total_tasks=3,
            completed_count=3,
            failed_count=0,
            cancelled_count=0,
            results=[],
            started_at=now,
            completed_at=now,
        )
        data = result.to_dict()
        assert data["total_tasks"] == 3
        assert data["success_rate"] == 100.0


class TestParallelismConfig:
    """Tests for ParallelismConfig dataclass."""

    def test_defaults(self) -> None:
        """should have sensible defaults."""
        config = ParallelismConfig()
        assert config.max_workers == 4
        assert config.timeout_seconds == 300.0
        assert config.fail_fast is False
        assert config.ordered_results is False

    def test_custom_values(self) -> None:
        """should accept custom values."""
        config = ParallelismConfig(
            max_workers=8,
            timeout_seconds=60.0,
            fail_fast=True,
            ordered_results=True,
        )
        assert config.max_workers == 8
        assert config.fail_fast is True


class TestParallelExecutor:
    """Tests for ParallelExecutor service."""

    def test_creation(self) -> None:
        """ParallelExecutor should be creatable."""
        executor = ParallelExecutor()
        assert executor.max_workers == 4

    def test_custom_config(self) -> None:
        """should accept custom config."""
        config = ParallelismConfig(max_workers=2)
        executor = ParallelExecutor(config=config)
        assert executor.max_workers == 2

    def test_set_max_workers(self) -> None:
        """should allow setting max workers."""
        executor = ParallelExecutor()
        executor.max_workers = 8
        assert executor.max_workers == 8

    def test_set_max_workers_invalid(self) -> None:
        """should reject invalid max workers."""
        executor = ParallelExecutor()
        with pytest.raises(ValueError):
            executor.max_workers = 0

    def test_execute_empty_tasks(self) -> None:
        """should handle empty task list."""
        executor = ParallelExecutor()
        result = executor.execute_sync([], lambda t: None)
        assert result.total_tasks == 0
        assert result.all_succeeded is True

    def test_execute_single_task(self) -> None:
        """should execute a single task."""
        executor = ParallelExecutor()
        task = ExecutionTask(
            task_id="t1",
            artifact_id="a1",
            artifact_type="Test",
            payload={"value": 42},
        )

        def handler(t: ExecutionTask) -> str:
            return f"processed-{t.task_id}"

        result = executor.execute_sync([task], handler)
        assert result.total_tasks == 1
        assert result.completed_count == 1
        assert result.results[0].result == "processed-t1"

    def test_execute_multiple_tasks(self) -> None:
        """should execute multiple tasks in parallel."""
        executor = ParallelExecutor(
            config=ParallelismConfig(max_workers=4)
        )
        tasks = [
            ExecutionTask(
                task_id=f"t{i}",
                artifact_id=f"a{i}",
                artifact_type="Test",
                payload={},
            )
            for i in range(5)
        ]

        results_collected: list[str] = []

        def handler(t: ExecutionTask) -> str:
            results_collected.append(t.task_id)
            return f"done-{t.task_id}"

        result = executor.execute_sync(tasks, handler)
        assert result.total_tasks == 5
        assert result.completed_count == 5
        assert len(results_collected) == 5

    def test_execute_with_priority(self) -> None:
        """should respect task priority."""
        executor = ParallelExecutor(
            config=ParallelismConfig(max_workers=1, ordered_results=True)
        )
        tasks = [
            ExecutionTask(
                task_id="low",
                artifact_id="a1",
                artifact_type="Test",
                payload={},
                priority=10,
            ),
            ExecutionTask(
                task_id="high",
                artifact_id="a2",
                artifact_type="Test",
                payload={},
                priority=1,
            ),
            ExecutionTask(
                task_id="medium",
                artifact_id="a3",
                artifact_type="Test",
                payload={},
                priority=5,
            ),
        ]

        execution_order: list[str] = []

        def handler(t: ExecutionTask) -> str:
            execution_order.append(t.task_id)
            return t.task_id

        result = executor.execute_sync(tasks, handler)
        assert result.completed_count == 3
        # With max_workers=1, tasks execute in priority order
        assert execution_order[0] == "high"

    def test_execute_with_failure(self) -> None:
        """should handle task failures."""
        executor = ParallelExecutor()
        task = ExecutionTask(
            task_id="fail",
            artifact_id="a1",
            artifact_type="Test",
            payload={},
        )

        def handler(t: ExecutionTask) -> None:
            raise ValueError("intentional error")

        result = executor.execute_sync([task], handler)
        assert result.failed_count == 1
        assert result.results[0].status == ExecutionStatus.FAILED
        assert "intentional" in result.results[0].error

    def test_execute_fail_fast(self) -> None:
        """should stop on first failure when fail_fast is True."""
        executor = ParallelExecutor(
            config=ParallelismConfig(max_workers=1, fail_fast=True)
        )
        tasks = [
            ExecutionTask(
                task_id=f"t{i}",
                artifact_id=f"a{i}",
                artifact_type="Test",
                payload={},
                priority=i,
            )
            for i in range(5)
        ]

        call_count = 0

        def handler(t: ExecutionTask) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("fail on second")
            return "ok"

        result = executor.execute_sync(tasks, handler)
        # Should have at least one failure and some cancelled
        assert result.failed_count >= 1

    def test_cancel(self) -> None:
        """should cancel execution."""
        executor = ParallelExecutor()
        executor.cancel()
        assert executor._cancelled is True


class TestParallelExecutorAsync:
    """Tests for async execution."""

    @pytest.mark.asyncio
    async def test_execute_async_empty(self) -> None:
        """should handle empty async execution."""
        executor = ParallelExecutor()
        result = await executor.execute_async([], lambda t: None)
        assert result.total_tasks == 0

    @pytest.mark.asyncio
    async def test_execute_async_single(self) -> None:
        """should execute single task async."""
        executor = ParallelExecutor()
        task = ExecutionTask(
            task_id="t1",
            artifact_id="a1",
            artifact_type="Test",
            payload={},
        )

        def handler(t: ExecutionTask) -> str:
            return "async-done"

        result = await executor.execute_async([task], handler)
        assert result.completed_count == 1
        assert result.results[0].result == "async-done"

    @pytest.mark.asyncio
    async def test_execute_async_concurrent(self) -> None:
        """should execute tasks concurrently."""
        executor = ParallelExecutor(
            config=ParallelismConfig(max_workers=3)
        )
        tasks = [
            ExecutionTask(
                task_id=f"t{i}",
                artifact_id=f"a{i}",
                artifact_type="Test",
                payload={},
            )
            for i in range(5)
        ]

        def handler(t: ExecutionTask) -> str:
            time.sleep(0.01)  # Small delay
            return f"done-{t.task_id}"

        result = await executor.execute_async(tasks, handler)
        assert result.completed_count == 5

    @pytest.mark.asyncio
    async def test_execute_async_with_failure(self) -> None:
        """should handle async failures."""
        executor = ParallelExecutor()
        task = ExecutionTask(
            task_id="fail",
            artifact_id="a1",
            artifact_type="Test",
            payload={},
        )

        def handler(t: ExecutionTask) -> None:
            raise RuntimeError("async failure")

        result = await executor.execute_async([task], handler)
        assert result.failed_count == 1


class TestCreateExecutor:
    """Tests for create_executor factory."""

    def test_create_default(self) -> None:
        """should create with defaults."""
        executor = create_executor()
        assert executor.max_workers == 4
        assert executor.config.fail_fast is False

    def test_create_custom(self) -> None:
        """should create with custom values."""
        executor = create_executor(
            max_workers=8,
            timeout_seconds=60.0,
            fail_fast=True,
        )
        assert executor.max_workers == 8
        assert executor.config.timeout_seconds == 60.0
        assert executor.config.fail_fast is True
