"""TUI command for Rice-Factor CLI.

This module provides the `rice-factor tui` command for launching
the interactive terminal user interface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from rice_factor.entrypoints.cli.utils import handle_errors

console = Console()


@handle_errors
def tui(
    project_dir: Annotated[
        Path | None,
        typer.Option(
            "--project",
            "-p",
            help="Project directory (defaults to current directory)",
        ),
    ] = None,
) -> None:
    """Launch interactive TUI mode.

    Provides a terminal user interface for workflow navigation
    and artifact browsing.

    Press 'q' to quit, '?' for help.
    """
    project_root = project_dir or Path.cwd()

    # Check if textual is available
    try:
        from rice_factor.entrypoints.tui.app import RiceFactorTUI
    except ImportError as e:
        console.print(
            "[red]Error: Textual library not installed.[/red]\n"
            "Install with: pip install rice-factor[tui]"
        )
        raise typer.Exit(1) from e

    # Try to set up services if project is initialized
    phase_service = None
    artifact_service = None

    project_path = project_root / ".project"
    if project_path.exists():
        try:
            from rice_factor.adapters.storage.approvals import ApprovalsTracker
            from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
            from rice_factor.domain.services.artifact_service import ArtifactService
            from rice_factor.domain.services.phase_service import PhaseService

            artifacts_dir = project_root / "artifacts"
            storage = FilesystemStorageAdapter(artifacts_dir)
            approvals = ApprovalsTracker(artifacts_dir / ".approvals")
            artifact_service = ArtifactService(storage, approvals)
            phase_service = PhaseService(project_root, artifact_service)
        except Exception:
            # Services unavailable, TUI will work with limited functionality
            pass

    # Launch TUI
    console.print("[cyan]Launching TUI...[/cyan]")
    app = RiceFactorTUI(
        project_root=project_root,
        phase_service=phase_service,
        artifact_service=artifact_service,
    )
    app.run()
