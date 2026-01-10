"""LLM error handler decorator.

This module provides the @handle_llm_errors decorator for consistent
error handling across LLM operations.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any, Literal, ParamSpec, TypeVar

from rice_factor.domain.failures.llm_errors import (
    LLMAPIError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from rice_factor.domain.services.failure_service import FailureService

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def handle_llm_errors(
    phase: str,
    failure_service: FailureService | None = None,
    max_retries: int = 0,
    retry_on: tuple[type[LLMError], ...] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for handling LLM errors consistently.

    Catches LLMError and subclasses, logs them, optionally creates
    FailureReport artifacts, and re-raises with enhanced context.

    Args:
        phase: The lifecycle phase for failure reports
        failure_service: Service for creating failure reports (optional)
        max_retries: Maximum retry attempts for recoverable errors (default 0)
        retry_on: Tuple of error types to retry on (default: API, Timeout, RateLimit)

    Returns:
        Decorated function with error handling

    Example:
        @handle_llm_errors(phase="plan_project", max_retries=3)
        def generate_project_plan(context):
            return llm.generate(...)
    """
    if retry_on is None:
        retry_on = (LLMAPIError, LLMTimeoutError, LLMRateLimitError)

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: LLMError | None = None
            attempts = 0

            while attempts <= max_retries:
                try:
                    return func(*args, **kwargs)
                except LLMError as e:
                    last_error = e
                    attempts += 1

                    # Log the error
                    _log_error(e, func.__name__, attempts, max_retries)

                    # Check if we should retry
                    should_retry = (
                        isinstance(e, retry_on)
                        and e.recoverable
                        and attempts <= max_retries
                    )

                    if not should_retry:
                        # Create failure report if service provided
                        if failure_service is not None:
                            failure_service.create_failure_report(
                                error=e,
                                phase=phase,
                            )

                        # Re-raise the error
                        raise

                    # Log retry attempt
                    logger.info(
                        f"Retrying {func.__name__} after {type(e).__name__} "
                        f"(attempt {attempts}/{max_retries})"
                    )

            # This should not be reached, but just in case
            if last_error is not None:
                raise last_error
            raise RuntimeError("Unexpected state in error handler")

        return wrapper

    return decorator


def _log_error(
    error: LLMError,
    func_name: str,
    attempt: int,
    max_retries: int,
) -> None:
    """Log an LLM error with context.

    Args:
        error: The error to log
        func_name: Name of the function that raised the error
        attempt: Current attempt number
        max_retries: Maximum retry attempts
    """
    level = logging.WARNING if error.recoverable else logging.ERROR

    logger.log(
        level,
        f"LLM error in {func_name}: {type(error).__name__} - {error}",
        extra={
            "error_type": type(error).__name__,
            "recoverable": error.recoverable,
            "attempt": attempt,
            "max_retries": max_retries,
        },
    )


class LLMErrorHandler:
    """Context manager for handling LLM errors.

    Alternative to the decorator for more complex scenarios.

    Example:
        with LLMErrorHandler(phase="plan_project", failure_service=fs) as handler:
            result = llm.generate(...)
            handler.result = result
    """

    def __init__(
        self,
        phase: str,
        failure_service: FailureService | None = None,
        artifact_id: str | None = None,
    ) -> None:
        """Initialize the error handler.

        Args:
            phase: The lifecycle phase for failure reports
            failure_service: Service for creating failure reports
            artifact_id: Related artifact ID if applicable
        """
        self.phase = phase
        self.failure_service = failure_service
        self.artifact_id = artifact_id
        self.result: Any = None
        self.error: LLMError | None = None

    def __enter__(self) -> "LLMErrorHandler":
        """Enter the context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> Literal[False]:
        """Handle any LLM errors on exit.

        Returns:
            False to re-raise the exception (never suppresses exceptions)
        """
        if exc_type is not None and issubclass(exc_type, LLMError):
            self.error = exc_val  # type: ignore[assignment]

            # Log the error
            logger.error(
                f"LLM error in phase {self.phase}: {type(exc_val).__name__} - {exc_val}"
            )

            # Create failure report if service provided
            if self.failure_service is not None:
                self.failure_service.create_failure_report(
                    error=exc_val,  # type: ignore[arg-type]
                    phase=self.phase,
                    artifact_id=self.artifact_id,
                )

        # Don't suppress the exception
        return False
