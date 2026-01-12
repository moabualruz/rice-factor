"""Pytest configuration and fixtures for rice_factor_web tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, AsyncGenerator, Generator

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.fixture
def temp_project_root() -> Generator[Path, None, None]:
    """Create a temporary project root directory.

    Sets up basic rice-factor project structure for testing.

    Yields:
        Path to temporary project root.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create basic project structure
        (root / "artifacts").mkdir()
        (root / ".project").mkdir()
        (root / "diffs").mkdir()

        # Create a minimal config
        config_file = root / ".project" / "config.yaml"
        config_file.write_text("project_name: test-project\n")

        yield root


@pytest.fixture
def mock_settings(temp_project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up environment variables for testing.

    Args:
        temp_project_root: Temporary project root fixture.
        monkeypatch: Pytest monkeypatch fixture.
    """
    from rice_factor_web.backend.config import clear_settings_cache

    monkeypatch.setenv("RF_WEB_PROJECT_ROOT", str(temp_project_root))
    monkeypatch.setenv("RF_WEB_DEBUG", "true")
    monkeypatch.setenv("RF_WEB_SECRET_KEY", "test-secret-key-for-testing-only")

    # Clear cached settings
    clear_settings_cache()


@pytest.fixture
async def async_client(
    mock_settings: None,
) -> AsyncGenerator["AsyncClient", None]:
    """Create an async HTTP client for testing.

    Args:
        mock_settings: Mock settings fixture.

    Yields:
        Async HTTP client configured for testing.
    """
    from httpx import ASGITransport, AsyncClient

    from rice_factor_web.backend.deps import clear_adapter_cache
    from rice_factor_web.backend.main import create_app

    # Clear any cached adapters
    clear_adapter_cache()

    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_artifact_data() -> dict[str, str | list[str]]:
    """Provide sample artifact data for testing.

    Returns:
        Dictionary with sample artifact data.
    """
    return {
        "artifact_type": "project_plan",
        "status": "draft",
        "created_by": "test_user",
        "payload": {
            "name": "Test Project",
            "description": "A test project for testing",
        },
    }
