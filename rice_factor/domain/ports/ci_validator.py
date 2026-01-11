"""CI Validator Port.

This module defines the protocol interface for CI validation stages.
Each CI stage (artifact validation, approval verification, etc.) implements
this protocol.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from rice_factor.domain.ci.models import CIStageResult


@runtime_checkable
class CIValidatorPort(Protocol):
    """Protocol for CI validation stages.

    Each stage in the CI pipeline implements this protocol to provide
    a consistent interface for the pipeline orchestrator.

    The CI acts as a "guardian" - it only verifies, enforces, rejects,
    and records. It never generates or modifies artifacts.
    """

    @property
    def stage_name(self) -> str:
        """Return the human-readable name of this validation stage."""
        ...

    def validate(self, repo_root: Path) -> CIStageResult:
        """Run validation for this stage.

        Args:
            repo_root: Path to the repository root directory.

        Returns:
            CIStageResult with pass/fail status and any failures found.
        """
        ...
