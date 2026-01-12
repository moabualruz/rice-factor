"""Slack notification adapter.

This module provides the SlackAdapter for sending notifications
to Slack channels via incoming webhooks or the Slack API.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from rice_factor.adapters.notifications.webhook_adapter import (
    NotificationEvent,
    NotificationPayload,
    NotificationResult,
    WebhookAdapter,
)


# Severity to Slack color mapping
SEVERITY_COLORS = {
    "info": "#36a64f",  # Green
    "warning": "#ffcc00",  # Yellow
    "error": "#ff0000",  # Red
    "success": "#36a64f",  # Green
}

# Event to emoji mapping
EVENT_EMOJIS = {
    NotificationEvent.ARTIFACT_CREATED: ":page_facing_up:",
    NotificationEvent.ARTIFACT_APPROVED: ":white_check_mark:",
    NotificationEvent.ARTIFACT_REJECTED: ":x:",
    NotificationEvent.ARTIFACT_LOCKED: ":lock:",
    NotificationEvent.BUILD_STARTED: ":hammer_and_wrench:",
    NotificationEvent.BUILD_COMPLETED: ":rocket:",
    NotificationEvent.BUILD_FAILED: ":boom:",
    NotificationEvent.TEST_PASSED: ":heavy_check_mark:",
    NotificationEvent.TEST_FAILED: ":warning:",
    NotificationEvent.COST_THRESHOLD: ":money_with_wings:",
    NotificationEvent.RATE_LIMIT: ":hourglass:",
    NotificationEvent.ERROR: ":rotating_light:",
}


class SlackAdapter(WebhookAdapter):
    """Slack notification adapter.

    Sends notifications to Slack channels using Slack's Block Kit
    format for rich formatting.

    Example:
        >>> adapter = SlackAdapter(
        ...     webhook_url="https://hooks.slack.com/services/XXX/YYY/ZZZ"
        ... )
        >>> adapter.send(payload)
    """

    def __init__(
        self,
        webhook_url: str,
        channel: str | None = None,
        username: str = "Rice-Factor",
        icon_emoji: str = ":rice:",
        include_metadata: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize the Slack adapter.

        Args:
            webhook_url: Slack incoming webhook URL.
            channel: Override channel (optional).
            username: Bot username to display.
            icon_emoji: Emoji icon for the bot.
            include_metadata: Whether to include metadata in attachments.
            **kwargs: Additional WebhookAdapter arguments.
        """
        super().__init__(url=webhook_url, **kwargs)
        self._channel = channel
        self._username = username
        self._icon_emoji = icon_emoji
        self._include_metadata = include_metadata

    def _format_payload(self, payload: NotificationPayload) -> dict[str, Any]:
        """Format payload for Slack's Block Kit.

        Args:
            payload: Notification payload.

        Returns:
            Slack-formatted message.
        """
        emoji = EVENT_EMOJIS.get(payload.event, ":bell:")
        color = SEVERITY_COLORS.get(payload.severity, "#808080")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {payload.title}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": payload.message,
                },
            },
        ]

        # Add metadata fields if enabled
        if self._include_metadata and payload.metadata:
            fields = []
            for key, value in list(payload.metadata.items())[:10]:  # Limit to 10 fields
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{value}",
                })

            if fields:
                blocks.append({
                    "type": "section",
                    "fields": fields[:10],  # Slack limit
                })

        # Add timestamp context
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Event: `{payload.event.value}` | Source: {payload.source} | "
                    f"<!date^{int(payload.timestamp.timestamp())}^{{date_short_pretty}} at {{time}}|{payload.timestamp.isoformat()}>",
                },
            ],
        })

        message: dict[str, Any] = {
            "username": self._username,
            "icon_emoji": self._icon_emoji,
            "blocks": blocks,
            "attachments": [
                {
                    "color": color,
                    "fallback": f"{payload.title}: {payload.message}",
                }
            ],
        }

        if self._channel:
            message["channel"] = self._channel

        return message

    def _do_send(self, payload: NotificationPayload) -> NotificationResult:
        """Send notification to Slack.

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

                return self._send_slack_with_requests(payload)
            except ImportError:
                return NotificationResult(
                    success=False,
                    response="Neither httpx nor requests is installed",
                )

        slack_message = self._format_payload(payload)

        try:
            with httpx.Client(
                timeout=self._timeout,
                verify=self._verify_ssl,
            ) as client:
                response = client.post(
                    self._url,
                    json=slack_message,
                    headers={"Content-Type": "application/json"},
                )

                # Slack returns "ok" on success
                return NotificationResult(
                    success=response.is_success and response.text == "ok",
                    status_code=response.status_code,
                    response=response.text[:500],
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                response=str(e),
            )

    def _send_slack_with_requests(
        self, payload: NotificationPayload
    ) -> NotificationResult:
        """Send using requests library.

        Args:
            payload: Notification payload.

        Returns:
            NotificationResult with response details.
        """
        import requests

        slack_message = self._format_payload(payload)

        try:
            response = requests.post(
                self._url,
                json=slack_message,
                headers={"Content-Type": "application/json"},
                timeout=self._timeout,
                verify=self._verify_ssl,
            )

            return NotificationResult(
                success=response.ok and response.text == "ok",
                status_code=response.status_code,
                response=response.text[:500],
            )
        except Exception as e:
            return NotificationResult(
                success=False,
                response=str(e),
            )

    def to_dict(self) -> dict[str, Any]:
        """Export adapter configuration.

        Returns:
            Dictionary with configuration.
        """
        config = super().to_dict()
        config.update({
            "type": "slack",
            "channel": self._channel,
            "username": self._username,
            "icon_emoji": self._icon_emoji,
            "include_metadata": self._include_metadata,
        })
        return config
