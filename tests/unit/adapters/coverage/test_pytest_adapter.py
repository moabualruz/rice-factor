"""Unit tests for pytest coverage adapter."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from rice_factor.adapters.coverage.pytest_adapter import (
    MockCoverageAdapter,
    PytestCoverageAdapter,
)
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.ports.coverage import (
    CoverageDriftResult,
    CoverageError,
    CoverageResult,
)


from dataclasses import dataclass as dc
from typing import Any


@dc
class MockTestPlan:
    """Mock artifact for testing with dict payload."""

    id: Any
    artifact_type: ArtifactType
    status: ArtifactStatus
    created_at: datetime
    updated_at: datetime
    payload: dict

    @property
    def age_months(self) -> float:
        return (datetime.now(timezone.utc) - self.created_at).days / 30.44


def _make_test_plan(
    baseline_coverage: float | None = None,
) -> MockTestPlan:
    """Create a test TestPlan artifact with dict payload."""
    payload = {}
    if baseline_coverage is not None:
        payload["baseline_coverage"] = baseline_coverage
        payload["baseline_recorded_at"] = datetime.now(timezone.utc).isoformat()

    return MockTestPlan(
        id=uuid4(),
        artifact_type=ArtifactType.TEST_PLAN,
        status=ArtifactStatus.LOCKED,
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
        updated_at=datetime.now(timezone.utc),
        payload=payload,
    )


class TestCoverageResult:
    """Tests for CoverageResult dataclass."""

    def test_creation(self) -> None:
        """CoverageResult should be creatable."""
        result = CoverageResult(
            percentage=85.5,
            lines_covered=855,
            lines_total=1000,
        )
        assert result.percentage == 85.5
        assert result.lines_covered == 855

    def test_to_dict(self) -> None:
        """to_dict should serialize correctly."""
        result = CoverageResult(
            percentage=85.567,
            lines_covered=855,
            lines_total=1000,
            branches_covered=100,
            branches_total=150,
        )
        d = result.to_dict()
        assert d["percentage"] == 85.57  # Rounded
        assert d["branches_covered"] == 100


class TestCoverageDriftResult:
    """Tests for CoverageDriftResult dataclass."""

    def test_creation(self) -> None:
        """CoverageDriftResult should be creatable."""
        result = CoverageDriftResult(
            baseline=90.0,
            current=85.0,
            drift=5.0,
            severity="warning",
            requires_review=False,
        )
        assert result.drift == 5.0
        assert result.severity == "warning"

    def test_to_dict(self) -> None:
        """to_dict should serialize correctly."""
        result = CoverageDriftResult(
            baseline=90.123,
            current=85.456,
            drift=4.667,
            severity="info",
            requires_review=False,
        )
        d = result.to_dict()
        assert d["baseline"] == 90.12
        assert d["drift"] == 4.67


class TestMockCoverageAdapter:
    """Tests for MockCoverageAdapter."""

    def test_get_current_coverage(self) -> None:
        """Should return configured coverage."""
        adapter = MockCoverageAdapter(current_coverage=85.0)
        result = adapter.get_current_coverage()
        assert result.percentage == 85.0

    def test_set_current_coverage(self) -> None:
        """Should allow setting coverage."""
        adapter = MockCoverageAdapter()
        adapter.set_current_coverage(90.0)
        result = adapter.get_current_coverage()
        assert result.percentage == 90.0

    def test_get_baseline_coverage(self) -> None:
        """Should extract baseline from TestPlan."""
        test_plan = _make_test_plan(baseline_coverage=95.0)
        adapter = MockCoverageAdapter()
        baseline = adapter.get_baseline_coverage(test_plan)
        assert baseline == 95.0

    def test_get_baseline_coverage_missing(self) -> None:
        """Should return 0.0 when no baseline."""
        test_plan = _make_test_plan()  # No baseline
        adapter = MockCoverageAdapter()
        baseline = adapter.get_baseline_coverage(test_plan)
        assert baseline == 0.0

    def test_calculate_drift_positive(self) -> None:
        """Positive drift means coverage decreased."""
        test_plan = _make_test_plan(baseline_coverage=90.0)
        adapter = MockCoverageAdapter(current_coverage=85.0)
        result = adapter.calculate_drift(test_plan)
        assert result.drift == 5.0  # 90 - 85
        assert result.baseline == 90.0
        assert result.current == 85.0

    def test_calculate_drift_negative(self) -> None:
        """Negative drift means coverage increased."""
        test_plan = _make_test_plan(baseline_coverage=85.0)
        adapter = MockCoverageAdapter(current_coverage=90.0)
        result = adapter.calculate_drift(test_plan)
        assert result.drift == -5.0  # 85 - 90
        assert result.severity == "ok"

    def test_calculate_drift_no_baseline(self) -> None:
        """Should handle missing baseline gracefully."""
        test_plan = _make_test_plan()  # No baseline
        adapter = MockCoverageAdapter(current_coverage=85.0)
        result = adapter.calculate_drift(test_plan)
        assert result.drift == 0.0
        assert result.requires_review is False

    def test_calculate_drift_triggers_review(self) -> None:
        """Should trigger review when drift exceeds threshold."""
        test_plan = _make_test_plan(baseline_coverage=95.0)
        adapter = MockCoverageAdapter(current_coverage=80.0, coverage_threshold=10.0)
        result = adapter.calculate_drift(test_plan)
        assert result.drift == 15.0  # 95 - 80
        assert result.requires_review is True
        assert result.severity == "critical"

    def test_update_baseline(self) -> None:
        """Should update baseline in payload."""
        test_plan = _make_test_plan()
        adapter = MockCoverageAdapter()
        adapter.update_baseline(test_plan, 92.5)
        assert test_plan.payload["baseline_coverage"] == 92.5
        assert "baseline_recorded_at" in test_plan.payload


class TestPytestCoverageAdapter:
    """Tests for PytestCoverageAdapter (non-subprocess)."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Should initialize with project root."""
        adapter = PytestCoverageAdapter(
            project_root=tmp_path,
            source_dir="src",
            coverage_threshold=15.0,
        )
        assert adapter.project_root == tmp_path
        assert adapter.source_dir == "src"
        assert adapter.coverage_threshold == 15.0

    def test_get_baseline_coverage(self, tmp_path: Path) -> None:
        """Should extract baseline from TestPlan."""
        test_plan = _make_test_plan(baseline_coverage=88.5)
        adapter = PytestCoverageAdapter(project_root=tmp_path)
        baseline = adapter.get_baseline_coverage(test_plan)
        assert baseline == 88.5

    def test_get_baseline_coverage_missing(self, tmp_path: Path) -> None:
        """Should return 0.0 for missing baseline."""
        test_plan = _make_test_plan()
        adapter = PytestCoverageAdapter(project_root=tmp_path)
        baseline = adapter.get_baseline_coverage(test_plan)
        assert baseline == 0.0

    def test_calculate_drift_simple(self, tmp_path: Path) -> None:
        """calculate_drift_simple should return baseline - current."""
        adapter = PytestCoverageAdapter(project_root=tmp_path)
        drift = adapter.calculate_drift_simple(95.0, 85.0)
        assert drift == 10.0

    def test_get_drift_severity_ok(self, tmp_path: Path) -> None:
        """Negative drift should be 'ok'."""
        adapter = PytestCoverageAdapter(project_root=tmp_path)
        severity = adapter.get_drift_severity(-5.0, 10.0)
        assert severity == "ok"

    def test_get_drift_severity_info(self, tmp_path: Path) -> None:
        """Small positive drift should be 'info'."""
        adapter = PytestCoverageAdapter(project_root=tmp_path)
        severity = adapter.get_drift_severity(3.0, 10.0)  # < 5% (half threshold)
        assert severity == "info"

    def test_get_drift_severity_warning(self, tmp_path: Path) -> None:
        """Medium drift should be 'warning'."""
        adapter = PytestCoverageAdapter(project_root=tmp_path)
        severity = adapter.get_drift_severity(7.0, 10.0)  # >= 5%, < 10%
        assert severity == "warning"

    def test_get_drift_severity_critical(self, tmp_path: Path) -> None:
        """Large drift should be 'critical'."""
        adapter = PytestCoverageAdapter(project_root=tmp_path)
        severity = adapter.get_drift_severity(15.0, 10.0)  # >= threshold
        assert severity == "critical"

    def test_update_baseline(self, tmp_path: Path) -> None:
        """Should update baseline in payload."""
        test_plan = _make_test_plan()
        adapter = PytestCoverageAdapter(project_root=tmp_path)
        adapter.update_baseline(test_plan, 91.0)
        assert test_plan.payload["baseline_coverage"] == 91.0
