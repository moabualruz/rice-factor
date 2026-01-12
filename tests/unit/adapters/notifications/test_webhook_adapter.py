"""Unit tests for WebhookAdapter."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.notifications.webhook_adapter import (
    NotificationEvent,
    NotificationPayload,
    NotificationResult,
    WebhookAdapter,
)


class TestNotificationEvent:
    """Tests for NotificationEvent enum."""

    def test_all_events_have_values(self) -> None:
        """All notification events should have string values."""
        for event in NotificationEvent:
            assert isinstance(event.value, str)
            assert len(event.value) > 0  # Non-empty value

    def test_artifact_events(self) -> None:
        """Artifact events should be defined."""
        assert NotificationEvent.ARTIFACT_CREATED.value == "artifact.created"
        assert NotificationEvent.ARTIFACT_APPROVED.value == "artifact.approved"
        assert NotificationEvent.ARTIFACT_REJECTED.value == "artifact.rejected"
        assert NotificationEvent.ARTIFACT_LOCKED.value == "artifact.locked"

    def test_build_events(self) -> None:
        """Build events should be defined."""
        assert NotificationEvent.BUILD_STARTED.value == "build.started"
        assert NotificationEvent.BUILD_COMPLETED.value == "build.completed"
        assert NotificationEvent.BUILD_FAILED.value == "build.failed"

    def test_test_events(self) -> None:
        """Test events should be defined."""
        assert NotificationEvent.TEST_PASSED.value == "test.passed"
        assert NotificationEvent.TEST_FAILED.value == "test.failed"


class TestNotificationPayload:
    """Tests for NotificationPayload dataclass."""

    def test_create_payload(self) -> None:
        """Should create payload with required fields."""
        timestamp = datetime.now(UTC)
        payload = NotificationPayload(
            event=NotificationEvent.ARTIFACT_CREATED,
            timestamp=timestamp,
            title="Test Title",
            message="Test message",
        )

        assert payload.event == NotificationEvent.ARTIFACT_CREATED
        assert payload.timestamp == timestamp
        assert payload.title == "Test Title"
        assert payload.message == "Test message"
        assert payload.severity == "info"  # Default
        assert payload.source == "rice-factor"  # Default

    def test_create_payload_with_metadata(self) -> None:
        """Should create payload with metadata."""
        payload = NotificationPayload(
            event=NotificationEvent.BUILD_FAILED,
            timestamp=datetime.now(UTC),
            title="Build Failed",
            message="Build failed with errors",
            severity="error",
            metadata={"build_id": "123", "errors": 5},
        )

        assert payload.severity == "error"
        assert payload.metadata["build_id"] == "123"
        assert payload.metadata["errors"] == 5

    def test_to_dict(self) -> None:
        """Should convert payload to dictionary."""
        timestamp = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        payload = NotificationPayload(
            event=NotificationEvent.ARTIFACT_APPROVED,
            timestamp=timestamp,
            title="Approved",
            message="Artifact was approved",
            source="test-system",
        )

        result = payload.to_dict()

        assert result["event"] == "artifact.approved"
        assert result["timestamp"] == "2026-01-01T12:00:00+00:00"
        assert result["title"] == "Approved"
        assert result["message"] == "Artifact was approved"
        assert result["source"] == "test-system"

    def test_default_metadata_is_empty_dict(self) -> None:
        """Default metadata should be empty dict."""
        payload = NotificationPayload(
            event=NotificationEvent.ERROR,
            timestamp=datetime.now(UTC),
            title="Error",
            message="An error occurred",
        )

        assert payload.metadata == {}


class TestNotificationResult:
    """Tests for NotificationResult dataclass."""

    def test_success_result(self) -> None:
        """Should create success result."""
        result = NotificationResult(
            success=True,
            status_code=200,
            response="ok",
            duration_ms=50.5,
        )

        assert result.success is True
        assert result.status_code == 200
        assert result.response == "ok"
        assert result.duration_ms == 50.5

    def test_failure_result(self) -> None:
        """Should create failure result."""
        result = NotificationResult(
            success=False,
            response="Connection refused",
        )

        assert result.success is False
        assert result.status_code is None
        assert result.response == "Connection refused"

    def test_default_values(self) -> None:
        """Should have sensible defaults."""
        result = NotificationResult(success=True)

        assert result.status_code is None
        assert result.response == ""
        assert result.duration_ms == 0.0


class TestWebhookAdapterInit:
    """Tests for WebhookAdapter initialization."""

    def test_init_with_url(self) -> None:
        """Should initialize with URL."""
        adapter = WebhookAdapter(url="https://example.com/webhook")

        assert adapter.url == "https://example.com/webhook"
        assert adapter.enabled is True

    def test_init_with_headers(self) -> None:
        """Should accept custom headers."""
        headers = {"Authorization": "Bearer token123"}
        adapter = WebhookAdapter(
            url="https://example.com/webhook",
            headers=headers,
        )

        assert adapter._headers == headers

    def test_init_with_timeout(self) -> None:
        """Should accept custom timeout."""
        adapter = WebhookAdapter(
            url="https://example.com/webhook",
            timeout=60.0,
        )

        assert adapter._timeout == 60.0

    def test_init_with_retry_settings(self) -> None:
        """Should accept retry settings."""
        adapter = WebhookAdapter(
            url="https://example.com/webhook",
            retry_count=5,
            retry_delay=2.0,
        )

        assert adapter._retry_count == 5
        assert adapter._retry_delay == 2.0


class TestWebhookAdapterEnable:
    """Tests for WebhookAdapter enable/disable."""

    def test_enable(self) -> None:
        """Should enable webhook."""
        adapter = WebhookAdapter(url="https://example.com")
        adapter.disable()
        assert adapter.enabled is False

        adapter.enable()
        assert adapter.enabled is True

    def test_disable(self) -> None:
        """Should disable webhook."""
        adapter = WebhookAdapter(url="https://example.com")
        assert adapter.enabled is True

        adapter.disable()
        assert adapter.enabled is False


class TestWebhookAdapterEventFilter:
    """Tests for WebhookAdapter event filtering."""

    def test_set_event_filter(self) -> None:
        """Should set event filter."""
        adapter = WebhookAdapter(url="https://example.com")
        adapter.set_event_filter([
            NotificationEvent.BUILD_FAILED,
            NotificationEvent.TEST_FAILED,
        ])

        assert adapter.should_send(NotificationEvent.BUILD_FAILED) is True
        assert adapter.should_send(NotificationEvent.TEST_FAILED) is True
        assert adapter.should_send(NotificationEvent.BUILD_COMPLETED) is False

    def test_empty_filter_allows_all(self) -> None:
        """Empty filter should allow all events."""
        adapter = WebhookAdapter(url="https://example.com")
        adapter.set_event_filter([])

        for event in NotificationEvent:
            assert adapter.should_send(event) is True

    def test_should_send_respects_enabled(self) -> None:
        """should_send should return False when disabled."""
        adapter = WebhookAdapter(url="https://example.com")
        adapter.disable()

        assert adapter.should_send(NotificationEvent.BUILD_FAILED) is False


class TestWebhookAdapterSend:
    """Tests for WebhookAdapter.send method."""

    def test_send_returns_filtered_result_when_filtered(self) -> None:
        """Should return filtered result when event is filtered."""
        adapter = WebhookAdapter(url="https://example.com")
        adapter.set_event_filter([NotificationEvent.ERROR])

        payload = NotificationPayload(
            event=NotificationEvent.BUILD_STARTED,  # Not in filter
            timestamp=datetime.now(UTC),
            title="Build Started",
            message="Starting build",
        )

        result = adapter.send(payload)

        assert result.success is True
        assert "filtered" in result.response.lower()

    def test_send_returns_filtered_when_disabled(self) -> None:
        """Should return filtered when adapter is disabled."""
        adapter = WebhookAdapter(url="https://example.com")
        adapter.disable()

        payload = NotificationPayload(
            event=NotificationEvent.BUILD_FAILED,
            timestamp=datetime.now(UTC),
            title="Build Failed",
            message="Build failed",
        )

        result = adapter.send(payload)

        assert result.success is True
        assert "filtered" in result.response.lower()

    def test_send_with_mocked_do_send(self) -> None:
        """Should send using _do_send method."""
        adapter = WebhookAdapter(url="https://example.com/webhook")
        payload = NotificationPayload(
            event=NotificationEvent.ARTIFACT_APPROVED,
            timestamp=datetime.now(UTC),
            title="Approved",
            message="Artifact approved",
        )

        # Mock _do_send directly to avoid HTTP library issues
        with patch.object(adapter, "_do_send") as mock_do_send:
            mock_do_send.return_value = NotificationResult(
                success=True,
                status_code=200,
                response="ok",
            )
            result = adapter.send(payload)

        assert result.success is True
        assert result.status_code == 200
        mock_do_send.assert_called_once()

    def test_send_retries_on_failure(self) -> None:
        """Should retry on failure."""
        adapter = WebhookAdapter(
            url="https://example.com",
            retry_count=3,
            retry_delay=0.01,  # Fast for testing
        )
        payload = NotificationPayload(
            event=NotificationEvent.ERROR,
            timestamp=datetime.now(UTC),
            title="Error",
            message="Error occurred",
        )

        call_count = 0

        def failing_send(p: NotificationPayload) -> NotificationResult:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return NotificationResult(success=False, response="Failed")
            return NotificationResult(success=True, response="ok")

        with patch.object(adapter, "_do_send", side_effect=failing_send):
            result = adapter.send(payload)

        assert result.success is True
        assert call_count == 3

    def test_send_returns_error_after_max_retries(self) -> None:
        """Should return error after max retries."""
        adapter = WebhookAdapter(
            url="https://example.com",
            retry_count=2,
            retry_delay=0.01,
        )
        payload = NotificationPayload(
            event=NotificationEvent.ERROR,
            timestamp=datetime.now(UTC),
            title="Error",
            message="Error occurred",
        )

        with patch.object(adapter, "_do_send") as mock_do_send:
            mock_do_send.return_value = NotificationResult(
                success=False,
                response="Connection refused",
            )
            result = adapter.send(payload)

        assert result.success is False
        assert mock_do_send.call_count == 2


class TestWebhookAdapterToDict:
    """Tests for WebhookAdapter.to_dict method."""

    def test_to_dict(self) -> None:
        """Should export configuration as dict."""
        adapter = WebhookAdapter(
            url="https://example.com/webhook",
            timeout=45.0,
            verify_ssl=False,
            retry_count=5,
        )
        adapter.set_event_filter([NotificationEvent.ERROR])

        result = adapter.to_dict()

        assert result["url"] == "https://example.com/webhook"
        assert result["enabled"] is True
        assert result["timeout"] == 45.0
        assert result["verify_ssl"] is False
        assert result["retry_count"] == 5
        assert "error" in result["event_filters"]


class TestWebhookAdapterAsync:
    """Tests for WebhookAdapter async methods."""

    @pytest.mark.asyncio
    async def test_send_async_filtered(self) -> None:
        """Async send should filter like sync."""
        adapter = WebhookAdapter(url="https://example.com")
        adapter.disable()

        payload = NotificationPayload(
            event=NotificationEvent.BUILD_FAILED,
            timestamp=datetime.now(UTC),
            title="Failed",
            message="Build failed",
        )

        result = await adapter.send_async(payload)

        assert result.success is True
        assert "filtered" in result.response.lower()
