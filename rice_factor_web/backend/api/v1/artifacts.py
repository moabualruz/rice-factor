"""Artifact API routes.

Provides endpoints for listing, viewing, and managing artifacts.
Maps to F22-01: Web Dashboard feature.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from rice_factor_web.backend.deps import CurrentUser, RequiredUser, ServiceAdapter
from rice_factor_web.backend.schemas.artifact import (
    ApproveArtifactRequest,
    ApproveArtifactResponse,
    ArtifactListResponse,
    ArtifactResponse,
    ArtifactStatsResponse,
    ArtifactSummary,
)
from rice_factor_web.backend.websocket.events import artifact_approved_event
from rice_factor_web.backend.websocket.manager import ws_manager

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


def _artifact_to_summary(artifact: Any) -> ArtifactSummary:
    """Convert domain artifact to summary schema."""
    created_at = artifact.created_at
    age_days = (datetime.now(timezone.utc) - created_at).days if created_at else 0

    return ArtifactSummary(
        id=artifact.id,
        artifact_type=artifact.artifact_type.value,
        status=artifact.status.value,
        created_at=created_at,
        updated_at=getattr(artifact, "updated_at", None),
        created_by=artifact.created_by.value if hasattr(artifact.created_by, "value") else str(artifact.created_by),
        age_days=age_days,
    )


def _artifact_to_response(artifact: Any, is_approved: bool = False) -> ArtifactResponse:
    """Convert domain artifact to full response schema."""
    summary = _artifact_to_summary(artifact)

    return ArtifactResponse(
        **summary.model_dump(),
        artifact_version=getattr(artifact, "artifact_version", "1.0.0"),
        depends_on=artifact.depends_on or [],
        payload=artifact.payload.model_dump() if artifact.payload else {},
        last_reviewed_at=getattr(artifact, "last_reviewed_at", None),
        review_notes=getattr(artifact, "review_notes", None),
        is_approved=is_approved,
    )


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    adapter: ServiceAdapter,
    artifact_type: str | None = Query(None, description="Filter by artifact type"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
) -> ArtifactListResponse:
    """List all artifacts with optional filtering.

    Args:
        adapter: Service adapter dependency.
        artifact_type: Optional filter by artifact type.
        status_filter: Optional filter by status (draft, approved, locked).

    Returns:
        List of artifact summaries.
    """
    from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType

    artifacts = []

    # Determine which types to check
    if artifact_type:
        try:
            types_to_check = [ArtifactType(artifact_type)]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid artifact type: {artifact_type}",
            )
    else:
        types_to_check = list(ArtifactType)

    # Determine status filter
    status_enum = None
    if status_filter:
        try:
            status_enum = ArtifactStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    # Load artifacts
    for atype in types_to_check:
        try:
            for artifact in adapter.storage.list_by_type(atype):
                if status_enum is None or artifact.status == status_enum:
                    artifacts.append(_artifact_to_summary(artifact))
        except Exception:
            # Type directory may not exist
            pass

    return ArtifactListResponse(
        artifacts=artifacts,
        total=len(artifacts),
    )


@router.get("/stats", response_model=ArtifactStatsResponse)
async def get_artifact_stats(adapter: ServiceAdapter) -> ArtifactStatsResponse:
    """Get statistics about artifacts in the project.

    Args:
        adapter: Service adapter dependency.

    Returns:
        Artifact statistics for dashboard display.
    """
    from rice_factor.domain.artifacts.enums import ArtifactType

    by_status: dict[str, int] = {"draft": 0, "approved": 0, "locked": 0}
    by_type: dict[str, int] = {}
    requiring_review = 0
    total = 0

    for atype in ArtifactType:
        type_count = 0
        try:
            for artifact in adapter.storage.list_by_type(atype):
                total += 1
                type_count += 1
                status_value = artifact.status.value
                by_status[status_value] = by_status.get(status_value, 0) + 1

                # Check if requiring review (draft and old)
                if artifact.status.value == "draft":
                    age = (datetime.now(timezone.utc) - artifact.created_at).days
                    if age > 7:
                        requiring_review += 1
        except Exception:
            pass

        if type_count > 0:
            by_type[atype.value] = type_count

    return ArtifactStatsResponse(
        total=total,
        by_status=by_status,
        by_type=by_type,
        requiring_review=requiring_review,
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: UUID,
    adapter: ServiceAdapter,
) -> ArtifactResponse:
    """Get a single artifact by ID.

    Args:
        artifact_id: UUID of the artifact.
        adapter: Service adapter dependency.

    Returns:
        Full artifact details.

    Raises:
        HTTPException: 404 if artifact not found.
    """
    try:
        artifact = adapter.artifact_service.get(artifact_id)
        is_approved = adapter.artifact_service.is_approved(artifact_id)
        return _artifact_to_response(artifact, is_approved)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found: {artifact_id}",
        ) from e


@router.post("/{artifact_id}/approve", response_model=ApproveArtifactResponse)
async def approve_artifact(
    artifact_id: UUID,
    adapter: ServiceAdapter,
    user: RequiredUser,
    request: ApproveArtifactRequest | None = None,
) -> ApproveArtifactResponse:
    """Approve an artifact.

    Requires authentication. Transitions artifact from DRAFT to APPROVED.

    Args:
        artifact_id: UUID of the artifact to approve.
        adapter: Service adapter dependency.
        user: Authenticated user (required).
        request: Optional approval request with notes.

    Returns:
        Approval confirmation.

    Raises:
        HTTPException: 400 if approval fails, 404 if not found.
    """
    username = user.get("username", user.get("id", "unknown"))

    try:
        approval = adapter.artifact_service.approve(
            artifact_id=artifact_id,
            approved_by=username,
        )

        # Broadcast WebSocket event
        artifact = adapter.artifact_service.get(artifact_id)
        event = artifact_approved_event(
            artifact_id=str(artifact_id),
            artifact_type=artifact.artifact_type.value,
            approved_by=username,
        )
        await ws_manager.broadcast(event)

        return ApproveArtifactResponse(
            artifact_id=artifact_id,
            approved=True,
            approved_by=username,
            approved_at=approval.approved_at,
        )
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact not found: {artifact_id}",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve artifact: {error_msg}",
        ) from e


@router.get("/graph/mermaid")
async def get_artifact_graph(
    adapter: ServiceAdapter,
) -> dict[str, str]:
    """Get artifact dependency graph in Mermaid format.

    Uses the GraphGenerator from M21 to create a flowchart
    showing artifact dependencies.

    Args:
        adapter: Service adapter dependency.

    Returns:
        Mermaid diagram syntax.
    """
    try:
        from rice_factor.adapters.viz.graph_generator import GraphGenerator
        from rice_factor.domain.artifacts.enums import ArtifactType

        # Collect all artifacts
        artifacts = []
        for atype in ArtifactType:
            try:
                for artifact in adapter.storage.list_by_type(atype):
                    artifacts.append(artifact)
            except Exception:
                pass

        if not artifacts:
            return {
                "diagram": "graph TD\n    A[No artifacts yet]",
                "count": 0,
            }

        # Generate graph
        generator = GraphGenerator()
        graph = generator.from_artifacts(artifacts)

        # Export to Mermaid
        from rice_factor.adapters.viz.mermaid_adapter import MermaidAdapter

        mermaid = MermaidAdapter()
        diagram = mermaid.export_flowchart(graph)

        return {
            "diagram": diagram,
            "count": len(artifacts),
        }
    except ImportError:
        # Fallback if viz adapters not available
        return {
            "diagram": "graph TD\n    A[Visualization not available]",
            "count": 0,
        }
    except Exception as e:
        return {
            "diagram": f"graph TD\n    A[Error: {str(e)[:50]}]",
            "count": 0,
        }


@router.get("/{artifact_id}/graph/mermaid")
async def get_artifact_dependency_graph(
    artifact_id: UUID,
    adapter: ServiceAdapter,
) -> dict[str, str]:
    """Get dependency graph for a specific artifact in Mermaid format.

    Shows the artifact and its direct dependencies, highlighting
    the current artifact.

    Args:
        artifact_id: UUID of the artifact to show dependencies for.
        adapter: Service adapter dependency.

    Returns:
        Mermaid diagram syntax with highlighted current artifact.

    Raises:
        HTTPException: 404 if artifact not found.
    """
    try:
        # Get the target artifact
        artifact = adapter.artifact_service.get(artifact_id)

        from rice_factor.domain.artifacts.enums import ArtifactType

        # Build nodes and edges for mermaid diagram
        nodes = []
        edges = []

        # Add current artifact (highlighted with special styling)
        artifact_label = artifact.artifact_type.value.replace("_", " ").title()
        artifact_node_id = f"A{str(artifact_id)[:8]}"
        nodes.append(f"    {artifact_node_id}[{artifact_label}]")
        nodes.append(f"    style {artifact_node_id} fill:#00a020,stroke:#00c030,stroke-width:3px")

        # Add dependencies
        depends_on = artifact.depends_on or []
        for i, dep_id in enumerate(depends_on):
            try:
                dep_artifact = adapter.artifact_service.get(dep_id)
                dep_label = dep_artifact.artifact_type.value.replace("_", " ").title()
                dep_node_id = f"D{i}"
                nodes.append(f"    {dep_node_id}[{dep_label}]")
                edges.append(f"    {dep_node_id} --> {artifact_node_id}")
            except Exception:
                # Dependency not found, show as missing
                dep_node_id = f"D{i}"
                nodes.append(f"    {dep_node_id}[Missing: {str(dep_id)[:8]}]")
                nodes.append(f"    style {dep_node_id} fill:#ff4444,stroke:#ff0000")
                edges.append(f"    {dep_node_id} -.-> {artifact_node_id}")

        # Find artifacts that depend on this one
        dependents = []
        for atype in ArtifactType:
            try:
                for other in adapter.storage.list_by_type(atype):
                    if other.id != artifact_id and artifact_id in (other.depends_on or []):
                        dependents.append(other)
            except Exception:
                pass

        for i, dep in enumerate(dependents):
            dep_label = dep.artifact_type.value.replace("_", " ").title()
            dep_node_id = f"R{i}"
            nodes.append(f"    {dep_node_id}[{dep_label}]")
            edges.append(f"    {artifact_node_id} --> {dep_node_id}")

        if not depends_on and not dependents:
            # No dependencies or dependents
            diagram = f"graph TD\n    {artifact_node_id}[{artifact_label}]\n    style {artifact_node_id} fill:#00a020,stroke:#00c030,stroke-width:3px\n    note[No dependencies]"
        else:
            diagram = "graph TD\n" + "\n".join(nodes) + "\n" + "\n".join(edges)

        return {
            "diagram": diagram,
            "artifact_id": str(artifact_id),
            "dependency_count": len(depends_on),
            "dependent_count": len(dependents),
        }
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact not found: {artifact_id}",
            ) from e
        return {
            "diagram": f"graph TD\n    A[Error: {str(e)[:50]}]",
            "artifact_id": str(artifact_id),
            "dependency_count": 0,
            "dependent_count": 0,
        }


@router.post("/{artifact_id}/lock")
async def lock_artifact(
    artifact_id: UUID,
    adapter: ServiceAdapter,
    user: RequiredUser,
) -> dict[str, Any]:
    """Lock an artifact (TestPlan only).

    Requires authentication. Transitions artifact from APPROVED to LOCKED.
    Only TestPlan artifacts can be locked.

    Args:
        artifact_id: UUID of the artifact to lock.
        adapter: Service adapter dependency.
        user: Authenticated user (required).

    Returns:
        Lock confirmation.

    Raises:
        HTTPException: 400 if lock fails, 404 if not found.
    """
    try:
        artifact = adapter.artifact_service.lock(artifact_id)
        return {
            "artifact_id": str(artifact_id),
            "locked": True,
            "status": artifact.status.value,
        }
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact not found: {artifact_id}",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot lock artifact: {error_msg}",
        ) from e


@router.get("/{artifact_id}/versions")
async def get_artifact_versions(
    artifact_id: UUID,
    adapter: ServiceAdapter,
) -> dict[str, Any]:
    """Get version history for an artifact.

    Note: Version tracking depends on the storage backend.
    The default filesystem adapter tracks only the current version.
    This endpoint returns the current version info and can be extended
    for backends that support full version history (e.g., Git-backed storage).

    Args:
        artifact_id: UUID of the artifact.
        adapter: Service adapter dependency.

    Returns:
        List of versions with metadata.

    Raises:
        HTTPException: 404 if artifact not found.
    """
    try:
        artifact = adapter.artifact_service.get(artifact_id)

        # Current implementation: return single version (current state)
        # This can be extended for Git-backed storage to return full history
        versions = [
            {
                "version": getattr(artifact, "artifact_version", "1.0.0"),
                "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                "status": artifact.status.value,
                "artifact_type": artifact.artifact_type.value,
            }
        ]

        return {
            "artifact_id": str(artifact_id),
            "versions": versions,
            "total": len(versions),
        }
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact not found: {artifact_id}",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get versions: {error_msg}",
        ) from e


@router.get("/{artifact_id}/versions/{version}")
async def get_artifact_version_payload(
    artifact_id: UUID,
    version: str,
    adapter: ServiceAdapter,
) -> dict[str, Any]:
    """Get the payload for a specific artifact version.

    Args:
        artifact_id: UUID of the artifact.
        version: Version number or identifier.
        adapter: Service adapter dependency.

    Returns:
        Artifact payload for the specified version.

    Raises:
        HTTPException: 404 if artifact or version not found.
    """
    try:
        artifact = adapter.artifact_service.get(artifact_id)

        # For now, return current payload (single version support)
        # Version comparison would require Git history or version snapshots
        return {
            "version": version,
            "payload": artifact.payload.model_dump() if artifact.payload else {},
        }
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact not found: {artifact_id}",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get version: {error_msg}",
        ) from e
