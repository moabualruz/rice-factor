"""Approve artifacts for progression."""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.audit.trail import AuditTrail
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus
from rice_factor.domain.services.artifact_resolver import ArtifactResolver
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
    """Check if approve command can be executed.

    Args:
        project_root: The project root directory.

    Raises:
        typer.Exit: If command cannot be executed.
    """
    phase_service = PhaseService(project_root=project_root)
    try:
        phase_service.require_phase("approve")
    except Exception as e:
        error(str(e))
        raise typer.Exit(1) from None


def _get_services(
    project_root: Path,
) -> tuple[ArtifactService, ArtifactResolver, AuditTrail]:
    """Get services for the approve command.

    Args:
        project_root: The project root directory.

    Returns:
        Tuple of (ArtifactService, ArtifactResolver, AuditTrail).
    """
    artifacts_dir = project_root / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    approvals = ApprovalsTracker(artifacts_dir=artifacts_dir)
    artifact_service = ArtifactService(storage=storage, approvals=approvals)
    resolver = ArtifactResolver(storage=storage)
    audit_trail = AuditTrail(project_root=project_root)
    return artifact_service, resolver, audit_trail


def _display_artifact_summary(
    artifact_id: str,
    artifact_type: str,
    status: ArtifactStatus,
    created_at: str,
    created_by: str,
) -> None:
    """Display artifact summary in a Rich panel.

    Args:
        artifact_id: The artifact UUID.
        artifact_type: The artifact type name.
        status: Current status.
        created_at: Creation timestamp.
        created_by: Creator identifier.
    """
    # Status color
    status_colors = {
        ArtifactStatus.DRAFT: "yellow",
        ArtifactStatus.APPROVED: "green",
        ArtifactStatus.LOCKED: "red",
    }
    status_color = status_colors.get(status, "white")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("ID", str(artifact_id))
    table.add_row("Type", artifact_type)
    table.add_row("Status", f"[{status_color}]{status.value.upper()}[/{status_color}]")
    table.add_row("Created", created_at)
    table.add_row("Created By", created_by)

    panel = Panel(
        table,
        title="Artifact Details",
        border_style="blue",
    )
    console.print(panel)


@handle_errors
def approve(
    artifact: str = typer.Argument(
        ..., help="Artifact to approve (UUID or file path)"
    ),
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """Approve an artifact, transitioning it from DRAFT to APPROVED status.

    Approves an artifact for progression in the workflow. Once approved,
    artifacts can proceed to the next phase. For TestPlan artifacts,
    approval is required before locking.

    ARTIFACT can be either:
    - A UUID (e.g., "a1b2c3d4-5678-...")
    - A file path (e.g., "artifacts/project_plans/xxx.json")
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    # Initialize services
    artifact_service, resolver, audit_trail = _get_services(project_root)

    # Resolve the artifact
    try:
        envelope = resolver.resolve(artifact)
    except Exception as e:
        error(str(e))
        raise typer.Exit(1) from None

    # Check if already approved
    if envelope.status == ArtifactStatus.APPROVED:
        warning(f"Artifact {envelope.id} is already approved")
        return

    if envelope.status == ArtifactStatus.LOCKED:
        error(f"Artifact {envelope.id} is locked and cannot be modified")
        raise typer.Exit(1)

    # Display artifact summary
    console.print()
    _display_artifact_summary(
        artifact_id=str(envelope.id),
        artifact_type=envelope.artifact_type.value,
        status=envelope.status,
        created_at=envelope.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        created_by=envelope.created_by.value,
    )
    console.print()

    # Confirm approval
    if not yes:
        confirm = typer.confirm("Approve this artifact?", default=False)
        if not confirm:
            info("Approval cancelled")
            return

    # Perform approval
    try:
        approval = artifact_service.approve(
            artifact_id=envelope.id,
            approved_by="user",
            artifact_type=envelope.artifact_type,
        )
    except Exception as e:
        error(f"Failed to approve artifact: {e}")
        raise typer.Exit(1) from None

    # Record in audit trail
    audit_trail.record_artifact_approved(
        artifact_id=envelope.id,
        approver="user",
    )

    console.print()
    success(f"Artifact {envelope.id} approved")
    info(f"Approval recorded at: {approval.approved_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # Show next steps based on artifact type
    if envelope.artifact_type.value == "TestPlan":
        info("Run 'rice-factor lock tests' to lock the TestPlan")
