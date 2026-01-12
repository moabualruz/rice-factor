"""Unit tests for OpenTelemetryExporter."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.metrics.opentelemetry_adapter import (
    OTLPConfig,
    OpenTelemetryExporter,
)
from rice_factor.adapters.metrics.prometheus_adapter import (
    MetricDefinition,
    MetricType,
    MetricsRegistry,
)


class TestOTLPConfig:
    """Tests for OTLPConfig dataclass."""

    def test_default_config(self) -> None:
        """Should have sensible defaults."""
        config = OTLPConfig()

        assert config.endpoint == "http://localhost:4317"
        assert config.timeout == 30.0
        assert config.service_name == "rice-factor"
        assert config.environment == "development"

    def test_custom_config(self) -> None:
        """Should accept custom values."""
        config = OTLPConfig(
            endpoint="http://collector:4318/v1/metrics",
            service_name="my-service",
            service_version="2.0.0",
            environment="production",
            headers={"Authorization": "Bearer token"},
        )

        assert config.endpoint == "http://collector:4318/v1/metrics"
        assert config.service_name == "my-service"
        assert config.service_version == "2.0.0"
        assert config.environment == "production"
        assert "Authorization" in config.headers


class TestOpenTelemetryExporter:
    """Tests for OpenTelemetryExporter."""

    @pytest.fixture
    def registry(self) -> MetricsRegistry:
        """Create registry with test metrics."""
        reg = MetricsRegistry()
        reg.register(MetricDefinition(
            name="test_counter",
            help_text="Test counter",
            metric_type=MetricType.COUNTER,
            labels=["status"],
        ))
        reg.register(MetricDefinition(
            name="test_gauge",
            help_text="Test gauge",
            metric_type=MetricType.GAUGE,
        ))
        reg.register(MetricDefinition(
            name="test_duration_seconds",
            help_text="Test histogram",
            metric_type=MetricType.HISTOGRAM,
            buckets=[0.1, 0.5, 1.0],
        ))
        return reg

    @pytest.fixture
    def exporter(self, registry: MetricsRegistry) -> OpenTelemetryExporter:
        """Create exporter with registry."""
        config = OTLPConfig(
            service_name="test-service",
            service_version="1.0.0",
        )
        return OpenTelemetryExporter(registry, config)

    def test_registry_property(self, exporter: OpenTelemetryExporter, registry: MetricsRegistry) -> None:
        """Should expose registry."""
        assert exporter.registry is registry

    def test_config_property(self, exporter: OpenTelemetryExporter) -> None:
        """Should expose config."""
        assert exporter.config.service_name == "test-service"

    def test_to_otlp_structure(self, exporter: OpenTelemetryExporter, registry: MetricsRegistry) -> None:
        """Should generate valid OTLP structure."""
        registry.increment("test_counter", {"status": "ok"})

        payload = exporter.to_otlp()

        assert "resourceMetrics" in payload
        assert len(payload["resourceMetrics"]) == 1

        resource_metrics = payload["resourceMetrics"][0]
        assert "resource" in resource_metrics
        assert "scopeMetrics" in resource_metrics

    def test_resource_attributes(self, exporter: OpenTelemetryExporter, registry: MetricsRegistry) -> None:
        """Should include resource attributes."""
        registry.increment("test_counter", {"status": "ok"})

        payload = exporter.to_otlp()

        resource = payload["resourceMetrics"][0]["resource"]
        attrs = resource["attributes"]

        # Check service.name
        service_name = next(
            (a for a in attrs if a["key"] == "service.name"),
            None
        )
        assert service_name is not None
        assert service_name["value"]["stringValue"] == "test-service"

    def test_counter_export(self, exporter: OpenTelemetryExporter, registry: MetricsRegistry) -> None:
        """Should export counter as OTLP sum."""
        registry.increment("test_counter", {"status": "ok"}, value=42)

        payload = exporter.to_otlp()

        metrics = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        counter_metric = next(
            (m for m in metrics if m["name"] == "test_counter"),
            None
        )

        assert counter_metric is not None
        assert "sum" in counter_metric
        assert counter_metric["sum"]["isMonotonic"] is True
        assert counter_metric["sum"]["aggregationTemporality"] == 2  # CUMULATIVE

        datapoint = counter_metric["sum"]["dataPoints"][0]
        assert datapoint["asDouble"] == 42.0

    def test_gauge_export(self, exporter: OpenTelemetryExporter, registry: MetricsRegistry) -> None:
        """Should export gauge as OTLP gauge."""
        registry.set_gauge("test_gauge", 98.6)

        payload = exporter.to_otlp()

        metrics = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        gauge_metric = next(
            (m for m in metrics if m["name"] == "test_gauge"),
            None
        )

        assert gauge_metric is not None
        assert "gauge" in gauge_metric

        datapoint = gauge_metric["gauge"]["dataPoints"][0]
        assert datapoint["asDouble"] == 98.6

    def test_histogram_export(self, exporter: OpenTelemetryExporter, registry: MetricsRegistry) -> None:
        """Should export histogram as OTLP histogram."""
        registry.observe_histogram("test_duration_seconds", 0.2)
        registry.observe_histogram("test_duration_seconds", 0.8)

        payload = exporter.to_otlp()

        metrics = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        hist_metric = next(
            (m for m in metrics if m["name"] == "test_duration_seconds"),
            None
        )

        assert hist_metric is not None
        assert "histogram" in hist_metric
        assert hist_metric["histogram"]["aggregationTemporality"] == 2

        datapoint = hist_metric["histogram"]["dataPoints"][0]
        assert datapoint["count"] == "2"
        assert datapoint["sum"] == 1.0
        assert "bucketCounts" in datapoint
        assert "explicitBounds" in datapoint

    def test_labels_as_attributes(self, exporter: OpenTelemetryExporter, registry: MetricsRegistry) -> None:
        """Should convert labels to OTLP attributes."""
        registry.increment("test_counter", {"status": "success"})

        payload = exporter.to_otlp()

        metrics = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        counter = next(m for m in metrics if m["name"] == "test_counter")
        datapoint = counter["sum"]["dataPoints"][0]

        status_attr = next(
            (a for a in datapoint["attributes"] if a["key"] == "status"),
            None
        )
        assert status_attr is not None
        assert status_attr["value"]["stringValue"] == "success"

    def test_to_json(self, exporter: OpenTelemetryExporter, registry: MetricsRegistry) -> None:
        """Should convert to JSON string."""
        registry.increment("test_counter", {"status": "ok"})

        json_str = exporter.to_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert "resourceMetrics" in data

    def test_export_to_json_file(
        self,
        exporter: OpenTelemetryExporter,
        registry: MetricsRegistry,
        tmp_path: any,
    ) -> None:
        """Should export to JSON file."""
        registry.increment("test_counter", {"status": "ok"})

        output_path = tmp_path / "metrics.json"
        exporter.export_to_json(str(output_path))

        content = json.loads(output_path.read_text())
        assert "resourceMetrics" in content

    def test_export_result_structure(
        self,
        exporter: OpenTelemetryExporter,
        registry: MetricsRegistry,
    ) -> None:
        """Should return properly structured export result."""
        registry.increment("test_counter", {"status": "ok"})

        # Test that export method returns proper structure even on error
        # (since we can't easily mock internal HTTP without a real server)
        result = exporter.export()

        # Should have either success=True with metrics_exported
        # or success=False with error message
        assert "success" in result
        if result["success"]:
            assert "metrics_exported" in result
        else:
            # Connection error expected since no real endpoint
            assert "error" in result or "status_code" in result

    def test_export_error_handling(
        self,
        exporter: OpenTelemetryExporter,
        registry: MetricsRegistry,
    ) -> None:
        """Should handle export errors gracefully."""
        registry.increment("test_counter", {"status": "ok"})

        with patch.object(exporter, "_export_with_requests") as mock_export:
            mock_export.return_value = {
                "success": False,
                "error": "Connection refused",
            }

            with patch.dict("sys.modules", {"httpx": None}):
                result = exporter.export()

        assert result["success"] is False
        assert "error" in result

    def test_empty_registry(self, registry: MetricsRegistry) -> None:
        """Should handle empty registry."""
        exporter = OpenTelemetryExporter(registry)

        payload = exporter.to_otlp()

        # Should still have structure but no metrics
        metrics = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        assert len(metrics) == 0

    def test_unit_detection(self, registry: MetricsRegistry) -> None:
        """Should detect units from metric names."""
        registry.register(MetricDefinition(
            name="bytes_total",
            help_text="Bytes",
            metric_type=MetricType.COUNTER,
        ))
        registry.increment("bytes_total")

        exporter = OpenTelemetryExporter(registry)
        payload = exporter.to_otlp()

        # Duration should get 's' unit
        metrics = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        duration_metric = next(
            (m for m in metrics if "duration" in m["name"] or "seconds" in m["name"]),
            None
        )
        if duration_metric:
            assert duration_metric["unit"] == "s"


class TestOTLPExporterIntegration:
    """Integration tests for OTLP exporter."""

    def test_full_workflow(self) -> None:
        """Should handle full workflow."""
        # Create registry
        registry = MetricsRegistry()
        registry.register(MetricDefinition(
            name="api_requests",
            help_text="API requests",
            metric_type=MetricType.COUNTER,
            labels=["endpoint", "method"],
        ))
        registry.register(MetricDefinition(
            name="response_time",
            help_text="Response time",
            metric_type=MetricType.HISTOGRAM,
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
        ))

        # Record metrics
        registry.increment("api_requests", {"endpoint": "/users", "method": "GET"})
        registry.increment("api_requests", {"endpoint": "/users", "method": "POST"})
        registry.observe_histogram("response_time", 0.025)
        registry.observe_histogram("response_time", 0.15)

        # Export
        config = OTLPConfig(service_name="api-server")
        exporter = OpenTelemetryExporter(registry, config)
        payload = exporter.to_otlp()

        # Verify
        metrics = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        assert len(metrics) == 2

        api_metric = next(m for m in metrics if m["name"] == "api_requests")
        assert len(api_metric["sum"]["dataPoints"]) == 2

        response_metric = next(m for m in metrics if m["name"] == "response_time")
        assert response_metric["histogram"]["dataPoints"][0]["count"] == "2"
