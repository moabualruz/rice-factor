"""Perform code refactoring."""

import typer
from rich.console import Console

console = Console()


def refactor(
    goal: str = typer.Argument(..., help="Refactoring goal description"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
) -> None:
    """Perform a refactoring operation based on the specified goal."""
    console.print(f"[yellow]rice-factor refactor '{goal}'[/yellow]: Not implemented yet")
    if dry_run:
        console.print("  [dim]Dry run mode[/dim]")
