"""Unit tests for ApprovalVerificationAdapter."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from rice_factor.adapters.ci.approval_verifier import ApprovalVerificationAdapter
from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIStage


def _create_artifact_file(
    artifacts_dir: Path,
    artifact_type: str = "ProjectPlan",
    status: str = "approved",
    artifact_id: str | None = None,
    subdir: str = "project_plans",
) -> str:
    """Create a schema-compliant artifact JSON file for testing.

    Returns:
        The artifact ID.
    """
    if artifact_id is None:
        artifact_id = str(uuid4())

    type_dir = artifacts_dir / subdir
    type_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = type_dir / f"{artifact_id}.json"
    artifact_data = {
        "id": artifact_id,
        "artifact_type": artifact_type,
        "artifact_version": "1.0",
        "status": status,
        "created_by": "llm",
        "created_at": "2026-01-11T10:00:00Z",
        "payload": {
            "domains": [{"name": "core", "responsibility": "Core functionality"}],
            "modules": [{"name": "main", "domain": "core"}],
            "constraints": {
                "architecture": "hexagonal",
                "languages": ["python"],
            },
        },
    }
    artifact_path.write_text(json.dumps(artifact_data, indent=2))
    return artifact_id


def _create_approvals_file(
    artifacts_dir: Path,
    approved_ids: list[str],
) -> None:
    """Create an approvals metadata file."""
    meta_dir = artifacts_dir / "_meta"
    meta_dir.mkdir(parents=True, exist_ok=True)

    approvals_file = meta_dir / "approvals.json"
    data = {
        "approvals": [
            {
                "artifact_id": aid,
                "approved_by": "human",
                "approved_at": "2026-01-11T10:00:00Z",
            }
            for aid in approved_ids
        ]
    }
    approvals_file.write_text(json.dumps(data, indent=2))


class TestApprovalVerificationAdapter:
    """Tests for ApprovalVerificationAdapter."""

    def test_stage_name(self) -> None:
        """stage_name should return 'Approval Verification'."""
        adapter = ApprovalVerificationAdapter()
        assert adapter.stage_name == "Approval Verification"

    def test_no_artifacts_directory_passes(self, tmp_path: Path) -> None:
        """Validation should pass when artifacts directory doesn't exist."""
        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert result.stage == CIStage.APPROVAL_VERIFICATION
        assert len(result.failures) == 0

    def test_empty_artifacts_directory_passes(self, tmp_path: Path) -> None:
        """Validation should pass with empty artifacts directory."""
        (tmp_path / "artifacts").mkdir()

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert len(result.failures) == 0


class TestApprovalVerification:
    """Tests for approval verification logic."""

    def test_approved_artifact_passes(self, tmp_path: Path) -> None:
        """Validation should pass for approved artifacts with approval record."""
        artifacts_dir = tmp_path / "artifacts"
        artifact_id = _create_artifact_file(artifacts_dir, status="approved")
        _create_approvals_file(artifacts_dir, [artifact_id])

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert len(result.failures) == 0

    def test_draft_artifact_skipped(self, tmp_path: Path) -> None:
        """Draft artifacts should not require approval."""
        artifacts_dir = tmp_path / "artifacts"
        _create_artifact_file(artifacts_dir, status="draft")
        # No approvals file needed

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        # Draft artifacts don't need approval
        assert result.passed is True
        assert len(result.failures) == 0

    def test_unapproved_artifact_fails(self, tmp_path: Path) -> None:
        """Validation should fail for approved status without approval record."""
        artifacts_dir = tmp_path / "artifacts"
        artifact_id = _create_artifact_file(artifacts_dir, status="approved")
        # Don't create approvals file

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        assert len(result.failures) == 1
        assert result.failures[0].code == CIFailureCode.ARTIFACT_NOT_APPROVED
        assert artifact_id in result.failures[0].message

    def test_locked_artifact_needs_approval(self, tmp_path: Path) -> None:
        """Locked artifacts also need approval records."""
        artifacts_dir = tmp_path / "artifacts"

        # Create a TestPlan (only type that can be locked)
        artifact_id = str(uuid4())
        type_dir = artifacts_dir / "test_plans"
        type_dir.mkdir(parents=True, exist_ok=True)

        artifact_data = {
            "id": artifact_id,
            "artifact_type": "TestPlan",
            "artifact_version": "1.0",
            "status": "locked",
            "created_by": "llm",
            "created_at": "2026-01-11T10:00:00Z",
            "payload": {
                "tests": [
                    {"id": "test-1", "target": "main", "assertions": ["should work"]}
                ]
            },
        }
        (type_dir / f"{artifact_id}.json").write_text(
            json.dumps(artifact_data, indent=2)
        )

        # No approval record
        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        assert len(result.failures) == 1
        assert result.failures[0].code == CIFailureCode.ARTIFACT_NOT_APPROVED


