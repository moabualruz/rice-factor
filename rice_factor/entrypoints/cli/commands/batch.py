"""CLI commands for batch artifact operations.

Provides commands for batch approval, rejection, and orchestration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from rice_factor.domain.services.batch_processor import (
    BatchOperation,
    BatchOperationType,
    BatchProcessor,
)
from rice_factor.domain.services.lifecycle_orchestrator import (
    LifecycleOrchestrator,
    Phase,
)

app = typer.Typer(help="Batch artifact operations")
console = Console()


@app.command("approve")
def batch_approve(
    pattern: str = typer.Argument(..., help="Pattern to match artifact IDs"),
    approver: str = typer.Option("cli", "--approver", "-a", help="Approver name"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Approval reason"),
    no_validate: bool = typer.Option(
        False, "--no-validate", help="Skip pre-validation"
    ),
) -> None:
    """Approve multiple artifacts matching a pattern.

    Example:
        rice-factor batch approve "project-plan-*"
    """
    repo_root = Path.cwd()
    processor = BatchProcessor(repo_root=repo_root)

    # In a real implementation, we would:
    # 1. Scan artifacts matching the pattern
    # 2. Get their IDs
    # For now, we'll demonstrate with the pattern as a single ID
    artifact_ids = [pattern]  # Placeholder

    console.print(f"[bold]Batch approving artifacts matching:[/bold] {pattern}")

    result = processor.approve_batch(
        artifact_ids=artifact_ids,
        approver=approver,
        reason=reason,
        validate_all=not no_validate,
    )

    # Display results
    table = Table(title="Batch Approval Results")
    table.add_column("Artifact ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    for r in result.results:
        status = "[green]Success[/green]" if r.success else "[red]Failed[/red]"
        details = r.error or f"{r.old_status} → {r.new_status}"
        table.add_row(r.artifact_id, status, details)

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {result.success_count}/{result.total_count} approved")


@app.command("reject")
def batch_reject(
    pattern: str = typer.Argument(..., help="Pattern to match artifact IDs"),
    reason: str = typer.Option(..., "--reason", "-r", help="Rejection reason"),
) -> None:
    """Reject multiple artifacts matching a pattern.

    Example:
        rice-factor batch reject "impl-plan-*" -r "Needs revision"
    """
    repo_root = Path.cwd()
    processor = BatchProcessor(repo_root=repo_root)

    artifact_ids = [pattern]  # Placeholder

    console.print(f"[bold]Batch rejecting artifacts matching:[/bold] {pattern}")

    result = processor.reject_batch(
        artifact_ids=artifact_ids,
        reason=reason,
    )

    table = Table(title="Batch Rejection Results")
    table.add_column("Artifact ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    for r in result.results:
        status = "[green]Rejected[/green]" if r.success else "[red]Failed[/red]"
        details = r.error or reason
        table.add_row(r.artifact_id, status, details)

    console.print(table)


@app.command("orchestrate")
def orchestrate_phase(
    phase: str = typer.Argument(..., help="Phase to execute (init/plan/scaffold/test/implement/execute/validate/refactor)"),
    run_to: bool = typer.Option(
        False, "--run-to", help="Run all phases up to and including this phase"
    ),
    skip: bool = typer.Option(False, "--skip", help="Skip this phase"),
) -> None:
    """Execute or skip a lifecycle phase.

    Example:
        rice-factor batch orchestrate plan
        rice-factor batch orchestrate test --run-to
        rice-factor batch orchestrate refactor --skip
    """
    repo_root = Path.cwd()
    orchestrator = LifecycleOrchestrator(repo_root=repo_root)

    try:
        target_phase = Phase(phase)
    except ValueError:
        console.print(f"[red]Unknown phase:[/red] {phase}")
        console.print(f"Valid phases: {', '.join(p.value for p in Phase)}")
        raise typer.Exit(1)

    # Start or resume
    state = orchestrator.resume()
    if state is None:
        console.print("[yellow]Starting new orchestration...[/yellow]")
        orchestrator.start()

    if skip:
        result = orchestrator.skip_phase(target_phase, "Skipped via CLI")
        console.print(f"[yellow]Skipped phase:[/yellow] {phase}")
        return

    if run_to:
        console.print(f"[bold]Running phases up to:[/bold] {phase}")
        results = orchestrator.run_to_phase(target_phase)

        table = Table(title="Phase Execution Results")
        table.add_column("Phase", style="cyan")
        table.add_column("Status")
        table.add_column("Artifacts Created")

        for r in results:
            status = (
                "[green]Completed[/green]"
                if r.status.value == "completed"
                else f"[red]{r.status.value}[/red]"
            )
            artifacts = ", ".join(r.artifacts_created) if r.artifacts_created else "-"
            table.add_row(r.phase.value, status, artifacts)

        console.print(table)
    else:
        console.print(f"[bold]Executing phase:[/bold] {phase}")
        result = orchestrator.execute_phase(target_phase)

        if result.status.value == "completed":
            console.print(f"[green]Phase completed:[/green] {phase}")
        else:
            console.print(f"[red]Phase failed:[/red] {phase}")
            if result.error:
                console.print(f"  Error: {result.error}")

    # Show progress
    progress = orchestrator.get_progress()
    console.print(
        f"\n[bold]Progress:[/bold] {progress['completed_phases']}/{progress['total_phases']} "
        f"({progress.get('progress_percent', 0):.1f}%)"
    )


@app.command("status")
def orchestration_status() -> None:
    """Show current orchestration status."""
    repo_root = Path.cwd()
    orchestrator = LifecycleOrchestrator(repo_root=repo_root)

    state = orchestrator.resume()
    if state is None:
        console.print("[yellow]No active orchestration.[/yellow]")
        console.print("Run 'rice-factor batch orchestrate init' to start.")
        return

    progress = orchestrator.get_progress()

    console.print("\n[bold]Orchestration Status[/bold]")
    console.print(f"  Current Phase: {state.current_phase.value}")
    console.print(f"  Status: {progress['status']}")
    console.print(
        f"  Progress: {progress['completed_phases']}/{progress['total_phases']} "
        f"({progress.get('progress_percent', 0):.1f}%)"
    )

    if state.phase_results:
        console.print("\n[bold]Phase History:[/bold]")
        table = Table()
        table.add_column("Phase")
        table.add_column("Status")
        table.add_column("Completed At")

        for phase_name, result in state.phase_results.items():
            status_color = "green" if result.status.value == "completed" else "red"
            completed = (
                result.completed_at.strftime("%Y-%m-%d %H:%M")
                if result.completed_at
                else "-"
            )
            table.add_row(
                phase_name,
                f"[{status_color}]{result.status.value}[/{status_color}]",
                completed,
            )

        console.print(table)


@app.command("reset")
def reset_orchestration(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Reset orchestration state."""
    if not force:
        confirm = typer.confirm("This will reset all orchestration progress. Continue?")
        if not confirm:
            raise typer.Abort()

    repo_root = Path.cwd()
    orchestrator = LifecycleOrchestrator(repo_root=repo_root)
    orchestrator.reset()
    console.print("[green]Orchestration state reset.[/green]")
