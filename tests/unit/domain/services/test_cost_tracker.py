"""Unit tests for CostTracker service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from rice_factor.domain.services.cost_tracker import (
    AlertLevel,
    CostAlert,
    CostLimitExceeded,
    CostLimits,
    CostRecord,
    CostSummary,
    CostThreshold,
    CostTracker,
    get_cost_tracker,
    reset_cost_tracker,
)


class TestAlertLevel:
    """Tests for AlertLevel enum."""

    def test_info_value(self) -> None:
        """AlertLevel.INFO should have 'info' value."""
        assert AlertLevel.INFO.value == "info"

    def test_warning_value(self) -> None:
        """AlertLevel.WARNING should have 'warning' value."""
        assert AlertLevel.WARNING.value == "warning"

    def test_critical_value(self) -> None:
        """AlertLevel.CRITICAL should have 'critical' value."""
        assert AlertLevel.CRITICAL.value == "critical"

    def test_limit_value(self) -> None:
        """AlertLevel.LIMIT should have 'limit' value."""
        assert AlertLevel.LIMIT.value == "limit"


class TestCostLimitExceeded:
    """Tests for CostLimitExceeded exception."""

    def test_exception_attributes(self) -> None:
        """CostLimitExceeded should store all attributes."""
        exc = CostLimitExceeded(
            current_cost=150.0,
            limit=100.0,
            period="daily",
        )
        assert exc.current_cost == 150.0
        assert exc.limit == 100.0
        assert exc.period == "daily"

    def test_exception_message(self) -> None:
        """CostLimitExceeded message should be descriptive."""
        exc = CostLimitExceeded(
            current_cost=50.0,
            limit=25.0,
            period="monthly",
        )
        assert "50.00" in str(exc)
        assert "25.00" in str(exc)
        assert "monthly" in str(exc)


class TestCostRecord:
    """Tests for CostRecord dataclass."""

    def test_record_attributes(self) -> None:
        """CostRecord should store all attributes."""
        now = datetime.now(UTC)
        record = CostRecord(
            timestamp=now,
            provider="claude",
            model="claude-sonnet-4-20250514",
            operation="generate",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.15,
            metadata={"task": "test"},
        )
        assert record.timestamp == now
        assert record.provider == "claude"
        assert record.cost_usd == 0.15

    def test_record_default_metadata(self) -> None:
        """CostRecord should have empty default metadata."""
        record = CostRecord(
            timestamp=datetime.now(UTC),
            provider="test",
            model="test",
            operation="test",
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
        )
        assert record.metadata == {}


class TestCostAlert:
    """Tests for CostAlert dataclass."""

    def test_alert_attributes(self) -> None:
        """CostAlert should store all attributes."""
        now = datetime.now(UTC)
        alert = CostAlert(
            timestamp=now,
            level=AlertLevel.WARNING,
            threshold=50.0,
            current_value=55.0,
            period="daily",
            message="Test alert",
        )
        assert alert.level == AlertLevel.WARNING
        assert alert.threshold == 50.0
        assert alert.current_value == 55.0


class TestCostThreshold:
    """Tests for CostThreshold dataclass."""

    def test_threshold_defaults(self) -> None:
        """CostThreshold should have triggered=False default."""
        threshold = CostThreshold(amount=100.0, level=AlertLevel.WARNING)
        assert threshold.triggered is False

    def test_threshold_custom(self) -> None:
        """CostThreshold should accept custom triggered state."""
        threshold = CostThreshold(
            amount=50.0, level=AlertLevel.CRITICAL, triggered=True
        )
        assert threshold.triggered is True


class TestCostLimits:
    """Tests for CostLimits dataclass."""

    def test_limits_defaults(self) -> None:
        """CostLimits should have sensible defaults."""
        limits = CostLimits(period="daily")
        assert limits.hard_limit is None
        assert limits.thresholds == []
        assert limits.enabled is True


class TestCostSummary:
    """Tests for CostSummary dataclass."""

    def test_summary_attributes(self) -> None:
        """CostSummary should store all attributes."""
        now = datetime.now(UTC)
        summary = CostSummary(
            period="daily",
            start_time=now - timedelta(hours=1),
            end_time=now,
            total_cost=100.0,
            by_provider={"claude": 80.0, "openai": 20.0},
            by_model={"claude-sonnet": 80.0, "gpt-4": 20.0},
            by_operation={"generate": 100.0},
            record_count=10,
        )
        assert summary.total_cost == 100.0
        assert summary.by_provider["claude"] == 80.0


class TestCostTrackerInit:
    """Tests for CostTracker initialization."""

    def test_starts_empty(self) -> None:
        """CostTracker should start with no records."""
        tracker = CostTracker()
        assert tracker.get_total_cost() == 0.0

    def test_has_default_periods(self) -> None:
        """CostTracker should have daily and monthly periods."""
        tracker = CostTracker()
        state = tracker.to_dict()
        assert "daily" in state["limits"]
        assert "monthly" in state["limits"]


class TestCostTrackerRecord:
    """Tests for CostTracker.record."""

    def test_record_adds_cost(self) -> None:
        """record should add cost to tracker."""
        tracker = CostTracker()

        record = tracker.record(
            provider="claude",
            model="claude-sonnet-4-20250514",
            operation="generate",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.15,
        )

        assert record.cost_usd == 0.15
        assert tracker.get_total_cost() == 0.15

    def test_record_with_metadata(self) -> None:
        """record should store metadata."""
        tracker = CostTracker()

        record = tracker.record(
            provider="claude",
            model="model",
            operation="op",
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            metadata={"request_id": "123"},
        )

        assert record.metadata["request_id"] == "123"

    def test_record_accumulates(self) -> None:
        """Multiple records should accumulate."""
        tracker = CostTracker()

        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.10,
        )
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.20,
        )

        assert tracker.get_total_cost() == pytest.approx(0.30)


class TestCostTrackerLimits:
    """Tests for CostTracker limits."""

    def test_set_daily_limit(self) -> None:
        """set_daily_limit should configure limit."""
        tracker = CostTracker()
        tracker.set_daily_limit(100.0)

        state = tracker.to_dict()
        assert state["limits"]["daily"]["hard_limit"] == 100.0

    def test_set_monthly_limit(self) -> None:
        """set_monthly_limit should configure limit."""
        tracker = CostTracker()
        tracker.set_monthly_limit(1000.0)

        state = tracker.to_dict()
        assert state["limits"]["monthly"]["hard_limit"] == 1000.0

    def test_limit_blocks_recording(self) -> None:
        """Hard limit should block recording when exceeded."""
        tracker = CostTracker()
        tracker.set_daily_limit(1.0)

        # First record is fine
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.50,
        )

        # Second record exceeds limit
        with pytest.raises(CostLimitExceeded) as exc_info:
            tracker.record(
                provider="claude", model="m", operation="o",
                input_tokens=0, output_tokens=0, cost_usd=0.60,
            )

        assert exc_info.value.limit == 1.0
        assert exc_info.value.period == "daily"

    def test_disabled_limit_allows_recording(self) -> None:
        """Disabled limit should allow recording."""
        tracker = CostTracker()
        tracker.set_daily_limit(0.10)
        tracker._limits["daily"].enabled = False

        # Should not raise despite exceeding limit
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=1.0,
        )

        assert tracker.get_total_cost() == 1.0


class TestCostTrackerThresholds:
    """Tests for CostTracker thresholds."""

    def test_add_threshold(self) -> None:
        """add_threshold should add threshold."""
        tracker = CostTracker()
        tracker.add_threshold("daily", 50.0, AlertLevel.WARNING)

        state = tracker.to_dict()
        assert len(state["limits"]["daily"]["thresholds"]) == 1
        assert state["limits"]["daily"]["thresholds"][0]["amount"] == 50.0

    def test_thresholds_sorted(self) -> None:
        """Thresholds should be sorted by amount."""
        tracker = CostTracker()
        tracker.add_threshold("daily", 100.0, AlertLevel.CRITICAL)
        tracker.add_threshold("daily", 50.0, AlertLevel.WARNING)

        state = tracker.to_dict()
        amounts = [t["amount"] for t in state["limits"]["daily"]["thresholds"]]
        assert amounts == [50.0, 100.0]

    def test_threshold_triggers_alert(self) -> None:
        """Crossing threshold should trigger alert."""
        tracker = CostTracker()
        tracker.add_threshold("daily", 0.50, AlertLevel.WARNING)

        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.60,
        )

        alerts = tracker.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING
        assert alerts[0].threshold == 0.50

    def test_threshold_triggers_once(self) -> None:
        """Threshold should only trigger once until reset."""
        tracker = CostTracker()
        tracker.add_threshold("daily", 0.50, AlertLevel.WARNING)

        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.60,
        )
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.30,
        )

        alerts = tracker.get_alerts()
        assert len(alerts) == 1  # Only one alert


class TestCostTrackerAlertHandlers:
    """Tests for CostTracker alert handlers."""

    def test_add_alert_handler(self) -> None:
        """add_alert_handler should register handler."""
        tracker = CostTracker()
        handler = MagicMock()
        tracker.add_alert_handler(handler)
        tracker.add_threshold("daily", 0.10, AlertLevel.WARNING)

        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.20,
        )

        handler.assert_called_once()
        alert = handler.call_args[0][0]
        assert alert.level == AlertLevel.WARNING

    def test_remove_alert_handler(self) -> None:
        """remove_alert_handler should unregister handler."""
        tracker = CostTracker()
        handler = MagicMock()
        tracker.add_alert_handler(handler)

        result = tracker.remove_alert_handler(handler)
        assert result is True

        tracker.add_threshold("daily", 0.10, AlertLevel.WARNING)
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.20,
        )

        handler.assert_not_called()

    def test_handler_error_doesnt_break_tracking(self) -> None:
        """Handler error should not break tracking."""
        tracker = CostTracker()

        def bad_handler(alert: CostAlert) -> None:
            raise ValueError("Handler error")

        tracker.add_alert_handler(bad_handler)
        tracker.add_threshold("daily", 0.10, AlertLevel.WARNING)

        # Should not raise
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.20,
        )

        assert tracker.get_total_cost() == 0.20


class TestCostTrackerGetters:
    """Tests for CostTracker getter methods."""

    def test_get_daily_cost(self) -> None:
        """get_daily_cost should return today's cost."""
        tracker = CostTracker()
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=10.0,
        )

        assert tracker.get_daily_cost() == 10.0

    def test_get_monthly_cost(self) -> None:
        """get_monthly_cost should return this month's cost."""
        tracker = CostTracker()
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=50.0,
        )

        assert tracker.get_monthly_cost() == 50.0

    def test_get_alerts_with_filter(self) -> None:
        """get_alerts should support filtering."""
        tracker = CostTracker()
        tracker.add_threshold("daily", 0.10, AlertLevel.WARNING)
        tracker.add_threshold("daily", 0.20, AlertLevel.CRITICAL)
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.25,
        )

        warning_alerts = tracker.get_alerts(level=AlertLevel.WARNING)
        assert len(warning_alerts) == 1

        critical_alerts = tracker.get_alerts(level=AlertLevel.CRITICAL)
        assert len(critical_alerts) == 1


