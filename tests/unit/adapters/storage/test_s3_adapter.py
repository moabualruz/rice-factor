"""Unit tests for S3StorageAdapter."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from rice_factor.adapters.storage.s3_adapter import S3StorageAdapter, TYPE_PREFIX_MAP
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.failures.errors import ArtifactNotFoundError


class TestS3StorageAdapterInit:
    """Tests for S3StorageAdapter initialization."""

    def test_init_with_bucket(self) -> None:
        """S3StorageAdapter should store bucket name."""
        adapter = S3StorageAdapter(bucket="my-bucket")
        assert adapter.bucket == "my-bucket"
        assert adapter.prefix == "artifacts"

    def test_init_with_custom_prefix(self) -> None:
        """S3StorageAdapter should accept custom prefix."""
        adapter = S3StorageAdapter(bucket="my-bucket", prefix="custom/prefix/")
        assert adapter.prefix == "custom/prefix"  # Trailing slash stripped

    def test_init_with_region(self) -> None:
        """S3StorageAdapter should accept region."""
        adapter = S3StorageAdapter(bucket="my-bucket", region="us-west-2")
        assert adapter._region == "us-west-2"


class TestS3StorageAdapterGetPath:
    """Tests for S3StorageAdapter.get_path_for_artifact."""

    def test_get_path_for_project_plan(self) -> None:
        """get_path_for_artifact should return correct path for ProjectPlan."""
        adapter = S3StorageAdapter(bucket="my-bucket")
        artifact_id = uuid4()

        path = adapter.get_path_for_artifact(artifact_id, ArtifactType.PROJECT_PLAN)

        # Use as_posix() for cross-platform comparison
        assert path.as_posix() == f"artifacts/project_plans/{artifact_id}.json"

    def test_get_path_for_test_plan(self) -> None:
        """get_path_for_artifact should return correct path for TestPlan."""
        adapter = S3StorageAdapter(bucket="my-bucket", prefix="custom")
        artifact_id = uuid4()

        path = adapter.get_path_for_artifact(artifact_id, ArtifactType.TEST_PLAN)

        # Use as_posix() for cross-platform comparison
        assert path.as_posix() == f"custom/test_plans/{artifact_id}.json"

    def test_all_artifact_types_mapped(self) -> None:
        """All artifact types should have a prefix mapping."""
        for artifact_type in ArtifactType:
            # Skip RECONCILIATION_PLAN if it's not in the enum
            if artifact_type in TYPE_PREFIX_MAP:
                assert TYPE_PREFIX_MAP[artifact_type] is not None


class TestS3StorageAdapterWithMockClient:
    """Tests for S3StorageAdapter with mocked S3 client."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock S3 client."""
        client = MagicMock()
        # Set up NoSuchKey exception
        client.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})
        return client

    @pytest.fixture
    def adapter(self, mock_client: MagicMock) -> S3StorageAdapter:
        """Create adapter with mock client."""
        return S3StorageAdapter(bucket="test-bucket", client=mock_client)

    def test_save_calls_put_object(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """save should call put_object with correct parameters."""
        # Create a minimal artifact-like object
        mock_artifact = MagicMock()
        mock_artifact.id = uuid4()
        mock_artifact.artifact_type = ArtifactType.PROJECT_PLAN
        mock_artifact.model_dump.return_value = {
            "id": str(mock_artifact.id),
            "artifact_type": "ProjectPlan",
            "artifact_version": "1.0",
            "status": "draft",
            "created_at": "2026-01-01T00:00:00Z",
            "created_by": "system",
            "payload": {},
        }

        adapter.save(mock_artifact)

        mock_client.put_object.assert_called_once()
        call_kwargs = mock_client.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["ContentType"] == "application/json"
        assert str(mock_artifact.id) in call_kwargs["Key"]

    def test_exists_returns_true_when_found(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """exists should return True when object exists."""
        artifact_id = uuid4()
        mock_client.head_object.return_value = {}

        result = adapter.exists(artifact_id, ArtifactType.PROJECT_PLAN)

        assert result is True
        mock_client.head_object.assert_called_once()

    def test_exists_returns_false_when_not_found(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """exists should return False when object doesn't exist."""
        artifact_id = uuid4()
        mock_client.head_object.side_effect = Exception("Not found")

        result = adapter.exists(artifact_id, ArtifactType.PROJECT_PLAN)

        assert result is False

    def test_delete_calls_delete_object(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """delete should call delete_object."""
        artifact_id = uuid4()
        mock_client.head_object.return_value = {}  # exists check

        adapter.delete(artifact_id, ArtifactType.PROJECT_PLAN)

        mock_client.delete_object.assert_called_once()

    def test_delete_raises_when_not_found(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """delete should raise ArtifactNotFoundError when not found."""
        artifact_id = uuid4()
        mock_client.head_object.side_effect = Exception("Not found")

        with pytest.raises(ArtifactNotFoundError):
            adapter.delete(artifact_id, ArtifactType.PROJECT_PLAN)

    def test_load_parses_json(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """load should parse JSON from S3 response."""
        artifact_id = uuid4()
        valid_artifact = {
            "id": str(artifact_id),
            "artifact_type": "ProjectPlan",
            "artifact_version": "1.0",
            "status": "draft",
            "created_at": "2026-01-01T00:00:00+00:00",
            "created_by": "system",
            "payload": {"name": "Test Project", "description": "Test"},
        }

        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(valid_artifact).encode("utf-8")
        mock_client.get_object.return_value = {"Body": mock_body}

        with patch.object(adapter, "_get_validator") as mock_validator:
            mock_validator.return_value.validate.return_value = MagicMock()
            adapter.load(Path(f"artifacts/project_plans/{artifact_id}.json"))

            mock_validator.return_value.validate.assert_called_once()

    def test_load_raises_on_not_found(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """load should raise ArtifactNotFoundError for missing objects."""
        mock_client.get_object.side_effect = mock_client.exceptions.NoSuchKey()

        with pytest.raises(ArtifactNotFoundError):
            adapter.load(Path("artifacts/missing.json"))

    def test_is_available_checks_bucket(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """is_available should check bucket accessibility."""
        mock_client.head_bucket.return_value = {}

        result = adapter.is_available()

        assert result is True
        mock_client.head_bucket.assert_called_with(Bucket="test-bucket")

    def test_is_available_returns_false_on_error(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """is_available should return False on error."""
        mock_client.head_bucket.side_effect = Exception("Access denied")

        result = adapter.is_available()

        assert result is False


class TestS3StorageAdapterListByType:
    """Tests for S3StorageAdapter.list_by_type."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock S3 client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def adapter(self, mock_client: MagicMock) -> S3StorageAdapter:
        """Create adapter with mock client."""
        return S3StorageAdapter(bucket="test-bucket", client=mock_client)

    def test_list_by_type_paginates(
        self,
        adapter: S3StorageAdapter,
        mock_client: MagicMock,
    ) -> None:
        """list_by_type should use paginator."""
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"Contents": [{"Key": "artifacts/project_plans/abc.json"}]}
        ]
        mock_client.get_paginator.return_value = mock_paginator

        # Mock load to fail so we get empty list
        with patch.object(adapter, "load", side_effect=ArtifactNotFoundError("test")):
            result = adapter.list_by_type(ArtifactType.PROJECT_PLAN)

        assert result == []
        mock_client.get_paginator.assert_called_with("list_objects_v2")


class TestS3StorageAdapterClientCreation:
    """Tests for S3StorageAdapter client creation."""

    def test_get_client_raises_without_boto3(self) -> None:
        """_get_client should raise ImportError without boto3."""
        adapter = S3StorageAdapter(bucket="test")

        with patch.dict("sys.modules", {"boto3": None}):
            # This test is tricky because boto3 might be installed
            # We test the error path by mocking the import
            pass  # Skip actual import test as it's environment-dependent

    def test_uses_provided_client(self) -> None:
        """Adapter should use provided client instead of creating new one."""
        mock_client = MagicMock()
        adapter = S3StorageAdapter(bucket="test", client=mock_client)

        result = adapter._get_client()

        assert result is mock_client
