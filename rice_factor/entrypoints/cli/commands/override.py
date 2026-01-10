"""Override command for bypassing blocked operations.

This module provides the override command for manually bypassing
phase gating and other blocked operations with audit trail support.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rice_factor.domain.services.override_service import OverrideService

console = Console()


def override(
    target: str = typer.Argument(
        ..., help="What to override (e.g., 'phase', 'approval')"
    ),
    reason: str = typer.Option(
        ..., "--reason", "-r", help="Reason for the override (required)"
    ),
    project_path: Path = typer.Option(
        Path.cwd(), "--path", "-p", help="Path to project directory"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """Override a blocked operation with audit trail.

    This command allows bypassing phase gating and other blocked operations.
    All overrides are recorded in the audit trail and flagged for reconciliation.

    Use with caution - overrides should be reconciled as soon as possible.

    Examples:
        rice-factor override phase --reason "Testing in development"
        rice-factor override approval --reason "Emergency hotfix"
    """
    # Check project is initialized
    if not (project_path / ".project").exists():
        console.print(
            "[red]Error:[/red] Project not initialized. Run 'rice-factor init' first."
        )
        raise typer.Exit(code=1)

    # Validate target
    valid_targets = ["phase", "approval", "validation"]
    if target not in valid_targets:
        console.print(
            f"[red]Error:[/red] Invalid override target '{target}'. "
            f"Valid targets: {', '.join(valid_targets)}"
        )
        raise typer.Exit(code=1)

    # Display warning
    console.print(
        Panel(
            "[bold red]WARNING: Manual Override[/bold red]\n\n"
            f"Target: {target}\n"
            f"Reason: {reason}\n\n"
            "[yellow]This override will be recorded in the audit trail "
            "and flagged for reconciliation.[/yellow]\n\n"
            "Overrides should be used sparingly and reconciled as soon as possible.",
            title="Override Warning",
            border_style="red",
        )
    )

    # Require confirmation
    if not yes:
        console.print(
            "\n[yellow]Type OVERRIDE to confirm (or anything else to cancel):[/yellow]"
        )
        confirmation = typer.prompt("")
        if confirmation != "OVERRIDE":
            console.print("[dim]Operation cancelled.[/dim]")
            return

    # Record the override
    override_service = OverrideService(project_path=project_path)
    override_record = override_service.record_override(
        target=target,
        reason=reason,
        context={"command": "manual override"},
    )

    console.print(
        f"\n[green]✓[/green] Override recorded: {override_record.id}"
    )
    console.print(
        "[yellow]Remember:[/yellow] This override must be reconciled. "
        "Run 'rice-factor override list' to see pending overrides."
    )


def override_list(
    project_path: Path = typer.Option(
        Path.cwd(), "--path", "-p", help="Path to project directory"
    ),
    all_overrides: bool = typer.Option(
        False, "--all", "-a", help="Show all overrides including reconciled"
    ),
) -> None:
    """List pending overrides that need reconciliation.

    By default shows only unreconciled overrides. Use --all to see all.
    """
    # Check project is initialized
    if not (project_path / ".project").exists():
        console.print(
            "[red]Error:[/red] Project not initialized. Run 'rice-factor init' first."
        )
        raise typer.Exit(code=1)

    override_service = OverrideService(project_path=project_path)

    if all_overrides:
        overrides = override_service.get_all_overrides()
        title = "All Overrides"
    else:
        overrides = override_service.get_pending_overrides()
        title = "Pending Overrides"

    if not overrides:
        if all_overrides:
            console.print("[dim]No overrides recorded.[/dim]")
        else:
            console.print("[green]✓[/green] No pending overrides.")
        return

    table = Table(title=title, show_header=True)
    table.add_column("ID", style="dim")
    table.add_column("Target", style="cyan")
    table.add_column("Reason")
    table.add_column("Timestamp", style="dim")
    table.add_column("Status", style="bold")

    for ovr in overrides:
        status = (
            "[green]Reconciled[/green]" if ovr.reconciled else "[yellow]Pending[/yellow]"
        )
        table.add_row(
            str(ovr.id)[:8],
            ovr.target,
            ovr.reason[:40] + "..." if len(ovr.reason) > 40 else ovr.reason,
            ovr.timestamp.strftime("%Y-%m-%d %H:%M"),
            status,
        )

    console.print(table)

    pending_count = len([o for o in overrides if not o.reconciled])
    if pending_count > 0:
        console.print(
            f"\n[yellow]⚠[/yellow] {pending_count} override(s) need reconciliation."
        )


def override_reconcile(
    override_id: str = typer.Argument(
        ..., help="Override ID to reconcile (can be partial)"
    ),
    project_path: Path = typer.Option(
        Path.cwd(), "--path", "-p", help="Path to project directory"
    ),
) -> None:
    """Mark an override as reconciled.

    Once the underlying issue has been addressed, mark the override
    as reconciled to clear it from the pending list.
    """
    # Check project is initialized
    if not (project_path / ".project").exists():
        console.print(
            "[red]Error:[/red] Project not initialized. Run 'rice-factor init' first."
        )
        raise typer.Exit(code=1)

    override_service = OverrideService(project_path=project_path)

    # Find matching override

    all_overrides = override_service.get_all_overrides()
    matching = [o for o in all_overrides if str(o.id).startswith(override_id)]

    if not matching:
        console.print(f"[red]Error:[/red] No override found matching '{override_id}'")
        raise typer.Exit(code=1)

    if len(matching) > 1:
        console.print(
            f"[red]Error:[/red] Multiple overrides match '{override_id}'. "
            "Please provide a more specific ID."
        )
        raise typer.Exit(code=1)

    override_record = matching[0]

    if override_record.reconciled:
        console.print(f"[yellow]Override {override_id} is already reconciled.[/yellow]")
        return

    if override_service.mark_reconciled(override_record.id):
        console.print(f"[green]✓[/green] Override {override_id} marked as reconciled.")
    else:
        console.print(f"[red]Error:[/red] Failed to reconcile override {override_id}")
        raise typer.Exit(code=1)


# Create subcommand app for override
app = typer.Typer(help="Override and reconciliation commands.")
app.command(name="create")(override)
app.command(name="list")(override_list)
app.command(name="reconcile")(override_reconcile)
