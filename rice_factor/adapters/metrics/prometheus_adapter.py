"""Prometheus metrics exporter adapter.

This module provides the PrometheusExporter for exporting metrics
in Prometheus exposition format.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class MetricType(Enum):
    """Types of Prometheus metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricDefinition:
    """Definition of a metric.

    Attributes:
        name: Metric name (must match [a-zA-Z_:][a-zA-Z0-9_:]*).
        help_text: Description of the metric.
        metric_type: Type of metric.
        labels: Label names for this metric.
        buckets: Bucket boundaries for histograms.
    """

    name: str
    help_text: str
    metric_type: MetricType
    labels: list[str] = field(default_factory=list)
    buckets: list[float] = field(default_factory=lambda: [
        0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10
    ])

    def __post_init__(self) -> None:
        """Validate metric name."""
        if not self.name:
            raise ValueError("Metric name cannot be empty")
        if not self.name[0].isalpha() and self.name[0] not in "_:":
            raise ValueError(
                f"Metric name must start with letter, underscore, or colon: {self.name}"
            )


@dataclass
class MetricValue:
    """Value of a metric with labels.

    Attributes:
        labels: Label values for this metric instance.
        value: Current value.
        timestamp: Unix timestamp in milliseconds (optional).
    """

    labels: dict[str, str]
    value: float
    timestamp: int | None = None


@dataclass
class HistogramValue:
    """Histogram metric value.

    Attributes:
        labels: Label values for this metric instance.
        buckets: Bucket counts keyed by upper bound.
        sum: Sum of all observed values.
        count: Total count of observations.
    """

    labels: dict[str, str]
    buckets: dict[float, int]
    sum: float
    count: int


