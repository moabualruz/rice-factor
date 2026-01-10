"""Generate planning artifacts via rice-factor plan commands."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import typer

from rice_factor.adapters.llm.stub import StubLLMAdapter

if TYPE_CHECKING:
    from pydantic import BaseModel
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
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

app = typer.Typer(help="Generate planning artifacts")


def _get_artifact_service(project_root: Path) -> ArtifactService:
    """Create an artifact service for the given project root.

    Args:
        project_root: Root directory of the project

    Returns:
        Configured ArtifactService
    """
    artifacts_dir = project_root / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    approvals = ApprovalsTracker(artifacts_dir=artifacts_dir)
    return ArtifactService(storage=storage, approvals=approvals)


def _check_phase(project_root: Path, command: str) -> None:
    """Check if the current project phase allows the command.

    Args:
        project_root: Root directory of the project
        command: Command name for phase checking

    Raises:
        typer.Exit: If phase requirement is not met
    """
    phase_service = PhaseService(project_root=project_root)
    try:
        phase_service.require_phase(command)
    except Exception as e:
        error(str(e))
        raise typer.Exit(1) from None


def _display_artifact_created(
    artifact_type: ArtifactType,
    artifact_id: str,
    file_path: Path,
) -> None:
    """Display artifact creation success message.

    Args:
        artifact_type: Type of artifact created
        artifact_id: UUID of the created artifact
        file_path: Path where artifact was saved
    """
    console.print()
    success(f"Created {artifact_type.value} artifact")
    console.print(f"  [dim]ID:[/dim] {artifact_id}")
    console.print(f"  [dim]File:[/dim] {file_path}")
    console.print()
    info(f"Run 'rice-factor approve {artifact_id}' to approve this artifact")


def _save_artifact(service: ArtifactService, artifact: ArtifactEnvelope[Any]) -> None:
    """Save an artifact using the service.

    Args:
        service: The artifact service
        artifact: The artifact to save
    """
    # Cast to satisfy mypy - the generic type is compatible
    service.storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))


@app.command()
@handle_errors
def project(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be created without saving"
    ),
) -> None:
    """Generate a ProjectPlan artifact.

    Defines the project structure including domains, modules, and constraints.
    Requires project to be initialized (Phase: INIT+).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan project")

    # Generate stub payload
    llm = StubLLMAdapter()
    payload = llm.generate_project_plan()

    # Create envelope
    artifact = ArtifactEnvelope(
        artifact_type=ArtifactType.PROJECT_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=payload,
    )

    if dry_run:
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create ProjectPlan:[/bold]")
        console.print(f"  Domains: {len(payload.domains)}")
        console.print(f"  Modules: {len(payload.modules)}")
        console.print(f"  Architecture: {payload.constraints.architecture.value}")
        return

    # Save artifact
    service = _get_artifact_service(project_root)
    _save_artifact(service, artifact)

    # Display success
    file_path = (
        project_root
        / "artifacts"
        / "project_plans"
        / f"{artifact.id}.json"
    )
    _display_artifact_created(ArtifactType.PROJECT_PLAN, str(artifact.id), file_path)


