"""Diagnose test/validation failures."""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.payloads.validation_result import (
    ValidationResultPayload,
    ValidationStatus,
)
from rice_factor.domain.services.artifact_service import ArtifactService
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
    """Check if diagnose command can be executed.

    Args:
        project_root: The project root directory.

    Raises:
        typer.Exit: If command cannot be executed.
    """
    phase_service = PhaseService(project_root=project_root)
    try:
        phase_service.require_phase("diagnose")
    except Exception as e:
        error(str(e))
        raise typer.Exit(1) from None


def _get_artifact_service(project_root: Path) -> ArtifactService:
    """Get artifact service for the project.

    Args:
        project_root: The project root directory.

    Returns:
        ArtifactService instance.
    """
    artifacts_dir = project_root / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    approvals = ApprovalsTracker(artifacts_dir=artifacts_dir)
    return ArtifactService(storage=storage, approvals=approvals)


def _analyze_failures(errors: list[str]) -> list[tuple[str, str]]:
    """Analyze failures and suggest fixes.

    Args:
        errors: List of error messages.

    Returns:
        List of (error, suggestion) tuples.
    """
    # Stub: Return placeholder analysis
    # In M06, this will use LLM to analyze failures
    suggestions: list[tuple[str, str]] = []
    for err in errors:
        suggestions.append((
            err,
            "Review the implementation and update as needed",
        ))
    return suggestions


def _display_analysis(
    payload: ValidationResultPayload,
    suggestions: list[tuple[str, str]],
) -> None:
    """Display failure analysis.

    Args:
        payload: The validation result payload.
        suggestions: List of (error, suggestion) tuples.
    """
    # Status panel
    status_color = "green" if payload.status == ValidationStatus.PASSED else "red"
    console.print(Panel(
        f"[{status_color}]{payload.status.value.upper()}[/{status_color}]",
        title=f"Validation: {payload.target}",
        border_style=status_color,
    ))

    if not suggestions:
        return

    console.print()
    console.print("[bold]Failure Analysis:[/bold]")
    console.print()

    table = Table()
    table.add_column("Error", style="red")
    table.add_column("Suggested Action", style="cyan")

    for err, suggestion in suggestions:
        table.add_row(err, suggestion)

    console.print(table)


@handle_errors
def diagnose(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
) -> None:
    """Analyze test/validation failures and suggest fixes.

    Loads the most recent ValidationResult and provides analysis
    of any failures, with suggestions for how to fix them.

    Currently uses stub analysis. Will use LLM in Milestone 06.
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    # Initialize services
    artifact_service = _get_artifact_service(project_root)

    # Load latest ValidationResult
    try:
        artifacts = artifact_service.storage.list_by_type(
            ArtifactType.VALIDATION_RESULT
        )
    except Exception:
        artifacts = []

    if not artifacts:
        warning("No validation results found")
        info("Run 'rice-factor test' first to generate validation results")
        return

    # Get most recent
    latest = max(artifacts, key=lambda a: a.created_at)
    payload = latest.payload

    if not isinstance(payload, ValidationResultPayload):
        error("Invalid validation result format")
        raise typer.Exit(1)

    console.print()
    console.print(f"[bold]Analyzing:[/bold] {latest.id}")
    console.print(f"[bold]Created:[/bold] {latest.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    console.print()

    # Analyze failures
    errors = payload.errors or []
    suggestions = _analyze_failures(errors)

    # Display analysis
    _display_analysis(payload, suggestions)

    console.print()
    if payload.status == ValidationStatus.PASSED:
        success("No failures to diagnose - all tests passed!")
    else:
        info("Next steps:")
        info("  1. Review the suggested actions above")
        info("  2. Update implementation with 'rice-factor impl <file>'")
        info("  3. Re-run tests with 'rice-factor test'")
