"""Unit tests for FilesystemStorageAdapter."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from rice_factor.adapters.storage import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import (
    ArtifactType,
)
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads import (
    ProjectPlanPayload,
    TestPlanPayload,
)
from rice_factor.domain.failures.errors import (
    ArtifactNotFoundError,
    ArtifactValidationError,
)


@pytest.fixture
def artifacts_dir(tmp_path: Path) -> Path:
    """Create a temporary artifacts directory."""
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    return artifacts


@pytest.fixture
def storage(artifacts_dir: Path) -> FilesystemStorageAdapter:
    """Create a storage adapter instance."""
    return FilesystemStorageAdapter(artifacts_dir)


@pytest.fixture
def project_plan_artifact() -> ArtifactEnvelope[ProjectPlanPayload]:
    """Create a sample ProjectPlan artifact."""
    payload = ProjectPlanPayload(
        domains=[{"name": "core", "responsibility": "Business logic"}],
        modules=[{"name": "auth", "domain": "core"}],
        constraints={"architecture": "hexagonal", "languages": ["python"]},
    )
    return ArtifactEnvelope(
        artifact_type=ArtifactType.PROJECT_PLAN,
        payload=payload,
    )


@pytest.fixture
def test_plan_artifact() -> ArtifactEnvelope[TestPlanPayload]:
    """Create a sample TestPlan artifact."""
    payload = TestPlanPayload(
        tests=[
            {
                "id": "test-001",
                "target": "auth.login",
                "assertions": ["returns token"],
            }
        ]
    )
    return ArtifactEnvelope(
        artifact_type=ArtifactType.TEST_PLAN,
        payload=payload,
    )


class TestSaveArtifact:
    """Tests for saving artifacts."""

    def test_save_creates_file(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test that save creates a JSON file."""
        path = storage.save(project_plan_artifact)
        assert path.exists()
        assert path.suffix == ".json"

    def test_save_creates_parent_directories(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test that save creates parent directories."""
        # Directory doesn't exist yet
        type_dir = storage.artifacts_dir / "project_plans"
        assert not type_dir.exists()

        storage.save(project_plan_artifact)

        assert type_dir.exists()

    def test_save_uses_correct_path_convention(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test that save uses artifacts/<type>/<uuid>.json convention."""
        path = storage.save(project_plan_artifact)
        expected = (
            storage.artifacts_dir
            / "project_plans"
            / f"{project_plan_artifact.id}.json"
        )
        assert path == expected

    def test_save_writes_valid_json(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test that saved file contains valid JSON."""
        path = storage.save(project_plan_artifact)
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)  # Should not raise
        assert "artifact_type" in data
        assert "payload" in data

    def test_save_preserves_uuid(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test that UUID is preserved in saved file."""
        path = storage.save(project_plan_artifact)
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["id"] == str(project_plan_artifact.id)

    def test_save_to_explicit_path(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
        artifacts_dir: Path,
    ) -> None:
        """Test saving to an explicit path."""
        explicit_path = artifacts_dir / "custom" / "my_artifact.json"
        path = storage.save(project_plan_artifact, explicit_path)
        assert path == explicit_path
        assert path.exists()


class TestLoadArtifact:
    """Tests for loading artifacts."""

    def test_load_returns_artifact(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test that load returns an ArtifactEnvelope."""
        path = storage.save(project_plan_artifact)
        loaded = storage.load(path)
        assert isinstance(loaded, ArtifactEnvelope)

    def test_load_preserves_data(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test that loaded artifact matches original."""
        path = storage.save(project_plan_artifact)
        loaded = storage.load(path)
        assert loaded.id == project_plan_artifact.id
        assert loaded.artifact_type == project_plan_artifact.artifact_type
        assert loaded.status == project_plan_artifact.status

    def test_load_nonexistent_raises(
        self,
        storage: FilesystemStorageAdapter,
        artifacts_dir: Path,
    ) -> None:
        """Test that loading nonexistent file raises ArtifactNotFoundError."""
        path = artifacts_dir / "does_not_exist.json"
        with pytest.raises(ArtifactNotFoundError):
            storage.load(path)

    def test_load_invalid_json_raises(
        self,
        storage: FilesystemStorageAdapter,
        artifacts_dir: Path,
    ) -> None:
        """Test that loading invalid JSON raises ArtifactValidationError."""
        path = artifacts_dir / "invalid.json"
        path.write_text("not valid json {{{", encoding="utf-8")
        with pytest.raises(ArtifactValidationError):
            storage.load(path)


class TestLoadById:
    """Tests for loading artifacts by UUID."""

    def test_load_by_id_with_type_hint(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test loading by ID with type hint."""
        storage.save(project_plan_artifact)
        loaded = storage.load_by_id(
            project_plan_artifact.id, ArtifactType.PROJECT_PLAN
        )
        assert loaded.id == project_plan_artifact.id

    def test_load_by_id_without_type_hint(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test loading by ID without type hint searches all types."""
        storage.save(project_plan_artifact)
        loaded = storage.load_by_id(project_plan_artifact.id)
        assert loaded.id == project_plan_artifact.id

    def test_load_by_id_nonexistent_raises(
        self,
        storage: FilesystemStorageAdapter,
    ) -> None:
        """Test that loading nonexistent ID raises ArtifactNotFoundError."""
        with pytest.raises(ArtifactNotFoundError):
            storage.load_by_id(uuid4())


class TestExists:
    """Tests for exists check."""

    def test_exists_returns_true_for_saved(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test exists returns True for saved artifact."""
        storage.save(project_plan_artifact)
        assert storage.exists(project_plan_artifact.id)

    def test_exists_returns_false_for_unsaved(
        self,
        storage: FilesystemStorageAdapter,
    ) -> None:
        """Test exists returns False for unsaved artifact."""
        assert not storage.exists(uuid4())

    def test_exists_with_type_hint(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test exists with type hint."""
        storage.save(project_plan_artifact)
        assert storage.exists(
            project_plan_artifact.id, ArtifactType.PROJECT_PLAN
        )
        assert not storage.exists(
            project_plan_artifact.id, ArtifactType.TEST_PLAN
        )


class TestDelete:
    """Tests for deleting artifacts."""

    def test_delete_removes_file(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test that delete removes the file."""
        path = storage.save(project_plan_artifact)
        assert path.exists()

        storage.delete(project_plan_artifact.id, ArtifactType.PROJECT_PLAN)
        assert not path.exists()

    def test_delete_nonexistent_raises(
        self,
        storage: FilesystemStorageAdapter,
    ) -> None:
        """Test that deleting nonexistent raises ArtifactNotFoundError."""
        with pytest.raises(ArtifactNotFoundError):
            storage.delete(uuid4())


class TestListByType:
    """Tests for listing artifacts by type."""

    def test_list_by_type_returns_all(
        self,
        storage: FilesystemStorageAdapter,
    ) -> None:
        """Test listing returns all artifacts of a type."""
        # Create multiple project plans
        for _ in range(3):
            payload = ProjectPlanPayload(
                domains=[{"name": "core", "responsibility": "Test"}],
                modules=[{"name": "test", "domain": "core"}],
                constraints={"architecture": "clean", "languages": ["python"]},
            )
            artifact = ArtifactEnvelope(
                artifact_type=ArtifactType.PROJECT_PLAN, payload=payload
            )
            storage.save(artifact)

        plans = storage.list_by_type(ArtifactType.PROJECT_PLAN)
        assert len(plans) == 3

    def test_list_by_type_empty(
        self,
        storage: FilesystemStorageAdapter,
    ) -> None:
        """Test listing returns empty list when no artifacts."""
        plans = storage.list_by_type(ArtifactType.PROJECT_PLAN)
        assert plans == []


class TestRoundTrip:
    """Tests for round-trip consistency."""

    def test_save_load_roundtrip(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test that save followed by load preserves all data."""
        path = storage.save(project_plan_artifact)
        loaded = storage.load(path)

        # Check all envelope fields
        assert loaded.id == project_plan_artifact.id
        assert loaded.artifact_type == project_plan_artifact.artifact_type
        assert loaded.artifact_version == project_plan_artifact.artifact_version
        assert loaded.status == project_plan_artifact.status
        assert loaded.created_by == project_plan_artifact.created_by

        # Check payload
        assert loaded.payload.model_dump() == project_plan_artifact.payload.model_dump()

    def test_multiple_roundtrips(
        self,
        storage: FilesystemStorageAdapter,
        project_plan_artifact: ArtifactEnvelope[ProjectPlanPayload],
    ) -> None:
        """Test multiple save/load cycles preserve data."""
        path = storage.save(project_plan_artifact)

        for _ in range(3):
            loaded = storage.load(path)
            path = storage.save(loaded)

        final = storage.load(path)
        assert final.id == project_plan_artifact.id


class TestPathConventions:
    """Tests for path conventions."""

    def test_get_path_for_project_plan(
        self,
        storage: FilesystemStorageAdapter,
    ) -> None:
        """Test path for ProjectPlan."""
        artifact_id = uuid4()
        path = storage.get_path_for_artifact(artifact_id, ArtifactType.PROJECT_PLAN)
        assert "project_plans" in str(path)
        assert str(artifact_id) in str(path)

    def test_get_path_for_test_plan(
        self,
        storage: FilesystemStorageAdapter,
    ) -> None:
        """Test path for TestPlan."""
        artifact_id = uuid4()
        path = storage.get_path_for_artifact(artifact_id, ArtifactType.TEST_PLAN)
        assert "test_plans" in str(path)
