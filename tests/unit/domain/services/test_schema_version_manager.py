"""Unit tests for SchemaVersionManager service."""

from __future__ import annotations

from typing import Any

import pytest

from rice_factor.domain.services.schema_version_manager import (
    CompatibilityLevel,
    IncompatibleVersionError,
    Migration,
    MigrationError,
    SchemaVersion,
    SchemaVersionManager,
    ValidationResult,
    VersionParseError,
    get_schema_version_manager,
    reset_schema_version_manager,
)


class TestSchemaVersion:
    """Tests for SchemaVersion class."""

    def test_parse_valid_version(self) -> None:
        """parse should handle valid version strings."""
        v = SchemaVersion.parse("1.0")
        assert v.major == 1
        assert v.minor == 0

    def test_parse_with_spaces(self) -> None:
        """parse should handle whitespace."""
        v = SchemaVersion.parse("  2.5  ")
        assert v.major == 2
        assert v.minor == 5

    def test_parse_invalid_format(self) -> None:
        """parse should raise on invalid format."""
        with pytest.raises(VersionParseError):
            SchemaVersion.parse("1.2.3")

        with pytest.raises(VersionParseError):
            SchemaVersion.parse("v1.0")

        with pytest.raises(VersionParseError):
            SchemaVersion.parse("")

    def test_str(self) -> None:
        """__str__ should return version string."""
        v = SchemaVersion(1, 2)
        assert str(v) == "1.2"

    def test_comparison(self) -> None:
        """SchemaVersion should be comparable."""
        v1 = SchemaVersion(1, 0)
        v2 = SchemaVersion(1, 1)
        v3 = SchemaVersion(2, 0)

        assert v1 < v2
        assert v2 < v3
        assert v1 == SchemaVersion(1, 0)

    def test_is_compatible_with_same(self) -> None:
        """Same versions should be fully compatible."""
        v1 = SchemaVersion(1, 0)
        v2 = SchemaVersion(1, 0)
        assert v1.is_compatible_with(v2) == CompatibilityLevel.FULL

    def test_is_compatible_with_minor_upgrade(self) -> None:
        """Minor version upgrades should be backward compatible."""
        v1 = SchemaVersion(1, 1)
        v2 = SchemaVersion(1, 0)
        assert v1.is_compatible_with(v2) == CompatibilityLevel.BACKWARD

    def test_is_compatible_with_minor_downgrade(self) -> None:
        """Minor version downgrades should be forward compatible."""
        v1 = SchemaVersion(1, 0)
        v2 = SchemaVersion(1, 1)
        assert v1.is_compatible_with(v2) == CompatibilityLevel.FORWARD

    def test_is_compatible_with_major_change(self) -> None:
        """Major version changes should be breaking."""
        v1 = SchemaVersion(1, 0)
        v2 = SchemaVersion(2, 0)
        assert v1.is_compatible_with(v2) == CompatibilityLevel.BREAKING


class TestCompatibilityLevel:
    """Tests for CompatibilityLevel enum."""

    def test_full_value(self) -> None:
        """FULL should have 'full' value."""
        assert CompatibilityLevel.FULL.value == "full"

    def test_breaking_value(self) -> None:
        """BREAKING should have 'breaking' value."""
        assert CompatibilityLevel.BREAKING.value == "breaking"


class TestMigrationError:
    """Tests for MigrationError exception."""

    def test_exception_attributes(self) -> None:
        """MigrationError should store all attributes."""
        exc = MigrationError(
            from_version="1.0",
            to_version="1.1",
            artifact_type="ProjectPlan",
            message="Test error",
        )
        assert exc.from_version == "1.0"
        assert exc.to_version == "1.1"
        assert exc.artifact_type == "ProjectPlan"

    def test_exception_message(self) -> None:
        """MigrationError message should be descriptive."""
        exc = MigrationError(
            from_version="1.0",
            to_version="2.0",
            artifact_type="TestPlan",
            message="Field missing",
        )
        assert "TestPlan" in str(exc)
        assert "1.0" in str(exc)
        assert "2.0" in str(exc)