class TestCostTrackerSummary:
    """Tests for CostTracker.get_summary."""

    def test_summary_aggregates(self) -> None:
        """get_summary should aggregate by dimensions."""
        tracker = CostTracker()
        tracker.record(
            provider="claude", model="claude-sonnet", operation="generate",
            input_tokens=1000, output_tokens=500, cost_usd=0.10,
        )
        tracker.record(
            provider="openai", model="gpt-4", operation="generate",
            input_tokens=500, output_tokens=250, cost_usd=0.05,
        )

        summary = tracker.get_summary("daily")

        assert summary.total_cost == pytest.approx(0.15)
        assert summary.by_provider["claude"] == pytest.approx(0.10)
        assert summary.by_provider["openai"] == pytest.approx(0.05)
        assert summary.record_count == 2


class TestCostTrackerExportReport:
    """Tests for CostTracker.export_report."""

    def test_export_json(self) -> None:
        """export_report with json format should return dict."""
        tracker = CostTracker()
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=10.0,
        )

        report = tracker.export_report(period="daily", format="json")

        assert isinstance(report, dict)
        assert report["total_cost_usd"] == 10.0
        assert "by_provider" in report

    def test_export_csv(self) -> None:
        """export_report with csv format should return string."""
        tracker = CostTracker()
        tracker.record(
            provider="claude", model="model", operation="op",
            input_tokens=0, output_tokens=0, cost_usd=1.0,
        )

        report = tracker.export_report(period="daily", format="csv")

        assert isinstance(report, str)
        assert "provider,model,operation,cost_usd" in report
        assert "claude,model,op" in report

    def test_export_text(self) -> None:
        """export_report with text format should return string."""
        tracker = CostTracker()
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=5.0,
        )

        report = tracker.export_report(period="daily", format="text")

        assert isinstance(report, str)
        assert "Cost Report" in report
        assert "claude" in report


