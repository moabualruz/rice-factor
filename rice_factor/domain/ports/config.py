"""Configuration port interface for hexagonal architecture.

This port defines the contract for accessing configuration values.
Adapters can implement this protocol to provide different config sources.
"""

from typing import Any, Protocol


class ConfigPort(Protocol):
    """Protocol for configuration access.

    Defines the interface that configuration adapters must implement.
    This allows the domain to access configuration without depending
    on specific implementations like Dynaconf.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: Dot-separated configuration key (e.g., "llm.provider")
            default: Default value if key is not found

        Returns:
            The configuration value, or default if not found.
        """
        ...

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value.

        Args:
            key: Dot-separated configuration key
            default: Default value if key is not found

        Returns:
            The boolean configuration value.
        """
        ...

    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value.

        Args:
            key: Dot-separated configuration key
            default: Default value if key is not found

        Returns:
            The integer configuration value.
        """
        ...

    def get_str(self, key: str, default: str = "") -> str:
        """Get a string configuration value.

        Args:
            key: Dot-separated configuration key
            default: Default value if key is not found

        Returns:
            The string configuration value.
        """
        ...

    def reload(self) -> None:
        """Reload configuration from all sources.

        Should be called when config files are modified to pick up
        changes without restarting the application.
        """
        ...

    def as_dict(self) -> dict[str, Any]:
        """Return all configuration as a dictionary.

        Returns:
            Dictionary containing all configuration values.
        """
        ...
