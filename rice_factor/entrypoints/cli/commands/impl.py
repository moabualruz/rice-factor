"""Implement code based on ImplementationPlan."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import typer
from rich.syntax import Syntax

from rice_factor.adapters.audit.trail import AuditTrail
from rice_factor.adapters.llm import create_llm_adapter_from_config
from rice_factor.adapters.llm.stub import StubLLMAdapter
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.config.settings import settings
from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.implementation_plan import (
    ImplementationPlanPayload,
)
from rice_factor.domain.services.artifact_builder import ArtifactBuilder
from rice_factor.domain.services.artifact_service import ArtifactService
from rice_factor.domain.services.context_builder import ContextBuilder, ContextBuilderError
from rice_factor.domain.services.diff_service import DiffService
from rice_factor.domain.services.phase_service import PhaseService
from rice_factor.domain.services.safety_enforcer import SafetyEnforcer
from rice_factor.entrypoints.cli.utils import (
    console,
    error,
    handle_errors,
    info,
    success,
)

if TYPE_CHECKING:
    from pydantic import BaseModel


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
    console.print()
    console.print(f"[bold]Diff for {target_file}:[/bold]")
    console.print()
    syntax = Syntax(content, "diff", theme="monokai", line_numbers=True)
    console.print(syntax)
    console.print()


def _get_services(project_root: Path) -> tuple[ArtifactService, DiffService]:
    """Get artifact and diff services for the project.

    Args:
        project_root: The project root directory.

    Returns:
        Tuple of (ArtifactService, DiffService).
    """
    artifacts_dir = project_root / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    approvals = ApprovalsTracker(artifacts_dir=artifacts_dir)
    artifact_service = ArtifactService(storage=storage, approvals=approvals)
    diff_service = DiffService(project_root=project_root)
    return artifact_service, diff_service


def _get_artifact_builder(project_root: Path, use_stub: bool = False) -> ArtifactBuilder:
    """Create an artifact builder with configured LLM.

    Args:
        project_root: Root directory of the project
        use_stub: If True, use StubLLMAdapter instead of real LLM

    Returns:
        Configured ArtifactBuilder
    """
    from rice_factor.adapters.llm import LLMAdapter

    artifacts_dir = project_root / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    context_builder = ContextBuilder(storage_adapter=storage)

    llm: LLMAdapter = StubLLMAdapter() if use_stub else create_llm_adapter_from_config()

    return ArtifactBuilder(
        llm_port=llm,  # type: ignore[arg-type]  # LLM adapters implement LLMPort
        storage=storage,  # type: ignore[arg-type]  # FilesystemStorageAdapter implements StoragePort
        context_builder=context_builder,
    )


def _save_artifact(service: ArtifactService, artifact: ArtifactEnvelope[Any]) -> None:
    """Save an artifact using the service.

    Args:
        service: The artifact service.
        artifact: The artifact to save.
    """
    service.storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))


def _display_failure(artifact: ArtifactEnvelope[Any]) -> None:
    """Display failure report details.

    Args:
        artifact: The failure report artifact
    """
    error("Failed to generate ImplementationPlan")
    if hasattr(artifact.payload, "summary"):
        console.print(f"  [red]Error:[/red] {artifact.payload.summary}")
    if hasattr(artifact.payload, "details"):
        details = artifact.payload.details
        if isinstance(details, dict):
            for key, value in details.items():
                console.print(f"  [dim]{key}:[/dim] {value}")
    if hasattr(artifact.payload, "recovery_action"):
        info(f"Recovery: {artifact.payload.recovery_action.value}")


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


@handle_errors
def impl(
    file_path: str = typer.Argument(..., help="Path to the file to implement"),
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be done without saving"
    ),
    use_stub: bool = typer.Option(
        False, "--stub", help="Use stub LLM for testing (no API calls)"
    ),
) -> None:
    """Generate implementation diff for a specific file.

    Creates a diff based on the ImplementationPlan for the target file.
    The diff is saved to audit/diffs/ and marked as pending review.

    Uses the configured LLM provider (set via RICE_LLM_PROVIDER or config).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    # Verify test lock is intact (M07-E-001)
    _check_test_lock(project_root)

    # Initialize services
    artifact_service, diff_service = _get_services(project_root)
    audit_trail = AuditTrail(project_root=project_root)

    # For stub mode, use direct StubLLMAdapter without context validation
    if use_stub:
        info(f"Generating implementation for {file_path} (stub mode)...")
        diff = diff_service.generate_diff(target_file=file_path)

        # Create a stub ImplementationPlan artifact
        llm = StubLLMAdapter()
        payload = llm.generate_implementation_plan(target=file_path)
        artifact = ArtifactEnvelope(
            artifact_type=ArtifactType.IMPLEMENTATION_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=payload,
        )
        # Save the artifact
        _save_artifact(artifact_service, artifact)
        success(f"Created ImplementationPlan artifact: {artifact.id}")
    else:
        # Show which LLM we're using
        provider_info = _get_llm_provider_info()
        info(f"Using LLM: {provider_info}")
        info(f"Generating implementation for {file_path}...")

        # Build ImplementationPlan artifact using ArtifactBuilder
        try:
            builder = _get_artifact_builder(project_root, use_stub=False)
            built_artifact = builder.build(
                pass_type=CompilerPassType.IMPLEMENTATION,
                project_root=project_root,
            )
        except ContextBuilderError as e:
            error(f"Context error: {e}")
            raise typer.Exit(1) from None

        # Check if it's a failure report
        if built_artifact.artifact_type == ArtifactType.FAILURE_REPORT:
            _display_failure(built_artifact)
            raise typer.Exit(1)

        # Get the payload
        if not isinstance(built_artifact.payload, ImplementationPlanPayload):
            error("Invalid artifact type returned")
            raise typer.Exit(1)

        success(f"Created ImplementationPlan artifact: {built_artifact.id}")

        # Generate diff from implementation plan
        diff = diff_service.generate_diff(
            target_file=file_path,
            plan_id=built_artifact.id,
        )

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
