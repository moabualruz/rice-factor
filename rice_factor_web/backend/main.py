"""FastAPI application factory for the Rice-Factor web interface.

This module creates and configures the FastAPI application that serves
the web interface for artifact management, diff review, and team approvals.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, AsyncGenerator

from rice_factor_web.backend.config import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: "FastAPI") -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events.

    Args:
        app: The FastAPI application instance.

    Yields:
        None during application lifetime.
    """
    # Startup
    settings = get_settings()
    if settings.debug:
        print(f"Rice-Factor Web starting in DEBUG mode")
        print(f"Project root: {settings.project_path}")
        print(f"API docs available at: http://{settings.host}:{settings.port}/api/docs")

    yield

    # Shutdown
    if settings.debug:
        print("Rice-Factor Web shutting down")


def create_app() -> "FastAPI":
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles

    from rice_factor_web.backend.api.router import api_router
    from rice_factor_web.backend.websocket.manager import ws_manager

    settings = get_settings()

    app = FastAPI(
        title="Rice-Factor Web Interface",
        description="Web interface for artifact review, diff management, and team approvals",
        version="0.1.0",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        openapi_url="/api/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS middleware for development
    if settings.debug and settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Mount API routes
    app.include_router(api_router, prefix="/api/v1")

    # WebSocket endpoint for real-time updates
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: "WebSocket") -> None:  # type: ignore[name-defined]
        """WebSocket endpoint for real-time artifact updates."""
        await ws_manager.websocket_endpoint(websocket)

    # Serve static frontend files in production
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists() and not settings.debug:
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


def run_server() -> None:
    """Run the web server using uvicorn.

    This is the entry point for the `rice-factor-web` CLI command.
    """
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "rice_factor_web.backend.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


# Application instance for uvicorn
app = create_app()
