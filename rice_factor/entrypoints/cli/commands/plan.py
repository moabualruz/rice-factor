"""Generate planning artifacts."""

import typer
from rich.console import Console

console = Console()


def plan(
    artifact_type: str = typer.Argument(..., help="Type of plan to generate (test, impl, arch)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
) -> None:
    """Generate a planning artifact (TestPlan, ImplPlan, or ArchitecturePlan)."""
    console.print(f"[yellow]rice-factor plan {artifact_type}[/yellow]: Not implemented yet")
    if dry_run:
        console.print("  [dim]Dry run mode[/dim]")
