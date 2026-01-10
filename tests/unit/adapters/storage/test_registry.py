"""Unit tests for ArtifactRegistry."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from rice_factor.adapters.storage.registry import ArtifactRegistry
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads import ProjectPlanPayload, TestPlanPayload
from rice_factor.domain.artifacts.payloads.project_plan import (
    Architecture,
    Constraints,
    Domain,
    Module,
)
from rice_factor.domain.artifacts.payloads.test_plan import TestDefinition
from rice_factor.domain.artifacts.registry import RegistryEntry
from rice_factor.domain.failures.errors import ArtifactDependencyError


def make_project_plan() -> ArtifactEnvelope[ProjectPlanPayload]:
    """Create a test ProjectPlan artifact."""
    return ArtifactEnvelope(
        artifact_type=ArtifactType.PROJECT_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=ProjectPlanPayload(
            domains=[Domain(name="core", responsibility="Core functionality")],
            modules=[Module(name="main", domain="core")],
            constraints=Constraints(
                architecture=Architecture.HEXAGONAL,
                languages=["python"],
            ),
        ),
    )


def make_test_plan() -> ArtifactEnvelope[TestPlanPayload]:
    """Create a test TestPlan artifact."""
    return ArtifactEnvelope(
        artifact_type=ArtifactType.TEST_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=TestPlanPayload(
            tests=[
                TestDefinition(
                    id="test-001",
                    target="main.py",
                    assertions=["assert main() returns 0"],
                )
            ],
        ),
    )


class TestArtifactRegistryInit:
    """Tests for ArtifactRegistry initialization."""

    def test_init_creates_empty_registry(self, tmp_path: Path) -> None:
        """ArtifactRegistry initializes with empty entries when no index exists."""
        registry = ArtifactRegistry(tmp_path)

        assert registry.list_all() == []

    def test_index_file_path(self, tmp_path: Path) -> None:
        """index_file returns correct path."""
        registry = ArtifactRegistry(tmp_path)

        expected = tmp_path / "_meta" / "index.json"
        assert registry.index_file == expected


class TestArtifactRegistryRegister:
    """Tests for ArtifactRegistry.register()."""

    def test_register_creates_entry(self, tmp_path: Path) -> None:
        """register() creates and returns a RegistryEntry."""
        registry = ArtifactRegistry(tmp_path)
        artifact = make_project_plan()

        entry = registry.register(artifact, "project_plans/abc123.json")

        assert isinstance(entry, RegistryEntry)
        assert entry.id == artifact.id
        assert entry.artifact_type == ArtifactType.PROJECT_PLAN
        assert entry.path == "project_plans/abc123.json"
        assert entry.status == ArtifactStatus.DRAFT

    def test_register_persists_to_file(self, tmp_path: Path) -> None:
        """register() persists the entry to index.json."""
        registry = ArtifactRegistry(tmp_path)
        artifact = make_project_plan()

        registry.register(artifact, "project_plans/abc123.json")

        # Check file exists and contains the entry
        assert registry.index_file.exists()
        content = json.loads(registry.index_file.read_text(encoding="utf-8"))
        assert len(content["artifacts"]) == 1
        assert content["artifacts"][0]["id"] == str(artifact.id)

    def test_register_multiple_artifacts(self, tmp_path: Path) -> None:
        """register() can handle multiple artifacts."""
        registry = ArtifactRegistry(tmp_path)
        artifact1 = make_project_plan()
        artifact2 = make_test_plan()

        registry.register(artifact1, "project_plans/proj1.json")
        registry.register(artifact2, "test_plans/test1.json")

        assert len(registry.list_all()) == 2

    def test_register_creates_meta_directory(self, tmp_path: Path) -> None:
        """register() creates _meta directory if it doesn't exist."""
        registry = ArtifactRegistry(tmp_path)
        artifact = make_project_plan()

        meta_dir = tmp_path / "_meta"
        assert not meta_dir.exists()

        registry.register(artifact, "project_plans/abc123.json")

        assert meta_dir.exists()


class TestArtifactRegistryUnregister:
    """Tests for ArtifactRegistry.unregister()."""

    def test_unregister_removes_entry(self, tmp_path: Path) -> None:
        """unregister() removes an entry and returns True."""
        registry = ArtifactRegistry(tmp_path)
        artifact = make_project_plan()
        registry.register(artifact, "project_plans/abc123.json")

        result = registry.unregister(artifact.id)

        assert result is True
        assert registry.lookup(artifact.id) is None

    def test_unregister_returns_false_for_unknown(self, tmp_path: Path) -> None:
        """unregister() returns False for unknown artifact."""
        registry = ArtifactRegistry(tmp_path)

        result = registry.unregister(uuid4())

        assert result is False

    def test_unregister_persists_removal(self, tmp_path: Path) -> None:
        """unregister() persists the removal to index.json."""
        registry = ArtifactRegistry(tmp_path)
        artifact = make_project_plan()
        registry.register(artifact, "project_plans/abc123.json")

        registry.unregister(artifact.id)

        # Reload and verify
        registry2 = ArtifactRegistry(tmp_path)
        assert registry2.lookup(artifact.id) is None


