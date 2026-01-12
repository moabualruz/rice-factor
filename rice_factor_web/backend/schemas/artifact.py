"""Pydantic schemas for artifact API endpoints.

These schemas define the request and response models for artifact operations,
mapping domain models to API-friendly representations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ArtifactSummary(BaseModel):
    """Summary view of an artifact for list responses.

    Contains essential fields for displaying artifacts in lists
    without the full payload.
    """

    id: UUID = Field(..., description="Unique artifact identifier")
    artifact_type: str = Field(..., description="Type of artifact (e.g., project_plan)")
    status: str = Field(..., description="Current status (draft, approved, locked)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    created_by: str = Field(..., description="Creator identifier")
    age_days: int = Field(0, description="Age in days since creation")

    model_config = {"from_attributes": True}


class ArtifactResponse(ArtifactSummary):
    """Full artifact response including payload.

    Extends summary with complete payload and additional metadata.
    """

    artifact_version: str = Field("1.0.0", description="Schema version")
    depends_on: list[UUID] = Field(default_factory=list, description="Dependency IDs")
    payload: dict[str, Any] = Field(default_factory=dict, description="Artifact payload")
    last_reviewed_at: datetime | None = Field(None, description="Last review timestamp")
    review_notes: str | None = Field(None, description="Review notes")
    is_approved: bool = Field(False, description="Whether artifact has approval")


class ArtifactListResponse(BaseModel):
    """Response for listing artifacts.

    Contains a list of artifact summaries with pagination info.
    """

    artifacts: list[ArtifactSummary] = Field(
        default_factory=list,
        description="List of artifact summaries",
    )
    total: int = Field(0, description="Total number of artifacts")


class ArtifactStatsResponse(BaseModel):
    """Statistics about artifacts in the project.

    Provides counts by status and type for dashboard display.
    """

    total: int = Field(0, description="Total artifact count")
    by_status: dict[str, int] = Field(
        default_factory=dict,
        description="Count by status (draft, approved, locked)",
    )
    by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Count by artifact type",
    )
    requiring_review: int = Field(0, description="Artifacts needing review")


class ApproveArtifactRequest(BaseModel):
    """Request to approve an artifact."""

    notes: str | None = Field(None, description="Optional approval notes")


class ApproveArtifactResponse(BaseModel):
    """Response after approving an artifact."""

    artifact_id: UUID = Field(..., description="Approved artifact ID")
    approved: bool = Field(True, description="Approval status")
    approved_by: str = Field(..., description="User who approved")
    approved_at: datetime = Field(..., description="Approval timestamp")
