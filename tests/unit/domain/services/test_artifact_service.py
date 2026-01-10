"""Unit tests for ArtifactService."""

from pathlib import Path
from uuid import uuid4

import pytest

from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
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
from rice_factor.domain.failures.errors import (
    ArtifactNotFoundError,
    ArtifactStatusError,
)
from rice_factor.domain.services.artifact_service import ArtifactService


@pytest.fixture
def artifacts_dir(tmp_path: Path) -> Path:
    """Create and return artifacts directory."""
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    return artifacts


@pytest.fixture
def storage(artifacts_dir: Path) -> FilesystemStorageAdapter:
    """Create storage adapter."""
    return FilesystemStorageAdapter(artifacts_dir)


@pytest.fixture
def approvals(artifacts_dir: Path) -> ApprovalsTracker:
    """Create approvals tracker."""
    return ApprovalsTracker(artifacts_dir)


@pytest.fixture
def service(
    storage: FilesystemStorageAdapter, approvals: ApprovalsTracker
) -> ArtifactService:
    """Create artifact service."""
    return ArtifactService(storage, approvals)


@pytest.fixture
def draft_project_plan(storage: FilesystemStorageAdapter) -> ArtifactEnvelope:
    """Create and save a draft ProjectPlan artifact."""
    artifact: ArtifactEnvelope[ProjectPlanPayload] = ArtifactEnvelope(
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
    storage.save(artifact)
    return artifact


@pytest.fixture
def draft_test_plan(storage: FilesystemStorageAdapter) -> ArtifactEnvelope:
    """Create and save a draft TestPlan artifact."""
    artifact: ArtifactEnvelope[TestPlanPayload] = ArtifactEnvelope(
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
    storage.save(artifact)
    return artifact


class TestArtifactServiceApprove:
    """Tests for ArtifactService.approve()."""

    def test_approve_transitions_draft_to_approved(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """approve() transitions artifact from DRAFT to APPROVED."""
        approval = service.approve(draft_project_plan.id, "human@test.com")

        # Check approval record
        assert approval.artifact_id == draft_project_plan.id
        assert approval.approved_by == "human@test.com"

        # Check artifact was updated
        artifact = service.get(draft_project_plan.id)
        assert artifact.status == ArtifactStatus.APPROVED

    def test_approve_records_in_tracker(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """approve() records approval in tracker."""
        service.approve(draft_project_plan.id, "human@test.com")

        assert service.is_approved(draft_project_plan.id) is True

    def test_approve_rejects_already_approved(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """approve() raises error for already approved artifact."""
        service.approve(draft_project_plan.id, "human@test.com")

        with pytest.raises(ArtifactStatusError) as exc_info:
            service.approve(draft_project_plan.id, "another@test.com")

        assert "Only DRAFT artifacts can be approved" in str(exc_info.value)

    def test_approve_with_type_hint(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """approve() works with artifact_type hint."""
        approval = service.approve(
            draft_project_plan.id,
            "human@test.com",
            artifact_type=ArtifactType.PROJECT_PLAN,
        )

        assert approval.artifact_id == draft_project_plan.id

    def test_approve_raises_for_nonexistent(self, service: ArtifactService) -> None:
        """approve() raises error for non-existent artifact."""
        with pytest.raises(ArtifactNotFoundError):
            service.approve(uuid4(), "human@test.com")


class TestArtifactServiceLock:
    """Tests for ArtifactService.lock()."""

    def test_lock_transitions_approved_to_locked(
        self, service: ArtifactService, draft_test_plan: ArtifactEnvelope
    ) -> None:
        """lock() transitions TestPlan from APPROVED to LOCKED."""
        # First approve
        service.approve(draft_test_plan.id, "human@test.com")

        # Then lock
        locked = service.lock(draft_test_plan.id)

        assert locked.status == ArtifactStatus.LOCKED

    def test_lock_rejects_draft_artifact(
        self, service: ArtifactService, draft_test_plan: ArtifactEnvelope
    ) -> None:
        """lock() raises error for DRAFT artifact."""
        with pytest.raises(ArtifactStatusError) as exc_info:
            service.lock(draft_test_plan.id)

        assert "Only APPROVED artifacts can be locked" in str(exc_info.value)

    def test_lock_rejects_non_testplan(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """lock() raises error for non-TestPlan artifact."""
        service.approve(draft_project_plan.id, "human@test.com")

        with pytest.raises(ArtifactStatusError) as exc_info:
            service.lock(draft_project_plan.id)

        assert "Only TestPlan artifacts can be locked" in str(exc_info.value)

    def test_lock_raises_for_nonexistent(self, service: ArtifactService) -> None:
        """lock() raises error for non-existent artifact."""
        with pytest.raises(ArtifactNotFoundError):
            service.lock(uuid4())


class TestArtifactServiceModify:
    """Tests for ArtifactService.modify()."""

    def test_modify_updates_draft_artifact(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """modify() updates payload of DRAFT artifact."""
        new_domains = [
            Domain(name="core", responsibility="Core functionality"),
            Domain(name="api", responsibility="API layer"),
        ]
        modified = service.modify(
            draft_project_plan.id,
            {"domains": new_domains},
        )

        assert len(modified.payload.domains) == 2
        assert modified.payload.domains[1].name == "api"

    def test_modify_persists_changes(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """modify() persists changes to storage."""
        new_domains = [
            Domain(name="updated", responsibility="Updated domain"),
        ]
        service.modify(
            draft_project_plan.id,
            {"domains": new_domains},
        )

        # Reload and verify
        reloaded = service.get(draft_project_plan.id)
        assert reloaded.payload.domains[0].name == "updated"

    def test_modify_rejects_approved_artifact(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """modify() raises error for APPROVED artifact."""
        service.approve(draft_project_plan.id, "human@test.com")

        new_domains = [Domain(name="fail", responsibility="Should fail")]
        with pytest.raises(ArtifactStatusError) as exc_info:
            service.modify(
                draft_project_plan.id,
                {"domains": new_domains},
            )

        assert "Only DRAFT artifacts can be modified" in str(exc_info.value)

    def test_modify_hard_fails_for_locked_artifact(
        self, service: ArtifactService, draft_test_plan: ArtifactEnvelope
    ) -> None:
        """modify() hard fails for LOCKED artifact with specific message."""
        service.approve(draft_test_plan.id, "human@test.com")
        service.lock(draft_test_plan.id)

        new_tests = [
            TestDefinition(
                id="test-002",
                target="other.py",
                assertions=["should fail"],
            )
        ]
        with pytest.raises(ArtifactStatusError) as exc_info:
            service.modify(
                draft_test_plan.id,
                {"tests": new_tests},
            )

        assert "LOCKED" in str(exc_info.value)
        assert "permanently immutable" in str(exc_info.value)

    def test_modify_raises_for_nonexistent(self, service: ArtifactService) -> None:
        """modify() raises error for non-existent artifact."""
        new_domains = [Domain(name="fail", responsibility="Should fail")]
        with pytest.raises(ArtifactNotFoundError):
            service.modify(uuid4(), {"domains": new_domains})


class TestArtifactServiceGet:
    """Tests for ArtifactService.get()."""

    def test_get_returns_artifact(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """get() returns the artifact by ID."""
        artifact = service.get(draft_project_plan.id)

        assert artifact.id == draft_project_plan.id
        assert artifact.artifact_type == ArtifactType.PROJECT_PLAN

    def test_get_with_type_hint(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """get() works with artifact_type hint."""
        artifact = service.get(
            draft_project_plan.id,
            artifact_type=ArtifactType.PROJECT_PLAN,
        )

        assert artifact.id == draft_project_plan.id

    def test_get_raises_for_nonexistent(self, service: ArtifactService) -> None:
        """get() raises error for non-existent artifact."""
        with pytest.raises(ArtifactNotFoundError):
            service.get(uuid4())


class TestArtifactServiceApprovalQueries:
    """Tests for ArtifactService approval query methods."""

    def test_is_approved_returns_true_after_approval(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """is_approved() returns True after approval."""
        service.approve(draft_project_plan.id, "human@test.com")

        assert service.is_approved(draft_project_plan.id) is True

    def test_is_approved_returns_false_before_approval(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """is_approved() returns False before approval."""
        assert service.is_approved(draft_project_plan.id) is False

    def test_get_approval_returns_record(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """get_approval() returns the approval record."""
        service.approve(draft_project_plan.id, "human@test.com")

        approval = service.get_approval(draft_project_plan.id)

        assert approval is not None
        assert approval.approved_by == "human@test.com"

    def test_get_approval_returns_none_before_approval(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """get_approval() returns None before approval."""
        assert service.get_approval(draft_project_plan.id) is None


class TestArtifactServiceRevokeApproval:
    """Tests for ArtifactService.revoke_approval()."""

    def test_revoke_approval_reverts_to_draft(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """revoke_approval() reverts artifact to DRAFT status."""
        service.approve(draft_project_plan.id, "human@test.com")

        result = service.revoke_approval(draft_project_plan.id)

        assert result is True
        artifact = service.get(draft_project_plan.id)
        assert artifact.status == ArtifactStatus.DRAFT
        assert service.is_approved(draft_project_plan.id) is False

    def test_revoke_approval_returns_false_for_unapproved(
        self, service: ArtifactService, draft_project_plan: ArtifactEnvelope
    ) -> None:
        """revoke_approval() returns False for unapproved artifact."""
        result = service.revoke_approval(draft_project_plan.id)

        assert result is False

    def test_revoke_approval_rejects_locked(
        self, service: ArtifactService, draft_test_plan: ArtifactEnvelope
    ) -> None:
        """revoke_approval() raises error for LOCKED artifact."""
        service.approve(draft_test_plan.id, "human@test.com")
        service.lock(draft_test_plan.id)

        with pytest.raises(ArtifactStatusError) as exc_info:
            service.revoke_approval(draft_test_plan.id)

        assert "LOCKED" in str(exc_info.value)
        assert "permanently immutable" in str(exc_info.value)

    def test_revoke_approval_returns_false_for_nonexistent(
        self, service: ArtifactService
    ) -> None:
        """revoke_approval() returns False for non-existent artifact."""
        result = service.revoke_approval(uuid4())

        assert result is False
