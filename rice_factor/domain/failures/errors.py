"""Exception types for Rice-Factor.

Defines the exception hierarchy used throughout the system.
"""


class RiceFactorError(Exception):
    """Base exception for all Rice-Factor errors."""


class ArtifactError(RiceFactorError):
    """Base class for artifact-related errors."""


class ArtifactStatusError(ArtifactError):
    """Raised when an invalid status transition is attempted.

    Examples:
        - Trying to approve an already approved artifact
        - Trying to lock an artifact that isn't approved
        - Trying to lock an artifact that isn't a TestPlan
    """


class ArtifactValidationError(ArtifactError):
    """Raised when artifact validation fails.

    Contains details about the validation failure including field paths.

    Attributes:
        message: Human-readable error message
        field_path: Path to the invalid field (e.g., 'payload.domains.0.name')
        expected: Expected value or type
        actual: Actual value received
        details: List of detailed error information
    """

    def __init__(
        self,
        message: str,
        *,
        field_path: str | None = None,
        expected: object = None,
        actual: object = None,
        details: list[dict[str, object]] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Human-readable error message
            field_path: Path to the invalid field
            expected: Expected value or type
            actual: Actual value received
            details: List of detailed error dictionaries
        """
        super().__init__(message)
        self.field_path = field_path
        self.expected = expected
        self.actual = actual
        self.details = details or []

    def __str__(self) -> str:
        """Return formatted error message."""
        parts = [self.args[0]]
        if self.field_path:
            parts.append(f"Field: {self.field_path}")
        if self.expected is not None:
            parts.append(f"Expected: {self.expected}")
        if self.actual is not None:
            parts.append(f"Actual: {self.actual}")
        return " | ".join(parts)


class ArtifactNotFoundError(ArtifactError):
    """Raised when an artifact cannot be found."""


class ArtifactDependencyError(ArtifactError):
    """Raised when artifact dependencies are not satisfied.

    Examples:
        - Dependency doesn't exist
        - Dependency is still in draft status
    """
