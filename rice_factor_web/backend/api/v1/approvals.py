"""Approval workflow API routes.

Provides endpoints for managing approval workflows.
Maps to F22-03: Team Approval Workflows feature.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from rice_factor_web.backend.deps import CurrentUser, ServiceAdapter
from rice_factor_web.backend.schemas.approval import (
    ApprovalHistoryResponse,
    ApprovalListResponse,
    ApprovalRecord,
    PendingApproval,
    RevokeApprovalRequest,
    RevokeApprovalResponse,
)

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=ApprovalListResponse)
async def list_pending_approvals(
    adapter: ServiceAdapter,
) -> ApprovalListResponse:
    """List all items pending approval.

    Combines artifacts and diffs that need approval.

    Args:
        adapter: Service adapter dependency.

    Returns:
        List of pending approval items.
    """
    from rice_factor.domain.artifacts.enums import ArtifactType

    pending: list[PendingApproval] = []
    approved_today = 0
    today = datetime.now(timezone.utc).date()

    # Get pending artifacts (DRAFT status)
    for atype in ArtifactType:
        try:
            for artifact in adapter.storage.list_by_type(atype):
                if artifact.status.value == "draft":
                    age_days = (datetime.now(timezone.utc) - artifact.created_at).days
                    priority = "high" if age_days > 7 else "normal"

                    pending.append(
                        PendingApproval(
                            id=artifact.id,
                            item_type="artifact",
                            name=f"{atype.value}: {artifact.id}",
                            status="pending",
                            created_at=artifact.created_at,
                            age_days=age_days,
                            priority=priority,
                        )
                    )

                # Count approvals today
                approval = adapter.approvals.get_approval(artifact.id)
                if approval and approval.approved_at.date() == today:
                    approved_today += 1
        except Exception:
            pass

    # Get pending diffs
    diffs_dir = adapter.project_root / "diffs"
    if diffs_dir.exists():
        for diff_file in diffs_dir.glob("*.diff"):
            try:
                status_file = diff_file.with_suffix(".status")
                if not status_file.exists():
                    # No status file means pending
                    diff_id = UUID(diff_file.stem.split("_")[0])
                    created_at = datetime.fromtimestamp(
                        diff_file.stat().st_mtime, tz=timezone.utc
                    )
                    age_days = (datetime.now(timezone.utc) - created_at).days

                    pending.append(
                        PendingApproval(
                            id=diff_id,
                            item_type="diff",
                            name=diff_file.name,
                            status="pending",
                            created_at=created_at,
                            age_days=age_days,
                            priority="high" if age_days > 3 else "normal",
                        )
                    )
                else:
                    status_text = status_file.read_text().strip()
                    if status_text == "pending":
                        diff_id = UUID(diff_file.stem.split("_")[0])
                        created_at = datetime.fromtimestamp(
                            diff_file.stat().st_mtime, tz=timezone.utc
                        )
                        age_days = (datetime.now(timezone.utc) - created_at).days

                        pending.append(
                            PendingApproval(
                                id=diff_id,
                                item_type="diff",
                                name=diff_file.name,
                                status="pending",
                                created_at=created_at,
                                age_days=age_days,
                                priority="high" if age_days > 3 else "normal",
                            )
                        )
            except Exception:
                pass

    # Sort by priority then age
    pending.sort(key=lambda x: (0 if x.priority == "high" else 1, -x.age_days))

    return ApprovalListResponse(
        pending=pending,
        total_pending=len(pending),
        approved_today=approved_today,
    )


@router.get("/history", response_model=ApprovalHistoryResponse)
async def get_approval_history(
    adapter: ServiceAdapter,
    limit: int = 50,
) -> ApprovalHistoryResponse:
    """Get approval history.

    Args:
        adapter: Service adapter dependency.
        limit: Maximum number of records to return.

    Returns:
        List of approval records.
    """
    approvals: list[ApprovalRecord] = []

    # Get all approvals from tracker (returns list of Approval objects)
    all_approvals = adapter.approvals.list_approvals()

    for approval in all_approvals:
        approvals.append(
            ApprovalRecord(
                artifact_id=approval.artifact_id,
                approved_by=approval.approved_by,
                approved_at=approval.approved_at,
                notes=None,
            )
        )

    # Sort by date descending
    approvals.sort(key=lambda x: x.approved_at, reverse=True)

    return ApprovalHistoryResponse(
        approvals=approvals[:limit],
        total=len(approvals),
    )


@router.post("/{artifact_id}/revoke", response_model=RevokeApprovalResponse)
async def revoke_approval(
    artifact_id: UUID,
    adapter: ServiceAdapter,
    user: CurrentUser,
    request: RevokeApprovalRequest,
) -> RevokeApprovalResponse:
    """Revoke an approval.

    Only APPROVED artifacts can have their approval revoked.
    LOCKED artifacts cannot be revoked.

    Args:
        artifact_id: UUID of the artifact.
        adapter: Service adapter dependency.
        user: Current user (optional if auth disabled).
        request: Revocation request with reason.

    Returns:
        Revocation confirmation.

    Raises:
        HTTPException: 400 if revocation fails, 404 if not found.
    """
    username = "anonymous"
    if user:
        username = user.get("username", user.get("id", "anonymous"))

    try:
        success = adapter.artifact_service.revoke_approval(artifact_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval not found for artifact: {artifact_id}",
            )

        return RevokeApprovalResponse(
            artifact_id=artifact_id,
            revoked=True,
            revoked_by=username,
            revoked_at=datetime.now(timezone.utc),
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "locked" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revoke approval for LOCKED artifacts",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot revoke approval: {error_msg}",
        ) from e
