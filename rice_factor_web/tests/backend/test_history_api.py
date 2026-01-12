"""Tests for history API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_history_empty(async_client: "AsyncClient") -> None:
    """Test listing history when empty."""
    response = await async_client.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "total" in data
    assert "has_more" in data
    assert isinstance(data["entries"], list)


@pytest.mark.asyncio
async def test_list_history_with_pagination(async_client: "AsyncClient") -> None:
    """Test listing history with pagination."""
    response = await async_client.get("/api/v1/history?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["entries"], list)


@pytest.mark.asyncio
async def test_list_action_types(async_client: "AsyncClient") -> None:
    """Test getting available action types."""
    response = await async_client.get("/api/v1/history/actions")
    assert response.status_code == 200
    data = response.json()
    assert "actions" in data
    assert isinstance(data["actions"], list)


@pytest.mark.asyncio
async def test_get_history_stats(async_client: "AsyncClient") -> None:
    """Test getting history statistics."""
    response = await async_client.get("/api/v1/history/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_action" in data
    assert "by_user" in data


@pytest.mark.asyncio
async def test_export_history_json(async_client: "AsyncClient") -> None:
    """Test exporting history as JSON."""
    response = await async_client.post(
        "/api/v1/history/export",
        json={"format": "json"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert "data" in data
    assert "entry_count" in data


@pytest.mark.asyncio
async def test_export_history_csv(async_client: "AsyncClient") -> None:
    """Test exporting history as CSV."""
    response = await async_client.post(
        "/api/v1/history/export",
        json={"format": "csv"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"
