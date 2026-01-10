"""Validation commands for checking artifacts and code.

This module provides the validate command for running schema, architecture,
test, and lint validations on a project.
"""

from pathlib import Path
from typing import TYPE_CHECKING, cast

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from pydantic import BaseModel

from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.validation_result import (
    ValidationResultPayload,
    ValidationStatus,
)
from rice_factor.domain.services.artifact_service import ArtifactService
from rice_factor.domain.services.phase_service import Phase, PhaseService
from rice_factor.domain.services.validation_orchestrator import (
    StepResult,
    ValidationOrchestrator,
    ValidationStep,
)

console = Console()


def _check_phase(project_path: Path) -> bool:
    """Check that the project is initialized."""
    artifacts_dir = project_path / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    approvals = ApprovalsTracker(artifacts_dir=artifacts_dir)
    artifact_service = ArtifactService(storage=storage, approvals=approvals)

    phase_service = PhaseService(project_path, artifact_service=artifact_service)
    current_phase = phase_service.get_current_phase()

    if current_phase == Phase.UNINIT:
        console.print(
            "[red]Error:[/red] Project not initialized. Run 'rice-factor init' first."
        )
        return False

    return True


def _display_results_table(results: list[StepResult]) -> None:
    """Display validation results in a table."""
    table = Table(title="Validation Results", show_header=True)
    table.add_column("Step", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Errors", style="dim")
    table.add_column("Details", style="dim")

    for result in results:
        status_icon = (
            "[green]✓ PASSED[/green]"
            if result.status == ValidationStatus.PASSED
            else "[red]✗ FAILED[/red]"
        )
        error_count = str(len(result.errors)) if result.errors else "-"

        # Get stub message or artifact count
        detail = ""
        if "stub" in result.details:
            detail = "[yellow]stubbed[/yellow]"
        elif "artifacts_validated" in result.details:
            detail = f"{result.details['artifacts_validated']} artifacts"
        elif "message" in result.details:
            detail = result.details["message"][:30]

        table.add_row(result.step.value, status_icon, error_count, detail)

    console.print(table)


def _display_errors(results: list[StepResult]) -> None:
    """Display detailed errors for failed steps."""
    for result in results:
        if result.errors:
            console.print(f"\n[red]Errors in {result.step.value}:[/red]")
            for error in result.errors:
                console.print(f"  [red]•[/red] {error}")


def validate(
    project_path: Path = typer.Option(
        Path.cwd(), "--path", "-p", help="Path to project directory"
    ),
    step: str | None = typer.Option(
        None,
        "--step",
        "-s",
        help="Run specific validation step (schema, architecture, tests, lint)",
    ),
    save_artifact: bool = typer.Option(
        True, "--save/--no-save", help="Save ValidationResult artifact"
    ),
) -> None:
    """Run validations on project artifacts and code.

    Runs schema, architecture, test, and lint validations. Results are
    displayed in a summary table with detailed error output.

    Use --step to run a specific validation only.
    """
    if not _check_phase(project_path):
        raise typer.Exit(code=1)

    orchestrator = ValidationOrchestrator(project_path=project_path)

    # Run specific step or all
    if step:
        try:
            validation_step = ValidationStep(step.lower())
        except ValueError:
            valid_steps = ", ".join(s.value for s in ValidationStep)
            console.print(
                f"[red]Error:[/red] Invalid step '{step}'. "
                f"Valid options: {valid_steps}"
            )
            raise typer.Exit(code=1) from None

        console.print(
            Panel(
                f"[bold]Running {validation_step.value} validation...[/bold]",
                title="Validation",
                border_style="cyan",
            )
        )

        result = orchestrator.run_step(validation_step)
        step_results = [result]
        overall_passed = result.status == ValidationStatus.PASSED
    else:
        console.print(
            Panel(
                "[bold]Running all validations...[/bold]\n\n"
                "• Schema validation\n"
                "• Architecture rules\n"
                "• Test suite\n"
                "• Lint checks",
                title="Validation",
                border_style="cyan",
            )
        )

        validation_result = orchestrator.run_all()
        step_results = validation_result.step_results
        overall_passed = validation_result.passed

    # Display results
    _display_results_table(step_results)

    # Display detailed errors
    _display_errors(step_results)

    # Summary
    passed_count = sum(
        1 for r in step_results if r.status == ValidationStatus.PASSED
    )
    failed_count = len(step_results) - passed_count

    if overall_passed:
        console.print(
            f"\n[green]✓[/green] All {passed_count} validation(s) passed."
        )
    else:
        console.print(
            f"\n[red]✗[/red] {failed_count} validation(s) failed, "
            f"{passed_count} passed."
        )

    # Save ValidationResult artifact
    if save_artifact:
        artifacts_dir = project_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)

        # Collect all errors
        all_errors = []
        for result in step_results:
            for error in result.errors:
                all_errors.append(f"[{result.step.value}] {error}")

        payload = ValidationResultPayload(
            target="project",
            status=(
                ValidationStatus.PASSED if overall_passed else ValidationStatus.FAILED
            ),
            errors=all_errors if all_errors else None,
        )

        envelope: ArtifactEnvelope[ValidationResultPayload] = ArtifactEnvelope(
            artifact_type=ArtifactType.VALIDATION_RESULT,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.SYSTEM,
            payload=payload,
        )

        storage.save(cast("ArtifactEnvelope[BaseModel]", envelope))
        console.print(f"\n[dim]ValidationResult saved: {envelope.id}[/dim]")

    if not overall_passed:
        raise typer.Exit(code=1)
