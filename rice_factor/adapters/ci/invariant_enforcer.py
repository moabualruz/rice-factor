"""Invariant enforcement CI stage adapter.

This module implements Stage 3 of the CI pipeline: Invariant Enforcement.
It enforces test immutability after lock and artifact-to-code mapping.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIFailure, CIStage, CIStageResult


class InvariantEnforcementAdapter:
    """CI validator for invariant enforcement.

    This adapter implements Stage 3 of the CI pipeline. It:
    1. Checks that tests are not modified after TestPlan is locked
    2. Checks that code changes are covered by approved plans
    3. Optionally checks architecture rules

    The CI acts as a guardian - it only verifies, never generates.
    """

    def __init__(
        self,
        base_branch: str = "main",
        tests_dir: str = "tests",
        source_dirs: list[str] | None = None,
    ) -> None:
        """Initialize the invariant enforcer.

        Args:
            base_branch: Branch to compare against for detecting changes.
            tests_dir: Directory containing tests.
            source_dirs: Directories containing source code (for artifact-to-code mapping).
        """
        self._base_branch = base_branch
        self._tests_dir = tests_dir
        self._source_dirs = source_dirs or ["src", "lib", "rice_factor"]

    @property
    def stage_name(self) -> str:
        """Return the human-readable name of this validation stage."""
        return "Invariant Enforcement"

    def validate(self, repo_root: Path) -> CIStageResult:
        """Run invariant enforcement.

        Args:
            repo_root: Path to the repository root.

        Returns:
            CIStageResult with pass/fail status and any failures found.
        """
        start_time = time.perf_counter()
        failures: list[CIFailure] = []

        artifacts_dir = repo_root / "artifacts"
        if not artifacts_dir.exists():
            # No artifacts directory - pass (nothing to enforce)
            return CIStageResult(
                stage=CIStage.INVARIANT_ENFORCEMENT,
                passed=True,
                failures=[],
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Get changed files from git
        changed_files = self._get_changed_files(repo_root)

        # Check 1: Test immutability (if TestPlan is locked)
        test_failures = self._check_test_immutability(
            artifacts_dir, repo_root, changed_files
        )
        failures.extend(test_failures)

        # Check 2: Artifact-to-code mapping
        mapping_failures = self._check_artifact_to_code_mapping(
            artifacts_dir, repo_root, changed_files
        )
        failures.extend(mapping_failures)

        duration_ms = (time.perf_counter() - start_time) * 1000
        return CIStageResult(
            stage=CIStage.INVARIANT_ENFORCEMENT,
            passed=len(failures) == 0,
            failures=failures,
            duration_ms=duration_ms,
        )

    def _get_changed_files(self, repo_root: Path) -> set[str]:
        """Get list of changed files from git.

        Args:
            repo_root: Path to the repository root.

        Returns:
            Set of changed file paths (relative to repo root).
        """
        try:
            result = subprocess.run(
                [
                    "git",
                    "diff",
                    "--name-only",
                    f"{self._base_branch}...HEAD",
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                # Fallback: diff against previous commit
                result = subprocess.run(
                    [
                        "git",
                        "diff",
                        "--name-only",
                        "HEAD~1",
                    ],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

            files = set()
            for line in result.stdout.strip().split("\n"):
                if line:
                    files.add(line)
            return files

        except (subprocess.SubprocessError, OSError):
            # If git fails, return empty set (fail open)
            return set()

    def _check_test_immutability(
        self,
        artifacts_dir: Path,
        repo_root: Path,
        changed_files: set[str],
    ) -> list[CIFailure]:
        """Check that tests are not modified when TestPlan is locked.

        Args:
            artifacts_dir: Path to the artifacts directory.
            repo_root: Path to the repository root.
            changed_files: Set of changed file paths.

        Returns:
            List of failures for test modifications.
        """
        failures: list[CIFailure] = []

        # Check if TestPlan is locked
        if not self._is_testplan_locked(artifacts_dir):
            return failures

        # Check if any test files were changed
        test_prefix = f"{self._tests_dir}/"
        for file_path in changed_files:
            # Normalize path separators
            normalized = file_path.replace("\\", "/")
            if normalized.startswith(test_prefix):
                failures.append(
                    CIFailure(
                        code=CIFailureCode.TEST_MODIFICATION_AFTER_LOCK,
                        message=f"Test file modified after TestPlan lock: {file_path}",
                        file_path=Path(file_path),
                        details={
                            "modified_file": file_path,
                            "tests_directory": self._tests_dir,
                        },
                    )
                )

        return failures

    def _is_testplan_locked(self, artifacts_dir: Path) -> bool:
        """Check if any TestPlan artifact is locked.

        Args:
            artifacts_dir: Path to the artifacts directory.

        Returns:
            True if a locked TestPlan exists.
        """
        test_plans_dir = artifacts_dir / "test_plans"
        if not test_plans_dir.exists():
            return False

        for json_file in test_plans_dir.glob("*.json"):
            if json_file.name.endswith(".approval.json"):
                continue
            try:
                with json_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                artifact_type = data.get("artifact_type")
                status = data.get("status")

                if (
                    artifact_type == ArtifactType.TEST_PLAN.value
                    and status == ArtifactStatus.LOCKED.value
                ):
                    return True
            except (json.JSONDecodeError, OSError):
                continue

        return False

    def _check_artifact_to_code_mapping(
        self,
        artifacts_dir: Path,
        repo_root: Path,
        changed_files: set[str],
    ) -> list[CIFailure]:
        """Check that code changes are covered by approved plans.

        Args:
            artifacts_dir: Path to the artifacts directory.
            repo_root: Path to the repository root.
            changed_files: Set of changed file paths.

        Returns:
            List of failures for unplanned code changes.
        """
        failures: list[CIFailure] = []

        # Build set of allowed files from plans
        allowed_files = self._get_allowed_files(artifacts_dir)

        # If no plans exist, skip this check
        if not allowed_files:
            return failures

        # Filter to only source files
        source_files = self._filter_source_files(changed_files)

        # Check each source file against allowed set
        for file_path in source_files:
            normalized = file_path.replace("\\", "/")
            if not self._is_file_allowed(normalized, allowed_files):
                failures.append(
                    CIFailure(
                        code=CIFailureCode.UNPLANNED_CODE_CHANGE,
                        message=f"Unplanned code change: {file_path}",
                        file_path=Path(file_path),
                        details={
                            "modified_file": file_path,
                            "allowed_files_count": len(allowed_files),
                        },
                    )
                )

        return failures

    def _get_allowed_files(self, artifacts_dir: Path) -> set[str]:
        """Get set of files allowed to be modified by approved plans.

        Args:
            artifacts_dir: Path to the artifacts directory.

        Returns:
            Set of allowed file paths (normalized).
        """
        allowed: set[str] = set()

        # Get targets from ImplementationPlans
        impl_dir = artifacts_dir / "implementation_plans"
        if impl_dir.exists():
            for json_file in impl_dir.glob("*.json"):
                if json_file.name.endswith(".approval.json"):
                    continue
                target = self._extract_impl_target(json_file)
                if target:
                    allowed.add(target.replace("\\", "/"))

        # Get affected files from RefactorPlans
        refactor_dir = artifacts_dir / "refactor_plans"
        if refactor_dir.exists():
            for json_file in refactor_dir.glob("*.json"):
                if json_file.name.endswith(".approval.json"):
                    continue
                affected = self._extract_refactor_files(json_file)
                for f in affected:
                    allowed.add(f.replace("\\", "/"))

        return allowed

    def _extract_impl_target(self, json_file: Path) -> str | None:
        """Extract target file from ImplementationPlan.

        Args:
            json_file: Path to the artifact JSON file.

        Returns:
            Target file path, or None if not found.
        """
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Check if it's an approved ImplementationPlan
            if data.get("artifact_type") != "ImplementationPlan":
                return None
            if data.get("status") not in ("approved", "locked"):
                return None

            payload = data.get("payload", {})
            return payload.get("target")

        except (json.JSONDecodeError, OSError):
            return None

    def _extract_refactor_files(self, json_file: Path) -> list[str]:
        """Extract affected files from RefactorPlan.

        Args:
            json_file: Path to the artifact JSON file.

        Returns:
            List of affected file paths.
        """
        files: list[str] = []
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Check if it's an approved RefactorPlan
            if data.get("artifact_type") != "RefactorPlan":
                return files
            if data.get("status") not in ("approved", "locked"):
                return files

            payload = data.get("payload", {})
            operations = payload.get("operations", [])

            for op in operations:
                # Extract from/to paths for move operations
                from_path = op.get("from") or op.get("from_path")
                to_path = op.get("to") or op.get("to_path")
                if from_path:
                    files.append(from_path)
                if to_path:
                    files.append(to_path)

        except (json.JSONDecodeError, OSError):
            pass

        return files

    def _filter_source_files(self, changed_files: set[str]) -> set[str]:
        """Filter to only source code files.

        Args:
            changed_files: Set of all changed file paths.

        Returns:
            Set of source file paths only.
        """
        source_files: set[str] = set()

        for file_path in changed_files:
            normalized = file_path.replace("\\", "/")

            # Skip non-Python files for now
            if not normalized.endswith(".py"):
                continue

            # Skip test files
            if normalized.startswith(f"{self._tests_dir}/"):
                continue

            # Skip config/doc files
            if normalized.startswith("docs/"):
                continue
            if normalized.startswith("."):
                continue

            # Check if in a source directory
            for source_dir in self._source_dirs:
                if normalized.startswith(f"{source_dir}/"):
                    source_files.add(file_path)
                    break

        return source_files

    def _is_file_allowed(self, file_path: str, allowed_files: set[str]) -> bool:
        """Check if a file is in the allowed set.

        Args:
            file_path: Normalized file path.
            allowed_files: Set of allowed file paths.

        Returns:
            True if file is allowed.
        """
        # Direct match
        if file_path in allowed_files:
            return True

        # Check if any allowed file is a prefix (directory)
        for allowed in allowed_files:
            if file_path.startswith(allowed.rstrip("/") + "/"):
                return True

        return False