class TestApprovalsMetadata:
    """Tests for approvals metadata loading."""

    def test_missing_approvals_file_no_failure(self, tmp_path: Path) -> None:
        """Missing approvals file is not itself a failure (only unapproved artifacts are)."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        # No approvals file, no artifacts

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        # No artifacts = no failures
        assert result.passed is True

    def test_invalid_approvals_json_fails(self, tmp_path: Path) -> None:
        """Invalid JSON in approvals file should fail."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        meta_dir = artifacts_dir / "_meta"
        meta_dir.mkdir()

        approvals_file = meta_dir / "approvals.json"
        approvals_file.write_text("{ invalid json }")

        # Create an artifact that would need approval
        _create_artifact_file(artifacts_dir, status="approved")

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        # Should have failure for invalid metadata
        metadata_failures = [
            f
            for f in result.failures
            if f.code == CIFailureCode.APPROVAL_METADATA_MISSING
        ]
        assert len(metadata_failures) >= 1


class TestMultipleArtifacts:
    """Tests for multiple artifact scenarios."""

    def test_all_approved_passes(self, tmp_path: Path) -> None:
        """All artifacts approved should pass."""
        artifacts_dir = tmp_path / "artifacts"
        id1 = _create_artifact_file(
            artifacts_dir, status="approved", subdir="project_plans"
        )
        id2 = _create_artifact_file(
            artifacts_dir, status="approved", subdir="architecture_plans"
        )
        _create_approvals_file(artifacts_dir, [id1, id2])

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True

    def test_partial_approval_fails(self, tmp_path: Path) -> None:
        """Only some artifacts approved should fail."""
        artifacts_dir = tmp_path / "artifacts"
        id1 = _create_artifact_file(
            artifacts_dir, status="approved", subdir="project_plans"
        )
        id2 = _create_artifact_file(
            artifacts_dir, status="approved", subdir="architecture_plans"
        )
        # Only approve first one
        _create_approvals_file(artifacts_dir, [id1])

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        # Should have one failure for second artifact
        unapproved_failures = [
            f for f in result.failures if f.code == CIFailureCode.ARTIFACT_NOT_APPROVED
        ]
        assert len(unapproved_failures) == 1
        assert id2 in unapproved_failures[0].message

    def test_mixed_draft_approved_status(self, tmp_path: Path) -> None:
        """Draft artifacts don't need approval, approved ones do."""
        artifacts_dir = tmp_path / "artifacts"
        draft_id = _create_artifact_file(
            artifacts_dir,
            artifact_id="draft-001",
            status="draft",
            subdir="project_plans",
        )
        approved_id = _create_artifact_file(
            artifacts_dir,
            artifact_id="approved-001",
            status="approved",
            subdir="architecture_plans",
        )
        # Only approve the approved one
        _create_approvals_file(artifacts_dir, [approved_id])

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        # Should pass - draft doesn't need approval, approved has approval
        assert result.passed is True


class TestDurationTracking:
    """Tests for duration tracking."""

    def test_duration_is_recorded(self, tmp_path: Path) -> None:
        """Validation should record duration."""
        (tmp_path / "artifacts").mkdir()

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.duration_ms >= 0


class TestArtifactDiscovery:
    """Tests for artifact file discovery."""

    def test_skips_metadata_files(self, tmp_path: Path) -> None:
        """Validator should skip _meta directory."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create a file in _meta that would fail if processed
        meta_dir = artifacts_dir / "_meta"
        meta_dir.mkdir()
        (meta_dir / "index.json").write_text(json.dumps({"artifacts": []}))

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        # Should pass - meta files should be skipped
        assert result.passed is True

    def test_skips_approval_files(self, tmp_path: Path) -> None:
        """Validator should skip .approval.json files."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        # Create an approval file that would fail if processed as artifact
        approval_file = artifacts_dir / "abc123.approval.json"
        approval_file.write_text(
            json.dumps({"approved_by": "user", "timestamp": "123"})
        )

        adapter = ApprovalVerificationAdapter()
        result = adapter.validate(tmp_path)

        # Should pass - approval files should be skipped
        assert result.passed is True
