"""Validation orchestrator for running all validation steps.

This module orchestrates schema, architecture, test, and lint validations,
aggregating results into a ValidationResult artifact.

The orchestrator uses dependency injection to receive validators, allowing
for proper separation between domain and adapter layers.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.payloads.validation_result import ValidationStatus
from rice_factor.domain.artifacts.validation_types import (
    ValidationContext,
)
from rice_factor.domain.artifacts.validation_types import (
    ValidationResult as RunnerValidationResult,
)

if TYPE_CHECKING:
    from rice_factor.domain.ports.storage import StoragePort
    from rice_factor.domain.ports.validation_runner import ValidationRunnerPort


class ValidationStep(str, Enum):
    """Types of validation steps."""

    SCHEMA = "schema"
    ARCHITECTURE = "architecture"
    TESTS = "tests"
    LINT = "lint"
    INVARIANTS = "invariants"


@dataclass
class StepResult:
    """Result of a single validation step.

    Attributes:
        step: The validation step that was run.
        status: Whether the step passed or failed.
        errors: List of error messages if the step failed.
        duration_ms: Time taken to run the step in milliseconds.
        details: Additional details about the validation.
    """

    step: ValidationStep
    status: ValidationStatus
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    details: dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Aggregated result of all validation steps.

    Attributes:
        overall_status: Whether all validations passed.
        step_results: Results for each validation step.
        total_duration_ms: Total time taken for all validations.
    """

    overall_status: ValidationStatus
    step_results: list[StepResult] = field(default_factory=list)
    total_duration_ms: float = 0.0

    @property
    def passed(self) -> bool:
        """Check if all validations passed."""
        return self.overall_status == ValidationStatus.PASSED

    @property
    def failed_steps(self) -> list[StepResult]:
        """Get list of failed validation steps."""
        return [r for r in self.step_results if r.status == ValidationStatus.FAILED]

    @property
    def error_count(self) -> int:
        """Get total number of errors across all steps."""
        return sum(len(r.errors) for r in self.step_results)


class StorageFactory(Protocol):
    """Factory protocol for creating storage adapters.

    This allows the orchestrator to create storage without directly
    depending on adapter implementations.
    """

    def __call__(self, artifacts_dir: Path) -> "StoragePort":
        """Create a storage adapter for the given directory."""
        ...


