"""Executor port protocol definition.

This module defines the ExecutorPort protocol that all executor adapters must
implement. Executors are dumb, deterministic, stateless, fail-fast tools that
apply approved artifacts to the codebase.

Executors are NOT allowed to:
- Infer intent
- Repair artifacts
- Recover silently
- Call LLMs
- Mutate artifacts

Think: Unix tools, not agents.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from rice_factor.domain.artifacts.execution_types import (
        ExecutionMode,
        ExecutionResult,
    )


@runtime_checkable
class ExecutorPort(Protocol):
    """Abstract interface for all executors.

    All executors must implement this protocol. Executors follow a strict
    9-step pipeline:
    1. Load artifact
    2. Validate schema
    3. Verify approval & lock status
    4. Capability check (per language)
    5. Precondition checks
    6. Generate diff
    7. (If APPLY) Apply diff
    8. Emit audit logs
    9. Return result

    Executors are:
    - Stateless: No state between invocations
    - Deterministic: Same input always produces same output
    - Fail-fast: Fail immediately on any precondition violation
    - Auditable: Every action is logged

    Example:
        >>> executor = ScaffoldExecutor(storage, validator)
        >>> result = executor.execute(
        ...     artifact_path=Path("artifacts/planning/scaffold_plan.json"),
        ...     repo_root=Path("/path/to/repo"),
        ...     mode=ExecutionMode.DRY_RUN
        ... )
        >>> if result.success:
        ...     print(f"Generated diffs: {result.diffs}")
    """

    def execute(
        self,
        artifact_path: Path,
        repo_root: Path,
        mode: "ExecutionMode",
    ) -> "ExecutionResult":
        """Execute the operation defined by the artifact.

        This method implements the full 9-step executor pipeline. It loads
        the artifact, validates it, checks preconditions, generates diffs,
        and optionally applies them.

        Args:
            artifact_path: Path to the artifact JSON file. Must be an
                approved artifact of the correct type for this executor.
            repo_root: Root directory of the target repository. All file
                operations are relative to this path.
            mode: Execution mode - DRY_RUN generates diff without applying,
                APPLY generates diff and applies it.

        Returns:
            ExecutionResult containing:
            - status: "success" or "failure"
            - diffs: List of paths to generated diff files
            - errors: List of error messages (if any)
            - logs: List of log messages

        Raises:
            ExecutorPreconditionError: Preconditions not met (e.g., artifact
                not approved, file already exists, path escapes repo).
            ExecutorCapabilityError: Operation not supported for the
                target language.
            ExecutorArtifactError: Invalid artifact (schema violation,
                wrong type).
            ExecutorApplyError: Failed to apply diff (git apply failed,
                file write failed).

        Note:
            Executors MUST emit audit logs before returning. An execution
            without an audit log entry is considered invalid.
        """
        ...
