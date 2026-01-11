"""Unit tests for FailureService."""

from datetime import UTC
from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.failure_report import (
    FailureCategory,
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
from rice_factor.domain.services.failure_service import FailureService


class TestFailureServiceCreation:
    """Tests for FailureService initialization."""

    def test_create_without_callbacks(self) -> None:
        """Can create service without callbacks."""
        service = FailureService()
        assert service._save_callback is None
        assert service._load_callback is None

    def test_create_with_save_callback(self) -> None:
        """Can create service with save callback."""
        mock_callback = MagicMock()
        service = FailureService(save_callback=mock_callback)
        assert service._save_callback is mock_callback

    def test_create_with_load_callback(self) -> None:
        """Can create service with load callback."""
        mock_callback = MagicMock()
        service = FailureService(load_callback=mock_callback)
        assert service._load_callback is mock_callback


class TestCreateFailureReport:
    """Tests for create_failure_report method."""

    @pytest.fixture
    def service(self) -> FailureService:
        """Create a service without storage."""
        return FailureService()

    def test_creates_envelope_from_llm_error(self, service: FailureService) -> None:
        """Should create an ArtifactEnvelope from an LLM error."""
        error = LLMError("Test error")

        envelope = service.create_failure_report(error, phase="plan_project")

        assert isinstance(envelope, ArtifactEnvelope)
        assert envelope.artifact_type == ArtifactType.FAILURE_REPORT
        assert envelope.status == ArtifactStatus.DRAFT

    def test_includes_phase(self, service: FailureService) -> None:
        """Should include phase in payload."""
        error = LLMError("Test")

        envelope = service.create_failure_report(error, phase="plan_architecture")

        assert envelope.payload.phase == "plan_architecture"

    def test_includes_artifact_id(self, service: FailureService) -> None:
        """Should include related artifact ID if provided."""
        error = LLMError("Test")

        envelope = service.create_failure_report(
            error, phase="impl", artifact_id="abc-123"
        )

        assert envelope.payload.artifact_id == "abc-123"

    def test_includes_raw_response(self, service: FailureService) -> None:
        """Should include raw response if provided."""
        error = LLMError("Test")

        envelope = service.create_failure_report(
            error, phase="impl", raw_response='{"error": "test"}'
        )

        assert envelope.payload.raw_response == '{"error": "test"}'

    def test_calls_save_callback_if_provided(self) -> None:
        """Should call save callback when provided."""
        mock_callback = MagicMock()
        service = FailureService(save_callback=mock_callback)
        error = LLMError("Test")

        service.create_failure_report(error, phase="test")

        mock_callback.assert_called_once()


class TestIsRecoverable:
    """Tests for is_recoverable method."""

    @pytest.fixture
    def service(self) -> FailureService:
        """Create a service instance."""
        return FailureService()

    @pytest.mark.parametrize(
        "error,expected",
        [
            (LLMAPIError("API error", status_code=500), True),
            (LLMTimeoutError(), True),
            (LLMRateLimitError(), True),
            (LLMMissingInformationError(), False),
            (LLMInvalidRequestError(), False),
        ],
    )
    def test_recoverability(
        self,
        service: FailureService,
        error: LLMError,
        expected: bool,
    ) -> None:
        """Each error type has correct recoverability."""
        assert service.is_recoverable(error) is expected


class TestGetRecoveryAction:
    """Tests for get_recovery_action method."""

    @pytest.fixture
    def service(self) -> FailureService:
        """Create a service instance."""
        return FailureService()

    def test_missing_info_requires_human_input(self, service: FailureService) -> None:
        """Missing info error requires human input."""
        error = LLMMissingInformationError()
        action = service.get_recovery_action(error)
        assert action == RecoveryAction.HUMAN_INPUT_REQUIRED

    def test_invalid_request_needs_fix(self, service: FailureService) -> None:
        """Invalid request error needs fix and retry."""
        error = LLMInvalidRequestError()
        action = service.get_recovery_action(error)
        assert action == RecoveryAction.FIX_AND_RETRY

    def test_rate_limit_retry_after_delay(self, service: FailureService) -> None:
        """Rate limit error suggests retry after delay."""
        error = LLMRateLimitError()
        action = service.get_recovery_action(error)
        assert action == RecoveryAction.RETRY_AFTER_DELAY

    def test_api_error_retry(self, service: FailureService) -> None:
        """API error suggests retry."""
        error = LLMAPIError("Server error", status_code=500)
        action = service.get_recovery_action(error)
        assert action == RecoveryAction.RETRY

    def test_timeout_error_retry(self, service: FailureService) -> None:
        """Timeout error suggests retry."""
        error = LLMTimeoutError()
        action = service.get_recovery_action(error)
        assert action == RecoveryAction.RETRY


class TestGetCategory:
    """Tests for _get_category method."""

    @pytest.fixture
    def service(self) -> FailureService:
        """Create a service instance."""
        return FailureService()

    @pytest.mark.parametrize(
        "error,expected_category",
        [
            (LLMMissingInformationError(), FailureCategory.MISSING_INFORMATION),
            (LLMInvalidRequestError(), FailureCategory.INVALID_REQUEST),
            (LLMAPIError("test", status_code=500), FailureCategory.API_ERROR),
            (LLMTimeoutError(), FailureCategory.TIMEOUT),
            (LLMRateLimitError(), FailureCategory.RATE_LIMIT),
            (LLMError("generic"), FailureCategory.INTERNAL_ERROR),
        ],
    )
    def test_category_mapping(
        self,
        service: FailureService,
        error: LLMError,
        expected_category: FailureCategory,
    ) -> None:
        """Each error type maps to correct category."""
        category = service._get_category(error)
        assert category == expected_category


class TestBuildDetails:
    """Tests for _build_details method."""

    @pytest.fixture
    def service(self) -> FailureService:
        """Create a service instance."""
        return FailureService()

    def test_includes_error_type(self, service: FailureService) -> None:
        """Details should include error type."""
        error = LLMError("Test")
        details = service._build_details(error)
        assert details["error_type"] == "LLMError"

    def test_includes_message(self, service: FailureService) -> None:
        """Details should include message."""
        error = LLMError("Test message")
        details = service._build_details(error)
        assert details["message"] == "Test message"

    def test_includes_missing_items(self, service: FailureService) -> None:
        """Should include missing items for MissingInformationError."""
        error = LLMMissingInformationError(missing_items=["X", "Y"])
        details = service._build_details(error)
        assert details["missing_items"] == ["X", "Y"]

    def test_includes_status_code(self, service: FailureService) -> None:
        """Should include status code for APIError."""
        error = LLMAPIError("test", status_code=503, provider="claude")
        details = service._build_details(error)
        assert details["status_code"] == 503
        assert details["provider"] == "claude"

    def test_includes_timeout_seconds(self, service: FailureService) -> None:
        """Should include timeout for TimeoutError."""
        error = LLMTimeoutError(timeout_seconds=120)
        details = service._build_details(error)
        assert details["timeout_seconds"] == 120


class TestResolveFailure:
    """Tests for resolve_failure method."""

    def test_returns_none_without_load_callback(self) -> None:
        """Should return None when no load callback configured."""
        service = FailureService()
        result = service.resolve_failure("abc-123", "Fixed manually")
        assert result is None

    def test_updates_status_to_approved(self) -> None:
        """Should update status to APPROVED on resolution."""
        from datetime import datetime
        from uuid import uuid4

        from rice_factor.domain.artifacts.payloads.failure_report import (
            FailureCategory,
            FailureReportPayload,
            RecoveryAction,
        )

        # Create a real payload for the mock envelope
        mock_payload = FailureReportPayload(
            phase="plan_project",
            category=FailureCategory.MISSING_INFORMATION,
            summary="Test failure",
            details={"original": "data"},
            recovery_action=RecoveryAction.HUMAN_INPUT_REQUIRED,
        )
        mock_envelope = MagicMock()
        mock_envelope.id = uuid4()
        mock_envelope.artifact_type = ArtifactType.FAILURE_REPORT
        mock_envelope.status = ArtifactStatus.DRAFT
        mock_envelope.created_by = "system"
        mock_envelope.created_at = datetime.now(UTC)
        mock_envelope.payload = mock_payload

        # Create mock callbacks
        mock_load = MagicMock(return_value=mock_envelope)
        mock_save = MagicMock()

        service = FailureService(save_callback=mock_save, load_callback=mock_load)
        result = service.resolve_failure("abc-123", "Fixed by user")

        assert result is not None
        mock_load.assert_called_once_with("abc-123")
        mock_save.assert_called_once()
        saved_envelope = mock_save.call_args[0][0]
        assert saved_envelope.status == ArtifactStatus.APPROVED

    def test_returns_none_if_not_found(self) -> None:
        """Should return None if failure not found."""
        mock_load = MagicMock(return_value=None)

        service = FailureService(load_callback=mock_load)
        result = service.resolve_failure("abc-123", "resolution")

        assert result is None
