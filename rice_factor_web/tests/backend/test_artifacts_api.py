"""Tests for artifacts API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_artifacts_empty(async_client: "AsyncClient") -> None:
    """Test listing artifacts when none exist."""
    response = await async_client.get("/api/v1/artifacts")
    assert response.status_code == 200
    data = response.json()
    assert data["artifacts"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_artifacts_with_invalid_type(async_client: "AsyncClient") -> None:
    """Test listing artifacts with invalid type filter."""
    response = await async_client.get("/api/v1/artifacts?artifact_type=invalid")
    assert response.status_code == 400
    assert "Invalid artifact type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_artifacts_with_invalid_status(async_client: "AsyncClient") -> None:
    """Test listing artifacts with invalid status filter."""
    response = await async_client.get("/api/v1/artifacts?status=invalid")
    assert response.status_code == 400
    assert "Invalid status" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_artifact_not_found(async_client: "AsyncClient") -> None:
    """Test getting non-existent artifact returns 404."""
    artifact_id = uuid4()
    response = await async_client.get(f"/api/v1/artifacts/{artifact_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_artifact_stats(async_client: "AsyncClient") -> None:
    """Test getting artifact statistics."""
    response = await async_client.get("/api/v1/artifacts/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_status" in data
    assert "by_type" in data
    assert "requiring_review" in data