class TestCostTrackerResetThresholds:
    """Tests for CostTracker.reset_thresholds."""

    def test_reset_thresholds(self) -> None:
        """reset_thresholds should allow re-triggering."""
        tracker = CostTracker()
        tracker.add_threshold("daily", 0.10, AlertLevel.WARNING)

        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.15,
        )
        assert len(tracker.get_alerts()) == 1

        tracker.reset_thresholds("daily")

        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=0.05,
        )
        assert len(tracker.get_alerts()) == 2  # New alert triggered


class TestCostTrackerClearRecords:
    """Tests for CostTracker.clear_records."""

    def test_clear_all_records(self) -> None:
        """clear_records without date should clear all."""
        tracker = CostTracker()
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=1.0,
        )
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=2.0,
        )

        count = tracker.clear_records()

        assert count == 2
        assert tracker.get_total_cost() == 0.0

    def test_clear_records_before_date(self) -> None:
        """clear_records with date should clear older records."""
        tracker = CostTracker()
        now = datetime.now(UTC)

        # Add record "in the past" by directly manipulating
        tracker._records.append(
            CostRecord(
                timestamp=now - timedelta(hours=2),
                provider="claude", model="m", operation="o",
                input_tokens=0, output_tokens=0, cost_usd=1.0,
            )
        )
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=2.0,
        )

        count = tracker.clear_records(before=now - timedelta(hours=1))

        assert count == 1
        assert tracker.get_total_cost() == 2.0