class MetricsRegistry:
    """Registry for metrics definitions and values.

    Thread-safe registry that stores metric definitions and their
    current values.

    Example:
        >>> registry = MetricsRegistry()
        >>> registry.register(MetricDefinition(
        ...     name="rice_factor_requests_total",
        ...     help_text="Total requests",
        ...     metric_type=MetricType.COUNTER,
        ...     labels=["provider", "status"],
        ... ))
        >>> registry.increment("rice_factor_requests_total", {"provider": "claude", "status": "success"})
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._definitions: dict[str, MetricDefinition] = {}
        self._counters: dict[str, dict[str, float]] = {}
        self._gauges: dict[str, dict[str, float]] = {}
        self._histograms: dict[str, dict[str, HistogramValue]] = {}
        self._lock = threading.RLock()

    def register(self, definition: MetricDefinition) -> None:
        """Register a metric definition.

        Args:
            definition: Metric definition to register.

        Raises:
            ValueError: If metric with same name already exists.
        """
        with self._lock:
            if definition.name in self._definitions:
                raise ValueError(f"Metric already registered: {definition.name}")

            self._definitions[definition.name] = definition

            # Initialize storage based on type
            if definition.metric_type == MetricType.COUNTER:
                self._counters[definition.name] = {}
            elif definition.metric_type == MetricType.GAUGE:
                self._gauges[definition.name] = {}
            elif definition.metric_type == MetricType.HISTOGRAM:
                self._histograms[definition.name] = {}

    def get_definition(self, name: str) -> MetricDefinition | None:
        """Get a metric definition.

        Args:
            name: Metric name.

        Returns:
            MetricDefinition or None if not found.
        """
        with self._lock:
            return self._definitions.get(name)

    def _label_key(self, labels: dict[str, str]) -> str:
        """Create a key from label values.

        Args:
            labels: Label name-value pairs.

        Returns:
            String key for storage.
        """
        return "|".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def increment(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        value: float = 1.0,
    ) -> None:
        """Increment a counter.

        Args:
            name: Metric name.
            labels: Label values.
            value: Amount to increment by.

        Raises:
            ValueError: If metric is not a counter.
        """
        labels = labels or {}
        with self._lock:
            definition = self._definitions.get(name)
            if not definition:
                raise ValueError(f"Metric not registered: {name}")
            if definition.metric_type != MetricType.COUNTER:
                raise ValueError(f"Metric {name} is not a counter")

            key = self._label_key(labels)
            current = self._counters[name].get(key, 0.0)
            self._counters[name][key] = current + value

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge value.

        Args:
            name: Metric name.
            value: New value.
            labels: Label values.

        Raises:
            ValueError: If metric is not a gauge.
        """
        labels = labels or {}
        with self._lock:
            definition = self._definitions.get(name)
            if not definition:
                raise ValueError(f"Metric not registered: {name}")
            if definition.metric_type != MetricType.GAUGE:
                raise ValueError(f"Metric {name} is not a gauge")

            key = self._label_key(labels)
            self._gauges[name][key] = value

    def inc_gauge(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        value: float = 1.0,
    ) -> None:
        """Increment a gauge.

        Args:
            name: Metric name.
            labels: Label values.
            value: Amount to increment by.
        """
        labels = labels or {}
        with self._lock:
            definition = self._definitions.get(name)
            if not definition:
                raise ValueError(f"Metric not registered: {name}")
            if definition.metric_type != MetricType.GAUGE:
                raise ValueError(f"Metric {name} is not a gauge")

            key = self._label_key(labels)
            current = self._gauges[name].get(key, 0.0)
            self._gauges[name][key] = current + value

    def dec_gauge(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        value: float = 1.0,
    ) -> None:
        """Decrement a gauge.

        Args:
            name: Metric name.
            labels: Label values.
            value: Amount to decrement by.
        """
        self.inc_gauge(name, labels, -value)

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Observe a value for a histogram.

        Args:
            name: Metric name.
            value: Observed value.
            labels: Label values.

        Raises:
            ValueError: If metric is not a histogram.
        """
        labels = labels or {}
        with self._lock:
            definition = self._definitions.get(name)
            if not definition:
                raise ValueError(f"Metric not registered: {name}")
            if definition.metric_type != MetricType.HISTOGRAM:
                raise ValueError(f"Metric {name} is not a histogram")

            key = self._label_key(labels)
            if key not in self._histograms[name]:
                # Initialize histogram
                self._histograms[name][key] = HistogramValue(
                    labels=labels,
                    buckets={b: 0 for b in definition.buckets},
                    sum=0.0,
                    count=0,
                )

            hist = self._histograms[name][key]
            hist.sum += value
            hist.count += 1

            # Update bucket counts
            for bucket in definition.buckets:
                if value <= bucket:
                    hist.buckets[bucket] += 1

    def get_counter(
        self, name: str, labels: dict[str, str] | None = None
    ) -> float:
        """Get counter value.

        Args:
            name: Metric name.
            labels: Label values.

        Returns:
            Current counter value.
        """
        labels = labels or {}
        with self._lock:
            key = self._label_key(labels)
            return self._counters.get(name, {}).get(key, 0.0)

    def get_gauge(
        self, name: str, labels: dict[str, str] | None = None
    ) -> float:
        """Get gauge value.

        Args:
            name: Metric name.
            labels: Label values.

        Returns:
            Current gauge value.
        """
        labels = labels or {}
        with self._lock:
            key = self._label_key(labels)
            return self._gauges.get(name, {}).get(key, 0.0)

    def get_histogram(
        self, name: str, labels: dict[str, str] | None = None
    ) -> HistogramValue | None:
        """Get histogram value.

        Args:
            name: Metric name.
            labels: Label values.

        Returns:
            HistogramValue or None if not found.
        """
        labels = labels or {}
        with self._lock:
            key = self._label_key(labels)
            return self._histograms.get(name, {}).get(key)

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metric values.

        Returns:
            Dictionary with all metric values.
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: {k: vars(v) for k, v in values.items()}
                    for name, values in self._histograms.items()
                },
            }

    def clear(self) -> None:
        """Clear all metric values (but keep definitions)."""
        with self._lock:
            for name in self._counters:
                self._counters[name] = {}
            for name in self._gauges:
                self._gauges[name] = {}
            for name in self._histograms:
                self._histograms[name] = {}


# Default Rice-Factor metrics
DEFAULT_METRICS = [
    MetricDefinition(
        name="rice_factor_llm_requests_total",
        help_text="Total LLM API requests",
        metric_type=MetricType.COUNTER,
        labels=["provider", "model", "status"],
    ),
    MetricDefinition(
        name="rice_factor_llm_tokens_total",
        help_text="Total tokens consumed",
        metric_type=MetricType.COUNTER,
        labels=["provider", "model", "direction"],
    ),
    MetricDefinition(
        name="rice_factor_llm_request_duration_seconds",
        help_text="LLM request duration in seconds",
        metric_type=MetricType.HISTOGRAM,
        labels=["provider", "model"],
        buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120],
    ),
    MetricDefinition(
        name="rice_factor_artifacts_total",
        help_text="Total artifacts by type and status",
        metric_type=MetricType.COUNTER,
        labels=["artifact_type", "status"],
    ),
    MetricDefinition(
        name="rice_factor_artifacts_active",
        help_text="Currently active artifacts",
        metric_type=MetricType.GAUGE,
        labels=["artifact_type", "status"],
    ),
    MetricDefinition(
        name="rice_factor_cost_dollars",
        help_text="Cumulative cost in dollars",
        metric_type=MetricType.COUNTER,
        labels=["provider", "model"],
    ),
    MetricDefinition(
        name="rice_factor_rate_limit_hits_total",
        help_text="Total rate limit hits",
        metric_type=MetricType.COUNTER,
        labels=["provider", "limit_type"],
    ),
    MetricDefinition(
        name="rice_factor_validation_runs_total",
        help_text="Total validation runs",
        metric_type=MetricType.COUNTER,
        labels=["validator", "result"],
    ),
    MetricDefinition(
        name="rice_factor_build_duration_seconds",
        help_text="Build duration in seconds",
        metric_type=MetricType.HISTOGRAM,
        labels=["result"],
        buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    ),
]


class PrometheusExporter:
    """Prometheus metrics exporter.

    Exports metrics in Prometheus text exposition format.

    Example:
        >>> registry = MetricsRegistry()
        >>> exporter = PrometheusExporter(registry)
        >>> output = exporter.export()
    """

    def __init__(
        self,
        registry: MetricsRegistry,
        namespace: str = "",
        include_timestamp: bool = False,
    ) -> None:
        """Initialize the exporter.

        Args:
            registry: MetricsRegistry to export from.
            namespace: Optional prefix for all metric names.
            include_timestamp: Whether to include timestamps in output.
        """
        self._registry = registry
        self._namespace = namespace
        self._include_timestamp = include_timestamp

    @property
    def registry(self) -> MetricsRegistry:
        """Get the metrics registry."""
        return self._registry

    def _format_name(self, name: str) -> str:
        """Format metric name with namespace.

        Args:
            name: Base metric name.

        Returns:
            Formatted name with namespace.
        """
        if self._namespace:
            return f"{self._namespace}_{name}"
        return name

    def _format_labels(self, labels: dict[str, str]) -> str:
        """Format labels for Prometheus output.

        Args:
            labels: Label name-value pairs.

        Returns:
            Formatted labels string.
        """
        if not labels:
            return ""
        parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(parts) + "}"

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

    def export(self) -> str:
        """Export all metrics in Prometheus text format.

        Returns:
            Metrics in Prometheus exposition format.
        """
        lines: list[str] = []
        timestamp = int(time.time() * 1000) if self._include_timestamp else None

        # Export counters
        for name, values in self._registry._counters.items():
            definition = self._registry.get_definition(name)
            if definition:
                formatted_name = self._format_name(name)
                lines.append(f"# HELP {formatted_name} {definition.help_text}")
                lines.append(f"# TYPE {formatted_name} counter")

                for key, value in values.items():
                    labels = self._parse_labels(key)
                    label_str = self._format_labels(labels)
                    if timestamp:
                        lines.append(f"{formatted_name}{label_str} {value} {timestamp}")
                    else:
                        lines.append(f"{formatted_name}{label_str} {value}")

        # Export gauges
        for name, values in self._registry._gauges.items():
            definition = self._registry.get_definition(name)
            if definition:
                formatted_name = self._format_name(name)
                lines.append(f"# HELP {formatted_name} {definition.help_text}")
                lines.append(f"# TYPE {formatted_name} gauge")

                for key, value in values.items():
                    labels = self._parse_labels(key)
                    label_str = self._format_labels(labels)
                    if timestamp:
                        lines.append(f"{formatted_name}{label_str} {value} {timestamp}")
                    else:
                        lines.append(f"{formatted_name}{label_str} {value}")

        # Export histograms
        for name, values in self._registry._histograms.items():
            definition = self._registry.get_definition(name)
            if definition:
                formatted_name = self._format_name(name)
                lines.append(f"# HELP {formatted_name} {definition.help_text}")
                lines.append(f"# TYPE {formatted_name} histogram")

                for key, hist in values.items():
                    labels = hist.labels
                    base_label_str = self._format_labels(labels)

                    # Output bucket counts
                    cumulative = 0
                    for bucket in sorted(definition.buckets):
                        cumulative += hist.buckets.get(bucket, 0)
                        bucket_labels = {**labels, "le": str(bucket)}
                        label_str = self._format_labels(bucket_labels)
                        if timestamp:
                            lines.append(
                                f"{formatted_name}_bucket{label_str} {cumulative} {timestamp}"
                            )
                        else:
                            lines.append(f"{formatted_name}_bucket{label_str} {cumulative}")

                    # +Inf bucket
                    inf_labels = {**labels, "le": "+Inf"}
                    label_str = self._format_labels(inf_labels)
                    if timestamp:
                        lines.append(f"{formatted_name}_bucket{label_str} {hist.count} {timestamp}")
                    else:
                        lines.append(f"{formatted_name}_bucket{label_str} {hist.count}")

                    # Sum and count
                    if timestamp:
                        lines.append(f"{formatted_name}_sum{base_label_str} {hist.sum} {timestamp}")
                        lines.append(f"{formatted_name}_count{base_label_str} {hist.count} {timestamp}")
                    else:
                        lines.append(f"{formatted_name}_sum{base_label_str} {hist.sum}")
                        lines.append(f"{formatted_name}_count{base_label_str} {hist.count}")

        return "\n".join(lines)

    def export_to_file(self, path: str) -> None:
        """Export metrics to a file.

        Args:
            path: File path to write to.
        """
        content = self.export()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def create_default_registry() -> MetricsRegistry:
    """Create a registry with default Rice-Factor metrics.

    Returns:
        MetricsRegistry with default metrics registered.
    """
    registry = MetricsRegistry()
    for metric in DEFAULT_METRICS:
        registry.register(metric)
    return registry