@app.command()
@handle_errors
def architecture(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be created without saving"
    ),
) -> None:
    """Generate an ArchitecturePlan artifact.

    Defines dependency laws and architectural layers.
    Requires ProjectPlan to be approved (Phase: PLANNING+).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan architecture")

    # Generate stub payload
    llm = StubLLMAdapter()
    payload = llm.generate_architecture_plan()

    # Create envelope
    artifact = ArtifactEnvelope(
        artifact_type=ArtifactType.ARCHITECTURE_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=payload,
    )

    if dry_run:
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create ArchitecturePlan:[/bold]")
        console.print(f"  Layers: {', '.join(payload.layers)}")
        console.print(f"  Rules: {len(payload.rules)}")
        return

    # Save artifact
    service = _get_artifact_service(project_root)
    _save_artifact(service, artifact)

    # Display success
    file_path = (
        project_root
        / "artifacts"
        / "architecture_plans"
        / f"{artifact.id}.json"
    )
    _display_artifact_created(
        ArtifactType.ARCHITECTURE_PLAN, str(artifact.id), file_path
    )


@app.command()
@handle_errors
def tests(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be created without saving"
    ),
) -> None:
    """Generate a TestPlan artifact.

    Defines the tests that verify correctness.
    Requires project to be scaffolded (Phase: SCAFFOLDED+).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan tests")

    # Generate stub payload
    llm = StubLLMAdapter()
    payload = llm.generate_test_plan()

    # Create envelope
    artifact = ArtifactEnvelope(
        artifact_type=ArtifactType.TEST_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=payload,
    )

    if dry_run:
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create TestPlan:[/bold]")
        console.print(f"  Tests: {len(payload.tests)}")
        for test in payload.tests[:3]:  # Show first 3
            console.print(f"    - {test.id}: {test.target}")
        if len(payload.tests) > 3:
            console.print(f"    ... and {len(payload.tests) - 3} more")
        return

    # Save artifact
    service = _get_artifact_service(project_root)
    _save_artifact(service, artifact)

    # Display success
    file_path = (
        project_root / "artifacts" / "test_plans" / f"{artifact.id}.json"
    )
    _display_artifact_created(ArtifactType.TEST_PLAN, str(artifact.id), file_path)
    warning("TestPlan must be locked before implementation can begin")


@app.command("impl")
@handle_errors
def implementation(
    target: str = typer.Argument(..., help="Target file to generate implementation for"),
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be created without saving"
    ),
) -> None:
    """Generate an ImplementationPlan artifact for a specific file.

    Defines implementation steps for a single target file.
    Requires TestPlan to be locked (Phase: TEST_LOCKED+).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan impl")

    # Generate stub payload
    llm = StubLLMAdapter()
    payload = llm.generate_implementation_plan(target)

    # Create envelope
    artifact = ArtifactEnvelope(
        artifact_type=ArtifactType.IMPLEMENTATION_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=payload,
    )

    if dry_run:
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create ImplementationPlan:[/bold]")
        console.print(f"  Target: {payload.target}")
        console.print(f"  Steps: {len(payload.steps)}")
        for i, step in enumerate(payload.steps, 1):
            console.print(f"    {i}. {step}")
        return

    # Save artifact
    service = _get_artifact_service(project_root)
    _save_artifact(service, artifact)

    # Display success
    file_path = (
        project_root
        / "artifacts"
        / "implementation_plans"
        / f"{artifact.id}.json"
    )
    _display_artifact_created(
        ArtifactType.IMPLEMENTATION_PLAN, str(artifact.id), file_path
    )


@app.command()
@handle_errors
def refactor(
    goal: str = typer.Argument(..., help="Goal of the refactoring"),
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be created without saving"
    ),
) -> None:
    """Generate a RefactorPlan artifact.

    Defines structural changes that preserve behavior.
    Requires TestPlan to be locked (Phase: TEST_LOCKED+).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan refactor")

    # Generate stub payload
    llm = StubLLMAdapter()
    payload = llm.generate_refactor_plan(goal)

    # Create envelope
    artifact = ArtifactEnvelope(
        artifact_type=ArtifactType.REFACTOR_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=payload,
    )

    if dry_run:
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create RefactorPlan:[/bold]")
        console.print(f"  Goal: {payload.goal}")
        console.print(f"  Operations: {len(payload.operations)}")
        for op in payload.operations:
            console.print(f"    - {op.type.value}")
        return

    # Save artifact
    service = _get_artifact_service(project_root)
    _save_artifact(service, artifact)

    # Display success
    file_path = (
        project_root
        / "artifacts"
        / "refactor_plans"
        / f"{artifact.id}.json"
    )
    _display_artifact_created(ArtifactType.REFACTOR_PLAN, str(artifact.id), file_path)
