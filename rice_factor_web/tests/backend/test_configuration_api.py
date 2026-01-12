"""Tests for configuration API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_configuration(async_client: "AsyncClient") -> None:
    """Test getting configuration."""
    # Mock exists/read_text for config files
    with patch("pathlib.Path.exists") as mock_exists, \
         patch("pathlib.Path.read_text") as mock_read:
        
        # Setup mocks
        mock_exists.side_effect = [True, True]  # Project config exists, user config exists
        mock_read.side_effect = ["project: config", "user: config"]

        response = await async_client.get("/api/v1/configuration")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "merged" in data
        assert data["project_config"] == "project: config"
        assert data["user_config"] == "user: config"
        assert "project_config_path" in data
        assert "user_config_path" in data


@pytest.mark.asyncio
async def test_update_configuration_project(async_client: "AsyncClient") -> None:
    """Test updating project configuration."""
    with patch("pathlib.Path.mkdir") as mock_mkdir, \
         patch("pathlib.Path.write_text") as mock_write, \
         patch("rice_factor_web.backend.api.v1.configuration.reload_settings") as mock_reload:
        
        payload = {
            "content": "key: value",
            "scope": "project"
        }
        
        response = await async_client.post("/api/v1/configuration", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "updated"
        
        mock_mkdir.assert_called_once()
        mock_write.assert_called_once_with("key: value", encoding="utf-8")
        mock_reload.assert_called_once()


@pytest.mark.asyncio
async def test_update_configuration_invalid_scope(async_client: "AsyncClient") -> None:
    """Test updating configuration with invalid scope."""
    payload = {
        "content": "key: value",
        "scope": "invalid"
    }
    
    response = await async_client.post("/api/v1/configuration", json=payload)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid scope" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_configuration_invalid_yaml(async_client: "AsyncClient") -> None:
    """Test updating configuration with invalid YAML."""
    payload = {
        "content": "key: : value",  # Invalid YAML
        "scope": "project"
    }
    
    response = await async_client.post("/api/v1/configuration", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid YAML" in response.json()["detail"]
