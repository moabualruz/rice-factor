"""Unit tests for ValidationOrchestrator."""

from pathlib import Path

from rice_factor.domain.artifacts.payloads.validation_result import ValidationStatus
from rice_factor.domain.services.validation_orchestrator import (
    StepResult,
    ValidationOrchestrator,
    ValidationResult,
    ValidationStep,
)


class TestValidationOrchestratorInitialization:
    """Tests for ValidationOrchestrator initialization."""

    def test_initialization_with_project_path(self, tmp_path: Path) -> None:
        """Orchestrator should initialize with project path."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        assert orchestrator.project_path == tmp_path

    def test_project_path_property(self, tmp_path: Path) -> None:
        """project_path property should return the project path."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        assert orchestrator.project_path == tmp_path


class TestRunAll:
    """Tests for run_all method."""

    def test_run_all_returns_validation_result(self, tmp_path: Path) -> None:
        """run_all should return a ValidationResult."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_all()
        assert isinstance(result, ValidationResult)

    def test_run_all_includes_all_steps(self, tmp_path: Path) -> None:
        """run_all should include results for all validation steps."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_all()

        steps = {r.step for r in result.step_results}
        assert ValidationStep.SCHEMA in steps
        assert ValidationStep.ARCHITECTURE in steps
        assert ValidationStep.TESTS in steps
        assert ValidationStep.LINT in steps

    def test_run_all_has_four_step_results(self, tmp_path: Path) -> None:
        """run_all should have results for all 4 steps."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_all()
        assert len(result.step_results) == 4

    def test_run_all_all_pass_gives_passed_status(self, tmp_path: Path) -> None:
        """run_all should return PASSED if all steps pass."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_all()

        # With stubs, all steps should pass
        assert result.overall_status == ValidationStatus.PASSED
        assert result.passed is True


class TestRunStep:
    """Tests for run_step method."""

    def test_run_step_schema(self, tmp_path: Path) -> None:
        """run_step should run schema validation."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_step(ValidationStep.SCHEMA)

        assert isinstance(result, StepResult)
        assert result.step == ValidationStep.SCHEMA

    def test_run_step_architecture(self, tmp_path: Path) -> None:
        """run_step should run architecture validation (stub)."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_step(ValidationStep.ARCHITECTURE)

        assert result.step == ValidationStep.ARCHITECTURE
        assert result.status == ValidationStatus.PASSED
        assert "stub" in result.details

    def test_run_step_tests(self, tmp_path: Path) -> None:
        """run_step should run test validation (stub)."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_step(ValidationStep.TESTS)

        assert result.step == ValidationStep.TESTS
        assert result.status == ValidationStatus.PASSED
        assert "stub" in result.details

    def test_run_step_lint(self, tmp_path: Path) -> None:
        """run_step should run lint validation (stub)."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_step(ValidationStep.LINT)

        assert result.step == ValidationStep.LINT
        assert result.status == ValidationStatus.PASSED
        assert "stub" in result.details


class TestSchemaValidation:
    """Tests for schema validation step."""

    def test_schema_validation_no_artifacts_dir(self, tmp_path: Path) -> None:
        """Schema validation should pass if no artifacts directory."""
        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_step(ValidationStep.SCHEMA)

        assert result.status == ValidationStatus.PASSED
        assert "No artifacts directory" in result.details.get("message", "")

    def test_schema_validation_empty_artifacts_dir(self, tmp_path: Path) -> None:
        """Schema validation should pass with empty artifacts directory."""
        (tmp_path / "artifacts").mkdir()

        orchestrator = ValidationOrchestrator(project_path=tmp_path)
        result = orchestrator.run_step(ValidationStep.SCHEMA)

        assert result.status == ValidationStatus.PASSED
        assert result.details.get("artifacts_validated") == "0"


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_step_result_creation(self) -> None:
        """StepResult should be creatable with required fields."""
        result = StepResult(
            step=ValidationStep.SCHEMA,
            status=ValidationStatus.PASSED,
        )
        assert result.step == ValidationStep.SCHEMA
        assert result.status == ValidationStatus.PASSED
        assert result.errors == []

    def test_step_result_with_errors(self) -> None:
        """StepResult should store errors."""
        result = StepResult(
            step=ValidationStep.SCHEMA,
            status=ValidationStatus.FAILED,
            errors=["Error 1", "Error 2"],
        )
        assert len(result.errors) == 2
        assert "Error 1" in result.errors

    def test_step_result_with_details(self) -> None:
        """StepResult should store details."""
        result = StepResult(
            step=ValidationStep.SCHEMA,
            status=ValidationStatus.PASSED,
            details={"key": "value"},
        )
        assert result.details["key"] == "value"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_creation(self) -> None:
        """ValidationResult should be creatable with required fields."""
        result = ValidationResult(overall_status=ValidationStatus.PASSED)
        assert result.overall_status == ValidationStatus.PASSED
        assert result.step_results == []

    def test_passed_property_when_passed(self) -> None:
        """passed property should return True when passed."""
        result = ValidationResult(overall_status=ValidationStatus.PASSED)
        assert result.passed is True

    def test_passed_property_when_failed(self) -> None:
        """passed property should return False when failed."""
        result = ValidationResult(overall_status=ValidationStatus.FAILED)
        assert result.passed is False

    def test_failed_steps_property(self) -> None:
        """failed_steps should return list of failed steps."""
        step1 = StepResult(step=ValidationStep.SCHEMA, status=ValidationStatus.PASSED)
        step2 = StepResult(step=ValidationStep.TESTS, status=ValidationStatus.FAILED)

        result = ValidationResult(
            overall_status=ValidationStatus.FAILED,
            step_results=[step1, step2],
        )

        assert len(result.failed_steps) == 1
        assert result.failed_steps[0].step == ValidationStep.TESTS

    def test_error_count_property(self) -> None:
        """error_count should return total errors across all steps."""
        step1 = StepResult(
            step=ValidationStep.SCHEMA,
            status=ValidationStatus.FAILED,
            errors=["Error 1", "Error 2"],
        )
        step2 = StepResult(
            step=ValidationStep.TESTS,
            status=ValidationStatus.FAILED,
            errors=["Error 3"],
        )

        result = ValidationResult(
            overall_status=ValidationStatus.FAILED,
            step_results=[step1, step2],
        )

        assert result.error_count == 3


class TestValidationStep:
    """Tests for ValidationStep enum."""

    def test_validation_step_values(self) -> None:
        """ValidationStep should have expected values."""
        assert ValidationStep.SCHEMA.value == "schema"
        assert ValidationStep.ARCHITECTURE.value == "architecture"
        assert ValidationStep.TESTS.value == "tests"
        assert ValidationStep.LINT.value == "lint"

    def test_validation_step_count(self) -> None:
        """ValidationStep should have 4 steps."""
        assert len(ValidationStep) == 4
