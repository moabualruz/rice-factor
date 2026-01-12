"""History browser API routes.

Provides endpoints for browsing and exporting audit history.
Maps to F22-04: History Browser feature.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Query

from rice_factor_web.backend.deps import ServiceAdapter
from rice_factor_web.backend.schemas.history import (
    ExportHistoryRequest,
    ExportHistoryResponse,
    HistoryEntry,
    HistoryListResponse,
)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
async def list_history(
    adapter: ServiceAdapter,
    action: str | None = Query(None, description="Filter by action type"),
    artifact_id: UUID | None = Query(None, description="Filter by artifact ID"),
    user: str | None = Query(None, description="Filter by user"),
    start_date: datetime | None = Query(None, description="Start of date range"),
    end_date: datetime | None = Query(None, description="End of date range"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Entries to skip"),
) -> HistoryListResponse:
    """List audit history entries with optional filtering.

    Args:
        adapter: Service adapter dependency.
        action: Optional filter by action type.
        artifact_id: Optional filter by artifact ID.
        user: Optional filter by user.
        start_date: Optional start of date range.
        end_date: Optional end of date range.
        limit: Maximum number of entries to return.
        offset: Number of entries to skip.

    Returns:
        List of history entries.
    """
    entries: list[HistoryEntry] = []

    # Read audit trail
    try:
        all_entries = adapter.audit_trail.get_entries()
    except Exception:
        # Audit trail may not exist yet
        return HistoryListResponse(entries=[], total=0, has_more=False)

    for idx, entry in enumerate(all_entries):
        # Apply filters
        if action and entry.get("action") != action:
            continue
        if artifact_id and entry.get("artifact_id") != str(artifact_id):
            continue
        if user and entry.get("user") != user:
            continue

        entry_timestamp = entry.get("timestamp")
        if isinstance(entry_timestamp, str):
            try:
                entry_timestamp = datetime.fromisoformat(entry_timestamp)
            except ValueError:
                entry_timestamp = None

        if entry_timestamp:
            if start_date and entry_timestamp < start_date:
                continue
            if end_date and entry_timestamp > end_date:
                continue

        # Parse artifact_id if present
        entry_artifact_id = None
        if entry.get("artifact_id"):
            try:
                entry_artifact_id = UUID(entry["artifact_id"])
            except (ValueError, TypeError):
                pass

        entries.append(
            HistoryEntry(
                id=str(idx),
                timestamp=entry_timestamp or datetime.now(timezone.utc),
                action=entry.get("action", "unknown"),
                user=entry.get("user"),
                artifact_id=entry_artifact_id,
                artifact_type=entry.get("artifact_type"),
                details=entry.get("details", {}),
            )
        )

    # Sort by timestamp descending
    entries.sort(key=lambda x: x.timestamp, reverse=True)

    # Apply pagination
    total = len(entries)
    entries = entries[offset : offset + limit]
    has_more = offset + len(entries) < total

    return HistoryListResponse(
        entries=entries,
        total=total,
        has_more=has_more,
    )


@router.get("/actions")
async def list_action_types(adapter: ServiceAdapter) -> dict[str, list[str]]:
    """Get list of distinct action types in history.

    Args:
        adapter: Service adapter dependency.

    Returns:
        Dictionary with list of action types.
    """
    actions: set[str] = set()

    try:
        all_entries = adapter.audit_trail.get_entries()
        for entry in all_entries:
            if action := entry.get("action"):
                actions.add(action)
    except Exception:
        pass

    return {"actions": sorted(actions)}


@router.post("/export", response_model=ExportHistoryResponse)
async def export_history(
    adapter: ServiceAdapter,
    request: ExportHistoryRequest,
) -> ExportHistoryResponse:
    """Export history data in specified format.

    Args:
        adapter: Service adapter dependency.
        request: Export request with format and optional filters.

    Returns:
        Exported data as string.
    """
    # Get filtered entries
    filters = request.filters
    entries: list[dict[str, str | int | bool | None]] = []

    try:
        all_entries = adapter.audit_trail.get_entries()
    except Exception:
        all_entries = []

    for entry in all_entries:
        # Apply filters if provided
        if filters:
            if filters.action and entry.get("action") != filters.action:
                continue
            if filters.artifact_id and entry.get("artifact_id") != str(filters.artifact_id):
                continue
            if filters.user and entry.get("user") != filters.user:
                continue

        entries.append(entry)

    # Export in requested format
    if request.format == "csv":
        output = io.StringIO()
        if entries:
            fieldnames = list(entries[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(entries)
        data = output.getvalue()
    else:
        # Default to JSON
        data = json.dumps(entries, indent=2, default=str)

    return ExportHistoryResponse(
        format=request.format,
        data=data,
        entry_count=len(entries),
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/stats")
async def get_history_stats(adapter: ServiceAdapter) -> dict[str, int | dict[str, int]]:
    """Get statistics about history entries.

    Args:
        adapter: Service adapter dependency.

    Returns:
        Statistics including counts by action type.
    """
    by_action: dict[str, int] = {}
    by_user: dict[str, int] = {}
    total = 0

    try:
        all_entries = adapter.audit_trail.get_entries()
        for entry in all_entries:
            total += 1
            action = entry.get("action", "unknown")
            by_action[action] = by_action.get(action, 0) + 1

            if user := entry.get("user"):
                by_user[user] = by_user.get(user, 0) + 1
    except Exception:
        pass

    return {
        "total": total,
        "by_action": by_action,
        "by_user": by_user,
    }
