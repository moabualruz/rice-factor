"""Generic webhook notification adapter.

This module provides the base WebhookAdapter for sending notifications
via HTTP webhooks. It supports any URL that accepts POST requests with
JSON payloads.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable


class NotificationEvent(Enum):
    """Types of notification events."""

    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_APPROVED = "artifact.approved"
    ARTIFACT_REJECTED = "artifact.rejected"
    ARTIFACT_LOCKED = "artifact.locked"
    BUILD_STARTED = "build.started"
    BUILD_COMPLETED = "build.completed"
    BUILD_FAILED = "build.failed"
    TEST_PASSED = "test.passed"
    TEST_FAILED = "test.failed"
    COST_THRESHOLD = "cost.threshold"
    RATE_LIMIT = "rate.limit"
    ERROR = "error"


@dataclass
class NotificationPayload:
    """Payload for a notification.

    Attributes:
        event: Type of event.
        timestamp: When the event occurred.
        title: Short title for the notification.
        message: Detailed message.
        severity: Severity level (info, warning, error).
        metadata: Additional event-specific data.
        source: Source system/component.
    """

    event: NotificationEvent
    timestamp: datetime
    title: str
    message: str
    severity: str = "info"
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = "rice-factor"

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "event": self.event.value,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "metadata": self.metadata,
            "source": self.source,
        }


@dataclass
class NotificationResult:
    """Result of sending a notification.

    Attributes:
        success: Whether notification was sent successfully.
        status_code: HTTP status code (if applicable).
        response: Response body or error message.
        duration_ms: Time taken to send in milliseconds.
    """

    success: bool
    status_code: int | None = None
    response: str = ""
    duration_ms: float = 0.0


# Handler type for notification events
NotificationHandler = Callable[[NotificationPayload], None]


class WebhookAdapter:
    """Generic webhook notification adapter.

    Sends notifications to any HTTP endpoint that accepts
    JSON POST requests.

    Example:
        >>> adapter = WebhookAdapter(url="https://example.com/webhook")
        >>> payload = NotificationPayload(
        ...     event=NotificationEvent.ARTIFACT_APPROVED,
        ...     timestamp=datetime.now(UTC),
        ...     title="Artifact Approved",
        ...     message="ProjectPlan was approved",
        ... )
        >>> result = adapter.send(payload)
    """

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the webhook adapter.

        Args:
            url: Webhook URL to POST to.
            headers: Optional HTTP headers to include.
            timeout: Request timeout in seconds.
            verify_ssl: Whether to verify SSL certificates.
            retry_count: Number of retries on failure.
            retry_delay: Delay between retries in seconds.
        """
        self._url = url
        self._headers = headers or {}
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._retry_count = retry_count
        self._retry_delay = retry_delay
        self._enabled = True
        self._event_filters: set[NotificationEvent] = set()
        self._lock = threading.RLock()

    @property
    def url(self) -> str:
        """Get the webhook URL."""
        return self._url

    @property
    def enabled(self) -> bool:
        """Check if webhook is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable the webhook."""
        with self._lock:
            self._enabled = True

    def disable(self) -> None:
        """Disable the webhook."""
        with self._lock:
            self._enabled = False

    def set_event_filter(self, events: list[NotificationEvent]) -> None:
        """Set which events to send notifications for.

        Args:
            events: List of events to filter for. Empty list means all events.
        """
        with self._lock:
            self._event_filters = set(events)

    def should_send(self, event: NotificationEvent) -> bool:
        """Check if a notification should be sent for this event.

        Args:
            event: Event type to check.

        Returns:
            True if notification should be sent.
        """
        with self._lock:
            if not self._enabled:
                return False
            if not self._event_filters:
                return True  # No filter means all events
            return event in self._event_filters

    def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send a notification.

        Args:
            payload: Notification payload to send.

        Returns:
            NotificationResult with success status.
        """
        if not self.should_send(payload.event):
            return NotificationResult(
                success=True,
                response="Notification filtered out",
            )

        import time

        start_time = time.monotonic()

        for attempt in range(self._retry_count):
            try:
                result = self._do_send(payload)
                result.duration_ms = (time.monotonic() - start_time) * 1000
                if result.success:
                    return result
            except Exception as e:
                if attempt == self._retry_count - 1:
                    return NotificationResult(
                        success=False,
                        response=str(e),
                        duration_ms=(time.monotonic() - start_time) * 1000,
                    )

            time.sleep(self._retry_delay)

        return NotificationResult(
            success=False,
            response="Max retries exceeded",
            duration_ms=(time.monotonic() - start_time) * 1000,
        )

    def _do_send(self, payload: NotificationPayload) -> NotificationResult:
        """Perform the actual HTTP request.

        Args:
            payload: Notification payload.

        Returns:
            NotificationResult with response details.
        """
        try:
            import httpx
        except ImportError:
            try:
                import requests

                return self._send_with_requests(payload)
            except ImportError:
                return NotificationResult(
                    success=False,
                    response="Neither httpx nor requests is installed",
                )

        headers = {
            "Content-Type": "application/json",
            **self._headers,
        }

        try:
            with httpx.Client(
                timeout=self._timeout,
                verify=self._verify_ssl,
            ) as client:
                response = client.post(
                    self._url,
                    json=payload.to_dict(),
                    headers=headers,
                )

                return NotificationResult(
                    success=response.is_success,
                    status_code=response.status_code,
                    response=response.text[:500],  # Truncate response
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                response=str(e),
            )

    def _send_with_requests(self, payload: NotificationPayload) -> NotificationResult:
        """Send using requests library as fallback.

        Args:
            payload: Notification payload.

        Returns:
            NotificationResult with response details.
        """
        import requests

        headers = {
            "Content-Type": "application/json",
            **self._headers,
        }

        try:
            response = requests.post(
                self._url,
                json=payload.to_dict(),
                headers=headers,
                timeout=self._timeout,
                verify=self._verify_ssl,
            )

            return NotificationResult(
                success=response.ok,
                status_code=response.status_code,
                response=response.text[:500],
            )
        except Exception as e:
            return NotificationResult(
                success=False,
                response=str(e),
            )

    async def send_async(self, payload: NotificationPayload) -> NotificationResult:
        """Send a notification asynchronously.

        Args:
            payload: Notification payload to send.

        Returns:
            NotificationResult with success status.
        """
        if not self.should_send(payload.event):
            return NotificationResult(
                success=True,
                response="Notification filtered out",
            )

        try:
            import httpx
        except ImportError:
            # Fall back to sync send
            return self.send(payload)

        import time

        start_time = time.monotonic()

        headers = {
            "Content-Type": "application/json",
            **self._headers,
        }

        for attempt in range(self._retry_count):
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout,
                    verify=self._verify_ssl,
                ) as client:
                    response = await client.post(
                        self._url,
                        json=payload.to_dict(),
                        headers=headers,
                    )

                    result = NotificationResult(
                        success=response.is_success,
                        status_code=response.status_code,
                        response=response.text[:500],
                        duration_ms=(time.monotonic() - start_time) * 1000,
                    )

                    if result.success:
                        return result

            except Exception as e:
                if attempt == self._retry_count - 1:
                    return NotificationResult(
                        success=False,
                        response=str(e),
                        duration_ms=(time.monotonic() - start_time) * 1000,
                    )

            import asyncio

            await asyncio.sleep(self._retry_delay)

        return NotificationResult(
            success=False,
            response="Max retries exceeded",
            duration_ms=(time.monotonic() - start_time) * 1000,
        )

    def to_dict(self) -> dict[str, Any]:
        """Export adapter configuration.

        Returns:
            Dictionary with configuration.
        """
        return {
            "url": self._url,
            "enabled": self._enabled,
            "timeout": self._timeout,
            "verify_ssl": self._verify_ssl,
            "retry_count": self._retry_count,
            "event_filters": [e.value for e in self._event_filters],
        }
