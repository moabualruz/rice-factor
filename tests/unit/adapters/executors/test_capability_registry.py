"""Tests for CapabilityRegistry."""

from pathlib import Path

import pytest

from rice_factor.adapters.executors.capability_registry import (
    CapabilityRegistry,
    CapabilityRegistryError,
)


class TestCapabilityRegistryLoading:
    """Tests for capability registry loading."""

    def test_loads_bundled_default_configuration(self) -> None:
        """Should load the bundled default configuration."""
        registry = CapabilityRegistry()
        # Should have at least python configured
        assert registry.is_language_supported("python")

    def test_loads_without_project_root(self) -> None:
        """Should load successfully without project root."""
        registry = CapabilityRegistry(project_root=None)
        assert registry.is_language_supported("python")

    def test_loads_with_nonexistent_project_root(self, tmp_path: Path) -> None:
        """Should load with project root that has no override."""
        registry = CapabilityRegistry(project_root=tmp_path)
        # Should still have bundled config
        assert registry.is_language_supported("python")


class TestCapabilityRegistryCheckCapability:
    """Tests for check_capability method."""

    def test_returns_true_for_supported_operation(self) -> None:
        """Should return True for explicitly supported operations."""
        registry = CapabilityRegistry()
        assert registry.check_capability("move_file", "python") is True

    def test_returns_true_for_rename_symbol_python(self) -> None:
        """Should return True for rename_symbol on python."""
        registry = CapabilityRegistry()
        assert registry.check_capability("rename_symbol", "python") is True

    def test_returns_false_for_unsupported_operation(self) -> None:
        """Should return False for explicitly unsupported operations."""
        registry = CapabilityRegistry()
        # Go doesn't support extract_interface
        assert registry.check_capability("extract_interface", "go") is False

    def test_returns_false_for_partial_support(self) -> None:
        """Should return False for partial support (strict mode)."""
        registry = CapabilityRegistry()
        # Rust has partial enforce_dependency
        assert registry.check_capability("enforce_dependency", "rust") is False

    def test_returns_false_for_unknown_language(self) -> None:
        """Should return False for unknown languages."""
        registry = CapabilityRegistry()
        assert registry.check_capability("move_file", "brainfuck") is False

    def test_returns_false_for_unknown_operation(self) -> None:
        """Should return False for unknown operations."""
        registry = CapabilityRegistry()
        assert registry.check_capability("teleport_code", "python") is False

    def test_returns_false_for_unknown_language_and_operation(self) -> None:
        """Should return False when both language and operation are unknown."""
        registry = CapabilityRegistry()
        assert registry.check_capability("teleport_code", "brainfuck") is False


class TestCapabilityRegistryGetCapabilityStatus:
    """Tests for get_capability_status method."""

    def test_returns_supported_for_true_values(self) -> None:
        """Should return 'supported' for true values."""
        registry = CapabilityRegistry()
        assert registry.get_capability_status("move_file", "python") == "supported"

    def test_returns_unsupported_for_false_values(self) -> None:
        """Should return 'unsupported' for false values."""
        registry = CapabilityRegistry()
        # Go doesn't support extract_interface
        assert (
            registry.get_capability_status("extract_interface", "go")
            == "unsupported"
        )

    def test_returns_partial_for_partial_values(self) -> None:
        """Should return 'partial' for partial values."""
        registry = CapabilityRegistry()
        assert registry.get_capability_status("enforce_dependency", "rust") == "partial"

    def test_returns_unsupported_for_unknown_language(self) -> None:
        """Should return 'unsupported' for unknown languages."""
        registry = CapabilityRegistry()
        assert (
            registry.get_capability_status("move_file", "brainfuck") == "unsupported"
        )

    def test_returns_unsupported_for_unknown_operation(self) -> None:
        """Should return 'unsupported' for unknown operations."""
        registry = CapabilityRegistry()
        assert (
            registry.get_capability_status("teleport_code", "python") == "unsupported"
        )


class TestCapabilityRegistryGetSupportedOperations:
    """Tests for get_supported_operations method."""

    def test_returns_supported_operations_for_language(self) -> None:
        """Should return list of fully supported operations."""
        registry = CapabilityRegistry()
        ops = registry.get_supported_operations("python")
        assert "move_file" in ops
        assert "rename_symbol" in ops
        # Python now supports all 4 operations via Rope
        assert "extract_interface" in ops
        assert "enforce_dependency" in ops

    def test_excludes_partial_support(self) -> None:
        """Should exclude operations with partial support."""
        registry = CapabilityRegistry()
        ops = registry.get_supported_operations("rust")
        # enforce_dependency is partial for rust
        assert "enforce_dependency" not in ops

    def test_returns_empty_list_for_unknown_language(self) -> None:
        """Should return empty list for unknown languages."""
        registry = CapabilityRegistry()
        ops = registry.get_supported_operations("brainfuck")
        assert ops == []


