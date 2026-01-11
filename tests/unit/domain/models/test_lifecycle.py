"""Unit tests for lifecycle policy models."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.models.lifecycle import (
    DEFAULT_POLICIES,
    LifecycleConfig,
    LifecyclePolicy,
    PolicyResult,
    ReviewTrigger,
    ReviewUrgency,
)


class TestReviewTrigger:
    """Tests for ReviewTrigger enum."""

    def test_age_value(self) -> None:
        """AGE trigger should have 'age' value."""
        assert ReviewTrigger.AGE.value == "age"

    def test_violation_value(self) -> None:
        """VIOLATION trigger should have 'violation' value."""
        assert ReviewTrigger.VIOLATION.value == "violation"

    def test_drift_value(self) -> None:
        """DRIFT trigger should have 'drift' value."""
        assert ReviewTrigger.DRIFT.value == "drift"

    def test_manual_value(self) -> None:
        """MANUAL trigger should have 'manual' value."""
        assert ReviewTrigger.MANUAL.value == "manual"


class TestReviewUrgency:
    """Tests for ReviewUrgency enum."""

    def test_informational_value(self) -> None:
        """INFORMATIONAL should have correct value."""
        assert ReviewUrgency.INFORMATIONAL.value == "informational"

    def test_recommended_value(self) -> None:
        """RECOMMENDED should have correct value."""
        assert ReviewUrgency.RECOMMENDED.value == "recommended"

    def test_required_value(self) -> None:
        """REQUIRED should have correct value."""
        assert ReviewUrgency.REQUIRED.value == "required"

    def test_mandatory_value(self) -> None:
        """MANDATORY should have correct value."""
        assert ReviewUrgency.MANDATORY.value == "mandatory"


class TestPolicyResult:
    """Tests for PolicyResult dataclass."""

    def test_creation(self) -> None:
        """PolicyResult should be creatable with all fields."""
        result = PolicyResult(
            artifact_id="test-001",
            artifact_type="ProjectPlan",
            triggers=[ReviewTrigger.AGE],
            urgency=ReviewUrgency.REQUIRED,
            age_months=4.5,
            violations=[],
            coverage_drift=None,
        )
        assert result.artifact_id == "test-001"
        assert result.artifact_type == "ProjectPlan"
        assert result.urgency == ReviewUrgency.REQUIRED

    def test_requires_action_when_required(self) -> None:
        """requires_action should be True for REQUIRED urgency."""
        result = PolicyResult(
            artifact_id="test",
            artifact_type="ProjectPlan",
            triggers=[],
            urgency=ReviewUrgency.REQUIRED,
            age_months=1.0,
            violations=[],
            coverage_drift=None,
        )
        assert result.requires_action is True

    def test_requires_action_when_mandatory(self) -> None:
        """requires_action should be True for MANDATORY urgency."""
        result = PolicyResult(
            artifact_id="test",
            artifact_type="ProjectPlan",
            triggers=[],
            urgency=ReviewUrgency.MANDATORY,
            age_months=1.0,
            violations=[],
            coverage_drift=None,
        )
        assert result.requires_action is True

    def test_requires_action_false_for_informational(self) -> None:
        """requires_action should be False for INFORMATIONAL."""
        result = PolicyResult(
            artifact_id="test",
            artifact_type="ProjectPlan",
            triggers=[],
            urgency=ReviewUrgency.INFORMATIONAL,
            age_months=1.0,
            violations=[],
            coverage_drift=None,
        )
        assert result.requires_action is False

    def test_requires_action_false_for_recommended(self) -> None:
        """requires_action should be False for RECOMMENDED."""
        result = PolicyResult(
            artifact_id="test",
            artifact_type="ProjectPlan",
            triggers=[],
            urgency=ReviewUrgency.RECOMMENDED,
            age_months=1.0,
            violations=[],
            coverage_drift=None,
        )
        assert result.requires_action is False

    def test_blocks_work_only_for_mandatory(self) -> None:
        """blocks_work should be True only for MANDATORY."""
        mandatory = PolicyResult(
            artifact_id="test",
            artifact_type="ProjectPlan",
            triggers=[],
            urgency=ReviewUrgency.MANDATORY,
            age_months=1.0,
            violations=[],
            coverage_drift=None,
        )
        required = PolicyResult(
            artifact_id="test",
            artifact_type="ProjectPlan",
            triggers=[],
            urgency=ReviewUrgency.REQUIRED,
            age_months=1.0,
            violations=[],
            coverage_drift=None,
        )
        assert mandatory.blocks_work is True
        assert required.blocks_work is False

    def test_to_dict(self) -> None:
        """to_dict should serialize all fields correctly."""
        result = PolicyResult(
            artifact_id="test-001",
            artifact_type="TestPlan",
            triggers=[ReviewTrigger.AGE, ReviewTrigger.DRIFT],
            urgency=ReviewUrgency.REQUIRED,
            age_months=3.5,
            violations=["violation1"],
            coverage_drift=12.5,
        )
        d = result.to_dict()

        assert d["artifact_id"] == "test-001"
        assert d["artifact_type"] == "TestPlan"
        assert d["triggers"] == ["age", "drift"]
        assert d["urgency"] == "required"
        assert d["age_months"] == 3.5
        assert d["violations"] == ["violation1"]
        assert d["coverage_drift"] == 12.5
        assert d["requires_action"] is True
        assert d["blocks_work"] is False


class TestLifecyclePolicy:
    """Tests for LifecyclePolicy dataclass."""

    def _make_artifact(
        self,
        age_days: int,
        artifact_type: ArtifactType = ArtifactType.PROJECT_PLAN,
    ) -> ArtifactEnvelope:
        """Create a test artifact with specified age."""
        created = datetime.now(timezone.utc) - timedelta(days=age_days)
        return ArtifactEnvelope(
            id=uuid4(),
            artifact_type=artifact_type,
            status=ArtifactStatus.DRAFT,
            created_at=created,
            updated_at=created,
            payload={},
        )

    def test_default_values(self) -> None:
        """Policy should have sensible defaults."""
        policy = LifecyclePolicy(artifact_type="ProjectPlan")
        assert policy.review_after_months == 3
        assert policy.warning_at_months is None
        assert policy.mandatory_on_violation is False
        assert policy.coverage_drift_threshold is None

    def test_evaluate_fresh_artifact(self) -> None:
        """Fresh artifact should be INFORMATIONAL."""
        policy = LifecyclePolicy(artifact_type="ProjectPlan")
        artifact = self._make_artifact(age_days=30)  # 1 month old

        result = policy.evaluate(artifact)

        assert result.urgency == ReviewUrgency.INFORMATIONAL
        assert result.triggers == []
        assert result.requires_action is False

    def test_evaluate_artifact_in_warning_period(self) -> None:
        """Artifact in warning period should be RECOMMENDED."""
        policy = LifecyclePolicy(
            artifact_type="ProjectPlan",
            review_after_months=3,
            warning_at_months=2,
        )
        artifact = self._make_artifact(age_days=75)  # ~2.5 months old

        result = policy.evaluate(artifact)

        assert result.urgency == ReviewUrgency.RECOMMENDED
        assert ReviewTrigger.AGE in result.triggers
        assert result.requires_action is False

    def test_evaluate_artifact_past_review_date(self) -> None:
        """Artifact past review date should be REQUIRED."""
        policy = LifecyclePolicy(
            artifact_type="ProjectPlan",
            review_after_months=3,
        )
        artifact = self._make_artifact(age_days=100)  # ~3.3 months old

        result = policy.evaluate(artifact)

        assert result.urgency == ReviewUrgency.REQUIRED
        assert ReviewTrigger.AGE in result.triggers
        assert result.requires_action is True

    def test_evaluate_with_violations_not_mandatory(self) -> None:
        """Violations without mandatory_on_violation should not escalate."""
        policy = LifecyclePolicy(
            artifact_type="ProjectPlan",
            mandatory_on_violation=False,
        )
        artifact = self._make_artifact(age_days=30)

        result = policy.evaluate(artifact, violations=["error1", "error2"])

        # Should not add VIOLATION trigger when not mandatory_on_violation
        assert ReviewTrigger.VIOLATION not in result.triggers
        assert result.urgency == ReviewUrgency.INFORMATIONAL

    def test_evaluate_with_violations_mandatory(self) -> None:
        """Violations with mandatory_on_violation should be MANDATORY."""
        policy = LifecyclePolicy(
            artifact_type="ArchitecturePlan",
            mandatory_on_violation=True,
        )
        artifact = self._make_artifact(
            age_days=30,
            artifact_type=ArtifactType.ARCHITECTURE_PLAN,
        )

        result = policy.evaluate(artifact, violations=["arch violation"])

        assert ReviewTrigger.VIOLATION in result.triggers
        assert result.urgency == ReviewUrgency.MANDATORY
        assert result.blocks_work is True

    def test_evaluate_with_coverage_drift_below_threshold(self) -> None:
        """Coverage drift below threshold should not trigger."""
        policy = LifecyclePolicy(
            artifact_type="TestPlan",
            coverage_drift_threshold=10.0,
        )
        artifact = self._make_artifact(
            age_days=30,
            artifact_type=ArtifactType.TEST_PLAN,
        )

        result = policy.evaluate(artifact, coverage_drift=5.0)

        assert ReviewTrigger.DRIFT not in result.triggers
        assert result.urgency == ReviewUrgency.INFORMATIONAL

    def test_evaluate_with_coverage_drift_above_threshold(self) -> None:
        """Coverage drift above threshold should trigger REQUIRED."""
        policy = LifecyclePolicy(
            artifact_type="TestPlan",
            coverage_drift_threshold=10.0,
        )
        artifact = self._make_artifact(
            age_days=30,
            artifact_type=ArtifactType.TEST_PLAN,
        )

        result = policy.evaluate(artifact, coverage_drift=15.0)

        assert ReviewTrigger.DRIFT in result.triggers
        assert result.urgency == ReviewUrgency.REQUIRED

    def test_evaluate_urgency_escalation(self) -> None:
        """Violations should escalate urgency to MANDATORY even if already REQUIRED."""
        policy = LifecyclePolicy(
            artifact_type="ArchitecturePlan",
            review_after_months=3,
            mandatory_on_violation=True,
        )
        artifact = self._make_artifact(
            age_days=100,  # Past review date = REQUIRED
            artifact_type=ArtifactType.ARCHITECTURE_PLAN,
        )

        result = policy.evaluate(artifact, violations=["violation"])

        # Should escalate from REQUIRED to MANDATORY
        assert result.urgency == ReviewUrgency.MANDATORY
        assert ReviewTrigger.AGE in result.triggers
        assert ReviewTrigger.VIOLATION in result.triggers

    def test_evaluate_multiple_triggers(self) -> None:
        """Multiple conditions should create multiple triggers."""
        policy = LifecyclePolicy(
            artifact_type="TestPlan",
            review_after_months=3,
            coverage_drift_threshold=10.0,
        )
        artifact = self._make_artifact(
            age_days=100,  # Past review
            artifact_type=ArtifactType.TEST_PLAN,
        )

        result = policy.evaluate(artifact, coverage_drift=15.0)

        assert ReviewTrigger.AGE in result.triggers
        assert ReviewTrigger.DRIFT in result.triggers

    def test_to_dict(self) -> None:
        """to_dict should serialize all fields."""
        policy = LifecyclePolicy(
            artifact_type="TestPlan",
            review_after_months=3,
            warning_at_months=2,
            mandatory_on_violation=True,
            coverage_drift_threshold=10.0,
        )
        d = policy.to_dict()

        assert d["artifact_type"] == "TestPlan"
        assert d["review_after_months"] == 3
        assert d["warning_at_months"] == 2
        assert d["mandatory_on_violation"] is True
        assert d["coverage_drift_threshold"] == 10.0

    def test_default_warning_period(self) -> None:
        """Warning period should default to 1 month before review."""
        policy = LifecyclePolicy(
            artifact_type="ProjectPlan",
            review_after_months=3,
            # warning_at_months not set
        )
        # Artifact at 2.5 months should be in warning period (default: 2-3 months)
        artifact = self._make_artifact(age_days=76)  # ~2.5 months

        result = policy.evaluate(artifact)

        assert result.urgency == ReviewUrgency.RECOMMENDED
        assert ReviewTrigger.AGE in result.triggers


class TestDefaultPolicies:
    """Tests for default policy definitions."""

    def test_project_plan_defaults(self) -> None:
        """ProjectPlan should have 3 month review cycle."""
        policy = DEFAULT_POLICIES["ProjectPlan"]
        assert policy.review_after_months == 3
        assert policy.warning_at_months == 2

    def test_architecture_plan_defaults(self) -> None:
        """ArchitecturePlan should have 6 month cycle and mandatory on violation."""
        policy = DEFAULT_POLICIES["ArchitecturePlan"]
        assert policy.review_after_months == 6
        assert policy.mandatory_on_violation is True

    def test_test_plan_defaults(self) -> None:
        """TestPlan should have coverage drift threshold."""
        policy = DEFAULT_POLICIES["TestPlan"]
        assert policy.coverage_drift_threshold == 10.0

    def test_implementation_plan_defaults(self) -> None:
        """ImplementationPlan should have 6 month cycle."""
        policy = DEFAULT_POLICIES["ImplementationPlan"]
        assert policy.review_after_months == 6


class TestLifecycleConfig:
    """Tests for LifecycleConfig."""

    def test_default_creates_all_policies(self) -> None:
        """default() should create policies for all artifact types."""
        config = LifecycleConfig.default()

        assert "ProjectPlan" in config.policies
        assert "ArchitecturePlan" in config.policies
        assert "TestPlan" in config.policies
        assert "ImplementationPlan" in config.policies

    def test_get_policy_existing(self) -> None:
        """get_policy should return policy for existing type."""
        config = LifecycleConfig.default()
        policy = config.get_policy("ProjectPlan")

        assert policy is not None
        assert policy.artifact_type == "ProjectPlan"

    def test_get_policy_nonexistent(self) -> None:
        """get_policy should return None for unknown type."""
        config = LifecycleConfig.default()
        policy = config.get_policy("UnknownPlan")

        assert policy is None

    def test_to_dict(self) -> None:
        """to_dict should serialize config correctly."""
        config = LifecycleConfig.default()
        d = config.to_dict()

        assert "policies" in d
        assert "ProjectPlan" in d["policies"]
        assert d["policies"]["ProjectPlan"]["review_after_months"] == 3

    def test_from_file_missing_file(self, tmp_path: Path) -> None:
        """from_file should return defaults for missing file."""
        config = LifecycleConfig.from_file(str(tmp_path / "nonexistent.yaml"))

        assert "ProjectPlan" in config.policies
        assert config.policies["ProjectPlan"].review_after_months == 3

    def test_from_file_valid_yaml(self, tmp_path: Path) -> None:
        """from_file should parse valid YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "lifecycle": {
                        "policies": {
                            "ProjectPlan": {
                                "review_after_months": 6,
                                "warning_at_months": 5,
                            }
                        }
                    }
                }
            )
        )

        config = LifecycleConfig.from_file(str(config_file))

        assert config.policies["ProjectPlan"].review_after_months == 6
        assert config.policies["ProjectPlan"].warning_at_months == 5
        # Other defaults should still exist
        assert "ArchitecturePlan" in config.policies

    def test_from_file_partial_config(self, tmp_path: Path) -> None:
        """from_file should merge partial config with defaults."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "lifecycle": {
                        "policies": {
                            "ProjectPlan": {
                                "review_after_months": 6,
                                # warning_at_months not specified
                            }
                        }
                    }
                }
            )
        )

        config = LifecycleConfig.from_file(str(config_file))

        # Overridden value
        assert config.policies["ProjectPlan"].review_after_months == 6
        # Default value preserved
        assert config.policies["ProjectPlan"].warning_at_months == 2

    def test_from_file_invalid_yaml(self, tmp_path: Path) -> None:
        """from_file should return defaults for invalid YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("{ invalid yaml [")

        config = LifecycleConfig.from_file(str(config_file))

        # Should fall back to defaults
        assert "ProjectPlan" in config.policies

    def test_from_file_empty_file(self, tmp_path: Path) -> None:
        """from_file should return defaults for empty file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        config = LifecycleConfig.from_file(str(config_file))

        assert "ProjectPlan" in config.policies

    def test_from_file_new_artifact_type(self, tmp_path: Path) -> None:
        """from_file should allow adding new artifact types."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "lifecycle": {
                        "policies": {
                            "CustomPlan": {
                                "review_after_months": 12,
                                "mandatory_on_violation": True,
                            }
                        }
                    }
                }
            )
        )

        config = LifecycleConfig.from_file(str(config_file))

        assert "CustomPlan" in config.policies
        assert config.policies["CustomPlan"].review_after_months == 12
        assert config.policies["CustomPlan"].mandatory_on_violation is True
