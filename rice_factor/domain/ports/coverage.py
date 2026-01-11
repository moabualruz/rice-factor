"""Coverage monitoring port for test coverage tracking.

This module defines the port interface for coverage monitoring,
allowing the domain layer to interact with coverage tools.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rice_factor.domain.artifacts.envelope import ArtifactEnvelope


class CoverageError(Exception):
    """Raised when coverage operations fail."""


@dataclass
class CoverageResult:
    """Result of a coverage measurement.

    Attributes:
        percentage: Coverage percentage (0.0 to 100.0).
        lines_covered: Number of lines covered.
        lines_total: Total number of lines.
        branches_covered: Number of branches covered (optional).
        branches_total: Total number of branches (optional).
    """

    percentage: float
    lines_covered: int = 0
    lines_total: int = 0
    branches_covered: int | None = None
    branches_total: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "percentage": round(self.percentage, 2),
            "lines_covered": self.lines_covered,
            "lines_total": self.lines_total,
            "branches_covered": self.branches_covered,
            "branches_total": self.branches_total,
        }


@dataclass
class CoverageDriftResult:
    """Result of coverage drift calculation.

    Attributes:
        baseline: Baseline coverage percentage.
        current: Current coverage percentage.
        drift: Coverage drift (baseline - current).
               Positive = coverage decreased (bad).
               Negative = coverage increased (good).
        severity: Drift severity level.
        requires_review: Whether the drift triggers a review.
    """

    baseline: float
    current: float
    drift: float
    severity: str
    requires_review: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "baseline": round(self.baseline, 2),
            "current": round(self.current, 2),
            "drift": round(self.drift, 2),
            "severity": self.severity,
            "requires_review": self.requires_review,
        }


class CoverageMonitorPort(ABC):
    """Port for test coverage monitoring.

    This abstract base class defines the interface for coverage monitoring
    adapters. Implementations can use pytest-cov, coverage.py, or other
    coverage tools.
    """

    @abstractmethod
    def get_current_coverage(self) -> CoverageResult:
        """Get the current test coverage.

        Returns:
            CoverageResult with coverage details.

        Raises:
            CoverageError: If coverage measurement fails.
        """
        ...

    @abstractmethod
    def get_baseline_coverage(
        self,
        test_plan: ArtifactEnvelope[Any],
    ) -> float:
        """Get baseline coverage from a TestPlan.

        Args:
            test_plan: The TestPlan artifact.

        Returns:
            Baseline coverage percentage, or 0.0 if not set.
        """
        ...

    @abstractmethod
    def calculate_drift(
        self,
        test_plan: ArtifactEnvelope[Any],
    ) -> CoverageDriftResult:
        """Calculate coverage drift from baseline.

        Args:
            test_plan: The TestPlan artifact with baseline.

        Returns:
            CoverageDriftResult with drift details.

        Raises:
            CoverageError: If coverage measurement fails.
        """
        ...

    @abstractmethod
    def update_baseline(
        self,
        test_plan: ArtifactEnvelope[Any],
        coverage: float,
    ) -> None:
        """Update baseline coverage in a TestPlan.

        Args:
            test_plan: The TestPlan artifact to update.
            coverage: The new baseline coverage percentage.
        """
        ...

    def get_drift_severity(self, drift: float, threshold: float = 10.0) -> str:
        """Get severity level for a drift value.

        Args:
            drift: Coverage drift percentage.
            threshold: Threshold for triggering review.

        Returns:
            Severity level: 'ok', 'info', 'warning', 'critical'.
        """
        if drift <= 0:
            return "ok"  # Coverage increased or unchanged
        elif drift < threshold / 2:
            return "info"  # Minor variance
        elif drift < threshold:
            return "warning"  # Noticeable decline
        else:
            return "critical"  # Major coverage loss
