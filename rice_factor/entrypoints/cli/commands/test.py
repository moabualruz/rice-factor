"""Run tests against the project."""

import typer
from rich.console import Console

console = Console()


def test(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose test output"),
) -> None:
    """Run tests against the locked TestPlan."""
    console.print("[yellow]rice-factor test[/yellow]: Not implemented yet")
    if verbose:
        console.print("  [dim]Verbose mode[/dim]")
