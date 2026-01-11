"""CI validation adapters.

This module provides validator implementations for CI pipeline stages:
- ArtifactValidationAdapter: Stage 1 - validates artifact status and schema
- ApprovalVerificationAdapter: Stage 2 - verifies all artifacts are approved
- InvariantEnforcementAdapter: Stage 3 - enforces test locks and architecture rules
- AuditVerificationAdapter: Stage 5 - verifies audit trail integrity
"""

from rice_factor.adapters.ci.approval_verifier import ApprovalVerificationAdapter
from rice_factor.adapters.ci.artifact_validator import ArtifactValidationAdapter
from rice_factor.adapters.ci.audit_verifier import AuditVerificationAdapter
from rice_factor.adapters.ci.invariant_enforcer import InvariantEnforcementAdapter

__all__ = [
    "ApprovalVerificationAdapter",
    "ArtifactValidationAdapter",
    "AuditVerificationAdapter",
    "InvariantEnforcementAdapter",
]
