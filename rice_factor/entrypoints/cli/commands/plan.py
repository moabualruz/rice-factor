"""Generate planning artifacts via rice-factor plan commands."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import typer

from rice_factor.adapters.llm import create_llm_adapter_from_config
from rice_factor.adapters.llm.stub import StubLLMAdapter

if TYPE_CHECKING:
    from pydantic import BaseModel
from rice_factor.adapters.executors.audit_logger import AuditLogger
from rice_factor.adapters.llm import LLMAdapter
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.config.settings import settings
from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.services.artifact_builder import ArtifactBuilder
from rice_factor.domain.services.artifact_service import ArtifactService
from rice_factor.domain.services.context_builder import ContextBuilder, ContextBuilderError
from rice_factor.domain.services.intake_validator import IntakeValidator
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


def _get_artifact_builder(project_root: Path, use_stub: bool = False) -> ArtifactBuilder:
    """Create an artifact builder with configured LLM.

    Args:
        project_root: Root directory of the project
        use_stub: If True, use StubLLMAdapter instead of real LLM

    Returns:
        Configured ArtifactBuilder
    """
    artifacts_dir = project_root / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    context_builder = ContextBuilder(storage_adapter=storage)

    llm: LLMAdapter = StubLLMAdapter() if use_stub else create_llm_adapter_from_config()

    return ArtifactBuilder(
        llm_port=llm,  # type: ignore[arg-type]  # LLM adapters implement LLMPort
        storage=storage,  # type: ignore[arg-type]  # FilesystemStorageAdapter implements StoragePort
        context_builder=context_builder,
    )


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


def _validate_intake(project_root: Path) -> None:
    """Validate intake files before planning.

    Ensures all required files exist and have meaningful content.
    This enforces "clarity before intelligence" - LLM cannot proceed
    without well-defined inputs.

    Args:
        project_root: Root directory of the project

    Raises:
        typer.Exit: If intake validation fails
    """
    project_dir = project_root / ".project"
    validator = IntakeValidator(project_dir=project_dir)
    result = validator.validate()

    if not result.valid:
        error("Intake validation failed")
        console.print()
        console.print(result.format_errors())
        raise typer.Exit(1)


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


def _display_failure(artifact: ArtifactEnvelope[Any]) -> None:
    """Display failure report details.

    Args:
        artifact: The failure report artifact
    """
    error("Failed to generate artifact")
    if hasattr(artifact.payload, "summary"):
        console.print(f"  [red]Error:[/red] {artifact.payload.summary}")
    if hasattr(artifact.payload, "details"):
        details = artifact.payload.details
        if isinstance(details, dict):
            for key, value in details.items():
                console.print(f"  [dim]{key}:[/dim] {value}")
    if hasattr(artifact.payload, "recovery_action"):
        info(f"Recovery: {artifact.payload.recovery_action.value}")


def _save_artifact(service: ArtifactService, artifact: ArtifactEnvelope[Any]) -> None:
    """Save an artifact using the service.

    Args:
        service: The artifact service
        artifact: The artifact to save
    """
    # Cast to satisfy mypy - the generic type is compatible
    service.storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))


def _get_llm_provider_info() -> str:
    """Get description of the configured LLM provider.

    Returns:
        String describing the LLM provider and model
    """
    provider = settings.get("llm.provider", "claude")
    if provider == "claude":
        model = settings.get("llm.model", "claude-3-5-sonnet-20241022")
    elif provider == "openai":
        model = settings.get("openai.model", "gpt-4-turbo")
    else:
        model = "stub"
    return f"{provider}/{model}"


@app.command()
@handle_errors
def project(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be created without saving"
    ),
    use_stub: bool = typer.Option(
        False, "--stub", help="Use stub LLM for testing (no API calls)"
    ),
) -> None:
    """Generate a ProjectPlan artifact.

    Defines the project structure including domains, modules, and constraints.
    Requires project to be initialized (Phase: INIT+).

    Uses the configured LLM provider (set via RICE_LLM_PROVIDER or config).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan project")

    # Validate intake files
    _validate_intake(project_root)

    if dry_run:
        # Use stub for dry run to avoid API calls
        llm = StubLLMAdapter()
        payload = llm.generate_project_plan()
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create ProjectPlan:[/bold]")
        console.print(f"  Domains: {len(payload.domains)}")
        console.print(f"  Modules: {len(payload.modules)}")
        console.print(f"  Architecture: {payload.constraints.architecture.value}")
        return

    # Show which LLM we're using
    provider_info = _get_llm_provider_info()
    if not use_stub:
        info(f"Using LLM: {provider_info}")

    # Build artifact using ArtifactBuilder
    try:
        builder = _get_artifact_builder(project_root, use_stub=use_stub)
        artifact = builder.build(
            pass_type=CompilerPassType.PROJECT,
            project_root=project_root,
        )
    except ContextBuilderError as e:
        error(f"Context error: {e}")
        raise typer.Exit(1) from None

    # Check if it's a failure report
    if artifact.artifact_type == ArtifactType.FAILURE_REPORT:
        _display_failure(artifact)
        raise typer.Exit(1)

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
    use_stub: bool = typer.Option(
        False, "--stub", help="Use stub LLM for testing (no API calls)"
    ),
) -> None:
    """Generate an ArchitecturePlan artifact.

    Defines dependency laws and architectural layers.
    Requires ProjectPlan to be approved (Phase: PLANNING+).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan architecture")

    # Validate intake files
    _validate_intake(project_root)

    if dry_run:
        # Use stub for dry run to avoid API calls
        llm = StubLLMAdapter()
        payload = llm.generate_architecture_plan()
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create ArchitecturePlan:[/bold]")
        console.print(f"  Layers: {', '.join(payload.layers)}")
        console.print(f"  Rules: {len(payload.rules)}")
        return

    # Show which LLM we're using
    provider_info = _get_llm_provider_info()
    if not use_stub:
        info(f"Using LLM: {provider_info}")

    # Build artifact using ArtifactBuilder
    try:
        builder = _get_artifact_builder(project_root, use_stub=use_stub)
        artifact = builder.build(
            pass_type=CompilerPassType.ARCHITECTURE,
            project_root=project_root,
        )
    except ContextBuilderError as e:
        error(f"Context error: {e}")
        raise typer.Exit(1) from None

    # Check if it's a failure report
    if artifact.artifact_type == ArtifactType.FAILURE_REPORT:
        _display_failure(artifact)
        raise typer.Exit(1)

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
    use_stub: bool = typer.Option(
        False, "--stub", help="Use stub LLM for testing (no API calls)"
    ),
) -> None:
    """Generate a TestPlan artifact.

    Defines the tests that verify correctness.
    Requires project to be scaffolded (Phase: SCAFFOLDED+).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan tests")

    # Validate intake files
    _validate_intake(project_root)

    if dry_run:
        # Use stub for dry run to avoid API calls
        llm = StubLLMAdapter()
        payload = llm.generate_test_plan()
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create TestPlan:[/bold]")
        console.print(f"  Tests: {len(payload.tests)}")
        for test in payload.tests[:3]:  # Show first 3
            console.print(f"    - {test.id}: {test.target}")
        if len(payload.tests) > 3:
            console.print(f"    ... and {len(payload.tests) - 3} more")
        return

    # Show which LLM we're using
    provider_info = _get_llm_provider_info()
    if not use_stub:
        info(f"Using LLM: {provider_info}")

    # Build artifact using ArtifactBuilder
    try:
        builder = _get_artifact_builder(project_root, use_stub=use_stub)
        artifact = builder.build(
            pass_type=CompilerPassType.TEST,
            project_root=project_root,
        )
    except ContextBuilderError as e:
        error(f"Context error: {e}")
        raise typer.Exit(1) from None

    # Check if it's a failure report
    if artifact.artifact_type == ArtifactType.FAILURE_REPORT:
        _display_failure(artifact)
        raise typer.Exit(1)

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
    use_stub: bool = typer.Option(
        False, "--stub", help="Use stub LLM for testing (no API calls)"
    ),
) -> None:
    """Generate an ImplementationPlan artifact for a specific file.

    Defines implementation steps for a single target file.
    Requires TestPlan to be locked (Phase: TEST_LOCKED+).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan impl")

    # Validate intake files
    _validate_intake(project_root)

    # Verify TestPlan lock integrity (GAP-M07-002)
    audit_logger = AuditLogger(project_root=project_root)
    try:
        safety = SafetyEnforcer(project_root=project_root)
        result = safety.check_test_lock_intact()
        if not result.is_valid:
            # Log the failure before raising
            audit_logger.log_safety_check(
                check_type="lock_verification",
                passed=False,
                details={"modified_files": result.modified_files},
                command="plan impl",
            )
            safety.require_test_lock_intact()  # This raises the proper error
        else:
            # Log successful verification
            audit_logger.log_safety_check(
                check_type="lock_verification",
                passed=True,
                command="plan impl",
            )
    except Exception as e:
        error(f"Lock verification failed: {e}")
        raise typer.Exit(1) from None

    if dry_run:
        # Use stub for dry run to avoid API calls
        llm = StubLLMAdapter()
        payload = llm.generate_implementation_plan(target)
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create ImplementationPlan:[/bold]")
        console.print(f"  Target: {payload.target}")
        console.print(f"  Steps: {len(payload.steps)}")
        for i, step in enumerate(payload.steps, 1):
            console.print(f"    {i}. {step}")
        return

    # Show which LLM we're using
    provider_info = _get_llm_provider_info()
    if not use_stub:
        info(f"Using LLM: {provider_info}")

    # Build artifact using ArtifactBuilder
    try:
        builder = _get_artifact_builder(project_root, use_stub=use_stub)
        artifact = builder.build(
            pass_type=CompilerPassType.IMPLEMENTATION,
            project_root=project_root,
            target_file=target,
        )
    except ContextBuilderError as e:
        error(f"Context error: {e}")
        raise typer.Exit(1) from None

    # Check if it's a failure report
    if artifact.artifact_type == ArtifactType.FAILURE_REPORT:
        _display_failure(artifact)
        raise typer.Exit(1)

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
    use_stub: bool = typer.Option(
        False, "--stub", help="Use stub LLM for testing (no API calls)"
    ),
) -> None:
    """Generate a RefactorPlan artifact.

    Defines structural changes that preserve behavior.
    Requires TestPlan to be locked (Phase: TEST_LOCKED+).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root, "plan refactor")

    # Validate intake files
    _validate_intake(project_root)

    # Verify TestPlan lock integrity (GAP-M07-002)
    audit_logger = AuditLogger(project_root=project_root)
    try:
        safety = SafetyEnforcer(project_root=project_root)
        result = safety.check_test_lock_intact()
        if not result.is_valid:
            # Log the failure before raising
            audit_logger.log_safety_check(
                check_type="lock_verification",
                passed=False,
                details={"modified_files": result.modified_files},
                command="plan refactor",
            )
            safety.require_test_lock_intact()  # This raises the proper error
        else:
            # Log successful verification
            audit_logger.log_safety_check(
                check_type="lock_verification",
                passed=True,
                command="plan refactor",
            )
    except Exception as e:
        error(f"Lock verification failed: {e}")
        raise typer.Exit(1) from None

    if dry_run:
        # Use stub for dry run to avoid API calls
        llm = StubLLMAdapter()
        payload = llm.generate_refactor_plan(goal)
        info("Dry run mode - artifact not saved")
        console.print()
        console.print("[bold]Would create RefactorPlan:[/bold]")
        console.print(f"  Goal: {payload.goal}")
        console.print(f"  Operations: {len(payload.operations)}")
        for op in payload.operations:
            console.print(f"    - {op.type.value}")
        return

    # Show which LLM we're using
    provider_info = _get_llm_provider_info()
    if not use_stub:
        info(f"Using LLM: {provider_info}")

    # Build artifact using ArtifactBuilder
    try:
        builder = _get_artifact_builder(project_root, use_stub=use_stub)
        artifact = builder.build(
            pass_type=CompilerPassType.REFACTOR,
            project_root=project_root,
            # Note: goal would be passed via artifacts parameter in full implementation
        )
    except ContextBuilderError as e:
        error(f"Context error: {e}")
        raise typer.Exit(1) from None

    # Check if it's a failure report
    if artifact.artifact_type == ArtifactType.FAILURE_REPORT:
        _display_failure(artifact)
        raise typer.Exit(1)

    # Display success
    file_path = (
        project_root
        / "artifacts"
        / "refactor_plans"
        / f"{artifact.id}.json"
    )
    _display_artifact_created(ArtifactType.REFACTOR_PLAN, str(artifact.id), file_path)
