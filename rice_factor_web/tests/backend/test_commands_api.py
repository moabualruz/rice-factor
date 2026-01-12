"""Tests for commands API endpoints."""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_execute_command_success(async_client: "AsyncClient") -> None:
    """Test successful command execution."""
    # Mock subprocess
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"success output", b"")
    mock_process.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        payload = {
            "args": ["plan", "project"]
        }
        
        response = await async_client.post("/api/v1/commands/execute", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["exit_code"] == 0
        assert data["stdout"] == "success output"
        assert data["stderr"] == ""
        
        # Verify call arguments
        # It should call sys.executable -m rice_factor.entrypoints.cli.main plan project
        args = mock_exec.call_args[0]
        assert args[0] == sys.executable
        assert args[1] == "-m"
        assert args[2] == "rice_factor.entrypoints.cli.main"
        assert args[3] == "plan"
        assert args[4] == "project"


@pytest.mark.asyncio
async def test_execute_command_error(async_client: "AsyncClient") -> None:
    """Test command execution with error exit code."""
    # Mock subprocess
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"error output")
    mock_process.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        payload = {
            "args": ["invalid-command"]
        }
        
        response = await async_client.post("/api/v1/commands/execute", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["exit_code"] == 1
        assert data["stdout"] == ""
        assert data["stderr"] == "error output"


@pytest.mark.asyncio
async def test_execute_command_exception(async_client: "AsyncClient") -> None:
    """Test command execution handling run exception."""
    with patch("asyncio.create_subprocess_exec", side_effect=OSError("Exec failed")):
        payload = {
            "args": ["plan"]
        }
        
        response = await async_client.post("/api/v1/commands/execute", json=payload)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to execute command" in response.json()["detail"]
