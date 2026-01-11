"""Validation error types for the validation engine.

This module defines the error hierarchy for validation failures:

ValidationError (base)
├── ValidatorConfigError           # Configuration issues
│   ├── LanguageNotSupportedError  # Unknown language
│   └── ValidatorNotFoundError     # Validator not registered
│
├── ValidatorExecutionError        # Execution issues
│   ├── CommandNotFoundError       # Test/lint command missing
│   ├── ValidationTimeoutError     # Command timed out
│   └── ProcessError               # Subprocess failed
│
└── InvariantViolationError        # Domain invariant violations
    ├── TestPlanNotLockedError     # TestPlan not locked
    ├── InvalidStatusError         # Invalid status transition
    ├── MissingApprovalError       # Missing approval record
    └── MissingDependencyError     # Missing artifact dependency

Note:
    These errors are raised for infrastructure/configuration issues,
    NOT for validation failures. Validation failures return
    ValidationResult(status="failed", errors=[...]).
"""


class ValidationError(Exception):
    """Base class for all validation errors.

    This is the root of the validation error hierarchy. All validation-related
    exceptions should inherit from this class.
    """

    def __init__(self, message: str) -> None:
        """Initialize the validation error.

        Args:
            message: Human-readable error description.
        """
        self.message = message
        super().__init__(message)


# --- Configuration Errors ---


class ValidatorConfigError(ValidationError):
    """Base class for validator configuration errors.

    Raised when a validator cannot be configured or initialized properly.
    """

    pass


class LanguageNotSupportedError(ValidatorConfigError):
    """Raised when a language is not supported by the validator.

    Attributes:
        language: The unsupported language.
        supported_languages: List of languages the validator supports.
    """

    def __init__(
        self,
        language: str,
        supported_languages: list[str] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            language: The unsupported language.
            supported_languages: List of supported languages (optional).
        """
        self.language = language
        self.supported_languages = supported_languages or []
        supported_str = ", ".join(self.supported_languages) if self.supported_languages else "none"
        message = f"Language '{language}' is not supported. Supported languages: {supported_str}"
        super().__init__(message)


class ValidatorNotFoundError(ValidatorConfigError):
    """Raised when a validator is not found in the registry.

    Attributes:
        validator_name: The name of the validator that was not found.
    """

    def __init__(self, validator_name: str) -> None:
        """Initialize the error.

        Args:
            validator_name: Name of the missing validator.
        """
        self.validator_name = validator_name
        message = f"Validator '{validator_name}' not found in registry"
        super().__init__(message)


# --- Execution Errors ---


class ValidatorExecutionError(ValidationError):
    """Base class for validator execution errors.

    Raised when a validator fails to execute due to external issues
    (missing commands, timeouts, subprocess failures).
    """

    pass


class CommandNotFoundError(ValidatorExecutionError):
    """Raised when a command required by the validator is not found.

    Attributes:
        command: The command that was not found.
        validator: The validator that needed the command.
    """

    def __init__(self, command: str, validator: str = "") -> None:
        """Initialize the error.

        Args:
            command: The missing command.
            validator: Name of the validator (optional).
        """
        self.command = command
        self.validator = validator
        prefix = f"[{validator}] " if validator else ""
        message = f"{prefix}Command '{command}' not found. Please ensure it is installed and in PATH."
        super().__init__(message)


class ValidationTimeoutError(ValidatorExecutionError):
    """Raised when a validation command times out.

    Attributes:
        command: The command that timed out.
        timeout_seconds: The timeout value in seconds.
    """

    def __init__(self, command: str, timeout_seconds: int) -> None:
        """Initialize the error.

        Args:
            command: The command that timed out.
            timeout_seconds: The timeout value.
        """
        self.command = command
        self.timeout_seconds = timeout_seconds
        message = f"Command '{command}' timed out after {timeout_seconds} seconds"
        super().__init__(message)


class ProcessError(ValidatorExecutionError):
    """Raised when a subprocess fails unexpectedly.

    This is for unexpected failures, not for validation failures
    (which are returned as ValidationResult).

    Attributes:
        command: The command that failed.
        exit_code: The exit code of the process.
        stderr: The stderr output (if available).
    """

    def __init__(
        self,
        command: str,
        exit_code: int | None = None,
        stderr: str = "",
    ) -> None:
        """Initialize the error.

        Args:
            command: The command that failed.
            exit_code: The process exit code (optional).
            stderr: The stderr output (optional).
        """
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        parts = [f"Process '{command}' failed"]
        if exit_code is not None:
            parts.append(f"with exit code {exit_code}")
        if stderr:
            parts.append(f": {stderr[:200]}")
        message = " ".join(parts)
        super().__init__(message)


# --- Invariant Violation Errors ---


class InvariantViolationError(ValidationError):
    """Base class for domain invariant violations.

    These are raised when pre-conditions for validation are not met.
    """

    pass


class TestPlanNotLockedError(InvariantViolationError):
    """Raised when TestPlan is not locked but should be.

    The TestPlan must be locked before implementation can proceed.

    Attributes:
        current_status: The current status of the TestPlan.
    """

    def __init__(self, current_status: str = "unknown") -> None:
        """Initialize the error.

        Args:
            current_status: Current status of the TestPlan.
        """
        self.current_status = current_status
        message = f"TestPlan must be locked before implementation. Current status: {current_status}"
        super().__init__(message)


class InvalidStatusError(InvariantViolationError):
    """Raised when an artifact has an invalid status transition.

    Attributes:
        artifact_id: ID of the artifact with invalid status.
        current_status: The current status.
        expected_statuses: List of valid statuses.
    """

    def __init__(
        self,
        artifact_id: str,
        current_status: str,
        expected_statuses: list[str] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            artifact_id: ID of the artifact.
            current_status: Current status of the artifact.
            expected_statuses: List of expected statuses (optional).
        """
        self.artifact_id = artifact_id
        self.current_status = current_status
        self.expected_statuses = expected_statuses or []
        expected_str = ", ".join(self.expected_statuses) if self.expected_statuses else "N/A"
        message = (
            f"Invalid status for artifact '{artifact_id}': "
            f"'{current_status}'. Expected one of: {expected_str}"
        )
        super().__init__(message)


class MissingApprovalError(InvariantViolationError):
    """Raised when an artifact is approved but has no approval record.

    Attributes:
        artifact_id: ID of the artifact missing approval.
    """

    def __init__(self, artifact_id: str) -> None:
        """Initialize the error.

        Args:
            artifact_id: ID of the artifact missing approval.
        """
        self.artifact_id = artifact_id
        message = f"Artifact '{artifact_id}' is APPROVED but has no approval record"
        super().__init__(message)


class MissingDependencyError(InvariantViolationError):
    """Raised when an artifact depends on a missing artifact.

    Attributes:
        artifact_id: ID of the artifact with missing dependency.
        dependency_id: ID of the missing dependency.
    """

    def __init__(self, artifact_id: str, dependency_id: str) -> None:
        """Initialize the error.

        Args:
            artifact_id: ID of the artifact with missing dependency.
            dependency_id: ID of the missing dependency.
        """
        self.artifact_id = artifact_id
        self.dependency_id = dependency_id
        message = f"Artifact '{artifact_id}' depends on missing artifact '{dependency_id}'"
        super().__init__(message)
