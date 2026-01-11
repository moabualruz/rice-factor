"""CI domain models.

This module provides the data models for CI pipeline results, failures,
and stage outcomes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from rice_factor.domain.ci.failure_codes import CIFailureCode


class CIStage(str, Enum):
    """CI pipeline stages."""

    ARTIFACT_VALIDATION = "artifact_validation"
    APPROVAL_VERIFICATION = "approval_verification"
    INVARIANT_ENFORCEMENT = "invariant_enforcement"
    TEST_EXECUTION = "test_execution"
    AUDIT_VERIFICATION = "audit_verification"


@dataclass(frozen=True)
class CIFailure:
    """A single CI validation failure.

    Attributes:
        code: The failure code from CIFailureCode enum.
        message: Human-readable failure description.
        file_path: Path to the file that caused the failure (if applicable).
        remediation: Guidance on how to fix the failure.
        details: Additional context about the failure.
    """

    code: CIFailureCode
    message: str
    file_path: Path | None = None
    remediation: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code.value,
            "message": self.message,
            "file_path": str(self.file_path) if self.file_path else None,
            "remediation": self.remediation or self.code.remediation,
            "details": self.details,
        }


@dataclass
class CIStageResult:
    """Result of a single CI pipeline stage.

    Attributes:
        stage: The stage that was executed.
        passed: Whether the stage passed (no failures).
        failures: List of failures found during this stage.
        duration_ms: Time taken to execute this stage in milliseconds.
        skipped: Whether this stage was skipped.
        skip_reason: Reason the stage was skipped (if skipped).
    """

    stage: CIStage
    passed: bool
    failures: list[CIFailure] = field(default_factory=list)
    duration_ms: float = 0.0
    skipped: bool = False
    skip_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "stage": self.stage.value,
            "passed": self.passed,
            "failures": [f.to_dict() for f in self.failures],
            "duration_ms": self.duration_ms,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }


@dataclass
class CIPipelineResult:
    """Aggregate result of the entire CI pipeline.

    Attributes:
        passed: Whether all stages passed.
        stage_results: Results from each stage.
        total_duration_ms: Total time for all stages.
        timestamp: When the pipeline was run.
        repo_root: Root directory of the repository.
        branch: Git branch being validated (if available).
        commit: Git commit SHA being validated (if available).
    """

    passed: bool
    stage_results: list[CIStageResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    repo_root: Path | None = None
    branch: str | None = None
    commit: str | None = None

    @property
    def failure_count(self) -> int:
        """Total number of failures across all stages."""
        return sum(len(r.failures) for r in self.stage_results)

    @property
    def all_failures(self) -> list[CIFailure]:
        """All failures from all stages."""
        failures = []
        for result in self.stage_results:
            failures.extend(result.failures)
        return failures

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "stage_results": [r.to_dict() for r in self.stage_results],
            "total_duration_ms": self.total_duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "repo_root": str(self.repo_root) if self.repo_root else None,
            "branch": self.branch,
            "commit": self.commit,
            "summary": {
                "total_failures": self.failure_count,
                "stages_passed": sum(1 for r in self.stage_results if r.passed),
                "stages_failed": sum(1 for r in self.stage_results if not r.passed),
                "stages_skipped": sum(1 for r in self.stage_results if r.skipped),
            },
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json

        return json.dumps(self.to_dict(), indent=2)

    def format_summary(self) -> str:
        """Format a human-readable summary of the pipeline result."""
        lines = []

        # Header
        status = "PASSED" if self.passed else "FAILED"
        lines.append(f"CI Pipeline: {status}")
        lines.append("")

        # Stage summary
        lines.append("Stage Results:")
        for result in self.stage_results:
            if result.skipped:
                status_icon = "⊘"
                status_text = f"SKIPPED ({result.skip_reason})"
            elif result.passed:
                status_icon = "✓"
                status_text = "PASSED"
            else:
                status_icon = "✗"
                status_text = f"FAILED ({len(result.failures)} failures)"

            lines.append(f"  {status_icon} {result.stage.value}: {status_text}")

        # Failures detail
        if self.failure_count > 0:
            lines.append("")
            lines.append(f"Failures ({self.failure_count} total):")
            for result in self.stage_results:
                for failure in result.failures:
                    lines.append(f"  [{failure.code.value}] {failure.message}")
                    if failure.file_path:
                        lines.append(f"    File: {failure.file_path}")
                    remediation = failure.remediation or failure.code.remediation
                    lines.append(f"    Remediation: {remediation}")

        # Duration
        lines.append("")
        lines.append(f"Total Duration: {self.total_duration_ms:.0f}ms")

        return "\n".join(lines)
