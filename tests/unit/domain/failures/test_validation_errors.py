"""Tests for validation error types."""


from rice_factor.domain.failures.validation_errors import (
    CommandNotFoundError,
    InvalidStatusError,
    InvariantViolationError,
    LanguageNotSupportedError,
    MissingApprovalError,
    MissingDependencyError,
    ProcessError,
    TestPlanNotLockedError,
    ValidationError,
    ValidationTimeoutError,
    ValidatorConfigError,
    ValidatorExecutionError,
    ValidatorNotFoundError,
)


class TestValidationError:
    """Tests for base ValidationError."""

    def test_create_with_message(self) -> None:
        """Test creating error with message."""
        error = ValidationError("Test error message")

        assert error.message == "Test error message"
        assert str(error) == "Test error message"

    def test_inheritance(self) -> None:
        """Test that ValidationError inherits from Exception."""
        error = ValidationError("Test")
        assert isinstance(error, Exception)


class TestValidatorConfigError:
    """Tests for configuration errors."""

    def test_language_not_supported(self) -> None:
        """Test LanguageNotSupportedError."""
        error = LanguageNotSupportedError(
            language="cobol",
            supported_languages=["python", "rust", "go"],
        )

        assert error.language == "cobol"
        assert "cobol" in str(error)
        assert "python" in str(error)
        assert error.supported_languages == ["python", "rust", "go"]
        assert isinstance(error, ValidatorConfigError)
        assert isinstance(error, ValidationError)

    def test_language_not_supported_no_list(self) -> None:
        """Test LanguageNotSupportedError without supported list."""
        error = LanguageNotSupportedError(language="cobol")

        assert error.language == "cobol"
        assert error.supported_languages == []
        assert "none" in str(error).lower()

    def test_validator_not_found(self) -> None:
        """Test ValidatorNotFoundError."""
        error = ValidatorNotFoundError(validator_name="custom_validator")

        assert error.validator_name == "custom_validator"
        assert "custom_validator" in str(error)
        assert isinstance(error, ValidatorConfigError)


class TestValidatorExecutionError:
    """Tests for execution errors."""

    def test_command_not_found_basic(self) -> None:
        """Test CommandNotFoundError with just command."""
        error = CommandNotFoundError(command="pytest")

        assert error.command == "pytest"
        assert error.validator == ""
        assert "pytest" in str(error)
        assert isinstance(error, ValidatorExecutionError)

    def test_command_not_found_with_validator(self) -> None:
        """Test CommandNotFoundError with validator name."""
        error = CommandNotFoundError(command="pytest", validator="test_runner")

        assert error.command == "pytest"
        assert error.validator == "test_runner"
        assert "[test_runner]" in str(error)
        assert "pytest" in str(error)

    def test_validation_timeout(self) -> None:
        """Test ValidationTimeoutError."""
        error = ValidationTimeoutError(command="pytest tests/", timeout_seconds=300)

        assert error.command == "pytest tests/"
        assert error.timeout_seconds == 300
        assert "pytest tests/" in str(error)
        assert "300" in str(error)
        assert isinstance(error, ValidatorExecutionError)

    def test_process_error_basic(self) -> None:
        """Test ProcessError with just command."""
        error = ProcessError(command="pytest")

        assert error.command == "pytest"
        assert error.exit_code is None
        assert error.stderr == ""
        assert "pytest" in str(error)
        assert isinstance(error, ValidatorExecutionError)

    def test_process_error_with_exit_code(self) -> None:
        """Test ProcessError with exit code."""
        error = ProcessError(command="pytest", exit_code=1)

        assert error.exit_code == 1
        assert "exit code 1" in str(error)

    def test_process_error_with_stderr(self) -> None:
        """Test ProcessError with stderr."""
        error = ProcessError(
            command="pytest",
            exit_code=1,
            stderr="AssertionError: Expected 1, got 2",
        )

        assert error.stderr == "AssertionError: Expected 1, got 2"
        assert "AssertionError" in str(error)

    def test_process_error_truncates_long_stderr(self) -> None:
        """Test that ProcessError truncates long stderr."""
        long_stderr = "x" * 500
        error = ProcessError(command="pytest", stderr=long_stderr)

        # Should truncate to 200 chars
        assert len(str(error)) < len(long_stderr)


class TestInvariantViolationError:
    """Tests for invariant violation errors."""

    def test_testplan_not_locked(self) -> None:
        """Test TestPlanNotLockedError."""
        error = TestPlanNotLockedError(current_status="draft")

        assert error.current_status == "draft"
        assert "locked" in str(error).lower()
        assert "draft" in str(error)
        assert isinstance(error, InvariantViolationError)

    def test_testplan_not_locked_default(self) -> None:
        """Test TestPlanNotLockedError with default status."""
        error = TestPlanNotLockedError()

        assert error.current_status == "unknown"
        assert "unknown" in str(error)

    def test_invalid_status(self) -> None:
        """Test InvalidStatusError."""
        error = InvalidStatusError(
            artifact_id="abc123",
            current_status="invalid",
            expected_statuses=["draft", "approved", "locked"],
        )

        assert error.artifact_id == "abc123"
        assert error.current_status == "invalid"
        assert "abc123" in str(error)
        assert "invalid" in str(error)
        assert isinstance(error, InvariantViolationError)

    def test_invalid_status_no_expected(self) -> None:
        """Test InvalidStatusError without expected list."""
        error = InvalidStatusError(
            artifact_id="abc123",
            current_status="invalid",
        )

        assert error.expected_statuses == []

    def test_missing_approval(self) -> None:
        """Test MissingApprovalError."""
        error = MissingApprovalError(artifact_id="abc123")

        assert error.artifact_id == "abc123"
        assert "abc123" in str(error)
        assert "approval" in str(error).lower()
        assert isinstance(error, InvariantViolationError)

    def test_missing_dependency(self) -> None:
        """Test MissingDependencyError."""
        error = MissingDependencyError(
            artifact_id="abc123",
            dependency_id="def456",
        )

        assert error.artifact_id == "abc123"
        assert error.dependency_id == "def456"
        assert "abc123" in str(error)
        assert "def456" in str(error)
        assert isinstance(error, InvariantViolationError)


class TestErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_config_errors_inherit_from_validation_error(self) -> None:
        """Test config errors are ValidationErrors."""
        errors = [
            LanguageNotSupportedError("test"),
            ValidatorNotFoundError("test"),
        ]

        for error in errors:
            assert isinstance(error, ValidationError)
            assert isinstance(error, ValidatorConfigError)

    def test_execution_errors_inherit_from_validation_error(self) -> None:
        """Test execution errors are ValidationErrors."""
        errors = [
            CommandNotFoundError("test"),
            ValidationTimeoutError("test", 60),
            ProcessError("test"),
        ]

        for error in errors:
            assert isinstance(error, ValidationError)
            assert isinstance(error, ValidatorExecutionError)

    def test_invariant_errors_inherit_from_validation_error(self) -> None:
        """Test invariant errors are ValidationErrors."""
        errors = [
            TestPlanNotLockedError(),
            InvalidStatusError("id", "status"),
            MissingApprovalError("id"),
            MissingDependencyError("id", "dep"),
        ]

        for error in errors:
            assert isinstance(error, ValidationError)
            assert isinstance(error, InvariantViolationError)
