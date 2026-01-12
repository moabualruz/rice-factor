"""Main API router that aggregates all v1 routes.

This module combines all API routes under a single router that
is mounted at /api/v1 in the main application.
"""

from __future__ import annotations

from fastapi import APIRouter

from rice_factor_web.backend.api.v1 import (
    approvals,
    artifacts,
    auth,
    diffs,
    history,
    projects,
)

api_router = APIRouter()

# Health check endpoint
@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring.

    Returns:
        Dictionary with status "ok".
    """
    return {"status": "ok"}


# Include all v1 routes
api_router.include_router(artifacts.router)
api_router.include_router(diffs.router)
api_router.include_router(approvals.router)
api_router.include_router(history.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
