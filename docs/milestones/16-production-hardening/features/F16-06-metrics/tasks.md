# F16-06: Metrics Export - Tasks

---

## Tasks

### T16-06-01: Create Prometheus Exporter [COMPLETE]
- Files: `rice_factor/adapters/metrics/prometheus_adapter.py`
- Implemented: MetricType, MetricDefinition, MetricsRegistry, PrometheusExporter, DEFAULT_METRICS

### T16-06-02: Create OpenTelemetry Exporter [COMPLETE]
- Files: `rice_factor/adapters/metrics/opentelemetry_adapter.py`
- Implemented: OTLPConfig, OpenTelemetryExporter with OTLP JSON export

### T16-06-03: Add Metrics Endpoint [COMPLETE]
- Files: `rice_factor/entrypoints/cli/commands/metrics.py`
- Implemented: show, export, push, definitions commands

### T16-06-04: Unit Tests for Metrics [COMPLETE]
- Files: `tests/unit/adapters/metrics/`
- Implemented: 47 unit tests for Prometheus and OpenTelemetry exporters

---

## Estimated Test Count: ~5
## Actual Test Count: 47