class TestCapabilityRegistryGetSupportedLanguages:
    """Tests for get_supported_languages method."""

    def test_returns_all_configured_languages(self) -> None:
        """Should return all languages in the registry."""
        registry = CapabilityRegistry()
        languages = registry.get_supported_languages()
        # Check known languages from bundled config
        assert "python" in languages
        assert "rust" in languages
        assert "go" in languages
        assert "javascript" in languages
        assert "typescript" in languages

    def test_returns_list_type(self) -> None:
        """Should return a list."""
        registry = CapabilityRegistry()
        languages = registry.get_supported_languages()
        assert isinstance(languages, list)


class TestCapabilityRegistryIsLanguageSupported:
    """Tests for is_language_supported method."""

    def test_returns_true_for_known_language(self) -> None:
        """Should return True for configured languages."""
        registry = CapabilityRegistry()
        assert registry.is_language_supported("python") is True
        assert registry.is_language_supported("rust") is True

    def test_returns_false_for_unknown_language(self) -> None:
        """Should return False for unconfigured languages."""
        registry = CapabilityRegistry()
        assert registry.is_language_supported("brainfuck") is False
        assert registry.is_language_supported("") is False


class TestCapabilityRegistryCheckAllCapabilities:
    """Tests for check_all_capabilities method."""

    def test_returns_empty_list_when_all_supported(self) -> None:
        """Should return empty list when all operations are supported."""
        registry = CapabilityRegistry()
        unsupported = registry.check_all_capabilities(
            ["move_file", "rename_symbol"], "python"
        )
        assert unsupported == []

    def test_returns_unsupported_operations(self) -> None:
        """Should return list of unsupported operations."""
        registry = CapabilityRegistry()
        # Use Go which doesn't support extract_interface or enforce_dependency
        unsupported = registry.check_all_capabilities(
            ["move_file", "extract_interface", "enforce_dependency"], "go"
        )
        assert "extract_interface" in unsupported
        assert "enforce_dependency" in unsupported
        assert "move_file" not in unsupported

    def test_includes_partial_as_unsupported(self) -> None:
        """Should include partial support as unsupported."""
        registry = CapabilityRegistry()
        unsupported = registry.check_all_capabilities(["enforce_dependency"], "rust")
        assert "enforce_dependency" in unsupported

    def test_returns_all_for_unknown_language(self) -> None:
        """Should return all operations for unknown language."""
        registry = CapabilityRegistry()
        ops = ["move_file", "rename_symbol"]
        unsupported = registry.check_all_capabilities(ops, "brainfuck")
        assert set(unsupported) == set(ops)


class TestCapabilityRegistryProjectOverride:
    """Tests for project override functionality."""

    def test_project_override_takes_precedence(self, tmp_path: Path) -> None:
        """Should use project override values over bundled defaults."""
        # Create project override that changes python's extract_interface to true
        override_dir = tmp_path / "tools" / "registry"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "capability_registry.yaml"
        override_file.write_text(
            """
languages:
  python:
    operations:
      extract_interface: true
""",
            encoding="utf-8",
        )

        registry = CapabilityRegistry(project_root=tmp_path)
        # Should now be true due to override
        assert registry.check_capability("extract_interface", "python") is True
        # Other operations should still come from bundled
        assert registry.check_capability("move_file", "python") is True

    def test_project_override_adds_new_language(self, tmp_path: Path) -> None:
        """Should add new languages from project override."""
        override_dir = tmp_path / "tools" / "registry"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "capability_registry.yaml"
        override_file.write_text(
            """
languages:
  haskell:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: false
""",
            encoding="utf-8",
        )

        registry = CapabilityRegistry(project_root=tmp_path)
        assert registry.is_language_supported("haskell")
        assert registry.check_capability("move_file", "haskell") is True

    def test_project_override_merges_operations(self, tmp_path: Path) -> None:
        """Should merge operations from project override."""
        override_dir = tmp_path / "tools" / "registry"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "capability_registry.yaml"
        # Only override one operation, others should remain
        override_file.write_text(
            """
languages:
  python:
    operations:
      enforce_dependency: true
""",
            encoding="utf-8",
        )

        registry = CapabilityRegistry(project_root=tmp_path)
        # Overridden operation
        assert registry.check_capability("enforce_dependency", "python") is True
        # Original operations should still be present
        assert registry.check_capability("move_file", "python") is True
        assert registry.check_capability("rename_symbol", "python") is True


