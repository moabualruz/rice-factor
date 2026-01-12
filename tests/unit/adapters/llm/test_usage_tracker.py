"""Unit tests for UsageTracker."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from rice_factor.adapters.llm.usage_tracker import (
    ProviderStats,
    UsageRecord,
    UsageTracker,
    get_usage_tracker,
    reset_usage_tracker,
)


class TestUsageRecord:
    """Tests for UsageRecord dataclass."""

    def test_default_values(self) -> None:
        """UsageRecord should have sensible defaults."""
        record = UsageRecord(
            timestamp=datetime.now(timezone.utc),
            provider="test",
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=150.0,
            cost_usd=0.01,
        )
        assert record.success is True
        assert record.error is None

    def test_with_error(self) -> None:
        """UsageRecord should accept error info."""
        record = UsageRecord(
            timestamp=datetime.now(timezone.utc),
            provider="test",
            model="test-model",
            input_tokens=100,
            output_tokens=0,
            latency_ms=50.0,
            cost_usd=0.0,
            success=False,
            error="Timeout",
        )
        assert record.success is False
        assert record.error == "Timeout"


class TestProviderStats:
    """Tests for ProviderStats dataclass."""

    def test_default_values(self) -> None:
        """ProviderStats should have zero defaults."""
        stats = ProviderStats(provider="test")
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.total_cost_usd == 0.0


class TestUsageTrackerRecord:
    """Tests for UsageTracker.record method."""

    def test_record_calculates_tokens(self) -> None:
        """record should calculate token counts."""
        tracker = UsageTracker()

        record = tracker.record(
            provider="claude",
            model="claude-sonnet",
            prompt="Hello world",  # ~3 tokens
            response="Hi there!",  # ~2 tokens
            latency_ms=100.0,
        )

        assert record.input_tokens > 0
        assert record.output_tokens > 0

    def test_record_calculates_cost(self) -> None:
        """record should calculate cost from token counts."""
        tracker = UsageTracker()

        record = tracker.record(
            provider="claude",
            model="claude-sonnet",
            prompt="a" * 4000,  # ~1000 tokens
            response="b" * 2000,  # ~500 tokens
            latency_ms=100.0,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.02,
        )

        # 1000 input * 0.01/1000 + 500 output * 0.02/1000 = 0.01 + 0.01 = 0.02
        assert record.cost_usd > 0

    def test_record_sets_timestamp(self) -> None:
        """record should set current timestamp."""
        tracker = UsageTracker()
        before = datetime.now(timezone.utc)

        record = tracker.record(
            provider="test",
            model="test",
            prompt="test",
            response="test",
            latency_ms=100.0,
        )

        after = datetime.now(timezone.utc)
        assert before <= record.timestamp <= after


class TestUsageTrackerRecordWithTokens:
    """Tests for UsageTracker.record_with_tokens method."""

    def test_uses_provided_tokens(self) -> None:
        """record_with_tokens should use provided token counts."""
        tracker = UsageTracker()

        record = tracker.record_with_tokens(
            provider="claude",
            model="claude-sonnet",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=100.0,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        )

        assert record.input_tokens == 1000
        assert record.output_tokens == 500
        # 1000 * 0.003/1000 + 500 * 0.015/1000 = 0.003 + 0.0075 = 0.0105
        assert abs(record.cost_usd - 0.0105) < 0.0001


class TestUsageTrackerCountTokens:
    """Tests for UsageTracker.count_tokens method."""

    def test_counts_tokens_approximately(self) -> None:
        """count_tokens should estimate token count."""
        tracker = UsageTracker()

        # Empty string
        assert tracker.count_tokens("") == 1  # min 1

        # Short text (~4 chars per token)
        assert tracker.count_tokens("Hello World!") == 3

        # Longer text
        assert tracker.count_tokens("a" * 100) == 25


class TestUsageTrackerTotalCost:
    """Tests for UsageTracker.total_cost method."""

    def test_total_cost_empty(self) -> None:
        """total_cost should return 0 when empty."""
        tracker = UsageTracker()
        assert tracker.total_cost() == 0.0

    def test_total_cost_sums_all_records(self) -> None:
        """total_cost should sum all record costs."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="claude",
            model="model1",
            input_tokens=1000,
            output_tokens=0,
            latency_ms=100.0,
            cost_per_1k_input=0.01,
        )
        tracker.record_with_tokens(
            provider="openai",
            model="model2",
            input_tokens=1000,
            output_tokens=0,
            latency_ms=100.0,
            cost_per_1k_input=0.02,
        )

        assert abs(tracker.total_cost() - 0.03) < 0.0001


