"""FastAPI dependency injection for the web backend.

Provides dependency functions for route handlers to access
services, authentication, and configuration.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, HTTPException, Request, status

from rice_factor_web.backend.config import get_settings
from rice_factor_web.backend.services.adapter import WebServiceAdapter

if TYPE_CHECKING:
    from rice_factor_web.backend.config import WebSettings


@lru_cache
def get_service_adapter() -> WebServiceAdapter:
    """Get the service adapter singleton.

    The adapter provides access to all domain services configured
    for the project root specified in settings.

    Returns:
        WebServiceAdapter instance.
    """
    settings = get_settings()
    return WebServiceAdapter(Path(settings.project_root).resolve())


def get_adapter_dependency() -> WebServiceAdapter:
    """FastAPI dependency for getting the service adapter.

    Returns:
        WebServiceAdapter instance.
    """
    return get_service_adapter()


# Type alias for dependency injection
ServiceAdapter = Annotated[WebServiceAdapter, Depends(get_adapter_dependency)]


def get_current_user(request: Request) -> dict[str, Any] | None:
    """Get the current user from session cookie.

    Args:
        request: The incoming request.

    Returns:
        User data dictionary or None if not authenticated.
    """
    from rice_factor_web.backend.auth.session import session_manager

    return session_manager.get_current_user(request)


def require_auth(request: Request) -> dict[str, Any]:
    """Require authentication for a route.

    Args:
        request: The incoming request.

    Returns:
        User data dictionary.

    Raises:
        HTTPException: 401 if not authenticated.
    """
    user = get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Type alias for authenticated user dependency
CurrentUser = Annotated[dict[str, Any] | None, Depends(get_current_user)]
RequiredUser = Annotated[dict[str, Any], Depends(require_auth)]


def clear_adapter_cache() -> None:
    """Clear the service adapter cache (useful for testing)."""
    get_service_adapter.cache_clear()
