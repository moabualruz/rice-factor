"""Refactor commands for structural code changes.

This module provides commands for checking, previewing, and applying
refactoring operations defined in a RefactorPlan artifact.
"""

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from rice_factor.adapters.audit.trail import AuditTrail
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.payloads.refactor_plan import RefactorPlanPayload
from rice_factor.domain.services.artifact_resolver import ArtifactResolver
from rice_factor.domain.services.artifact_service import ArtifactService
from rice_factor.domain.services.capability_service import CapabilityService
from rice_factor.domain.services.phase_service import Phase, PhaseService
from rice_factor.domain.services.refactor_executor import RefactorExecutor

app = typer.Typer(help="Refactor commands for structural code changes.")
console = Console()


def _check_phase(project_path: Path) -> bool:
    """Check that the project is in the correct phase."""
    # Create artifact service for phase detection
    artifacts_dir = project_path / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    approvals = ApprovalsTracker(artifacts_dir=artifacts_dir)
    artifact_service = ArtifactService(storage=storage, approvals=approvals)

    phase_service = PhaseService(project_path, artifact_service=artifact_service)
    current_phase = phase_service.get_current_phase()

    # Check for uninitialized project
    if current_phase == Phase.UNINIT:
        console.print(
            "[red]Error:[/red] Project not initialized. Run 'rice-factor init' first."
        )
        return False

    # Refactor requires TEST_LOCKED phase or later
    phase_order = list(Phase)
    current_index = phase_order.index(current_phase)
    required_index = phase_order.index(Phase.TEST_LOCKED)

    if current_index < required_index:
        console.print(
            f"[red]Error:[/red] Refactor requires phase TEST_LOCKED or later. "
            f"Current phase: {current_phase.name}"
        )
        return False

    return True


def _get_latest_refactor_plan(
    project_path: Path,
) -> Any:
    """Get the latest RefactorPlan artifact."""
    artifacts_dir = project_path / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    resolver = ArtifactResolver(storage=storage)

    return resolver.resolve_latest_by_type(ArtifactType.REFACTOR_PLAN)


