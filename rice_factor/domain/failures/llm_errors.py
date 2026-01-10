"""LLM-related error types.

This module defines the exception hierarchy for LLM operations including:
- LLMError: Base class for all LLM errors
- LLMAPIError: Provider API failures
- LLMTimeoutError: Request timeout
- LLMRateLimitError: Rate limiting
- LLMMissingInformationError: Explicit LLM failure for missing info
- LLMInvalidRequestError: Explicit LLM failure for invalid request
- LLMOutputError: Base class for output validation errors
- InvalidJSONError: LLM returned non-JSON
- SchemaViolationError: LLM output doesn't match schema
- CodeInOutputError: LLM returned source code
- MultipleArtifactsError: LLM returned multiple artifacts
- ExplanatoryTextError: LLM included text outside JSON
"""

from rice_factor.domain.failures.errors import RiceFactorError


class LLMError(RiceFactorError):
    """Base exception for all LLM-related errors.

    Attributes:
        message: Human-readable error message
        details: Additional error details
        recoverable: Whether the error can be recovered from (e.g., by retry)
    """

    def __init__(
        self,
        message: str,
        *,
        details: str | None = None,
        recoverable: bool = True,
    ) -> None:
        """Initialize LLM error.

        Args:
            message: Human-readable error message
            details: Additional error details
            recoverable: Whether the error is recoverable
        """
        super().__init__(message)
        self.message = message
        self.details = details
        self.recoverable = recoverable

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class LLMAPIError(LLMError):
    """Raised for provider API failures (5xx errors, network issues).

    Attributes:
        status_code: HTTP status code if available
        provider: Name of the LLM provider (e.g., 'claude', 'openai')
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        provider: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code if available
            provider: Name of the LLM provider
            details: Additional error details
        """
        super().__init__(message, details=details, recoverable=True)
        self.status_code = status_code
        self.provider = provider

    def __str__(self) -> str:
        """Return formatted error message with provider and status."""
        parts = []
        if self.provider:
            parts.append(f"[{self.provider}]")
        parts.append(self.message)
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.details:
            parts.append(f": {self.details}")
        return " ".join(parts)


class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out.

    Attributes:
        timeout_seconds: The timeout value that was exceeded
    """

    def __init__(
        self,
        message: str = "LLM request timed out",
        *,
        timeout_seconds: int | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize timeout error.

        Args:
            message: Human-readable error message
            timeout_seconds: The timeout value that was exceeded
            details: Additional error details
        """
        super().__init__(message, details=details, recoverable=True)
        self.timeout_seconds = timeout_seconds

    def __str__(self) -> str:
        """Return formatted error message with timeout value."""
        if self.timeout_seconds:
            return f"{self.message} after {self.timeout_seconds}s"
        return self.message


class LLMRateLimitError(LLMError):
    """Raised when the LLM provider rate limits the request.

    Attributes:
        retry_after: Recommended wait time in seconds before retrying
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: int | None = None,
        provider: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Human-readable error message
            retry_after: Seconds to wait before retrying
            provider: Name of the LLM provider
            details: Additional error details
        """
        super().__init__(message, details=details, recoverable=True)
        self.retry_after = retry_after
        self.provider = provider

    def __str__(self) -> str:
        """Return formatted error message with retry info."""
        parts = []
        if self.provider:
            parts.append(f"[{self.provider}]")
        parts.append(self.message)
        if self.retry_after:
            parts.append(f"(retry after {self.retry_after}s)")
        return " ".join(parts)


