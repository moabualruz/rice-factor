"""Pydantic schemas for history API endpoints.

These schemas define the request and response models for the history browser.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    """A single history/audit entry."""

    id: str = Field(..., description="Entry identifier")
    timestamp: datetime = Field(..., description="When the event occurred")
    action: str = Field(..., description="Action type (e.g., artifact.approved)")
    user: str | None = Field(None, description="User who performed action")
    artifact_id: UUID | None = Field(None, description="Related artifact ID")
    artifact_type: str | None = Field(None, description="Type of artifact")
    details: dict[str, str | int | bool | None] = Field(
        default_factory=dict,
        description="Additional event details",
    )

    model_config = {"from_attributes": True}


class HistoryListResponse(BaseModel):
    """Response for listing history entries."""

    entries: list[HistoryEntry] = Field(
        default_factory=list,
        description="List of history entries",
    )
    total: int = Field(0, description="Total entry count")
    has_more: bool = Field(False, description="Whether more entries exist")


class HistoryFilterRequest(BaseModel):
    """Request parameters for filtering history."""

    action: str | None = Field(None, description="Filter by action type")
    artifact_id: UUID | None = Field(None, description="Filter by artifact ID")
    user: str | None = Field(None, description="Filter by user")
    start_date: datetime | None = Field(None, description="Start of date range")
    end_date: datetime | None = Field(None, description="End of date range")
    limit: int = Field(100, ge=1, le=1000, description="Max entries to return")
    offset: int = Field(0, ge=0, description="Entries to skip")


class ExportHistoryRequest(BaseModel):
    """Request to export history data."""

    format: str = Field("json", description="Export format (json, csv)")
    filters: HistoryFilterRequest | None = Field(None, description="Optional filters")


class ExportHistoryResponse(BaseModel):
    """Response containing exported history data."""

    format: str = Field(..., description="Export format used")
    data: str = Field(..., description="Exported data as string")
    entry_count: int = Field(0, description="Number of entries exported")
    generated_at: datetime = Field(..., description="Export timestamp")
