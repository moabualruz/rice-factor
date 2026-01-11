"""Unit tests for drift detection domain models."""

from datetime import datetime

import pytest

from rice_factor.domain.drift.models import (
    DriftConfig,
    DriftReport,
    DriftSeverity,
    DriftSignal,
    DriftSignalType,
)


class TestDriftSignalType:
    """Tests for DriftSignalType enum."""

    def test_has_all_signal_types(self) -> None:
        """Should have all 4 drift signal types."""
        assert DriftSignalType.ORPHAN_CODE.value == "orphan_code"
        assert DriftSignalType.ORPHAN_PLAN.value == "orphan_plan"
        assert DriftSignalType.UNDOCUMENTED_BEHAVIOR.value == "undocumented_behavior"
        assert DriftSignalType.REFACTOR_HOTSPOT.value == "refactor_hotspot"

    def test_is_string_enum(self) -> None:
        """DriftSignalType value should be a string."""
        assert DriftSignalType.ORPHAN_CODE.value == "orphan_code"


class TestDriftSeverity:
    """Tests for DriftSeverity enum."""

    def test_has_all_severity_levels(self) -> None:
        """Should have all 4 severity levels."""
        assert DriftSeverity.LOW.value == "low"
        assert DriftSeverity.MEDIUM.value == "medium"
        assert DriftSeverity.HIGH.value == "high"
        assert DriftSeverity.CRITICAL.value == "critical"


