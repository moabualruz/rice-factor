"""Audit commands for drift detection and health checks.

This module provides CLI commands for auditing the codebase:
- rice-factor audit drift: Detect drift between code and artifacts
"""

import json
from pathlib import Path
from typing import Any

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
    console.print("  Signals by severity:")
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


@app.command("coverage")
def audit_coverage(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    threshold: float = typer.Option(
        10.0,
        "--threshold",
        "-t",
        help="Coverage drift threshold percentage. Default is 10.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON.",
    ),
    no_run: bool = typer.Option(
        False,
        "--no-run",
        help="Skip running tests - use existing coverage report if available.",
    ),
) -> None:
    """Check coverage drift for TestPlan artifacts.

    Compares current test coverage against baseline coverage recorded
    when TestPlans were locked.

    Exit codes:
      0 - All TestPlans within threshold
      1 - Some TestPlans exceed drift threshold
      2 - Critical drift detected (> 2x threshold)
    """
    project_root = _find_project_root(path)
    artifacts_dir = project_root / "artifacts"

    if not output_json:
        info(f"Checking coverage drift in {project_root}")

    # Collect TestPlan data
    test_plans: list[dict[str, Any]] = []

    if not artifacts_dir.exists():
        if output_json:
            print(json.dumps({"test_plans": [], "summary": {"total": 0}}))
        else:
            info("No artifacts directory found")
        return

    # Scan for TestPlan artifacts
    for artifact_path in artifacts_dir.rglob("*.json"):
        if "_meta" in str(artifact_path):
            continue

        try:
            data = json.loads(artifact_path.read_text(encoding="utf-8"))
            if data.get("artifact_type") != "TestPlan":
                continue

            # Only check locked TestPlans (those with baselines)
            if data.get("status") != "locked":
                continue

            # Get baseline from payload
            payload = data.get("payload", {})
            baseline = payload.get("baseline_coverage", 0.0)

            test_plans.append({
                "id": data.get("id", "unknown"),
                "status": data.get("status"),
                "baseline_coverage": baseline,
                "baseline_recorded_at": payload.get("baseline_recorded_at"),
                "path": str(artifact_path),
            })
        except (json.JSONDecodeError, OSError):
            continue

    if not test_plans:
        if output_json:
            print(json.dumps({
                "test_plans": [],
                "summary": {"total": 0, "message": "No locked TestPlans with baselines found"},
            }))
        else:
            info("No locked TestPlans with baselines found")
        return

    # Try to get current coverage
    current_coverage: float | None = None
    coverage_file = project_root / "coverage.json"

    if not no_run:
        if not output_json:
            info("Running tests with coverage...")

        try:
            import subprocess
            subprocess.run(
                ["pytest", "--cov=rice_factor", "--cov-report=json", "-q", "--tb=no"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if coverage_file.exists():
                cov_data = json.loads(coverage_file.read_text())
                current_coverage = cov_data.get("totals", {}).get("percent_covered", 0.0)
        except Exception as e:
            if not output_json:
                error(f"Failed to run coverage: {e}")

    # Check for existing coverage file
    if current_coverage is None and coverage_file.exists():
        try:
            cov_data = json.loads(coverage_file.read_text())
            current_coverage = cov_data.get("totals", {}).get("percent_covered", 0.0)
        except (json.JSONDecodeError, OSError):
            pass

    if current_coverage is None:
        if output_json:
            print(json.dumps({
                "test_plans": test_plans,
                "summary": {
                    "total": len(test_plans),
                    "error": "Could not determine current coverage",
                },
            }))
        else:
            error("Could not determine current coverage")
        raise typer.Exit(1)

    # Calculate drift for each TestPlan
    results = []
    exceeds_threshold = 0
    critical_drift = 0

    for tp in test_plans:
        baseline = tp["baseline_coverage"]
        drift = baseline - current_coverage if baseline > 0 else 0.0

        status = "ok"
        if drift >= threshold * 2:
            status = "critical"
            critical_drift += 1
            exceeds_threshold += 1
        elif drift >= threshold:
            status = "exceeds"
            exceeds_threshold += 1
        elif drift > threshold / 2:
            status = "warning"

        results.append({
            **tp,
            "current_coverage": round(current_coverage, 2),
            "drift": round(drift, 2),
            "status": status,
        })

    # Output
    if output_json:
        print(json.dumps({
            "test_plans": results,
            "summary": {
                "total": len(results),
                "current_coverage": round(current_coverage, 2),
                "threshold": threshold,
                "exceeds_threshold": exceeds_threshold,
                "critical": critical_drift,
            },
        }, indent=2))
    else:
        _display_coverage_report(results, current_coverage, threshold)

    # Exit codes
    if critical_drift > 0:
        raise typer.Exit(2)
    elif exceeds_threshold > 0:
        raise typer.Exit(1)


def _display_coverage_report(
    results: list[dict[str, Any]],
    current_coverage: float,
    threshold: float,
) -> None:
    """Display the coverage report in a nice format.

    Args:
        results: List of coverage results per TestPlan.
        current_coverage: Current overall coverage percentage.
        threshold: Drift threshold percentage.
    """
    console.print()

    # Summary header
    exceeds = sum(1 for r in results if r["status"] in ("exceeds", "critical"))
    if exceeds == 0:
        console.print(
            Panel(
                f"[green]✓ All {len(results)} TestPlan(s) within drift threshold[/green]\n"
                f"Current coverage: {current_coverage:.1f}%",
                title="Coverage Drift Report",
                style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[red]✗ {exceeds} of {len(results)} TestPlan(s) exceed threshold[/red]\n"
                f"Current coverage: {current_coverage:.1f}% | Threshold: {threshold}%",
                title="Coverage Drift Report",
                style="red",
            )
        )

    # Create table
    table = Table(title="TestPlan Coverage")
    table.add_column("ID", style="dim", width=25)
    table.add_column("Baseline", style="cyan", width=10)
    table.add_column("Current", style="white", width=10)
    table.add_column("Drift", style="white", width=10)
    table.add_column("Status", style="white", width=12)

    for result in sorted(results, key=lambda r: -r["drift"]):
        drift = result["drift"]
        status = result["status"]

        # Drift formatting
        drift_str = f"{drift:+.1f}%"
        if drift > 0:
            drift_str = f"[red]{drift_str}[/red]"
        elif drift < 0:
            drift_str = f"[green]{drift_str}[/green]"

        # Status formatting
        status_style = {
            "ok": "green",
            "warning": "yellow",
            "exceeds": "red",
            "critical": "bold red",
        }.get(status, "white")
        status_str = f"[{status_style}]{status.upper()}[/{status_style}]"

        table.add_row(
            str(result["id"])[:24],
            f"{result['baseline_coverage']:.1f}%",
            f"{result['current_coverage']:.1f}%",
            drift_str,
            status_str,
        )

    console.print(table)
    console.print()

    # Legend
    console.print("[dim]Legend:[/dim]")
    console.print(f"  [green]OK[/green]: Drift < {threshold/2:.0f}%")
    console.print(f"  [yellow]WARNING[/yellow]: Drift {threshold/2:.0f}% - {threshold:.0f}%")
    console.print(f"  [red]EXCEEDS[/red]: Drift > {threshold:.0f}%")
    console.print(f"  [bold red]CRITICAL[/bold red]: Drift > {threshold*2:.0f}%")
    console.print()
