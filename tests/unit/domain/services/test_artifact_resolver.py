"""Unit tests for ArtifactResolver."""

from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest
from pydantic import BaseModel

from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.project_plan import (
    Architecture,
    Constraints,
    Domain,
    Module,
    ProjectPlanPayload,
)
from rice_factor.domain.failures.errors import ArtifactNotFoundError
from rice_factor.domain.services.artifact_resolver import ArtifactResolver


def _create_project_plan_payload() -> ProjectPlanPayload:
    """Create a valid ProjectPlanPayload for testing."""
    return ProjectPlanPayload(
        domains=[Domain(name="core", responsibility="Core functionality")],
        modules=[Module(name="main", domain="core")],
        constraints=Constraints(architecture=Architecture.HEXAGONAL, languages=["python"]),
    )


class TestArtifactResolverInitialization:
    """Tests for ArtifactResolver initialization."""

    def test_resolver_initialization(self, tmp_path: Path) -> None:
        """Resolver should initialize with storage."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        assert resolver.storage is storage

    def test_resolver_storage_property(self, tmp_path: Path) -> None:
        """Storage property should return storage adapter."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        assert resolver.storage == storage


class TestResolveByPath:
    """Tests for resolve_by_path method."""

    def test_resolve_valid_path(self, tmp_path: Path) -> None:
        """resolve_by_path should load artifact from valid path."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        # Create and save an artifact
        payload = _create_project_plan_payload()
        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=payload,
        )
        path = storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        # Resolve by path
        resolved = resolver.resolve_by_path(path)

        assert resolved.id == artifact.id
        assert resolved.artifact_type == ArtifactType.PROJECT_PLAN

    def test_resolve_invalid_path_fails(self, tmp_path: Path) -> None:
        """resolve_by_path should raise error for invalid path."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        with pytest.raises(ArtifactNotFoundError):
            resolver.resolve_by_path(Path("/nonexistent/path.json"))


class TestResolveById:
    """Tests for resolve_by_id method."""

    def test_resolve_valid_uuid(self, tmp_path: Path) -> None:
        """resolve_by_id should load artifact by UUID."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        # Create and save an artifact
        payload = _create_project_plan_payload()
        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=payload,
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        # Resolve by ID
        resolved = resolver.resolve_by_id(artifact.id)

        assert resolved.id == artifact.id

    def test_resolve_with_type_hint(self, tmp_path: Path) -> None:
        """resolve_by_id should use type hint for faster lookup."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        # Create and save an artifact
        payload = _create_project_plan_payload()
        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=payload,
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        # Resolve with type hint
        resolved = resolver.resolve_by_id(
            artifact.id, artifact_type=ArtifactType.PROJECT_PLAN
        )

        assert resolved.id == artifact.id

    def test_resolve_invalid_uuid_fails(self, tmp_path: Path) -> None:
        """resolve_by_id should raise error for invalid UUID."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        with pytest.raises(ArtifactNotFoundError):
            resolver.resolve_by_id(uuid4())


class TestResolve:
    """Tests for resolve method."""

    def test_resolve_uuid_string(self, tmp_path: Path) -> None:
        """resolve should handle UUID string."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        # Create and save an artifact
        payload = _create_project_plan_payload()
        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=payload,
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        # Resolve by UUID string
        resolved = resolver.resolve(str(artifact.id))

        assert resolved.id == artifact.id

    def test_resolve_file_path(self, tmp_path: Path) -> None:
        """resolve should handle file path."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        # Create and save an artifact
        payload = _create_project_plan_payload()
        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=payload,
        )
        path = storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        # Resolve by path string
        resolved = resolver.resolve(str(path))

        assert resolved.id == artifact.id

    def test_resolve_relative_path(self, tmp_path: Path) -> None:
        """resolve should handle path relative to artifacts dir."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        # Create and save an artifact
        payload = _create_project_plan_payload()
        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=payload,
        )
        path = storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        # Get relative path
        relative = path.relative_to(artifacts_dir)

        # Resolve by relative path
        resolved = resolver.resolve(str(relative))

        assert resolved.id == artifact.id

    def test_resolve_invalid_identifier_fails(self, tmp_path: Path) -> None:
        """resolve should raise error for invalid identifier."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        with pytest.raises(ArtifactNotFoundError):
            resolver.resolve("not-a-uuid-or-path")


class TestResolveLatestByType:
    """Tests for resolve_latest_by_type method."""

    def test_resolve_latest_returns_most_recent(self, tmp_path: Path) -> None:
        """resolve_latest_by_type should return most recent artifact."""
        import time

        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        # Create first artifact
        artifact1: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=_create_project_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact1))

        # Small delay to ensure different timestamps
        time.sleep(0.01)

        # Create second artifact
        artifact2: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=_create_project_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact2))

        # Resolve latest
        latest = resolver.resolve_latest_by_type(ArtifactType.PROJECT_PLAN)

        assert latest is not None
        assert latest.id == artifact2.id

    def test_resolve_latest_returns_none_when_empty(self, tmp_path: Path) -> None:
        """resolve_latest_by_type should return None when no artifacts exist."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        latest = resolver.resolve_latest_by_type(ArtifactType.PROJECT_PLAN)

        assert latest is None


class TestListByType:
    """Tests for list_by_type method."""

    def test_list_by_type_returns_artifacts(self, tmp_path: Path) -> None:
        """list_by_type should return all artifacts of type."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        # Create two artifacts
        for _ in range(2):
            artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
                artifact_type=ArtifactType.PROJECT_PLAN,
                status=ArtifactStatus.DRAFT,
                created_by=CreatedBy.LLM,
                payload=_create_project_plan_payload(),
            )
            storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        # List artifacts
        artifacts = resolver.list_by_type(ArtifactType.PROJECT_PLAN)

        assert len(artifacts) == 2

    def test_list_by_type_returns_empty_when_none(self, tmp_path: Path) -> None:
        """list_by_type should return empty list when no artifacts exist."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        artifacts = resolver.list_by_type(ArtifactType.PROJECT_PLAN)

        assert artifacts == []


class TestExists:
    """Tests for exists method."""

    def test_exists_returns_true_for_valid(self, tmp_path: Path) -> None:
        """exists should return True for valid artifact."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        # Create and save an artifact
        artifact: ArtifactEnvelope[Any] = ArtifactEnvelope(
            artifact_type=ArtifactType.PROJECT_PLAN,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=_create_project_plan_payload(),
        )
        storage.save(cast("ArtifactEnvelope[BaseModel]", artifact))

        assert resolver.exists(str(artifact.id)) is True

    def test_exists_returns_false_for_invalid(self, tmp_path: Path) -> None:
        """exists should return False for invalid artifact."""
        artifacts_dir = tmp_path / "artifacts"
        storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
        resolver = ArtifactResolver(storage=storage)

        assert resolver.exists(str(uuid4())) is False
