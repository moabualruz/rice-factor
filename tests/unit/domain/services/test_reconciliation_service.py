"""Unit tests for ReconciliationService."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.payloads.reconciliation_plan import (
    ReconciliationAction,
)
from rice_factor.domain.drift.models import (
    DriftReport,
    DriftSeverity,
    DriftSignal,
    DriftSignalType,
)
from rice_factor.domain.services.reconciliation_service import (
    ReconciliationService,
    SIGNAL_ACTION_MAP,
    check_work_freeze,
)


class TestSignalActionMapping:
    """Tests for signal-to-action mapping."""

    def test_orphan_code_maps_to_create_artifact(self) -> None:
        """ORPHAN_CODE should map to CREATE_ARTIFACT."""
        assert SIGNAL_ACTION_MAP[DriftSignalType.ORPHAN_CODE] == ReconciliationAction.CREATE_ARTIFACT

    def test_orphan_plan_maps_to_archive_artifact(self) -> None:
        """ORPHAN_PLAN should map to ARCHIVE_ARTIFACT."""
        assert SIGNAL_ACTION_MAP[DriftSignalType.ORPHAN_PLAN] == ReconciliationAction.ARCHIVE_ARTIFACT

    def test_undocumented_behavior_maps_to_update_requirements(self) -> None:
        """UNDOCUMENTED_BEHAVIOR should map to UPDATE_REQUIREMENTS."""
        assert SIGNAL_ACTION_MAP[DriftSignalType.UNDOCUMENTED_BEHAVIOR] == ReconciliationAction.UPDATE_REQUIREMENTS

    def test_refactor_hotspot_maps_to_review_code(self) -> None:
        """REFACTOR_HOTSPOT should map to REVIEW_CODE."""
        assert SIGNAL_ACTION_MAP[DriftSignalType.REFACTOR_HOTSPOT] == ReconciliationAction.REVIEW_CODE


class TestReconciliationServiceGeneratePlan:
    """Tests for ReconciliationService.generate_plan."""

    def test_generates_valid_artifact(self) -> None:
        """generate_plan should return a valid ArtifactEnvelope."""
        service = ReconciliationService()

        drift_report = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.MEDIUM,
                    path="src/orphan.py",
                    description="Orphan code file",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )

        plan = service.generate_plan(drift_report)

        assert plan.artifact_type == ArtifactType.RECONCILIATION_PLAN
        assert plan.status == ArtifactStatus.DRAFT
        assert plan.id is not None

    def test_includes_all_signals_as_steps(self) -> None:
        """All signals should be converted to steps."""
        service = ReconciliationService()

        drift_report = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.MEDIUM,
                    path="src/orphan1.py",
                    description="First orphan",
                    detected_at=datetime.now(),
                ),
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_PLAN,
                    severity=DriftSeverity.HIGH,
                    path="artifacts/stale.json",
                    description="Stale plan",
                    detected_at=datetime.now(),
                ),
            ],
            threshold=3,
        )

        plan = service.generate_plan(drift_report)

        assert len(plan.payload.steps) == 2

    def test_steps_sorted_by_priority(self) -> None:
        """Steps should be sorted with higher severity first."""
        service = ReconciliationService()

        drift_report = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.LOW,
                    path="src/low.py",
                    description="Low severity",
                    detected_at=datetime.now(),
                ),
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_PLAN,
                    severity=DriftSeverity.CRITICAL,
                    path="artifacts/critical.json",
                    description="Critical severity",
                    detected_at=datetime.now(),
                ),
            ],
            threshold=3,
        )

        plan = service.generate_plan(drift_report)

        # Critical should come first (lower priority number)
        assert plan.payload.steps[0].priority == 1
        assert plan.payload.steps[0].target == "artifacts/critical.json"
        assert plan.payload.steps[1].priority == 2

    def test_freeze_new_work_default_true(self) -> None:
        """freeze_new_work should default to True."""
        service = ReconciliationService()

        drift_report = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.MEDIUM,
                    path="src/orphan.py",
                    description="Orphan code file",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )

        plan = service.generate_plan(drift_report)

        assert plan.payload.freeze_new_work is True

    def test_freeze_new_work_can_be_disabled(self) -> None:
        """freeze_new_work can be set to False."""
        service = ReconciliationService()

        drift_report = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.MEDIUM,
                    path="src/orphan.py",
                    description="Orphan code file",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )

        plan = service.generate_plan(drift_report, freeze_new_work=False)

        assert plan.payload.freeze_new_work is False

    def test_empty_signals_produces_empty_steps(self) -> None:
        """No signals should produce no steps."""
        service = ReconciliationService()

        drift_report = DriftReport(signals=[], threshold=3)

        plan = service.generate_plan(drift_report)

        assert len(plan.payload.steps) == 0

    def test_step_action_matches_signal_type(self) -> None:
        """Each step's action should match the signal type mapping."""
        service = ReconciliationService()

        drift_report = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.MEDIUM,
                    path="src/orphan.py",
                    description="Orphan code file",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )

        plan = service.generate_plan(drift_report)

        assert plan.payload.steps[0].action == ReconciliationAction.CREATE_ARTIFACT

    def test_step_includes_reason_from_signal(self) -> None:
        """Step reason should come from signal description."""
        service = ReconciliationService()

        drift_report = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.MEDIUM,
                    path="src/orphan.py",
                    description="This is the description",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )

        plan = service.generate_plan(drift_report)

        assert plan.payload.steps[0].reason == "This is the description"


