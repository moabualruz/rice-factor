"""Microsoft Teams notification adapter.

This module provides the TeamsAdapter for sending notifications
to Microsoft Teams channels via incoming webhooks.
"""

from __future__ import annotations

from typing import Any

from rice_factor.adapters.notifications.webhook_adapter import (
    NotificationEvent,
    NotificationPayload,
    NotificationResult,
    WebhookAdapter,
)


# Severity to Teams theme color mapping
SEVERITY_COLORS = {
    "info": "0076D7",  # Blue
    "warning": "FFC107",  # Yellow
    "error": "DC3545",  # Red
    "success": "28A745",  # Green
}

# Event to emoji mapping (Teams uses regular emoji)
EVENT_EMOJIS = {
    NotificationEvent.ARTIFACT_CREATED: "📄",
    NotificationEvent.ARTIFACT_APPROVED: "✅",
    NotificationEvent.ARTIFACT_REJECTED: "❌",
    NotificationEvent.ARTIFACT_LOCKED: "🔒",
    NotificationEvent.BUILD_STARTED: "🔨",
    NotificationEvent.BUILD_COMPLETED: "🚀",
    NotificationEvent.BUILD_FAILED: "💥",
    NotificationEvent.TEST_PASSED: "✔️",
    NotificationEvent.TEST_FAILED: "⚠️",
    NotificationEvent.COST_THRESHOLD: "💸",
    NotificationEvent.RATE_LIMIT: "⏳",
    NotificationEvent.ERROR: "🚨",
}


class TeamsAdapter(WebhookAdapter):
    """Microsoft Teams notification adapter.

    Sends notifications to Teams channels using Adaptive Cards
    for rich formatting.

    Example:
        >>> adapter = TeamsAdapter(
        ...     webhook_url="https://outlook.office.com/webhook/XXX"
        ... )
        >>> adapter.send(payload)
    """

    def __init__(
        self,
        webhook_url: str,
        include_metadata: bool = True,
        use_adaptive_cards: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize the Teams adapter.

        Args:
            webhook_url: Teams incoming webhook URL.
            include_metadata: Whether to include metadata in cards.
            use_adaptive_cards: Use Adaptive Cards (newer format).
            **kwargs: Additional WebhookAdapter arguments.
        """
        super().__init__(url=webhook_url, **kwargs)
        self._include_metadata = include_metadata
        self._use_adaptive_cards = use_adaptive_cards

    def _format_adaptive_card(self, payload: NotificationPayload) -> dict[str, Any]:
        """Format payload as Teams Adaptive Card.

        Args:
            payload: Notification payload.

        Returns:
            Adaptive Card message format.
        """
        emoji = EVENT_EMOJIS.get(payload.event, "🔔")
        color = SEVERITY_COLORS.get(payload.severity, "808080")

        body = [
            {
                "type": "TextBlock",
                "size": "Large",
                "weight": "Bolder",
                "text": f"{emoji} {payload.title}",
            },
            {
                "type": "TextBlock",
                "text": payload.message,
                "wrap": True,
            },
        ]

        # Add metadata as fact set
        if self._include_metadata and payload.metadata:
            facts = [
                {"title": key, "value": str(value)}
                for key, value in list(payload.metadata.items())[:10]
            ]
            if facts:
                body.append({
                    "type": "FactSet",
                    "facts": facts,
                })

        # Add footer with event info
        body.append({
            "type": "TextBlock",
            "text": f"Event: {payload.event.value} | Source: {payload.source}",
            "size": "Small",
            "isSubtle": True,
        })

        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "msteams": {
                            "width": "Full",
                        },
                        "body": body,
                    },
                }
            ],
        }

    def _format_message_card(self, payload: NotificationPayload) -> dict[str, Any]:
        """Format payload as Teams MessageCard (legacy format).

        Args:
            payload: Notification payload.

        Returns:
            MessageCard format.
        """
        emoji = EVENT_EMOJIS.get(payload.event, "🔔")
        color = SEVERITY_COLORS.get(payload.severity, "808080")

        sections = [
            {
                "activityTitle": f"{emoji} {payload.title}",
                "text": payload.message,
            }
        ]

        # Add metadata as facts
        if self._include_metadata and payload.metadata:
            facts = [
                {"name": key, "value": str(value)}
                for key, value in list(payload.metadata.items())[:10]
            ]
            if facts:
                sections[0]["facts"] = facts

        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": payload.title,
            "sections": sections,
        }

    def _do_send(self, payload: NotificationPayload) -> NotificationResult:
        """Send notification to Teams.

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

                return self._send_teams_with_requests(payload)
            except ImportError:
                return NotificationResult(
                    success=False,
                    response="Neither httpx nor requests is installed",
                )

        if self._use_adaptive_cards:
            teams_message = self._format_adaptive_card(payload)
        else:
            teams_message = self._format_message_card(payload)

        try:
            with httpx.Client(
                timeout=self._timeout,
                verify=self._verify_ssl,
            ) as client:
                response = client.post(
                    self._url,
                    json=teams_message,
                    headers={"Content-Type": "application/json"},
                )

                # Teams returns "1" on success for webhooks
                return NotificationResult(
                    success=response.is_success,
                    status_code=response.status_code,
                    response=response.text[:500],
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                response=str(e),
            )

    def _send_teams_with_requests(
        self, payload: NotificationPayload
    ) -> NotificationResult:
        """Send using requests library.

        Args:
            payload: Notification payload.

        Returns:
            NotificationResult with response details.
        """
        import requests

        if self._use_adaptive_cards:
            teams_message = self._format_adaptive_card(payload)
        else:
            teams_message = self._format_message_card(payload)

        try:
            response = requests.post(
                self._url,
                json=teams_message,
                headers={"Content-Type": "application/json"},
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

    def to_dict(self) -> dict[str, Any]:
        """Export adapter configuration.

        Returns:
            Dictionary with configuration.
        """
        config = super().to_dict()
        config.update({
            "type": "teams",
            "include_metadata": self._include_metadata,
            "use_adaptive_cards": self._use_adaptive_cards,
        })
        return config
