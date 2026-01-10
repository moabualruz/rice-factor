"""Refactor Executor adapter.

This module provides the RefactorExecutorAdapter that performs mechanical
refactoring operations (move_file, rename_symbol) from an approved RefactorPlan
artifact. It integrates with the capability registry to check operation support.

Example:
    >>> executor = RefactorExecutorAdapter(
    ...     storage=storage,
    ...     capability_registry=registry,
    ...     audit_logger=logger,
    ... )
    >>> result = executor.execute(
    ...     artifact_path=Path("artifacts/refactor_plan.json"),
    ...     repo_root=Path("/project"),
    ...     mode=ExecutionMode.DRY_RUN,
    ... )
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
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
from rice_factor.domain.artifacts.payloads.refactor_plan import (
    RefactorOperation,
    RefactorOperationType,
    RefactorPlanPayload,
)
from rice_factor.domain.failures.executor_errors import (
    ArtifactNotApprovedError,
    ArtifactTypeError,
    FileAlreadyExistsError,
    SourceFileNotFoundError,
    UnsupportedOperationError,
)

if TYPE_CHECKING:
    from rice_factor.adapters.executors.capability_registry import CapabilityRegistry
    from rice_factor.domain.ports.storage import StoragePort


class RefactorExecutorAdapter:
    """Executor adapter for refactoring operations from RefactorPlan artifacts.

    Implements the 9-step executor pipeline for refactoring:
    1. Load artifact
    2. Validate schema
    3. Verify approval status
    4. Capability check (per language)
    5. Precondition checks (source exists, dest doesn't)
    6. Generate diff
    7. Apply (if APPLY mode)
    8. Emit audit logs
    9. Return result

    Attributes:
        storage: Storage port for loading artifacts.
        capability_registry: Registry for checking operation support.
        audit_logger: Logger for recording execution audit trail.
    """

    EXECUTOR_NAME = "refactor"

    # Language detection files
    LANGUAGE_MARKERS: ClassVar[dict[str, list[str]]] = {
        "python": ["pyproject.toml", "setup.py", "requirements.txt"],
        "rust": ["Cargo.toml"],
        "go": ["go.mod"],
        "javascript": ["package.json"],
        "typescript": ["package.json", "tsconfig.json"],
        "java": ["pom.xml", "build.gradle"],
    }

    def __init__(
        self,
        storage: StoragePort,
        capability_registry: CapabilityRegistry,
        audit_logger: AuditLogger,
    ) -> None:
        """Initialize the refactor executor adapter.

        Args:
            storage: Storage port for loading artifacts.
            capability_registry: Registry for checking operation support.
            audit_logger: Logger for recording execution audit trail.
        """
        self._storage = storage
        self._capability_registry = capability_registry
        self._audit_logger = audit_logger

    def execute(
        self,
        artifact_path: Path,
        repo_root: Path,
        mode: ExecutionMode,
    ) -> ExecutionResult:
        """Execute refactoring operations from a RefactorPlan.

        Args:
            artifact_path: Path to the RefactorPlan artifact.
            repo_root: Root of the repository for file operations.
            mode: Execution mode (DRY_RUN or APPLY).

        Returns:
            ExecutionResult with status, diffs, errors, and logs.
        """
        artifact_path = Path(artifact_path)
        repo_root = Path(repo_root)

        with execution_timer() as timer:
            try:
                result = self._execute_pipeline(artifact_path, repo_root, mode)
                # Log success
                self._audit_logger.log_success(
                    executor=self.EXECUTOR_NAME,
                    artifact=str(artifact_path),
                    mode=mode.value,
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
            artifact_path: Path to the artifact.
            repo_root: Repository root for operations.
            mode: Execution mode.

        Returns:
            ExecutionResult on success.

        Raises:
            Various executor errors on failure.
        """
        # Step 1: Load artifact
        artifact = self._storage.load(artifact_path)

        # Step 2: Validate artifact type
        if artifact.artifact_type != ArtifactType.REFACTOR_PLAN:
            raise ArtifactTypeError(
                expected_type=ArtifactType.REFACTOR_PLAN.value,
                actual_type=artifact.artifact_type.value,
            )

        # Step 3: Verify approval status
        if artifact.status not in (ArtifactStatus.APPROVED, ArtifactStatus.LOCKED):
            raise ArtifactNotApprovedError(
                artifact_id=str(artifact.id),
                current_status=artifact.status.value,
            )

        # Cast is safe because we verified artifact_type above
        payload = artifact.payload
        if not isinstance(payload, RefactorPlanPayload):
            raise ArtifactTypeError(
                expected_type=ArtifactType.REFACTOR_PLAN.value,
                actual_type=type(payload).__name__,
            )

        # Step 4: Capability check
        language = self._detect_language(repo_root)
        for operation in payload.operations:
            op_name = self._get_operation_name(operation.type)
            if not self._capability_registry.check_capability(op_name, language):
                raise UnsupportedOperationError(
                    operation=op_name,
                    language=language,
                    message=f"Operation '{op_name}' not supported for {language}",
                )

        # Step 5: Precondition checks
        for operation in payload.operations:
            self._check_preconditions(operation, repo_root)

        # Step 6: Generate diffs
        diffs_content: list[str] = []
        for operation in payload.operations:
            diff = self._generate_diff(operation, repo_root)
            if diff:
                diffs_content.append(diff)

        # Save combined diff
        diff_path = self._save_diff(diffs_content, repo_root)
        logs: list[str] = []

        # Step 7: Apply (if APPLY mode)
        if mode == ExecutionMode.APPLY:
            for operation in payload.operations:
                self._apply_operation(operation, repo_root)
                logs.append(f"Applied: {self._describe_operation(operation)}")
        else:
            for operation in payload.operations:
                logs.append(f"Would apply: {self._describe_operation(operation)}")

        # Steps 8 & 9: Return result (audit logging is done in execute())
        return ExecutionResult.success_result(
            diffs=[diff_path],
            logs=logs,
        )

    def _detect_language(self, repo_root: Path) -> str:
        """Detect the primary language of the repository.

        Args:
            repo_root: Repository root directory.

        Returns:
            Language string matching capability registry keys.
        """
        for language, markers in self.LANGUAGE_MARKERS.items():
            for marker in markers:
                if (repo_root / marker).exists():
                    return language

        # Fallback to file extension analysis
        extensions: dict[str, int] = {}
        for file in repo_root.rglob("*"):
            if file.is_file() and file.suffix:
                ext = file.suffix.lower()
                extensions[ext] = extensions.get(ext, 0) + 1

        ext_to_lang = {
            ".py": "python",
            ".rs": "rust",
            ".go": "go",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
        }

        if extensions:
            top_ext = max(extensions, key=extensions.get)  # type: ignore[arg-type]
            return ext_to_lang.get(top_ext, "unknown")

        return "unknown"

    def _get_operation_name(self, op_type: RefactorOperationType) -> str:
        """Convert operation type to capability registry operation name.

        Args:
            op_type: The operation type enum.

        Returns:
            Operation name string.
        """
        return op_type.value

    def _check_preconditions(
        self,
        operation: RefactorOperation,
        repo_root: Path,
    ) -> None:
        """Check preconditions for an operation.

        Args:
            operation: The operation to check.
            repo_root: Repository root.

        Raises:
            SourceFileNotFoundError: If source file doesn't exist.
            FileAlreadyExistsError: If destination already exists.
        """
        if operation.type == RefactorOperationType.MOVE_FILE:
            if operation.from_path:
                source = repo_root / operation.from_path
                if not source.exists():
                    raise SourceFileNotFoundError(file_path=operation.from_path)
            if operation.to_path:
                dest = repo_root / operation.to_path
                if dest.exists():
                    raise FileAlreadyExistsError(file_path=operation.to_path)

        elif operation.type == RefactorOperationType.RENAME_SYMBOL:
            if operation.from_path:
                source = repo_root / operation.from_path
                if not source.exists():
                    raise SourceFileNotFoundError(file_path=operation.from_path)

    def _generate_diff(
        self,
        operation: RefactorOperation,
        repo_root: Path,
    ) -> str:
        """Generate a unified diff for an operation.

        Args:
            operation: The operation to generate diff for.
            repo_root: Repository root.

        Returns:
            Unified diff string.
        """
        if operation.type == RefactorOperationType.MOVE_FILE:
            return self._generate_move_file_diff(operation, repo_root)
        elif operation.type == RefactorOperationType.RENAME_SYMBOL:
            return self._generate_rename_symbol_diff(operation, repo_root)

        return ""

    def _generate_move_file_diff(
        self,
        operation: RefactorOperation,
        repo_root: Path,
    ) -> str:
        """Generate diff for file move operation.

        Args:
            operation: The move operation.
            repo_root: Repository root.

        Returns:
            Unified diff string.
        """
        from_path = operation.from_path or ""
        to_path = operation.to_path or ""

        if not from_path:
            return ""

        source = repo_root / from_path
        if not source.exists():
            return ""

        diff_lines = [
            f"diff --git a/{from_path} b/{to_path}",
            f"rename from {from_path}",
            f"rename to {to_path}",
            f"--- a/{from_path}",
            f"+++ b/{to_path}",
        ]

        return "\n".join(diff_lines)

    def _generate_rename_symbol_diff(
        self,
        operation: RefactorOperation,
        repo_root: Path,
    ) -> str:
        """Generate diff for symbol rename operation.

        Args:
            operation: The rename operation.
            repo_root: Repository root.

        Returns:
            Unified diff string.
        """
        file_path = operation.from_path or ""
        old_symbol = operation.symbol or ""
        new_symbol = operation.to_path or ""  # to_path used for new name

        if not file_path or not old_symbol or not new_symbol:
            return ""

        source = repo_root / file_path
        if not source.exists():
            return ""

        content = source.read_text(encoding="utf-8")
        lines = content.split("\n")
        new_content = content.replace(old_symbol, new_symbol)
        new_lines = new_content.split("\n")

        diff_lines = [
            f"diff --git a/{file_path} b/{file_path}",
            f"--- a/{file_path}",
            f"+++ b/{file_path}",
        ]

        # Generate hunks showing changes
        for i, (old_line, new_line) in enumerate(zip(lines, new_lines, strict=True)):
            if old_line != new_line:
                diff_lines.append(f"@@ -{i + 1},1 +{i + 1},1 @@")
                diff_lines.append(f"-{old_line}")
                diff_lines.append(f"+{new_line}")

        return "\n".join(diff_lines)

    def _save_diff(
        self,
        diffs_content: list[str],
        repo_root: Path,
    ) -> Path:
        """Save combined diff to audit directory.

        Args:
            diffs_content: List of diff strings.
            repo_root: Repository root.

        Returns:
            Path to the saved diff file.
        """
        audit_dir = repo_root / "audit" / "diffs"
        audit_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        diff_path = audit_dir / f"{timestamp}_refactor.diff"

        combined_diff = "\n\n".join(diffs_content)
        diff_path.write_text(combined_diff, encoding="utf-8")

        return diff_path

    def _apply_operation(
        self,
        operation: RefactorOperation,
        repo_root: Path,
    ) -> None:
        """Apply an operation to the filesystem.

        Args:
            operation: The operation to apply.
            repo_root: Repository root.
        """
        if operation.type == RefactorOperationType.MOVE_FILE:
            self._apply_move_file(operation, repo_root)
        elif operation.type == RefactorOperationType.RENAME_SYMBOL:
            self._apply_rename_symbol(operation, repo_root)

    def _apply_move_file(
        self,
        operation: RefactorOperation,
        repo_root: Path,
    ) -> None:
        """Apply file move operation.

        Args:
            operation: The move operation.
            repo_root: Repository root.
        """
        from_path = operation.from_path
        to_path = operation.to_path

        if not from_path or not to_path:
            return

        source = repo_root / from_path
        dest = repo_root / to_path

        # Create parent directories
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Move the file
        shutil.move(str(source), str(dest))

    def _apply_rename_symbol(
        self,
        operation: RefactorOperation,
        repo_root: Path,
    ) -> None:
        """Apply symbol rename operation.

        Args:
            operation: The rename operation.
            repo_root: Repository root.
        """
        file_path = operation.from_path
        old_symbol = operation.symbol
        new_symbol = operation.to_path  # to_path used for new name

        if not file_path or not old_symbol or new_symbol is None:
            return

        source = repo_root / file_path
        content = source.read_text(encoding="utf-8")
        new_content = content.replace(old_symbol, new_symbol)
        source.write_text(new_content, encoding="utf-8")

    def _describe_operation(self, operation: RefactorOperation) -> str:
        """Create a human-readable description of an operation.

        Args:
            operation: The operation to describe.

        Returns:
            Description string.
        """
        if operation.type == RefactorOperationType.MOVE_FILE:
            return f"move_file: {operation.from_path} -> {operation.to_path}"
        elif operation.type == RefactorOperationType.RENAME_SYMBOL:
            return f"rename_symbol: {operation.symbol} -> {operation.to_path} in {operation.from_path}"
        elif operation.type == RefactorOperationType.EXTRACT_INTERFACE:
            return f"extract_interface: {operation.symbol} in {operation.from_path}"
        elif operation.type == RefactorOperationType.ENFORCE_DEPENDENCY:
            return f"enforce_dependency: {operation.from_path} -> {operation.to_path}"
        return f"{operation.type.value}"
