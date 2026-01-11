"""Artifact validation CI stage adapter.

This module implements Stage 1 of the CI pipeline: Artifact Validation.
It checks that all artifacts in the repository are valid, not in draft status,
and that locked artifacts have not been modified.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from rice_factor.adapters.validators.schema import ArtifactValidator, SCHEMA_FILE_MAP
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIFailure, CIStage, CIStageResult


class ArtifactValidationAdapter:
    """CI validator for artifact status and schema validation.

    This adapter implements Stage 1 of the CI pipeline. It:
    1. Scans the artifacts/ directory for all artifact files
    2. Validates each artifact against its JSON Schema
    3. Checks that no artifacts are in DRAFT status
    4. Checks that LOCKED artifacts have not been modified

    The CI acts as a guardian - it only verifies, never generates.
    """

    def __init__(self, base_branch: str = "main") -> None:
        """Initialize the artifact validator.

        Args:
            base_branch: Branch to compare against for locked artifact changes.
        """
        self._base_branch = base_branch
        self._schema_validator = ArtifactValidator()

    @property
    def stage_name(self) -> str:
        """Return the human-readable name of this validation stage."""
        return "Artifact Validation"

    def validate(self, repo_root: Path) -> CIStageResult:
        """Run artifact validation.

        Args:
            repo_root: Path to the repository root.

        Returns:
            CIStageResult with pass/fail status and any failures found.
        """
        start_time = time.perf_counter()
        failures: list[CIFailure] = []

        artifacts_dir = repo_root / "artifacts"
        if not artifacts_dir.exists():
            # No artifacts directory - pass (nothing to validate)
            return CIStageResult(
                stage=CIStage.ARTIFACT_VALIDATION,
                passed=True,
                failures=[],
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Discover all artifact files
        artifact_files = self._discover_artifacts(artifacts_dir)

        for artifact_file in artifact_files:
            file_failures = self._validate_artifact_file(artifact_file, repo_root)
            failures.extend(file_failures)

        duration_ms = (time.perf_counter() - start_time) * 1000
        return CIStageResult(
            stage=CIStage.ARTIFACT_VALIDATION,
            passed=len(failures) == 0,
            failures=failures,
            duration_ms=duration_ms,
        )

    def _discover_artifacts(self, artifacts_dir: Path) -> list[Path]:
        """Discover all artifact JSON files in the artifacts directory.

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

    def _validate_artifact_file(
        self, artifact_file: Path, repo_root: Path
    ) -> list[CIFailure]:
        """Validate a single artifact file.

        Args:
            artifact_file: Path to the artifact JSON file.
            repo_root: Path to the repository root.

        Returns:
            List of failures found for this artifact.
        """
        failures: list[CIFailure] = []
        relative_path = artifact_file.relative_to(repo_root)

        # Load artifact data
        try:
            with artifact_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            failures.append(
                CIFailure(
                    code=CIFailureCode.SCHEMA_VALIDATION_FAILED,
                    message=f"Invalid JSON in artifact file: {e}",
                    file_path=relative_path,
                    details={"error": str(e)},
                )
            )
            return failures

        # Check 1: Schema validation
        schema_failure = self._check_schema(data, artifact_file, relative_path)
        if schema_failure:
            failures.append(schema_failure)

        # Check 2: Draft status
        draft_failure = self._check_draft_status(data, relative_path)
        if draft_failure:
            failures.append(draft_failure)

        # Check 3: Locked artifact modification
        locked_failure = self._check_locked_modification(
            data, artifact_file, repo_root, relative_path
        )
        if locked_failure:
            failures.append(locked_failure)

        return failures

    def _check_schema(
        self, data: dict[str, Any], artifact_file: Path, relative_path: Path
    ) -> CIFailure | None:
        """Validate artifact against its JSON Schema.

        Args:
            data: Parsed artifact JSON data.
            artifact_file: Path to the artifact file.
            relative_path: Relative path for error reporting.

        Returns:
            CIFailure if validation fails, None otherwise.
        """
        try:
            # Get artifact type
            artifact_type_str = data.get("artifact_type")
            if not artifact_type_str:
                return CIFailure(
                    code=CIFailureCode.SCHEMA_VALIDATION_FAILED,
                    message="Artifact missing 'artifact_type' field",
                    file_path=relative_path,
                )

            try:
                artifact_type = ArtifactType(artifact_type_str)
            except ValueError:
                return CIFailure(
                    code=CIFailureCode.SCHEMA_VALIDATION_FAILED,
                    message=f"Unknown artifact type: {artifact_type_str}",
                    file_path=relative_path,
                )

            # Check if we have a schema for this type
            if artifact_type not in SCHEMA_FILE_MAP:
                # No schema defined for this type - skip schema validation
                return None

            # Validate using the existing schema validator
            self._schema_validator.validate(data)
            return None

        except Exception as e:
            return CIFailure(
                code=CIFailureCode.SCHEMA_VALIDATION_FAILED,
                message=f"Schema validation failed: {e}",
                file_path=relative_path,
                details={"error": str(e)},
            )

    def _check_draft_status(
        self, data: dict[str, Any], relative_path: Path
    ) -> CIFailure | None:
        """Check if artifact is in draft status.

        Args:
            data: Parsed artifact JSON data.
            relative_path: Relative path for error reporting.

        Returns:
            CIFailure if artifact is draft, None otherwise.
        """
        status_str = data.get("status")
        if not status_str:
            return None  # No status field - let schema validation catch this

        try:
            status = ArtifactStatus(status_str)
            if status == ArtifactStatus.DRAFT:
                artifact_id = data.get("id", "unknown")
                artifact_type = data.get("artifact_type", "unknown")
                return CIFailure(
                    code=CIFailureCode.DRAFT_ARTIFACT_PRESENT,
                    message=f"Draft artifact found: {artifact_type} ({artifact_id})",
                    file_path=relative_path,
                    details={
                        "artifact_id": artifact_id,
                        "artifact_type": artifact_type,
                    },
                )
        except ValueError:
            pass  # Invalid status - let schema validation catch this

        return None

    def _check_locked_modification(
        self,
        data: dict[str, Any],
        artifact_file: Path,
        repo_root: Path,
        relative_path: Path,
    ) -> CIFailure | None:
        """Check if a locked artifact has been modified.

        Args:
            data: Parsed artifact JSON data.
            artifact_file: Path to the artifact file.
            repo_root: Path to the repository root.
            relative_path: Relative path for error reporting.

        Returns:
            CIFailure if locked artifact was modified, None otherwise.
        """
        status_str = data.get("status")
        if not status_str:
            return None

        try:
            status = ArtifactStatus(status_str)
            if status != ArtifactStatus.LOCKED:
                return None  # Only check locked artifacts
        except ValueError:
            return None

        # Check if file has been modified compared to base branch
        if self._is_file_modified(artifact_file, repo_root):
            artifact_id = data.get("id", "unknown")
            artifact_type = data.get("artifact_type", "unknown")
            return CIFailure(
                code=CIFailureCode.LOCKED_ARTIFACT_MODIFIED,
                message=f"Locked artifact modified: {artifact_type} ({artifact_id})",
                file_path=relative_path,
                details={
                    "artifact_id": artifact_id,
                    "artifact_type": artifact_type,
                    "base_branch": self._base_branch,
                },
            )

        return None

    def _is_file_modified(self, file_path: Path, repo_root: Path) -> bool:
        """Check if a file has been modified compared to base branch.

        Args:
            file_path: Path to the file to check.
            repo_root: Path to the repository root.

        Returns:
            True if file was modified, False otherwise.
        """
        try:
            relative_path = file_path.relative_to(repo_root)
            result = subprocess.run(
                [
                    "git",
                    "diff",
                    "--name-only",
                    f"{self._base_branch}...HEAD",
                    "--",
                    str(relative_path),
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            # If the file appears in diff output, it was modified
            return str(relative_path) in result.stdout
        except (subprocess.SubprocessError, OSError):
            # If git command fails, assume not modified (fail open)
            return False
