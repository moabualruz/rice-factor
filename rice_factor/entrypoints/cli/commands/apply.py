"""Apply generated code changes."""

import typer
from rich.console import Console

console = Console()


def apply(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
) -> None:
    """Apply pending code changes from the staging area."""
    console.print("[yellow]rice-factor apply[/yellow]: Not implemented yet")
    if dry_run:
        console.print("  [dim]Dry run mode[/dim]")
