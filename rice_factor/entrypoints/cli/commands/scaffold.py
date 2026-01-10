"""Generate code scaffolding from plans."""

import typer
from rich.console import Console

console = Console()


def scaffold(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
) -> None:
    """Generate code scaffolding from approved ImplPlan."""
    console.print("[yellow]rice-factor scaffold[/yellow]: Not implemented yet")
    if dry_run:
        console.print("  [dim]Dry run mode[/dim]")
