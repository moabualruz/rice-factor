"""OpenTelemetry metrics exporter adapter.

This module provides the OpenTelemetryExporter for exporting metrics
using the OpenTelemetry Protocol (OTLP).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from rice_factor.adapters.metrics.prometheus_adapter import (
    MetricType,
    MetricsRegistry,
)


@dataclass
class OTLPConfig:
    """Configuration for OTLP export.

    Attributes:
        endpoint: OTLP endpoint URL.
        headers: Optional headers for authentication.
        timeout: Request timeout in seconds.
        export_interval: Interval between exports in seconds.
        service_name: Service name for resource attributes.
        service_version: Service version.
        environment: Deployment environment.
    """

    endpoint: str = "http://localhost:4317"
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    export_interval: float = 60.0
    service_name: str = "rice-factor"
    service_version: str = "1.0.0"
    environment: str = "development"


@dataclass
class OTLPMetricPoint:
    """A single metric data point.

    Attributes:
        name: Metric name.
        description: Metric description.
        unit: Unit of measurement.
        value: Metric value.
        attributes: Key-value attributes.
        timestamp_ns: Unix timestamp in nanoseconds.
        metric_type: Type of metric.
    """

    name: str
    description: str
    unit: str
    value: float | dict[str, Any]
    attributes: dict[str, str]
    timestamp_ns: int
    metric_type: str


class OpenTelemetryExporter:
    """OpenTelemetry metrics exporter.

    Exports metrics using OTLP format. Supports both OTLP/HTTP and
    OTLP/gRPC endpoints (via JSON over HTTP for simplicity).

    Example:
        >>> registry = MetricsRegistry()
        >>> config = OTLPConfig(endpoint="http://collector:4318/v1/metrics")
        >>> exporter = OpenTelemetryExporter(registry, config)
        >>> exporter.export()
    """

    def __init__(
        self,
        registry: MetricsRegistry,
        config: OTLPConfig | None = None,
    ) -> None:
        """Initialize the exporter.

        Args:
            registry: MetricsRegistry to export from.
            config: OTLP configuration.
        """
        self._registry = registry
        self._config = config or OTLPConfig()
        self._last_export: float = 0.0

    @property
    def registry(self) -> MetricsRegistry:
        """Get the metrics registry."""
        return self._registry

    @property
    def config(self) -> OTLPConfig:
        """Get the OTLP configuration."""
        return self._config

    def _get_resource(self) -> dict[str, Any]:
        """Build OTLP resource attributes.

        Returns:
            Resource object with attributes.
        """
        return {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": self._config.service_name}},
                {"key": "service.version", "value": {"stringValue": self._config.service_version}},
                {"key": "deployment.environment", "value": {"stringValue": self._config.environment}},
            ]
        }

    def _parse_labels(self, key: str) -> dict[str, str]:
        """Parse labels from storage key.

        Args:
            key: Storage key in format "k1=v1|k2=v2".

        Returns:
            Label dictionary.
        """
        if not key:
            return {}
        labels = {}
        for part in key.split("|"):
            if "=" in part:
                k, v = part.split("=", 1)
                labels[k] = v
        return labels

    def _labels_to_attributes(self, labels: dict[str, str]) -> list[dict[str, Any]]:
        """Convert labels to OTLP attributes.

        Args:
            labels: Label name-value pairs.

        Returns:
            List of OTLP attribute objects.
        """
        return [
            {"key": k, "value": {"stringValue": v}}
            for k, v in sorted(labels.items())
        ]

    def _build_counter_datapoint(
        self,
        value: float,
        attributes: list[dict[str, Any]],
        timestamp_ns: int,
        start_timestamp_ns: int,
    ) -> dict[str, Any]:
        """Build a counter data point.

        Args:
            value: Counter value.
            attributes: OTLP attributes.
            timestamp_ns: Current timestamp.
            start_timestamp_ns: Start timestamp.

        Returns:
            OTLP counter data point.
        """
        return {
            "attributes": attributes,
            "startTimeUnixNano": str(start_timestamp_ns),
            "timeUnixNano": str(timestamp_ns),
            "asDouble": value,
        }

    def _build_gauge_datapoint(
        self,
        value: float,
        attributes: list[dict[str, Any]],
        timestamp_ns: int,
    ) -> dict[str, Any]:
        """Build a gauge data point.

        Args:
            value: Gauge value.
            attributes: OTLP attributes.
            timestamp_ns: Current timestamp.

        Returns:
            OTLP gauge data point.
        """
        return {
            "attributes": attributes,
            "timeUnixNano": str(timestamp_ns),
            "asDouble": value,
        }

    def _build_histogram_datapoint(
        self,
        hist: Any,
        attributes: list[dict[str, Any]],
        timestamp_ns: int,
        start_timestamp_ns: int,
        buckets: list[float],
    ) -> dict[str, Any]:
        """Build a histogram data point.

        Args:
            hist: HistogramValue object.
            attributes: OTLP attributes.
            timestamp_ns: Current timestamp.
            start_timestamp_ns: Start timestamp.
            buckets: Bucket boundaries.

        Returns:
            OTLP histogram data point.
        """
        # Calculate bucket counts
        bucket_counts = []
        cumulative = 0
        for bucket in sorted(buckets):
            bucket_count = hist.buckets.get(bucket, 0)
            bucket_counts.append(cumulative + bucket_count)
            cumulative += bucket_count

        return {
            "attributes": attributes,
            "startTimeUnixNano": str(start_timestamp_ns),
            "timeUnixNano": str(timestamp_ns),
            "count": str(hist.count),
            "sum": hist.sum,
            "bucketCounts": [str(c) for c in bucket_counts],
            "explicitBounds": buckets,
        }

    def to_otlp(self) -> dict[str, Any]:
        """Convert metrics to OTLP format.

        Returns:
            OTLP metrics request payload.
        """
        timestamp_ns = int(time.time() * 1_000_000_000)
        # Use last export time as start time, or 1 hour ago if first export
        start_timestamp_ns = int(
            self._last_export * 1_000_000_000
            if self._last_export > 0
            else (time.time() - 3600) * 1_000_000_000
        )

        metrics: list[dict[str, Any]] = []

        # Export counters
        for name, values in self._registry._counters.items():
            definition = self._registry.get_definition(name)
            if definition and values:
                datapoints = []
                for key, value in values.items():
                    labels = self._parse_labels(key)
                    attributes = self._labels_to_attributes(labels)
                    datapoints.append(
                        self._build_counter_datapoint(
                            value, attributes, timestamp_ns, start_timestamp_ns
                        )
                    )

                metrics.append({
                    "name": name,
                    "description": definition.help_text,
                    "unit": "1",
                    "sum": {
                        "dataPoints": datapoints,
                        "aggregationTemporality": 2,  # CUMULATIVE
                        "isMonotonic": True,
                    },
                })

        # Export gauges
        for name, values in self._registry._gauges.items():
            definition = self._registry.get_definition(name)
            if definition and values:
                datapoints = []
                for key, value in values.items():
                    labels = self._parse_labels(key)
                    attributes = self._labels_to_attributes(labels)
                    datapoints.append(
                        self._build_gauge_datapoint(value, attributes, timestamp_ns)
                    )

                metrics.append({
                    "name": name,
                    "description": definition.help_text,
                    "unit": "1",
                    "gauge": {
                        "dataPoints": datapoints,
                    },
                })

        # Export histograms
        for name, values in self._registry._histograms.items():
            definition = self._registry.get_definition(name)
            if definition and values:
                datapoints = []
                for key, hist in values.items():
                    attributes = self._labels_to_attributes(hist.labels)
                    datapoints.append(
                        self._build_histogram_datapoint(
                            hist,
                            attributes,
                            timestamp_ns,
                            start_timestamp_ns,
                            definition.buckets,
                        )
                    )

                metrics.append({
                    "name": name,
                    "description": definition.help_text,
                    "unit": "s" if "seconds" in name or "duration" in name else "1",
                    "histogram": {
                        "dataPoints": datapoints,
                        "aggregationTemporality": 2,  # CUMULATIVE
                    },
                })

        return {
            "resourceMetrics": [
                {
                    "resource": self._get_resource(),
                    "scopeMetrics": [
                        {
                            "scope": {
                                "name": "rice_factor",
                                "version": self._config.service_version,
                            },
                            "metrics": metrics,
                        }
                    ],
                }
            ]
        }

    def export(self) -> dict[str, Any]:
        """Export metrics to OTLP endpoint.

        Returns:
            Response from the OTLP endpoint or error dict.
        """
        payload = self.to_otlp()
        self._last_export = time.time()

        try:
            import httpx
        except ImportError:
            try:
                import requests

                return self._export_with_requests(payload)
            except ImportError:
                return {
                    "success": False,
                    "error": "Neither httpx nor requests is installed",
                }

        headers = {
            "Content-Type": "application/json",
            **self._config.headers,
        }

        try:
            with httpx.Client(timeout=self._config.timeout) as client:
                response = client.post(
                    self._config.endpoint,
                    json=payload,
                    headers=headers,
                )
                return {
                    "success": response.is_success,
                    "status_code": response.status_code,
                    "metrics_exported": len(payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]),
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _export_with_requests(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Export using requests library.

        Args:
            payload: OTLP payload.

        Returns:
            Response dict.
        """
        import requests

        headers = {
            "Content-Type": "application/json",
            **self._config.headers,
        }

        try:
            response = requests.post(
                self._config.endpoint,
                json=payload,
                headers=headers,
                timeout=self._config.timeout,
            )
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "metrics_exported": len(payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def export_to_json(self, path: str) -> None:
        """Export metrics to a JSON file.

        Args:
            path: File path to write to.
        """
        payload = self.to_otlp()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def to_json(self) -> str:
        """Convert metrics to JSON string.

        Returns:
            JSON string of OTLP payload.
        """
        return json.dumps(self.to_otlp(), indent=2)
