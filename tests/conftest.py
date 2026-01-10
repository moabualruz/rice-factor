"""Pytest configuration and shared fixtures."""

from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for project tests."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    yield project_dir


@pytest.fixture
def sample_config() -> dict:
    """Provide a sample configuration dictionary."""
    return {
        "llm": {
            "provider": "claude",
            "model": "claude-3-5-sonnet",
        },
        "execution": {
            "dry_run": False,
            "auto_approve": False,
            "max_retries": 3,
        },
        "output": {
            "color": True,
            "verbose": False,
            "log_level": "INFO",
        },
    }
