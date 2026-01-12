"""Batch processor service for multi-artifact operations.

This module provides the BatchProcessor service that handles batch
approval, rejection, and processing of multiple artifacts with
transaction support and rollback capability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from rice_factor.domain.artifacts.envelope import ArtifactStatus


class BatchOperationType(Enum):
    """Type of batch operation."""

    APPROVE = "approve"
    REJECT = "reject"
    LOCK = "lock"
    TRANSITION = "transition"


class BatchResultStatus(Enum):
    """Status of a batch operation result."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class BatchOperation:
    """A batch operation to be executed.

    Attributes:
        operation_type: Type of operation.
        artifact_ids: IDs of artifacts to process.
        options: Operation-specific options.
    """

    operation_type: BatchOperationType
    artifact_ids: list[str]
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArtifactResult:
    """Result for a single artifact in a batch.

    Attributes:
        artifact_id: ID of the artifact.
        success: Whether operation succeeded.
        error: Error message if failed.
        old_status: Status before operation.
        new_status: Status after operation.
    """

    artifact_id: str
    success: bool
    error: str | None = None
    old_status: str | None = None
    new_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "success": self.success,
            "error": self.error,
            "old_status": self.old_status,
            "new_status": self.new_status,
        }


@dataclass
class BatchResult:
    """Result of a batch operation.

    Attributes:
        operation_type: Type of operation executed.
        status: Overall batch status.
        total_count: Total artifacts processed.
        success_count: Number of successes.
        failure_count: Number of failures.
        results: Individual artifact results.
        started_at: When batch started.
        completed_at: When batch finished.
    """

    operation_type: BatchOperationType
    status: BatchResultStatus
    total_count: int
    success_count: int
    failure_count: int
    results: list[ArtifactResult]
    started_at: datetime
    completed_at: datetime | None = None

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_count == 0:
            return 100.0
        return (self.success_count / self.total_count) * 100

    @property
    def all_succeeded(self) -> bool:
        """Check if all operations succeeded."""
        return self.failure_count == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_type": self.operation_type.value,
            "status": self.status.value,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_rate, 2),
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class BatchProcessor:
    """Service for batch artifact operations.

    Handles batch approval, rejection, and processing of multiple
    artifacts with transaction support and rollback capability.

    Attributes:
        repo_root: Root directory of the repository.
        artifact_service: Optional artifact service for operations.
    """

    repo_root: Path
    artifact_service: Any = None
    _rollback_stack: list[Callable[[], None]] = field(
        default_factory=list, init=False, repr=False
    )

    def approve_batch(
        self,
        artifact_ids: list[str],
        approver: str = "batch",
        reason: str | None = None,
        validate_all: bool = True,
    ) -> BatchResult:
        """Approve multiple artifacts in a batch.

        Args:
            artifact_ids: IDs of artifacts to approve.
            approver: Name of approver.
            reason: Reason for approval.
            validate_all: Validate all before approving any.

        Returns:
            BatchResult with details.
        """
        started_at = datetime.now(UTC)
        self._rollback_stack.clear()
        results: list[ArtifactResult] = []

        if not artifact_ids:
            return BatchResult(
                operation_type=BatchOperationType.APPROVE,
                status=BatchResultStatus.SUCCESS,
                total_count=0,
                success_count=0,
                failure_count=0,
                results=[],
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

        # Pre-validation if requested
        if validate_all:
            for artifact_id in artifact_ids:
                if not self._can_approve(artifact_id):
                    return BatchResult(
                        operation_type=BatchOperationType.APPROVE,
                        status=BatchResultStatus.FAILED,
                        total_count=len(artifact_ids),
                        success_count=0,
                        failure_count=len(artifact_ids),
                        results=[
                            ArtifactResult(
                                artifact_id=aid,
                                success=False,
                                error="Pre-validation failed",
                            )
                            for aid in artifact_ids
                        ],
                        started_at=started_at,
                        completed_at=datetime.now(UTC),
                    )

        success_count = 0
        failure_count = 0

        for artifact_id in artifact_ids:
            try:
                old_status = self._get_artifact_status(artifact_id)
                self._approve_artifact(artifact_id, approver, reason)
                new_status = self._get_artifact_status(artifact_id)

                results.append(
                    ArtifactResult(
                        artifact_id=artifact_id,
                        success=True,
                        old_status=old_status,
                        new_status=new_status,
                    )
                )
                success_count += 1

                # Add rollback action
                self._rollback_stack.append(
                    lambda aid=artifact_id, old=old_status: self._rollback_status(
                        aid, old
                    )
                )

            except Exception as e:
                results.append(
                    ArtifactResult(
                        artifact_id=artifact_id,
                        success=False,
                        error=str(e),
                    )
                )
                failure_count += 1

        status = (
            BatchResultStatus.SUCCESS
            if failure_count == 0
            else (
                BatchResultStatus.PARTIAL
                if success_count > 0
                else BatchResultStatus.FAILED
            )
        )

        return BatchResult(
            operation_type=BatchOperationType.APPROVE,
            status=status,
            total_count=len(artifact_ids),
            success_count=success_count,
            failure_count=failure_count,
            results=results,
            started_at=started_at,
            completed_at=datetime.now(UTC),
        )

    def reject_batch(
        self,
        artifact_ids: list[str],
        reason: str,
        individual_reasons: dict[str, str] | None = None,
    ) -> BatchResult:
        """Reject multiple artifacts in a batch.

        Args:
            artifact_ids: IDs of artifacts to reject.
            reason: Shared reason for rejection.
            individual_reasons: Per-artifact reasons (overrides shared).

        Returns:
            BatchResult with details.
        """
        started_at = datetime.now(UTC)
        self._rollback_stack.clear()
        results: list[ArtifactResult] = []
        success_count = 0
        failure_count = 0

        for artifact_id in artifact_ids:
            try:
                artifact_reason = (
                    individual_reasons.get(artifact_id, reason)
                    if individual_reasons
                    else reason
                )
                old_status = self._get_artifact_status(artifact_id)
                self._reject_artifact(artifact_id, artifact_reason)
                new_status = self._get_artifact_status(artifact_id)

                results.append(
                    ArtifactResult(
                        artifact_id=artifact_id,
                        success=True,
                        old_status=old_status,
                        new_status=new_status,
                    )
                )
                success_count += 1

            except Exception as e:
                results.append(
                    ArtifactResult(
                        artifact_id=artifact_id,
                        success=False,
                        error=str(e),
                    )
                )
                failure_count += 1

        status = (
            BatchResultStatus.SUCCESS
            if failure_count == 0
            else (
                BatchResultStatus.PARTIAL
                if success_count > 0
                else BatchResultStatus.FAILED
            )
        )

        return BatchResult(
            operation_type=BatchOperationType.REJECT,
            status=status,
            total_count=len(artifact_ids),
            success_count=success_count,
            failure_count=failure_count,
            results=results,
            started_at=started_at,
            completed_at=datetime.now(UTC),
        )

    def execute(self, operation: BatchOperation) -> BatchResult:
        """Execute a batch operation.

        Args:
            operation: BatchOperation to execute.

        Returns:
            BatchResult with details.
        """
        if operation.operation_type == BatchOperationType.APPROVE:
            return self.approve_batch(
                operation.artifact_ids,
                approver=operation.options.get("approver", "batch"),
                reason=operation.options.get("reason"),
                validate_all=operation.options.get("validate_all", True),
            )
        elif operation.operation_type == BatchOperationType.REJECT:
            return self.reject_batch(
                operation.artifact_ids,
                reason=operation.options.get("reason", "Batch rejection"),
                individual_reasons=operation.options.get("individual_reasons"),
            )
        else:
            return BatchResult(
                operation_type=operation.operation_type,
                status=BatchResultStatus.FAILED,
                total_count=len(operation.artifact_ids),
                success_count=0,
                failure_count=len(operation.artifact_ids),
                results=[
                    ArtifactResult(
                        artifact_id=aid,
                        success=False,
                        error=f"Unsupported operation: {operation.operation_type.value}",
                    )
                    for aid in operation.artifact_ids
                ],
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )

    def rollback(self) -> int:
        """Rollback the last batch operation.

        Returns:
            Number of operations rolled back.
        """
        count = 0
        while self._rollback_stack:
            try:
                action = self._rollback_stack.pop()
                action()
                count += 1
            except Exception:
                pass
        return count

    def _can_approve(self, artifact_id: str) -> bool:
        """Check if artifact can be approved.

        Args:
            artifact_id: ID of artifact.

        Returns:
            True if can be approved.
        """
        # Stub implementation - always returns True
        # Real implementation would check artifact status
        return True

    def _get_artifact_status(self, artifact_id: str) -> str:
        """Get current artifact status.

        Args:
            artifact_id: ID of artifact.

        Returns:
            Status string.
        """
        # Stub implementation
        return ArtifactStatus.DRAFT.value

    def _approve_artifact(
        self,
        artifact_id: str,
        approver: str,
        reason: str | None,
    ) -> None:
        """Approve a single artifact.

        Args:
            artifact_id: ID of artifact.
            approver: Name of approver.
            reason: Reason for approval.
        """
        # Stub implementation - would use artifact_service
        pass

    def _reject_artifact(self, artifact_id: str, reason: str) -> None:
        """Reject a single artifact.

        Args:
            artifact_id: ID of artifact.
            reason: Reason for rejection.
        """
        # Stub implementation - would use artifact_service
        pass

    def _rollback_status(self, artifact_id: str, old_status: str | None) -> None:
        """Rollback artifact to previous status.

        Args:
            artifact_id: ID of artifact.
            old_status: Previous status.
        """
        # Stub implementation
        pass
