"""Unit tests for AuditVerificationAdapter."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from rice_factor.adapters.ci.audit_verifier import AuditVerificationAdapter
from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIStage


def _create_audit_entry(
    executor: str = "scaffold",
    artifact: str = "artifacts/scaffold_plan.json",
    status: str = "success",
    diff_path: str | None = None,
) -> dict:
    """Create a sample audit log entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "executor": executor,
        "artifact": artifact,
        "status": status,
        "mode": "apply",
    }
    if diff_path:
        entry["diff"] = diff_path
    return entry


def _write_audit_log(audit_dir: Path, entries: list[dict]) -> None:
    """Write audit log entries to executions.log."""
    log_path = audit_dir / "executions.log"
    audit_dir.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _create_diff_file(audit_dir: Path, filename: str, content: str = "test diff") -> str:
    """Create a diff file and return its relative path."""
    diffs_dir = audit_dir / "diffs"
    diffs_dir.mkdir(parents=True, exist_ok=True)
    diff_path = diffs_dir / filename
    diff_path.write_text(content, encoding="utf-8")
    return f"audit/diffs/{filename}"


class TestAuditVerificationAdapter:
    """Tests for AuditVerificationAdapter."""

    def test_stage_name(self) -> None:
        """stage_name should return 'Audit Verification'."""
        adapter = AuditVerificationAdapter()
        assert adapter.stage_name == "Audit Verification"

    def test_no_audit_directory_passes(self, tmp_path: Path) -> None:
        """Validation should pass when audit directory doesn't exist."""
        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert result.stage == CIStage.AUDIT_VERIFICATION
        assert len(result.failures) == 0

    def test_empty_audit_directory_passes(self, tmp_path: Path) -> None:
        """Validation should pass with empty audit directory."""
        (tmp_path / "audit").mkdir()

        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert len(result.failures) == 0


class TestAuditLogVerification:
    """Tests for audit log verification."""

    def test_valid_audit_log_passes(self, tmp_path: Path) -> None:
        """Should pass with valid audit log entries."""
        audit_dir = tmp_path / "audit"
        entries = [
            _create_audit_entry(executor="scaffold"),
            _create_audit_entry(executor="diff_executor"),
        ]
        _write_audit_log(audit_dir, entries)

        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert len(result.failures) == 0

    def test_malformed_entry_fails(self, tmp_path: Path) -> None:
        """Should fail with malformed JSON entries."""
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir(parents=True)
        log_path = audit_dir / "executions.log"
        log_path.write_text("not valid json\n", encoding="utf-8")

        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        integrity_failures = [
            f for f in result.failures
            if f.code == CIFailureCode.AUDIT_INTEGRITY_VIOLATION
        ]
        assert len(integrity_failures) == 1
        assert "malformed" in integrity_failures[0].message.lower()

    def test_missing_required_fields_fails(self, tmp_path: Path) -> None:
        """Should fail when entries are missing required fields."""
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir(parents=True)
        log_path = audit_dir / "executions.log"
        # Valid JSON but missing required fields
        log_path.write_text('{"foo": "bar"}\n', encoding="utf-8")

        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        integrity_failures = [
            f for f in result.failures
            if f.code == CIFailureCode.AUDIT_INTEGRITY_VIOLATION
        ]
        assert len(integrity_failures) == 1


class TestDiffFileVerification:
    """Tests for diff file existence verification."""

    def test_existing_diff_file_passes(self, tmp_path: Path) -> None:
        """Should pass when referenced diff files exist."""
        audit_dir = tmp_path / "audit"
        diff_path = _create_diff_file(audit_dir, "test.diff")
        entries = [_create_audit_entry(diff_path=diff_path)]
        _write_audit_log(audit_dir, entries)

        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True

    def test_missing_diff_file_fails(self, tmp_path: Path) -> None:
        """Should fail when referenced diff file doesn't exist."""
        audit_dir = tmp_path / "audit"
        entries = [_create_audit_entry(diff_path="audit/diffs/missing.diff")]
        _write_audit_log(audit_dir, entries)

        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        missing_failures = [
            f for f in result.failures
            if f.code == CIFailureCode.AUDIT_MISSING_ENTRY
        ]
        assert len(missing_failures) == 1
        assert "missing.diff" in missing_failures[0].message

    def test_entry_without_diff_passes(self, tmp_path: Path) -> None:
        """Should pass when entry has no diff field."""
        audit_dir = tmp_path / "audit"
        entries = [_create_audit_entry()]  # No diff_path
        _write_audit_log(audit_dir, entries)

        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True


