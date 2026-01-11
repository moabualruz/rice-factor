"""Approval verification CI stage adapter.

This module implements Stage 2 of the CI pipeline: Approval Verification.
It verifies that all non-draft artifacts have valid approval records.
"""

import json
import time
from pathlib import Path

from rice_factor.domain.artifacts.enums import ArtifactStatus
from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIFailure, CIStage, CIStageResult


class ApprovalVerificationAdapter:
    """CI validator for approval verification.

    This adapter implements Stage 2 of the CI pipeline. It:
    1. Loads the approvals metadata from _meta/approvals.json
    2. Discovers all artifacts in the repository
    3. Verifies that non-draft artifacts have approval records

    The CI acts as a guardian - it only verifies, never generates.
    """

    def __init__(self) -> None:
        """Initialize the approval verifier."""
        pass

    @property
    def stage_name(self) -> str:
        """Return the human-readable name of this validation stage."""
        return "Approval Verification"

    def validate(self, repo_root: Path) -> CIStageResult:
        """Run approval verification.

        Args:
            repo_root: Path to the repository root.

        Returns:
            CIStageResult with pass/fail status and any failures found.
        """
        start_time = time.perf_counter()
        failures: list[CIFailure] = []

        artifacts_dir = repo_root / "artifacts"
        if not artifacts_dir.exists():
            # No artifacts directory - pass (nothing to verify)
            return CIStageResult(
                stage=CIStage.APPROVAL_VERIFICATION,
                passed=True,
                failures=[],
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Load approvals metadata
        approved_ids, metadata_failure = self._load_approvals(artifacts_dir)
        if metadata_failure:
            failures.append(metadata_failure)

        # Discover all artifacts that need approval
        artifact_files = self._discover_artifacts(artifacts_dir)

        for artifact_file in artifact_files:
            file_failure = self._verify_approval(
                artifact_file, repo_root, approved_ids
            )
            if file_failure:
                failures.append(file_failure)

        duration_ms = (time.perf_counter() - start_time) * 1000
        return CIStageResult(
            stage=CIStage.APPROVAL_VERIFICATION,
            passed=len(failures) == 0,
            failures=failures,
            duration_ms=duration_ms,
        )

    def _load_approvals(
        self, artifacts_dir: Path
    ) -> tuple[set[str], CIFailure | None]:
        """Load approvals from metadata file.

        Args:
            artifacts_dir: Path to the artifacts directory.

        Returns:
            Tuple of (set of approved artifact IDs, optional failure).
        """
        approvals_file = artifacts_dir / "_meta" / "approvals.json"
        approved_ids: set[str] = set()

        if not approvals_file.exists():
            # No approvals file - will fail on any non-draft artifact
            return approved_ids, None

        try:
            with approvals_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data.get("approvals", []):
                artifact_id = item.get("artifact_id")
                if artifact_id:
                    approved_ids.add(artifact_id)

            return approved_ids, None

        except json.JSONDecodeError as e:
            return approved_ids, CIFailure(
                code=CIFailureCode.APPROVAL_METADATA_MISSING,
                message=f"Invalid approvals metadata: {e}",
                file_path=approvals_file.relative_to(artifacts_dir.parent),
                details={"error": str(e)},
            )

    def _discover_artifacts(self, artifacts_dir: Path) -> list[Path]:
        """Discover all artifact JSON files.

        Args:
            artifacts_dir: Path to the artifacts directory.

        Returns:
            List of paths to artifact JSON files.
        """
        artifact_files = []

        for json_file in artifacts_dir.rglob("*.json"):
            # Skip metadata files
            if "_meta" in json_file.parts:
                continue
            # Skip approval files
            if json_file.name.endswith(".approval.json"):
                continue
            # Skip index files
            if json_file.name == "index.json":
                continue
            artifact_files.append(json_file)

        return artifact_files

    def _verify_approval(
        self,
        artifact_file: Path,
        repo_root: Path,
        approved_ids: set[str],
    ) -> CIFailure | None:
        """Verify that an artifact has approval.

        Args:
            artifact_file: Path to the artifact JSON file.
            repo_root: Path to the repository root.
            approved_ids: Set of approved artifact IDs.

        Returns:
            CIFailure if artifact is not approved, None otherwise.
        """
        relative_path = artifact_file.relative_to(repo_root)

        try:
            with artifact_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            # Let artifact validation handle JSON errors
            return None

        # Get artifact info
        artifact_id = data.get("id")
        artifact_type = data.get("artifact_type", "Unknown")
        status_str = data.get("status")

        if not artifact_id or not status_str:
            # Missing required fields - let artifact validation handle
            return None

        # Draft artifacts don't need approval
        try:
            status = ArtifactStatus(status_str)
            if status == ArtifactStatus.DRAFT:
                return None
        except ValueError:
            return None

        # Check if artifact is approved
        if artifact_id not in approved_ids:
            return CIFailure(
                code=CIFailureCode.ARTIFACT_NOT_APPROVED,
                message=f"Artifact not approved: {artifact_type} ({artifact_id})",
                file_path=relative_path,
                details={
                    "artifact_id": artifact_id,
                    "artifact_type": artifact_type,
                },
            )

        return None