class TestReconciliationServiceSavePlan:
    """Tests for ReconciliationService.save_plan."""

    def test_save_calls_storage(self) -> None:
        """save_plan should call storage.save."""
        mock_storage = MagicMock()
        service = ReconciliationService(storage=mock_storage)

        drift_report = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.MEDIUM,
                    path="src/orphan.py",
                    description="Orphan code file",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )

        plan = service.generate_plan(drift_report)
        service.save_plan(plan)

        mock_storage.save.assert_called_once_with(plan)

    def test_save_raises_without_storage(self) -> None:
        """save_plan should raise if no storage configured."""
        service = ReconciliationService()

        drift_report = DriftReport(signals=[], threshold=3)
        plan = service.generate_plan(drift_report)

        with pytest.raises(RuntimeError, match="No storage adapter"):
            service.save_plan(plan)


class TestCheckWorkFreeze:
    """Tests for check_work_freeze function."""

    def test_no_freeze_when_no_plans(self) -> None:
        """Should return False when no reconciliation plans exist."""
        mock_storage = MagicMock()
        mock_storage.list_by_type.return_value = []

        is_frozen, artifact_id = check_work_freeze(mock_storage)

        assert is_frozen is False
        assert artifact_id is None

    def test_no_freeze_when_plan_approved(self) -> None:
        """Should return False when reconciliation plan is approved."""
        mock_plan = MagicMock()
        mock_plan.status = ArtifactStatus.APPROVED
        mock_plan.id = "test-id"

        mock_storage = MagicMock()
        mock_storage.list_by_type.return_value = [mock_plan]

        is_frozen, artifact_id = check_work_freeze(mock_storage)

        assert is_frozen is False
        assert artifact_id is None

    def test_freeze_when_draft_plan_exists(self) -> None:
        """Should return True when draft plan with freeze_new_work=True exists."""
        mock_payload = MagicMock()
        mock_payload.freeze_new_work = True

        mock_plan = MagicMock()
        mock_plan.status = ArtifactStatus.DRAFT
        mock_plan.id = "freeze-plan-id"
        mock_plan.payload = mock_payload

        mock_storage = MagicMock()
        mock_storage.list_by_type.return_value = [mock_plan]

        is_frozen, artifact_id = check_work_freeze(mock_storage)

        assert is_frozen is True
        assert artifact_id == "freeze-plan-id"

    def test_no_freeze_when_freeze_disabled(self) -> None:
        """Should return False when draft plan has freeze_new_work=False."""
        mock_payload = MagicMock()
        mock_payload.freeze_new_work = False

        mock_plan = MagicMock()
        mock_plan.status = ArtifactStatus.DRAFT
        mock_plan.id = "no-freeze-plan-id"
        mock_plan.payload = mock_payload

        mock_storage = MagicMock()
        mock_storage.list_by_type.return_value = [mock_plan]

        is_frozen, artifact_id = check_work_freeze(mock_storage)

        assert is_frozen is False
        assert artifact_id is None

    def test_handles_storage_exception(self) -> None:
        """Should return False if storage raises exception."""
        mock_storage = MagicMock()
        mock_storage.list_by_type.side_effect = Exception("Storage error")

        is_frozen, artifact_id = check_work_freeze(mock_storage)

        assert is_frozen is False
        assert artifact_id is None
