"""Unit tests for TeamsAdapter."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.notifications.teams_adapter import (
    EVENT_EMOJIS,
    SEVERITY_COLORS,
    TeamsAdapter,
)
from rice_factor.adapters.notifications.webhook_adapter import (
    NotificationEvent,
    NotificationPayload,
    NotificationResult,
)


class TestTeamsAdapterInit:
    """Tests for TeamsAdapter initialization."""

    def test_init_with_webhook_url(self) -> None:
        """Should initialize with webhook URL."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX"
        )

        assert adapter.url == "https://outlook.office.com/webhook/XXX"

    def test_init_include_metadata_default(self) -> None:
        """Should include metadata by default."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX"
        )

        assert adapter._include_metadata is True

    def test_init_use_adaptive_cards_default(self) -> None:
        """Should use Adaptive Cards by default."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX"
        )

        assert adapter._use_adaptive_cards is True

    def test_init_with_legacy_format(self) -> None:
        """Should accept legacy MessageCard format option."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX",
            use_adaptive_cards=False,
        )

        assert adapter._use_adaptive_cards is False


class TestTeamsAdapterEmojiMapping:
    """Tests for Teams emoji mappings."""

    def test_all_events_have_emoji(self) -> None:
        """All notification events should have emoji mapping."""
        for event in NotificationEvent:
            assert event in EVENT_EMOJIS

    def test_emoji_format(self) -> None:
        """Emojis should use Unicode format (not Slack format)."""
        for emoji in EVENT_EMOJIS.values():
            # Teams uses Unicode emoji, not :emoji: format
            assert not emoji.startswith(":")


class TestTeamsAdapterColorMapping:
    """Tests for Teams color mappings."""

    def test_severity_colors(self) -> None:
        """Severity levels should map to hex colors without #."""
        for color in SEVERITY_COLORS.values():
            # Teams uses hex without # prefix
            assert not color.startswith("#")
            assert len(color) == 6


