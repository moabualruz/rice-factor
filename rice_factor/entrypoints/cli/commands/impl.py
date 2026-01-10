"""Implement code based on scaffolds."""

import typer
from rich.console import Console

console = Console()


def impl(
    file_path: str = typer.Argument(..., help="Path to the file to implement"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
) -> None:
    """Implement code for a specific file based on scaffolded structure."""
    console.print(f"[yellow]rice-factor impl {file_path}[/yellow]: Not implemented yet")
    if dry_run:
        console.print("  [dim]Dry run mode[/dim]")