class TestCostTrackerGetRecords:
    """Tests for CostTracker.get_records."""

    def test_get_records_by_provider(self) -> None:
        """get_records should filter by provider."""
        tracker = CostTracker()
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=1.0,
        )
        tracker.record(
            provider="openai", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=2.0,
        )

        records = tracker.get_records(provider="claude")

        assert len(records) == 1
        assert records[0].provider == "claude"

    def test_get_records_by_model(self) -> None:
        """get_records should filter by model."""
        tracker = CostTracker()
        tracker.record(
            provider="claude", model="sonnet", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=1.0,
        )
        tracker.record(
            provider="claude", model="opus", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=2.0,
        )

        records = tracker.get_records(model="sonnet")

        assert len(records) == 1
        assert records[0].model == "sonnet"


class TestCostTrackerToDict:
    """Tests for CostTracker.to_dict."""

    def test_to_dict_returns_state(self) -> None:
        """to_dict should return complete state."""
        tracker = CostTracker()
        tracker.set_daily_limit(100.0)
        tracker.add_threshold("daily", 50.0, AlertLevel.WARNING)
        tracker.record(
            provider="claude", model="m", operation="o",
            input_tokens=0, output_tokens=0, cost_usd=10.0,
        )

        state = tracker.to_dict()

        assert state["total_cost"] == 10.0
        assert state["limits"]["daily"]["hard_limit"] == 100.0
        assert state["record_count"] == 1


class TestGlobalCostTracker:
    """Tests for global cost tracker functions."""

    def test_get_cost_tracker_returns_same_instance(self) -> None:
        """get_cost_tracker should return same instance."""
        reset_cost_tracker()

        tracker1 = get_cost_tracker()
        tracker2 = get_cost_tracker()

        assert tracker1 is tracker2

    def test_reset_cost_tracker_clears_instance(self) -> None:
        """reset_cost_tracker should clear global instance."""
        tracker1 = get_cost_tracker()

        reset_cost_tracker()

        tracker2 = get_cost_tracker()
        assert tracker1 is not tracker2


class TestThreadSafety:
    """Tests for thread safety of CostTracker."""

    def test_concurrent_recording(self) -> None:
        """record should be thread-safe."""
        import threading

        tracker = CostTracker()
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for _ in range(10):
                    tracker.record(
                        provider="claude", model="m", operation="o",
                        input_tokens=100, output_tokens=50, cost_usd=0.01,
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert tracker.get_total_cost() == pytest.approx(0.50)  # 50 records * 0.01
