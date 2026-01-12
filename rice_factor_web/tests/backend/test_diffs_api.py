"""Tests for diffs API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_diffs_empty(async_client: "AsyncClient") -> None:
    """Test listing diffs when none exist."""
    response = await async_client.get("/api/v1/diffs")
    assert response.status_code == 200
    data = response.json()
    assert data["diffs"] == []
    assert data["total"] == 0
    assert data["pending_count"] == 0


@pytest.mark.asyncio
async def test_get_diff_not_found(async_client: "AsyncClient") -> None:
    """Test getting non-existent diff returns 404."""
    diff_id = uuid4()
    response = await async_client.get(f"/api/v1/diffs/{diff_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_diff_not_found(async_client: "AsyncClient") -> None:
    """Test approving non-existent diff returns 404."""
    diff_id = uuid4()
    response = await async_client.post(f"/api/v1/diffs/{diff_id}/approve")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reject_diff_not_found(async_client: "AsyncClient") -> None:
    """Test rejecting non-existent diff returns 404."""
    diff_id = uuid4()
    response = await async_client.post(
        f"/api/v1/diffs/{diff_id}/reject",
        json={"reason": "Test rejection"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_diffs_with_status_filter(async_client: "AsyncClient") -> None:
    """Test listing diffs with status filter."""
    response = await async_client.get("/api/v1/diffs?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["diffs"], list)
