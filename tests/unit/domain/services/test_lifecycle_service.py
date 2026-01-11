"""Unit tests for LifecycleService."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import pytest

from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.models.lifecycle import (
    LifecycleConfig,
    LifecyclePolicy,
    ReviewTrigger,
    ReviewUrgency,
)
from rice_factor.domain.services.lifecycle_service import (
    AgeReport,
    LifecycleBlockingError,
    LifecycleService,
    ReviewPrompt,
)


@dataclass
class MockStoragePort:
    """Mock storage port for testing."""

    artifacts: list[ArtifactEnvelope[Any]] = field(default_factory=list)
    saved_artifacts: list[ArtifactEnvelope[Any]] = field(default_factory=list)

    def list_all(self) -> list[ArtifactEnvelope[Any]]:
        """List all artifacts."""
        return self.artifacts

    def load(self, artifact_id: str) -> ArtifactEnvelope[Any]:
        """Load artifact by ID."""
        for artifact in self.artifacts:
            if str(artifact.id).startswith(artifact_id):
                return artifact
        raise ValueError(f"Artifact not found: {artifact_id}")

    def save(self, artifact: ArtifactEnvelope[Any]) -> None:
        """Save artifact."""
        self.saved_artifacts.append(artifact)


@dataclass
class MockArchValidator:
    """Mock architecture validator."""

    violations_by_id: dict[str, list[Any]] = field(default_factory=dict)

    def check_violations(self, arch_plan: ArtifactEnvelope[Any]) -> list[Any]:
        """Return violations for artifact."""
        return self.violations_by_id.get(str(arch_plan.id), [])


@dataclass
class MockCoverageMonitor:
    """Mock coverage monitor."""

    drift_by_id: dict[str, float] = field(default_factory=dict)

    def calculate_drift(self, test_plan: ArtifactEnvelope[Any]) -> float:
        """Return coverage drift for artifact."""
        return self.drift_by_id.get(str(test_plan.id), 0.0)


def _make_artifact(
    age_days: int,
    artifact_type: ArtifactType = ArtifactType.PROJECT_PLAN,
    status: ArtifactStatus = ArtifactStatus.DRAFT,
) -> ArtifactEnvelope[Any]:
    """Create a test artifact with specified age."""
    created = datetime.now(timezone.utc) - timedelta(days=age_days)
    return ArtifactEnvelope(
        id=uuid4(),
        artifact_type=artifact_type,
        status=status,
        created_at=created,
        updated_at=created,
        payload={},
    )


class TestReviewPrompt:
    """Tests for ReviewPrompt dataclass."""

    def test_creation(self) -> None:
        """ReviewPrompt should be creatable."""
        prompt = ReviewPrompt(
            artifact_id="test-001",
            artifact_type="ProjectPlan",
            urgency=ReviewUrgency.REQUIRED,
            message="Review required",
            actions=["Fix it"],
        )
        assert prompt.artifact_id == "test-001"
        assert prompt.urgency == ReviewUrgency.REQUIRED

    def test_to_dict(self) -> None:
        """to_dict should serialize all fields."""
        prompt = ReviewPrompt(
            artifact_id="test-001",
            artifact_type="ProjectPlan",
            urgency=ReviewUrgency.REQUIRED,
            message="Review required",
            actions=["Fix it", "Run tests"],
        )
        d = prompt.to_dict()
        assert d["artifact_id"] == "test-001"
        assert d["urgency"] == "required"
        assert d["actions"] == ["Fix it", "Run tests"]


class TestAgeReport:
    """Tests for AgeReport dataclass."""

    def test_creation(self) -> None:
        """AgeReport should be creatable."""
        report = AgeReport(
            generated_at=datetime.now(timezone.utc),
            total_artifacts=10,
            requiring_action=[],
            blocking=[],
            healthy=[],
        )
        assert report.total_artifacts == 10

    def test_to_dict(self) -> None:
        """to_dict should serialize correctly."""
        report = AgeReport(
            generated_at=datetime(2026, 1, 11, 12, 0, 0, tzinfo=timezone.utc),
            total_artifacts=3,
            requiring_action=[],
            blocking=[],
            healthy=[],
        )
        d = report.to_dict()
        assert d["total_artifacts"] == 3
        assert "generated_at" in d
        assert d["requiring_action_count"] == 0


class TestLifecycleBlockingError:
    """Tests for LifecycleBlockingError."""

    def test_error_message(self) -> None:
        """Error should have descriptive message."""
        from rice_factor.domain.models.lifecycle import PolicyResult

        result = PolicyResult(
            artifact_id="test-001-abcd",
            artifact_type="ProjectPlan",
            triggers=[ReviewTrigger.AGE],
            urgency=ReviewUrgency.MANDATORY,
            age_months=4.0,
            violations=[],
            coverage_drift=None,
        )
        error = LifecycleBlockingError([result])
        assert "test-001" in str(error)
        assert "mandatory" in str(error)


class TestLifecycleServiceEvaluate:
    """Tests for LifecycleService evaluation."""

    def test_evaluate_artifact_with_policy(self) -> None:
        """Should evaluate artifact against its policy."""
        artifact = _make_artifact(age_days=100)  # ~3.3 months
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        result = service.evaluate_artifact(artifact)

        assert result is not None
        assert result.urgency == ReviewUrgency.REQUIRED
        assert ReviewTrigger.AGE in result.triggers

    def test_evaluate_artifact_without_policy(self) -> None:
        """Should return None for artifact without policy."""
        # Create artifact with type that has no default policy
        artifact = _make_artifact(age_days=30)
        # Manually override artifact_type to something unknown
        storage = MockStoragePort(artifacts=[artifact])
        config = LifecycleConfig(policies={})  # No policies
        service = LifecycleService(artifact_store=storage, config=config)

        result = service.evaluate_artifact(artifact)

        assert result is None

    def test_evaluate_all_returns_results(self) -> None:
        """evaluate_all should return results for all artifacts."""
        artifacts = [
            _make_artifact(age_days=30, artifact_type=ArtifactType.PROJECT_PLAN),
            _make_artifact(age_days=100, artifact_type=ArtifactType.TEST_PLAN),
        ]
        storage = MockStoragePort(artifacts=artifacts)
        service = LifecycleService(artifact_store=storage)

        results = service.evaluate_all()

        assert len(results) == 2

    def test_evaluate_all_with_arch_validator(self) -> None:
        """evaluate_all should include violations for ArchitecturePlan."""
        artifact = _make_artifact(age_days=30, artifact_type=ArtifactType.ARCHITECTURE_PLAN)
        storage = MockStoragePort(artifacts=[artifact])
        arch_validator = MockArchValidator(violations_by_id={str(artifact.id): ["violation1"]})
        service = LifecycleService(
            artifact_store=storage,
            arch_validator=arch_validator,
        )

        results = service.evaluate_all()

        assert len(results) == 1
        assert results[0].urgency == ReviewUrgency.MANDATORY
        assert ReviewTrigger.VIOLATION in results[0].triggers

    def test_evaluate_all_with_coverage_monitor(self) -> None:
        """evaluate_all should include drift for TestPlan."""
        artifact = _make_artifact(age_days=30, artifact_type=ArtifactType.TEST_PLAN)
        storage = MockStoragePort(artifacts=[artifact])
        coverage_monitor = MockCoverageMonitor(drift_by_id={str(artifact.id): 15.0})
        service = LifecycleService(
            artifact_store=storage,
            coverage_monitor=coverage_monitor,
        )

        results = service.evaluate_all()

        assert len(results) == 1
        assert ReviewTrigger.DRIFT in results[0].triggers


class TestLifecycleServiceBlocking:
    """Tests for blocking functionality."""

    def test_get_blocking_issues_empty(self) -> None:
        """Should return empty list when no blocking issues."""
        artifact = _make_artifact(age_days=30)  # Fresh, not blocking
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        blocking = service.get_blocking_issues()

        assert blocking == []

    def test_get_blocking_issues_with_violations(self) -> None:
        """Should return blocking issues for violations."""
        artifact = _make_artifact(age_days=30, artifact_type=ArtifactType.ARCHITECTURE_PLAN)
        storage = MockStoragePort(artifacts=[artifact])
        arch_validator = MockArchValidator(violations_by_id={str(artifact.id): ["violation"]})
        service = LifecycleService(
            artifact_store=storage,
            arch_validator=arch_validator,
        )

        blocking = service.get_blocking_issues()

        assert len(blocking) == 1
        assert blocking[0].blocks_work

    def test_check_can_proceed_true(self) -> None:
        """check_can_proceed should return True when no blocking issues."""
        artifact = _make_artifact(age_days=30)
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        can_proceed, blocking = service.check_can_proceed()

        assert can_proceed is True
        assert blocking == []

    def test_check_can_proceed_false(self) -> None:
        """check_can_proceed should return False with blocking issues."""
        artifact = _make_artifact(age_days=30, artifact_type=ArtifactType.ARCHITECTURE_PLAN)
        storage = MockStoragePort(artifacts=[artifact])
        arch_validator = MockArchValidator(violations_by_id={str(artifact.id): ["violation"]})
        service = LifecycleService(
            artifact_store=storage,
            arch_validator=arch_validator,
        )

        can_proceed, blocking = service.check_can_proceed()

        assert can_proceed is False
        assert len(blocking) == 1

    def test_require_can_proceed_raises(self) -> None:
        """require_can_proceed should raise when blocked."""
        artifact = _make_artifact(age_days=30, artifact_type=ArtifactType.ARCHITECTURE_PLAN)
        storage = MockStoragePort(artifacts=[artifact])
        arch_validator = MockArchValidator(violations_by_id={str(artifact.id): ["violation"]})
        service = LifecycleService(
            artifact_store=storage,
            arch_validator=arch_validator,
        )

        with pytest.raises(LifecycleBlockingError) as exc:
            service.require_can_proceed()

        assert len(exc.value.blocking_issues) == 1

    def test_require_can_proceed_succeeds(self) -> None:
        """require_can_proceed should not raise when not blocked."""
        artifact = _make_artifact(age_days=30)
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        # Should not raise
        service.require_can_proceed()


class TestLifecycleServicePrompts:
    """Tests for prompt generation."""

    def test_generate_prompts_empty_for_fresh(self) -> None:
        """Should not generate prompts for fresh artifacts."""
        artifact = _make_artifact(age_days=30)  # 1 month old
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        prompts = service.generate_prompts()

        assert prompts == []

    def test_generate_prompts_for_old_artifact(self) -> None:
        """Should generate prompts for old artifacts."""
        artifact = _make_artifact(age_days=100)  # ~3.3 months
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        prompts = service.generate_prompts()

        assert len(prompts) == 1
        assert prompts[0].urgency == ReviewUrgency.REQUIRED
        assert "Review required" in prompts[0].message

    def test_generate_prompts_mandatory_message(self) -> None:
        """Mandatory prompts should have BLOCKING message."""
        artifact = _make_artifact(age_days=30, artifact_type=ArtifactType.ARCHITECTURE_PLAN)
        storage = MockStoragePort(artifacts=[artifact])
        arch_validator = MockArchValidator(violations_by_id={str(artifact.id): ["violation"]})
        service = LifecycleService(
            artifact_store=storage,
            arch_validator=arch_validator,
        )

        prompts = service.generate_prompts()

        assert len(prompts) == 1
        assert "BLOCKING" in prompts[0].message

    def test_generate_prompts_recommended_message(self) -> None:
        """Recommended prompts should suggest review."""
        artifact = _make_artifact(age_days=75)  # ~2.5 months, warning period
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        prompts = service.generate_prompts()

        assert len(prompts) == 1
        assert prompts[0].urgency == ReviewUrgency.RECOMMENDED
        assert "should be reviewed" in prompts[0].message

    def test_generate_prompts_actions(self) -> None:
        """Prompts should include suggested actions."""
        artifact = _make_artifact(age_days=100)
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        prompts = service.generate_prompts()

        assert len(prompts[0].actions) > 0


class TestLifecycleServiceAgeReport:
    """Tests for age report generation."""

    def test_generate_age_report(self) -> None:
        """Should generate comprehensive age report."""
        artifacts = [
            _make_artifact(age_days=30),  # Fresh
            _make_artifact(age_days=100),  # Old, requires action
            _make_artifact(age_days=30, artifact_type=ArtifactType.ARCHITECTURE_PLAN),  # Will be blocking
        ]
        storage = MockStoragePort(artifacts=artifacts)
        arch_validator = MockArchValidator(violations_by_id={str(artifacts[2].id): ["v"]})
        service = LifecycleService(
            artifact_store=storage,
            arch_validator=arch_validator,
        )

        report = service.generate_age_report()

        assert report.total_artifacts == 3
        assert len(report.healthy) == 1
        assert len(report.requiring_action) == 2  # 1 old + 1 blocking
        assert len(report.blocking) == 1


class TestLifecycleServiceReview:
    """Tests for review recording."""

    def test_record_review_updates_timestamp(self) -> None:
        """record_review should update last_reviewed_at."""
        artifact = _make_artifact(age_days=100)
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        result = service.record_review(str(artifact.id)[:8])

        assert result.last_reviewed_at is not None
        assert len(storage.saved_artifacts) == 1

    def test_record_review_with_notes(self) -> None:
        """record_review should save notes."""
        artifact = _make_artifact(age_days=100)
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        result = service.record_review(str(artifact.id)[:8], notes="Looks good")

        assert result.review_notes == "Looks good"

    def test_extend_artifact(self) -> None:
        """extend_artifact should record extension reason."""
        artifact = _make_artifact(age_days=100)
        storage = MockStoragePort(artifacts=[artifact])
        service = LifecycleService(artifact_store=storage)

        result = service.extend_artifact(str(artifact.id)[:8], months=3, reason="Still valid")

        assert result.review_notes is not None
        assert "Extended for 3 months" in result.review_notes
        assert "Still valid" in result.review_notes