class LLMMissingInformationError(LLMError):
    """Raised when the LLM explicitly returns a missing_information error.

    This error is NOT recoverable without human input. The LLM determined
    that required information is missing from the context and cannot
    proceed without clarification.

    Attributes:
        missing_items: List of specific items that are missing
    """

    def __init__(
        self,
        message: str = "Missing required information",
        *,
        missing_items: list[str] | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize missing information error.

        Args:
            message: Human-readable error message
            missing_items: List of specific missing items
            details: Additional error details
        """
        # This error requires human input to resolve
        super().__init__(message, details=details, recoverable=False)
        self.missing_items = missing_items or []

    def __str__(self) -> str:
        """Return formatted error message with missing items."""
        parts = [self.message]
        if self.missing_items:
            items = ", ".join(self.missing_items)
            parts.append(f"Missing: {items}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class LLMInvalidRequestError(LLMError):
    """Raised when the LLM explicitly returns an invalid_request error.

    The LLM determined that the request itself is invalid and cannot
    be fulfilled. This may be recoverable by fixing the request.

    Attributes:
        invalid_reason: Explanation of why the request is invalid
    """

    def __init__(
        self,
        message: str = "Invalid request",
        *,
        invalid_reason: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize invalid request error.

        Args:
            message: Human-readable error message
            invalid_reason: Explanation of why the request is invalid
            details: Additional error details
        """
        # Could potentially be recoverable if the request can be fixed
        super().__init__(message, details=details, recoverable=False)
        self.invalid_reason = invalid_reason

    def __str__(self) -> str:
        """Return formatted error message with reason."""
        parts = [self.message]
        if self.invalid_reason:
            parts.append(f"Reason: {self.invalid_reason}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


# ============================================================================
# LLM Output Validation Errors
# ============================================================================


class LLMOutputError(LLMError):
    """Base exception for LLM output validation errors.

    These errors occur when the LLM returns output that doesn't conform
    to the expected format (valid JSON, matching schema, no code, etc.).
    """

    def __init__(
        self,
        message: str,
        *,
        raw_snippet: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize output error.

        Args:
            message: Human-readable error message
            raw_snippet: Snippet of the raw output for debugging
            details: Additional error details
        """
        # Output errors are generally not recoverable by retry
        super().__init__(message, details=details, recoverable=False)
        self.raw_snippet = raw_snippet

    def __str__(self) -> str:
        """Return formatted error message."""
        parts = [self.message]
        if self.details:
            parts.append(f"Details: {self.details}")
        if self.raw_snippet:
            # Show first 100 chars of raw snippet
            snippet = self.raw_snippet[:100]
            if len(self.raw_snippet) > 100:
                snippet += "..."
            parts.append(f"Output: {snippet!r}")
        return " | ".join(parts)


class InvalidJSONError(LLMOutputError):
    """Raised when LLM output cannot be parsed as JSON.

    Attributes:
        parse_error: The underlying JSON parse error message
    """

    def __init__(
        self,
        message: str = "LLM output is not valid JSON",
        *,
        parse_error: str | None = None,
        raw_snippet: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize invalid JSON error.

        Args:
            message: Human-readable error message
            parse_error: The underlying JSON parse error
            raw_snippet: Snippet of the raw output
            details: Additional error details
        """
        super().__init__(message, raw_snippet=raw_snippet, details=details)
        self.parse_error = parse_error

    def __str__(self) -> str:
        """Return formatted error message."""
        parts = [self.message]
        if self.parse_error:
            parts.append(f"Parse error: {self.parse_error}")
        if self.raw_snippet:
            snippet = self.raw_snippet[:100]
            if len(self.raw_snippet) > 100:
                snippet += "..."
            parts.append(f"Output: {snippet!r}")
        return " | ".join(parts)


class SchemaViolationError(LLMOutputError):
    """Raised when LLM output doesn't match the expected JSON schema.

    Attributes:
        schema_path: Path in the schema where validation failed
        validation_errors: List of specific validation errors
    """

    def __init__(
        self,
        message: str = "LLM output doesn't match expected schema",
        *,
        schema_path: str | None = None,
        validation_errors: list[str] | None = None,
        raw_snippet: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize schema violation error.

        Args:
            message: Human-readable error message
            schema_path: Path in schema where validation failed
            validation_errors: List of validation error messages
            raw_snippet: Snippet of the raw output
            details: Additional error details
        """
        super().__init__(message, raw_snippet=raw_snippet, details=details)
        self.schema_path = schema_path
        self.validation_errors = validation_errors or []

    def __str__(self) -> str:
        """Return formatted error message."""
        parts = [self.message]
        if self.schema_path:
            parts.append(f"at: {self.schema_path}")
        if self.validation_errors:
            errors_str = "; ".join(self.validation_errors[:3])
            if len(self.validation_errors) > 3:
                errors_str += f" (+{len(self.validation_errors) - 3} more)"
            parts.append(f"Errors: {errors_str}")
        return " | ".join(parts)


class CodeInOutputError(LLMOutputError):
    """Raised when LLM output contains source code.

    The LLM should only output structured JSON artifacts, not code.

    Attributes:
        location: Location in the artifact where code was found
        code_snippet: The detected code snippet
    """

    def __init__(
        self,
        message: str = "LLM output contains source code",
        *,
        location: str | None = None,
        code_snippet: str | None = None,
        raw_snippet: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize code in output error.

        Args:
            message: Human-readable error message
            location: Location in artifact where code was found
            code_snippet: The detected code snippet
            raw_snippet: Snippet of the raw output
            details: Additional error details
        """
        super().__init__(message, raw_snippet=raw_snippet, details=details)
        self.location = location
        self.code_snippet = code_snippet

    def __str__(self) -> str:
        """Return formatted error message."""
        parts = [self.message]
        if self.location:
            parts.append(f"at: {self.location}")
        if self.code_snippet:
            snippet = self.code_snippet[:50]
            if len(self.code_snippet) > 50:
                snippet += "..."
            parts.append(f"Code: {snippet!r}")
        return " | ".join(parts)


class MultipleArtifactsError(LLMOutputError):
    """Raised when LLM output contains multiple top-level JSON objects.

    Each LLM call should produce exactly one artifact.

    Attributes:
        count: Number of JSON objects found
    """

    def __init__(
        self,
        message: str = "LLM output contains multiple artifacts",
        *,
        count: int | None = None,
        raw_snippet: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize multiple artifacts error.

        Args:
            message: Human-readable error message
            count: Number of JSON objects found
            raw_snippet: Snippet of the raw output
            details: Additional error details
        """
        super().__init__(message, raw_snippet=raw_snippet, details=details)
        self.count = count

    def __str__(self) -> str:
        """Return formatted error message."""
        parts = [self.message]
        if self.count:
            parts.append(f"Found {self.count} objects")
        return " | ".join(parts)


class ExplanatoryTextError(LLMOutputError):
    """Raised when LLM output includes explanatory text outside JSON.

    The LLM should output only JSON with no additional explanation.

    Attributes:
        text_snippet: The detected explanatory text
    """

    def __init__(
        self,
        message: str = "LLM output contains explanatory text outside JSON",
        *,
        text_snippet: str | None = None,
        raw_snippet: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize explanatory text error.

        Args:
            message: Human-readable error message
            text_snippet: The detected explanatory text
            raw_snippet: Snippet of the raw output
            details: Additional error details
        """
        super().__init__(message, raw_snippet=raw_snippet, details=details)
        self.text_snippet = text_snippet

    def __str__(self) -> str:
        """Return formatted error message."""
        parts = [self.message]
        if self.text_snippet:
            snippet = self.text_snippet[:50]
            if len(self.text_snippet) > 50:
                snippet += "..."
            parts.append(f"Text: {snippet!r}")
        return " | ".join(parts)
