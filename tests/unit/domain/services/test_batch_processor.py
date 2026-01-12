"""Unit tests for BatchProcessor service."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from rice_factor.domain.services.batch_processor import (
    ArtifactResult,
    BatchOperation,
    BatchOperationType,
    BatchProcessor,
    BatchResult,
    BatchResultStatus,
)


class TestBatchOperationType:
    """Tests for BatchOperationType enum."""

    def test_all_types_exist(self) -> None:
        """All expected types should exist."""
        assert BatchOperationType.APPROVE.value == "approve"
        assert BatchOperationType.REJECT.value == "reject"
        assert BatchOperationType.LOCK.value == "lock"
        assert BatchOperationType.TRANSITION.value == "transition"


class TestBatchResultStatus:
    """Tests for BatchResultStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """All expected statuses should exist."""
        assert BatchResultStatus.SUCCESS.value == "success"
        assert BatchResultStatus.PARTIAL.value == "partial"
        assert BatchResultStatus.FAILED.value == "failed"
        assert BatchResultStatus.ROLLED_BACK.value == "rolled_back"


class TestBatchOperation:
    """Tests for BatchOperation dataclass."""

    def test_creation(self) -> None:
        """BatchOperation should be creatable."""
        op = BatchOperation(
            operation_type=BatchOperationType.APPROVE,
            artifact_ids=["a1", "a2", "a3"],
        )
        assert op.operation_type == BatchOperationType.APPROVE
        assert len(op.artifact_ids) == 3

    def test_with_options(self) -> None:
        """should accept options."""
        op = BatchOperation(
            operation_type=BatchOperationType.REJECT,
            artifact_ids=["a1"],
            options={"reason": "Test rejection"},
        )
        assert op.options["reason"] == "Test rejection"


class TestArtifactResult:
    """Tests for ArtifactResult dataclass."""

    def test_creation(self) -> None:
        """ArtifactResult should be creatable."""
        result = ArtifactResult(
            artifact_id="art-1",
            success=True,
            old_status="draft",
            new_status="approved",
        )
        assert result.artifact_id == "art-1"
        assert result.success is True

    def test_with_error(self) -> None:
        """should include error details."""
        result = ArtifactResult(
            artifact_id="art-1",
            success=False,
            error="Validation failed",
        )
        assert result.success is False
        assert "failed" in result.error.lower()

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        result = ArtifactResult(
            artifact_id="a1",
            success=True,
            old_status="draft",
            new_status="approved",
        )
        data = result.to_dict()
        assert data["artifact_id"] == "a1"
        assert data["success"] is True


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_creation(self) -> None:
        """BatchResult should be creatable."""
        now = datetime.now(UTC)
        result = BatchResult(
            operation_type=BatchOperationType.APPROVE,
            status=BatchResultStatus.SUCCESS,
            total_count=5,
            success_count=5,
            failure_count=0,
            results=[],
            started_at=now,
        )
        assert result.total_count == 5
        assert result.all_succeeded is True

    def test_success_rate(self) -> None:
        """should calculate success rate."""
        now = datetime.now(UTC)
        result = BatchResult(
            operation_type=BatchOperationType.APPROVE,
            status=BatchResultStatus.PARTIAL,
            total_count=10,
            success_count=8,
            failure_count=2,
            results=[],
            started_at=now,
        )
        assert result.success_rate == 80.0

    def test_success_rate_zero_total(self) -> None:
        """should handle zero total."""
        now = datetime.now(UTC)
        result = BatchResult(
            operation_type=BatchOperationType.APPROVE,
            status=BatchResultStatus.SUCCESS,
            total_count=0,
            success_count=0,
            failure_count=0,
            results=[],
            started_at=now,
        )
        assert result.success_rate == 100.0

    def test_not_all_succeeded(self) -> None:
        """should detect failures."""
        now = datetime.now(UTC)
        result = BatchResult(
            operation_type=BatchOperationType.APPROVE,
            status=BatchResultStatus.PARTIAL,
            total_count=5,
            success_count=4,
            failure_count=1,
            results=[],
            started_at=now,
        )
        assert result.all_succeeded is False

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        result = BatchResult(
            operation_type=BatchOperationType.APPROVE,
            status=BatchResultStatus.SUCCESS,
            total_count=3,
            success_count=3,
            failure_count=0,
            results=[],
            started_at=now,
            completed_at=now,
        )
        data = result.to_dict()
        assert data["operation_type"] == "approve"
        assert data["status"] == "success"


