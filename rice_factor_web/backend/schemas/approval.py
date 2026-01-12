"""Pydantic schemas for approval API endpoints.

These schemas define the request and response models for team approval workflows.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApprovalRecord(BaseModel):
    """Record of an artifact approval."""

    artifact_id: UUID = Field(..., description="Approved artifact ID")
    approved_by: str = Field(..., description="User who approved")
    approved_at: datetime = Field(..., description="Approval timestamp")
    notes: str | None = Field(None, description="Approval notes")

    model_config = {"from_attributes": True}


class PendingApproval(BaseModel):
    """An item pending approval."""

    id: UUID = Field(..., description="Item ID (artifact or diff)")
    item_type: str = Field(..., description="Type: 'artifact' or 'diff'")
    name: str = Field(..., description="Display name")
    status: str = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    age_days: int = Field(0, description="Age in days")
    priority: str = Field("normal", description="Priority level")


class ApprovalListResponse(BaseModel):
    """Response for listing pending approvals."""

    pending: list[PendingApproval] = Field(
        default_factory=list,
        description="List of items pending approval",
    )
    total_pending: int = Field(0, description="Total pending count")
    approved_today: int = Field(0, description="Approvals made today")


class ApprovalHistoryResponse(BaseModel):
    """Response for approval history."""

    approvals: list[ApprovalRecord] = Field(
        default_factory=list,
        description="List of approval records",
    )
    total: int = Field(0, description="Total approval count")


class RevokeApprovalRequest(BaseModel):
    """Request to revoke an approval."""

    reason: str = Field(..., description="Reason for revoking")


class RevokeApprovalResponse(BaseModel):
    """Response after revoking an approval."""

    artifact_id: UUID = Field(..., description="Artifact ID")
    revoked: bool = Field(True, description="Revocation status")
    revoked_by: str = Field(..., description="User who revoked")
    revoked_at: datetime = Field(..., description="Revocation timestamp")
