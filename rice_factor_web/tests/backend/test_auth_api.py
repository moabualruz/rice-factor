"""Tests for authentication API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_auth_status_anonymous(async_client: "AsyncClient") -> None:
    """Test auth status returns anonymous when auth disabled."""
    response = await async_client.get("/api/v1/auth/status")
    assert response.status_code == 200
    data = response.json()
    # Auth is disabled by default, so user is anonymous
    assert data["authenticated"] is True
    assert data["user"]["username"] == "anonymous"
    assert data["user"]["provider"] == "local"


@pytest.mark.asyncio
async def test_list_providers(async_client: "AsyncClient") -> None:
    """Test listing available OAuth providers."""
    response = await async_client.get("/api/v1/auth/providers")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert len(data["providers"]) == 2  # github and google
    # Both should be disabled (no credentials configured)
    for provider in data["providers"]:
        assert provider["enabled"] is False


@pytest.mark.asyncio
async def test_github_login_not_configured(async_client: "AsyncClient") -> None:
    """Test GitHub login returns 503 when not configured."""
    response = await async_client.get(
        "/api/v1/auth/github/login",
        follow_redirects=False,
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_google_login_not_configured(async_client: "AsyncClient") -> None:
    """Test Google login returns 503 when not configured."""
    response = await async_client.get(
        "/api/v1/auth/google/login",
        follow_redirects=False,
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_logout(async_client: "AsyncClient") -> None:
    """Test logout endpoint."""
    response = await async_client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["logged_out"] is True
    assert "Successfully" in data["message"]
