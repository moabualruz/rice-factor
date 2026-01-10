"""Validation orchestrator for running all validation steps.

This module orchestrates schema, architecture, test, and lint validations,
aggregating results into a ValidationResult artifact.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.payloads.validation_result import ValidationStatus


class ValidationStep(str, Enum):
    """Types of validation steps."""

    SCHEMA = "schema"
    ARCHITECTURE = "architecture"
    TESTS = "tests"
    LINT = "lint"


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


class ValidationOrchestrator:
    """Orchestrates validation steps for a project.

    Runs schema, architecture, test, and lint validations,
    collecting results into an aggregated ValidationResult.

    Attributes:
        project_path: Path to the project root.
    """

    def __init__(self, project_path: Path) -> None:
        """Initialize the validation orchestrator.

        Args:
            project_path: Path to the project root directory.
        """
        self._project_path = project_path
        self._artifacts_dir = project_path / "artifacts"

    @property
    def project_path(self) -> Path:
        """Get the project path."""
        return self._project_path

    def run_all(self) -> ValidationResult:
        """Run all validation steps.

        Returns:
            Aggregated validation result with all step results.
        """
        step_results: list[StepResult] = []
        total_duration = 0.0

        for step in ValidationStep:
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
        if step == ValidationStep.SCHEMA:
            return self._run_schema_validation()
        elif step == ValidationStep.ARCHITECTURE:
            return self._run_architecture_validation()
        elif step == ValidationStep.TESTS:
            return self._run_test_validation()
        elif step == ValidationStep.LINT:
            return self._run_lint_validation()
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

        storage = FilesystemStorageAdapter(artifacts_dir=self._artifacts_dir)

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
        """Run architecture rule validation (stub).

        Returns:
            Result of architecture validation (stubbed).
        """
        # Stub implementation - will be implemented in M06
        return StepResult(
            step=ValidationStep.ARCHITECTURE,
            status=ValidationStatus.PASSED,
            errors=[],
            details={
                "message": "Architecture validation stubbed (pending M06)",
                "stub": "true",
            },
        )

    def _run_test_validation(self) -> StepResult:
        """Run test suite validation (stub).

        Returns:
            Result of test validation (stubbed).
        """
        # Stub implementation - will be implemented in M06
        return StepResult(
            step=ValidationStep.TESTS,
            status=ValidationStatus.PASSED,
            errors=[],
            details={
                "message": "Test execution stubbed (pending M06)",
                "stub": "true",
            },
        )

    def _run_lint_validation(self) -> StepResult:
        """Run lint validation (stub).

        Returns:
            Result of lint validation (stubbed).
        """
        # Stub implementation - will be implemented in M06
        return StepResult(
            step=ValidationStep.LINT,
            status=ValidationStatus.PASSED,
            errors=[],
            details={
                "message": "Lint execution stubbed (pending M06)",
                "stub": "true",
            },
        )
