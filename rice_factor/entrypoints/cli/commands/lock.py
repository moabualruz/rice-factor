"""Lock artifacts to prevent modification."""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.audit.trail import AuditTrail
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
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
    """Check if lock command can be executed.

    Args:
        project_root: The project root directory.

    Raises:
        typer.Exit: If command cannot be executed.
    """
    phase_service = PhaseService(project_root=project_root)
    try:
        phase_service.require_phase("lock")
    except Exception as e:
        error(str(e))
        raise typer.Exit(1) from None


def _get_services(
    project_root: Path,
) -> tuple[ArtifactService, ArtifactResolver, AuditTrail]:
    """Get services for the lock command.

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
def lock(
    artifact: str = typer.Argument(
        ..., help="Artifact to lock ('tests' for TestPlan, or UUID/path)"
    ),
    path: str = typer.Option(".", "--path", "-p", help="Project root directory"),
) -> None:
    """Lock an artifact, making it permanently immutable.

    This command locks an APPROVED TestPlan artifact, transitioning it to
    LOCKED status. Once locked, an artifact CANNOT be modified or unlocked.

    ARTIFACT can be:
    - 'tests' to lock the most recent approved TestPlan
    - A UUID of a TestPlan artifact
    - A file path to a TestPlan artifact

    WARNING: Locking is PERMANENT and IRREVERSIBLE!
    """
    project_root = Path(path).resolve()

    # Check phase
    _check_phase(project_root)

    # Initialize services
    artifact_service, resolver, audit_trail = _get_services(project_root)

    # Handle 'tests' shorthand
    if artifact.lower() == "tests":
        # Find the most recent approved TestPlan
        latest = resolver.resolve_latest_by_type(ArtifactType.TEST_PLAN)
        if latest is None:
            error("No TestPlan artifacts found")
            info("Run 'rice-factor plan tests' to create a TestPlan")
            raise typer.Exit(1)
        envelope = latest
    else:
        # Resolve by UUID or path
        try:
            envelope = resolver.resolve(artifact)
        except Exception as e:
            error(str(e))
            raise typer.Exit(1) from None

    # Verify it's a TestPlan
    if envelope.artifact_type != ArtifactType.TEST_PLAN:
        error(f"Only TestPlan artifacts can be locked, got: {envelope.artifact_type.value}")
        raise typer.Exit(1)

    # Check if already locked
    if envelope.status == ArtifactStatus.LOCKED:
        warning(f"TestPlan {envelope.id} is already locked")
        return

    # Check if approved
    if envelope.status != ArtifactStatus.APPROVED:
        error(f"TestPlan must be approved before locking. Current status: {envelope.status.value}")
        info("Run 'rice-factor approve <artifact>' first")
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

    # Display immutability warning
    console.print(Panel(
        "[bold red]WARNING: Locking is PERMANENT![/bold red]\n\n"
        "Once locked, this TestPlan:\n"
        "  - Cannot be modified\n"
        "  - Cannot be unlocked\n"
        "  - Becomes the immutable test contract\n\n"
        "All future implementations must satisfy these tests.",
        title="⚠️  Immutability Warning",
        border_style="red",
    ))
    console.print()

    # Require explicit confirmation
    confirmation = typer.prompt(
        "Type LOCK to confirm (or anything else to cancel)",
        default="",
        show_default=False,
    )

    if confirmation != "LOCK":
        info("Lock cancelled")
        return

    # Perform lock
    try:
        artifact_service.lock(
            artifact_id=envelope.id,
            artifact_type=ArtifactType.TEST_PLAN,
        )
    except Exception as e:
        error(f"Failed to lock artifact: {e}")
        raise typer.Exit(1) from None

    # Record in audit trail
    audit_trail.record_artifact_locked(
        artifact_id=envelope.id,
    )

    console.print()
    success(f"TestPlan {envelope.id} is now LOCKED")
    warning("This artifact is permanently immutable")
    info("Proceed to implementation with 'rice-factor plan impl <file>'")
