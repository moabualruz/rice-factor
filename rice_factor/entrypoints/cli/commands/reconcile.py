"""Reconcile command for generating reconciliation plans.

This module provides the CLI command for generating reconciliation plans
from drift analysis.
"""

import json
from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.drift.detector import DriftDetectorAdapter
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.payloads.reconciliation_plan import (
    ReconciliationAction,
)
from rice_factor.domain.drift.models import DriftConfig
from rice_factor.domain.services.reconciliation_service import ReconciliationService
from rice_factor.entrypoints.cli.utils import console, error, info, success, warning


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


def _action_color(action: ReconciliationAction) -> str:
    """Get the Rich color for an action type."""
    return {
        ReconciliationAction.UPDATE_ARTIFACT: "yellow",
        ReconciliationAction.ARCHIVE_ARTIFACT: "dim",
        ReconciliationAction.CREATE_ARTIFACT: "green",
        ReconciliationAction.UPDATE_REQUIREMENTS: "blue",
        ReconciliationAction.REVIEW_CODE: "cyan",
        ReconciliationAction.DELETE_CODE: "red",
    }.get(action, "white")


def reconcile(
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
        3,
        "--threshold",
        "-t",
        help="Drift threshold for reconciliation.",
    ),
    no_freeze: bool = typer.Option(
        False,
        "--no-freeze",
        help="Don't freeze new work while reconciling.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show plan without saving.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON.",
    ),
) -> None:
    """Generate reconciliation plan for detected drift.

    Runs drift analysis and generates a ReconciliationPlan artifact with
    steps to resolve the drift. By default, the plan will freeze new work
    until approved.

    Exit codes:
      0 - Plan generated successfully (or no drift detected)
      1 - Error generating plan
    """
    project_root = _find_project_root(path)
    artifacts_dir = project_root / "artifacts"

    if not output_json:
        info(f"Analyzing drift in {project_root}")

    # Configure and run drift detection
    config = DriftConfig(
        drift_threshold=threshold,
        source_dirs=[str(code_dir)],
    )

    detector = DriftDetectorAdapter(config=config)
    drift_report = detector.full_analysis(project_root)

    # Check if reconciliation is needed
    if drift_report.signal_count == 0:
        if output_json:
            print(json.dumps({"status": "no_drift", "signals": 0}))
        else:
            success("No drift detected - no reconciliation needed")
        return

    if not drift_report.requires_reconciliation:
        if output_json:
            print(
                json.dumps(
                    {
                        "status": "below_threshold",
                        "signals": drift_report.signal_count,
                        "threshold": threshold,
                    }
                )
            )
        else:
            warning(
                f"Drift detected ({drift_report.signal_count} signals) but below "
                f"threshold ({threshold}). Use --threshold to override."
            )
        return

    # Generate reconciliation plan
    storage = FilesystemStorageAdapter(artifacts_dir)
    service = ReconciliationService(storage=storage)

    plan = service.generate_plan(
        drift_report,
        freeze_new_work=not no_freeze,
    )

    # Output the plan
    if output_json:
        output = {
            "status": "plan_generated",
            "artifact_id": str(plan.id),
            "steps": [
                {
                    "priority": step.priority,
                    "action": step.action.value,
                    "target": step.target,
                    "reason": step.reason,
                }
                for step in plan.payload.steps
            ],
            "freeze_new_work": plan.payload.freeze_new_work,
            "dry_run": dry_run,
        }
        print(json.dumps(output, indent=2))
    else:
        _display_plan(plan, dry_run=dry_run)

    # Save unless dry run
    if not dry_run:
        try:
            service.save_plan(plan)
            if not output_json:
                success(f"Reconciliation plan saved: {plan.id}")
                if plan.payload.freeze_new_work:
                    warning("New work is now frozen until this plan is approved")
                    info("Run 'rice-factor approve <artifact-id>' to approve the plan")
        except Exception as e:
            if not output_json:
                error(f"Failed to save plan: {e}")
            raise typer.Exit(1) from None


def _display_plan(plan: Any, dry_run: bool = False) -> None:
    """Display the reconciliation plan.

    Args:
        plan: The ReconciliationPlan artifact.
        dry_run: Whether this is a dry run.
    """
    console.print()

    # Header
    title = "[dim](DRY RUN)[/dim] " if dry_run else ""
    console.print(
        Panel(
            f"{title}[bold]Reconciliation Plan[/bold]\n"
            f"Artifact ID: {plan.id}\n"
            f"Drift Report: {plan.payload.drift_report_id}\n"
            f"Freeze New Work: {plan.payload.freeze_new_work}",
            style="blue",
        )
    )

    # Steps table
    if plan.payload.steps:
        table = Table(title="Reconciliation Steps")
        table.add_column("#", style="dim", width=4)
        table.add_column("Action", style="cyan", width=20)
        table.add_column("Target", style="white")
        table.add_column("Reason", style="dim")

        for step in plan.payload.steps:
            color = _action_color(step.action)
            table.add_row(
                str(step.priority),
                f"[{color}]{step.action.value.replace('_', ' ').title()}[/{color}]",
                step.target,
                step.reason[:50] + "..." if len(step.reason) > 50 else step.reason,
            )

        console.print(table)
    else:
        console.print("[dim]No steps in plan[/dim]")

    console.print()
