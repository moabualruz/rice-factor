"""Lifecycle policy models for artifact management.

This module provides models for artifact lifecycle management:
- LifecyclePolicy: Configurable policy per artifact type
- PolicyResult: Result of policy evaluation
- ReviewTrigger: What triggers a review requirement
- ReviewUrgency: How urgent is the review
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rice_factor.domain.artifacts.envelope import ArtifactEnvelope


class ReviewTrigger(str, Enum):
    """What triggers a review requirement."""

    AGE = "age"  # Time-based
    VIOLATION = "violation"  # Rule violation
    DRIFT = "drift"  # Coverage/content drift
    MANUAL = "manual"  # User-initiated


class ReviewUrgency(str, Enum):
    """How urgent is the review."""

    INFORMATIONAL = "informational"  # FYI, no action required
    RECOMMENDED = "recommended"  # Should review soon
    REQUIRED = "required"  # Must review before proceeding
    MANDATORY = "mandatory"  # Blocks all work until reviewed


@dataclass
class PolicyResult:
    """Result of policy evaluation."""

    artifact_id: str
    artifact_type: str
    triggers: list[ReviewTrigger]
    urgency: ReviewUrgency
    age_months: float
    violations: list[Any]
    coverage_drift: float | None

    @property
    def requires_action(self) -> bool:
        """Check if this result requires user action."""
        return self.urgency in (ReviewUrgency.REQUIRED, ReviewUrgency.MANDATORY)

    @property
    def blocks_work(self) -> bool:
        """Check if this result blocks further work."""
        return self.urgency == ReviewUrgency.MANDATORY

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "triggers": [t.value for t in self.triggers],
            "urgency": self.urgency.value,
            "age_months": round(self.age_months, 2),
            "violations": self.violations,
            "coverage_drift": self.coverage_drift,
            "requires_action": self.requires_action,
            "blocks_work": self.blocks_work,
        }


@dataclass
class LifecyclePolicy:
    """Policy for artifact lifecycle management.

    Attributes:
        artifact_type: The artifact type this policy applies to.
        review_after_months: Months after which review is required.
        warning_at_months: Months at which to show warning (default: 1 month before review).
        mandatory_on_violation: If True, violations make review mandatory.
        coverage_drift_threshold: Percentage drift that triggers review (for TestPlan).
    """

    artifact_type: str
    review_after_months: int = 3
    warning_at_months: int | None = None  # None = 1 month before review
    mandatory_on_violation: bool = False
    coverage_drift_threshold: float | None = None  # Percent

    def evaluate(
        self,
        artifact: ArtifactEnvelope[Any],
        violations: list[Any] | None = None,
        coverage_drift: float | None = None,
    ) -> PolicyResult:
        """Evaluate an artifact against this policy.

        Args:
            artifact: The artifact to evaluate.
            violations: List of violations for this artifact (if any).
            coverage_drift: Coverage drift percentage (for TestPlan).

        Returns:
            PolicyResult with evaluation details.
        """
        triggers: list[ReviewTrigger] = []
        urgency = ReviewUrgency.INFORMATIONAL

        # Check age
        if artifact.age_months >= self.review_after_months:
            triggers.append(ReviewTrigger.AGE)
            urgency = ReviewUrgency.REQUIRED
        elif self._in_warning_period(artifact):
            triggers.append(ReviewTrigger.AGE)
            urgency = ReviewUrgency.RECOMMENDED

        # Check violations
        if violations and self.mandatory_on_violation:
            triggers.append(ReviewTrigger.VIOLATION)
            urgency = ReviewUrgency.MANDATORY

        # Check coverage drift
        if (
            coverage_drift is not None
            and self.coverage_drift_threshold is not None
            and coverage_drift >= self.coverage_drift_threshold
        ):
            triggers.append(ReviewTrigger.DRIFT)
            if urgency != ReviewUrgency.MANDATORY:
                urgency = ReviewUrgency.REQUIRED

        return PolicyResult(
            artifact_id=str(artifact.id),
            artifact_type=str(artifact.artifact_type.value),
            triggers=triggers,
            urgency=urgency,
            age_months=artifact.age_months,
            violations=violations or [],
            coverage_drift=coverage_drift,
        )

    def _in_warning_period(self, artifact: ArtifactEnvelope[Any]) -> bool:
        """Check if artifact is in the warning period.

        Args:
            artifact: The artifact to check.

        Returns:
            True if in warning period, False otherwise.
        """
        warning = self.warning_at_months
        if warning is None:
            warning = self.review_after_months - 1
        return warning <= artifact.age_months < self.review_after_months

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "artifact_type": self.artifact_type,
            "review_after_months": self.review_after_months,
            "warning_at_months": self.warning_at_months,
            "mandatory_on_violation": self.mandatory_on_violation,
            "coverage_drift_threshold": self.coverage_drift_threshold,
        }


# Default policies per artifact type (from spec 5.5.3)
DEFAULT_POLICIES: dict[str, LifecyclePolicy] = {
    "ProjectPlan": LifecyclePolicy(
        artifact_type="ProjectPlan",
        review_after_months=3,
        warning_at_months=2,
    ),
    "ArchitecturePlan": LifecyclePolicy(
        artifact_type="ArchitecturePlan",
        review_after_months=6,
        warning_at_months=5,
        mandatory_on_violation=True,
    ),
    "TestPlan": LifecyclePolicy(
        artifact_type="TestPlan",
        review_after_months=3,
        warning_at_months=2,
        coverage_drift_threshold=10.0,
    ),
    "ImplementationPlan": LifecyclePolicy(
        artifact_type="ImplementationPlan",
        review_after_months=6,
        warning_at_months=5,
    ),
    "ScaffoldPlan": LifecyclePolicy(
        artifact_type="ScaffoldPlan",
        review_after_months=6,
        warning_at_months=5,
    ),
    "RefactorPlan": LifecyclePolicy(
        artifact_type="RefactorPlan",
        review_after_months=3,
        warning_at_months=2,
    ),
    "ValidationResult": LifecyclePolicy(
        artifact_type="ValidationResult",
        review_after_months=1,
        warning_at_months=0,
    ),
}


@dataclass
class LifecycleConfig:
    """Configuration for artifact lifecycle management."""

    policies: dict[str, LifecyclePolicy] = field(default_factory=dict)

    @classmethod
    def default(cls) -> LifecycleConfig:
        """Create config with default policies."""
        return cls(policies=DEFAULT_POLICIES.copy())

    @classmethod
    def from_file(cls, path: str) -> LifecycleConfig:
        """Load configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            LifecycleConfig with policies from file merged with defaults.
        """
        from pathlib import Path

        config_path = Path(path)
        if not config_path.exists():
            return cls.default()

        try:
            import yaml
        except ImportError:
            return cls.default()

        try:
            with config_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except (OSError, yaml.YAMLError):
            return cls.default()

        if not data or not isinstance(data, dict):
            return cls.default()

        # Start with defaults
        policies = DEFAULT_POLICIES.copy()

        # Merge in config values
        lifecycle_data = data.get("lifecycle", {})
        if isinstance(lifecycle_data, dict):
            policies_data = lifecycle_data.get("policies", {})
            if isinstance(policies_data, dict):
                for artifact_type, policy_data in policies_data.items():
                    if not isinstance(policy_data, dict):
                        continue

                    # Build policy from config + defaults
                    default = policies.get(artifact_type)
                    if default:
                        policies[artifact_type] = LifecyclePolicy(
                            artifact_type=artifact_type,
                            review_after_months=policy_data.get(
                                "review_after_months", default.review_after_months
                            ),
                            warning_at_months=policy_data.get(
                                "warning_at_months", default.warning_at_months
                            ),
                            mandatory_on_violation=policy_data.get(
                                "mandatory_on_violation", default.mandatory_on_violation
                            ),
                            coverage_drift_threshold=policy_data.get(
                                "coverage_drift_threshold",
                                default.coverage_drift_threshold,
                            ),
                        )
                    else:
                        # New artifact type not in defaults
                        policies[artifact_type] = LifecyclePolicy(
                            artifact_type=artifact_type,
                            **policy_data,
                        )

        return cls(policies=policies)

    def get_policy(self, artifact_type: str) -> LifecyclePolicy | None:
        """Get policy for an artifact type.

        Args:
            artifact_type: The artifact type to get policy for.

        Returns:
            The policy, or None if no policy exists.
        """
        return self.policies.get(artifact_type)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "policies": {
                name: policy.to_dict() for name, policy in self.policies.items()
            }
        }
