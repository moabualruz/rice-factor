"""Validate project artifacts and code."""

import typer
from rich.console import Console

console = Console()


def validate(
    strict: bool = typer.Option(False, "--strict", "-s", help="Fail on warnings"),
) -> None:
    """Validate all artifacts and code against specifications."""
    console.print("[yellow]rice-factor validate[/yellow]: Not implemented yet")
    if strict:
        console.print("  [dim]Strict mode[/dim]")