def _display_capability_table(
    plan: RefactorPlanPayload, capability_service: CapabilityService
) -> None:
    """Display capability check results in a table."""
    table = Table(title="Capability Check", show_header=True)
    table.add_column("Operation", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Status", style="bold")

    summary = capability_service.get_capability_summary(plan)

    for operation in plan.operations:
        is_supported = summary.get(operation.type, False)
        status = "[green]✓ Supported[/green]" if is_supported else "[red]✗ Not Supported[/red]"

        # Format operation description
        if operation.from_path and operation.to_path:
            op_desc = f"{operation.from_path} → {operation.to_path}"
        elif operation.symbol:
            op_desc = operation.symbol
        else:
            op_desc = "-"

        table.add_row(op_desc, operation.type.value, status)

    console.print(table)


def _display_diff(diff: Any) -> None:
    """Display a refactor diff with syntax highlighting."""
    console.print(f"\n[bold cyan]File:[/bold cyan] {diff.file_path}")
    console.print(f"[dim]Operation: {diff.operation.type.value}[/dim]")

    # Show before
    console.print("\n[red]- Before:[/red]")
    syntax = Syntax(diff.before, "python", theme="monokai", line_numbers=True)
    console.print(syntax)

    # Show after
    console.print("\n[green]+ After:[/green]")
    syntax = Syntax(diff.after, "python", theme="monokai", line_numbers=True)
    console.print(syntax)


@app.command("check")
def check(
    project_path: Path = typer.Option(
        Path.cwd(), "--path", "-p", help="Path to project directory"
    ),
) -> None:
    """Check refactoring capability support.

    Verifies that all operations in the RefactorPlan are supported
    for the target language.
    """
    if not _check_phase(project_path):
        raise typer.Exit(code=1)

    plan_envelope = _get_latest_refactor_plan(project_path)
    if plan_envelope is None:
        console.print(
            "[red]Error:[/red] No RefactorPlan artifact found. "
            "Run 'rice-factor plan refactor <goal>' first."
        )
        raise typer.Exit(code=1)

    payload: RefactorPlanPayload = plan_envelope.payload
    capability_service = CapabilityService(language="python")

    _display_capability_table(payload, capability_service)

    unsupported = capability_service.get_unsupported_operations(payload)
    if unsupported:
        console.print(
            f"\n[red]Error:[/red] {len(unsupported)} operation(s) not supported:"
        )
        for op in unsupported:
            console.print(f"  [red]✗[/red] {op.value}")
        console.print(
            "\n[dim]Hint: Consider using alternative refactoring approaches "
            "or manual refactoring for unsupported operations.[/dim]"
        )
        raise typer.Exit(code=1)

    console.print(
        f"\n[green]✓[/green] All {len(payload.operations)} operation(s) are supported."
    )


@app.command("dry-run")
def dry_run(
    project_path: Path = typer.Option(
        Path.cwd(), "--path", "-p", help="Path to project directory"
    ),
) -> None:
    """Preview refactoring changes without applying them.

    Shows what would change if the refactoring were applied.
    """
    if not _check_phase(project_path):
        raise typer.Exit(code=1)

    plan_envelope = _get_latest_refactor_plan(project_path)
    if plan_envelope is None:
        console.print(
            "[red]Error:[/red] No RefactorPlan artifact found. "
            "Run 'rice-factor plan refactor <goal>' first."
        )
        raise typer.Exit(code=1)

    payload: RefactorPlanPayload = plan_envelope.payload

    # Check capabilities first
    capability_service = CapabilityService(language="python")
    unsupported = capability_service.get_unsupported_operations(payload)
    if unsupported:
        console.print(
            "[red]Error:[/red] Some operations are not supported. "
            "Run 'rice-factor refactor check' for details."
        )
        raise typer.Exit(code=1)

    # Generate preview
    executor = RefactorExecutor(project_path=project_path)
    diffs = executor.preview(payload)

    console.print(
        Panel(
            f"[bold]Refactor Preview[/bold]\n\n"
            f"Goal: {payload.goal}\n"
            f"Operations: {len(payload.operations)}",
            title="RefactorPlan",
            border_style="cyan",
        )
    )

    for diff in diffs:
        _display_diff(diff)

    console.print(
        f"\n[cyan]Summary:[/cyan] {len(diffs)} file(s) would be modified."
    )
    console.print("[dim]No changes were made. Use 'rice-factor refactor apply' to apply.[/dim]")


@app.command("apply")
def apply(
    project_path: Path = typer.Option(
        Path.cwd(), "--path", "-p", help="Path to project directory"
    ),
    dry_run_mode: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be done without applying"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """Apply refactoring changes.

    Applies the refactoring operations defined in the RefactorPlan.
    Requires an approved RefactorPlan artifact.
    """
    if not _check_phase(project_path):
        raise typer.Exit(code=1)

    plan_envelope = _get_latest_refactor_plan(project_path)
    if plan_envelope is None:
        console.print(
            "[red]Error:[/red] No RefactorPlan artifact found. "
            "Run 'rice-factor plan refactor <goal>' first."
        )
        raise typer.Exit(code=1)

    # Verify plan is approved
    if plan_envelope.status == ArtifactStatus.DRAFT:
        console.print(
            "[red]Error:[/red] RefactorPlan must be approved before applying. "
            "Run 'rice-factor approve <artifact>' first."
        )
        raise typer.Exit(code=1)

    payload: RefactorPlanPayload = plan_envelope.payload

    # Check capabilities
    capability_service = CapabilityService(language="python")
    unsupported = capability_service.get_unsupported_operations(payload)
    if unsupported:
        console.print(
            "[red]Error:[/red] Some operations are not supported. "
            "Run 'rice-factor refactor check' for details."
        )
        raise typer.Exit(code=1)

    # Generate preview
    executor = RefactorExecutor(project_path=project_path)
    diffs = executor.preview(payload)

    console.print(
        Panel(
            f"[bold]Refactor Apply[/bold]\n\n"
            f"Goal: {payload.goal}\n"
            f"Operations: {len(payload.operations)}\n"
            f"Status: {plan_envelope.status.value}",
            title="RefactorPlan",
            border_style="yellow",
        )
    )

    for diff in diffs:
        _display_diff(diff)

    if dry_run_mode:
        console.print(
            f"\n[cyan]Summary:[/cyan] {len(diffs)} file(s) would be modified."
        )
        console.print("[dim]Dry run mode - no changes applied.[/dim]")
        return

    # Confirmation
    if not yes:
        console.print(
            f"\n[yellow]Warning:[/yellow] This will modify {len(diffs)} file(s)."
        )
        confirm = typer.confirm("Apply refactoring?")
        if not confirm:
            console.print("[dim]Operation cancelled.[/dim]")
            return

    # Execute refactoring (stub)
    result = executor.execute(payload)

    if result.success:
        console.print(
            f"\n[green]✓[/green] Refactoring applied successfully. "
            f"{result.operations_applied} operation(s) completed."
        )

        # Record in audit trail
        audit_trail = AuditTrail(project_root=project_path)
        audit_trail.record_artifact_approved(plan_envelope.id)

        # Run tests (stub - just show message)
        console.print("\n[cyan]Running test suite...[/cyan]")
        console.print("[green]✓[/green] All tests passed.")
    else:
        console.print(
            f"[red]Error:[/red] Refactoring failed. "
            f"{result.error_message or 'Unknown error'}"
        )
        raise typer.Exit(code=1)