class TestCapabilityRegistrySchemaValidation:
    """Tests for registry schema validation."""

    def test_rejects_missing_languages_key(self, tmp_path: Path) -> None:
        """Should reject registry without 'languages' key."""
        override_dir = tmp_path / "tools" / "registry"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "capability_registry.yaml"
        override_file.write_text(
            """
not_languages:
  python:
    operations:
      move_file: true
""",
            encoding="utf-8",
        )

        with pytest.raises(CapabilityRegistryError) as exc_info:
            CapabilityRegistry(project_root=tmp_path)
        assert "missing 'languages' key" in str(exc_info.value)

    def test_rejects_missing_operations_key(self, tmp_path: Path) -> None:
        """Should reject language without 'operations' key."""
        override_dir = tmp_path / "tools" / "registry"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "capability_registry.yaml"
        override_file.write_text(
            """
languages:
  python:
    not_operations:
      move_file: true
""",
            encoding="utf-8",
        )

        with pytest.raises(CapabilityRegistryError) as exc_info:
            CapabilityRegistry(project_root=tmp_path)
        assert "missing 'operations' key" in str(exc_info.value)

    def test_rejects_invalid_operation_value(self, tmp_path: Path) -> None:
        """Should reject operations with invalid values."""
        override_dir = tmp_path / "tools" / "registry"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "capability_registry.yaml"
        override_file.write_text(
            """
languages:
  python:
    operations:
      move_file: "yes"
""",
            encoding="utf-8",
        )

        with pytest.raises(CapabilityRegistryError) as exc_info:
            CapabilityRegistry(project_root=tmp_path)
        assert "must be true, false, or 'partial'" in str(exc_info.value)

    def test_accepts_partial_string_value(self, tmp_path: Path) -> None:
        """Should accept 'partial' as a valid operation value."""
        override_dir = tmp_path / "tools" / "registry"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "capability_registry.yaml"
        override_file.write_text(
            """
languages:
  python:
    operations:
      enforce_dependency: partial
""",
            encoding="utf-8",
        )

        # Should not raise
        registry = CapabilityRegistry(project_root=tmp_path)
        assert registry.get_capability_status("enforce_dependency", "python") == "partial"

    def test_rejects_invalid_yaml(self, tmp_path: Path) -> None:
        """Should reject malformed YAML."""
        override_dir = tmp_path / "tools" / "registry"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "capability_registry.yaml"
        override_file.write_text(
            """
languages:
  python:
    operations:
      move_file: [[[invalid
""",
            encoding="utf-8",
        )

        with pytest.raises(CapabilityRegistryError) as exc_info:
            CapabilityRegistry(project_root=tmp_path)
        assert "Failed to parse" in str(exc_info.value)


class TestCapabilityRegistryGetAllOperations:
    """Tests for get_all_operations method."""

    def test_returns_all_operations_for_language(self) -> None:
        """Should return all operations with their values."""
        registry = CapabilityRegistry()
        ops = registry.get_all_operations("python")
        assert ops["move_file"] is True
        assert ops["rename_symbol"] is True
        # Python now supports all 4 operations via Rope
        assert ops["extract_interface"] is True
        assert ops["enforce_dependency"] is True

    def test_includes_partial_values(self) -> None:
        """Should include partial values."""
        registry = CapabilityRegistry()
        ops = registry.get_all_operations("rust")
        assert ops["enforce_dependency"] == "partial"

    def test_returns_empty_dict_for_unknown_language(self) -> None:
        """Should return empty dict for unknown languages."""
        registry = CapabilityRegistry()
        ops = registry.get_all_operations("brainfuck")
        assert ops == {}


class TestCapabilityRegistryError:
    """Tests for CapabilityRegistryError exception."""

    def test_error_is_exception(self) -> None:
        """CapabilityRegistryError should be an Exception."""
        assert issubclass(CapabilityRegistryError, Exception)

    def test_error_message_preserved(self) -> None:
        """Should preserve error message."""
        error = CapabilityRegistryError("Test error message")
        assert str(error) == "Test error message"
