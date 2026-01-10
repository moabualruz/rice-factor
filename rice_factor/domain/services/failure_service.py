"""Failure handling service.

This module provides the FailureService for managing blocking failures
and creating FailureReport artifacts.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.failure_report import (
    FailureCategory,
    FailureReportPayload,
    RecoveryAction,
)
from rice_factor.domain.failures.llm_errors import (
    LLMAPIError,
    LLMError,
    LLMInvalidRequestError,
    LLMMissingInformationError,
    LLMRateLimitError,
    LLMTimeoutError,
)

# Type alias for a function that saves failure reports
SaveFailureCallback = Callable[[ArtifactEnvelope[FailureReportPayload]], None]

# Type alias for a function that loads failure reports
LoadFailureCallback = Callable[[str], ArtifactEnvelope[FailureReportPayload] | None]


class FailureService:
    """Service for handling LLM failures and creating FailureReport artifacts.

    Responsible for:
    - Creating FailureReport artifacts from LLM errors
    - Determining if an error is recoverable
    - Suggesting recovery actions

    Note: Storage operations are handled via optional callbacks to avoid
    coupling to specific storage implementations.
    """

    def __init__(
        self,
        save_callback: SaveFailureCallback | None = None,
        load_callback: LoadFailureCallback | None = None,
    ) -> None:
        """Initialize the failure service.

        Args:
            save_callback: Optional callback for saving failure reports.
            load_callback: Optional callback for loading failure reports.
        """
        self._save_callback = save_callback
        self._load_callback = load_callback

    def create_failure_report(
        self,
        error: LLMError,
        phase: str,
        artifact_id: str | None = None,
        raw_response: str | None = None,
    ) -> ArtifactEnvelope[FailureReportPayload]:
        """Create a FailureReport artifact from an LLM error.

        Args:
            error: The LLM error that occurred
            phase: The lifecycle phase where the failure occurred
            artifact_id: Related artifact ID if applicable
            raw_response: Raw LLM response if available

        Returns:
            ArtifactEnvelope containing the FailureReportPayload
        """
        category = self._get_category(error)
        recovery_action = self.get_recovery_action(error)

        # Build details dict from error attributes
        details = self._build_details(error)

        payload = FailureReportPayload(
            phase=phase,
            artifact_id=artifact_id,
            category=category,
            summary=str(error),
            details=details,
            blocking=not error.recoverable,
            recovery_action=recovery_action,
            timestamp=datetime.now(UTC),
            raw_response=raw_response,
        )

        # Create envelope - payload is passed directly as Pydantic model
        envelope: ArtifactEnvelope[FailureReportPayload] = ArtifactEnvelope(
            artifact_type=ArtifactType.FAILURE_REPORT,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.SYSTEM,
            payload=payload,
        )

        # Save via callback if provided
        if self._save_callback is not None:
            self._save_callback(envelope)

        return envelope

    def is_recoverable(self, error: LLMError) -> bool:
        """Check if an error is recoverable without human intervention.

        Args:
            error: The LLM error to check

        Returns:
            True if the error can be recovered from (e.g., by retry)
        """
        return error.recoverable

    def get_recovery_action(self, error: LLMError) -> RecoveryAction:
        """Get the recommended recovery action for an error.

        Args:
            error: The LLM error to get action for

        Returns:
            Recommended RecoveryAction
        """
        if isinstance(error, LLMMissingInformationError):
            return RecoveryAction.HUMAN_INPUT_REQUIRED
        elif isinstance(error, LLMInvalidRequestError):
            return RecoveryAction.FIX_AND_RETRY
        elif isinstance(error, LLMRateLimitError):
            return RecoveryAction.RETRY_AFTER_DELAY
        elif isinstance(error, (LLMAPIError, LLMTimeoutError)):
            return RecoveryAction.RETRY
        else:
            # Unknown error - check recoverability
            if error.recoverable:
                return RecoveryAction.RETRY
            return RecoveryAction.ABORT

    def resolve_failure(
        self,
        failure_id: str,
        resolution: str,
    ) -> ArtifactEnvelope[FailureReportPayload] | None:
        """Mark a failure as resolved.

        Args:
            failure_id: ID of the failure report artifact
            resolution: Description of how the failure was resolved

        Returns:
            Updated envelope if found and updated, None otherwise
        """
        if self._load_callback is None:
            return None

        # Load the existing failure report
        envelope = self._load_callback(failure_id)
        if envelope is None:
            return None

        # Get existing payload and update details with resolution info
        old_payload = envelope.payload
        old_details = dict(old_payload.details) if old_payload.details else {}
        old_details["resolution"] = resolution
        old_details["resolved_at"] = datetime.now(UTC).isoformat()

        # Create new payload with updated details
        new_payload = FailureReportPayload(
            phase=old_payload.phase,
            artifact_id=old_payload.artifact_id,
            category=old_payload.category,
            summary=old_payload.summary,
            details=old_details,
            blocking=old_payload.blocking,
            recovery_action=old_payload.recovery_action,
            timestamp=old_payload.timestamp,
            raw_response=old_payload.raw_response,
        )

        # Create updated envelope with new status
        updated_envelope: ArtifactEnvelope[FailureReportPayload] = ArtifactEnvelope(
            id=envelope.id,
            artifact_type=envelope.artifact_type,
            status=ArtifactStatus.APPROVED,  # Mark as resolved
            created_by=envelope.created_by,
            created_at=envelope.created_at,
            payload=new_payload,
        )

        # Save via callback if provided
        if self._save_callback is not None:
            self._save_callback(updated_envelope)

        return updated_envelope

    def _get_category(self, error: LLMError) -> FailureCategory:
        """Map an LLM error to a failure category.

        Args:
            error: The LLM error

        Returns:
            Appropriate FailureCategory
        """
        if isinstance(error, LLMMissingInformationError):
            return FailureCategory.MISSING_INFORMATION
        elif isinstance(error, LLMInvalidRequestError):
            return FailureCategory.INVALID_REQUEST
        elif isinstance(error, LLMAPIError):
            return FailureCategory.API_ERROR
        elif isinstance(error, LLMTimeoutError):
            return FailureCategory.TIMEOUT
        elif isinstance(error, LLMRateLimitError):
            return FailureCategory.RATE_LIMIT
        else:
            return FailureCategory.INTERNAL_ERROR

    def _build_details(self, error: LLMError) -> dict[str, Any]:
        """Build a details dict from error attributes.

        Args:
            error: The LLM error

        Returns:
            Dict with relevant error details
        """
        details: dict[str, Any] = {
            "error_type": type(error).__name__,
            "message": error.message,
            "recoverable": error.recoverable,
        }

        if error.details:
            details["error_details"] = error.details

        # Add type-specific details
        if isinstance(error, LLMMissingInformationError):
            details["missing_items"] = error.missing_items
        elif isinstance(error, LLMInvalidRequestError):
            details["invalid_reason"] = error.invalid_reason
        elif isinstance(error, LLMAPIError):
            details["status_code"] = error.status_code
            details["provider"] = error.provider
        elif isinstance(error, LLMTimeoutError):
            details["timeout_seconds"] = error.timeout_seconds
        elif isinstance(error, LLMRateLimitError):
            details["retry_after"] = error.retry_after
            details["provider"] = error.provider

        return details
