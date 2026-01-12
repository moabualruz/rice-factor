"""Configuration management for the web backend.

Uses Dynaconf for layered configuration with environment variable support.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class WebSettings(BaseModel):
    """Web backend configuration settings.

    All settings can be overridden via environment variables with the
    RF_WEB_ prefix. For example:
        - RF_WEB_DEBUG=true
        - RF_WEB_SECRET_KEY=my-secret
        - RF_WEB_PROJECT_ROOT=/path/to/project
    """

    debug: bool = Field(default=False, description="Enable debug mode")
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to listen on")
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for session signing",
    )
    project_root: str = Field(
        default=".",
        description="Root path of the rice-factor project to serve",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins for development",
    )

    # OAuth2 settings (optional)
    github_client_id: str | None = Field(
        default=None,
        description="GitHub OAuth client ID",
    )
    github_client_secret: str | None = Field(
        default=None,
        description="GitHub OAuth client secret",
    )
    google_client_id: str | None = Field(
        default=None,
        description="Google OAuth client ID",
    )
    google_client_secret: str | None = Field(
        default=None,
        description="Google OAuth client secret",
    )

    # Session settings
    session_max_age: int = Field(
        default=86400 * 7,  # 7 days
        description="Session cookie max age in seconds",
    )
    session_cookie_name: str = Field(
        default="rf_session",
        description="Name of the session cookie",
    )

    @property
    def project_path(self) -> Path:
        """Get project root as a Path object."""
        return Path(self.project_root).resolve()

    model_config = {"extra": "ignore"}


def _load_from_env() -> dict[str, Any]:
    """Load settings from environment variables with RF_WEB_ prefix."""
    import os

    prefix = "RF_WEB_"
    result: dict[str, Any] = {}

    for key, value in os.environ.items():
        if key.startswith(prefix):
            setting_name = key[len(prefix) :].lower()
            # Handle boolean values
            if value.lower() in ("true", "1", "yes"):
                result[setting_name] = True
            elif value.lower() in ("false", "0", "no"):
                result[setting_name] = False
            # Handle integer values
            elif value.isdigit():
                result[setting_name] = int(value)
            # Handle comma-separated lists
            elif "," in value:
                result[setting_name] = [v.strip() for v in value.split(",")]
            else:
                result[setting_name] = value

    return result


@lru_cache
def get_settings() -> WebSettings:
    """Get the web settings singleton.

    Settings are loaded from environment variables with RF_WEB_ prefix.
    Use RF_WEB_DEBUG=true for development mode.

    Returns:
        WebSettings instance with merged configuration.
    """
    env_settings = _load_from_env()
    return WebSettings(**env_settings)


def clear_settings_cache() -> None:
    """Clear the settings cache (useful for testing)."""
    get_settings.cache_clear()
