"""Unit tests for CI failure codes."""

import pytest

from rice_factor.domain.ci.failure_codes import CIFailureCategory, CIFailureCode


class TestCIFailureCode:
    """Tests for CIFailureCode enum."""

    def test_all_artifact_codes_exist(self) -> None:
        """All artifact validation failure codes should exist."""
        assert CIFailureCode.DRAFT_ARTIFACT_PRESENT.value == "DRAFT_ARTIFACT_PRESENT"
        assert CIFailureCode.LOCKED_ARTIFACT_MODIFIED.value == "LOCKED_ARTIFACT_MODIFIED"
        assert CIFailureCode.SCHEMA_VALIDATION_FAILED.value == "SCHEMA_VALIDATION_FAILED"
        assert CIFailureCode.ARTIFACT_HASH_MISMATCH.value == "ARTIFACT_HASH_MISMATCH"

    def test_all_approval_codes_exist(self) -> None:
        """All approval verification failure codes should exist."""
        assert CIFailureCode.ARTIFACT_NOT_APPROVED.value == "ARTIFACT_NOT_APPROVED"
        assert CIFailureCode.APPROVAL_METADATA_MISSING.value == "APPROVAL_METADATA_MISSING"
        assert CIFailureCode.APPROVAL_EXPIRED.value == "APPROVAL_EXPIRED"

    def test_all_invariant_codes_exist(self) -> None:
        """All invariant enforcement failure codes should exist."""
        assert (
            CIFailureCode.TEST_MODIFICATION_AFTER_LOCK.value
            == "TEST_MODIFICATION_AFTER_LOCK"
        )
        assert CIFailureCode.UNPLANNED_CODE_CHANGE.value == "UNPLANNED_CODE_CHANGE"
        assert CIFailureCode.ARCHITECTURE_VIOLATION.value == "ARCHITECTURE_VIOLATION"
        assert CIFailureCode.TEST_FAILURE.value == "TEST_FAILURE"
        assert CIFailureCode.LINT_FAILURE.value == "LINT_FAILURE"
        assert CIFailureCode.ORPHANED_CODE_CHANGE.value == "ORPHANED_CODE_CHANGE"

    def test_all_audit_codes_exist(self) -> None:
        """All audit verification failure codes should exist."""
        assert (
            CIFailureCode.AUDIT_INTEGRITY_VIOLATION.value == "AUDIT_INTEGRITY_VIOLATION"
        )
        assert CIFailureCode.AUDIT_MISSING_ENTRY.value == "AUDIT_MISSING_ENTRY"
        assert CIFailureCode.AUDIT_HASH_CHAIN_BROKEN.value == "AUDIT_HASH_CHAIN_BROKEN"

    def test_category_property_returns_correct_category(self) -> None:
        """category property should return correct category."""
        assert CIFailureCode.DRAFT_ARTIFACT_PRESENT.category == CIFailureCategory.ARTIFACT
        assert (
            CIFailureCode.ARTIFACT_NOT_APPROVED.category == CIFailureCategory.APPROVAL
        )
        assert (
            CIFailureCode.TEST_MODIFICATION_AFTER_LOCK.category
            == CIFailureCategory.INVARIANT
        )
        assert (
            CIFailureCode.AUDIT_INTEGRITY_VIOLATION.category == CIFailureCategory.AUDIT
        )

    def test_remediation_property_returns_string(self) -> None:
        """remediation property should return remediation guidance."""
        remediation = CIFailureCode.DRAFT_ARTIFACT_PRESENT.remediation
        assert isinstance(remediation, str)
        assert len(remediation) > 0
        assert "rice-factor approve" in remediation

    def test_all_codes_have_remediation(self) -> None:
        """All failure codes should have remediation guidance."""
        for code in CIFailureCode:
            remediation = code.remediation
            assert isinstance(remediation, str), f"{code.value} missing remediation"
            assert len(remediation) > 0, f"{code.value} has empty remediation"

    def test_all_codes_have_category(self) -> None:
        """All failure codes should have a category."""
        for code in CIFailureCode:
            category = code.category
            assert isinstance(
                category, CIFailureCategory
            ), f"{code.value} has invalid category"


class TestCIFailureCategory:
    """Tests for CIFailureCategory enum."""

    def test_all_categories_exist(self) -> None:
        """All categories should exist."""
        assert CIFailureCategory.ARTIFACT.value == "artifact"
        assert CIFailureCategory.APPROVAL.value == "approval"
        assert CIFailureCategory.INVARIANT.value == "invariant"
        assert CIFailureCategory.AUDIT.value == "audit"

    def test_category_count(self) -> None:
        """There should be exactly 4 categories."""
        assert len(CIFailureCategory) == 4
