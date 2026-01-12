"""Unit tests for PrometheusExporter and MetricsRegistry."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from rice_factor.adapters.metrics.prometheus_adapter import (
    DEFAULT_METRICS,
    HistogramValue,
    MetricDefinition,
    MetricType,
    MetricsRegistry,
    PrometheusExporter,
    create_default_registry,
)


class TestMetricType:
    """Tests for MetricType enum."""

    def test_metric_types_exist(self) -> None:
        """All expected metric types should exist."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"


class TestMetricDefinition:
    """Tests for MetricDefinition dataclass."""

    def test_create_definition(self) -> None:
        """Should create metric definition."""
        defn = MetricDefinition(
            name="test_metric",
            help_text="A test metric",
            metric_type=MetricType.COUNTER,
        )

        assert defn.name == "test_metric"
        assert defn.help_text == "A test metric"
        assert defn.metric_type == MetricType.COUNTER
        assert defn.labels == []

    def test_create_with_labels(self) -> None:
        """Should create definition with labels."""
        defn = MetricDefinition(
            name="test_metric",
            help_text="Test",
            metric_type=MetricType.COUNTER,
            labels=["provider", "status"],
        )

        assert defn.labels == ["provider", "status"]

    def test_create_histogram_with_buckets(self) -> None:
        """Should create histogram with custom buckets."""
        defn = MetricDefinition(
            name="test_duration",
            help_text="Duration",
            metric_type=MetricType.HISTOGRAM,
            buckets=[0.1, 0.5, 1.0, 5.0],
        )

        assert defn.buckets == [0.1, 0.5, 1.0, 5.0]

    def test_default_buckets(self) -> None:
        """Should have default buckets for histogram."""
        defn = MetricDefinition(
            name="test_duration",
            help_text="Duration",
            metric_type=MetricType.HISTOGRAM,
        )

        assert len(defn.buckets) > 0
        assert defn.buckets[0] < defn.buckets[-1]  # Sorted

    def test_empty_name_raises(self) -> None:
        """Should raise for empty name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            MetricDefinition(
                name="",
                help_text="Test",
                metric_type=MetricType.COUNTER,
            )

    def test_invalid_name_start_raises(self) -> None:
        """Should raise for invalid name start character."""
        with pytest.raises(ValueError, match="must start with"):
            MetricDefinition(
                name="123_metric",
                help_text="Test",
                metric_type=MetricType.COUNTER,
            )


class TestMetricsRegistry:
    """Tests for MetricsRegistry."""

    @pytest.fixture
    def registry(self) -> MetricsRegistry:
        """Create a fresh registry."""
        return MetricsRegistry()

    def test_register_metric(self, registry: MetricsRegistry) -> None:
        """Should register a metric."""
        defn = MetricDefinition(
            name="test_total",
            help_text="Test counter",
            metric_type=MetricType.COUNTER,
        )

        registry.register(defn)

        assert registry.get_definition("test_total") is not None

    def test_register_duplicate_raises(self, registry: MetricsRegistry) -> None:
        """Should raise for duplicate registration."""
        defn = MetricDefinition(
            name="test_total",
            help_text="Test",
            metric_type=MetricType.COUNTER,
        )

        registry.register(defn)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(defn)

    def test_increment_counter(self, registry: MetricsRegistry) -> None:
        """Should increment counter."""
        registry.register(MetricDefinition(
            name="test_total",
            help_text="Test",
            metric_type=MetricType.COUNTER,
        ))

        registry.increment("test_total")
        registry.increment("test_total", value=2.5)

        assert registry.get_counter("test_total") == 3.5

    def test_increment_with_labels(self, registry: MetricsRegistry) -> None:
        """Should increment counter with labels."""
        registry.register(MetricDefinition(
            name="requests_total",
            help_text="Requests",
            metric_type=MetricType.COUNTER,
            labels=["status"],
        ))

        registry.increment("requests_total", {"status": "success"})
        registry.increment("requests_total", {"status": "success"})
        registry.increment("requests_total", {"status": "error"})

        assert registry.get_counter("requests_total", {"status": "success"}) == 2.0
        assert registry.get_counter("requests_total", {"status": "error"}) == 1.0

    def test_increment_unregistered_raises(self, registry: MetricsRegistry) -> None:
        """Should raise for unregistered metric."""
        with pytest.raises(ValueError, match="not registered"):
            registry.increment("unknown_metric")

    def test_increment_non_counter_raises(self, registry: MetricsRegistry) -> None:
        """Should raise for non-counter metric."""
        registry.register(MetricDefinition(
            name="test_gauge",
            help_text="Test",
            metric_type=MetricType.GAUGE,
        ))

        with pytest.raises(ValueError, match="not a counter"):
            registry.increment("test_gauge")

    def test_set_gauge(self, registry: MetricsRegistry) -> None:
        """Should set gauge value."""
        registry.register(MetricDefinition(
            name="temperature",
            help_text="Temperature",
            metric_type=MetricType.GAUGE,
        ))

        registry.set_gauge("temperature", 72.5)

        assert registry.get_gauge("temperature") == 72.5

    def test_inc_dec_gauge(self, registry: MetricsRegistry) -> None:
        """Should increment and decrement gauge."""
        registry.register(MetricDefinition(
            name="active_connections",
            help_text="Connections",
            metric_type=MetricType.GAUGE,
        ))

        registry.set_gauge("active_connections", 10.0)
        registry.inc_gauge("active_connections", value=5.0)
        registry.dec_gauge("active_connections", value=3.0)

        assert registry.get_gauge("active_connections") == 12.0

    def test_observe_histogram(self, registry: MetricsRegistry) -> None:
        """Should observe histogram values."""
        registry.register(MetricDefinition(
            name="request_duration",
            help_text="Duration",
            metric_type=MetricType.HISTOGRAM,
            buckets=[0.1, 0.5, 1.0, 5.0],
        ))

        registry.observe_histogram("request_duration", 0.2)
        registry.observe_histogram("request_duration", 0.8)
        registry.observe_histogram("request_duration", 2.0)

        hist = registry.get_histogram("request_duration")

        assert hist is not None
        assert hist.count == 3
        assert hist.sum == 3.0
        # Each observation increments all buckets the value fits into
        # 0.2 fits in buckets 0.5, 1.0, 5.0
        # 0.8 fits in buckets 1.0, 5.0
        # 2.0 fits in bucket 5.0
        assert hist.buckets[0.1] == 0  # No values <= 0.1
        assert hist.buckets[0.5] == 1  # 0.2 <= 0.5
        assert hist.buckets[1.0] == 2  # 0.2, 0.8 <= 1.0
        assert hist.buckets[5.0] == 3  # All values <= 5.0

    def test_get_all_metrics(self, registry: MetricsRegistry) -> None:
        """Should get all metrics."""
        registry.register(MetricDefinition(
            name="counter_1",
            help_text="Counter",
            metric_type=MetricType.COUNTER,
        ))
        registry.register(MetricDefinition(
            name="gauge_1",
            help_text="Gauge",
            metric_type=MetricType.GAUGE,
        ))

        registry.increment("counter_1")
        registry.set_gauge("gauge_1", 42.0)

        all_metrics = registry.get_all_metrics()

        assert "counters" in all_metrics
        assert "gauges" in all_metrics
        assert "histograms" in all_metrics

    def test_clear(self, registry: MetricsRegistry) -> None:
        """Should clear metric values."""
        registry.register(MetricDefinition(
            name="test_counter",
            help_text="Test",
            metric_type=MetricType.COUNTER,
        ))
        registry.increment("test_counter", value=10.0)

        registry.clear()

        assert registry.get_counter("test_counter") == 0.0
        # Definition should still exist
        assert registry.get_definition("test_counter") is not None

    def test_thread_safety(self, registry: MetricsRegistry) -> None:
        """Should be thread-safe."""
        registry.register(MetricDefinition(
            name="concurrent_counter",
            help_text="Test",
            metric_type=MetricType.COUNTER,
        ))

        def increment_many() -> None:
            for _ in range(1000):
                registry.increment("concurrent_counter")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(increment_many) for _ in range(4)]
            for f in futures:
                f.result()

        assert registry.get_counter("concurrent_counter") == 4000.0


class TestPrometheusExporter:
    """Tests for PrometheusExporter."""

    @pytest.fixture
    def registry(self) -> MetricsRegistry:
        """Create registry with test metrics."""
        reg = MetricsRegistry()
        reg.register(MetricDefinition(
            name="test_requests_total",
            help_text="Total requests",
            metric_type=MetricType.COUNTER,
            labels=["status"],
        ))
        reg.register(MetricDefinition(
            name="test_temperature",
            help_text="Temperature gauge",
            metric_type=MetricType.GAUGE,
        ))
        reg.register(MetricDefinition(
            name="test_duration_seconds",
            help_text="Duration histogram",
            metric_type=MetricType.HISTOGRAM,
            buckets=[0.1, 0.5, 1.0],
        ))
        return reg

    def test_export_empty_registry(self, registry: MetricsRegistry) -> None:
        """Should export empty registry."""
        exporter = PrometheusExporter(registry)
        output = exporter.export()

        # Should have TYPE and HELP but no values
        assert "test_requests_total" in output
        assert "# TYPE" in output

    def test_export_counter(self, registry: MetricsRegistry) -> None:
        """Should export counter in Prometheus format."""
        registry.increment("test_requests_total", {"status": "ok"}, value=42)

        exporter = PrometheusExporter(registry)
        output = exporter.export()

        assert '# HELP test_requests_total Total requests' in output
        assert '# TYPE test_requests_total counter' in output
        assert 'test_requests_total{status="ok"} 42' in output

    def test_export_gauge(self, registry: MetricsRegistry) -> None:
        """Should export gauge in Prometheus format."""
        registry.set_gauge("test_temperature", 98.6)

        exporter = PrometheusExporter(registry)
        output = exporter.export()

        assert '# TYPE test_temperature gauge' in output
        assert 'test_temperature 98.6' in output

    def test_export_histogram(self, registry: MetricsRegistry) -> None:
        """Should export histogram in Prometheus format."""
        registry.observe_histogram("test_duration_seconds", 0.05)
        registry.observe_histogram("test_duration_seconds", 0.3)

        exporter = PrometheusExporter(registry)
        output = exporter.export()

        assert '# TYPE test_duration_seconds histogram' in output
        assert 'test_duration_seconds_bucket{le="0.1"}' in output
        assert 'test_duration_seconds_bucket{le="+Inf"}' in output
        assert 'test_duration_seconds_sum' in output
        assert 'test_duration_seconds_count' in output

    def test_export_with_namespace(self, registry: MetricsRegistry) -> None:
        """Should add namespace prefix."""
        registry.increment("test_requests_total", {"status": "ok"})

        exporter = PrometheusExporter(registry, namespace="myapp")
        output = exporter.export()

        assert 'myapp_test_requests_total' in output

    def test_export_with_timestamp(self, registry: MetricsRegistry) -> None:
        """Should include timestamp when enabled."""
        registry.increment("test_requests_total", {"status": "ok"})

        exporter = PrometheusExporter(registry, include_timestamp=True)
        output = exporter.export()

        # Should have timestamp at end of line (13-digit unix ms)
        lines = [l for l in output.split("\n") if "test_requests_total{" in l]
        assert len(lines) > 0
        parts = lines[0].split()
        assert len(parts) == 3  # metric value timestamp

    def test_export_to_file(self, registry: MetricsRegistry, tmp_path: any) -> None:
        """Should export to file."""
        registry.increment("test_requests_total", {"status": "ok"})

        exporter = PrometheusExporter(registry)
        output_path = tmp_path / "metrics.prom"
        exporter.export_to_file(str(output_path))

        content = output_path.read_text()
        assert "test_requests_total" in content


class TestDefaultMetrics:
    """Tests for default metrics."""

    def test_default_metrics_exist(self) -> None:
        """Should have default metrics defined."""
        assert len(DEFAULT_METRICS) > 0

    def test_default_metrics_are_valid(self) -> None:
        """All default metrics should have valid definitions."""
        for metric in DEFAULT_METRICS:
            assert metric.name.startswith("rice_factor_")
            assert metric.help_text
            assert metric.metric_type in MetricType

    def test_create_default_registry(self) -> None:
        """Should create registry with default metrics."""
        registry = create_default_registry()

        # Spot check some expected metrics
        assert registry.get_definition("rice_factor_llm_requests_total") is not None
        assert registry.get_definition("rice_factor_artifacts_total") is not None
        assert registry.get_definition("rice_factor_cost_dollars") is not None

    def test_default_registry_is_usable(self) -> None:
        """Should be able to use default registry."""
        registry = create_default_registry()

        # Should be able to record metrics
        registry.increment(
            "rice_factor_llm_requests_total",
            {"provider": "claude", "model": "opus", "status": "success"},
        )
        registry.observe_histogram(
            "rice_factor_llm_request_duration_seconds",
            2.5,
            {"provider": "claude", "model": "opus"},
        )

        assert registry.get_counter(
            "rice_factor_llm_requests_total",
            {"provider": "claude", "model": "opus", "status": "success"},
        ) == 1.0