class TestBatchProcessor:
    """Tests for BatchProcessor service."""

    def test_creation(self, tmp_path: Path) -> None:
        """BatchProcessor should be creatable."""
        processor = BatchProcessor(repo_root=tmp_path)
        assert processor.repo_root == tmp_path

    def test_approve_batch_empty(self, tmp_path: Path) -> None:
        """should handle empty batch."""
        processor = BatchProcessor(repo_root=tmp_path)
        result = processor.approve_batch([])
        assert result.status == BatchResultStatus.SUCCESS
        assert result.total_count == 0

    def test_approve_batch(self, tmp_path: Path) -> None:
        """should approve multiple artifacts."""
        processor = BatchProcessor(repo_root=tmp_path)
        result = processor.approve_batch(
            ["art-1", "art-2", "art-3"],
            approver="test-user",
            reason="Batch approved",
        )
        assert result.status == BatchResultStatus.SUCCESS
        assert result.total_count == 3
        assert result.success_count == 3

    def test_reject_batch(self, tmp_path: Path) -> None:
        """should reject multiple artifacts."""
        processor = BatchProcessor(repo_root=tmp_path)
        result = processor.reject_batch(
            ["art-1", "art-2"],
            reason="Batch rejected",
        )
        assert result.status == BatchResultStatus.SUCCESS
        assert result.total_count == 2

    def test_reject_batch_individual_reasons(self, tmp_path: Path) -> None:
        """should use individual reasons."""
        processor = BatchProcessor(repo_root=tmp_path)
        result = processor.reject_batch(
            ["art-1", "art-2"],
            reason="Default reason",
            individual_reasons={"art-1": "Specific reason for art-1"},
        )
        assert result.status == BatchResultStatus.SUCCESS

    def test_execute_approve_operation(self, tmp_path: Path) -> None:
        """should execute approve operation."""
        processor = BatchProcessor(repo_root=tmp_path)
        operation = BatchOperation(
            operation_type=BatchOperationType.APPROVE,
            artifact_ids=["a1", "a2"],
            options={"approver": "test"},
        )
        result = processor.execute(operation)
        assert result.operation_type == BatchOperationType.APPROVE
        assert result.success_count == 2

    def test_execute_reject_operation(self, tmp_path: Path) -> None:
        """should execute reject operation."""
        processor = BatchProcessor(repo_root=tmp_path)
        operation = BatchOperation(
            operation_type=BatchOperationType.REJECT,
            artifact_ids=["a1"],
            options={"reason": "Test reject"},
        )
        result = processor.execute(operation)
        assert result.operation_type == BatchOperationType.REJECT

    def test_execute_unsupported_operation(self, tmp_path: Path) -> None:
        """should fail for unsupported operations."""
        processor = BatchProcessor(repo_root=tmp_path)
        operation = BatchOperation(
            operation_type=BatchOperationType.LOCK,
            artifact_ids=["a1"],
        )
        result = processor.execute(operation)
        assert result.status == BatchResultStatus.FAILED

    def test_rollback(self, tmp_path: Path) -> None:
        """should rollback batch operation."""
        processor = BatchProcessor(repo_root=tmp_path)
        processor.approve_batch(["a1", "a2", "a3"])
        count = processor.rollback()
        assert count == 3
