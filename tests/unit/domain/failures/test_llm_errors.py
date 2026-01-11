"""Unit tests for LLM error types."""

import pytest

from rice_factor.domain.failures.errors import RiceFactorError
from rice_factor.domain.failures.llm_errors import (
    LLMAPIError,
    LLMError,
    LLMInvalidRequestError,
    LLMMissingInformationError,
    LLMRateLimitError,
    LLMTimeoutError,
)


class TestLLMError:
    """Tests for LLMError base class."""

    def test_inherits_from_rice_factor_error(self) -> None:
        """LLMError should inherit from RiceFactorError."""
        assert issubclass(LLMError, RiceFactorError)

    def test_create_with_message(self) -> None:
        """Can create error with just a message."""
        error = LLMError("Test error")
        assert error.message == "Test error"
        assert error.details is None
        assert error.recoverable is True  # Default is recoverable

    def test_create_with_all_attributes(self) -> None:
        """Can create error with all attributes."""
        error = LLMError(
            "Test error",
            details="Additional details",
            recoverable=False,
        )
        assert error.message == "Test error"
        assert error.details == "Additional details"
        assert error.recoverable is False

    def test_str_without_details(self) -> None:
        """String representation without details."""
        error = LLMError("Test error")
        assert str(error) == "Test error"

    def test_str_with_details(self) -> None:
        """String representation with details."""
        error = LLMError("Test error", details="More info")
        assert str(error) == "Test error: More info"


class TestLLMAPIError:
    """Tests for LLMAPIError."""

    def test_inherits_from_llm_error(self) -> None:
        """LLMAPIError should inherit from LLMError."""
        assert issubclass(LLMAPIError, LLMError)

    def test_create_with_status_code(self) -> None:
        """Can create with status code."""
        error = LLMAPIError("API failed", status_code=500)
        assert error.status_code == 500
        assert error.recoverable is True

    def test_create_with_provider(self) -> None:
        """Can create with provider name."""
        error = LLMAPIError("API failed", provider="claude")
        assert error.provider == "claude"

    def test_str_with_all_info(self) -> None:
        """String representation includes provider and status."""
        error = LLMAPIError(
            "Connection failed",
            status_code=503,
            provider="openai",
            details="Service unavailable",
        )
        result = str(error)
        assert "[openai]" in result
        assert "Connection failed" in result
        assert "(HTTP 503)" in result
        assert "Service unavailable" in result


class TestLLMTimeoutError:
    """Tests for LLMTimeoutError."""

    def test_inherits_from_llm_error(self) -> None:
        """LLMTimeoutError should inherit from LLMError."""
        assert issubclass(LLMTimeoutError, LLMError)

    def test_default_message(self) -> None:
        """Has a default message."""
        error = LLMTimeoutError()
        assert "timed out" in error.message.lower()

    def test_create_with_timeout_seconds(self) -> None:
        """Can create with timeout seconds."""
        error = LLMTimeoutError(timeout_seconds=120)
        assert error.timeout_seconds == 120
        assert error.recoverable is True

    def test_str_with_timeout(self) -> None:
        """String includes timeout value."""
        error = LLMTimeoutError(timeout_seconds=60)
        assert "60s" in str(error)


class TestLLMRateLimitError:
    """Tests for LLMRateLimitError."""

    def test_inherits_from_llm_error(self) -> None:
        """LLMRateLimitError should inherit from LLMError."""
        assert issubclass(LLMRateLimitError, LLMError)

    def test_default_message(self) -> None:
        """Has a default message."""
        error = LLMRateLimitError()
        assert "rate limit" in error.message.lower()

    def test_create_with_retry_after(self) -> None:
        """Can create with retry_after seconds."""
        error = LLMRateLimitError(retry_after=30)
        assert error.retry_after == 30
        assert error.recoverable is True

    def test_str_with_retry_after(self) -> None:
        """String includes retry info."""
        error = LLMRateLimitError(retry_after=60, provider="claude")
        result = str(error)
        assert "retry after 60s" in result
        assert "[claude]" in result


class TestLLMMissingInformationError:
    """Tests for LLMMissingInformationError."""

    def test_inherits_from_llm_error(self) -> None:
        """LLMMissingInformationError should inherit from LLMError."""
        assert issubclass(LLMMissingInformationError, LLMError)

    def test_not_recoverable(self) -> None:
        """Missing information errors are NOT recoverable."""
        error = LLMMissingInformationError()
        assert error.recoverable is False

    def test_default_message(self) -> None:
        """Has a default message."""
        error = LLMMissingInformationError()
        assert "missing" in error.message.lower()

    def test_create_with_missing_items(self) -> None:
        """Can create with list of missing items."""
        error = LLMMissingInformationError(
            missing_items=["Domain 'User'", "Module 'Auth'"]
        )
        assert error.missing_items == ["Domain 'User'", "Module 'Auth'"]

    def test_str_with_missing_items(self) -> None:
        """String includes missing items."""
        error = LLMMissingInformationError(
            missing_items=["X", "Y"],
            details="More context",
        )
        result = str(error)
        assert "Missing: X, Y" in result
        assert "Details: More context" in result


class TestLLMInvalidRequestError:
    """Tests for LLMInvalidRequestError."""

    def test_inherits_from_llm_error(self) -> None:
        """LLMInvalidRequestError should inherit from LLMError."""
        assert issubclass(LLMInvalidRequestError, LLMError)

    def test_not_recoverable(self) -> None:
        """Invalid request errors are NOT recoverable."""
        error = LLMInvalidRequestError()
        assert error.recoverable is False

    def test_default_message(self) -> None:
        """Has a default message."""
        error = LLMInvalidRequestError()
        assert "invalid" in error.message.lower()

    def test_create_with_reason(self) -> None:
        """Can create with invalid reason."""
        error = LLMInvalidRequestError(
            invalid_reason="Schema mismatch"
        )
        assert error.invalid_reason == "Schema mismatch"

    def test_str_with_reason(self) -> None:
        """String includes reason."""
        error = LLMInvalidRequestError(
            invalid_reason="Bad schema",
            details="More info",
        )
        result = str(error)
        assert "Reason: Bad schema" in result
        assert "Details: More info" in result


class TestErrorRecoverability:
    """Tests for error recoverability."""

    @pytest.mark.parametrize(
        "error_class,expected_recoverable",
        [
            (LLMError, True),
            (LLMAPIError, True),
            (LLMTimeoutError, True),
            (LLMRateLimitError, True),
            (LLMMissingInformationError, False),
            (LLMInvalidRequestError, False),
        ],
    )
    def test_default_recoverability(
        self,
        error_class: type[LLMError],
        expected_recoverable: bool,
    ) -> None:
        """Each error type has correct default recoverability."""
        if error_class in (LLMAPIError,):
            error = error_class("test", status_code=500)
        else:
            error = error_class("test")
        assert error.recoverable is expected_recoverable
