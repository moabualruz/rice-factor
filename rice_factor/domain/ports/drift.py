"""Drift detection port definitions.

This module provides the protocol interface for drift detection operations.
"""

from pathlib import Path
from typing import Protocol

from rice_factor.domain.drift.models import DriftReport, DriftSignal


class DriftDetectorPort(Protocol):
    """Port for drift detection operations.

    This protocol defines the interface for detecting drift between
    code and artifacts in a project.
    """

    def detect_orphan_code(self, code_dir: Path) -> list[DriftSignal]:
        """Find code files not covered by any plan.

        Args:
            code_dir: Directory to scan for code files.

        Returns:
            List of drift signals for orphaned code.
        """
        ...

    def detect_orphan_plans(self, repo_root: Path) -> list[DriftSignal]:
        """Find plans targeting non-existent code.

        Args:
            repo_root: Root directory of the repository.

        Returns:
            List of drift signals for orphaned plans.
        """
        ...

    def detect_undocumented_behavior(self, repo_root: Path) -> list[DriftSignal]:
        """Find tests covering behavior not in requirements.

        Args:
            repo_root: Root directory of the repository.

        Returns:
            List of drift signals for undocumented behavior.
        """
        ...

    def detect_refactor_hotspots(
        self,
        repo_root: Path,
        threshold: int = 3,
        window_days: int = 30,
    ) -> list[DriftSignal]:
        """Find frequently refactored areas.

        Args:
            repo_root: Root directory of the repository.
            threshold: Number of refactors to trigger signal.
            window_days: Lookback period in days.

        Returns:
            List of drift signals for refactor hotspots.
        """
        ...

    def full_analysis(self, repo_root: Path) -> DriftReport:
        """Run complete drift analysis.

        Args:
            repo_root: Root directory of the repository.

        Returns:
            Complete drift analysis report.
        """
        ...