class TestArtifactRegistryUpdateStatus:
    """Tests for ArtifactRegistry.update_status()."""

    def test_update_status_changes_entry(self, tmp_path: Path) -> None:
        """update_status() updates the status of an entry."""
        registry = ArtifactRegistry(tmp_path)
        artifact = make_project_plan()
        registry.register(artifact, "project_plans/abc123.json")

        result = registry.update_status(artifact.id, ArtifactStatus.APPROVED)

        assert result is True
        entry = registry.lookup(artifact.id)
        assert entry is not None
        assert entry.status == ArtifactStatus.APPROVED

    def test_update_status_returns_false_for_unknown(self, tmp_path: Path) -> None:
        """update_status() returns False for unknown artifact."""
        registry = ArtifactRegistry(tmp_path)

        result = registry.update_status(uuid4(), ArtifactStatus.APPROVED)

        assert result is False


class TestArtifactRegistryLookup:
    """Tests for ArtifactRegistry.lookup()."""

    def test_lookup_returns_entry(self, tmp_path: Path) -> None:
        """lookup() returns the RegistryEntry for a registered artifact."""
        registry = ArtifactRegistry(tmp_path)
        artifact = make_project_plan()
        registry.register(artifact, "project_plans/abc123.json")

        entry = registry.lookup(artifact.id)

        assert entry is not None
        assert entry.id == artifact.id

    def test_lookup_returns_none_for_unknown(self, tmp_path: Path) -> None:
        """lookup() returns None for unknown artifact."""
        registry = ArtifactRegistry(tmp_path)

        assert registry.lookup(uuid4()) is None


class TestArtifactRegistryListByType:
    """Tests for ArtifactRegistry.list_by_type()."""

    def test_list_by_type_filters_correctly(self, tmp_path: Path) -> None:
        """list_by_type() returns only artifacts of the specified type."""
        registry = ArtifactRegistry(tmp_path)
        proj1 = make_project_plan()
        proj2 = make_project_plan()
        test1 = make_test_plan()

        registry.register(proj1, "project_plans/proj1.json")
        registry.register(proj2, "project_plans/proj2.json")
        registry.register(test1, "test_plans/test1.json")

        project_plans = registry.list_by_type(ArtifactType.PROJECT_PLAN)
        test_plans = registry.list_by_type(ArtifactType.TEST_PLAN)

        assert len(project_plans) == 2
        assert len(test_plans) == 1

    def test_list_by_type_returns_empty_for_no_matches(self, tmp_path: Path) -> None:
        """list_by_type() returns empty list when no artifacts match."""
        registry = ArtifactRegistry(tmp_path)
        artifact = make_project_plan()
        registry.register(artifact, "project_plans/abc123.json")

        result = registry.list_by_type(ArtifactType.TEST_PLAN)

        assert result == []


class TestArtifactRegistryListByStatus:
    """Tests for ArtifactRegistry.list_by_status()."""

    def test_list_by_status_filters_correctly(self, tmp_path: Path) -> None:
        """list_by_status() returns only artifacts with the specified status."""
        registry = ArtifactRegistry(tmp_path)
        draft = make_project_plan()
        approved = make_project_plan().approve()

        registry.register(draft, "project_plans/draft.json")
        registry.register(approved, "project_plans/approved.json")

        drafts = registry.list_by_status(ArtifactStatus.DRAFT)
        approved_list = registry.list_by_status(ArtifactStatus.APPROVED)

        assert len(drafts) == 1
        assert len(approved_list) == 1
        assert drafts[0].id == draft.id
        assert approved_list[0].id == approved.id


class TestArtifactRegistryListAll:
    """Tests for ArtifactRegistry.list_all()."""

    def test_list_all_returns_all_entries(self, tmp_path: Path) -> None:
        """list_all() returns all registered artifacts."""
        registry = ArtifactRegistry(tmp_path)
        artifact1 = make_project_plan()
        artifact2 = make_test_plan()

        registry.register(artifact1, "project_plans/proj1.json")
        registry.register(artifact2, "test_plans/test1.json")

        all_entries = registry.list_all()

        assert len(all_entries) == 2


