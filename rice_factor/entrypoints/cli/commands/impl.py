"""Implement code based on ImplementationPlan."""

from pathlib import Path

import typer
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
)


def _check_phase(project_root: Path) -> None:
    """Check if impl command can be executed.

    Args:
        project_root: The project root directory.

    Raises:
        typer.Exit: If command cannot be executed.
    """
    phase_service = PhaseService(project_root=project_root)
    try:
        phase_service.require_phase("impl")
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
    console.print(f"[bold]Diff for {target_file}:[/bold]")
    console.print()
    syntax = Syntax(content, "diff", theme="monokai", line_numbers=True)
    console.print(syntax)
    console.print()


@handle_errors
def impl(
    file_path: str = typer.Argument(..., help="Path to the file to implement"),
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be done without saving"
    ),
) -> None:
    """Generate implementation diff for a specific file.

    Creates a diff based on the ImplementationPlan for the target file.
    The diff is saved to audit/diffs/ and marked as pending review.

    Currently uses stub diff generation. Will use LLM in Milestone 04.
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    # Initialize services
    diff_service = DiffService(project_root=project_root)
    audit_trail = AuditTrail(project_root=project_root)

    # Generate diff
    info(f"Generating implementation for {file_path}...")
    diff = diff_service.generate_diff(target_file=file_path)

    # Display the diff
    _display_diff(diff.content, file_path)

    if dry_run:
        info("Dry run mode - diff not saved")
        info(f"Would save diff with ID: {diff.id}")
        return

    # Save diff
    diff_path = diff_service.save_diff(diff)
    success(f"Diff saved: {diff_path.relative_to(project_root)}")

    # Record in audit trail
    audit_trail.record_diff_generated(
        target_file=file_path,
        diff_path=diff_path,
        diff_id=diff.id,
    )

    info(f"Diff ID: {diff.id}")
    info("Run 'rice-factor review' to approve or reject this diff")
