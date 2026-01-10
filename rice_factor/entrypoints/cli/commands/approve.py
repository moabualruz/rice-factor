"""Approve artifacts for progression."""

import typer
from rich.console import Console

console = Console()


def approve(
    artifact: str = typer.Argument(..., help="Artifact to approve (e.g., TestPlan, ImplPlan)"),
) -> None:
    """Approve an artifact, transitioning it from draft to approved status."""
    console.print(f"[yellow]rice-factor approve {artifact}[/yellow]: Not implemented yet")
