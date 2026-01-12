"""API endpoints for configuration management.

Allows reading and updating application configuration.
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import yaml

from rice_factor.config.settings import (
    settings,
    reload_settings,
    _project_config_file,
    _user_config_file,
)

router = APIRouter(prefix="/configuration", tags=["configuration"])


class ConfigResponse(BaseModel):
    """Configuration response model."""
    merged: dict[str, Any]
    project_config: str | None
    user_config: str | None
    project_config_path: str
    user_config_path: str


class ConfigUpdate(BaseModel):
    """Configuration update model."""
    content: str
    scope: str = "project"  # "project" or "user"


@router.get("", response_model=ConfigResponse)
async def get_configuration() -> ConfigResponse:
    """Get current configuration.

    Returns:
        Current configuration state including raw files.
    """
    # Get merged settings
    merged = settings.as_dict()

    # Read raw files
    project_content = None
    if _project_config_file.exists():
        try:
            project_content = _project_config_file.read_text(encoding="utf-8")
        except Exception:
            pass

    user_content = None
    if _user_config_file.exists():
        try:
            user_content = _user_config_file.read_text(encoding="utf-8")
        except Exception:
            pass

    return ConfigResponse(
        merged=merged,
        project_config=project_content,
        user_config=user_content,
        project_config_path=str(_project_config_file.absolute()),
        user_config_path=str(_user_config_file.absolute()),
    )


@router.post("", status_code=status.HTTP_200_OK)
async def update_configuration(update: ConfigUpdate) -> dict[str, str]:
    """Update configuration file.

    Args:
        update: Update payload.

    Returns:
        Status message.
    """
    if update.scope == "project":
        path = _project_config_file
    elif update.scope == "user":
        path = _user_config_file
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope: {update.scope}",
        )

    # Validate YAML
    try:
        yaml.safe_load(update.content)
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid YAML: {e}",
        )

    # Write file
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(update.content, encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write config: {e}",
        )

    # Reload settings
    reload_settings()

    return {"status": "updated", "path": str(path)}