class TestUsageTrackerTotalTokens:
    """Tests for UsageTracker.total_tokens method."""

    def test_total_tokens_empty(self) -> None:
        """total_tokens should return (0, 0) when empty."""
        tracker = UsageTracker()
        assert tracker.total_tokens() == (0, 0)

    def test_total_tokens_sums_all_records(self) -> None:
        """total_tokens should sum input and output separately."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="test",
            model="model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=100.0,
        )
        tracker.record_with_tokens(
            provider="test",
            model="model",
            input_tokens=200,
            output_tokens=100,
            latency_ms=100.0,
        )

        assert tracker.total_tokens() == (300, 150)


class TestUsageTrackerByProvider:
    """Tests for UsageTracker.by_provider method."""

    def test_by_provider_empty(self) -> None:
        """by_provider should return empty dict when no records."""
        tracker = UsageTracker()
        assert tracker.by_provider() == {}

    def test_by_provider_groups_by_provider(self) -> None:
        """by_provider should group stats by provider."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="claude",
            model="model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=100.0,
            cost_per_1k_input=0.01,
        )
        tracker.record_with_tokens(
            provider="ollama",
            model="model",
            input_tokens=200,
            output_tokens=100,
            latency_ms=200.0,
        )

        stats = tracker.by_provider()

        assert "claude" in stats
        assert "ollama" in stats
        assert stats["claude"].total_requests == 1
        assert stats["ollama"].total_requests == 1

    def test_by_provider_calculates_stats(self) -> None:
        """by_provider should calculate aggregate stats correctly."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="claude",
            model="model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=100.0,
        )
        tracker.record_with_tokens(
            provider="claude",
            model="model",
            input_tokens=200,
            output_tokens=100,
            latency_ms=200.0,
        )

        stats = tracker.by_provider()["claude"]

        assert stats.total_requests == 2
        assert stats.successful_requests == 2
        assert stats.total_input_tokens == 300
        assert stats.total_output_tokens == 150
        assert stats.avg_latency_ms == 150.0
        assert stats.min_latency_ms == 100.0
        assert stats.max_latency_ms == 200.0


class TestUsageTrackerByModel:
    """Tests for UsageTracker.by_model method."""

    def test_by_model_groups_by_model(self) -> None:
        """by_model should group costs by model."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="claude",
            model="model-a",
            input_tokens=1000,
            output_tokens=0,
            latency_ms=100.0,
            cost_per_1k_input=0.01,
        )
        tracker.record_with_tokens(
            provider="claude",
            model="model-b",
            input_tokens=1000,
            output_tokens=0,
            latency_ms=100.0,
            cost_per_1k_input=0.02,
        )

        by_model = tracker.by_model()

        assert abs(by_model["model-a"] - 0.01) < 0.0001
        assert abs(by_model["model-b"] - 0.02) < 0.0001


class TestUsageTrackerGetRecords:
    """Tests for UsageTracker.get_records method."""

    def test_get_records_returns_all(self) -> None:
        """get_records should return all records when no filters."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="claude",
            model="model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=100.0,
        )
        tracker.record_with_tokens(
            provider="ollama",
            model="model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=100.0,
        )

        records = tracker.get_records()

        assert len(records) == 2

    def test_get_records_filters_by_provider(self) -> None:
        """get_records should filter by provider."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="claude",
            model="model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=100.0,
        )
        tracker.record_with_tokens(
            provider="ollama",
            model="model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=100.0,
        )

        records = tracker.get_records(provider="claude")

        assert len(records) == 1
        assert records[0].provider == "claude"


class TestUsageTrackerClear:
    """Tests for UsageTracker.clear method."""

    def test_clear_removes_all_records(self) -> None:
        """clear should remove all records."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="test",
            model="model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=100.0,
        )

        count = tracker.clear()

        assert count == 1
        assert len(tracker.get_records()) == 0


class TestUsageTrackerExportPrometheus:
    """Tests for UsageTracker.export_prometheus method."""

    def test_export_prometheus_format(self) -> None:
        """export_prometheus should return Prometheus format."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="claude",
            model="model",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=100.0,
            cost_per_1k_input=0.01,
        )

        output = tracker.export_prometheus()

        assert "llm_cost_usd" in output
        assert "llm_tokens_total" in output
        assert "llm_requests_total" in output
        assert "llm_latency_ms" in output
        assert 'provider="claude"' in output


class TestUsageTrackerExportJson:
    """Tests for UsageTracker.export_json method."""

    def test_export_json_structure(self) -> None:
        """export_json should return expected structure."""
        tracker = UsageTracker()

        tracker.record_with_tokens(
            provider="claude",
            model="model",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=100.0,
            cost_per_1k_input=0.01,
        )

        data = tracker.export_json()

        assert "total_cost_usd" in data
        assert "total_input_tokens" in data
        assert "total_output_tokens" in data
        assert "by_provider" in data
        assert "by_model" in data
        assert "record_count" in data
        assert data["record_count"] == 1


class TestGlobalTracker:
    """Tests for global tracker functions."""

    def test_get_usage_tracker_returns_same_instance(self) -> None:
        """get_usage_tracker should return same instance."""
        reset_usage_tracker()

        tracker1 = get_usage_tracker()
        tracker2 = get_usage_tracker()

        assert tracker1 is tracker2

    def test_reset_usage_tracker_clears_instance(self) -> None:
        """reset_usage_tracker should clear global instance."""
        tracker1 = get_usage_tracker()

        reset_usage_tracker()

        tracker2 = get_usage_tracker()
        assert tracker1 is not tracker2
