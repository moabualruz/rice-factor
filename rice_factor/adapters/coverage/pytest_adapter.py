"""Pytest coverage adapter for coverage monitoring.

This module provides a coverage adapter that uses pytest-cov
to measure test coverage.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from rice_factor.domain.ports.coverage import (
    CoverageDriftResult,
    CoverageError,
    CoverageMonitorPort,
    CoverageResult,
)

if TYPE_CHECKING:
    from pathlib import Path

    from rice_factor.domain.artifacts.envelope import ArtifactEnvelope


class PytestCoverageAdapter(CoverageMonitorPort):
    """Coverage adapter using pytest-cov.

    This adapter runs pytest with coverage measurement and parses
    the JSON coverage report to extract coverage metrics.
    """

    def __init__(
        self,
        project_root: Path,
        source_dir: str = "rice_factor",
        coverage_threshold: float = 10.0,
    ) -> None:
        """Initialize the adapter.

        Args:
            project_root: Path to the project root.
            source_dir: Source directory to measure coverage for.
            coverage_threshold: Drift threshold for triggering review.
        """
        self.project_root = project_root
        self.source_dir = source_dir
        self.coverage_threshold = coverage_threshold
        self.coverage_file = project_root / "coverage.json"

    def get_current_coverage(self) -> CoverageResult:
        """Run tests with coverage and return the result.

        Returns:
            CoverageResult with coverage details.

        Raises:
            CoverageError: If coverage measurement fails.
        """
        try:
            result = subprocess.run(
                [
                    "pytest",
                    f"--cov={self.source_dir}",
                    "--cov-report=json",
                    "-q",
                    "--tb=no",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
        except subprocess.TimeoutExpired as e:
            raise CoverageError("Coverage measurement timed out") from e
        except FileNotFoundError as e:
            raise CoverageError("pytest not found - is it installed?") from e

        if not self.coverage_file.exists():
            raise CoverageError(
                f"Coverage report not generated at {self.coverage_file}. "
                f"Exit code: {result.returncode}. "
                f"Stderr: {result.stderr[:500] if result.stderr else 'none'}"
            )

        try:
            with self.coverage_file.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CoverageError(f"Invalid coverage JSON: {e}") from e

        totals = data.get("totals", {})
        return CoverageResult(
            percentage=totals.get("percent_covered", 0.0),
            lines_covered=totals.get("covered_lines", 0),
            lines_total=totals.get("num_statements", 0),
            branches_covered=totals.get("covered_branches"),
            branches_total=totals.get("num_branches"),
        )

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
        payload = test_plan.payload
        if isinstance(payload, dict):
            return float(payload.get("baseline_coverage", 0.0))
        elif hasattr(payload, "baseline_coverage"):
            return float(getattr(payload, "baseline_coverage", 0.0) or 0.0)
        return 0.0

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
        baseline = self.get_baseline_coverage(test_plan)

        # Handle case where no baseline is set
        if baseline == 0.0:
            return CoverageDriftResult(
                baseline=0.0,
                current=0.0,
                drift=0.0,
                severity="ok",
                requires_review=False,
            )

        result = self.get_current_coverage()
        current = result.percentage
        drift = baseline - current

        severity = self.get_drift_severity(drift, self.coverage_threshold)
        requires_review = drift >= self.coverage_threshold

        return CoverageDriftResult(
            baseline=baseline,
            current=current,
            drift=drift,
            severity=severity,
            requires_review=requires_review,
        )

    def update_baseline(
        self,
        test_plan: ArtifactEnvelope[Any],
        coverage: float,
    ) -> None:
        """Update baseline coverage in a TestPlan.

        Note: This modifies the artifact in-place. The caller is
        responsible for saving the artifact.

        Args:
            test_plan: The TestPlan artifact to update.
            coverage: The new baseline coverage percentage.
        """
        payload = test_plan.payload
        if isinstance(payload, dict):
            payload["baseline_coverage"] = coverage
            payload["baseline_recorded_at"] = datetime.now(UTC).isoformat()
        elif hasattr(payload, "__dict__"):
            payload.baseline_coverage = coverage
            payload.baseline_recorded_at = datetime.now(UTC).isoformat()

    def calculate_drift_simple(self, baseline: float, current: float) -> float:
        """Calculate simple drift percentage.

        Args:
            baseline: Baseline coverage percentage.
            current: Current coverage percentage.

        Returns:
            Drift value (positive = coverage decreased).
        """
        return baseline - current


class MockCoverageAdapter(CoverageMonitorPort):
    """Mock coverage adapter for testing.

    This adapter allows setting coverage values programmatically
    instead of actually running tests.
    """

    def __init__(
        self,
        current_coverage: float = 85.0,
        coverage_threshold: float = 10.0,
    ) -> None:
        """Initialize the mock adapter.

        Args:
            current_coverage: The coverage value to return.
            coverage_threshold: Drift threshold for triggering review.
        """
        self._current_coverage = current_coverage
        self.coverage_threshold = coverage_threshold

    def set_current_coverage(self, coverage: float) -> None:
        """Set the current coverage value.

        Args:
            coverage: The coverage percentage to return.
        """
        self._current_coverage = coverage

    def get_current_coverage(self) -> CoverageResult:
        """Get the configured coverage value."""
        return CoverageResult(
            percentage=self._current_coverage,
            lines_covered=int(self._current_coverage * 10),
            lines_total=1000,
        )

    def get_baseline_coverage(
        self,
        test_plan: ArtifactEnvelope[Any],
    ) -> float:
        """Get baseline from payload."""
        payload = test_plan.payload
        if isinstance(payload, dict):
            return float(payload.get("baseline_coverage", 0.0))
        return 0.0

    def calculate_drift(
        self,
        test_plan: ArtifactEnvelope[Any],
    ) -> CoverageDriftResult:
        """Calculate drift using mock values."""
        baseline = self.get_baseline_coverage(test_plan)

        if baseline == 0.0:
            return CoverageDriftResult(
                baseline=0.0,
                current=self._current_coverage,
                drift=0.0,
                severity="ok",
                requires_review=False,
            )

        drift = baseline - self._current_coverage
        severity = self.get_drift_severity(drift, self.coverage_threshold)
        requires_review = drift >= self.coverage_threshold

        return CoverageDriftResult(
            baseline=baseline,
            current=self._current_coverage,
            drift=drift,
            severity=severity,
            requires_review=requires_review,
        )

    def update_baseline(
        self,
        test_plan: ArtifactEnvelope[Any],
        coverage: float,
    ) -> None:
        """Update baseline in payload."""
        payload = test_plan.payload
        if isinstance(payload, dict):
            payload["baseline_coverage"] = coverage
            payload["baseline_recorded_at"] = datetime.now(UTC).isoformat()
