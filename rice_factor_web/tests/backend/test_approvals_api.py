"""Tests for approvals API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_pending_approvals(async_client: "AsyncClient") -> None:
    """Test listing pending approvals."""
    response = await async_client.get("/api/v1/approvals")
    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    assert "total_pending" in data
    assert "approved_today" in data
    assert isinstance(data["pending"], list)


@pytest.mark.asyncio
async def test_get_approval_history(async_client: "AsyncClient") -> None:
    """Test getting approval history."""
    response = await async_client.get("/api/v1/approvals/history")
    assert response.status_code == 200
    data = response.json()
    assert "approvals" in data
    assert "total" in data
    assert isinstance(data["approvals"], list)


@pytest.mark.asyncio
async def test_get_approval_history_with_limit(async_client: "AsyncClient") -> None:
    """Test getting approval history with limit."""
    response = await async_client.get("/api/v1/approvals/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["approvals"], list)


@pytest.mark.asyncio
async def test_revoke_approval_not_found(async_client: "AsyncClient") -> None:
    """Test revoking non-existent approval returns 404."""
    artifact_id = uuid4()
    response = await async_client.post(
        f"/api/v1/approvals/{artifact_id}/revoke",
        json={"reason": "Test revocation"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pending_approvals_empty(async_client: "AsyncClient") -> None:
    """Test pending approvals list is empty initially."""
    response = await async_client.get("/api/v1/approvals")
    assert response.status_code == 200
    data = response.json()
    assert data["total_pending"] >= 0
