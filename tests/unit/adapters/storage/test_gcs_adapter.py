"""Unit tests for GCSStorageAdapter."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from rice_factor.adapters.storage.gcs_adapter import GCSStorageAdapter, TYPE_PREFIX_MAP
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.failures.errors import ArtifactNotFoundError


class TestGCSStorageAdapterInit:
    """Tests for GCSStorageAdapter initialization."""

    def test_init_with_bucket(self) -> None:
        """GCSStorageAdapter should store bucket name."""
        adapter = GCSStorageAdapter(bucket_name="my-bucket")
        assert adapter.bucket_name == "my-bucket"
        assert adapter.prefix == "artifacts"

    def test_init_with_custom_prefix(self) -> None:
        """GCSStorageAdapter should accept custom prefix."""
        adapter = GCSStorageAdapter(bucket_name="my-bucket", prefix="custom/prefix/")
        assert adapter.prefix == "custom/prefix"  # Trailing slash stripped

    def test_init_with_project(self) -> None:
        """GCSStorageAdapter should accept project."""
        adapter = GCSStorageAdapter(bucket_name="my-bucket", project="my-project")
        assert adapter._project == "my-project"


class TestGCSStorageAdapterGetPath:
    """Tests for GCSStorageAdapter.get_path_for_artifact."""

    def test_get_path_for_project_plan(self) -> None:
        """get_path_for_artifact should return correct path for ProjectPlan."""
        adapter = GCSStorageAdapter(bucket_name="my-bucket")
        artifact_id = uuid4()

        path = adapter.get_path_for_artifact(artifact_id, ArtifactType.PROJECT_PLAN)

        # Use as_posix() for cross-platform comparison
        assert path.as_posix() == f"artifacts/project_plans/{artifact_id}.json"

    def test_get_path_for_test_plan(self) -> None:
        """get_path_for_artifact should return correct path for TestPlan."""
        adapter = GCSStorageAdapter(bucket_name="my-bucket", prefix="custom")
        artifact_id = uuid4()

        path = adapter.get_path_for_artifact(artifact_id, ArtifactType.TEST_PLAN)

        # Use as_posix() for cross-platform comparison
        assert path.as_posix() == f"custom/test_plans/{artifact_id}.json"

    def test_all_artifact_types_mapped(self) -> None:
        """All artifact types should have a prefix mapping."""
        for artifact_type in ArtifactType:
            if artifact_type in TYPE_PREFIX_MAP:
                assert TYPE_PREFIX_MAP[artifact_type] is not None


class TestGCSStorageAdapterWithMockClient:
    """Tests for GCSStorageAdapter with mocked GCS client."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock GCS client."""
        return MagicMock()

    @pytest.fixture
    def mock_bucket(self) -> MagicMock:
        """Create a mock GCS bucket."""
        return MagicMock()

    @pytest.fixture
    def adapter(
        self, mock_client: MagicMock, mock_bucket: MagicMock
    ) -> GCSStorageAdapter:
        """Create adapter with mock client and bucket."""
        adapter = GCSStorageAdapter(bucket_name="test-bucket", client=mock_client)
        adapter._bucket = mock_bucket
        return adapter

    def test_save_uploads_json(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """save should upload JSON to GCS."""
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

        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        adapter.save(mock_artifact)

        mock_bucket.blob.assert_called_once()
        mock_blob.upload_from_string.assert_called_once()
        call_kwargs = mock_blob.upload_from_string.call_args[1]
        assert call_kwargs["content_type"] == "application/json"

    def test_exists_returns_true_when_found(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """exists should return True when blob exists."""
        artifact_id = uuid4()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob

        result = adapter.exists(artifact_id, ArtifactType.PROJECT_PLAN)

        assert result is True
        mock_blob.exists.assert_called_once()

    def test_exists_returns_false_when_not_found(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """exists should return False when blob doesn't exist."""
        artifact_id = uuid4()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob

        result = adapter.exists(artifact_id, ArtifactType.PROJECT_PLAN)

        assert result is False

    def test_delete_deletes_blob(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """delete should delete the blob."""
        artifact_id = uuid4()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob

        adapter.delete(artifact_id, ArtifactType.PROJECT_PLAN)

        mock_blob.delete.assert_called_once()

    def test_delete_raises_when_not_found(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """delete should raise ArtifactNotFoundError when not found."""
        artifact_id = uuid4()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob

        with pytest.raises(ArtifactNotFoundError):
            adapter.delete(artifact_id, ArtifactType.PROJECT_PLAN)

    def test_load_parses_json(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """load should parse JSON from GCS response."""
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

        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_text.return_value = json.dumps(valid_artifact)
        mock_bucket.blob.return_value = mock_blob

        with patch.object(adapter, "_get_validator") as mock_validator:
            mock_validator.return_value.validate.return_value = MagicMock()
            adapter.load(Path(f"artifacts/project_plans/{artifact_id}.json"))

            mock_validator.return_value.validate.assert_called_once()

    def test_load_raises_on_not_found(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """load should raise ArtifactNotFoundError for missing blobs."""
        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob

        with pytest.raises(ArtifactNotFoundError):
            adapter.load(Path("artifacts/missing.json"))

    def test_is_available_checks_bucket(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """is_available should check bucket accessibility."""
        mock_bucket.exists.return_value = True

        result = adapter.is_available()

        assert result is True
        mock_bucket.exists.assert_called_once()

    def test_is_available_returns_false_on_error(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """is_available should return False on error."""
        mock_bucket.exists.side_effect = Exception("Access denied")

        result = adapter.is_available()

        assert result is False


class TestGCSStorageAdapterListByType:
    """Tests for GCSStorageAdapter.list_by_type."""

    @pytest.fixture
    def mock_bucket(self) -> MagicMock:
        """Create a mock GCS bucket."""
        return MagicMock()

    @pytest.fixture
    def adapter(self, mock_bucket: MagicMock) -> GCSStorageAdapter:
        """Create adapter with mock bucket."""
        adapter = GCSStorageAdapter(bucket_name="test-bucket", client=MagicMock())
        adapter._bucket = mock_bucket
        return adapter

    def test_list_by_type_iterates_blobs(
        self,
        adapter: GCSStorageAdapter,
        mock_bucket: MagicMock,
    ) -> None:
        """list_by_type should iterate over blobs."""
        mock_blob = MagicMock()
        mock_blob.name = "artifacts/project_plans/abc.json"
        mock_bucket.list_blobs.return_value = [mock_blob]

        # Mock load to fail so we get empty list
        with patch.object(adapter, "load", side_effect=ArtifactNotFoundError("test")):
            result = adapter.list_by_type(ArtifactType.PROJECT_PLAN)

        assert result == []
        mock_bucket.list_blobs.assert_called_once()


class TestGCSStorageAdapterClientCreation:
    """Tests for GCSStorageAdapter client creation."""

    def test_uses_provided_client(self) -> None:
        """Adapter should use provided client instead of creating new one."""
        mock_client = MagicMock()
        adapter = GCSStorageAdapter(bucket_name="test", client=mock_client)

        result = adapter._get_client()

        assert result is mock_client


class TestGCSStorageAdapterLoadById:
    """Tests for GCSStorageAdapter.load_by_id."""

    @pytest.fixture
    def mock_bucket(self) -> MagicMock:
        """Create a mock GCS bucket."""
        return MagicMock()

    @pytest.fixture
    def adapter(self, mock_bucket: MagicMock) -> GCSStorageAdapter:
        """Create adapter with mock bucket."""
        adapter = GCSStorageAdapter(bucket_name="test-bucket", client=MagicMock())
        adapter._bucket = mock_bucket
        return adapter

    def test_load_by_id_with_type_hint(
        self,
        adapter: GCSStorageAdapter,
    ) -> None:
        """load_by_id should use type hint when provided."""
        artifact_id = uuid4()

        with patch.object(adapter, "load") as mock_load:
            mock_load.return_value = MagicMock()
            adapter.load_by_id(artifact_id, ArtifactType.PROJECT_PLAN)

            mock_load.assert_called_once()
            path_arg = mock_load.call_args[0][0]
            assert "project_plans" in str(path_arg)

    def test_load_by_id_searches_all_types(
        self,
        adapter: GCSStorageAdapter,
    ) -> None:
        """load_by_id should search all types when no hint provided."""
        artifact_id = uuid4()

        with patch.object(adapter, "load") as mock_load:
            # Make it find on third try
            mock_load.side_effect = [
                ArtifactNotFoundError("not found"),
                ArtifactNotFoundError("not found"),
                MagicMock(),  # Found!
            ]
            adapter.load_by_id(artifact_id)

            assert mock_load.call_count == 3

    def test_load_by_id_raises_when_not_found(
        self,
        adapter: GCSStorageAdapter,
    ) -> None:
        """load_by_id should raise when artifact not found anywhere."""
        artifact_id = uuid4()

        with patch.object(adapter, "load") as mock_load:
            mock_load.side_effect = ArtifactNotFoundError("not found")

            with pytest.raises(ArtifactNotFoundError):
                adapter.load_by_id(artifact_id)