class TestHashChainVerification:
    """Tests for hash chain integrity verification."""

    def test_valid_hashes_pass(self, tmp_path: Path) -> None:
        """Should pass when hashes match."""
        audit_dir = tmp_path / "audit"
        content = "test diff content"
        diff_path = _create_diff_file(audit_dir, "test.diff", content)

        # Create hash metadata
        meta_dir = audit_dir / "_meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        hashes = {diff_path: expected_hash}
        (meta_dir / "hashes.json").write_text(json.dumps(hashes), encoding="utf-8")

        adapter = AuditVerificationAdapter(verify_hashes=True)
        result = adapter.validate(tmp_path)

        assert result.passed is True

    def test_hash_mismatch_fails(self, tmp_path: Path) -> None:
        """Should fail when hash doesn't match."""
        audit_dir = tmp_path / "audit"
        content = "actual content"
        diff_path = _create_diff_file(audit_dir, "test.diff", content)

        # Create hash metadata with wrong hash
        meta_dir = audit_dir / "_meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        hashes = {diff_path: "wrong_hash"}
        (meta_dir / "hashes.json").write_text(json.dumps(hashes), encoding="utf-8")

        adapter = AuditVerificationAdapter(verify_hashes=True)
        result = adapter.validate(tmp_path)

        assert result.passed is False
        hash_failures = [
            f for f in result.failures
            if f.code == CIFailureCode.AUDIT_HASH_CHAIN_BROKEN
        ]
        assert len(hash_failures) == 1

    def test_no_hash_file_passes(self, tmp_path: Path) -> None:
        """Should pass when no hash file exists (hash verification skipped)."""
        audit_dir = tmp_path / "audit"
        _create_diff_file(audit_dir, "test.diff")

        adapter = AuditVerificationAdapter(verify_hashes=True)
        result = adapter.validate(tmp_path)

        assert result.passed is True

    def test_hash_verification_disabled(self, tmp_path: Path) -> None:
        """Should skip hash verification when disabled."""
        audit_dir = tmp_path / "audit"
        content = "actual content"
        diff_path = _create_diff_file(audit_dir, "test.diff", content)

        # Create hash metadata with wrong hash
        meta_dir = audit_dir / "_meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        hashes = {diff_path: "wrong_hash"}
        (meta_dir / "hashes.json").write_text(json.dumps(hashes), encoding="utf-8")

        adapter = AuditVerificationAdapter(verify_hashes=False)
        result = adapter.validate(tmp_path)

        # Should pass because hash verification is disabled
        hash_failures = [
            f for f in result.failures
            if f.code == CIFailureCode.AUDIT_HASH_CHAIN_BROKEN
        ]
        assert len(hash_failures) == 0


class TestMultipleFailures:
    """Tests for multiple failure reporting."""

    def test_reports_all_failures(self, tmp_path: Path) -> None:
        """Should report multiple failures found."""
        audit_dir = tmp_path / "audit"

        # Create entries with multiple missing diffs
        entries = [
            _create_audit_entry(diff_path="audit/diffs/missing1.diff"),
            _create_audit_entry(diff_path="audit/diffs/missing2.diff"),
        ]
        _write_audit_log(audit_dir, entries)

        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        missing_failures = [
            f for f in result.failures
            if f.code == CIFailureCode.AUDIT_MISSING_ENTRY
        ]
        assert len(missing_failures) == 2


class TestDurationTracking:
    """Tests for duration tracking."""

    def test_duration_is_recorded(self, tmp_path: Path) -> None:
        """Validation should record duration."""
        (tmp_path / "audit").mkdir()

        adapter = AuditVerificationAdapter()
        result = adapter.validate(tmp_path)

        assert result.duration_ms >= 0


