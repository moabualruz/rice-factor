"""Metrics commands for Rice-Factor.

This module provides CLI commands for viewing and exporting metrics:
- rice-factor metrics show: Display current metrics
- rice-factor metrics export: Export metrics in Prometheus or OTLP format
"""

import json
from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.metrics.opentelemetry_adapter import (
    OTLPConfig,
    OpenTelemetryExporter,
)
from rice_factor.adapters.metrics.prometheus_adapter import (
    MetricType,
    MetricsRegistry,
    PrometheusExporter,
    create_default_registry,
)
from rice_factor.entrypoints.cli.utils import console, error, info, success

app = typer.Typer(
    name="metrics",
    help="Metrics commands for viewing and exporting metrics.",
    no_args_is_help=True,
)


# Global registry - populated on demand
_registry: MetricsRegistry | None = None


def get_registry() -> MetricsRegistry:
    """Get or create the metrics registry.

    Returns:
        MetricsRegistry with default metrics.
    """
    global _registry
    if _registry is None:
        _registry = create_default_registry()
    return _registry


def _find_project_root(path: Path | None) -> Path:
    """Find the project root directory.

    Args:
        path: Starting path to search from. If None, uses CWD.

    Returns:
        Path to the project root.
    """
    start = path or Path.cwd()

    # Walk up looking for .project/
    current = start
    for _ in range(10):
        if (current / ".project").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent

    return start


def _load_metrics_from_state(project_root: Path) -> None:
    """Load metrics from saved state file.

    Args:
        project_root: Project root directory.
    """
    registry = get_registry()
    state_file = project_root / ".project" / "metrics_state.json"

    if not state_file.exists():
        return

    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))

        # Load counters
        for name, values in data.get("counters", {}).items():
            if registry.get_definition(name):
                for key, value in values.items():
                    labels = {}
                    if key:
                        for part in key.split("|"):
                            if "=" in part:
                                k, v = part.split("=", 1)
                                labels[k] = v
                    # Increment by the saved value
                    registry.increment(name, labels, value)

        # Load gauges
        for name, values in data.get("gauges", {}).items():
            if registry.get_definition(name):
                for key, value in values.items():
                    labels = {}
                    if key:
                        for part in key.split("|"):
                            if "=" in part:
                                k, v = part.split("=", 1)
                                labels[k] = v
                    registry.set_gauge(name, value, labels)

    except (json.JSONDecodeError, OSError):
        pass


def _display_metrics(registry: MetricsRegistry) -> None:
    """Display metrics in a nice format.

    Args:
        registry: MetricsRegistry to display.
    """
    console.print()

    all_metrics = registry.get_all_metrics()

    # Counters
    counters = all_metrics.get("counters", {})
    if any(v for v in counters.values()):
        table = Table(title="Counters")
        table.add_column("Name", style="cyan")
        table.add_column("Labels", style="dim")
        table.add_column("Value", style="green", justify="right")

        for name, values in sorted(counters.items()):
            for key, value in sorted(values.items()):
                table.add_row(
                    name,
                    key if key else "-",
                    f"{value:.2f}",
                )

        console.print(table)
        console.print()

    # Gauges
    gauges = all_metrics.get("gauges", {})
    if any(v for v in gauges.values()):
        table = Table(title="Gauges")
        table.add_column("Name", style="cyan")
        table.add_column("Labels", style="dim")
        table.add_column("Value", style="yellow", justify="right")

        for name, values in sorted(gauges.items()):
            for key, value in sorted(values.items()):
                table.add_row(
                    name,
                    key if key else "-",
                    f"{value:.2f}",
                )

        console.print(table)
        console.print()

    # Histograms
    histograms = all_metrics.get("histograms", {})
    if any(v for v in histograms.values()):
        table = Table(title="Histograms")
        table.add_column("Name", style="cyan")
        table.add_column("Labels", style="dim")
        table.add_column("Count", style="white", justify="right")
        table.add_column("Sum", style="white", justify="right")
        table.add_column("Avg", style="magenta", justify="right")

        for name, values in sorted(histograms.items()):
            for key, hist in sorted(values.items()):
                count = hist.get("count", 0)
                total = hist.get("sum", 0)
                avg = total / count if count > 0 else 0

                labels_str = ""
                labels = hist.get("labels", {})
                if labels:
                    labels_str = "|".join(f"{k}={v}" for k, v in labels.items())

                table.add_row(
                    name,
                    labels_str if labels_str else "-",
                    str(count),
                    f"{total:.2f}",
                    f"{avg:.3f}",
                )

        console.print(table)
        console.print()

    # Summary
    total_counters = sum(len(v) for v in counters.values())
    total_gauges = sum(len(v) for v in gauges.values())
    total_histograms = sum(len(v) for v in histograms.values())

    if total_counters + total_gauges + total_histograms == 0:
        console.print(
            Panel(
                "[dim]No metrics data collected yet[/dim]",
                title="Metrics Summary",
            )
        )
    else:
        console.print(
            Panel(
                f"Counters: {total_counters}\n"
                f"Gauges: {total_gauges}\n"
                f"Histograms: {total_histograms}",
                title="Metrics Summary",
            )
        )


