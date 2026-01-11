"""ValidationRunnerPort protocol for validation runners.

This module defines the interface for validation runners (tests, lint,
architecture, invariants), distinct from the existing ValidatorPort which
handles artifact schema validation.

Following hexagonal architecture, this port is defined in the domain layer
and implemented by adapters.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from rice_factor.domain.artifacts.validation_types import (
        ValidationContext,
        ValidationResult,
    )


@runtime_checkable
class ValidationRunnerPort(Protocol):
    """Protocol for validation runners.

    Validators implementing this protocol are:
    - Emit-only (produce results, no side effects)
    - Deterministic
    - Fail-fast
    - Auditable

    Example implementations:
    - TestRunnerAdapter: Runs native test commands (pytest, cargo test, etc.)
    - LintRunnerAdapter: Runs native lint commands (ruff, clippy, etc.)
    - ArchitectureValidator: Checks hexagonal layer import rules
    - InvariantChecker: Verifies domain invariants

    Note:
        Validators NEVER raise exceptions for validation failures.
        They return ValidationResult(status="failed", errors=[...]).
        Exceptions are only raised for infrastructure/configuration errors.
    """

    @property
    def name(self) -> str:
        """Unique name for this validator.

        Returns:
            A short identifier for the validator (e.g., "test_runner", "lint_runner").
        """
        ...

    def validate(
        self,
        target: Path,
        context: "ValidationContext",
    ) -> "ValidationResult":
        """Validate the target.

        Args:
            target: Path to validate (file, directory, or artifacts directory).
            context: Validation context containing repo_root, language, and config.

        Returns:
            ValidationResult with status ("passed" or "failed") and any errors.

        Note:
            This method should NOT raise exceptions for validation failures.
            Instead, return ValidationResult(status="failed", errors=[...]).
            Only raise exceptions for infrastructure errors (missing commands,
            configuration errors, etc.).
        """
        ...
