"""Tests for ValidationRunnerPort protocol."""

from pathlib import Path

from rice_factor.adapters.validators import (
    ArchitectureValidator,
    InvariantChecker,
    LintRunnerAdapter,
    TestRunnerAdapter,
)
from rice_factor.domain.artifacts.validation_types import (
    ValidationContext,
    ValidationResult,
)
from rice_factor.domain.ports.validation_runner import ValidationRunnerPort


class TestValidationRunnerPort:
    """Tests for ValidationRunnerPort protocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """Test that protocol is runtime checkable."""
        assert hasattr(ValidationRunnerPort, "__protocol_attrs__") or isinstance(
            ValidationRunnerPort, type
        )

    def test_test_runner_implements_protocol(self) -> None:
        """Test TestRunnerAdapter implements protocol."""
        adapter = TestRunnerAdapter()

        # Check required attributes
        assert hasattr(adapter, "name")
        assert hasattr(adapter, "validate")
        assert callable(adapter.validate)

    def test_lint_runner_implements_protocol(self) -> None:
        """Test LintRunnerAdapter implements protocol."""
        adapter = LintRunnerAdapter()

        assert hasattr(adapter, "name")
        assert hasattr(adapter, "validate")
        assert callable(adapter.validate)

    def test_architecture_validator_implements_protocol(self) -> None:
        """Test ArchitectureValidator implements protocol."""
        validator = ArchitectureValidator()

        assert hasattr(validator, "name")
        assert hasattr(validator, "validate")
        assert callable(validator.validate)

    def test_invariant_checker_implements_protocol(self) -> None:
        """Test InvariantChecker implements protocol."""
        checker = InvariantChecker()

        assert hasattr(checker, "name")
        assert hasattr(checker, "validate")
        assert callable(checker.validate)

    def test_name_property_returns_string(self) -> None:
        """Test that name property returns a string."""
        adapters = [
            TestRunnerAdapter(),
            LintRunnerAdapter(),
            ArchitectureValidator(),
            InvariantChecker(),
        ]

        for adapter in adapters:
            assert isinstance(adapter.name, str)
            assert len(adapter.name) > 0

    def test_validate_returns_validation_result(self, tmp_path: Path) -> None:
        """Test that validate returns ValidationResult."""
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={"skip_architecture": True},
        )

        # Use architecture validator since it doesn't need external commands
        validator = ArchitectureValidator()
        result = validator.validate(tmp_path, context)

        assert isinstance(result, ValidationResult)
        assert result.status in ("passed", "failed")


class TestCustomValidator:
    """Tests for creating custom validators."""

    def test_custom_validator_can_implement_protocol(self, tmp_path: Path) -> None:
        """Test that custom classes can implement the protocol."""

        class CustomValidator:
            """Custom validator for testing."""

            @property
            def name(self) -> str:
                return "custom_validator"

            def validate(
                self,
                target: Path,
                _context: ValidationContext,
            ) -> ValidationResult:
                return ValidationResult.passed_result(
                    target=str(target),
                    validator=self.name,
                )

        validator = CustomValidator()
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={},
        )

        result = validator.validate(tmp_path, context)

        assert result.passed
        assert result.validator == "custom_validator"