@app.command("show")
def show_metrics(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON.",
    ),
) -> None:
    """Display current metrics.

    Shows all collected metrics including counters, gauges, and histograms.
    """
    project_root = _find_project_root(path)
    registry = get_registry()

    # Load any saved state
    _load_metrics_from_state(project_root)

    if output_json:
        print(json.dumps(registry.get_all_metrics(), indent=2))
    else:
        info(f"Loading metrics from {project_root}")
        _display_metrics(registry)


@app.command("export")
def export_metrics(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path. If not specified, outputs to stdout.",
    ),
    format: str = typer.Option(
        "prometheus",
        "--format",
        "-f",
        help="Output format: prometheus or otlp.",
    ),
    namespace: str = typer.Option(
        "",
        "--namespace",
        "-n",
        help="Metric namespace prefix (Prometheus only).",
    ),
) -> None:
    """Export metrics in Prometheus or OTLP format.

    Formats:
      - prometheus: Prometheus text exposition format
      - otlp: OpenTelemetry Protocol JSON format

    Example:
      rice-factor metrics export --format prometheus > metrics.prom
      rice-factor metrics export --format otlp -o metrics.json
    """
    project_root = _find_project_root(path)
    registry = get_registry()

    # Load any saved state
    _load_metrics_from_state(project_root)

    if format.lower() == "prometheus":
        exporter = PrometheusExporter(
            registry=registry,
            namespace=namespace,
        )
        content = exporter.export()

        if output:
            output.write_text(content, encoding="utf-8")
            success(f"Exported Prometheus metrics to {output}")
        else:
            print(content)

    elif format.lower() in ("otlp", "opentelemetry"):
        config = OTLPConfig()
        exporter = OpenTelemetryExporter(
            registry=registry,
            config=config,
        )
        content = exporter.to_json()

        if output:
            output.write_text(content, encoding="utf-8")
            success(f"Exported OTLP metrics to {output}")
        else:
            print(content)

    else:
        error(f"Unknown format: {format}. Use 'prometheus' or 'otlp'.")
        raise typer.Exit(1)


@app.command("push")
def push_metrics(
    endpoint: str = typer.Option(
        ...,
        "--endpoint",
        "-e",
        help="OTLP endpoint URL.",
    ),
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    service_name: str = typer.Option(
        "rice-factor",
        "--service",
        "-s",
        help="Service name for OTLP resource.",
    ),
) -> None:
    """Push metrics to an OTLP endpoint.

    Example:
      rice-factor metrics push --endpoint http://localhost:4318/v1/metrics
    """
    project_root = _find_project_root(path)
    registry = get_registry()

    # Load any saved state
    _load_metrics_from_state(project_root)

    config = OTLPConfig(
        endpoint=endpoint,
        service_name=service_name,
    )
    exporter = OpenTelemetryExporter(
        registry=registry,
        config=config,
    )

    info(f"Pushing metrics to {endpoint}...")
    result = exporter.export()

    if result.get("success"):
        success(f"Pushed {result.get('metrics_exported', 0)} metrics successfully")
    else:
        error(f"Failed to push metrics: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)


@app.command("definitions")
def list_definitions(
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON.",
    ),
) -> None:
    """List all metric definitions.

    Shows all registered metrics with their types and descriptions.
    """
    registry = get_registry()

    if output_json:
        definitions = []
        for name, defn in registry._definitions.items():
            definitions.append({
                "name": name,
                "type": defn.metric_type.value,
                "help": defn.help_text,
                "labels": defn.labels,
            })
        print(json.dumps(definitions, indent=2))
    else:
        console.print()

        table = Table(title="Metric Definitions")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Labels", style="dim")
        table.add_column("Description", style="white")

        for name, defn in sorted(registry._definitions.items()):
            table.add_row(
                name,
                defn.metric_type.value,
                ", ".join(defn.labels) if defn.labels else "-",
                defn.help_text[:50] + "..." if len(defn.help_text) > 50 else defn.help_text,
            )

        console.print(table)
        console.print()
        console.print(f"[dim]Total: {len(registry._definitions)} metrics defined[/dim]")
