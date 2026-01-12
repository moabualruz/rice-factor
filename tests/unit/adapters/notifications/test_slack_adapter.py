"""Unit tests for SlackAdapter."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.notifications.slack_adapter import (
    EVENT_EMOJIS,
    SEVERITY_COLORS,
    SlackAdapter,
)
from rice_factor.adapters.notifications.webhook_adapter import (
    NotificationEvent,
    NotificationPayload,
    NotificationResult,
)


class TestSlackAdapterInit:
    """Tests for SlackAdapter initialization."""

    def test_init_with_webhook_url(self) -> None:
        """Should initialize with webhook URL."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX/YYY/ZZZ"
        )

        assert adapter.url == "https://hooks.slack.com/services/XXX/YYY/ZZZ"
        assert adapter._username == "Rice-Factor"
        assert adapter._icon_emoji == ":rice:"

    def test_init_with_channel(self) -> None:
        """Should accept channel override."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX",
            channel="#alerts",
        )

        assert adapter._channel == "#alerts"

    def test_init_with_custom_username(self) -> None:
        """Should accept custom username."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX",
            username="MyBot",
        )

        assert adapter._username == "MyBot"

    def test_init_with_custom_icon(self) -> None:
        """Should accept custom icon emoji."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX",
            icon_emoji=":robot_face:",
        )

        assert adapter._icon_emoji == ":robot_face:"

    def test_init_include_metadata_default(self) -> None:
        """Should include metadata by default."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX"
        )

        assert adapter._include_metadata is True


class TestSlackAdapterEmojiMapping:
    """Tests for Slack emoji mappings."""

    def test_all_events_have_emoji(self) -> None:
        """All notification events should have emoji mapping."""
        for event in NotificationEvent:
            assert event in EVENT_EMOJIS

    def test_emoji_format(self) -> None:
        """Emojis should use Slack format :emoji_name:."""
        for emoji in EVENT_EMOJIS.values():
            assert emoji.startswith(":")
            assert emoji.endswith(":")


class TestSlackAdapterColorMapping:
    """Tests for Slack color mappings."""

    def test_severity_colors(self) -> None:
        """Severity levels should map to hex colors."""
        assert SEVERITY_COLORS["info"].startswith("#")
        assert SEVERITY_COLORS["warning"].startswith("#")
        assert SEVERITY_COLORS["error"].startswith("#")
        assert SEVERITY_COLORS["success"].startswith("#")


