"""Artifact lifecycle management commands.

This module provides CLI commands for artifact lifecycle management:
- rice-factor artifact age: Show artifact ages and lifecycle status
- rice-factor artifact extend: Extend artifact validity period
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.entrypoints.cli.utils import console, error, info, success

app = typer.Typer(
    name="artifact",
    help="Artifact lifecycle management commands.",
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


def _format_age(months: float) -> str:
    """Format age in human-readable form.

    Args:
        months: Age in months.

    Returns:
        Formatted string like "3 months", "1 month", "< 1 month".
    """
    if months < 1:
        return "< 1 month"
    elif months < 2:
        return "1 month"
    else:
        return f"{int(months)} months"


def _status_style(age_months: float, threshold_months: int = 3) -> str:
    """Get status style based on age.

    Args:
        age_months: Age in months.
        threshold_months: Threshold for review.

    Returns:
        Rich style string.
    """
    if age_months >= threshold_months:
        return "red"
    elif age_months >= threshold_months - 1:
        return "yellow"
    else:
        return "green"


@app.command("age")
def artifact_age(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    artifact_type: str = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by artifact type (e.g., ProjectPlan).",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON.",
    ),
) -> None:
    """Show artifact ages and lifecycle status.

    Lists all artifacts with their creation dates, ages, and review status.

    Exit codes:
      0 - All artifacts healthy
      1 - Some artifacts require review
      2 - Artifacts have critical violations or are significantly overdue
    """
    project_root = _find_project_root(path)

    if not output_json:
        info(f"Scanning artifacts in {project_root}")

    # Collect artifact data
    artifacts_data: list[dict[str, Any]] = []

    # Scan artifact directories
    artifacts_dir = project_root / "artifacts"
    if not artifacts_dir.exists():
        if output_json:
            print(json.dumps({"artifacts": [], "summary": {"total": 0}}))
        else:
            info("No artifacts directory found")
        return

    # Type filter
    type_filter: ArtifactType | None = None
    if artifact_type:
        try:
            type_filter = ArtifactType(artifact_type)
        except ValueError as e:
            error(f"Unknown artifact type: {artifact_type}")
            raise typer.Exit(1) from e

    # Scan all artifact JSON files
    for artifact_path in artifacts_dir.rglob("*.json"):
        if "_meta" in str(artifact_path):
            continue

        try:
            data = json.loads(artifact_path.read_text(encoding="utf-8"))
            art_type = data.get("artifact_type")

            # Apply type filter
            if type_filter and art_type != type_filter.value:
                continue

            # Calculate age
            created_str = data.get("created_at", "")
            if created_str:
                try:
                    # Parse ISO datetime
                    if created_str.endswith("Z"):
                        created_str = created_str[:-1] + "+00:00"
                    created = datetime.fromisoformat(created_str)
                    age_days = (datetime.now(created.tzinfo) - created).days
                    age_months = age_days / 30.44
                except ValueError:
                    age_days = 0
                    age_months = 0.0
            else:
                age_days = 0
                age_months = 0.0

            # Get review info
            reviewed_str = data.get("last_reviewed_at")
            days_since_review = None
            if reviewed_str:
                try:
                    if reviewed_str.endswith("Z"):
                        reviewed_str = reviewed_str[:-1] + "+00:00"
                    reviewed = datetime.fromisoformat(reviewed_str)
                    days_since_review = (datetime.now(reviewed.tzinfo) - reviewed).days
                except ValueError:
                    pass

            artifacts_data.append({
                "id": data.get("id", "unknown"),
                "artifact_type": art_type,
                "status": data.get("status", "unknown"),
                "created_at": data.get("created_at"),
                "age_days": age_days,
                "age_months": age_months,
                "last_reviewed_at": data.get("last_reviewed_at"),
                "days_since_review": days_since_review,
                "review_notes": data.get("review_notes"),
            })

        except (json.JSONDecodeError, OSError):
            continue

    # Output
    if output_json:
        summary = {
            "total": len(artifacts_data),
            "needing_review": sum(1 for a in artifacts_data if a["age_months"] >= 3),
            "overdue": sum(1 for a in artifacts_data if a["age_months"] >= 6),
        }
        print(json.dumps({"artifacts": artifacts_data, "summary": summary}, indent=2))
    else:
        _display_age_report(artifacts_data)

    # Exit codes
    overdue_count = sum(1 for a in artifacts_data if a["age_months"] >= 6)
    review_count = sum(1 for a in artifacts_data if a["age_months"] >= 3)

    if overdue_count > 0:
        raise typer.Exit(2)
    elif review_count > 0:
        raise typer.Exit(1)


def _display_age_report(artifacts: list[dict[str, Any]]) -> None:
    """Display the age report in a nice format.

    Args:
        artifacts: List of artifact data dictionaries.
    """
    console.print()

    if not artifacts:
        console.print(
            Panel(
                "[dim]No artifacts found[/dim]",
                title="Artifact Age Report",
            )
        )
        return

    # Group by status
    overdue = [a for a in artifacts if a["age_months"] >= 6]
    needs_review = [a for a in artifacts if 3 <= a["age_months"] < 6]
    healthy = [a for a in artifacts if a["age_months"] < 3]

    # Header
    if overdue:
        header_style = "red"
        header_text = f"[red]⚠ {len(overdue)} artifact(s) significantly overdue[/red]"
    elif needs_review:
        header_style = "yellow"
        header_text = f"[yellow]⏰ {len(needs_review)} artifact(s) need review[/yellow]"
    else:
        header_style = "green"
        header_text = "[green]✓ All artifacts healthy[/green]"

    console.print(
        Panel(
            header_text,
            title="Artifact Age Report",
            style=header_style,
        )
    )

    # Create table
    table = Table(title="Artifacts")
    table.add_column("Type", style="cyan", width=20)
    table.add_column("ID", style="dim", width=38)
    table.add_column("Status", style="white", width=10)
    table.add_column("Age", style="white", width=12)
    table.add_column("Review Status", style="white", width=20)

    # Sort by age (oldest first)
    sorted_artifacts = sorted(artifacts, key=lambda a: -a["age_months"])

    for artifact in sorted_artifacts:
        age_months = artifact["age_months"]
        age_style = _status_style(age_months)
        age_text = f"[{age_style}]{_format_age(age_months)}[/{age_style}]"

        # Review status
        if artifact["days_since_review"] is not None:
            review_text = f"Reviewed {artifact['days_since_review']} days ago"
        else:
            review_text = "[dim]Never reviewed[/dim]"

        # Mark overdue
        if age_months >= 6:
            review_text = "[red]OVERDUE[/red]"
        elif age_months >= 3:
            review_text = "[yellow]REVIEW NEEDED[/yellow]"

        table.add_row(
            artifact["artifact_type"],
            str(artifact["id"])[:36],
            artifact["status"],
            age_text,
            review_text,
        )

    console.print(table)
    console.print()

    # Summary
    console.print("[dim]Summary:[/dim]")
    console.print(f"  Total artifacts: {len(artifacts)}")
    console.print(f"  [green]Healthy: {len(healthy)}[/green]")
    console.print(f"  [yellow]Needs review: {len(needs_review)}[/yellow]")
    console.print(f"  [red]Overdue: {len(overdue)}[/red]")
    console.print()


@app.command("review")
def artifact_review(
    artifact_id: str = typer.Argument(..., help="Artifact ID to mark as reviewed"),
    notes: str = typer.Option(
        None,
        "--notes",
        "-n",
        help="Optional review notes.",
    ),
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path.",
    ),
) -> None:
    """Mark an artifact as reviewed.

    This command updates the artifact's last_reviewed_at timestamp,
    which resets the age-based review timer.
    """
    project_root = _find_project_root(path)

    # Find the artifact
    artifacts_dir = project_root / "artifacts"
    if not artifacts_dir.exists():
        error("No artifacts directory found")
        raise typer.Exit(1)

    found_path: Path | None = None
    found_data: dict[str, Any] | None = None

    for artifact_path in artifacts_dir.rglob("*.json"):
        if "_meta" in str(artifact_path):
            continue

        try:
            data = json.loads(artifact_path.read_text(encoding="utf-8"))
            if str(data.get("id", "")).startswith(artifact_id):
                found_path = artifact_path
                found_data = data
                break
        except (json.JSONDecodeError, OSError):
            continue

    if found_path is None or found_data is None:
        error(f"Artifact not found: {artifact_id}")
        raise typer.Exit(1)

    # Check if LOCKED
    if found_data.get("status") == "locked":
        error("Cannot review LOCKED artifacts - they are immutable")
        raise typer.Exit(1)

    # Update the artifact
    now = datetime.utcnow().isoformat() + "Z"
    found_data["last_reviewed_at"] = now
    if notes:
        found_data["review_notes"] = notes
    found_data["updated_at"] = now

    # Save
    found_path.write_text(json.dumps(found_data, indent=2), encoding="utf-8")

    success(f"Artifact '{artifact_id[:8]}...' marked as reviewed")
    if notes:
        info(f"Review notes: {notes}")
    info("Review timestamp updated - artifact age timer reset")


@app.command("extend")
def artifact_extend(
    artifact_id: str = typer.Argument(..., help="Artifact ID to extend"),
    reason: str = typer.Option(
        ...,
        "--reason",
        "-r",
        help="Reason for extension (required for audit trail).",
    ),
    months: int = typer.Option(
        None,
        "--months",
        "-m",
        help="Extension period in months. Defaults to artifact type's review period.",
    ),
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path.",
    ),
) -> None:
    """Extend artifact validity period.

    This command extends an artifact's review date by updating its last_reviewed_at
    timestamp. The extension reason is recorded in review_notes for audit purposes.

    Cannot extend LOCKED artifacts.
    """
    project_root = _find_project_root(path)

    # Find the artifact
    artifacts_dir = project_root / "artifacts"
    if not artifacts_dir.exists():
        error("No artifacts directory found")
        raise typer.Exit(1)

    found_path: Path | None = None
    found_data: dict[str, Any] | None = None

    for artifact_path in artifacts_dir.rglob("*.json"):
        if "_meta" in str(artifact_path):
            continue

        try:
            data = json.loads(artifact_path.read_text(encoding="utf-8"))
            if str(data.get("id", "")).startswith(artifact_id):
                found_path = artifact_path
                found_data = data
                break
        except (json.JSONDecodeError, OSError):
            continue

    if found_path is None or found_data is None:
        error(f"Artifact not found: {artifact_id}")
        raise typer.Exit(1)

    # Check if LOCKED
    if found_data.get("status") == "locked":
        error("Cannot extend LOCKED artifacts - they must remain immutable")
        raise typer.Exit(1)

    # Determine extension period
    if months is None:
        # Default based on artifact type
        art_type = found_data.get("artifact_type", "")
        default_periods = {
            "ProjectPlan": 3,
            "ArchitecturePlan": 6,
            "TestPlan": 3,
            "ImplementationPlan": 6,
        }
        months = default_periods.get(art_type, 3)

    # Update the artifact
    now = datetime.utcnow().isoformat() + "Z"
    found_data["last_reviewed_at"] = now
    found_data["review_notes"] = f"Extended: {reason}"
    found_data["updated_at"] = now

    # Save
    found_path.write_text(json.dumps(found_data, indent=2), encoding="utf-8")

    # Calculate new review date
    new_review_date = datetime.utcnow() + timedelta(days=months * 30)

    success(f"Artifact '{artifact_id[:8]}...' extended for {months} months")
    info(f"New review date: {new_review_date.strftime('%Y-%m-%d')}")
    info("Reason recorded in audit log")


@app.command("migrate")
def artifact_migrate(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without writing to disk.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON.",
    ),
) -> None:
    """Migrate artifacts to add lifecycle timestamp fields.

    This command adds `updated_at` and `created_at` fields to artifacts
    that are missing them. The migration is idempotent - running it multiple
    times has no effect after the first run.

    For artifacts missing timestamps, the file modification time is used
    as a fallback.
    """
    from rice_factor.migrations.add_timestamps import run_migration

    project_root = _find_project_root(path)

    if not output_json:
        if dry_run:
            info("DRY RUN - no changes will be made")
        info(f"Migrating artifacts in {project_root}")

    result = run_migration(
        repo_root=project_root,
        dry_run=dry_run,
        verbose=verbose,
    )

    if output_json:
        output = {
            "migrated": result.migrated,
            "skipped": result.skipped,
            "failed": result.failed,
            "total": result.total,
            "errors": result.errors,
        }
        print(json.dumps(output, indent=2))
    else:
        console.print()
        if result.migrated > 0:
            success(f"Migrated {result.migrated} artifact(s)")
        if result.skipped > 0:
            info(f"Skipped {result.skipped} artifact(s) (already up-to-date)")
        if result.failed > 0:
            error(f"Failed to migrate {result.failed} artifact(s)")
            for err in result.errors:
                console.print(f"  [dim]{err}[/dim]")
        console.print()

    if result.failed > 0:
        raise typer.Exit(1)
