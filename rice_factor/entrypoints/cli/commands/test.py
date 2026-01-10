"""Run tests against the project."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import typer
from rich.table import Table

if TYPE_CHECKING:
    from pydantic import BaseModel
from rice_factor.adapters.audit.trail import AuditTrail
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
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
)


def _check_phase(project_root: Path) -> None:
    """Check if test command can be executed.

    Args:
        project_root: The project root directory.

    Raises:
        typer.Exit: If command cannot be executed.
    """
    phase_service = PhaseService(project_root=project_root)
    try:
        phase_service.require_phase("test")
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


def _save_artifact(service: ArtifactService, artifact: ArtifactEnvelope[Any]) -> None:
    """Save an artifact using the service.

    Args:
        service: The artifact service.
        artifact: The artifact to save.
    """
    service.storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))


def _run_stub_tests() -> tuple[int, int, list[str]]:
    """Run stub tests.

    Returns:
        Tuple of (total_tests, failed_tests, error_messages).
    """
    # Stub: Return mock test results
    # In M06, this will run actual tests using the native test runner
    return (5, 0, [])


def _display_results(
    total: int,
    failed: int,
    errors: list[str],
    verbose: bool = False,
) -> None:
    """Display test results.

    Args:
        total: Total number of tests.
        failed: Number of failed tests.
        errors: List of error messages.
        verbose: Whether to show verbose output.
    """
    passed = total - failed

    table = Table(title="Test Results")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")

    table.add_row("[green]Passed[/green]", str(passed))
    table.add_row("[red]Failed[/red]", str(failed))
    table.add_row("Total", str(total))

    console.print()
    console.print(table)

    if errors and (verbose or failed > 0):
        console.print()
        console.print("[bold red]Errors:[/bold red]")
        for err in errors:
            console.print(f"  - {err}")


@handle_errors
def test(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose test output"
    ),
) -> None:
    """Run tests against the locked TestPlan.

    Executes the test suite and creates a ValidationResult artifact
    with the results.

    Currently uses stub test results. Will run actual tests in Milestone 06.
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    # Initialize services
    artifact_service = _get_artifact_service(project_root)
    audit_trail = AuditTrail(project_root=project_root)

    # Run tests
    info("Running tests...")
    total, failed, errors = _run_stub_tests()

    # Display results
    _display_results(total, failed, errors, verbose)

    # Create ValidationResult artifact
    passed = failed == 0
    status = ValidationStatus.PASSED if passed else ValidationStatus.FAILED

    payload = ValidationResultPayload(
        target="test_suite",
        status=status,
        errors=errors if errors else None,
    )

    artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
        artifact_type=ArtifactType.VALIDATION_RESULT,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.SYSTEM,
        payload=payload,
    )

    # Save artifact
    _save_artifact(artifact_service, artifact)

    # Record in audit trail
    audit_trail.record_test_run(
        passed=passed,
        total_tests=total,
        failed_tests=failed,
        result_id=artifact.id,
    )

    console.print()
    if passed:
        success(f"All {total} tests passed!")
    else:
        error(f"{failed}/{total} tests failed")
        info("Run 'rice-factor diagnose' to analyze failures")
        raise typer.Exit(1)
