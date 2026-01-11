"""Lifecycle service for artifact management.

This module provides the LifecycleService for managing artifact lifecycles,
including age tracking, policy evaluation, and review prompts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol

from rice_factor.domain.models.lifecycle import (
    LifecycleConfig,
    LifecyclePolicy,
    PolicyResult,
    ReviewTrigger,
    ReviewUrgency,
)

if TYPE_CHECKING:
    from rice_factor.domain.artifacts.envelope import ArtifactEnvelope


class StoragePort(Protocol):
    """Protocol for artifact storage operations."""

    def list_all(self) -> list[ArtifactEnvelope[Any]]:
        """List all artifacts."""
        ...

    def load(self, artifact_id: str) -> ArtifactEnvelope[Any]:
        """Load an artifact by ID."""
        ...

    def save(self, artifact: ArtifactEnvelope[Any]) -> None:
        """Save an artifact."""
        ...


class ArchitectureValidatorPort(Protocol):
    """Protocol for architecture validation."""

    def check_violations(
        self,
        arch_plan: ArtifactEnvelope[Any],
    ) -> list[Any]:
        """Check code against architecture rules."""
        ...


class CoverageMonitorPort(Protocol):
    """Protocol for coverage monitoring."""

    def calculate_drift(
        self,
        test_plan: ArtifactEnvelope[Any],
    ) -> float:
        """Calculate coverage drift percentage."""
        ...


class LifecycleBlockingError(Exception):
    """Raised when work is blocked due to lifecycle issues."""

    def __init__(self, blocking_issues: list[PolicyResult]) -> None:
        self.blocking_issues = blocking_issues
        messages = [
            f"{issue.artifact_type} ({issue.artifact_id[:8]}...): {issue.urgency.value}"
            for issue in blocking_issues
        ]
        super().__init__(f"Lifecycle issues block work: {'; '.join(messages)}")


@dataclass
class ReviewPrompt:
    """A review prompt for an artifact."""

    artifact_id: str
    artifact_type: str
    urgency: ReviewUrgency
    message: str
    actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "urgency": self.urgency.value,
            "message": self.message,
            "actions": self.actions,
        }


@dataclass
class AgeReport:
    """Report on artifact ages and policy status."""

    generated_at: datetime
    total_artifacts: int
    requiring_action: list[PolicyResult]
    blocking: list[PolicyResult]
    healthy: list[PolicyResult]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "total_artifacts": self.total_artifacts,
            "requiring_action_count": len(self.requiring_action),
            "blocking_count": len(self.blocking),
            "healthy_count": len(self.healthy),
            "requiring_action": [r.to_dict() for r in self.requiring_action],
            "blocking": [r.to_dict() for r in self.blocking],
            "healthy": [r.to_dict() for r in self.healthy],
        }


@dataclass
class LifecycleService:
    """Service for managing artifact lifecycles.

    This service evaluates artifacts against their lifecycle policies,
    generates review prompts, and can block work when mandatory reviews
    are pending.
    """

    artifact_store: StoragePort
    config: LifecycleConfig = field(default_factory=LifecycleConfig.default)
    arch_validator: ArchitectureValidatorPort | None = None
    coverage_monitor: CoverageMonitorPort | None = None

    @property
    def policies(self) -> dict[str, LifecyclePolicy]:
        """Get policies from config."""
        return self.config.policies

    def evaluate_artifact(
        self,
        artifact: ArtifactEnvelope[Any],
        violations: list[Any] | None = None,
        coverage_drift: float | None = None,
    ) -> PolicyResult | None:
        """Evaluate a single artifact against its policy.

        Args:
            artifact: The artifact to evaluate.
            violations: Any violations for this artifact.
            coverage_drift: Coverage drift percentage (for TestPlan).

        Returns:
            PolicyResult if a policy exists, None otherwise.
        """
        artifact_type = str(artifact.artifact_type.value)
        policy = self.policies.get(artifact_type)
        if policy is None:
            return None

        return policy.evaluate(artifact, violations, coverage_drift)

    def evaluate_all(self) -> list[PolicyResult]:
        """Evaluate all artifacts against their policies.

        Returns:
            List of PolicyResult for all artifacts.
        """
        results: list[PolicyResult] = []

        for artifact in self.artifact_store.list_all():
            artifact_type = str(artifact.artifact_type.value)
            policy = self.policies.get(artifact_type)
            if policy is None:
                continue

            # Get violations for ArchitecturePlan
            violations = None
            if artifact_type == "ArchitecturePlan" and self.arch_validator:
                violations = self.arch_validator.check_violations(artifact)

            # Get coverage drift for TestPlan
            coverage_drift = None
            if artifact_type == "TestPlan" and self.coverage_monitor:
                coverage_drift = self.coverage_monitor.calculate_drift(artifact)

            result = policy.evaluate(artifact, violations, coverage_drift)
            results.append(result)

        return results

    def get_blocking_issues(self) -> list[PolicyResult]:
        """Get issues that block further work.

        Returns:
            List of PolicyResult with MANDATORY urgency.
        """
        return [r for r in self.evaluate_all() if r.blocks_work]

    def check_can_proceed(self) -> tuple[bool, list[PolicyResult]]:
        """Check if new work can proceed.

        Returns:
            Tuple of (can_proceed, blocking_issues).
        """
        blocking = self.get_blocking_issues()
        return len(blocking) == 0, blocking

    def require_can_proceed(self) -> None:
        """Require that work can proceed.

        Raises:
            LifecycleBlockingError: If there are blocking issues.
        """
        can_proceed, blocking = self.check_can_proceed()
        if not can_proceed:
            raise LifecycleBlockingError(blocking)

    def generate_prompts(self) -> list[ReviewPrompt]:
        """Generate review prompts for artifacts needing attention.

        Returns:
            List of ReviewPrompt for artifacts with triggers.
        """
        prompts: list[ReviewPrompt] = []
        results = self.evaluate_all()

        for result in results:
            if not result.triggers:
                continue

            prompt = ReviewPrompt(
                artifact_id=result.artifact_id,
                artifact_type=result.artifact_type,
                urgency=result.urgency,
                message=self._format_message(result),
                actions=self._suggested_actions(result),
            )
            prompts.append(prompt)

        return prompts

    def _format_message(self, result: PolicyResult) -> str:
        """Format a review message for a policy result.

        Args:
            result: The policy result.

        Returns:
            Formatted message string.
        """
        artifact_desc = f"{result.artifact_type} ({result.artifact_id[:8]}...)"
        age_str = f"{result.age_months:.1f} months old"

        if result.urgency == ReviewUrgency.MANDATORY:
            if ReviewTrigger.VIOLATION in result.triggers:
                return f"BLOCKING: {artifact_desc} has {len(result.violations)} violation(s) - review required"
            return f"BLOCKING: {artifact_desc} must be reviewed before proceeding"

        if result.urgency == ReviewUrgency.REQUIRED:
            reasons = []
            if ReviewTrigger.AGE in result.triggers:
                reasons.append(f"age: {age_str}")
            if ReviewTrigger.DRIFT in result.triggers:
                reasons.append(f"coverage drift: {result.coverage_drift:.1f}%")
            reason_str = ", ".join(reasons)
            return f"Review required: {artifact_desc} ({reason_str})"

        if result.urgency == ReviewUrgency.RECOMMENDED:
            return f"{artifact_desc} should be reviewed soon ({age_str})"

        return f"FYI: {artifact_desc} is {age_str}"

    def _suggested_actions(self, result: PolicyResult) -> list[str]:
        """Generate suggested actions for a policy result.

        Args:
            result: The policy result.

        Returns:
            List of suggested action strings.
        """
        actions = []

        if result.blocks_work:
            if ReviewTrigger.VIOLATION in result.triggers:
                actions.append("Fix architecture violations")
            actions.append(f"Run: rice-factor artifact review {result.artifact_id[:8]}...")

        elif result.requires_action:
            actions.append(f"Review artifact: {result.artifact_id[:8]}...")
            actions.append("Consider: rice-factor artifact extend --reason 'Still accurate'")

        else:
            actions.append("No immediate action required")

        return actions

    def generate_age_report(self) -> AgeReport:
        """Generate a comprehensive age report.

        Returns:
            AgeReport with all evaluation results.
        """
        results = self.evaluate_all()

        return AgeReport(
            generated_at=datetime.now(UTC),
            total_artifacts=len(results),
            requiring_action=[r for r in results if r.requires_action],
            blocking=[r for r in results if r.blocks_work],
            healthy=[r for r in results if not r.requires_action],
        )

    def record_review(
        self,
        artifact_id: str,
        notes: str | None = None,
    ) -> ArtifactEnvelope[Any]:
        """Record that an artifact was reviewed.

        Args:
            artifact_id: ID of the artifact to mark as reviewed.
            notes: Optional review notes.

        Returns:
            The updated artifact.
        """
        artifact = self.artifact_store.load(artifact_id)
        artifact.last_reviewed_at = datetime.now(UTC)
        artifact.review_notes = notes
        self.artifact_store.save(artifact)
        return artifact

    def extend_artifact(
        self,
        artifact_id: str,
        months: int,
        reason: str,
    ) -> ArtifactEnvelope[Any]:
        """Extend an artifact's validity period.

        This is essentially the same as recording a review with a reason,
        but semantically indicates the artifact is being extended rather
        than fully reviewed.

        Args:
            artifact_id: ID of the artifact to extend.
            months: Number of months to extend (for logging).
            reason: Reason for extension.

        Returns:
            The updated artifact.
        """
        notes = f"Extended for {months} months: {reason}"
        return self.record_review(artifact_id, notes)
