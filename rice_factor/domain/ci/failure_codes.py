"""CI failure code taxonomy.

This module defines the canonical set of CI failure codes used to classify
validation failures in the CI pipeline. Each code has a category, description,
and remediation guidance.
"""

from enum import Enum


class CIFailureCategory(str, Enum):
    """Categories of CI failure codes."""

    ARTIFACT = "artifact"
    APPROVAL = "approval"
    INVARIANT = "invariant"
    AUDIT = "audit"


class CIFailureCode(str, Enum):
    """Canonical CI failure codes.

    Each code represents a specific type of CI validation failure.
    Codes are grouped by category (artifact, approval, invariant, audit).

    Attributes:
        value: The failure code string (e.g., "DRAFT_ARTIFACT_PRESENT").
    """

    # Artifact validation failures (Stage 1)
    DRAFT_ARTIFACT_PRESENT = "DRAFT_ARTIFACT_PRESENT"
    LOCKED_ARTIFACT_MODIFIED = "LOCKED_ARTIFACT_MODIFIED"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    ARTIFACT_HASH_MISMATCH = "ARTIFACT_HASH_MISMATCH"

    # Approval verification failures (Stage 2)
    ARTIFACT_NOT_APPROVED = "ARTIFACT_NOT_APPROVED"
    APPROVAL_METADATA_MISSING = "APPROVAL_METADATA_MISSING"
    APPROVAL_EXPIRED = "APPROVAL_EXPIRED"

    # Invariant enforcement failures (Stage 3/4)
    TEST_MODIFICATION_AFTER_LOCK = "TEST_MODIFICATION_AFTER_LOCK"
    UNPLANNED_CODE_CHANGE = "UNPLANNED_CODE_CHANGE"
    ARCHITECTURE_VIOLATION = "ARCHITECTURE_VIOLATION"
    TEST_FAILURE = "TEST_FAILURE"
    LINT_FAILURE = "LINT_FAILURE"
    ORPHANED_CODE_CHANGE = "ORPHANED_CODE_CHANGE"

    # Audit verification failures (Stage 5)
    AUDIT_INTEGRITY_VIOLATION = "AUDIT_INTEGRITY_VIOLATION"
    AUDIT_MISSING_ENTRY = "AUDIT_MISSING_ENTRY"
    AUDIT_HASH_CHAIN_BROKEN = "AUDIT_HASH_CHAIN_BROKEN"

    @property
    def category(self) -> CIFailureCategory:
        """Get the category for this failure code."""
        return _CATEGORY_MAP[self.value]

    @property
    def remediation(self) -> str:
        """Get remediation guidance for this failure code."""
        return _REMEDIATION_MAP[self.value]


# Category mapping (defined outside enum to avoid becoming enum members)
_CATEGORY_MAP: dict[str, CIFailureCategory] = {
    "DRAFT_ARTIFACT_PRESENT": CIFailureCategory.ARTIFACT,
    "LOCKED_ARTIFACT_MODIFIED": CIFailureCategory.ARTIFACT,
    "SCHEMA_VALIDATION_FAILED": CIFailureCategory.ARTIFACT,
    "ARTIFACT_HASH_MISMATCH": CIFailureCategory.ARTIFACT,
    "ARTIFACT_NOT_APPROVED": CIFailureCategory.APPROVAL,
    "APPROVAL_METADATA_MISSING": CIFailureCategory.APPROVAL,
    "APPROVAL_EXPIRED": CIFailureCategory.APPROVAL,
    "TEST_MODIFICATION_AFTER_LOCK": CIFailureCategory.INVARIANT,
    "UNPLANNED_CODE_CHANGE": CIFailureCategory.INVARIANT,
    "ARCHITECTURE_VIOLATION": CIFailureCategory.INVARIANT,
    "TEST_FAILURE": CIFailureCategory.INVARIANT,
    "LINT_FAILURE": CIFailureCategory.INVARIANT,
    "ORPHANED_CODE_CHANGE": CIFailureCategory.INVARIANT,
    "AUDIT_INTEGRITY_VIOLATION": CIFailureCategory.AUDIT,
    "AUDIT_MISSING_ENTRY": CIFailureCategory.AUDIT,
    "AUDIT_HASH_CHAIN_BROKEN": CIFailureCategory.AUDIT,
}

# Remediation guidance mapping
_REMEDIATION_MAP: dict[str, str] = {
    "DRAFT_ARTIFACT_PRESENT": (
        "Approve or remove draft artifacts before merging. "
        "Run 'rice-factor approve <artifact>' for each draft."
    ),
    "LOCKED_ARTIFACT_MODIFIED": (
        "Locked artifacts cannot be modified. "
        "Revert changes to locked artifact or create a new artifact version."
    ),
    "SCHEMA_VALIDATION_FAILED": (
        "Fix artifact schema errors. "
        "Run 'rice-factor validate <artifact>' to see details."
    ),
    "ARTIFACT_HASH_MISMATCH": (
        "Artifact content has been modified outside the system. "
        "Regenerate the artifact using the appropriate plan command."
    ),
    "ARTIFACT_NOT_APPROVED": (
        "All artifacts must be approved before merging. "
        "Run 'rice-factor approve <artifact>' for each unapproved artifact."
    ),
    "APPROVAL_METADATA_MISSING": (
        "Approval metadata is incomplete. "
        "Re-run the approval process with proper credentials."
    ),
    "APPROVAL_EXPIRED": (
        "Artifact approval has expired. "
        "Re-approve the artifact to refresh the approval timestamp."
    ),
    "TEST_MODIFICATION_AFTER_LOCK": (
        "Tests cannot be modified after TestPlan is locked. "
        "Revert test changes or unlock TestPlan for modification."
    ),
    "UNPLANNED_CODE_CHANGE": (
        "Code changes must be traced to an approved plan. "
        "Either create a plan for these changes or revert them."
    ),
    "ARCHITECTURE_VIOLATION": (
        "Code violates architecture rules defined in ArchitecturePlan. "
        "Fix the violations or update the architecture plan."
    ),
    "TEST_FAILURE": (
        "Tests are failing. Fix the test failures before merging."
    ),
    "LINT_FAILURE": (
        "Code does not pass linting. Run the linter and fix issues."
    ),
    "ORPHANED_CODE_CHANGE": (
        "Code was changed without a corresponding approved plan. "
        "Create a plan for orphaned changes or revert them."
    ),
    "AUDIT_INTEGRITY_VIOLATION": (
        "Audit trail has been tampered with. "
        "This is a serious violation - contact security team."
    ),
    "AUDIT_MISSING_ENTRY": (
        "Expected audit entry is missing. "
        "Ensure all operations are properly logged."
    ),
    "AUDIT_HASH_CHAIN_BROKEN": (
        "Audit hash chain integrity check failed. "
        "This indicates potential tampering - contact security team."
    ),
}