class TestDriftSignal:
    """Tests for DriftSignal dataclass."""

    def test_create_signal(self) -> None:
        """Should create a drift signal with all fields."""
        now = datetime.now()
        signal = DriftSignal(
            signal_type=DriftSignalType.ORPHAN_CODE,
            severity=DriftSeverity.MEDIUM,
            path="src/orphan.py",
            description="No plan covers this file",
            detected_at=now,
            related_artifact_id="abc123",
            suggested_action="Create ImplementationPlan",
        )

        assert signal.signal_type == DriftSignalType.ORPHAN_CODE
        assert signal.severity == DriftSeverity.MEDIUM
        assert signal.path == "src/orphan.py"
        assert signal.detected_at == now
        assert signal.related_artifact_id == "abc123"

    def test_to_dict(self) -> None:
        """Should serialize to dictionary."""
        now = datetime.now()
        signal = DriftSignal(
            signal_type=DriftSignalType.ORPHAN_PLAN,
            severity=DriftSeverity.HIGH,
            path="impl-plan.json",
            description="Plan targets missing file",
            detected_at=now,
        )

        data = signal.to_dict()

        assert data["signal_type"] == "orphan_plan"
        assert data["severity"] == "high"
        assert data["path"] == "impl-plan.json"
        assert data["detected_at"] == now.isoformat()

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields should default to None."""
        signal = DriftSignal(
            signal_type=DriftSignalType.REFACTOR_HOTSPOT,
            severity=DriftSeverity.MEDIUM,
            path="src/hot.py",
            description="Frequently refactored",
            detected_at=datetime.now(),
        )

        assert signal.related_artifact_id is None
        assert signal.suggested_action is None


class TestDriftReport:
    """Tests for DriftReport dataclass."""

    def test_empty_report(self) -> None:
        """Empty report should pass and not require reconciliation."""
        report = DriftReport()

        assert report.signal_count == 0
        assert report.exceeds_threshold is False
        assert report.requires_reconciliation is False

    def test_signal_count(self) -> None:
        """Should count signals correctly."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.MEDIUM,
                path=f"src/file{i}.py",
                description="Test",
                detected_at=datetime.now(),
            )
            for i in range(5)
        ]
        report = DriftReport(signals=signals, threshold=3)

        assert report.signal_count == 5
        assert report.exceeds_threshold is True
        assert report.requires_reconciliation is True

    def test_threshold_evaluation(self) -> None:
        """Threshold should be correctly evaluated."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.MEDIUM,
                path="src/file.py",
                description="Test",
                detected_at=datetime.now(),
            )
            for _ in range(2)
        ]
        report = DriftReport(signals=signals, threshold=3)

        assert report.exceeds_threshold is False

        report_at_threshold = DriftReport(signals=signals + signals[:1], threshold=3)
        assert report_at_threshold.exceeds_threshold is True

    def test_critical_signal_requires_reconciliation(self) -> None:
        """Critical signals should require reconciliation regardless of threshold."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_PLAN,
                severity=DriftSeverity.CRITICAL,
                path="plan.json",
                description="Critical issue",
                detected_at=datetime.now(),
            )
        ]
        report = DriftReport(signals=signals, threshold=10)

        assert report.signal_count == 1
        assert report.exceeds_threshold is False
        assert report.requires_reconciliation is True

    def test_by_type_filter(self) -> None:
        """Should filter signals by type."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.MEDIUM,
                path="src/a.py",
                description="Orphan code",
                detected_at=datetime.now(),
            ),
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_PLAN,
                severity=DriftSeverity.HIGH,
                path="plan.json",
                description="Orphan plan",
                detected_at=datetime.now(),
            ),
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.MEDIUM,
                path="src/b.py",
                description="Orphan code 2",
                detected_at=datetime.now(),
            ),
        ]
        report = DriftReport(signals=signals)

        orphan_code = report.by_type(DriftSignalType.ORPHAN_CODE)
        orphan_plan = report.by_type(DriftSignalType.ORPHAN_PLAN)
        hotspots = report.by_type(DriftSignalType.REFACTOR_HOTSPOT)

        assert len(orphan_code) == 2
        assert len(orphan_plan) == 1
        assert len(hotspots) == 0

    def test_by_severity_filter(self) -> None:
        """Should filter signals by severity."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.MEDIUM,
                path="src/a.py",
                description="Medium",
                detected_at=datetime.now(),
            ),
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_PLAN,
                severity=DriftSeverity.HIGH,
                path="plan.json",
                description="High",
                detected_at=datetime.now(),
            ),
        ]
        report = DriftReport(signals=signals)

        medium = report.by_severity(DriftSeverity.MEDIUM)
        high = report.by_severity(DriftSeverity.HIGH)

        assert len(medium) == 1
        assert len(high) == 1

    def test_to_dict(self) -> None:
        """Should serialize to dictionary with summary."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.MEDIUM,
                path="src/file.py",
                description="Test",
                detected_at=datetime.now(),
            ),
        ]
        report = DriftReport(
            signals=signals,
            threshold=3,
            code_files_scanned=10,
            artifacts_checked=5,
        )

        data = report.to_dict()

        assert data["signal_count"] == 1
        assert data["threshold"] == 3
        assert data["code_files_scanned"] == 10
        assert data["artifacts_checked"] == 5
        assert "summary" in data
        assert data["summary"]["orphan_code"] == 1

    def test_has_high_severity(self) -> None:
        """Should detect high or critical severity signals."""
        low_signal = DriftSignal(
            signal_type=DriftSignalType.ORPHAN_CODE,
            severity=DriftSeverity.LOW,
            path="file.py",
            description="Low",
            detected_at=datetime.now(),
        )
        high_signal = DriftSignal(
            signal_type=DriftSignalType.ORPHAN_PLAN,
            severity=DriftSeverity.HIGH,
            path="plan.json",
            description="High",
            detected_at=datetime.now(),
        )

        low_report = DriftReport(signals=[low_signal])
        high_report = DriftReport(signals=[high_signal])

        assert low_report.has_high_severity is False
        assert high_report.has_high_severity is True


class TestDriftConfig:
    """Tests for DriftConfig dataclass."""

    def test_defaults(self) -> None:
        """Should have sensible defaults."""
        config = DriftConfig()

        assert config.drift_threshold == 3
        assert config.refactor_threshold == 3
        assert config.refactor_window_days == 30
        assert "*.py" in config.code_patterns
        assert "src" in config.source_dirs

    def test_should_ignore(self) -> None:
        """Should correctly identify ignored paths."""
        config = DriftConfig()

        assert config.should_ignore("test_main.py") is True
        assert config.should_ignore("tests/test.py") is True
        assert config.should_ignore("__pycache__/cache.pyc") is True
        assert config.should_ignore("src/main.py") is False

    def test_matches_code_pattern(self) -> None:
        """Should correctly match code patterns."""
        config = DriftConfig()

        assert config.matches_code_pattern("main.py") is True
        assert config.matches_code_pattern("app.ts") is True
        assert config.matches_code_pattern("readme.md") is False