class TestMigration:
    """Tests for Migration dataclass."""

    def test_migration_attributes(self) -> None:
        """Migration should store all attributes."""
        migrate_fn = lambda data, f, t: data
        migration = Migration(
            from_version=SchemaVersion(1, 0),
            to_version=SchemaVersion(1, 1),
            artifact_type="ProjectPlan",
            migrate=migrate_fn,
            description="Add new field",
        )
        assert migration.from_version == SchemaVersion(1, 0)
        assert migration.artifact_type == "ProjectPlan"
        assert migration.rollback is None


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self) -> None:
        """ValidationResult should represent valid state."""
        result = ValidationResult(
            compatible=True,
            level=CompatibilityLevel.FULL,
        )
        assert result.compatible is True
        assert result.issues == []

    def test_invalid_result(self) -> None:
        """ValidationResult should represent invalid state."""
        result = ValidationResult(
            compatible=False,
            level=CompatibilityLevel.BREAKING,
            issues=["Major version mismatch"],
        )
        assert result.compatible is False
        assert len(result.issues) == 1


class TestSchemaVersionManagerInit:
    """Tests for SchemaVersionManager initialization."""

    def test_has_default_versions(self) -> None:
        """Manager should initialize with default artifact types."""
        manager = SchemaVersionManager()
        types = manager.get_registered_types()

        assert "ProjectPlan" in types
        assert "ArchitecturePlan" in types
        assert "TestPlan" in types

    def test_default_version_is_1_0(self) -> None:
        """Default version should be 1.0."""
        manager = SchemaVersionManager()
        version = manager.get_current_version("ProjectPlan")

        assert version is not None
        assert version.major == 1
        assert version.minor == 0


class TestSchemaVersionManagerSetVersion:
    """Tests for SchemaVersionManager.set_current_version."""

    def test_set_version_string(self) -> None:
        """set_current_version should accept string."""
        manager = SchemaVersionManager()
        manager.set_current_version("ProjectPlan", "2.0")

        version = manager.get_current_version("ProjectPlan")
        assert version is not None
        assert version.major == 2

    def test_set_version_object(self) -> None:
        """set_current_version should accept SchemaVersion."""
        manager = SchemaVersionManager()
        manager.set_current_version("ProjectPlan", SchemaVersion(3, 1))

        version = manager.get_current_version("ProjectPlan")
        assert version is not None
        assert version.major == 3
        assert version.minor == 1

    def test_set_version_new_type(self) -> None:
        """set_current_version should create new type."""
        manager = SchemaVersionManager()
        manager.set_current_version("CustomType", "1.0")

        assert "CustomType" in manager.get_registered_types()


class TestSchemaVersionManagerRegisterMigration:
    """Tests for SchemaVersionManager.register_migration."""

    def test_register_migration(self) -> None:
        """register_migration should add migration."""
        manager = SchemaVersionManager()
        migrate_fn = lambda data, f, t: data

        migration = manager.register_migration(
            artifact_type="ProjectPlan",
            from_version="1.0",
            to_version="1.1",
            migrate=migrate_fn,
            description="Add new field",
        )

        assert migration.from_version == SchemaVersion(1, 0)
        assert manager.get_migration_count("ProjectPlan") == 1

    def test_register_multiple_migrations(self) -> None:
        """Should handle multiple migrations."""
        manager = SchemaVersionManager()
        migrate_fn = lambda data, f, t: data

        manager.register_migration("ProjectPlan", "1.0", "1.1", migrate_fn)
        manager.register_migration("ProjectPlan", "1.1", "1.2", migrate_fn)

        assert manager.get_migration_count("ProjectPlan") == 2


class TestSchemaVersionManagerGetMigrationPath:
    """Tests for SchemaVersionManager.get_migration_path."""

    def test_no_path_when_same_version(self) -> None:
        """No migration needed for same version."""
        manager = SchemaVersionManager()

        path = manager.get_migration_path("ProjectPlan", "1.0", "1.0")
        assert path == []

    def test_direct_path(self) -> None:
        """Should find direct migration."""
        manager = SchemaVersionManager()
        migrate_fn = lambda data, f, t: data

        manager.register_migration("ProjectPlan", "1.0", "1.1", migrate_fn)

        path = manager.get_migration_path("ProjectPlan", "1.0", "1.1")
        assert len(path) == 1
        assert path[0].to_version == SchemaVersion(1, 1)

    def test_multi_step_path(self) -> None:
        """Should find multi-step migration path."""
        manager = SchemaVersionManager()
        migrate_fn = lambda data, f, t: data

        manager.register_migration("ProjectPlan", "1.0", "1.1", migrate_fn)
        manager.register_migration("ProjectPlan", "1.1", "1.2", migrate_fn)
        manager.register_migration("ProjectPlan", "1.2", "2.0", migrate_fn)

        path = manager.get_migration_path("ProjectPlan", "1.0", "2.0")
        assert len(path) == 3

    def test_no_path_available(self) -> None:
        """Should return empty list when no path exists."""
        manager = SchemaVersionManager()

        path = manager.get_migration_path("ProjectPlan", "1.0", "2.0")
        assert path == []


