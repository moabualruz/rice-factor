"""Audit commands for drift detection and health checks.

This module provides CLI commands for auditing the codebase:
- rice-factor audit drift: Detect drift between code and artifacts
"""

import json
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.drift.detector import DriftDetectorAdapter
from rice_factor.domain.drift.models import (
    DriftConfig,
    DriftReport,
    DriftSeverity,
    DriftSignalType,
)
from rice_factor.entrypoints.cli.utils import console, error, info, success

app = typer.Typer(
    name="audit",
    help="Audit commands for drift detection and health checks.",
    no_args_is_help=True,
)


def _find_project_root(path: Path | None) -> Path:
    """Find the project root directory.

    Args:
        path: Starting path to search from. If None, uses CWD.

    Returns:
        Path to the project root (directory containing .project/).
    """
    start = path or Path.cwd()

    # Walk up looking for .project/
    current = start
    for _ in range(10):  # Max depth
        if (current / ".project").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent

    # No .project/ found, use starting path
    return start


def _severity_color(severity: DriftSeverity) -> str:
    """Get the Rich color for a severity level."""
    return {
        DriftSeverity.LOW: "dim",
        DriftSeverity.MEDIUM: "yellow",
        DriftSeverity.HIGH: "red",
        DriftSeverity.CRITICAL: "bold red",
    }.get(severity, "white")


def _display_drift_report(report: DriftReport, output_json: bool = False) -> None:
    """Display drift report.

    Args:
        report: The drift report to display.
        output_json: If True, output JSON. Otherwise, human-readable.
    """
    if output_json:
        # Use plain print() for JSON to avoid Rich formatting
        print(json.dumps(report.to_dict(), indent=2))
        return

    # Human-readable output
    console.print()

    # Status header
    if report.signal_count == 0:
        console.print(
            Panel(
                "[green]✓ No drift detected[/green]",
                style="green",
            )
        )
    elif report.requires_reconciliation:
        console.print(
            Panel(
                "[red]✗ RECONCILIATION REQUIRED[/red]\n"
                f"Drift signals: {report.signal_count} (threshold: {report.threshold})",
                style="red",
            )
        )
    else:
        console.print(
            Panel(
                f"[yellow]⚠ Drift detected ({report.signal_count} signals)[/yellow]\n"
                f"Below threshold ({report.threshold})",
                style="yellow",
            )
        )

    # Group by signal type
    for signal_type in DriftSignalType:
        signals = report.by_type(signal_type)
        if not signals:
            continue

        table = Table(title=f"{signal_type.value.replace('_', ' ').title()}")
        table.add_column("Severity", style="cyan", width=10)
        table.add_column("Path", style="white")
        table.add_column("Description", style="dim")

        for signal in signals:
            color = _severity_color(signal.severity)
            table.add_row(
                f"[{color}]{signal.severity.value.upper()}[/{color}]",
                signal.path,
                signal.description[:60] + "..." if len(signal.description) > 60 else signal.description,
            )

        console.print(table)
        console.print()

    # Summary
    console.print("[dim]Summary:[/dim]")
    console.print(f"  Code files scanned: {report.code_files_scanned}")
    console.print(f"  Artifacts checked: {report.artifacts_checked}")
    console.print(f"  Signals by severity:")
    for severity in DriftSeverity:
        count = len(report.by_severity(severity))
        if count > 0:
            color = _severity_color(severity)
            console.print(f"    [{color}]{severity.value.upper()}[/{color}]: {count}")
    console.print()


@app.command("drift")
def audit_drift(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    code_dir: Path = typer.Option(
        Path("src"),
        "--code-dir",
        "-d",
        help="Code directory to scan (relative to project root).",
    ),
    threshold: int = typer.Option(
        None,
        "--threshold",
        "-t",
        help="Override drift threshold. Default is 3.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON.",
    ),
) -> None:
    """Detect drift between code and artifacts.

    Scans for:
    - Orphan code: Source files not covered by any implementation plan
    - Orphan plans: Plans targeting non-existent files
    - Refactor hotspots: Files frequently modified (possible design issues)

    Exit codes:
      0 - No drift detected
      1 - Drift detected but below threshold
      2 - Reconciliation required (threshold exceeded or critical signals)
    """
    project_root = _find_project_root(path)

    if not output_json:
        info(f"Running drift analysis on {project_root}")

    # Configure the detector
    config = DriftConfig(
        drift_threshold=threshold if threshold is not None else 3,
        source_dirs=[str(code_dir)],
    )

    # Create detector and run analysis
    detector = DriftDetectorAdapter(
        config=config,
    )

    report = detector.full_analysis(project_root)

    # Override threshold if specified
    if threshold is not None:
        report.threshold = threshold

    _display_drift_report(report, output_json=output_json)

    # Exit codes
    if report.requires_reconciliation:
        if not output_json:
            error("Reconciliation required - drift exceeds threshold or has critical signals")
        raise typer.Exit(2)
    elif report.signal_count > 0:
        if not output_json:
            info("Drift detected but below threshold")
        raise typer.Exit(1)
    else:
        if not output_json:
            success("No drift detected")