class TestOrphanedCodeDetection:
    """Tests for orphaned code change detection."""

    def test_no_orphans_without_audit_dir(self, tmp_path: Path) -> None:
        """Should pass when no audit directory exists."""
        adapter = AuditVerificationAdapter(detect_orphans=True)
        result = adapter.validate(tmp_path)
        assert result.passed is True

    def test_no_orphans_with_empty_audit(self, tmp_path: Path) -> None:
        """Should pass when audit directory is empty."""
        (tmp_path / "audit").mkdir()
        adapter = AuditVerificationAdapter(detect_orphans=True)
        result = adapter.validate(tmp_path)
        assert result.passed is True

    def test_orphan_detection_disabled(self, tmp_path: Path) -> None:
        """Should skip orphan detection when disabled."""
        (tmp_path / "audit").mkdir()
        adapter = AuditVerificationAdapter(detect_orphans=False)
        result = adapter.validate(tmp_path)

        orphan_failures = [
            f for f in result.failures
            if f.code == CIFailureCode.ORPHANED_CODE_CHANGE
        ]
        assert len(orphan_failures) == 0

    def test_extracts_files_from_audit_target(self, tmp_path: Path) -> None:
        """Should extract target files from audit entries."""
        audit_dir = tmp_path / "audit"
        entries = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "executor": "scaffold",
                "target": "src/main.py",
                "status": "success",
            }
        ]
        _write_audit_log(audit_dir, entries)

        adapter = AuditVerificationAdapter()
        audited = adapter._get_audited_files(audit_dir, tmp_path)

        assert "src/main.py" in audited

    def test_extracts_files_from_diff_content(self, tmp_path: Path) -> None:
        """Should extract file paths from diff content."""
        audit_dir = tmp_path / "audit"
        diff_content = """--- a/src/old.py
+++ b/src/new.py
@@ -1,3 +1,3 @@
-old line
+new line
"""
        diff_path = _create_diff_file(audit_dir, "change.diff", diff_content)

        entries = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "executor": "refactor",
                "diff": diff_path,
                "status": "success",
            }
        ]
        _write_audit_log(audit_dir, entries)

        adapter = AuditVerificationAdapter()
        audited = adapter._get_audited_files(audit_dir, tmp_path)

        assert "src/old.py" in audited
        assert "src/new.py" in audited

    def test_extracts_files_from_artifact_payload(self, tmp_path: Path) -> None:
        """Should extract files from artifact payload."""
        audit_dir = tmp_path / "audit"
        entries = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "executor": "impl",
                "artifact": {
                    "artifact_type": "ImplementationPlan",
                    "payload": {"target": "src/service.py"},
                },
                "status": "success",
            }
        ]
        _write_audit_log(audit_dir, entries)

        adapter = AuditVerificationAdapter()
        audited = adapter._get_audited_files(audit_dir, tmp_path)

        assert "src/service.py" in audited

    def test_extracts_refactor_operations(self, tmp_path: Path) -> None:
        """Should extract files from refactor operations."""
        audit_dir = tmp_path / "audit"
        entries = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "executor": "refactor",
                "artifact": {
                    "artifact_type": "RefactorPlan",
                    "payload": {
                        "operations": [
                            {"from": "src/old.py", "to": "src/new.py"},
                            {"from_path": "src/a.py", "to_path": "src/b.py"},
                        ]
                    },
                },
                "status": "success",
            }
        ]
        _write_audit_log(audit_dir, entries)

        adapter = AuditVerificationAdapter()
        audited = adapter._get_audited_files(audit_dir, tmp_path)

        assert "src/old.py" in audited
        assert "src/new.py" in audited
        assert "src/a.py" in audited
        assert "src/b.py" in audited

    def test_extract_files_from_diff_header(self, tmp_path: Path) -> None:
        """Should parse unified diff headers."""
        audit_dir = tmp_path / "audit"
        diff_content = """--- a/rice_factor/service.py
+++ b/rice_factor/service.py
@@ -10,5 +10,6 @@
 line
+new line
"""
        diff_path = _create_diff_file(audit_dir, "mod.diff", diff_content)

        adapter = AuditVerificationAdapter()
        files = adapter._extract_files_from_diff(tmp_path / diff_path)

        assert "rice_factor/service.py" in files

    def test_handles_deleted_files_in_diff(self, tmp_path: Path) -> None:
        """Should handle /dev/null in deleted file diffs."""
        audit_dir = tmp_path / "audit"
        diff_content = """--- a/src/deleted.py
+++ /dev/null
@@ -1,3 +0,0 @@
-deleted content
"""
        diff_path = _create_diff_file(audit_dir, "delete.diff", diff_content)

        adapter = AuditVerificationAdapter()
        files = adapter._extract_files_from_diff(tmp_path / diff_path)

        assert "src/deleted.py" in files
        assert "/dev/null" not in files
        assert "dev/null" not in files
