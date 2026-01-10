"""Generate code scaffolding from ScaffoldPlan."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import typer
from rich.table import Table
from rich.tree import Tree

from rice_factor.adapters.audit.trail import AuditTrail
from rice_factor.adapters.llm import create_llm_adapter_from_config
from rice_factor.adapters.llm.stub import StubLLMAdapter

if TYPE_CHECKING:
    from pydantic import BaseModel
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.config.settings import settings
from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.scaffold_plan import FileKind, ScaffoldPlanPayload
from rice_factor.domain.services.artifact_builder import ArtifactBuilder
from rice_factor.domain.services.artifact_service import ArtifactService
from rice_factor.domain.services.context_builder import ContextBuilder, ContextBuilderError
from rice_factor.domain.services.phase_service import PhaseService
from rice_factor.domain.services.scaffold_service import ScaffoldService
from rice_factor.entrypoints.cli.utils import (
    console,
    error,
    handle_errors,
    info,
    success,
    warning,
)

# File kind icons for display
FILE_KIND_ICONS: dict[FileKind, tuple[str, str]] = {
    FileKind.SOURCE: ("[blue]", ""),
    FileKind.TEST: ("[green]", ""),
    FileKind.CONFIG: ("[yellow]⚙", ""),
    FileKind.DOC: ("[cyan]", ""),
}


def _get_services(project_root: Path) -> tuple[ArtifactService, ScaffoldService]:
    """Get artifact and scaffold services for the project.

    Args:
        project_root: The project root directory.

    Returns:
        Tuple of (ArtifactService, ScaffoldService).
    """
    artifacts_dir = project_root / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    approvals = ApprovalsTracker(artifacts_dir=artifacts_dir)
    artifact_service = ArtifactService(storage=storage, approvals=approvals)
    scaffold_service = ScaffoldService(project_root=project_root)
    return artifact_service, scaffold_service


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


def _check_phase(project_root: Path) -> None:
    """Check if scaffold command can be executed.

    Args:
        project_root: The project root directory.

    Raises:
        typer.Exit: If command cannot be executed.
    """
    phase_service = PhaseService(project_root=project_root)
    try:
        phase_service.require_phase("scaffold")
    except Exception as e:
        error(str(e))
        raise typer.Exit(1) from None


def _save_artifact(service: ArtifactService, artifact: ArtifactEnvelope[Any]) -> None:
    """Save an artifact using the service.

    Args:
        service: The artifact service.
        artifact: The artifact to save.
    """
    service.storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))


def _display_preview(
    files: list[tuple[str, FileKind, bool]],
    dry_run: bool = False,
) -> tuple[int, int]:
    """Display a preview of files to be scaffolded.

    Args:
        files: List of (path, kind, would_create) tuples.
        dry_run: If True, show dry run message.

    Returns:
        Tuple of (would_create_count, would_skip_count).
    """
    if dry_run:
        info("Dry run mode - no files will be created")
        console.print()

    tree = Tree("[bold]Scaffold Preview[/bold]")
    would_create = 0
    would_skip = 0

    for path, kind, will_create in files:
        icon_color, icon = FILE_KIND_ICONS.get(kind, ("[white]", ""))
        status = "[green]create[/green]" if will_create else "[yellow]skip[/yellow]"
        tree.add(f"{icon_color}{icon}[/] {path} ({status})")
        if will_create:
            would_create += 1
        else:
            would_skip += 1

    console.print(tree)
    console.print()
    return would_create, would_skip


def _display_result(
    created: list[str],
    skipped: list[str],
    errors: list[tuple[str, str]],
) -> None:
    """Display scaffold result summary.

    Args:
        created: List of created file paths.
        skipped: List of skipped file paths.
        errors: List of (path, error) tuples.
    """
    table = Table(title="Scaffold Summary")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")

    table.add_row("[green]Created[/green]", str(len(created)))
    table.add_row("[yellow]Skipped[/yellow]", str(len(skipped)))
    if errors:
        table.add_row("[red]Errors[/red]", str(len(errors)))

    console.print(table)

    if errors:
        console.print()
        error("Some files could not be created:")
        for path, err in errors:
            console.print(f"  {path}: {err}")


def _display_failure(artifact: ArtifactEnvelope[Any]) -> None:
    """Display failure report details.

    Args:
        artifact: The failure report artifact
    """
    error("Failed to generate ScaffoldPlan")
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
def scaffold(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be created without saving"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
    use_stub: bool = typer.Option(
        False, "--stub", help="Use stub LLM for testing (no API calls)"
    ),
) -> None:
    """Create file structure from ScaffoldPlan.

    Generates a ScaffoldPlan using the LLM, saves it as an artifact, and
    creates the file structure with TODO comments.

    Files that already exist are skipped with a warning.

    Uses the configured LLM provider (set via RICE_LLM_PROVIDER or config).
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    _artifact_service, scaffold_service = _get_services(project_root)
    audit_trail = AuditTrail(project_root=project_root)

    if dry_run:
        # Use stub for dry run to avoid API calls
        llm = StubLLMAdapter()
        payload = llm.generate_scaffold_plan()

        # Preview files
        preview = scaffold_service.preview(payload)
        would_create, would_skip = _display_preview(preview, dry_run=True)

        info("Would create ScaffoldPlan artifact")
        info(f"Would create {would_create} files")
        return

    # For stub mode, use direct StubLLMAdapter without context validation
    # This allows testing without requiring full artifact chain
    if use_stub:
        from rice_factor.domain.artifacts.enums import ArtifactStatus, CreatedBy

        llm = StubLLMAdapter()
        payload = llm.generate_scaffold_plan()
        # Create the artifact envelope
        artifact = ArtifactEnvelope(
            artifact_type=ArtifactType.SCAFFOLD_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=payload,
        )
        artifact_id = artifact.id
        # Save the artifact
        artifact_service, _ = _get_services(project_root)
        _save_artifact(artifact_service, artifact)
    else:
        # Show which LLM we're using
        provider_info = _get_llm_provider_info()
        info(f"Using LLM: {provider_info}")

        # Build ScaffoldPlan artifact using ArtifactBuilder
        try:
            builder = _get_artifact_builder(project_root, use_stub=False)
            built_artifact = builder.build(
                pass_type=CompilerPassType.SCAFFOLD,
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
        if not isinstance(built_artifact.payload, ScaffoldPlanPayload):
            error("Invalid artifact type returned")
            raise typer.Exit(1)

        payload = built_artifact.payload
        artifact_id = built_artifact.id

    # Preview files
    preview = scaffold_service.preview(payload)
    would_create, would_skip = _display_preview(preview)

    if would_create == 0:
        warning("No new files to create - all files already exist")
        return

    # Confirmation
    if not yes:
        console.print(f"This will create [bold]{would_create}[/bold] files.")
        if would_skip > 0:
            console.print(f"[yellow]{would_skip}[/yellow] files will be skipped (already exist).")
        console.print()
        confirm = typer.confirm("Proceed with scaffold?")
        if not confirm:
            info("Scaffold cancelled")
            raise typer.Exit(0)

    success(f"Created ScaffoldPlan artifact: {artifact_id}")

    # Execute scaffold
    result = scaffold_service.scaffold(payload)

    # Record in audit trail
    audit_trail.record_scaffold_executed(
        files_created=len(result.created),
        files_skipped=len(result.skipped),
    )

    # Display result
    _display_result(result.created, result.skipped, result.errors)

    if result.success:
        success(f"Scaffold complete! Created {len(result.created)} files.")
    else:
        error("Scaffold completed with errors")
        raise typer.Exit(1)
