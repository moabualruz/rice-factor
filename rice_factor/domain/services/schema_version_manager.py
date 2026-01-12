"""Schema version management and migration framework.

This module provides the SchemaVersionManager service that tracks schema
versions, manages migrations between versions, and validates backward
compatibility.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol


class VersionParseError(ValueError):
    """Raised when version string cannot be parsed."""

    pass


class MigrationError(Exception):
    """Raised when migration fails."""

    def __init__(
        self,
        from_version: str,
        to_version: str,
        artifact_type: str,
        message: str,
    ) -> None:
        """Initialize the exception.

        Args:
            from_version: Source version.
            to_version: Target version.
            artifact_type: Type of artifact being migrated.
            message: Error message.
        """
        self.from_version = from_version
        self.to_version = to_version
        self.artifact_type = artifact_type
        super().__init__(
            f"Migration failed for {artifact_type} "
            f"({from_version} -> {to_version}): {message}"
        )


class IncompatibleVersionError(Exception):
    """Raised when versions are incompatible."""

    def __init__(
        self,
        current_version: str,
        required_version: str,
        artifact_type: str,
    ) -> None:
        """Initialize the exception.

        Args:
            current_version: Current schema version.
            required_version: Required schema version.
            artifact_type: Type of artifact.
        """
        self.current_version = current_version
        self.required_version = required_version
        self.artifact_type = artifact_type
        super().__init__(
            f"Incompatible version for {artifact_type}: "
            f"have {current_version}, need {required_version}"
        )


class CompatibilityLevel(Enum):
    """Schema compatibility levels."""

    FULL = "full"  # Fully compatible (both directions)
    FORWARD = "forward"  # New schema can read old data
    BACKWARD = "backward"  # Old schema can read new data
    BREAKING = "breaking"  # Incompatible change


@dataclass(frozen=True, order=True)
class SchemaVersion:
    """Semantic version for schemas.

    Attributes:
        major: Major version (breaking changes).
        minor: Minor version (backward-compatible features).
    """

    major: int
    minor: int

    @classmethod
    def parse(cls, version_str: str) -> SchemaVersion:
        """Parse a version string.

        Args:
            version_str: Version string like "1.0" or "2.1".

        Returns:
            SchemaVersion instance.

        Raises:
            VersionParseError: If string cannot be parsed.
        """
        match = re.match(r"^(\d+)\.(\d+)$", version_str.strip())
        if not match:
            raise VersionParseError(
                f"Invalid version format: {version_str!r}. Expected 'major.minor'"
            )
        return cls(major=int(match.group(1)), minor=int(match.group(2)))

    def __str__(self) -> str:
        """Return version as string."""
        return f"{self.major}.{self.minor}"

    def is_compatible_with(self, other: SchemaVersion) -> CompatibilityLevel:
        """Check compatibility with another version.

        Args:
            other: Version to compare against.

        Returns:
            CompatibilityLevel indicating compatibility.
        """
        if self == other:
            return CompatibilityLevel.FULL

        if self.major != other.major:
            return CompatibilityLevel.BREAKING

        if self.minor >= other.minor:
            return CompatibilityLevel.BACKWARD
        else:
            return CompatibilityLevel.FORWARD


# Migration function type: (artifact_data, from_version, to_version) -> migrated_data
MigrationFunc = Callable[[dict[str, Any], str, str], dict[str, Any]]


@dataclass
class Migration:
    """A single migration step.

    Attributes:
        from_version: Source version.
        to_version: Target version.
        artifact_type: Type of artifact this applies to.
        migrate: Migration function.
        rollback: Optional rollback function.
        description: Human-readable description.
    """

    from_version: SchemaVersion
    to_version: SchemaVersion
    artifact_type: str
    migrate: MigrationFunc
    rollback: MigrationFunc | None = None
    description: str = ""


@dataclass
class ValidationResult:
    """Result of compatibility validation.

    Attributes:
        compatible: Whether versions are compatible.
        level: Compatibility level.
        issues: List of compatibility issues found.
        warnings: List of warnings (non-blocking).
    """

    compatible: bool
    level: CompatibilityLevel
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class MigrationRegistry(Protocol):
    """Protocol for migration registries."""

    def get_migrations(
        self,
        artifact_type: str,
        from_version: SchemaVersion,
        to_version: SchemaVersion,
    ) -> list[Migration]:
        """Get migration path between versions."""
        ...


class SchemaVersionManager:
    """Schema version management service.

    Tracks current schema versions, manages migrations, and validates
    backward compatibility for artifacts.

    Example:
        >>> manager = SchemaVersionManager()
        >>> manager.set_current_version("ProjectPlan", "1.0")
        >>> manager.register_migration(
        ...     artifact_type="ProjectPlan",
        ...     from_version="1.0",
        ...     to_version="1.1",
        ...     migrate=lambda data, f, t: {**data, "new_field": None},
        ... )
        >>> migrated = manager.migrate(artifact, "ProjectPlan", "1.0", "1.1")
    """

    def __init__(self) -> None:
        """Initialize the schema version manager."""
        self._current_versions: dict[str, SchemaVersion] = {}
        self._migrations: dict[str, list[Migration]] = {}
        self._lock = threading.RLock()

        # Initialize default versions
        self._init_default_versions()

    def _init_default_versions(self) -> None:
        """Initialize default schema versions."""
        default_types = [
            "ProjectPlan",
            "ArchitecturePlan",
            "ScaffoldPlan",
            "TestPlan",
            "ImplementationPlan",
            "RefactorPlan",
            "ValidationResult",
            "FailureReport",
            "ReconciliationPlan",
        ]
        for artifact_type in default_types:
            self._current_versions[artifact_type] = SchemaVersion(1, 0)
            self._migrations[artifact_type] = []

    def set_current_version(
        self,
        artifact_type: str,
        version: str | SchemaVersion,
    ) -> None:
        """Set the current schema version for an artifact type.

        Args:
            artifact_type: Type of artifact.
            version: Version string or SchemaVersion.
        """
        with self._lock:
            if isinstance(version, str):
                version = SchemaVersion.parse(version)
            self._current_versions[artifact_type] = version
            if artifact_type not in self._migrations:
                self._migrations[artifact_type] = []

    def get_current_version(
        self,
        artifact_type: str,
    ) -> SchemaVersion | None:
        """Get the current schema version for an artifact type.

        Args:
            artifact_type: Type of artifact.

        Returns:
            Current version, or None if not registered.
        """
        return self._current_versions.get(artifact_type)

    def register_migration(
        self,
        artifact_type: str,
        from_version: str | SchemaVersion,
        to_version: str | SchemaVersion,
        migrate: MigrationFunc,
        rollback: MigrationFunc | None = None,
        description: str = "",
    ) -> Migration:
        """Register a migration between versions.

        Args:
            artifact_type: Type of artifact.
            from_version: Source version.
            to_version: Target version.
            migrate: Migration function.
            rollback: Optional rollback function.
            description: Human-readable description.

        Returns:
            The registered Migration.
        """
        with self._lock:
            if isinstance(from_version, str):
                from_version = SchemaVersion.parse(from_version)
            if isinstance(to_version, str):
                to_version = SchemaVersion.parse(to_version)

            migration = Migration(
                from_version=from_version,
                to_version=to_version,
                artifact_type=artifact_type,
                migrate=migrate,
                rollback=rollback,
                description=description,
            )

            if artifact_type not in self._migrations:
                self._migrations[artifact_type] = []
                # Also register the type if not already known
                if artifact_type not in self._current_versions:
                    self._current_versions[artifact_type] = to_version

            self._migrations[artifact_type].append(migration)
            # Sort by version for easier path finding
            self._migrations[artifact_type].sort(
                key=lambda m: (m.from_version, m.to_version)
            )

            return migration

    def get_migration_path(
        self,
        artifact_type: str,
        from_version: str | SchemaVersion,
        to_version: str | SchemaVersion,
    ) -> list[Migration]:
        """Get the migration path between versions.

        Args:
            artifact_type: Type of artifact.
            from_version: Source version.
            to_version: Target version.

        Returns:
            List of migrations to apply in order.
        """
        with self._lock:
            if isinstance(from_version, str):
                from_version = SchemaVersion.parse(from_version)
            if isinstance(to_version, str):
                to_version = SchemaVersion.parse(to_version)

            if from_version == to_version:
                return []

            migrations = self._migrations.get(artifact_type, [])
            if not migrations:
                return []

            # Build graph and find path
            return self._find_migration_path(
                migrations, from_version, to_version
            )

    def _find_migration_path(
        self,
        migrations: list[Migration],
        from_version: SchemaVersion,
        to_version: SchemaVersion,
    ) -> list[Migration]:
        """Find path through migration graph using BFS.

        Args:
            migrations: Available migrations.
            from_version: Starting version.
            to_version: Target version.

        Returns:
            List of migrations to apply, or empty if no path.
        """
        # Build adjacency list
        graph: dict[SchemaVersion, list[Migration]] = {}
        for m in migrations:
            if m.from_version not in graph:
                graph[m.from_version] = []
            graph[m.from_version].append(m)

        # BFS to find shortest path
        from collections import deque

        queue: deque[tuple[SchemaVersion, list[Migration]]] = deque()
        queue.append((from_version, []))
        visited: set[SchemaVersion] = set()

        while queue:
            current, path = queue.popleft()

            if current == to_version:
                return path

            if current in visited:
                continue
            visited.add(current)

            for migration in graph.get(current, []):
                if migration.to_version not in visited:
                    queue.append((migration.to_version, path + [migration]))

        return []

    def migrate(
        self,
        artifact_data: dict[str, Any],
        artifact_type: str,
        from_version: str | SchemaVersion,
        to_version: str | SchemaVersion | None = None,
    ) -> dict[str, Any]:
        """Migrate artifact data between versions.

        Args:
            artifact_data: Artifact data to migrate.
            artifact_type: Type of artifact.
            from_version: Current version of the data.
            to_version: Target version (defaults to current).

        Returns:
            Migrated artifact data.

        Raises:
            MigrationError: If migration fails.
        """
        with self._lock:
            if isinstance(from_version, str):
                from_version = SchemaVersion.parse(from_version)
            if to_version is None:
                to_version = self._current_versions.get(artifact_type)
                if to_version is None:
                    return artifact_data
            elif isinstance(to_version, str):
                to_version = SchemaVersion.parse(to_version)

            if from_version == to_version:
                return artifact_data

            path = self.get_migration_path(artifact_type, from_version, to_version)
            if not path and from_version != to_version:
                raise MigrationError(
                    from_version=str(from_version),
                    to_version=str(to_version),
                    artifact_type=artifact_type,
                    message="No migration path found",
                )

            result = artifact_data.copy()
            for migration in path:
                try:
                    result = migration.migrate(
                        result,
                        str(migration.from_version),
                        str(migration.to_version),
                    )
                    # Update version in result
                    if "artifact_version" in result:
                        result["artifact_version"] = str(migration.to_version)
                except Exception as e:
                    raise MigrationError(
                        from_version=str(migration.from_version),
                        to_version=str(migration.to_version),
                        artifact_type=artifact_type,
                        message=str(e),
                    ) from e

            return result

    def validate_compatibility(
        self,
        artifact_data: dict[str, Any],
        artifact_type: str,
        target_version: str | SchemaVersion | None = None,
    ) -> ValidationResult:
        """Validate artifact compatibility with target version.

        Args:
            artifact_data: Artifact data to validate.
            artifact_type: Type of artifact.
            target_version: Version to validate against (defaults to current).

        Returns:
            ValidationResult with compatibility information.
        """
        with self._lock:
            # Get artifact version
            artifact_version_str = artifact_data.get("artifact_version", "1.0")
            try:
                artifact_version = SchemaVersion.parse(artifact_version_str)
            except VersionParseError as e:
                return ValidationResult(
                    compatible=False,
                    level=CompatibilityLevel.BREAKING,
                    issues=[f"Invalid artifact version: {e}"],
                )

            # Get target version
            if target_version is None:
                target_version = self._current_versions.get(artifact_type)
                if target_version is None:
                    return ValidationResult(
                        compatible=True,
                        level=CompatibilityLevel.FULL,
                        warnings=[f"Unknown artifact type: {artifact_type}"],
                    )
            elif isinstance(target_version, str):
                target_version = SchemaVersion.parse(target_version)

            # Check compatibility
            level = artifact_version.is_compatible_with(target_version)
            issues: list[str] = []
            warnings: list[str] = []

            if level == CompatibilityLevel.BREAKING:
                issues.append(
                    f"Major version mismatch: {artifact_version} vs {target_version}"
                )

                # Check if migration path exists
                path = self.get_migration_path(
                    artifact_type, artifact_version, target_version
                )
                if path:
                    warnings.append(
                        f"Migration path available: {len(path)} step(s)"
                    )

            elif level == CompatibilityLevel.FORWARD:
                warnings.append(
                    f"Artifact version {artifact_version} is older than "
                    f"current {target_version}"
                )

            elif level == CompatibilityLevel.BACKWARD:
                warnings.append(
                    f"Artifact version {artifact_version} is newer than "
                    f"current {target_version}"
                )

            return ValidationResult(
                compatible=(level != CompatibilityLevel.BREAKING),
                level=level,
                issues=issues,
                warnings=warnings,
            )

    def needs_migration(
        self,
        artifact_data: dict[str, Any],
        artifact_type: str,
    ) -> bool:
        """Check if artifact needs migration.

        Args:
            artifact_data: Artifact data to check.
            artifact_type: Type of artifact.

        Returns:
            True if migration is needed.
        """
        with self._lock:
            artifact_version_str = artifact_data.get("artifact_version", "1.0")
            try:
                artifact_version = SchemaVersion.parse(artifact_version_str)
            except VersionParseError:
                return True

            current = self._current_versions.get(artifact_type)
            if current is None:
                return False

            return artifact_version != current

    def get_registered_types(self) -> list[str]:
        """Get all registered artifact types.

        Returns:
            List of artifact type names.
        """
        with self._lock:
            return list(self._current_versions.keys())

    def get_migration_count(self, artifact_type: str) -> int:
        """Get number of registered migrations for a type.

        Args:
            artifact_type: Type of artifact.

        Returns:
            Number of migrations registered.
        """
        with self._lock:
            return len(self._migrations.get(artifact_type, []))

    def to_dict(self) -> dict[str, Any]:
        """Export manager state as dictionary.

        Returns:
            Dict with all version and migration info.
        """
        with self._lock:
            return {
                "versions": {
                    t: str(v) for t, v in self._current_versions.items()
                },
                "migrations": {
                    t: [
                        {
                            "from": str(m.from_version),
                            "to": str(m.to_version),
                            "description": m.description,
                        }
                        for m in migrations
                    ]
                    for t, migrations in self._migrations.items()
                    if migrations
                },
            }


# Global schema version manager instance
_schema_manager: SchemaVersionManager | None = None


def get_schema_version_manager() -> SchemaVersionManager:
    """Get the global schema version manager instance.

    Returns:
        The global SchemaVersionManager instance.
    """
    global _schema_manager
    if _schema_manager is None:
        _schema_manager = SchemaVersionManager()
    return _schema_manager


def reset_schema_version_manager() -> None:
    """Reset the global schema version manager (useful for testing)."""
    global _schema_manager
    _schema_manager = None
