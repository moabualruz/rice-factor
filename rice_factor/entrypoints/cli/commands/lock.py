"""Lock artifacts to prevent modification."""

import typer
from rich.console import Console

console = Console()


def lock(
    artifact: str = typer.Argument(..., help="Artifact to lock (e.g., TestPlan)"),
) -> None:
    """Lock an artifact, making it immutable."""
    console.print(f"[yellow]rice-factor lock {artifact}[/yellow]: Not implemented yet")
