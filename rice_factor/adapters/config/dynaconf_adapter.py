"""Dynaconf adapter implementing the ConfigPort protocol.

This adapter wraps Dynaconf to provide configuration access
through the hexagonal architecture port interface.
"""

from typing import Any

from rice_factor.config.settings import reload_settings, settings


class DynaconfConfigAdapter:
    """Adapter that implements ConfigPort using Dynaconf.

    Provides typed access to configuration values with support
    for nested keys using dot notation.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated key.

        Args:
            key: Dot-separated key like "llm.provider" or "execution.dry_run"
            default: Default value if key is not found

        Returns:
            The configuration value, or default if not found.
        """
        try:
            # Dynaconf supports dot notation for nested access
            return settings.get(key, default)
        except (KeyError, AttributeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value.

        Args:
            key: Dot-separated configuration key
            default: Default value if key is not found

        Returns:
            The boolean configuration value.
        """
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value.

        Args:
            key: Dot-separated configuration key
            default: Default value if key is not found

        Returns:
            The integer configuration value.
        """
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_str(self, key: str, default: str = "") -> str:
        """Get a string configuration value.

        Args:
            key: Dot-separated configuration key
            default: Default value if key is not found

        Returns:
            The string configuration value.
        """
        value = self.get(key, default)
        return str(value) if value is not None else default

    def reload(self) -> None:
        """Reload configuration from all sources."""
        reload_settings()

    def as_dict(self) -> dict[str, Any]:
        """Return all configuration as a dictionary.

        Returns:
            Dictionary containing all configuration values.
        """
        result: dict[str, Any] = settings.as_dict()
        return result


# Default adapter instance for convenience
config_adapter = DynaconfConfigAdapter()
