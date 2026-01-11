"""Filesystem-based artifact storage adapter.

This module implements artifact persistence using the local filesystem,
storing artifacts as JSON files in a structured directory layout.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from rice_factor.adapters.validators import ArtifactValidator
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.failures.errors import (
    ArtifactNotFoundError,
    ArtifactValidationError,
)

# Map artifact type to directory name
TYPE_DIR_MAP: dict[ArtifactType, str] = {
    ArtifactType.PROJECT_PLAN: "project_plans",
    ArtifactType.ARCHITECTURE_PLAN: "architecture_plans",
    ArtifactType.SCAFFOLD_PLAN: "scaffold_plans",
    ArtifactType.TEST_PLAN: "test_plans",
    ArtifactType.IMPLEMENTATION_PLAN: "implementation_plans",
    ArtifactType.REFACTOR_PLAN: "refactor_plans",
    ArtifactType.VALIDATION_RESULT: "validation_results",
    ArtifactType.RECONCILIATION_PLAN: "reconciliation_plans",
}


class FilesystemStorageAdapter:
    """Filesystem-based storage adapter for artifacts.

    Stores artifacts as JSON files in a structured directory layout:
    - artifacts/<type_dir>/<uuid>.json
    - artifacts/_meta/index.json

    Attributes:
        artifacts_dir: Root directory for artifact storage.
    """

    def __init__(
        self,
        artifacts_dir: Path,
        validator: ArtifactValidator | None = None,
    ) -> None:
        """Initialize the storage adapter.

        Args:
            artifacts_dir: Root directory for artifact storage.
            validator: Optional validator instance. Creates one if not provided.
        """
        self._artifacts_dir = artifacts_dir
        self._validator = validator or ArtifactValidator()

    @property
    def artifacts_dir(self) -> Path:
        """Get the artifacts root directory."""
        return self._artifacts_dir

    def save(self, artifact: ArtifactEnvelope[BaseModel], path: Path | None = None) -> Path:
        """Save an artifact to the filesystem.

        Args:
            artifact: The artifact envelope to save.
            path: Optional explicit path. If not provided, uses default path.

        Returns:
            The path where the artifact was saved.

        Raises:
            IOError: If the artifact cannot be saved.
        """
        if path is None:
            path = self.get_path_for_artifact(artifact.id, artifact.artifact_type)

        # Create parent directories
        path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize to JSON
        data = self._serialize_artifact(artifact)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        # Write atomically by writing to temp then renaming
        path.write_text(json_str, encoding="utf-8")

        return path

    def load(self, path: Path) -> ArtifactEnvelope[BaseModel]:
        """Load an artifact from the filesystem.

        Args:
            path: Path to the artifact JSON file.

        Returns:
            The loaded and validated artifact envelope.

        Raises:
            ArtifactNotFoundError: If the file doesn't exist.
            ArtifactValidationError: If the artifact is invalid.
        """
        if not path.exists():
            raise ArtifactNotFoundError(f"Artifact not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ArtifactValidationError(
                f"Invalid JSON in artifact file: {e}",
                field_path="$",
            ) from e

        return self._validator.validate(data)

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
        if artifact_type is not None:
            path = self.get_path_for_artifact(artifact_id, artifact_type)
            if path.exists():
                return self.load(path)
            raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")

        # Search all type directories
        for atype in ArtifactType:
            path = self.get_path_for_artifact(artifact_id, atype)
            if path.exists():
                return self.load(path)

        raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")

    def exists(self, artifact_id: UUID, artifact_type: ArtifactType | None = None) -> bool:
        """Check if an artifact exists.

        Args:
            artifact_id: The UUID to check.
            artifact_type: Optional type hint to narrow the search.

        Returns:
            True if the artifact exists, False otherwise.
        """
        if artifact_type is not None:
            path = self.get_path_for_artifact(artifact_id, artifact_type)
            return path.exists()

        # Search all type directories
        for atype in ArtifactType:
            path = self.get_path_for_artifact(artifact_id, atype)
            if path.exists():
                return True

        return False

    def delete(self, artifact_id: UUID, artifact_type: ArtifactType | None = None) -> None:
        """Delete an artifact from storage.

        Args:
            artifact_id: The UUID of the artifact to delete.
            artifact_type: Optional type hint to narrow the search.

        Raises:
            ArtifactNotFoundError: If the artifact doesn't exist.
        """
        path: Path | None = None

        if artifact_type is not None:
            path = self.get_path_for_artifact(artifact_id, artifact_type)
            if not path.exists():
                raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")
        else:
            # Search all type directories
            for atype in ArtifactType:
                candidate = self.get_path_for_artifact(artifact_id, atype)
                if candidate.exists():
                    path = candidate
                    break

            if path is None:
                raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")

        path.unlink()

    def list_by_type(
        self, artifact_type: ArtifactType
    ) -> list[ArtifactEnvelope[BaseModel]]:
        """List all artifacts of a specific type.

        Args:
            artifact_type: The type of artifacts to list.

        Returns:
            List of artifact envelopes of the specified type.
        """
        type_dir = self._get_type_dir(artifact_type)
        if not type_dir.exists():
            return []

        artifacts: list[ArtifactEnvelope[BaseModel]] = []
        for path in type_dir.glob("*.json"):
            try:
                artifact = self.load(path)
                artifacts.append(artifact)
            except (ArtifactValidationError, ArtifactNotFoundError):
                # Skip invalid artifacts
                continue

        return artifacts

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
        type_dir = self._get_type_dir(artifact_type)
        return type_dir / f"{artifact_id}.json"

    def _get_type_dir(self, artifact_type: ArtifactType) -> Path:
        """Get the directory for a specific artifact type."""
        dir_name = TYPE_DIR_MAP.get(artifact_type)
        if dir_name is None:
            dir_name = artifact_type.value.lower()
        return self._artifacts_dir / dir_name

    def _serialize_artifact(self, artifact: ArtifactEnvelope[BaseModel]) -> dict[str, Any]:
        """Serialize an artifact to a dictionary for JSON storage.

        Handles special types like UUID and datetime.
        """
        data = artifact.model_dump(mode="json")

        # Ensure UUID is serialized as string
        if isinstance(data.get("id"), UUID):
            data["id"] = str(data["id"])

        # Ensure datetime is ISO format string
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()

        # Ensure depends_on UUIDs are strings
        if "depends_on" in data:
            data["depends_on"] = [
                str(dep) if isinstance(dep, UUID) else dep
                for dep in data["depends_on"]
            ]

        return data
