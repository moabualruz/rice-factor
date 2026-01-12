"""Tests for WebSocket functionality."""

from __future__ import annotations

import pytest

from rice_factor_web.backend.websocket.events import (
    WebSocketEvent,
    WebSocketEventType,
    artifact_approved_event,
    diff_approved_event,
    notification_event,
)
from rice_factor_web.backend.websocket.manager import ConnectionManager


def test_websocket_event_to_json() -> None:
    """Test WebSocket event serialization to JSON."""
    event = WebSocketEvent(
        event_type=WebSocketEventType.ARTIFACT_APPROVED,
        data={"artifact_id": "123", "approved_by": "test"},
    )
    json_str = event.to_json()
    assert '"type": "artifact.approved"' in json_str
    assert '"artifact_id": "123"' in json_str
    assert "timestamp" in json_str


def test_websocket_event_from_json() -> None:
    """Test WebSocket event deserialization from JSON."""
    event = WebSocketEvent(
        event_type=WebSocketEventType.DIFF_APPROVED,
        data={"diff_id": "456"},
    )
    json_str = event.to_json()

    parsed = WebSocketEvent.from_json(json_str)
    assert parsed.event_type == WebSocketEventType.DIFF_APPROVED
    assert parsed.data["diff_id"] == "456"


def test_artifact_approved_event_helper() -> None:
    """Test artifact approved event helper function."""
    event = artifact_approved_event(
        artifact_id="test-id",
        artifact_type="project_plan",
        approved_by="test_user",
    )
    assert event.event_type == WebSocketEventType.ARTIFACT_APPROVED
    assert event.data["artifact_id"] == "test-id"
    assert event.data["artifact_type"] == "project_plan"
    assert event.data["approved_by"] == "test_user"


def test_diff_approved_event_helper() -> None:
    """Test diff approved event helper function."""
    event = diff_approved_event(
        diff_id="diff-id",
        target_file="src/main.py",
        approved_by="reviewer",
    )
    assert event.event_type == WebSocketEventType.DIFF_APPROVED
    assert event.data["diff_id"] == "diff-id"
    assert event.data["target_file"] == "src/main.py"


def test_notification_event_helper() -> None:
    """Test notification event helper function."""
    event = notification_event(
        title="Test Title",
        message="Test message",
        severity="warning",
    )
    assert event.event_type == WebSocketEventType.NOTIFICATION
    assert event.data["title"] == "Test Title"
    assert event.data["severity"] == "warning"


def test_connection_manager_initial_state() -> None:
    """Test connection manager starts with no connections."""
    manager = ConnectionManager()
    assert manager.connection_count == 0


@pytest.mark.asyncio
async def test_connection_manager_broadcast_no_connections() -> None:
    """Test broadcasting with no connections doesn't error."""
    manager = ConnectionManager()
    event = notification_event("Test", "Message")
    # Should not raise
    await manager.broadcast(event)