class TestArtifactRegistryValidateDependencies:
    """Tests for ArtifactRegistry.validate_dependencies()."""

    def test_validate_passes_with_no_dependencies(self, tmp_path: Path) -> None:
        """validate_dependencies() passes for artifacts with no dependencies."""
        registry = ArtifactRegistry(tmp_path)
        artifact = make_project_plan()

        # Should not raise
        registry.validate_dependencies(artifact)

    def test_validate_passes_with_approved_dependency(self, tmp_path: Path) -> None:
        """validate_dependencies() passes when all dependencies are approved."""
        registry = ArtifactRegistry(tmp_path)
        dependency = make_project_plan().approve()
        registry.register(dependency, "project_plans/dep.json")

        artifact = ArtifactEnvelope(
            artifact_type=ArtifactType.TEST_PLAN,
            depends_on=[dependency.id],
            payload=TestPlanPayload(
                tests=[
                    TestDefinition(
                        id="test-001",
                        target="main.py",
                        assertions=["test"],
                    )
                ],
            ),
        )

        # Should not raise
        registry.validate_dependencies(artifact)

    def test_validate_passes_with_locked_dependency(self, tmp_path: Path) -> None:
        """validate_dependencies() passes when dependency is locked."""
        registry = ArtifactRegistry(tmp_path)
        dependency = make_test_plan().approve().lock()
        registry.register(dependency, "test_plans/dep.json")

        artifact = ArtifactEnvelope(
            artifact_type=ArtifactType.IMPLEMENTATION_PLAN,
            depends_on=[dependency.id],
            payload=ProjectPlanPayload(
                domains=[Domain(name="core", responsibility="Core")],
                modules=[Module(name="main", domain="core")],
                constraints=Constraints(
                    architecture=Architecture.HEXAGONAL, languages=["python"]
                ),
            ),
        )

        # Should not raise
        registry.validate_dependencies(artifact)

    def test_validate_fails_with_missing_dependency(self, tmp_path: Path) -> None:
        """validate_dependencies() raises error for missing dependency."""
        registry = ArtifactRegistry(tmp_path)
        missing_id = uuid4()

        artifact = ArtifactEnvelope(
            artifact_type=ArtifactType.TEST_PLAN,
            depends_on=[missing_id],
            payload=TestPlanPayload(
                tests=[
                    TestDefinition(
                        id="test-001",
                        target="main.py",
                        assertions=["test"],
                    )
                ],
            ),
        )

        with pytest.raises(ArtifactDependencyError) as exc_info:
            registry.validate_dependencies(artifact)

        assert str(missing_id) in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_validate_fails_with_draft_dependency(self, tmp_path: Path) -> None:
        """validate_dependencies() raises error for draft dependency."""
        registry = ArtifactRegistry(tmp_path)
        draft_dep = make_project_plan()  # Still in DRAFT
        registry.register(draft_dep, "project_plans/draft.json")

        artifact = ArtifactEnvelope(
            artifact_type=ArtifactType.TEST_PLAN,
            depends_on=[draft_dep.id],
            payload=TestPlanPayload(
                tests=[
                    TestDefinition(
                        id="test-001",
                        target="main.py",
                        assertions=["test"],
                    )
                ],
            ),
        )

        with pytest.raises(ArtifactDependencyError) as exc_info:
            registry.validate_dependencies(artifact)

        assert str(draft_dep.id) in str(exc_info.value)
        assert "DRAFT" in str(exc_info.value)


class TestArtifactRegistryPersistence:
    """Tests for ArtifactRegistry persistence."""

    def test_loads_existing_index(self, tmp_path: Path) -> None:
        """ArtifactRegistry loads existing index from file."""
        artifact_id = uuid4()
        now = datetime.now(UTC)

        # Create index file manually
        meta_dir = tmp_path / "_meta"
        meta_dir.mkdir(parents=True)
        index_file = meta_dir / "index.json"
        index_file.write_text(
            json.dumps(
                {
                    "artifacts": [
                        {
                            "id": str(artifact_id),
                            "artifact_type": "ProjectPlan",
                            "path": "project_plans/existing.json",
                            "status": "approved",
                            "created_at": now.isoformat(),
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        # Load registry
        registry = ArtifactRegistry(tmp_path)

        entry = registry.lookup(artifact_id)
        assert entry is not None
        assert entry.path == "project_plans/existing.json"
        assert entry.status == ArtifactStatus.APPROVED

    def test_handles_corrupted_json_gracefully(self, tmp_path: Path) -> None:
        """ArtifactRegistry handles corrupted JSON by starting fresh."""
        meta_dir = tmp_path / "_meta"
        meta_dir.mkdir(parents=True)
        index_file = meta_dir / "index.json"
        index_file.write_text("not valid json", encoding="utf-8")

        # Should not raise, just start fresh
        registry = ArtifactRegistry(tmp_path)

        assert registry.list_all() == []

    def test_handles_missing_keys_gracefully(self, tmp_path: Path) -> None:
        """ArtifactRegistry handles malformed JSON by starting fresh."""
        meta_dir = tmp_path / "_meta"
        meta_dir.mkdir(parents=True)
        index_file = meta_dir / "index.json"
        index_file.write_text('{"artifacts": [{"bad": "data"}]}', encoding="utf-8")

        # Should not raise, just start fresh
        registry = ArtifactRegistry(tmp_path)

        assert registry.list_all() == []
