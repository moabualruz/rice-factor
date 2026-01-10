"""Initialize a new rice-factor project."""

import typer
from rich.console import Console

app = typer.Typer(help="Initialize a new rice-factor project")
console = Console()


@app.callback(invoke_without_command=True)
def init(
    ctx: typer.Context,
    path: str = typer.Argument(".", help="Path to initialize project in"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
) -> None:
    """Initialize a new rice-factor project in the specified directory."""
    if ctx.invoked_subcommand is None:
        console.print("[yellow]rice-factor init[/yellow]: Not implemented yet")
        console.print(f"  Would initialize project at: {path}")
        if force:
            console.print("  [red]Force mode enabled[/red]")
