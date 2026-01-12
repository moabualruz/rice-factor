"""Web interface CLI commands.

Provides commands for starting the web server and building the frontend.
Maps to F22-05: CLI Commands feature.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from rice_factor.entrypoints.cli.utils import console, error, info, success, warning

app = typer.Typer(
    name="web",
    help="Web interface commands for rice-factor.",
    no_args_is_help=True,
)


def _check_web_dependencies() -> bool:
    """Check if web dependencies are installed."""
    try:
        import uvicorn  # noqa: F401
        import fastapi  # noqa: F401

        return True
    except ImportError:
        return False


def _get_frontend_dir() -> Path:
    """Get the frontend directory path."""
    # Try relative to this file first (development)
    this_file = Path(__file__)
    dev_path = this_file.parent.parent.parent.parent.parent / "rice_factor_web" / "frontend"
    if dev_path.exists():
        return dev_path

    # Try relative to package root (installed)
    import rice_factor_web

    pkg_path = Path(rice_factor_web.__file__).parent / "frontend"
    if pkg_path.exists():
        return pkg_path

    return dev_path  # Return default even if not found for error handling


def _check_node_npm() -> bool:
    """Check if Node.js and npm are available."""
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    return shutil.which(npm_cmd) is not None


@app.command()
def serve(
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Server host"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable hot reload (development)"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of worker processes"),
) -> None:
    """Start the web server.

    Launches the Rice-Factor web interface using uvicorn.

    Examples:
        rice-factor web serve
        rice-factor web serve --port 8080
        rice-factor web serve --reload  # for development
    """
    if not _check_web_dependencies():
        error("Web dependencies not installed.")
        console.print(
            "\nInstall with: [bold]pip install rice-factor[web][/bold]\n"
            "Or: [bold]uv add rice-factor[web][/bold]"
        )
        raise typer.Exit(1)

    try:
        import uvicorn
    except ImportError:
        error("uvicorn not found. Install with: pip install uvicorn[standard]")
        raise typer.Exit(1)

    info(f"Starting Rice-Factor web server on http://{host}:{port}")

    if reload:
        warning("Hot reload enabled - for development use only")

    try:
        uvicorn.run(
            "rice_factor_web.backend.main:create_app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            factory=True,
            log_level="info",
        )
    except Exception as e:
        error(f"Failed to start server: {e}")
        raise typer.Exit(1)


@app.command()
def build(
    outdir: Optional[Path] = typer.Option(
        None, "--outdir", "-o", help="Output directory (default: frontend/dist)"
    ),
    install: bool = typer.Option(True, "--install/--no-install", help="Install npm dependencies first"),
) -> None:
    """Build the frontend for production.

    Runs npm build to create optimized production assets.

    Examples:
        rice-factor web build
        rice-factor web build --outdir ./dist
        rice-factor web build --no-install
    """
    if not _check_node_npm():
        error("Node.js and npm are required to build the frontend.")
        console.print("\nInstall Node.js from: [link]https://nodejs.org/[/link]")
        raise typer.Exit(1)

    frontend_dir = _get_frontend_dir()

    if not frontend_dir.exists():
        error(f"Frontend directory not found: {frontend_dir}")
        raise typer.Exit(1)

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    # Install dependencies if requested
    if install:
        info("Installing npm dependencies...")
        try:
            result = subprocess.run(
                [npm_cmd, "install"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            error(f"npm install failed: {e.stderr}")
            raise typer.Exit(1)

    # Build the frontend
    info("Building frontend for production...")
    build_cmd = [npm_cmd, "run", "build"]

    if outdir:
        build_cmd.extend(["--", "--outDir", str(outdir)])

    try:
        result = subprocess.run(
            build_cmd,
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout)

        output_path = outdir or (frontend_dir / "dist")
        success(f"Frontend built successfully: {output_path}")

    except subprocess.CalledProcessError as e:
        error(f"Build failed: {e.stderr}")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Check web interface status and dependencies.

    Shows whether web dependencies are installed and the frontend is ready.
    """
    console.print("[bold]Rice-Factor Web Interface Status[/bold]\n")

    # Check Python dependencies
    web_deps = _check_web_dependencies()
    if web_deps:
        console.print("[green]✓[/green] Python web dependencies installed")
    else:
        console.print("[red]✗[/red] Python web dependencies not installed")
        console.print("  Install with: [bold]pip install rice-factor[web][/bold]")

    # Check Node.js
    node_available = _check_node_npm()
    if node_available:
        console.print("[green]✓[/green] Node.js and npm available")
    else:
        console.print("[yellow]![/yellow] Node.js not available (optional, for building frontend)")

    # Check frontend directory
    frontend_dir = _get_frontend_dir()
    if frontend_dir.exists():
        console.print(f"[green]✓[/green] Frontend directory: {frontend_dir}")

        # Check if built
        dist_dir = frontend_dir / "dist"
        if dist_dir.exists():
            console.print("[green]✓[/green] Frontend is built")
        else:
            console.print("[yellow]![/yellow] Frontend not built (run: rice-factor web build)")

        # Check node_modules
        node_modules = frontend_dir / "node_modules"
        if node_modules.exists():
            console.print("[green]✓[/green] npm dependencies installed")
        else:
            console.print("[yellow]![/yellow] npm dependencies not installed")
    else:
        console.print(f"[red]✗[/red] Frontend directory not found: {frontend_dir}")

    console.print()
