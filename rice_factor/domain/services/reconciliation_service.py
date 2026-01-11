"""Reconciliation service for generating reconciliation plans.

This module provides the service for generating ReconciliationPlan artifacts
from drift reports.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads import ReconciliationPlanPayload
from rice_factor.domain.artifacts.payloads.reconciliation_plan import (
    ReconciliationAction,
    ReconciliationStep,
)
from rice_factor.domain.drift.models import (
    DriftReport,
    DriftSeverity,
    DriftSignal,
    DriftSignalType,
)

if TYPE_CHECKING:
    from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter


# Mapping from drift signal type to reconciliation action
SIGNAL_ACTION_MAP: dict[DriftSignalType, ReconciliationAction] = {
    DriftSignalType.ORPHAN_CODE: ReconciliationAction.CREATE_ARTIFACT,
    DriftSignalType.ORPHAN_PLAN: ReconciliationAction.ARCHIVE_ARTIFACT,
    DriftSignalType.UNDOCUMENTED_BEHAVIOR: ReconciliationAction.UPDATE_REQUIREMENTS,
    DriftSignalType.REFACTOR_HOTSPOT: ReconciliationAction.REVIEW_CODE,
}

# Priority boost for critical signals
SEVERITY_PRIORITY_BOOST: dict[DriftSeverity, int] = {
    DriftSeverity.CRITICAL: 100,
    DriftSeverity.HIGH: 50,
    DriftSeverity.MEDIUM: 10,
    DriftSeverity.LOW: 0,
}


class ReconciliationService:
    """Service for generating reconciliation plans from drift reports.

    This service converts drift signals into actionable reconciliation steps
    and generates ReconciliationPlan artifacts.
    """

    def __init__(
        self,
        storage: FilesystemStorageAdapter | None = None,
    ) -> None:
        """Initialize the reconciliation service.

        Args:
            storage: Optional storage adapter for saving artifacts.
        """
        self._storage = storage

    def generate_plan(
        self,
        drift_report: DriftReport,
        *,
        freeze_new_work: bool = True,
        created_by: CreatedBy = CreatedBy.SYSTEM,
    ) -> ArtifactEnvelope[ReconciliationPlanPayload]:
        """Generate a ReconciliationPlan from a drift report.

        Args:
            drift_report: The drift report to generate a plan from.
            freeze_new_work: Whether to freeze new work while reconciling.
            created_by: Origin of this artifact.

        Returns:
            An ArtifactEnvelope containing the ReconciliationPlan.
        """
        # Generate drift report ID from report content
        drift_report_id = self._generate_drift_report_id(drift_report)

        # Convert signals to steps, sorted by priority
        steps = self._signals_to_steps(drift_report.signals)

        # Create the payload
        payload = ReconciliationPlanPayload(
            drift_report_id=drift_report_id,
            steps=steps,
            freeze_new_work=freeze_new_work,
        )

        # Create the envelope
        artifact_id = uuid4()
        now = datetime.now()

        envelope: ArtifactEnvelope[ReconciliationPlanPayload] = ArtifactEnvelope(
            id=artifact_id,
            artifact_type=ArtifactType.RECONCILIATION_PLAN,
            version="1.0.0",
            created_at=now,
            created_by=created_by,
            status=ArtifactStatus.DRAFT,
            payload=payload,
            hash=self._compute_hash(payload),
        )

        return envelope

    def save_plan(
        self,
        plan: ArtifactEnvelope[ReconciliationPlanPayload],
    ) -> None:
        """Save a reconciliation plan to storage.

        Args:
            plan: The plan to save.

        Raises:
            RuntimeError: If no storage adapter is configured.
        """
        if self._storage is None:
            raise RuntimeError("No storage adapter configured")
        self._storage.save(plan)

    def _signals_to_steps(
        self,
        signals: list[DriftSignal],
    ) -> list[ReconciliationStep]:
        """Convert drift signals to reconciliation steps.

        Steps are sorted by priority (higher severity = higher priority).

        Args:
            signals: List of drift signals.

        Returns:
            List of reconciliation steps sorted by priority.
        """
        steps: list[ReconciliationStep] = []

        # Group signals and assign priorities
        for i, signal in enumerate(signals):
            step = self._signal_to_step(signal, base_priority=i + 1)
            steps.append(step)

        # Sort by priority (lower number = higher priority)
        steps.sort(key=lambda s: s.priority)

        # Renumber priorities sequentially
        for i, step in enumerate(steps):
            # Create new step with updated priority (Pydantic models are immutable-ish)
            steps[i] = ReconciliationStep(
                action=step.action,
                target=step.target,
                reason=step.reason,
                drift_signal_id=step.drift_signal_id,
                priority=i + 1,
            )

        return steps

    def _signal_to_step(
        self,
        signal: DriftSignal,
        base_priority: int,
    ) -> ReconciliationStep:
        """Convert a single drift signal to a reconciliation step.

        Args:
            signal: The drift signal.
            base_priority: Base priority number.

        Returns:
            A ReconciliationStep for this signal.
        """
        action = SIGNAL_ACTION_MAP.get(
            signal.signal_type, ReconciliationAction.REVIEW_CODE
        )

        # Lower priority number = higher priority
        # Use severity order as primary sort key (CRITICAL=1, HIGH=2, MEDIUM=3, LOW=4)
        # Then use base_priority as secondary sort key within same severity
        severity_order = {
            DriftSeverity.CRITICAL: 1,
            DriftSeverity.HIGH: 2,
            DriftSeverity.MEDIUM: 3,
            DriftSeverity.LOW: 4,
        }
        severity_value = severity_order.get(signal.severity, 5)
        effective_priority = severity_value * 1000 + base_priority

        # Generate a signal ID from the signal content
        signal_id = self._generate_signal_id(signal)

        return ReconciliationStep(
            action=action,
            target=signal.path,
            reason=signal.description,
            drift_signal_id=signal_id,
            priority=effective_priority,
        )

    def _generate_drift_report_id(self, drift_report: DriftReport) -> str:
        """Generate a unique ID for a drift report.

        Args:
            drift_report: The drift report.

        Returns:
            A unique identifier string.
        """
        # Use timestamp and signal count for uniqueness
        content = f"{drift_report.analyzed_at.isoformat()}:{drift_report.signal_count}"
        return f"drift-{hashlib.sha256(content.encode()).hexdigest()[:12]}"

    def _generate_signal_id(self, signal: DriftSignal) -> str:
        """Generate a unique ID for a drift signal.

        Args:
            signal: The drift signal.

        Returns:
            A unique identifier string.
        """
        content = f"{signal.signal_type.value}:{signal.path}:{signal.detected_at.isoformat()}"
        return f"signal-{hashlib.sha256(content.encode()).hexdigest()[:12]}"

    def _compute_hash(self, payload: ReconciliationPlanPayload) -> str:
        """Compute hash for the payload.

        Args:
            payload: The payload to hash.

        Returns:
            SHA256 hash of the payload.
        """
        content = payload.model_dump_json()
        return hashlib.sha256(content.encode()).hexdigest()


def check_work_freeze(storage: FilesystemStorageAdapter) -> tuple[bool, str | None]:
    """Check if new work is blocked due to pending reconciliation.

    Args:
        storage: Storage adapter to query.

    Returns:
        Tuple of (is_frozen, artifact_id) where artifact_id is the blocking plan.
    """
    try:
        reconciliation_plans = storage.list_by_type(ArtifactType.RECONCILIATION_PLAN)
    except Exception:
        # No reconciliation plans directory = no freeze
        return False, None

    for plan in reconciliation_plans:
        # Only non-approved plans with freeze_new_work=True block
        if plan.status == ArtifactStatus.APPROVED:
            continue

        # Check if this plan freezes work
        payload = plan.payload
        if hasattr(payload, "freeze_new_work") and payload.freeze_new_work:
            return True, str(plan.id)

    return False, None
