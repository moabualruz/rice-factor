"""Tests for version and basic imports."""

import rice_factor


def test_version_exists() -> None:
    """Version string should be defined."""
    assert hasattr(rice_factor, "__version__")
    assert isinstance(rice_factor.__version__, str)


def test_version_format() -> None:
    """Version should follow semver format."""
    version = rice_factor.__version__
    parts = version.split(".")
    assert len(parts) >= 2, "Version should have at least major.minor"
    assert all(part.isdigit() for part in parts[:2]), "Version parts should be numeric"
