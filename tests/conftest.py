"""Pytest configuration and shared fixtures."""

import json
import shutil
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


@pytest.fixture
def demo_project_fixture() -> Path:
    """Return path to the demo project fixture (read-only reference)."""
    return Path(__file__).parent / "fixtures" / "demo-project"


@pytest.fixture
def demo_project(tmp_path: Path, demo_project_fixture: Path) -> Generator[Path, None, None]:
    """Copy demo project fixture to temp directory for isolated testing."""
    project_dir = tmp_path / "demo-project"
    shutil.copytree(demo_project_fixture, project_dir)
    yield project_dir


@pytest.fixture
def initialized_project(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a fully initialized Rice-Factor project."""
    project_dir = tmp_path / "initialized_project"
    project_dir.mkdir()

    # Create .project directory structure
    project_subdir = project_dir / ".project"
    project_subdir.mkdir()
    (project_subdir / "requirements.md").write_text("# Requirements\n\nTest project.")
    (project_subdir / "constraints.md").write_text("# Constraints\n\nNo constraints.")
    (project_subdir / "glossary.md").write_text("# Glossary\n\nNo terms.")

    # Create artifacts directory
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir()

    # Create audit directory with trail file
    audit_dir = project_dir / "audit"
    audit_dir.mkdir()
    (audit_dir / "trail.json").write_text(json.dumps([]))

    # Create phase state file
    (project_subdir / ".phase").write_text("INITIALIZED")

    yield project_dir


@pytest.fixture
def mvp_project(tmp_path: Path) -> Generator[Path, None, None]:
    """Create an MVP-ready project with basic structure.

    This fixture provides a project that has passed initialization
    and is ready for plan/scaffold operations.
    """
    project_dir = tmp_path / "mvp_project"
    project_dir.mkdir()

    # Create .project directory structure
    project_subdir = project_dir / ".project"
    project_subdir.mkdir()
    (project_subdir / "requirements.md").write_text(
        "# Requirements\n\n## Overview\nSimple test project.\n\n## Features\n- Feature 1\n"
    )
    (project_subdir / "constraints.md").write_text(
        "# Constraints\n\n## Technical\n- Python 3.11+\n"
    )
    (project_subdir / "glossary.md").write_text("# Glossary\n\n- **Term**: Definition\n")

    # Create artifacts directory
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir()

    # Create audit directory with trail file
    audit_dir = project_dir / "audit"
    audit_dir.mkdir()
    (audit_dir / "trail.json").write_text(json.dumps([]))

    # Create phase state file
    (project_subdir / ".phase").write_text("INITIALIZED")

    # Create src directory
    src_dir = project_dir / "src"
    src_dir.mkdir()

    yield project_dir
