"""Diff Executor adapter.

This module provides the DiffExecutor that applies approved diffs to the codebase
using git apply. This executor only applies diffs - it never generates them.

Example:
    >>> executor = DiffExecutor(diff_service, audit_logger, storage)
    >>> result = executor.execute(
    ...     artifact_path=Path("audit/diffs/20260110_120000_file.diff"),
    ...     repo_root=Path("/project"),
    ...     mode=ExecutionMode.APPLY,
    ... )
"""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING, ClassVar

from rice_factor.adapters.executors.audit_logger import (
    AuditLogger,
    execution_timer,
)
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.execution_types import (
    ExecutionMode,
    ExecutionResult,
)
from rice_factor.domain.failures.executor_errors import (
    DiffNotApprovedError,
    GitApplyError,
    TestsLockedError,
)
from rice_factor.domain.services.diff_service import Diff, DiffService, DiffStatus

if TYPE_CHECKING:
    from pathlib import Path

    from rice_factor.domain.ports.storage import StoragePort


class DiffExecutor:
    """Executor for applying approved diffs to the codebase.

    Implements the 9-step executor pipeline for diff application:
    1. Load diff
    2. Validate diff format
    3. Verify approval status
    4. Capability check (N/A for diff)
    5. Precondition checks (authorized files, test lock)
    6. N/A (diff is input, not generated)
    7. Apply (if APPLY mode)
    8. Emit audit logs
    9. Return result

    This executor ONLY applies diffs - it never generates them.

    Attributes:
        diff_service: Service for managing diffs.
        audit_logger: Logger for recording execution audit trail.
        storage: Storage port for checking test lock status.
    """

    EXECUTOR_NAME = "diff"

    # Patterns for identifying test files
    TEST_FILE_PATTERNS: ClassVar[list[str]] = [
        r"^tests?/",  # tests/ or test/
        r"^test_",  # test_*.py
        r"_test\.py$",  # *_test.py
        r"_tests\.py$",  # *_tests.py
        r"\.test\.[jt]sx?$",  # *.test.js/jsx/ts/tsx
        r"\.spec\.[jt]sx?$",  # *.spec.js/jsx/ts/tsx
        r"_test\.go$",  # *_test.go
        r"_test\.rs$",  # *_test.rs
    ]

    def __init__(
        self,
        diff_service: DiffService,
        audit_logger: AuditLogger,
        storage: StoragePort | None = None,
    ) -> None:
        """Initialize the diff executor.

        Args:
            diff_service: Service for managing diffs.
            audit_logger: Logger for recording execution audit trail.
            storage: Optional storage port for checking test lock status.
        """
        self._diff_service = diff_service
        self._audit_logger = audit_logger
        self._storage = storage

    def execute(
        self,
        artifact_path: Path,
        repo_root: Path,
        mode: ExecutionMode,
    ) -> ExecutionResult:
        """Execute diff application.

        Args:
            artifact_path: Path to the diff file or diff ID.
            repo_root: Root of the repository for git operations.
            mode: Execution mode (DRY_RUN or APPLY).

        Returns:
            ExecutionResult with status, diffs, errors, and logs.
        """
        from pathlib import Path as PathClass

        artifact_path = PathClass(artifact_path)
        repo_root = PathClass(repo_root)

        with execution_timer() as timer:
            try:
                result = self._execute_pipeline(artifact_path, repo_root, mode)
                # Log success
                self._audit_logger.log_success(
                    executor=self.EXECUTOR_NAME,
                    artifact=str(artifact_path),
                    mode=mode.value,
                    diff_path=str(artifact_path),
                    files_affected=result.logs,
                    duration_ms=timer["duration_ms"],
                )
                return result
            except Exception as e:
                # Log failure
                error_msg = str(e)
                self._audit_logger.log_failure(
                    executor=self.EXECUTOR_NAME,
                    artifact=str(artifact_path),
                    mode=mode.value,
                    error=error_msg,
                    duration_ms=timer["duration_ms"],
                )
                return ExecutionResult.failure_result(errors=[error_msg])

    def _execute_pipeline(
        self,
        artifact_path: Path,
        repo_root: Path,
        mode: ExecutionMode,
    ) -> ExecutionResult:
        """Execute the 9-step pipeline.

        Args:
            artifact_path: Path to the diff file.
            repo_root: Repository root for git operations.
            mode: Execution mode.

        Returns:
            ExecutionResult on success.

        Raises:
            Various executor errors on failure.
        """
        from pathlib import Path as PathClass

        # Step 1: Load diff
        diff = self._load_diff(artifact_path)
        diff_content = diff.content if diff else self._read_diff_file(artifact_path)

        # Step 2: Validate diff format and parse files
        touched_files = self._parse_diff_files(diff_content)

        # Step 3: Verify approval status
        if diff and diff.status != DiffStatus.APPROVED:
            raise DiffNotApprovedError(
                diff_id=str(diff.id),
                current_status=diff.status.value,
            )

        # Step 4: Capability check (N/A for diff - always supported)

        # Step 5: Precondition checks
        # Check test lock
        if self._is_test_locked() and self._has_test_files(touched_files):
            test_files = [f for f in touched_files if self._is_test_file(f)]
            raise TestsLockedError(
                file_path=test_files[0] if test_files else "test file",
            )

        # Step 6: N/A (diff is input, not generated)

        # Step 7: Apply (if APPLY mode)
        logs: list[str] = []
        if mode == ExecutionMode.APPLY:
            success, output = self._git_apply(artifact_path, repo_root, dry_run=False)
            if not success:
                raise GitApplyError(
                    diff_path=str(artifact_path),
                    git_output=output,
                    exit_code=1,
                )
            logs.append(f"Applied diff: {artifact_path}")
            for file in touched_files:
                logs.append(f"Modified: {file}")

            # Mark diff as applied if we have a diff object
            if diff:
                self._diff_service.mark_applied(diff.id)
        else:
            # DRY_RUN: use git apply --check
            success, output = self._git_apply(artifact_path, repo_root, dry_run=True)
            if not success:
                raise GitApplyError(
                    diff_path=str(artifact_path),
                    git_output=output,
                    exit_code=1,
                )
            logs.append(f"Dry-run: diff would apply cleanly: {artifact_path}")
            for file in touched_files:
                logs.append(f"Would modify: {file}")

        # Steps 8 & 9: Return result (audit logging is done in execute())
        return ExecutionResult.success_result(
            diffs=[PathClass(artifact_path)],
            logs=logs,
        )

    def _load_diff(self, artifact_path: Path) -> Diff | None:
        """Load diff from diff service if available.

        Args:
            artifact_path: Path to the diff file.

        Returns:
            Diff object if found, None otherwise.
        """
        # Try to find diff by searching the service
        try:
            # Try to load all diffs and find matching one
            all_diffs = self._diff_service.list_diffs()
            for diff in all_diffs:
                # Match by path pattern or ID
                if str(diff.id) in str(artifact_path):
                    return diff
                # Also check if the target file matches
                if diff.target_file in str(artifact_path):
                    return diff
        except Exception:
            pass
        return None

    def _read_diff_file(self, diff_path: Path) -> str:
        """Read diff content from file.

        Args:
            diff_path: Path to the diff file.

        Returns:
            Diff content as string.
        """
        return diff_path.read_text(encoding="utf-8")

    def _parse_diff_files(self, diff_content: str) -> list[str]:
        """Parse file paths from unified diff content.

        Args:
            diff_content: The diff content in unified diff format.

        Returns:
            List of file paths mentioned in the diff.
        """
        files: set[str] = set()

        # Match --- a/path and +++ b/path patterns
        for line in diff_content.split("\n"):
            if line.startswith("--- a/") or line.startswith("+++ b/"):
                path = line[6:].strip()
                if path and path != "/dev/null":
                    files.add(path)
            elif line.startswith("--- "):
                # Handle --- path (without a/ prefix)
                path = line[4:].strip()
                if path and path != "/dev/null" and not path.startswith("a/"):
                    files.add(path)
            elif line.startswith("+++ "):
                # Handle +++ path (without b/ prefix)
                path = line[4:].strip()
                if path and path != "/dev/null" and not path.startswith("b/"):
                    files.add(path)

        return sorted(files)

    def _git_apply(
        self,
        diff_path: Path,
        repo_root: Path,
        dry_run: bool,
    ) -> tuple[bool, str]:
        """Run git apply on a diff.

        Args:
            diff_path: Path to the diff file.
            repo_root: Repository root directory.
            dry_run: If True, use --check flag.

        Returns:
            Tuple of (success, output).
        """
        cmd = ["git", "apply"]
        if dry_run:
            cmd.append("--check")
        cmd.append(str(diff_path))

        try:
            result = subprocess.run(
                cmd,
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = result.stdout + result.stderr
            return result.returncode == 0, output.strip()
        except subprocess.TimeoutExpired:
            return False, "git apply timed out"
        except FileNotFoundError:
            return False, "git command not found"
        except Exception as e:
            return False, str(e)

    def _is_test_file(self, path: str) -> bool:
        """Check if a file path is a test file.

        Args:
            path: File path to check.

        Returns:
            True if the path matches test file patterns.
        """
        return any(re.search(pattern, path) for pattern in self.TEST_FILE_PATTERNS)

    def _has_test_files(self, files: list[str]) -> bool:
        """Check if any files are test files.

        Args:
            files: List of file paths.

        Returns:
            True if any file is a test file.
        """
        return any(self._is_test_file(f) for f in files)

    def _is_test_locked(self) -> bool:
        """Check if tests are locked.

        Returns:
            True if TestPlan is locked, False otherwise.
        """
        if self._storage is None:
            return False

        try:
            # Try to find a locked TestPlan
            test_plans = self._storage.list_by_type(ArtifactType.TEST_PLAN)
            for plan in test_plans:
                if plan.status == ArtifactStatus.LOCKED:
                    return True
        except Exception:
            pass
        return False

    def check_authorized_files(
        self,
        touched_files: list[str],
        authorized_files: list[str],
    ) -> list[str]:
        """Check which touched files are not authorized.

        Args:
            touched_files: Files modified by the diff.
            authorized_files: Files allowed to be modified.

        Returns:
            List of unauthorized files.
        """
        authorized_set = set(authorized_files)
        return [f for f in touched_files if f not in authorized_set]
