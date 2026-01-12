"""Tests for projects API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_project(async_client: "AsyncClient") -> None:
    """Test getting current project information."""
    response = await async_client.get("/api/v1/projects/current")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "root" in data
    assert "initialized" in data
    assert "has_artifacts" in data


@pytest.mark.asyncio
async def test_get_current_phase(async_client: "AsyncClient") -> None:
    """Test getting current project phase."""
    response = await async_client.get("/api/v1/projects/phase")
    assert response.status_code == 200
    data = response.json()
    assert "phase" in data
    assert "description" in data
    assert "artifact_counts" in data
    assert "available_commands" in data


@pytest.mark.asyncio
async def test_get_project_config(async_client: "AsyncClient") -> None:
    """Test getting project configuration."""
    response = await async_client.get("/api/v1/projects/config")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data
    assert "config" in data
