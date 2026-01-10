"""Artifact resolver for locating artifacts by path or UUID.

This module provides the ArtifactResolver service for resolving artifact
references to actual artifacts, supporting both file paths and UUIDs.
"""

from pathlib import Path
from uuid import UUID

from pydantic import BaseModel

from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.failures.errors import ArtifactNotFoundError


class ArtifactResolver:
    """Service for resolving artifact references.

    Resolves artifact identifiers (file paths or UUIDs) to actual artifacts.
    Supports both explicit file paths and UUID lookups across all artifact types.

    Attributes:
        storage: Storage adapter for loading artifacts.
    """

    def __init__(self, storage: FilesystemStorageAdapter) -> None:
        """Initialize the resolver.

        Args:
            storage: Storage adapter for artifact operations.
        """
        self._storage = storage

    @property
    def storage(self) -> FilesystemStorageAdapter:
        """Get the storage adapter."""
        return self._storage

    def resolve(self, identifier: str) -> ArtifactEnvelope[BaseModel]:
        """Resolve an artifact by path or UUID.

        Attempts to interpret the identifier as:
        1. A UUID (tries to load by ID)
        2. A file path (loads directly)

        Args:
            identifier: Either a UUID string or file path.

        Returns:
            The resolved artifact envelope.

        Raises:
            ArtifactNotFoundError: If the artifact cannot be found.
        """
        # First, try to parse as UUID
        try:
            artifact_id = UUID(identifier)
            return self.resolve_by_id(artifact_id)
        except ValueError:
            pass

        # Try as file path
        path = Path(identifier)
        if path.exists():
            return self.resolve_by_path(path)

        # Try relative to artifacts directory
        relative_path = self._storage.artifacts_dir / identifier
        if relative_path.exists():
            return self.resolve_by_path(relative_path)

        raise ArtifactNotFoundError(
            f"Could not resolve artifact: '{identifier}'. "
            "Provide a valid UUID or file path."
        )

    def resolve_by_path(self, path: Path) -> ArtifactEnvelope[BaseModel]:
        """Load an artifact by file path.

        Args:
            path: Path to the artifact JSON file.

        Returns:
            The loaded artifact envelope.

        Raises:
            ArtifactNotFoundError: If the file doesn't exist.
        """
        if not path.exists():
            raise ArtifactNotFoundError(f"Artifact file not found: {path}")

        return self._storage.load(path)

    def resolve_by_id(
        self,
        artifact_id: UUID,
        artifact_type: ArtifactType | None = None,
    ) -> ArtifactEnvelope[BaseModel]:
        """Load an artifact by UUID.

        Searches across all artifact type directories if type is not specified.

        Args:
            artifact_id: The UUID of the artifact.
            artifact_type: Optional type hint to narrow the search.

        Returns:
            The loaded artifact envelope.

        Raises:
            ArtifactNotFoundError: If the artifact cannot be found.
        """
        return self._storage.load_by_id(artifact_id, artifact_type)

    def resolve_latest_by_type(
        self,
        artifact_type: ArtifactType,
    ) -> ArtifactEnvelope[BaseModel] | None:
        """Get the most recent artifact of a specific type.

        Args:
            artifact_type: The type of artifact to find.

        Returns:
            The most recent artifact, or None if none exist.
        """
        artifacts = self._storage.list_by_type(artifact_type)
        if not artifacts:
            return None

        # Sort by created_at and return the most recent
        artifacts.sort(key=lambda a: a.created_at, reverse=True)
        return artifacts[0]

    def list_by_type(
        self,
        artifact_type: ArtifactType,
    ) -> list[ArtifactEnvelope[BaseModel]]:
        """List all artifacts of a specific type.

        Args:
            artifact_type: The type of artifacts to list.

        Returns:
            List of artifact envelopes.
        """
        return self._storage.list_by_type(artifact_type)

    def exists(self, identifier: str) -> bool:
        """Check if an artifact exists.

        Args:
            identifier: Either a UUID string or file path.

        Returns:
            True if the artifact exists.
        """
        try:
            self.resolve(identifier)
            return True
        except ArtifactNotFoundError:
            return False
