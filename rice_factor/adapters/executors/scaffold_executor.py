"""Scaffold Executor adapter.

This module provides the ScaffoldExecutor that creates empty files and directories
from an approved ScaffoldPlan artifact. It implements the ExecutorPort protocol
with the full 9-step pipeline.

Example:
    >>> executor = ScaffoldExecutor(storage, audit_logger, project_root)
    >>> result = executor.execute(
    ...     artifact_path=Path("artifacts/scaffold_plan.json"),
    ...     repo_root=Path("/project"),
    ...     mode=ExecutionMode.APPLY,
    ... )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rice_factor.adapters.executors.audit_logger import (
    AuditLogger,
    execution_timer,
)
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.execution_types import (
    ExecutionMode,
    ExecutionResult,
)
from rice_factor.domain.failures.errors import ArtifactNotFoundError
from rice_factor.domain.failures.executor_errors import (
    ArtifactNotApprovedError,
    ArtifactSchemaError,
    ArtifactTypeError,
    PathEscapesRepoError,
)
from rice_factor.domain.services.scaffold_service import ScaffoldService

if TYPE_CHECKING:
    from pathlib import Path

    from rice_factor.domain.artifacts.payloads.scaffold_plan import (
        FileEntry,
        ScaffoldPlanPayload,
    )
    from rice_factor.domain.ports.storage import StoragePort


class ScaffoldExecutor:
    """Executor for creating files from ScaffoldPlan artifacts.

    Implements the 9-step executor pipeline for scaffold operations:
    1. Load artifact
    2. Validate schema
    3. Verify approval status
    4. Capability check (N/A for scaffold)
    5. Precondition checks (path security)
    6. Generate diff
    7. Apply (if APPLY mode)
    8. Emit audit logs
    9. Return result

    Attributes:
        storage: Storage port for loading artifacts.
        audit_logger: Logger for recording execution audit trail.
        project_root: Root directory for scaffold operations.
    """

    EXECUTOR_NAME = "scaffold"

    def __init__(
        self,
        storage: StoragePort,
        audit_logger: AuditLogger,
        project_root: Path,
    ) -> None:
        """Initialize the scaffold executor.

        Args:
            storage: Storage port for loading artifacts.
            audit_logger: Logger for recording execution audit trail.
            project_root: Root directory for scaffold operations.
        """
        from pathlib import Path as PathClass

        self._storage = storage
        self._audit_logger = audit_logger
        self._project_root = PathClass(project_root)
        self._scaffold_service = ScaffoldService(project_root=self._project_root)

    def execute(
        self,
        artifact_path: Path,
        repo_root: Path,
        mode: ExecutionMode,
    ) -> ExecutionResult:
        """Execute scaffold operations from an artifact.

        Args:
            artifact_path: Path to the ScaffoldPlan artifact.
            repo_root: Root of the repository (for path security checks).
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
                    diff_path=str(result.diffs[0]) if result.diffs else None,
                    files_affected=[str(p) for p in result.diffs],
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
            artifact_path: Path to the artifact.
            repo_root: Repository root for security checks.
            mode: Execution mode.

        Returns:
            ExecutionResult on success.

        Raises:
            Various executor errors on failure.
        """
        from pathlib import Path as PathClass

        # Step 1: Load artifact
        try:
            envelope = self._storage.load(artifact_path)
        except ArtifactNotFoundError:
            raise
        except Exception as e:
            raise ArtifactSchemaError(
                artifact_path=str(artifact_path),
                validation_errors=[str(e)],
            ) from e

        # Step 2: Validate schema (already done by storage.load)
        # Step 3: Verify approval status
        if envelope.artifact_type != ArtifactType.SCAFFOLD_PLAN:
            raise ArtifactTypeError(
                expected_type="ScaffoldPlan",
                actual_type=envelope.artifact_type.value,
            )

        if envelope.status != ArtifactStatus.APPROVED:
            raise ArtifactNotApprovedError(
                artifact_id=str(envelope.id),
                current_status=envelope.status.value,
            )

        # Extract payload
        payload: ScaffoldPlanPayload = envelope.payload  # type: ignore[assignment]

        # Step 4: Capability check (N/A for scaffold - always supported)

        # Step 5: Precondition checks (path security)
        for entry in payload.files:
            if self._path_escapes_repo(entry.path, repo_root):
                raise PathEscapesRepoError(
                    path=entry.path,
                    repo_root=str(repo_root),
                )

        # Step 6: Generate diff
        diff_content = self._generate_diff(payload.files, repo_root)
        diff_path = self._audit_logger.save_diff(diff_content, self.EXECUTOR_NAME)

        # Step 7: Apply (if APPLY mode)
        logs: list[str] = []
        if mode == ExecutionMode.APPLY:
            result = self._scaffold_service.scaffold(payload, dry_run=False)
            for path in result.created:
                logs.append(f"Created: {path}")
            for path in result.skipped:
                logs.append(f"Skipped (exists): {path}")
            for path, error in result.errors:
                logs.append(f"Error: {path} - {error}")
        else:
            # DRY_RUN: just preview
            for entry in payload.files:
                file_path = repo_root / entry.path
                if file_path.exists():
                    logs.append(f"Would skip (exists): {entry.path}")
                else:
                    logs.append(f"Would create: {entry.path}")

        # Steps 8 & 9: Return result (audit logging is done in execute())
        return ExecutionResult.success_result(
            diffs=[PathClass(diff_path)],
            logs=logs,
        )

    def _path_escapes_repo(self, path: str, repo_root: Path) -> bool:
        """Check if a path would escape the repository root.

        Args:
            path: Relative path to check.
            repo_root: Repository root path.

        Returns:
            True if the path escapes the repo, False otherwise.
        """
        try:
            # Resolve the full path
            full_path = (repo_root / path).resolve()
            repo_resolved = repo_root.resolve()

            # Check if path is within repo
            # Using is_relative_to for Python 3.9+
            return not str(full_path).startswith(str(repo_resolved))
        except (ValueError, OSError):
            # Any resolution error means the path is suspicious
            return True

    def _generate_diff(self, files: list[FileEntry], repo_root: Path) -> str:
        """Generate a unified diff showing file creation.

        Args:
            files: List of file entries to scaffold.
            repo_root: Repository root for path resolution.

        Returns:
            Unified diff format string.
        """
        diff_lines: list[str] = []

        for entry in files:
            file_path = repo_root / entry.path

            # Skip existing files (they won't be modified)
            if file_path.exists():
                continue

            # Generate the TODO content for this file
            content = self._scaffold_service.generate_todo_comment(entry)
            content_lines = content.split("\n") if content else []

            # Generate unified diff format
            diff_lines.append(f"diff --git a/{entry.path} b/{entry.path}")
            diff_lines.append("new file mode 100644")
            diff_lines.append("--- /dev/null")
            diff_lines.append(f"+++ b/{entry.path}")

            if content_lines:
                # Remove empty trailing line if present
                if content_lines and content_lines[-1] == "":
                    content_lines = content_lines[:-1]

                diff_lines.append(f"@@ -0,0 +1,{len(content_lines)} @@")
                for line in content_lines:
                    diff_lines.append(f"+{line}")
            else:
                diff_lines.append("@@ -0,0 +0,0 @@")

            diff_lines.append("")  # Blank line between files

        return "\n".join(diff_lines)
