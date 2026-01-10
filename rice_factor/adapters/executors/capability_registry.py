"""Capability Registry for refactoring operations.

This module provides the CapabilityRegistry class that tracks which refactoring
operations are supported for each programming language. The registry loads from
a bundled default configuration and can be overridden by a project-specific
configuration.

Example:
    >>> registry = CapabilityRegistry()
    >>> registry.check_capability("move_file", "python")
    True
    >>> registry.check_capability("extract_interface", "python")
    False
"""

from __future__ import annotations

import importlib.resources
from typing import TYPE_CHECKING, Any, Literal

import yaml

if TYPE_CHECKING:
    from pathlib import Path

# Type alias for capability status
CapabilityStatus = Literal["supported", "unsupported", "partial"]


class CapabilityRegistryError(Exception):
    """Raised when there's an error with the capability registry."""

    pass


class CapabilityRegistry:
    """Registry for tracking refactoring operation capabilities by language.

    The registry loads capabilities from:
    1. Bundled default configuration (rice_factor/config/capability_registry.yaml)
    2. Optional project override (tools/registry/capability_registry.yaml)

    Project overrides are merged with bundled defaults, with project values
    taking precedence.

    Attributes:
        _registry: The loaded and merged registry data.
        _project_root: Optional path to project root for loading overrides.
    """

    # Known operations that can be checked
    KNOWN_OPERATIONS = frozenset(
        {
            "move_file",
            "rename_symbol",
            "extract_interface",
            "enforce_dependency",
        }
    )

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize the capability registry.

        Args:
            project_root: Optional path to project root. If provided, the
                registry will look for an override file at
                tools/registry/capability_registry.yaml within the project.
        """
        self._project_root = project_root
        self._registry: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load and merge registry configurations."""
        # Load bundled default
        bundled = self._load_bundled_registry()
        self._validate_registry_schema(bundled)

        # Load project override if available
        if self._project_root is not None:
            project = self._load_project_registry(self._project_root)
            if project is not None:
                self._validate_registry_schema(project)
                bundled = self._merge_registries(bundled, project)

        self._registry = bundled

    def _load_bundled_registry(self) -> dict[str, Any]:
        """Load the bundled default capability registry.

        Returns:
            The parsed YAML data as a dictionary.

        Raises:
            CapabilityRegistryError: If the bundled registry cannot be loaded.
        """
        try:
            # Use importlib.resources for package data access
            files = importlib.resources.files("rice_factor.config")
            registry_file = files.joinpath("capability_registry.yaml")
            content = registry_file.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                raise CapabilityRegistryError(
                    "Bundled capability registry is not a valid YAML mapping"
                )
            return data
        except Exception as e:
            raise CapabilityRegistryError(
                f"Failed to load bundled capability registry: {e}"
            ) from e

    def _load_project_registry(self, project_root: Path) -> dict[str, Any] | None:
        """Load the project-specific capability registry override.

        Args:
            project_root: Path to the project root directory.

        Returns:
            The parsed YAML data, or None if no override file exists.

        Raises:
            CapabilityRegistryError: If the override file exists but cannot be parsed.
        """
        override_path = project_root / "tools" / "registry" / "capability_registry.yaml"
        if not override_path.exists():
            return None

        try:
            content = override_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                raise CapabilityRegistryError(
                    f"Project capability registry at {override_path} is not a valid YAML mapping"
                )
            return data
        except yaml.YAMLError as e:
            raise CapabilityRegistryError(
                f"Failed to parse project capability registry at {override_path}: {e}"
            ) from e

    def _merge_registries(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge override registry into base registry.

        Performs a deep merge where override values take precedence.

        Args:
            base: The base registry configuration.
            override: The override registry configuration.

        Returns:
            The merged registry configuration.
        """
        result = dict(base)

        # Merge languages
        if "languages" in override:
            if "languages" not in result:
                result["languages"] = {}

            for lang, lang_config in override.get("languages", {}).items():
                if lang not in result["languages"]:
                    result["languages"][lang] = lang_config
                else:
                    # Merge language config
                    base_lang = result["languages"][lang]
                    if "operations" in lang_config:
                        if "operations" not in base_lang:
                            base_lang["operations"] = {}
                        base_lang["operations"].update(lang_config["operations"])

        return result

    def _validate_registry_schema(self, data: dict[str, Any]) -> None:
        """Validate the registry data against the expected schema.

        Args:
            data: The registry data to validate.

        Raises:
            CapabilityRegistryError: If the data does not match the expected schema.
        """
        if "languages" not in data:
            raise CapabilityRegistryError(
                "Invalid registry schema: missing 'languages' key"
            )

        languages = data["languages"]
        if not isinstance(languages, dict):
            raise CapabilityRegistryError(
                "Invalid registry schema: 'languages' must be a mapping"
            )

        for lang, lang_config in languages.items():
            if not isinstance(lang_config, dict):
                raise CapabilityRegistryError(
                    f"Invalid registry schema: language '{lang}' must be a mapping"
                )

            if "operations" not in lang_config:
                raise CapabilityRegistryError(
                    f"Invalid registry schema: language '{lang}' missing 'operations' key"
                )

            operations = lang_config["operations"]
            if not isinstance(operations, dict):
                raise CapabilityRegistryError(
                    f"Invalid registry schema: operations for '{lang}' must be a mapping"
                )

            for op, value in operations.items():
                if not isinstance(value, bool) and value != "partial":
                    raise CapabilityRegistryError(
                        f"Invalid registry schema: operation '{op}' for '{lang}' "
                        f"must be true, false, or 'partial', got {value!r}"
                    )

    def check_capability(self, operation: str, language: str) -> bool:
        """Check if an operation is supported for a language.

        In strict mode, "partial" support is treated as False.

        Args:
            operation: The operation to check (e.g., "move_file", "rename_symbol").
            language: The programming language (e.g., "python", "rust").

        Returns:
            True only if the operation is explicitly supported (true) for the
            language. Returns False for unsupported, partial, unknown language,
            or unknown operation.
        """
        languages = self._registry.get("languages", {})
        if language not in languages:
            return False

        operations = languages[language].get("operations", {})
        if operation not in operations:
            return False

        value = operations[operation]
        # Only return True for explicit True, not for "partial"
        return value is True

    def get_capability_status(self, operation: str, language: str) -> CapabilityStatus:
        """Get the detailed capability status for an operation.

        Args:
            operation: The operation to check.
            language: The programming language.

        Returns:
            "supported" if true, "partial" if partial, "unsupported" otherwise.
        """
        languages = self._registry.get("languages", {})
        if language not in languages:
            return "unsupported"

        operations = languages[language].get("operations", {})
        if operation not in operations:
            return "unsupported"

        value = operations[operation]
        if value is True:
            return "supported"
        elif value == "partial":
            return "partial"
        else:
            return "unsupported"

    def get_supported_operations(self, language: str) -> list[str]:
        """Get list of fully supported operations for a language.

        Args:
            language: The programming language.

        Returns:
            List of operation names that are fully supported (true).
            Returns empty list for unknown languages.
        """
        languages = self._registry.get("languages", {})
        if language not in languages:
            return []

        operations = languages[language].get("operations", {})
        return [op for op, value in operations.items() if value is True]

    def get_supported_languages(self) -> list[str]:
        """Get list of all configured languages.

        Returns:
            List of language names in the registry.
        """
        return list(self._registry.get("languages", {}).keys())

    def is_language_supported(self, language: str) -> bool:
        """Check if a language is configured in the registry.

        Args:
            language: The programming language to check.

        Returns:
            True if the language has configuration, False otherwise.
        """
        return language in self._registry.get("languages", {})

    def check_all_capabilities(
        self, operations: list[str], language: str
    ) -> list[str]:
        """Check multiple operations and return unsupported ones.

        Args:
            operations: List of operations to check.
            language: The programming language.

        Returns:
            List of operations that are NOT supported for the language.
        """
        return [op for op in operations if not self.check_capability(op, language)]

    def get_all_operations(self, language: str) -> dict[str, bool | str]:
        """Get all operations and their values for a language.

        Args:
            language: The programming language.

        Returns:
            Dictionary mapping operation names to their values (True/False/"partial").
            Returns empty dict for unknown languages.
        """
        languages = self._registry.get("languages", {})
        if language not in languages:
            return {}

        return dict(languages[language].get("operations", {}))
