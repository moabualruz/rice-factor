"""Pydantic schemas for diff API endpoints.

These schemas define the request and response models for diff review operations.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DiffSummary(BaseModel):
    """Summary view of a diff for list responses."""

    id: UUID = Field(..., description="Unique diff identifier")
    target_file: str = Field(..., description="File the diff applies to")
    status: str = Field(..., description="Diff status (pending, approved, rejected, applied)")
    created_at: datetime = Field(..., description="Creation timestamp")
    lines_added: int = Field(0, description="Number of lines added")
    lines_removed: int = Field(0, description="Number of lines removed")
    artifact_id: UUID | None = Field(None, description="Related artifact ID")

    model_config = {"from_attributes": True}


class DiffResponse(DiffSummary):
    """Full diff response including content."""

    content: str = Field(..., description="Unified diff content")
    language: str = Field("text", description="Language for syntax highlighting")
    original_content: str | None = Field(None, description="Original file content")
    modified_content: str | None = Field(None, description="Modified file content")


class DiffListResponse(BaseModel):
    """Response for listing diffs."""

    diffs: list[DiffSummary] = Field(
        default_factory=list,
        description="List of diff summaries",
    )
    total: int = Field(0, description="Total number of diffs")
    pending_count: int = Field(0, description="Number of pending diffs")


class ApproveDiffRequest(BaseModel):
    """Request to approve a diff."""

    comment: str | None = Field(None, description="Optional approval comment")


class RejectDiffRequest(BaseModel):
    """Request to reject a diff."""

    reason: str = Field(..., description="Reason for rejection")


class DiffActionResponse(BaseModel):
    """Response after a diff action (approve/reject)."""

    diff_id: UUID = Field(..., description="Diff ID")
    action: str = Field(..., description="Action taken (approved, rejected)")
    performed_by: str = Field(..., description="User who performed action")
    performed_at: datetime = Field(..., description="Action timestamp")
