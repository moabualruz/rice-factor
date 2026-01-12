"""Google Cloud Storage artifact storage adapter.

This module implements artifact persistence using Google Cloud Storage,
storing artifacts as JSON objects in a structured path layout.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.failures.errors import (
    ArtifactNotFoundError,
    ArtifactValidationError,
)

if TYPE_CHECKING:
    from google.cloud.storage import Bucket, Client

# Map artifact type to prefix
TYPE_PREFIX_MAP: dict[ArtifactType, str] = {
    ArtifactType.PROJECT_PLAN: "project_plans",
    ArtifactType.ARCHITECTURE_PLAN: "architecture_plans",
    ArtifactType.SCAFFOLD_PLAN: "scaffold_plans",
    ArtifactType.TEST_PLAN: "test_plans",
    ArtifactType.IMPLEMENTATION_PLAN: "implementation_plans",
    ArtifactType.REFACTOR_PLAN: "refactor_plans",
    ArtifactType.VALIDATION_RESULT: "validation_results",
    ArtifactType.RECONCILIATION_PLAN: "reconciliation_plans",
}


class GCSStorageAdapter:
    """Google Cloud Storage adapter for artifacts.

    Stores artifacts as JSON objects in a GCS bucket with structured paths:
    - <prefix>/<type_prefix>/<uuid>.json

    Attributes:
        bucket_name: GCS bucket name.
        prefix: Path prefix for all artifacts.
    """

    def __init__(
        self,
        bucket_name: str,
        prefix: str = "artifacts",
        project: str | None = None,
        credentials_path: str | None = None,
        client: Client | None = None,
    ) -> None:
        """Initialize the GCS storage adapter.

        Args:
            bucket_name: GCS bucket name.
            prefix: Path prefix for all artifacts.
            project: GCP project ID (optional).
            credentials_path: Path to service account credentials JSON.
            client: Pre-configured GCS client (for testing).
        """
        self._bucket_name = bucket_name
        self._prefix = prefix.rstrip("/")
        self._project = project
        self._credentials_path = credentials_path
        self._client = client
        self._bucket: Bucket | None = None
        self._validator: Any = None  # Lazy loaded

    @property
    def bucket_name(self) -> str:
        """Get the GCS bucket name."""
        return self._bucket_name

    @property
    def prefix(self) -> str:
        """Get the path prefix."""
        return self._prefix

    def _get_client(self) -> Client:
        """Get or create the GCS client.

        Returns:
            Configured GCS client.
        """
        if self._client is not None:
            return self._client

        try:
            from google.cloud import storage
            from google.oauth2 import service_account
        except ImportError as e:
            raise ImportError(
                "google-cloud-storage is required for GCS storage. "
                "Install with: pip install google-cloud-storage"
            ) from e

        if self._credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                self._credentials_path
            )
            self._client = storage.Client(
                project=self._project,
                credentials=credentials,
            )
        else:
            self._client = storage.Client(project=self._project)

        return self._client

    def _get_bucket(self) -> Bucket:
        """Get the GCS bucket.

        Returns:
            GCS Bucket object.
        """
        if self._bucket is not None:
            return self._bucket

        client = self._get_client()
        self._bucket = client.bucket(self._bucket_name)
        return self._bucket

    def _get_validator(self) -> Any:
        """Get or create the artifact validator."""
        if self._validator is None:
            from rice_factor.adapters.validators import ArtifactValidator

            self._validator = ArtifactValidator()
        return self._validator

    def save(
        self,
        artifact: ArtifactEnvelope[BaseModel],
        path: Path | None = None,
    ) -> Path:
        """Save an artifact to GCS.

        Args:
            artifact: The artifact envelope to save.
            path: Optional explicit path (used as GCS blob name).

        Returns:
            The path where the artifact was saved.

        Raises:
            IOError: If the artifact cannot be saved.
        """
        if path is None:
            path = self.get_path_for_artifact(artifact.id, artifact.artifact_type)

        blob_name = str(path)
        data = self._serialize_artifact(artifact)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        bucket = self._get_bucket()
        try:
            blob = bucket.blob(blob_name)
            blob.upload_from_string(
                json_str,
                content_type="application/json",
            )
        except Exception as e:
            raise IOError(f"Failed to save artifact to GCS: {e}") from e

        return path

    def load(self, path: Path) -> ArtifactEnvelope[BaseModel]:
        """Load an artifact from GCS.

        Args:
            path: GCS blob name (as Path).

        Returns:
            The loaded and validated artifact envelope.

        Raises:
            ArtifactNotFoundError: If the blob doesn't exist.
            ArtifactValidationError: If the artifact is invalid.
        """
        blob_name = str(path)
        bucket = self._get_bucket()
        blob = bucket.blob(blob_name)

        try:
            if not blob.exists():
                raise ArtifactNotFoundError(f"Artifact not found: {path}")
            content = blob.download_as_text()
        except ArtifactNotFoundError:
            raise
        except Exception as e:
            if "Not Found" in str(e) or "404" in str(e):
                raise ArtifactNotFoundError(f"Artifact not found: {path}")
            raise IOError(f"Failed to load artifact from GCS: {e}") from e

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ArtifactValidationError(
                f"Invalid JSON in artifact: {e}",
                field_path="$",
            ) from e

        return self._get_validator().validate(data)

    def load_by_id(
        self,
        artifact_id: UUID,
        artifact_type: ArtifactType | None = None,
    ) -> ArtifactEnvelope[BaseModel]:
        """Load an artifact by its UUID.

        Args:
            artifact_id: The UUID of the artifact.
            artifact_type: Optional type hint to narrow the search.

        Returns:
            The loaded and validated artifact envelope.

        Raises:
            ArtifactNotFoundError: If the artifact doesn't exist.
        """
        if artifact_type is not None:
            path = self.get_path_for_artifact(artifact_id, artifact_type)
            return self.load(path)

        # Search all type prefixes
        for atype in ArtifactType:
            path = self.get_path_for_artifact(artifact_id, atype)
            try:
                return self.load(path)
            except ArtifactNotFoundError:
                continue

        raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")

    def exists(
        self,
        artifact_id: UUID,
        artifact_type: ArtifactType | None = None,
    ) -> bool:
        """Check if an artifact exists.

        Args:
            artifact_id: The UUID to check.
            artifact_type: Optional type hint to narrow the search.

        Returns:
            True if the artifact exists, False otherwise.
        """
        bucket = self._get_bucket()

        def check_blob(blob_name: str) -> bool:
            try:
                blob = bucket.blob(blob_name)
                return blob.exists()
            except Exception:
                return False

        if artifact_type is not None:
            path = self.get_path_for_artifact(artifact_id, artifact_type)
            return check_blob(str(path))

        # Search all type prefixes
        for atype in ArtifactType:
            path = self.get_path_for_artifact(artifact_id, atype)
            if check_blob(str(path)):
                return True

        return False

    def delete(
        self,
        artifact_id: UUID,
        artifact_type: ArtifactType | None = None,
    ) -> None:
        """Delete an artifact from GCS.

        Args:
            artifact_id: The UUID of the artifact to delete.
            artifact_type: Optional type hint to narrow the search.

        Raises:
            ArtifactNotFoundError: If the artifact doesn't exist.
        """
        blob_name: str | None = None

        if artifact_type is not None:
            path = self.get_path_for_artifact(artifact_id, artifact_type)
            blob_name = str(path)
            if not self.exists(artifact_id, artifact_type):
                raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")
        else:
            # Search all type prefixes
            for atype in ArtifactType:
                path = self.get_path_for_artifact(artifact_id, atype)
                if self.exists(artifact_id, atype):
                    blob_name = str(path)
                    break

            if blob_name is None:
                raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")

        bucket = self._get_bucket()
        try:
            blob = bucket.blob(blob_name)
            blob.delete()
        except Exception as e:
            raise IOError(f"Failed to delete artifact from GCS: {e}") from e

    def list_by_type(
        self,
        artifact_type: ArtifactType,
    ) -> list[ArtifactEnvelope[BaseModel]]:
        """List all artifacts of a specific type.

        Args:
            artifact_type: The type of artifacts to list.

        Returns:
            List of artifact envelopes of the specified type.
        """
        prefix = self._get_type_prefix(artifact_type)
        bucket = self._get_bucket()

        artifacts: list[ArtifactEnvelope[BaseModel]] = []

        try:
            blobs = bucket.list_blobs(prefix=prefix)
            for blob in blobs:
                if blob.name.endswith(".json"):
                    try:
                        artifact = self.load(Path(blob.name))
                        artifacts.append(artifact)
                    except (ArtifactValidationError, ArtifactNotFoundError):
                        continue
        except Exception:
            pass  # Return empty list on error

        return artifacts

    def get_path_for_artifact(
        self,
        artifact_id: UUID,
        artifact_type: ArtifactType,
    ) -> Path:
        """Get the GCS blob path for an artifact.

        Args:
            artifact_id: The artifact's UUID.
            artifact_type: The artifact's type.

        Returns:
            The GCS blob path as a Path object.
        """
        type_prefix = self._get_type_prefix(artifact_type)
        return Path(f"{type_prefix}/{artifact_id}.json")

    def _get_type_prefix(self, artifact_type: ArtifactType) -> str:
        """Get the path prefix for a specific artifact type."""
        type_name = TYPE_PREFIX_MAP.get(artifact_type)
        if type_name is None:
            type_name = artifact_type.value.lower()
        return f"{self._prefix}/{type_name}"

    def _serialize_artifact(
        self,
        artifact: ArtifactEnvelope[BaseModel],
    ) -> dict[str, Any]:
        """Serialize an artifact to a dictionary for JSON storage."""
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

    def is_available(self) -> bool:
        """Check if GCS is accessible.

        Returns:
            True if GCS bucket is accessible.
        """
        try:
            bucket = self._get_bucket()
            return bucket.exists()
        except Exception:
            return False
