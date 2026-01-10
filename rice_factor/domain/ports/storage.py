"""Storage port for artifact persistence.

This module defines the interface for artifact storage, following
the hexagonal architecture pattern.
"""

from pathlib import Path
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope


class StoragePort(Protocol):
    """Protocol for artifact storage operations.

    Implementations handle loading and saving artifacts to a storage backend
    (filesystem, database, etc.).
    """

    def save(self, artifact: ArtifactEnvelope[BaseModel], path: Path) -> None:
        """Save an artifact to storage.

        Args:
            artifact: The artifact envelope to save.
            path: Path where the artifact should be saved.

        Raises:
            IOError: If the artifact cannot be saved.
        """
        ...

    def load(self, path: Path) -> ArtifactEnvelope[BaseModel]:
        """Load an artifact from storage.

        Args:
            path: Path to the artifact file.

        Returns:
            The loaded and validated artifact envelope.

        Raises:
            ArtifactNotFoundError: If the artifact doesn't exist.
            ArtifactValidationError: If the artifact is invalid.
        """
        ...

    def load_by_id(
        self, artifact_id: UUID, artifact_type: ArtifactType | None = None
    ) -> ArtifactEnvelope[BaseModel]:
        """Load an artifact by its UUID.

        Args:
            artifact_id: The UUID of the artifact.
            artifact_type: Optional type hint to narrow the search.

        Returns:
            The loaded and validated artifact envelope.

        Raises:
            ArtifactNotFoundError: If the artifact doesn't exist.
            ArtifactValidationError: If the artifact is invalid.
        """
        ...

    def exists(self, artifact_id: UUID) -> bool:
        """Check if an artifact exists.

        Args:
            artifact_id: The UUID to check.

        Returns:
            True if the artifact exists, False otherwise.
        """
        ...

    def delete(self, artifact_id: UUID) -> None:
        """Delete an artifact from storage.

        Args:
            artifact_id: The UUID of the artifact to delete.

        Raises:
            ArtifactNotFoundError: If the artifact doesn't exist.
        """
        ...

    def list_by_type(
        self, artifact_type: ArtifactType
    ) -> list[ArtifactEnvelope[BaseModel]]:
        """List all artifacts of a specific type.

        Args:
            artifact_type: The type of artifacts to list.

        Returns:
            List of artifact envelopes of the specified type.
        """
        ...

    def get_path_for_artifact(
        self, artifact_id: UUID, artifact_type: ArtifactType
    ) -> Path:
        """Get the storage path for an artifact.

        Args:
            artifact_id: The artifact's UUID.
            artifact_type: The artifact's type.

        Returns:
            The path where the artifact is/should be stored.
        """
        ...
