"""Audit verification CI stage adapter.

This module implements Stage 5 of the CI pipeline: Audit Verification.
It verifies the integrity of the audit trail.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIFailure, CIStage, CIStageResult


class AuditVerificationAdapter:
    """CI validator for audit trail verification.

    This adapter implements Stage 5 of the CI pipeline. It:
    1. Verifies the audit log exists and is valid
    2. Checks that diff files referenced in audit log exist
    3. Verifies hash chain integrity (if enabled)

    The CI acts as a guardian - it only verifies, never generates.
    """

    def __init__(self, verify_hashes: bool = True) -> None:
        """Initialize the audit verifier.

        Args:
            verify_hashes: Whether to verify diff file hashes.
        """
        self._verify_hashes = verify_hashes

    @property
    def stage_name(self) -> str:
        """Return the human-readable name of this validation stage."""
        return "Audit Verification"

    def validate(self, repo_root: Path) -> CIStageResult:
        """Run audit verification.

        Args:
            repo_root: Path to the repository root.

        Returns:
            CIStageResult with pass/fail status and any failures found.
        """
        start_time = time.perf_counter()
        failures: list[CIFailure] = []

        audit_dir = repo_root / "audit"
        if not audit_dir.exists():
            # No audit directory - pass (nothing to verify)
            return CIStageResult(
                stage=CIStage.AUDIT_VERIFICATION,
                passed=True,
                failures=[],
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Check 1: Verify audit log exists and is parseable
        log_failures = self._verify_audit_log(audit_dir, repo_root)
        failures.extend(log_failures)

        # Check 2: Verify referenced diff files exist
        diff_failures = self._verify_diff_files(audit_dir, repo_root)
        failures.extend(diff_failures)

        # Check 3: Verify hash chain (if enabled)
        if self._verify_hashes:
            hash_failures = self._verify_hash_chain(audit_dir, repo_root)
            failures.extend(hash_failures)

        duration_ms = (time.perf_counter() - start_time) * 1000
        return CIStageResult(
            stage=CIStage.AUDIT_VERIFICATION,
            passed=len(failures) == 0,
            failures=failures,
            duration_ms=duration_ms,
        )

    def _verify_audit_log(
        self, audit_dir: Path, repo_root: Path
    ) -> list[CIFailure]:
        """Verify the audit log file exists and is valid.

        Args:
            audit_dir: Path to the audit directory.
            repo_root: Path to the repository root.

        Returns:
            List of failures found.
        """
        failures: list[CIFailure] = []
        log_path = audit_dir / "executions.log"

        if not log_path.exists():
            # No log file is OK if no executions have happened
            return failures

        try:
            content = log_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n") if content.strip() else []

            malformed_count = 0
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    # Basic validation
                    if not isinstance(entry, dict):
                        malformed_count += 1
                    elif "timestamp" not in entry or "executor" not in entry:
                        malformed_count += 1
                except json.JSONDecodeError:
                    malformed_count += 1

            if malformed_count > 0:
                failures.append(
                    CIFailure(
                        code=CIFailureCode.AUDIT_INTEGRITY_VIOLATION,
                        message=f"Audit log contains {malformed_count} malformed entries",
                        file_path=log_path.relative_to(repo_root),
                        details={
                            "malformed_count": malformed_count,
                            "total_lines": len(lines),
                        },
                    )
                )

        except OSError as e:
            failures.append(
                CIFailure(
                    code=CIFailureCode.AUDIT_MISSING_ENTRY,
                    message=f"Cannot read audit log: {e}",
                    file_path=log_path.relative_to(repo_root),
                    details={"error": str(e)},
                )
            )

        return failures

    def _verify_diff_files(
        self, audit_dir: Path, repo_root: Path
    ) -> list[CIFailure]:
        """Verify that referenced diff files exist.

        Args:
            audit_dir: Path to the audit directory.
            repo_root: Path to the repository root.

        Returns:
            List of failures found.
        """
        failures: list[CIFailure] = []
        log_path = audit_dir / "executions.log"

        if not log_path.exists():
            return failures

        try:
            content = log_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n") if content.strip() else []

            for line in lines:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    diff_path = entry.get("diff")
                    if diff_path:
                        full_path = repo_root / diff_path
                        if not full_path.exists():
                            failures.append(
                                CIFailure(
                                    code=CIFailureCode.AUDIT_MISSING_ENTRY,
                                    message=f"Referenced diff file missing: {diff_path}",
                                    file_path=Path(diff_path),
                                    details={
                                        "entry_timestamp": entry.get("timestamp"),
                                        "executor": entry.get("executor"),
                                    },
                                )
                            )
                except json.JSONDecodeError:
                    # Skip malformed entries (handled elsewhere)
                    continue

        except OSError:
            # Error reading log handled elsewhere
            pass

        return failures

    def _verify_hash_chain(
        self, audit_dir: Path, repo_root: Path
    ) -> list[CIFailure]:
        """Verify hash chain integrity.

        Checks that hashes stored in audit metadata match actual diff content.

        Args:
            audit_dir: Path to the audit directory.
            repo_root: Path to the repository root.

        Returns:
            List of failures found.
        """
        failures: list[CIFailure] = []
        hashes_file = audit_dir / "_meta" / "hashes.json"

        if not hashes_file.exists():
            # No hash file = no hash verification
            return failures

        try:
            with hashes_file.open("r", encoding="utf-8") as f:
                stored_hashes = json.load(f)

            for diff_path, stored_hash in stored_hashes.items():
                full_path = repo_root / diff_path
                if not full_path.exists():
                    # Missing file handled elsewhere
                    continue

                # Compute actual hash
                content = full_path.read_bytes()
                actual_hash = hashlib.sha256(content).hexdigest()

                if actual_hash != stored_hash:
                    failures.append(
                        CIFailure(
                            code=CIFailureCode.AUDIT_HASH_CHAIN_BROKEN,
                            message=f"Diff file hash mismatch: {diff_path}",
                            file_path=Path(diff_path),
                            details={
                                "expected_hash": stored_hash,
                                "actual_hash": actual_hash,
                            },
                        )
                    )

        except (json.JSONDecodeError, OSError) as e:
            failures.append(
                CIFailure(
                    code=CIFailureCode.AUDIT_INTEGRITY_VIOLATION,
                    message=f"Cannot read hash metadata: {e}",
                    file_path=hashes_file.relative_to(repo_root),
                    details={"error": str(e)},
                )
            )

        return failures