class TestSchemaVersionManagerMigrate:
    """Tests for SchemaVersionManager.migrate."""

    def test_migrate_simple(self) -> None:
        """migrate should apply transformation."""
        manager = SchemaVersionManager()

        def add_field(data: dict[str, Any], f: str, t: str) -> dict[str, Any]:
            return {**data, "new_field": "default"}

        manager.register_migration("ProjectPlan", "1.0", "1.1", add_field)

        artifact = {"artifact_version": "1.0", "name": "test"}
        result = manager.migrate(artifact, "ProjectPlan", "1.0", "1.1")

        assert result["new_field"] == "default"
        assert result["artifact_version"] == "1.1"

    def test_migrate_to_current(self) -> None:
        """migrate should use current version as default."""
        manager = SchemaVersionManager()
        manager.set_current_version("ProjectPlan", "1.1")

        def add_field(data: dict[str, Any], f: str, t: str) -> dict[str, Any]:
            return {**data, "migrated": True}

        manager.register_migration("ProjectPlan", "1.0", "1.1", add_field)

        artifact = {"artifact_version": "1.0", "name": "test"}
        result = manager.migrate(artifact, "ProjectPlan", "1.0")

        assert result["migrated"] is True

    def test_migrate_chain(self) -> None:
        """migrate should apply migration chain."""
        manager = SchemaVersionManager()

        def add_a(data: dict[str, Any], f: str, t: str) -> dict[str, Any]:
            return {**data, "a": 1}

        def add_b(data: dict[str, Any], f: str, t: str) -> dict[str, Any]:
            return {**data, "b": 2}

        manager.register_migration("ProjectPlan", "1.0", "1.1", add_a)
        manager.register_migration("ProjectPlan", "1.1", "1.2", add_b)

        artifact = {"artifact_version": "1.0", "name": "test"}
        result = manager.migrate(artifact, "ProjectPlan", "1.0", "1.2")

        assert result["a"] == 1
        assert result["b"] == 2
        assert result["artifact_version"] == "1.2"

    def test_migrate_no_path_raises(self) -> None:
        """migrate should raise when no path exists."""
        manager = SchemaVersionManager()

        artifact = {"artifact_version": "1.0", "name": "test"}
        with pytest.raises(MigrationError) as exc_info:
            manager.migrate(artifact, "ProjectPlan", "1.0", "2.0")

        assert "No migration path found" in str(exc_info.value)

    def test_migrate_error_propagates(self) -> None:
        """migrate should propagate migration errors."""
        manager = SchemaVersionManager()

        def bad_migrate(data: dict[str, Any], f: str, t: str) -> dict[str, Any]:
            raise ValueError("Bad data")

        manager.register_migration("ProjectPlan", "1.0", "1.1", bad_migrate)

        artifact = {"artifact_version": "1.0"}
        with pytest.raises(MigrationError):
            manager.migrate(artifact, "ProjectPlan", "1.0", "1.1")