class ValidationOrchestrator:
    """Orchestrates validation steps for a project.

    Runs schema, architecture, test, and lint validations,
    collecting results into an aggregated ValidationResult.

    Uses dependency injection for validators to maintain hexagonal
    architecture separation.

    Attributes:
        project_path: Path to the project root.
    """

    def __init__(
        self,
        project_path: Path,
        *,
        language: str = "python",
        config: dict[str, Any] | None = None,
        test_runner: "ValidationRunnerPort | None" = None,
        lint_runner: "ValidationRunnerPort | None" = None,
        architecture_validator: "ValidationRunnerPort | None" = None,
        invariant_checker: "ValidationRunnerPort | None" = None,
        storage_factory: StorageFactory | None = None,
    ) -> None:
        """Initialize the validation orchestrator.

        Args:
            project_path: Path to the project root directory.
            language: Programming language of the project.
            config: Optional configuration dictionary.
            test_runner: Optional test runner validator.
            lint_runner: Optional lint runner validator.
            architecture_validator: Optional architecture validator.
            invariant_checker: Optional invariant checker.
            storage_factory: Optional factory for creating storage adapters.
        """
        self._project_path = project_path
        self._artifacts_dir = project_path / "artifacts"
        self._language = language
        self._config = config or {}

        # Store validators (will be lazily initialized if None)
        self._test_runner = test_runner
        self._lint_runner = lint_runner
        self._architecture_validator = architecture_validator
        self._invariant_checker = invariant_checker
        self._storage_factory = storage_factory

        # Lazy initialization flags
        self._validators_initialized = False

    def _ensure_validators_initialized(self) -> None:
        """Lazily initialize validators if not provided."""
        if self._validators_initialized:
            return

        # Import adapters here to avoid import at module level
        # This maintains flexibility while allowing default behavior
        if self._test_runner is None:
            from rice_factor.adapters.validators import TestRunnerAdapter
            self._test_runner = TestRunnerAdapter()

        if self._lint_runner is None:
            from rice_factor.adapters.validators import LintRunnerAdapter
            self._lint_runner = LintRunnerAdapter()

        if self._architecture_validator is None:
            from rice_factor.adapters.validators import ArchitectureValidator
            self._architecture_validator = ArchitectureValidator()

        if self._invariant_checker is None:
            from rice_factor.adapters.validators import InvariantChecker
            self._invariant_checker = InvariantChecker()

        if self._storage_factory is None:
            from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter

            def default_storage_factory(d: Path) -> FilesystemStorageAdapter:
                return FilesystemStorageAdapter(artifacts_dir=d)

            self._storage_factory = default_storage_factory  # type: ignore[assignment]

        self._validators_initialized = True

    @property
    def project_path(self) -> Path:
        """Get the project path."""
        return self._project_path

    def _get_validation_context(self) -> ValidationContext:
        """Create a validation context for validators."""
        return ValidationContext(
            repo_root=self._project_path,
            language=self._language,
            config=self._config,
        )

    def run_all(self, steps: list[ValidationStep] | None = None) -> ValidationResult:
        """Run all (or specified) validation steps.

        Args:
            steps: Optional list of steps to run. If None, runs all steps.

        Returns:
            Aggregated validation result with all step results.
        """
        self._ensure_validators_initialized()

        if steps is None:
            steps = list(ValidationStep)

        step_results: list[StepResult] = []
        total_duration = 0.0

        for step in steps:
            result = self.run_step(step)
            step_results.append(result)
            total_duration += result.duration_ms

        # Determine overall status
        overall_status = ValidationStatus.PASSED
        for result in step_results:
            if result.status == ValidationStatus.FAILED:
                overall_status = ValidationStatus.FAILED
                break

        return ValidationResult(
            overall_status=overall_status,
            step_results=step_results,
            total_duration_ms=total_duration,
        )

    def run_step(self, step: ValidationStep) -> StepResult:
        """Run a single validation step.

        Args:
            step: The validation step to run.

        Returns:
            Result of the validation step.
        """
        self._ensure_validators_initialized()

        if step == ValidationStep.SCHEMA:
            return self._run_schema_validation()
        elif step == ValidationStep.ARCHITECTURE:
            return self._run_architecture_validation()
        elif step == ValidationStep.TESTS:
            return self._run_test_validation()
        elif step == ValidationStep.LINT:
            return self._run_lint_validation()
        elif step == ValidationStep.INVARIANTS:
            return self._run_invariant_validation()
        else:
            return StepResult(
                step=step,
                status=ValidationStatus.FAILED,
                errors=[f"Unknown validation step: {step}"],
            )

    def _run_schema_validation(self) -> StepResult:
        """Run schema validation on all artifacts.

        Returns:
            Result of schema validation.
        """
        errors: list[str] = []
        details: dict[str, str] = {}

        if not self._artifacts_dir.exists():
            return StepResult(
                step=ValidationStep.SCHEMA,
                status=ValidationStatus.PASSED,
                errors=[],
                details={"message": "No artifacts directory found"},
            )

        assert self._storage_factory is not None
        storage = self._storage_factory(self._artifacts_dir)

        # Validate all artifacts by type
        artifact_count = 0
        for artifact_type in ArtifactType:
            try:
                artifacts = storage.list_by_type(artifact_type)
                for artifact in artifacts:
                    artifact_count += 1
                    # Artifact was already validated on load, so it passed
                    details[str(artifact.id)] = "valid"
            except Exception as e:
                errors.append(f"Error validating {artifact_type.value}: {e}")

        status = ValidationStatus.PASSED if not errors else ValidationStatus.FAILED
        details["artifacts_validated"] = str(artifact_count)

        return StepResult(
            step=ValidationStep.SCHEMA,
            status=status,
            errors=errors,
            details=details,
        )

    def _run_architecture_validation(self) -> StepResult:
        """Run architecture rule validation.

        Returns:
            Result of architecture validation.
        """
        context = self._get_validation_context()

        try:
            assert self._architecture_validator is not None
            result = self._architecture_validator.validate(self._project_path, context)
            return self._convert_runner_result(ValidationStep.ARCHITECTURE, result)
        except Exception as e:
            return StepResult(
                step=ValidationStep.ARCHITECTURE,
                status=ValidationStatus.FAILED,
                errors=[f"Architecture validation error: {e}"],
            )

    def _run_test_validation(self) -> StepResult:
        """Run test suite validation.

        Returns:
            Result of test validation.
        """
        context = self._get_validation_context()

        try:
            assert self._test_runner is not None
            result = self._test_runner.validate(self._project_path, context)
            return self._convert_runner_result(ValidationStep.TESTS, result)
        except Exception as e:
            return StepResult(
                step=ValidationStep.TESTS,
                status=ValidationStatus.FAILED,
                errors=[f"Test validation error: {e}"],
            )

    def _run_lint_validation(self) -> StepResult:
        """Run lint validation.

        Returns:
            Result of lint validation.
        """
        context = self._get_validation_context()

        try:
            assert self._lint_runner is not None
            result = self._lint_runner.validate(self._project_path, context)
            return self._convert_runner_result(ValidationStep.LINT, result)
        except Exception as e:
            return StepResult(
                step=ValidationStep.LINT,
                status=ValidationStatus.FAILED,
                errors=[f"Lint validation error: {e}"],
            )

    def _run_invariant_validation(self) -> StepResult:
        """Run invariant checking.

        Returns:
            Result of invariant validation.
        """
        context = self._get_validation_context()

        try:
            assert self._invariant_checker is not None
            result = self._invariant_checker.validate(self._artifacts_dir, context)
            return self._convert_runner_result(ValidationStep.INVARIANTS, result)
        except Exception as e:
            return StepResult(
                step=ValidationStep.INVARIANTS,
                status=ValidationStatus.FAILED,
                errors=[f"Invariant check error: {e}"],
            )

    def _convert_runner_result(
        self,
        step: ValidationStep,
        result: RunnerValidationResult,
    ) -> StepResult:
        """Convert a ValidationRunnerPort result to StepResult.

        Args:
            step: The validation step.
            result: The runner result to convert.

        Returns:
            Converted StepResult.
        """
        status = ValidationStatus.PASSED if result.passed else ValidationStatus.FAILED
        return StepResult(
            step=step,
            status=status,
            errors=result.errors,
            duration_ms=float(result.duration_ms),
            details={"validator": result.validator},
        )