class TestSlackAdapterFormatPayload:
    """Tests for SlackAdapter._format_payload method."""

    @pytest.fixture
    def adapter(self) -> SlackAdapter:
        """Create test adapter."""
        return SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX"
        )

    def test_format_basic_payload(self, adapter: SlackAdapter) -> None:
        """Should format basic payload with blocks."""
        payload = NotificationPayload(
            event=NotificationEvent.ARTIFACT_APPROVED,
            timestamp=datetime.now(UTC),
            title="Artifact Approved",
            message="ProjectPlan was approved",
        )

        result = adapter._format_payload(payload)

        assert "blocks" in result
        assert "attachments" in result
        assert result["username"] == "Rice-Factor"
        assert result["icon_emoji"] == ":rice:"

    def test_format_includes_header_block(self, adapter: SlackAdapter) -> None:
        """Should include header block with emoji."""
        payload = NotificationPayload(
            event=NotificationEvent.BUILD_FAILED,
            timestamp=datetime.now(UTC),
            title="Build Failed",
            message="Build failed with errors",
        )

        result = adapter._format_payload(payload)

        header_block = result["blocks"][0]
        assert header_block["type"] == "header"
        assert ":boom:" in header_block["text"]["text"]
        assert "Build Failed" in header_block["text"]["text"]

    def test_format_includes_message_section(self, adapter: SlackAdapter) -> None:
        """Should include message section."""
        payload = NotificationPayload(
            event=NotificationEvent.BUILD_STARTED,
            timestamp=datetime.now(UTC),
            title="Build Started",
            message="Starting the build process",
        )

        result = adapter._format_payload(payload)

        section_block = result["blocks"][1]
        assert section_block["type"] == "section"
        assert section_block["text"]["text"] == "Starting the build process"

    def test_format_includes_metadata_fields(self, adapter: SlackAdapter) -> None:
        """Should include metadata as fields."""
        payload = NotificationPayload(
            event=NotificationEvent.COST_THRESHOLD,
            timestamp=datetime.now(UTC),
            title="Cost Threshold",
            message="Cost threshold reached",
            metadata={"current_cost": "$50.00", "threshold": "$45.00"},
        )

        result = adapter._format_payload(payload)

        # Find section with fields
        fields_section = None
        for block in result["blocks"]:
            if block.get("type") == "section" and "fields" in block:
                fields_section = block
                break

        assert fields_section is not None
        assert len(fields_section["fields"]) == 2

    def test_format_limits_metadata_fields(self, adapter: SlackAdapter) -> None:
        """Should limit metadata to 10 fields."""
        metadata = {f"field_{i}": f"value_{i}" for i in range(15)}
        payload = NotificationPayload(
            event=NotificationEvent.ERROR,
            timestamp=datetime.now(UTC),
            title="Error",
            message="Error with lots of metadata",
            metadata=metadata,
        )

        result = adapter._format_payload(payload)

        # Find section with fields
        fields_section = None
        for block in result["blocks"]:
            if block.get("type") == "section" and "fields" in block:
                fields_section = block
                break

        assert fields_section is not None
        assert len(fields_section["fields"]) <= 10

    def test_format_includes_context(self, adapter: SlackAdapter) -> None:
        """Should include context block with timestamp."""
        payload = NotificationPayload(
            event=NotificationEvent.TEST_PASSED,
            timestamp=datetime.now(UTC),
            title="Tests Passed",
            message="All tests passed",
            source="test-runner",
        )

        result = adapter._format_payload(payload)

        context_block = result["blocks"][-1]
        assert context_block["type"] == "context"
        assert "test-runner" in context_block["elements"][0]["text"]

    def test_format_includes_color_attachment(self, adapter: SlackAdapter) -> None:
        """Should include colored attachment."""
        payload = NotificationPayload(
            event=NotificationEvent.TEST_FAILED,
            timestamp=datetime.now(UTC),
            title="Tests Failed",
            message="Some tests failed",
            severity="warning",
        )

        result = adapter._format_payload(payload)

        assert len(result["attachments"]) == 1
        assert result["attachments"][0]["color"] == SEVERITY_COLORS["warning"]

    def test_format_includes_channel_when_set(self) -> None:
        """Should include channel when set."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX",
            channel="#my-channel",
        )
        payload = NotificationPayload(
            event=NotificationEvent.BUILD_COMPLETED,
            timestamp=datetime.now(UTC),
            title="Build Complete",
            message="Build finished",
        )

        result = adapter._format_payload(payload)

        assert result["channel"] == "#my-channel"

    def test_format_excludes_metadata_when_disabled(self) -> None:
        """Should exclude metadata when include_metadata is False."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX",
            include_metadata=False,
        )
        payload = NotificationPayload(
            event=NotificationEvent.ARTIFACT_CREATED,
            timestamp=datetime.now(UTC),
            title="Created",
            message="Artifact created",
            metadata={"artifact_id": "123"},
        )

        result = adapter._format_payload(payload)

        # Check no section has fields
        for block in result["blocks"]:
            if block.get("type") == "section":
                assert "fields" not in block


class TestSlackAdapterSend:
    """Tests for SlackAdapter send method."""

    def test_send_success_with_mocked_do_send(self) -> None:
        """Should send successfully when _do_send succeeds."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX"
        )
        payload = NotificationPayload(
            event=NotificationEvent.BUILD_COMPLETED,
            timestamp=datetime.now(UTC),
            title="Complete",
            message="Build completed",
        )

        # Mock _do_send directly to avoid HTTP library import issues
        with patch.object(adapter, "_do_send") as mock_do_send:
            mock_do_send.return_value = NotificationResult(
                success=True,
                status_code=200,
                response="ok",
            )
            result = adapter.send(payload)

        assert result.success is True
        mock_do_send.assert_called_once()

    def test_send_formats_slack_message(self) -> None:
        """Should format message using Slack Block Kit."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX"
        )
        payload = NotificationPayload(
            event=NotificationEvent.ERROR,
            timestamp=datetime.now(UTC),
            title="Error",
            message="Error occurred",
        )

        # Verify the message is formatted correctly
        formatted = adapter._format_payload(payload)
        assert "blocks" in formatted
        assert "attachments" in formatted

    def test_send_handles_failure(self) -> None:
        """Should handle send failure."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX",
            retry_count=1,
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
                status_code=400,
                response="invalid_payload",
            )
            result = adapter.send(payload)

        assert result.success is False


class TestSlackAdapterToDict:
    """Tests for SlackAdapter.to_dict method."""

    def test_to_dict(self) -> None:
        """Should export configuration as dict."""
        adapter = SlackAdapter(
            webhook_url="https://hooks.slack.com/services/XXX",
            channel="#alerts",
            username="TestBot",
            icon_emoji=":test:",
            include_metadata=False,
        )

        result = adapter.to_dict()

        assert result["type"] == "slack"
        assert result["channel"] == "#alerts"
        assert result["username"] == "TestBot"
        assert result["icon_emoji"] == ":test:"
        assert result["include_metadata"] is False
