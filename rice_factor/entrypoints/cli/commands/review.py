"""Review pending diffs for approval."""

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
    """Check if review command can be executed.

    Args:
        project_root: The project root directory.

    Raises:
        typer.Exit: If command cannot be executed.
    """
    phase_service = PhaseService(project_root=project_root)
    try:
        phase_service.require_phase("review")
    except Exception as e:
        error(str(e))
        raise typer.Exit(1) from None


def _display_diff(content: str, target_file: str) -> None:
    """Display a diff with syntax highlighting.

    Args:
        content: The diff content.
        target_file: The target file name.
    """
    console.print()
    panel = Panel(
        Syntax(content, "diff", theme="monokai", line_numbers=True),
        title=f"Diff for {target_file}",
        border_style="blue",
    )
    console.print(panel)
    console.print()


@handle_errors
def review(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
) -> None:
    """Review and approve/reject pending diffs.

    Shows the most recent pending diff and prompts for approval.
    Approved diffs can be applied with 'rice-factor apply'.
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    # Initialize services
    diff_service = DiffService(project_root=project_root)
    audit_trail = AuditTrail(project_root=project_root)

    # Load pending diff
    pending_diff = diff_service.load_pending_diff()

    if not pending_diff:
        warning("No pending diffs to review")
        info("Generate a diff with 'rice-factor impl <file>'")
        return

    # Display diff info
    console.print(f"[bold]Diff ID:[/bold] {pending_diff.id}")
    console.print(f"[bold]Target:[/bold] {pending_diff.target_file}")
    console.print(f"[bold]Created:[/bold] {pending_diff.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # Display the diff
    _display_diff(pending_diff.content, pending_diff.target_file)

    # Prompt for action
    console.print("[bold]Actions:[/bold]")
    console.print("  [green]a[/green] - Approve this diff")
    console.print("  [red]r[/red] - Reject this diff")
    console.print("  [yellow]s[/yellow] - Skip (keep pending)")
    console.print()

    action = typer.prompt(
        "Choose action",
        type=str,
        default="s",
    ).lower()

    if action == "a":
        # Approve the diff
        diff_service.approve_diff(pending_diff.id)
        audit_trail.record_diff_approved(diff_id=pending_diff.id)
        success(f"Diff {pending_diff.id} approved")
        info("Run 'rice-factor apply' to apply this diff")

    elif action == "r":
        # Reject the diff
        reason = typer.prompt(
            "Reason for rejection (optional)",
            default="",
            show_default=False,
        )
        diff_service.reject_diff(pending_diff.id)
        audit_trail.record_diff_rejected(
            diff_id=pending_diff.id,
            reason=reason if reason else None,
        )
        warning(f"Diff {pending_diff.id} rejected")
        info("Generate a new diff with 'rice-factor impl <file>'")

    else:
        # Skip
        info("Diff kept pending for later review")
