"""API endpoints for executing CLI commands.

Allows executing rice-factor CLI commands from the web interface.
"""

import asyncio
import shlex
import sys
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/commands", tags=["commands"])


class CommandRequest(BaseModel):
    """Command execution request."""
    args: list[str]
    cwd: str | None = None


class CommandResponse(BaseModel):
    """Command execution response."""
    command: str
    exit_code: int
    stdout: str
    stderr: str


@router.post("/execute", response_model=CommandResponse)
async def execute_command(request: CommandRequest) -> CommandResponse:
    """Execute a rice-factor CLI command.

    Args:
        request: Command request details.

    Returns:
        Command execution result.
    """
    # Sanitize: Ensure we only run rice-factor
    # We could technically run anything, but for security let's assume
    # we allow running "uv run rice-factor" or just "rice-factor" if installed.
    # We will invoke the same python interpreter with "-m rice_factor.entrypoints.cli.main"
    # or use "uv run". Using sys.executable is safer for env consistency.

    cmd = [sys.executable, "-m", "rice_factor.entrypoints.cli.main"] + request.args
    
    # Construct full command string for display
    full_cmd_str = " ".join(shlex.quote(arg) for arg in cmd)
    
    try:
        # Run subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=request.cwd,
        )

        stdout, stderr = await process.communicate()

        return CommandResponse(
            command=full_cmd_str,
            exit_code=process.returncode or 0,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute command: {e}",
        )
