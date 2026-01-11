"""CI/CD integration domain models and services.

This module provides CI pipeline validation capabilities for ensuring
artifacts, approvals, invariants, and audit trails are correct before
code merges.

The CI acts as a "guardian" - it never generates artifacts, only verifies,
enforces, rejects, and records.
"""

from rice_factor.domain.ci.failure_codes import CIFailureCategory, CIFailureCode
from rice_factor.domain.ci.models import (
    CIFailure,
    CIPipelineResult,
    CIStage,
    CIStageResult,
)
from rice_factor.domain.ci.pipeline import CIPipeline, CIPipelineConfig

__all__ = [
    "CIFailure",
    "CIFailureCategory",
    "CIFailureCode",
    "CIPipeline",
    "CIPipelineConfig",
    "CIPipelineResult",
    "CIStage",
    "CIStageResult",
]
