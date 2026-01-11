"""Apply approved code changes."""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.syntax import Syntax

from rice_factor.adapters.audit.trail import AuditTrail
from rice_factor.adapters.executors.audit_logger import AuditLogger
from rice_factor.adapters.executors.diff_executor import DiffExecutor
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.execution_types import ExecutionMode
from rice_factor.domain.services.diff_service import DiffService
from rice_factor.domain.services.phase_service import PhaseService
from rice_factor.domain.services.safety_enforcer import SafetyEnforcer
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


def _check_test_lock(project_root: Path) -> None:
    """Verify that test files haven't been modified since lock.

    Args:
        project_root: The project root directory.

    Raises:
        typer.Exit: If test lock is violated.
    """
    safety = SafetyEnforcer(project_root=project_root)
    result = safety.check_test_lock_intact()

    if not result.is_valid:
        error("TestPlan lock violated!")
        for modified in result.modified_files:
            error(f"  Modified: {modified}")
        info("Recovery: Reset tests to locked state with 'git checkout <test_files>'")
        raise typer.Exit(1)


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


def _get_diff_executor(project_root: Path) -> DiffExecutor:
    """Create a DiffExecutor for the project.

    Args:
        project_root: Root directory of the project.

    Returns:
        Configured DiffExecutor.
    """
    diff_service = DiffService(project_root=project_root)
    audit_logger = AuditLogger(project_root=project_root)
    artifacts_dir = project_root / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    return DiffExecutor(
        diff_service=diff_service,
        audit_logger=audit_logger,
        storage=storage,  # type: ignore[arg-type]  # Implements StoragePort
    )


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

    Uses git apply to apply the diff to the codebase.
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    # Verify test lock is intact (M07-E-001)
    _check_test_lock(project_root)

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

    # Get the diff path from the index
    diffs_dir = project_root / "audit" / "diffs"
    diff_path = None
    for diff_file in diffs_dir.glob("*.diff"):
        if str(approved_diff.id) in diff_file.name or approved_diff.target_file.replace("/", "_") in diff_file.name:
            diff_path = diff_file
            break

    if not diff_path:
        error("Could not find diff file for approved diff")
        raise typer.Exit(1)

    if dry_run:
        # Use DiffExecutor for dry run
        diff_executor = _get_diff_executor(project_root)
        result = diff_executor.execute(
            artifact_path=diff_path,
            repo_root=project_root,
            mode=ExecutionMode.DRY_RUN,
        )
        if result.status == "success":
            info("Dry run mode - diff would apply cleanly")
            for log in result.logs:
                console.print(f"  {log}")
        else:
            error("Dry run failed - diff would not apply cleanly")
            for err in result.errors:
                console.print(f"  [red]{err}[/red]")
        return

    # Confirmation
    if not yes:
        console.print()
        console.print(f"This will modify: [bold]{approved_diff.target_file}[/bold]")
        confirm = typer.confirm("Apply this diff?")
        if not confirm:
            info("Apply cancelled")
            raise typer.Exit(0)

    # Apply the diff using DiffExecutor
    info(f"Applying diff to {approved_diff.target_file}...")
    diff_executor = _get_diff_executor(project_root)
    result = diff_executor.execute(
        artifact_path=diff_path,
        repo_root=project_root,
        mode=ExecutionMode.APPLY,
    )

    if result.status == "success":
        # Record in audit trail
        audit_trail.record_diff_applied(diff_id=approved_diff.id)

        success(f"Diff applied to {approved_diff.target_file}")
        for log in result.logs:
            console.print(f"  {log}")
        info("Run 'rice-factor test' to verify the implementation")
    else:
        error("Failed to apply diff")
        for err in result.errors:
            console.print(f"  [red]{err}[/red]")
        raise typer.Exit(1)
