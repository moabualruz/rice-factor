"""Apply approved code changes."""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.syntax import Syntax

from rice_factor.adapters.audit.trail import AuditTrail
from rice_factor.domain.services.diff_service import DiffService
from rice_factor.domain.services.phase_service import PhaseService
from rice_factor.entrypoints.cli.utils import (
    console,
    error,
    handle_errors,
    info,
    success,
    warning,
)


def _check_phase(project_root: Path) -> None:
    """Check if apply command can be executed.

    Args:
        project_root: The project root directory.

    Raises:
        typer.Exit: If command cannot be executed.
    """
    phase_service = PhaseService(project_root=project_root)
    try:
        phase_service.require_phase("apply")
    except Exception as e:
        error(str(e))
        raise typer.Exit(1) from None


def _display_diff(content: str, target_file: str) -> None:
    """Display a diff with syntax highlighting.

    Args:
        content: The diff content.
        target_file: The target file name.
    """
    panel = Panel(
        Syntax(content, "diff", theme="monokai", line_numbers=True),
        title=f"Diff for {target_file}",
        border_style="green",
    )
    console.print(panel)


@handle_errors
def apply(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be done without applying"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """Apply approved diffs to the codebase.

    Applies the most recent approved diff. Requires confirmation before
    making changes.

    Currently uses stub application (logs operation, no actual changes).
    Will apply real diffs in Milestone 05.
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    # Initialize services
    diff_service = DiffService(project_root=project_root)
    audit_trail = AuditTrail(project_root=project_root)

    # Load approved diff
    approved_diff = diff_service.load_approved_diff()

    if not approved_diff:
        warning("No approved diffs to apply")
        info("Approve a diff with 'rice-factor review'")
        return

    # Display diff info
    console.print()
    console.print(f"[bold]Diff ID:[/bold] {approved_diff.id}")
    console.print(f"[bold]Target:[/bold] {approved_diff.target_file}")
    console.print(f"[bold]Approved:[/bold] {approved_diff.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    console.print()

    # Display the diff
    _display_diff(approved_diff.content, approved_diff.target_file)

    if dry_run:
        info("Dry run mode - diff not applied")
        info(f"Would apply diff to: {approved_diff.target_file}")
        return

    # Confirmation
    if not yes:
        console.print()
        console.print(f"This will modify: [bold]{approved_diff.target_file}[/bold]")
        confirm = typer.confirm("Apply this diff?")
        if not confirm:
            info("Apply cancelled")
            raise typer.Exit(0)

    # Stub: Apply the diff (in M05, this will actually patch the file)
    # For now, just mark it as applied and log the operation
    info(f"Applying diff to {approved_diff.target_file}...")

    # Mark as applied
    diff_service.mark_applied(approved_diff.id)

    # Record in audit trail
    audit_trail.record_diff_applied(diff_id=approved_diff.id)

    success(f"Diff applied to {approved_diff.target_file}")
    info("[dim]Note: Stub mode - no actual file changes made[/dim]")
    info("Run 'rice-factor test' to verify the implementation")
