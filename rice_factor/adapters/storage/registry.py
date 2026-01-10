"""Artifact registry for tracking all artifacts.

This module provides the registry that maintains an index of all artifacts
and enables quick lookup by ID, type, or status.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.registry import RegistryEntry
from rice_factor.domain.failures.errors import ArtifactDependencyError


class ArtifactRegistry:
    """Registry for tracking all artifacts in the system.

    Maintains an index of all artifacts in `artifacts/_meta/index.json`
    and enables quick lookup by ID, type, or status.

    Attributes:
        index_file: Path to the index JSON file.
    """

    def __init__(self, artifacts_dir: Path) -> None:
        """Initialize the artifact registry.

        Args:
            artifacts_dir: Root directory for artifacts.
        """
        self._artifacts_dir = artifacts_dir
        self._meta_dir = artifacts_dir / "_meta"
        self._index_file = self._meta_dir / "index.json"
        self._entries: dict[UUID, RegistryEntry] = {}

        # Load existing index
        self._load()

    @property
    def index_file(self) -> Path:
        """Get the path to the index file."""
        return self._index_file

    def register(
        self,
        artifact: ArtifactEnvelope[BaseModel],
        path: str,
    ) -> RegistryEntry:
        """Register an artifact in the registry.

        Args:
            artifact: The artifact envelope to register.
            path: Relative path to the artifact file.

        Returns:
            The created RegistryEntry.
        """
        entry = RegistryEntry(
            id=artifact.id,
            artifact_type=artifact.artifact_type,
            path=path,
            status=artifact.status,
            created_at=artifact.created_at,
        )
        self._entries[artifact.id] = entry
        self._save()
        return entry

    def unregister(self, artifact_id: UUID) -> bool:
        """Remove an artifact from the registry.

        Args:
            artifact_id: UUID of the artifact to remove.

        Returns:
            True if removed, False if not found.
        """
        if artifact_id in self._entries:
            del self._entries[artifact_id]
            self._save()
            return True
        return False

    def update_status(self, artifact_id: UUID, status: ArtifactStatus) -> bool:
        """Update the status of an artifact in the registry.

        Args:
            artifact_id: UUID of the artifact to update.
            status: New status value.

        Returns:
            True if updated, False if not found.
        """
        if artifact_id in self._entries:
            entry = self._entries[artifact_id]
            updated = RegistryEntry(
                id=entry.id,
                artifact_type=entry.artifact_type,
                path=entry.path,
                status=status,
                created_at=entry.created_at,
            )
            self._entries[artifact_id] = updated
            self._save()
            return True
        return False

    def lookup(self, artifact_id: UUID) -> RegistryEntry | None:
        """Look up an artifact by ID.

        Args:
            artifact_id: UUID of the artifact.

        Returns:
            The RegistryEntry, or None if not found.
        """
        return self._entries.get(artifact_id)

    def list_by_type(self, artifact_type: ArtifactType) -> list[RegistryEntry]:
        """List all artifacts of a given type.

        Args:
            artifact_type: The type to filter by.

        Returns:
            List of matching RegistryEntry objects.
        """
        return [
            entry
            for entry in self._entries.values()
            if entry.artifact_type == artifact_type
        ]

    def list_by_status(self, status: ArtifactStatus) -> list[RegistryEntry]:
        """List all artifacts with a given status.

        Args:
            status: The status to filter by.

        Returns:
            List of matching RegistryEntry objects.
        """
        return [entry for entry in self._entries.values() if entry.status == status]

    def list_all(self) -> list[RegistryEntry]:
        """List all registered artifacts.

        Returns:
            List of all RegistryEntry objects.
        """
        return list(self._entries.values())

    def validate_dependencies(
        self, artifact: ArtifactEnvelope[BaseModel]
    ) -> None:
        """Validate that all dependencies of an artifact are satisfied.

        Checks that:
        1. All dependency UUIDs exist in the registry
        2. All dependencies are APPROVED or LOCKED (not DRAFT)

        Args:
            artifact: The artifact to validate dependencies for.

        Raises:
            ArtifactDependencyError: If any dependency is missing or in draft status.
        """
        for dep_id in artifact.depends_on:
            entry = self.lookup(dep_id)

            if entry is None:
                raise ArtifactDependencyError(
                    f"Dependency '{dep_id}' not found in registry. "
                    "All dependencies must exist before an artifact can be saved."
                )

            if entry.status == ArtifactStatus.DRAFT:
                raise ArtifactDependencyError(
                    f"Dependency '{dep_id}' is still in DRAFT status. "
                    "All dependencies must be APPROVED or LOCKED."
                )

    def _load(self) -> None:
        """Load registry from the index file."""
        if not self._index_file.exists():
            self._entries = {}
            return

        try:
            content = self._index_file.read_text(encoding="utf-8")
            data = json.loads(content)

            self._entries = {}
            for item in data.get("artifacts", []):
                entry = RegistryEntry(
                    id=UUID(item["id"]),
                    artifact_type=ArtifactType(item["artifact_type"]),
                    path=item["path"],
                    status=ArtifactStatus(item["status"]),
                    created_at=datetime.fromisoformat(item["created_at"]),
                )
                self._entries[entry.id] = entry
        except (json.JSONDecodeError, KeyError, ValueError):
            # If file is corrupted, start fresh
            self._entries = {}

    def _save(self) -> None:
        """Save registry to the index file."""
        # Ensure meta directory exists
        self._meta_dir.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "artifacts": [
                {
                    "id": str(entry.id),
                    "artifact_type": entry.artifact_type.value,
                    "path": entry.path,
                    "status": entry.status.value,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in self._entries.values()
            ]
        }

        json_str = json.dumps(data, indent=2)
        self._index_file.write_text(json_str, encoding="utf-8")
