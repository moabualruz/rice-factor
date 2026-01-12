"""Parallel executor service for concurrent artifact processing.

This module provides the ParallelExecutor service that executes multiple
implementation plans or other artifact operations in parallel using
configurable worker pools.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class ExecutionStatus(Enum):
    """Status of an execution task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionTask:
    """A task to be executed in parallel.

    Attributes:
        task_id: Unique identifier for the task.
        artifact_id: ID of the artifact being processed.
        artifact_type: Type of the artifact.
        payload: Data to be processed.
        priority: Task priority (lower = higher priority).
    """

    task_id: str
    artifact_id: str
    artifact_type: str
    payload: dict[str, Any]
    priority: int = 0


@dataclass
class ExecutionResult:
    """Result of a single execution task.

    Attributes:
        task_id: ID of the task.
        artifact_id: ID of the artifact.
        status: Execution status.
        result: Output from execution.
        error: Error message if failed.
        started_at: When execution started.
        completed_at: When execution finished.
        duration_ms: Execution duration in milliseconds.
    """

    task_id: str
    artifact_id: str
    status: ExecutionStatus
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def duration_ms(self) -> float | None:
        """Get execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "artifact_id": self.artifact_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
        }


@dataclass
class BatchExecutionResult:
    """Result of a batch parallel execution.

    Attributes:
        total_tasks: Total number of tasks.
        completed_count: Number of completed tasks.
        failed_count: Number of failed tasks.
        cancelled_count: Number of cancelled tasks.
        results: Individual task results.
        started_at: When batch started.
        completed_at: When batch finished.
    """

    total_tasks: int
    completed_count: int
    failed_count: int
    cancelled_count: int
    results: list[ExecutionResult]
    started_at: datetime
    completed_at: datetime | None = None

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_tasks == 0:
            return 100.0
        return (self.completed_count / self.total_tasks) * 100

    @property
    def all_succeeded(self) -> bool:
        """Check if all tasks succeeded."""
        return self.failed_count == 0 and self.cancelled_count == 0

    @property
    def duration_ms(self) -> float | None:
        """Get batch duration in milliseconds."""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_tasks": self.total_tasks,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "cancelled_count": self.cancelled_count,
            "success_rate": round(self.success_rate, 2),
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_ms": self.duration_ms,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class ParallelismConfig:
    """Configuration for parallel execution.

    Attributes:
        max_workers: Maximum number of parallel workers.
        timeout_seconds: Timeout for each task in seconds.
        fail_fast: Stop all tasks on first failure.
        ordered_results: Return results in task order.
    """

    max_workers: int = 4
    timeout_seconds: float = 300.0
    fail_fast: bool = False
    ordered_results: bool = False


@dataclass
class ParallelExecutor:
    """Service for parallel artifact execution.

    This service manages a worker pool for executing multiple artifact
    operations concurrently with configurable parallelism levels.

    Attributes:
        config: Parallelism configuration.
    """

    config: ParallelismConfig = field(default_factory=ParallelismConfig)
    _executor: ThreadPoolExecutor | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the executor."""
        self._cancelled = False

    def execute_sync(
        self,
        tasks: list[ExecutionTask],
        handler: Callable[[ExecutionTask], Any],
    ) -> BatchExecutionResult:
        """Execute tasks synchronously using thread pool.

        Args:
            tasks: List of tasks to execute.
            handler: Function to call for each task.

        Returns:
            BatchExecutionResult with all results.
        """
        started_at = datetime.now(UTC)
        results: list[ExecutionResult] = []
        completed_count = 0
        failed_count = 0
        cancelled_count = 0
        self._cancelled = False

        if not tasks:
            return BatchExecutionResult(
                total_tasks=0,
                completed_count=0,
                failed_count=0,
                cancelled_count=0,
                results=[],
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

        # Sort by priority (lower = higher priority)
        sorted_tasks = sorted(tasks, key=lambda t: t.priority)

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_task = {
                executor.submit(self._execute_task, task, handler): task
                for task in sorted_tasks
            }

            for future in as_completed(future_to_task):
                if self._cancelled:
                    cancelled_count += 1
                    task = future_to_task[future]
                    results.append(
                        ExecutionResult(
                            task_id=task.task_id,
                            artifact_id=task.artifact_id,
                            status=ExecutionStatus.CANCELLED,
                        )
                    )
                    continue

                result = future.result()
                results.append(result)

                if result.status == ExecutionStatus.COMPLETED:
                    completed_count += 1
                elif result.status == ExecutionStatus.FAILED:
                    failed_count += 1
                    if self.config.fail_fast:
                        self._cancelled = True

        # Cancel remaining futures if fail_fast triggered
        if self._cancelled:
            for future in future_to_task:
                if not future.done():
                    future.cancel()
                    cancelled_count += 1
                    task = future_to_task[future]
                    results.append(
                        ExecutionResult(
                            task_id=task.task_id,
                            artifact_id=task.artifact_id,
                            status=ExecutionStatus.CANCELLED,
                        )
                    )

        # Sort by original order if requested
        if self.config.ordered_results:
            task_order = {t.task_id: i for i, t in enumerate(sorted_tasks)}
            results.sort(key=lambda r: task_order.get(r.task_id, 0))

        return BatchExecutionResult(
            total_tasks=len(tasks),
            completed_count=completed_count,
            failed_count=failed_count,
            cancelled_count=cancelled_count,
            results=results,
            started_at=started_at,
            completed_at=datetime.now(UTC),
        )

    async def execute_async(
        self,
        tasks: list[ExecutionTask],
        handler: Callable[[ExecutionTask], Any],
    ) -> BatchExecutionResult:
        """Execute tasks asynchronously.

        Args:
            tasks: List of tasks to execute.
            handler: Function to call for each task.

        Returns:
            BatchExecutionResult with all results.
        """
        started_at = datetime.now(UTC)
        results: list[ExecutionResult] = []
        completed_count = 0
        failed_count = 0
        cancelled_count = 0
        self._cancelled = False

        if not tasks:
            return BatchExecutionResult(
                total_tasks=0,
                completed_count=0,
                failed_count=0,
                cancelled_count=0,
                results=[],
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority)

        # Create semaphore for concurrency limiting
        semaphore = asyncio.Semaphore(self.config.max_workers)

        async def run_task(task: ExecutionTask) -> ExecutionResult:
            async with semaphore:
                if self._cancelled:
                    return ExecutionResult(
                        task_id=task.task_id,
                        artifact_id=task.artifact_id,
                        status=ExecutionStatus.CANCELLED,
                    )
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._execute_task, task, handler
                )

        # Execute all tasks concurrently
        task_futures = [run_task(task) for task in sorted_tasks]
        async_results = await asyncio.gather(*task_futures, return_exceptions=True)

        for i, result_or_exc in enumerate(async_results):
            if isinstance(result_or_exc, Exception):
                task = sorted_tasks[i]
                result = ExecutionResult(
                    task_id=task.task_id,
                    artifact_id=task.artifact_id,
                    status=ExecutionStatus.FAILED,
                    error=str(result_or_exc),
                )
                failed_count += 1
            else:
                result = result_or_exc
                if result.status == ExecutionStatus.COMPLETED:
                    completed_count += 1
                elif result.status == ExecutionStatus.FAILED:
                    failed_count += 1
                    if self.config.fail_fast:
                        self._cancelled = True
                elif result.status == ExecutionStatus.CANCELLED:
                    cancelled_count += 1

            results.append(result)

        if self.config.ordered_results:
            task_order = {t.task_id: i for i, t in enumerate(sorted_tasks)}
            results.sort(key=lambda r: task_order.get(r.task_id, 0))

        return BatchExecutionResult(
            total_tasks=len(tasks),
            completed_count=completed_count,
            failed_count=failed_count,
            cancelled_count=cancelled_count,
            results=results,
            started_at=started_at,
            completed_at=datetime.now(UTC),
        )

    def _execute_task(
        self,
        task: ExecutionTask,
        handler: Callable[[ExecutionTask], Any],
    ) -> ExecutionResult:
        """Execute a single task.

        Args:
            task: Task to execute.
            handler: Handler function.

        Returns:
            ExecutionResult for the task.
        """
        started_at = datetime.now(UTC)

        try:
            result = handler(task)
            return ExecutionResult(
                task_id=task.task_id,
                artifact_id=task.artifact_id,
                status=ExecutionStatus.COMPLETED,
                result=result,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )
        except Exception as e:
            return ExecutionResult(
                task_id=task.task_id,
                artifact_id=task.artifact_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

    def cancel(self) -> None:
        """Cancel all running and pending tasks."""
        self._cancelled = True

    @property
    def max_workers(self) -> int:
        """Get maximum number of workers."""
        return self.config.max_workers

    @max_workers.setter
    def max_workers(self, value: int) -> None:
        """Set maximum number of workers."""
        if value < 1:
            raise ValueError("max_workers must be at least 1")
        self.config.max_workers = value


def create_executor(
    max_workers: int = 4,
    timeout_seconds: float = 300.0,
    fail_fast: bool = False,
) -> ParallelExecutor:
    """Create a ParallelExecutor with configuration.

    Args:
        max_workers: Maximum parallel workers.
        timeout_seconds: Task timeout.
        fail_fast: Stop on first failure.

    Returns:
        Configured ParallelExecutor.
    """
    return ParallelExecutor(
        config=ParallelismConfig(
            max_workers=max_workers,
            timeout_seconds=timeout_seconds,
            fail_fast=fail_fast,
        )
    )
