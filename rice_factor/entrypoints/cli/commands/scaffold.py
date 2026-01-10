"""Generate code scaffolding from ScaffoldPlan."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import typer
from rich.table import Table
from rich.tree import Tree

from rice_factor.adapters.llm.stub import StubLLMAdapter

if TYPE_CHECKING:
    from pydantic import BaseModel
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.scaffold_plan import FileKind
from rice_factor.domain.services.artifact_service import ArtifactService
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


@handle_errors
def scaffold(
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be created without saving"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """Create file structure from ScaffoldPlan.

    Generates a ScaffoldPlan using the LLM (stub for now), saves it as an
    artifact, and creates the file structure with TODO comments.

    Files that already exist are skipped with a warning.
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    artifact_service, scaffold_service = _get_services(project_root)

    # Generate scaffold plan using stub LLM
    llm = StubLLMAdapter()
    payload = llm.generate_scaffold_plan()

    # Preview files
    preview = scaffold_service.preview(payload)
    would_create, would_skip = _display_preview(preview, dry_run=dry_run)

    if would_create == 0:
        warning("No new files to create - all files already exist")
        return

    # Confirmation
    if not dry_run and not yes:
        console.print(f"This will create [bold]{would_create}[/bold] files.")
        if would_skip > 0:
            console.print(f"[yellow]{would_skip}[/yellow] files will be skipped (already exist).")
        console.print()
        confirm = typer.confirm("Proceed with scaffold?")
        if not confirm:
            info("Scaffold cancelled")
            raise typer.Exit(0)

    # Create artifact envelope
    artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
        artifact_type=ArtifactType.SCAFFOLD_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=payload,
    )

    if dry_run:
        info("Would create ScaffoldPlan artifact")
        info(f"Would create {would_create} files")
        return

    # Save artifact
    _save_artifact(artifact_service, artifact)
    success(f"Created ScaffoldPlan artifact: {artifact.id}")

    # Execute scaffold
    result = scaffold_service.scaffold(payload)

    # Display result
    _display_result(result.created, result.skipped, result.errors)

    if result.success:
        success(f"Scaffold complete! Created {len(result.created)} files.")
    else:
        error("Scaffold completed with errors")
        raise typer.Exit(1)