class TestSchemaVersionManagerValidateCompatibility:
    """Tests for SchemaVersionManager.validate_compatibility."""

    def test_validate_same_version(self) -> None:
        """Same version should be fully compatible."""
        manager = SchemaVersionManager()
        manager.set_current_version("ProjectPlan", "1.0")

        artifact = {"artifact_version": "1.0", "name": "test"}
        result = manager.validate_compatibility(artifact, "ProjectPlan")

        assert result.compatible is True
        assert result.level == CompatibilityLevel.FULL

    def test_validate_minor_upgrade(self) -> None:
        """Minor upgrade should be compatible with warning."""
        manager = SchemaVersionManager()
        manager.set_current_version("ProjectPlan", "1.1")

        artifact = {"artifact_version": "1.0", "name": "test"}
        result = manager.validate_compatibility(artifact, "ProjectPlan")

        assert result.compatible is True
        assert result.level == CompatibilityLevel.FORWARD
        assert len(result.warnings) > 0

    def test_validate_major_change(self) -> None:
        """Major change should be incompatible."""
        manager = SchemaVersionManager()
        manager.set_current_version("ProjectPlan", "2.0")

        artifact = {"artifact_version": "1.0", "name": "test"}
        result = manager.validate_compatibility(artifact, "ProjectPlan")

        assert result.compatible is False
        assert result.level == CompatibilityLevel.BREAKING
        assert len(result.issues) > 0

    def test_validate_invalid_version(self) -> None:
        """Invalid version string should fail validation."""
        manager = SchemaVersionManager()

        artifact = {"artifact_version": "invalid", "name": "test"}
        result = manager.validate_compatibility(artifact, "ProjectPlan")

        assert result.compatible is False
        assert len(result.issues) > 0

    def test_validate_unknown_type(self) -> None:
        """Unknown type should return compatible with warning."""
        manager = SchemaVersionManager()

        artifact = {"artifact_version": "1.0"}
        result = manager.validate_compatibility(artifact, "UnknownType")

        assert result.compatible is True
        assert len(result.warnings) > 0


class TestSchemaVersionManagerNeedsMigration:
    """Tests for SchemaVersionManager.needs_migration."""

    def test_needs_migration_when_different(self) -> None:
        """needs_migration should return True when versions differ."""
        manager = SchemaVersionManager()
        manager.set_current_version("ProjectPlan", "1.1")

        artifact = {"artifact_version": "1.0"}
        assert manager.needs_migration(artifact, "ProjectPlan") is True

    def test_no_migration_when_same(self) -> None:
        """needs_migration should return False when versions match."""
        manager = SchemaVersionManager()
        manager.set_current_version("ProjectPlan", "1.0")

        artifact = {"artifact_version": "1.0"}
        assert manager.needs_migration(artifact, "ProjectPlan") is False

    def test_needs_migration_with_invalid_version(self) -> None:
        """needs_migration should return True for invalid versions."""
        manager = SchemaVersionManager()

        artifact = {"artifact_version": "bad"}
        assert manager.needs_migration(artifact, "ProjectPlan") is True


class TestSchemaVersionManagerToDict:
    """Tests for SchemaVersionManager.to_dict."""

    def test_to_dict_includes_versions(self) -> None:
        """to_dict should include current versions."""
        manager = SchemaVersionManager()
        manager.set_current_version("ProjectPlan", "2.0")

        state = manager.to_dict()

        assert "versions" in state
        assert state["versions"]["ProjectPlan"] == "2.0"

    def test_to_dict_includes_migrations(self) -> None:
        """to_dict should include registered migrations."""
        manager = SchemaVersionManager()
        manager.register_migration(
            "ProjectPlan", "1.0", "1.1",
            lambda d, f, t: d,
            description="Test migration",
        )

        state = manager.to_dict()

        assert "migrations" in state
        assert "ProjectPlan" in state["migrations"]
        assert len(state["migrations"]["ProjectPlan"]) == 1


class TestGlobalSchemaVersionManager:
    """Tests for global schema version manager functions."""

    def test_get_schema_version_manager_returns_same_instance(self) -> None:
        """get_schema_version_manager should return same instance."""
        reset_schema_version_manager()

        manager1 = get_schema_version_manager()
        manager2 = get_schema_version_manager()

        assert manager1 is manager2

    def test_reset_schema_version_manager_clears_instance(self) -> None:
        """reset_schema_version_manager should clear global instance."""
        manager1 = get_schema_version_manager()

        reset_schema_version_manager()

        manager2 = get_schema_version_manager()
        assert manager1 is not manager2


class TestThreadSafety:
    """Tests for thread safety of SchemaVersionManager."""

    def test_concurrent_registration(self) -> None:
        """register_migration should be thread-safe."""
        import threading

        manager = SchemaVersionManager()
        initial_count = len(manager.get_registered_types())
        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                manager.register_migration(
                    f"CustomType{i}",
                    "1.0", "1.1",
                    lambda d, f, t: d,
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Should have added 10 new types
        assert len(manager.get_registered_types()) == initial_count + 10
