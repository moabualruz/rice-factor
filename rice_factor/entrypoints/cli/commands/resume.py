"""Resume command for recovering from interrupted operations.

This module provides the resume command for recovering from failures
and continuing interrupted workflows.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.artifact_service import ArtifactService
from rice_factor.domain.services.override_service import OverrideService
from rice_factor.domain.services.phase_service import (
    PHASE_DESCRIPTIONS,
    Phase,
    PhaseService,
)

console = Console()


def resume(
    project_path: Path = typer.Option(
        Path.cwd(), "--path", "-p", help="Path to project directory"
    ),
) -> None:
    """Resume after a failure or interruption.

    Analyzes the current project state to identify where the workflow
    was interrupted and suggests next steps.
    """
    # Check project is initialized
    if not (project_path / ".project").exists():
        console.print(
            "[red]Error:[/red] Project not initialized. Run 'rice-factor init' first."
        )
        raise typer.Exit(code=1)

    # Determine current state
    artifacts_dir = project_path / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    approvals = ApprovalsTracker(artifacts_dir=artifacts_dir)
    artifact_service = ArtifactService(storage=storage, approvals=approvals)
    phase_service = PhaseService(project_path, artifact_service=artifact_service)

    current_phase = phase_service.get_current_phase()
    phase_description = PHASE_DESCRIPTIONS.get(current_phase, "Unknown phase")

    # Count artifacts by type
    artifact_counts: dict[str, int] = {}
    for artifact_type in ArtifactType:
        try:
            artifacts = storage.list_by_type(artifact_type)
            if artifacts:
                artifact_counts[artifact_type.value] = len(artifacts)
        except Exception:
            pass

    # Display state summary
    console.print(
        Panel(
            f"[bold]Current Phase:[/bold] {current_phase.name}\n"
            f"[dim]{phase_description}[/dim]",
            title="Project State",
            border_style="cyan",
        )
    )

    # Display artifacts
    if artifact_counts:
        table = Table(title="Artifacts", show_header=True)
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="bold")

        for atype, count in sorted(artifact_counts.items()):
            table.add_row(atype, str(count))

        console.print(table)
    else:
        console.print("[dim]No artifacts found.[/dim]")

    # Suggest next steps based on phase
    console.print("\n[bold]Suggested Next Steps:[/bold]")

    if current_phase == Phase.UNINIT:
        console.print("  1. Run [cyan]rice-factor init[/cyan] to initialize the project")
    elif current_phase == Phase.INIT:
        console.print("  1. Run [cyan]rice-factor plan project[/cyan] to create a project plan")
        console.print("  2. Approve the plan with [cyan]rice-factor approve <id>[/cyan]")
    elif current_phase == Phase.PLANNING:
        console.print("  1. Run [cyan]rice-factor scaffold[/cyan] to create file structure")
        console.print("  2. Run [cyan]rice-factor plan tests[/cyan] to create test plan")
    elif current_phase == Phase.SCAFFOLDED:
        console.print("  1. Run [cyan]rice-factor plan tests[/cyan] to create test plan")
        console.print("  2. Approve and lock tests with [cyan]rice-factor lock tests[/cyan]")
    elif current_phase == Phase.TEST_LOCKED:
        console.print("  1. Run [cyan]rice-factor plan impl <file>[/cyan] to plan implementation")
        console.print("  2. Run [cyan]rice-factor impl <file>[/cyan] to generate code")
        console.print("  3. Review and apply with [cyan]rice-factor apply[/cyan]")
    elif current_phase == Phase.IMPLEMENTING:
        console.print("  1. Continue with [cyan]rice-factor impl <file>[/cyan]")
        console.print("  2. Run [cyan]rice-factor test[/cyan] to verify changes")
        console.print("  3. Run [cyan]rice-factor validate[/cyan] to check all validations")
    elif current_phase == Phase.COMPLETE:
        console.print("  [green]✓[/green] Project workflow is complete!")
        console.print("  You can run [cyan]rice-factor validate[/cyan] to verify status")

    # Check for pending overrides
    override_service = OverrideService(project_path=project_path)
    pending = override_service.get_pending_overrides()
    if pending:
        console.print(
            f"\n[yellow]⚠[/yellow] {len(pending)} pending override(s) need reconciliation."
        )
        console.print("  Run [cyan]rice-factor override list[/cyan] to see details.")