class TestTeamsAdapterFormatAdaptiveCard:
    """Tests for TeamsAdapter._format_adaptive_card method."""

    @pytest.fixture
    def adapter(self) -> TeamsAdapter:
        """Create test adapter."""
        return TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX"
        )

    def test_format_basic_adaptive_card(self, adapter: TeamsAdapter) -> None:
        """Should format basic Adaptive Card."""
        payload = NotificationPayload(
            event=NotificationEvent.ARTIFACT_APPROVED,
            timestamp=datetime.now(UTC),
            title="Artifact Approved",
            message="ProjectPlan was approved",
        )

        result = adapter._format_adaptive_card(payload)

        assert result["type"] == "message"
        assert len(result["attachments"]) == 1
        attachment = result["attachments"][0]
        assert attachment["contentType"] == "application/vnd.microsoft.card.adaptive"

    def test_format_adaptive_card_version(self, adapter: TeamsAdapter) -> None:
        """Should use correct Adaptive Card version."""
        payload = NotificationPayload(
            event=NotificationEvent.BUILD_STARTED,
            timestamp=datetime.now(UTC),
            title="Build Started",
            message="Starting build",
        )

        result = adapter._format_adaptive_card(payload)

        content = result["attachments"][0]["content"]
        assert content["type"] == "AdaptiveCard"
        assert content["version"] == "1.4"

    def test_format_adaptive_card_title(self, adapter: TeamsAdapter) -> None:
        """Should include title with emoji."""
        payload = NotificationPayload(
            event=NotificationEvent.BUILD_FAILED,
            timestamp=datetime.now(UTC),
            title="Build Failed",
            message="Build failed with errors",
        )

        result = adapter._format_adaptive_card(payload)

        content = result["attachments"][0]["content"]
        title_block = content["body"][0]
        assert title_block["type"] == "TextBlock"
        assert title_block["weight"] == "Bolder"
        assert "💥" in title_block["text"]
        assert "Build Failed" in title_block["text"]

    def test_format_adaptive_card_message(self, adapter: TeamsAdapter) -> None:
        """Should include message body."""
        payload = NotificationPayload(
            event=NotificationEvent.TEST_PASSED,
            timestamp=datetime.now(UTC),
            title="Tests Passed",
            message="All 100 tests passed successfully",
        )

        result = adapter._format_adaptive_card(payload)

        content = result["attachments"][0]["content"]
        message_block = content["body"][1]
        assert message_block["type"] == "TextBlock"
        assert message_block["text"] == "All 100 tests passed successfully"
        assert message_block["wrap"] is True

    def test_format_adaptive_card_with_metadata(self, adapter: TeamsAdapter) -> None:
        """Should include metadata as FactSet."""
        payload = NotificationPayload(
            event=NotificationEvent.COST_THRESHOLD,
            timestamp=datetime.now(UTC),
            title="Cost Alert",
            message="Cost threshold exceeded",
            metadata={"current": "$50", "limit": "$45"},
        )

        result = adapter._format_adaptive_card(payload)

        content = result["attachments"][0]["content"]
        # Find FactSet in body
        fact_set = None
        for block in content["body"]:
            if block.get("type") == "FactSet":
                fact_set = block
                break

        assert fact_set is not None
        assert len(fact_set["facts"]) == 2

    def test_format_adaptive_card_limits_metadata(self, adapter: TeamsAdapter) -> None:
        """Should limit metadata to 10 facts."""
        metadata = {f"field_{i}": f"value_{i}" for i in range(15)}
        payload = NotificationPayload(
            event=NotificationEvent.ERROR,
            timestamp=datetime.now(UTC),
            title="Error",
            message="Error with metadata",
            metadata=metadata,
        )

        result = adapter._format_adaptive_card(payload)

        content = result["attachments"][0]["content"]
        fact_set = None
        for block in content["body"]:
            if block.get("type") == "FactSet":
                fact_set = block
                break

        assert fact_set is not None
        assert len(fact_set["facts"]) <= 10

    def test_format_adaptive_card_footer(self, adapter: TeamsAdapter) -> None:
        """Should include footer with event info."""
        payload = NotificationPayload(
            event=NotificationEvent.ARTIFACT_LOCKED,
            timestamp=datetime.now(UTC),
            title="Locked",
            message="Artifact locked",
            source="test-system",
        )

        result = adapter._format_adaptive_card(payload)

        content = result["attachments"][0]["content"]
        footer_block = content["body"][-1]
        assert footer_block["size"] == "Small"
        assert footer_block["isSubtle"] is True
        assert "artifact.locked" in footer_block["text"]
        assert "test-system" in footer_block["text"]

    def test_format_adaptive_card_excludes_metadata_when_disabled(self) -> None:
        """Should exclude metadata when disabled."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX",
            include_metadata=False,
        )
        payload = NotificationPayload(
            event=NotificationEvent.ARTIFACT_CREATED,
            timestamp=datetime.now(UTC),
            title="Created",
            message="Created",
            metadata={"id": "123"},
        )

        result = adapter._format_adaptive_card(payload)

        content = result["attachments"][0]["content"]
        for block in content["body"]:
            assert block.get("type") != "FactSet"


class TestTeamsAdapterFormatMessageCard:
    """Tests for TeamsAdapter._format_message_card method (legacy)."""

    @pytest.fixture
    def adapter(self) -> TeamsAdapter:
        """Create test adapter with legacy format."""
        return TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX",
            use_adaptive_cards=False,
        )

    def test_format_message_card_type(self, adapter: TeamsAdapter) -> None:
        """Should format as MessageCard."""
        payload = NotificationPayload(
            event=NotificationEvent.BUILD_COMPLETED,
            timestamp=datetime.now(UTC),
            title="Complete",
            message="Build completed",
        )

        result = adapter._format_message_card(payload)

        assert result["@type"] == "MessageCard"
        assert result["@context"] == "http://schema.org/extensions"

    def test_format_message_card_color(self, adapter: TeamsAdapter) -> None:
        """Should include theme color based on severity."""
        payload = NotificationPayload(
            event=NotificationEvent.TEST_FAILED,
            timestamp=datetime.now(UTC),
            title="Failed",
            message="Tests failed",
            severity="error",
        )

        result = adapter._format_message_card(payload)

        assert result["themeColor"] == SEVERITY_COLORS["error"]

    def test_format_message_card_sections(self, adapter: TeamsAdapter) -> None:
        """Should include sections with title and text."""
        payload = NotificationPayload(
            event=NotificationEvent.RATE_LIMIT,
            timestamp=datetime.now(UTC),
            title="Rate Limited",
            message="Provider rate limit reached",
        )

        result = adapter._format_message_card(payload)

        assert len(result["sections"]) >= 1
        section = result["sections"][0]
        assert "⏳" in section["activityTitle"]
        assert "Rate Limited" in section["activityTitle"]
        assert section["text"] == "Provider rate limit reached"

    def test_format_message_card_with_facts(self, adapter: TeamsAdapter) -> None:
        """Should include metadata as facts."""
        payload = NotificationPayload(
            event=NotificationEvent.ERROR,
            timestamp=datetime.now(UTC),
            title="Error",
            message="Error occurred",
            metadata={"error_code": "E123", "module": "builder"},
        )

        result = adapter._format_message_card(payload)

        section = result["sections"][0]
        assert "facts" in section
        assert len(section["facts"]) == 2


class TestTeamsAdapterSend:
    """Tests for TeamsAdapter send method."""

    def test_send_success_with_mocked_do_send(self) -> None:
        """Should send successfully when _do_send succeeds."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX",
            use_adaptive_cards=True,
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
                response="1",
            )
            result = adapter.send(payload)

        assert result.success is True
        mock_do_send.assert_called_once()

    def test_send_formats_adaptive_card(self) -> None:
        """Should format message as Adaptive Card."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX",
            use_adaptive_cards=True,
        )
        payload = NotificationPayload(
            event=NotificationEvent.BUILD_COMPLETED,
            timestamp=datetime.now(UTC),
            title="Complete",
            message="Build completed",
        )

        # Verify the message is formatted correctly
        formatted = adapter._format_adaptive_card(payload)
        assert formatted["type"] == "message"
        assert "attachments" in formatted

    def test_send_formats_message_card(self) -> None:
        """Should format message as MessageCard when legacy mode."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX",
            use_adaptive_cards=False,
        )
        payload = NotificationPayload(
            event=NotificationEvent.ERROR,
            timestamp=datetime.now(UTC),
            title="Error",
            message="Error occurred",
        )

        # Verify the message is formatted correctly
        formatted = adapter._format_message_card(payload)
        assert formatted["@type"] == "MessageCard"

    def test_send_handles_failure(self) -> None:
        """Should handle send failure."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX",
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
                response="Bad request",
            )
            result = adapter.send(payload)

        assert result.success is False


class TestTeamsAdapterToDict:
    """Tests for TeamsAdapter.to_dict method."""

    def test_to_dict(self) -> None:
        """Should export configuration as dict."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX",
            include_metadata=False,
            use_adaptive_cards=False,
        )

        result = adapter.to_dict()

        assert result["type"] == "teams"
        assert result["include_metadata"] is False
        assert result["use_adaptive_cards"] is False

    def test_to_dict_inherits_base(self) -> None:
        """Should include base adapter config."""
        adapter = TeamsAdapter(
            webhook_url="https://outlook.office.com/webhook/XXX",
            timeout=45.0,
        )

        result = adapter.to_dict()

        assert result["timeout"] == 45.0
        assert "enabled" in result
