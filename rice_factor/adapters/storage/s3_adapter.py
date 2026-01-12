"""S3-based artifact storage adapter.

This module implements artifact persistence using Amazon S3,
storing artifacts as JSON objects in a structured key layout.
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
    from mypy_boto3_s3 import S3Client

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


class S3StorageAdapter:
    """S3-based storage adapter for artifacts.

    Stores artifacts as JSON objects in an S3 bucket with structured keys:
    - <prefix>/<type_prefix>/<uuid>.json

    Attributes:
        bucket: S3 bucket name.
        prefix: Key prefix for all artifacts.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "artifacts",
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        client: S3Client | None = None,
    ) -> None:
        """Initialize the S3 storage adapter.

        Args:
            bucket: S3 bucket name.
            prefix: Key prefix for all artifacts.
            region: AWS region (optional).
            endpoint_url: Custom endpoint URL for S3-compatible services.
            access_key_id: AWS access key ID (optional, uses default chain).
            secret_access_key: AWS secret access key (optional).
            client: Pre-configured S3 client (for testing).
        """
        self._bucket = bucket
        self._prefix = prefix.rstrip("/")
        self._region = region
        self._endpoint_url = endpoint_url
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._client = client
        self._validator: Any = None  # Lazy loaded

    @property
    def bucket(self) -> str:
        """Get the S3 bucket name."""
        return self._bucket

    @property
    def prefix(self) -> str:
        """Get the key prefix."""
        return self._prefix

    def _get_client(self) -> S3Client:
        """Get or create the S3 client.

        Returns:
            Configured S3 client.
        """
        if self._client is not None:
            return self._client

        try:
            import boto3
        except ImportError as e:
            raise ImportError(
                "boto3 is required for S3 storage. "
                "Install with: pip install boto3"
            ) from e

        kwargs: dict[str, Any] = {}
        if self._region:
            kwargs["region_name"] = self._region
        if self._endpoint_url:
            kwargs["endpoint_url"] = self._endpoint_url
        if self._access_key_id and self._secret_access_key:
            kwargs["aws_access_key_id"] = self._access_key_id
            kwargs["aws_secret_access_key"] = self._secret_access_key

        self._client = boto3.client("s3", **kwargs)
        return self._client

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
        """Save an artifact to S3.

        Args:
            artifact: The artifact envelope to save.
            path: Optional explicit path (used as S3 key).

        Returns:
            The path (S3 key) where the artifact was saved.

        Raises:
            IOError: If the artifact cannot be saved.
        """
        if path is None:
            path = self.get_path_for_artifact(artifact.id, artifact.artifact_type)

        key = str(path)
        data = self._serialize_artifact(artifact)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        client = self._get_client()
        try:
            client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=json_str.encode("utf-8"),
                ContentType="application/json",
            )
        except Exception as e:
            raise IOError(f"Failed to save artifact to S3: {e}") from e

        return path

    def load(self, path: Path) -> ArtifactEnvelope[BaseModel]:
        """Load an artifact from S3.

        Args:
            path: S3 key (as Path) of the artifact.

        Returns:
            The loaded and validated artifact envelope.

        Raises:
            ArtifactNotFoundError: If the object doesn't exist.
            ArtifactValidationError: If the artifact is invalid.
        """
        key = str(path)
        client = self._get_client()

        try:
            response = client.get_object(Bucket=self._bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
        except client.exceptions.NoSuchKey:
            raise ArtifactNotFoundError(f"Artifact not found: {path}")
        except Exception as e:
            if "NoSuchKey" in str(type(e).__name__):
                raise ArtifactNotFoundError(f"Artifact not found: {path}")
            raise IOError(f"Failed to load artifact from S3: {e}") from e

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
        client = self._get_client()

        def check_key(key: str) -> bool:
            try:
                client.head_object(Bucket=self._bucket, Key=key)
                return True
            except Exception:
                return False

        if artifact_type is not None:
            path = self.get_path_for_artifact(artifact_id, artifact_type)
            return check_key(str(path))

        # Search all type prefixes
        for atype in ArtifactType:
            path = self.get_path_for_artifact(artifact_id, atype)
            if check_key(str(path)):
                return True

        return False

    def delete(
        self,
        artifact_id: UUID,
        artifact_type: ArtifactType | None = None,
    ) -> None:
        """Delete an artifact from S3.

        Args:
            artifact_id: The UUID of the artifact to delete.
            artifact_type: Optional type hint to narrow the search.

        Raises:
            ArtifactNotFoundError: If the artifact doesn't exist.
        """
        key: str | None = None

        if artifact_type is not None:
            path = self.get_path_for_artifact(artifact_id, artifact_type)
            key = str(path)
            if not self.exists(artifact_id, artifact_type):
                raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")
        else:
            # Search all type prefixes
            for atype in ArtifactType:
                path = self.get_path_for_artifact(artifact_id, atype)
                if self.exists(artifact_id, atype):
                    key = str(path)
                    break

            if key is None:
                raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")

        client = self._get_client()
        try:
            client.delete_object(Bucket=self._bucket, Key=key)
        except Exception as e:
            raise IOError(f"Failed to delete artifact from S3: {e}") from e

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
        client = self._get_client()

        artifacts: list[ArtifactEnvelope[BaseModel]] = []
        paginator = client.get_paginator("list_objects_v2")

        try:
            for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith(".json"):
                        try:
                            artifact = self.load(Path(key))
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
        """Get the S3 key path for an artifact.

        Args:
            artifact_id: The artifact's UUID.
            artifact_type: The artifact's type.

        Returns:
            The S3 key as a Path object.
        """
        type_prefix = self._get_type_prefix(artifact_type)
        return Path(f"{type_prefix}/{artifact_id}.json")

    def _get_type_prefix(self, artifact_type: ArtifactType) -> str:
        """Get the key prefix for a specific artifact type."""
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
        """Check if S3 is accessible.

        Returns:
            True if S3 bucket is accessible.
        """
        try:
            client = self._get_client()
            client.head_bucket(Bucket=self._bucket)
            return True
        except Exception:
            return False
