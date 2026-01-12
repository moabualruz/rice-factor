"""WebSocket event types and models.

Defines the event types that can be broadcast to connected clients
for real-time updates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class WebSocketEventType(str, Enum):
    """Types of real-time events that can be broadcast."""

    # Artifact events
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_APPROVED = "artifact.approved"
    ARTIFACT_REJECTED = "artifact.rejected"
    ARTIFACT_LOCKED = "artifact.locked"
    ARTIFACT_MODIFIED = "artifact.modified"

    # Diff events
    DIFF_CREATED = "diff.created"
    DIFF_APPROVED = "diff.approved"
    DIFF_REJECTED = "diff.rejected"
    DIFF_APPLIED = "diff.applied"

    # Phase events
    PHASE_CHANGED = "phase.changed"

    # Build/test events
    BUILD_STARTED = "build.started"
    BUILD_COMPLETED = "build.completed"
    BUILD_FAILED = "build.failed"
    TEST_PASSED = "test.passed"
    TEST_FAILED = "test.failed"

    # System events
    ERROR = "error"
    NOTIFICATION = "notification"


@dataclass
class WebSocketEvent:
    """A WebSocket event to broadcast to clients.

    Attributes:
        event_type: The type of event.
        data: Event-specific data payload.
        timestamp: When the event occurred (defaults to now).
    """

    event_type: WebSocketEventType
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self) -> str:
        """Serialize the event to JSON string.

        Returns:
            JSON string representation of the event.
        """
        return json.dumps(
            {
                "type": self.event_type.value,
                "data": self.data,
                "timestamp": self.timestamp.isoformat(),
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketEvent":
        """Deserialize an event from JSON string.

        Args:
            json_str: JSON string to parse.

        Returns:
            WebSocketEvent instance.
        """
        parsed = json.loads(json_str)
        return cls(
            event_type=WebSocketEventType(parsed["type"]),
            data=parsed["data"],
            timestamp=datetime.fromisoformat(parsed["timestamp"]),
        )


def artifact_approved_event(
    artifact_id: str,
    artifact_type: str,
    approved_by: str,
) -> WebSocketEvent:
    """Create an artifact approved event.

    Args:
        artifact_id: UUID of the approved artifact.
        artifact_type: Type of the artifact.
        approved_by: User who approved.

    Returns:
        WebSocketEvent for broadcasting.
    """
    return WebSocketEvent(
        event_type=WebSocketEventType.ARTIFACT_APPROVED,
        data={
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "approved_by": approved_by,
        },
    )


def diff_approved_event(
    diff_id: str,
    target_file: str,
    approved_by: str,
) -> WebSocketEvent:
    """Create a diff approved event.

    Args:
        diff_id: UUID of the approved diff.
        target_file: File the diff applies to.
        approved_by: User who approved.

    Returns:
        WebSocketEvent for broadcasting.
    """
    return WebSocketEvent(
        event_type=WebSocketEventType.DIFF_APPROVED,
        data={
            "diff_id": diff_id,
            "target_file": target_file,
            "approved_by": approved_by,
        },
    )


def notification_event(
    title: str,
    message: str,
    severity: str = "info",
) -> WebSocketEvent:
    """Create a notification event.

    Args:
        title: Notification title.
        message: Notification message.
        severity: One of "info", "warning", "error", "success".

    Returns:
        WebSocketEvent for broadcasting.
    """
    return WebSocketEvent(
        event_type=WebSocketEventType.NOTIFICATION,
        data={
            "title": title,
            "message": message,
            "severity": severity,
        },
    )
