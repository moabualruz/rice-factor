"""Tests for configuration system."""

import pytest

from rice_factor.adapters.config.dynaconf_adapter import DynaconfConfigAdapter
from rice_factor.config.settings import get_config_paths, settings


def test_settings_loads_defaults() -> None:
    """Settings should load default values."""
    assert settings.llm.provider == "claude"
    assert settings.execution.dry_run is False


def test_settings_has_nested_values() -> None:
    """Settings should have properly nested configuration."""
    assert hasattr(settings, "llm")
    assert hasattr(settings.llm, "model")
    assert hasattr(settings, "output")
    assert hasattr(settings.output, "log_level")


def test_config_paths_returns_defaults() -> None:
    """Config paths should include defaults file."""
    paths = get_config_paths()
    assert "defaults" in paths
    assert paths["defaults"] is not None


class TestDynaconfAdapter:
    """Tests for DynaconfConfigAdapter."""

    @pytest.fixture
    def adapter(self) -> DynaconfConfigAdapter:
        """Create adapter instance."""
        return DynaconfConfigAdapter()

    def test_get_returns_value(self, adapter: DynaconfConfigAdapter) -> None:
        """Get should return configuration value."""
        assert adapter.get("llm.provider") == "claude"

    def test_get_returns_default_for_missing(
        self, adapter: DynaconfConfigAdapter
    ) -> None:
        """Get should return default for missing keys."""
        assert adapter.get("nonexistent.key", "default") == "default"

    def test_get_bool_converts_value(self, adapter: DynaconfConfigAdapter) -> None:
        """Get bool should convert value to boolean."""
        # execution.dry_run is false in defaults
        assert adapter.get_bool("execution.dry_run") is False

    def test_get_int_converts_value(self, adapter: DynaconfConfigAdapter) -> None:
        """Get int should convert value to integer."""
        assert adapter.get_int("llm.max_tokens") == 4096

    def test_get_str_converts_value(self, adapter: DynaconfConfigAdapter) -> None:
        """Get str should convert value to string."""
        assert adapter.get_str("llm.provider") == "claude"

    def test_as_dict_returns_all_config(self, adapter: DynaconfConfigAdapter) -> None:
        """As dict should return all configuration."""
        config_dict = adapter.as_dict()
        # Dynaconf returns uppercase keys
        assert "LLM" in config_dict
        assert "EXECUTION" in config_dict
        assert "OUTPUT" in config_dict
