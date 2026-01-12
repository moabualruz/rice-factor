"""Status bar widget for TUI.

This module provides a status bar widget for displaying current
project phase and other status information.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, Static


class StatusBar(Static):
    """Status bar showing current project status.

    Displays the current phase and other relevant information
    at the bottom of the TUI.
    """

    # Rice-Factor brand colors
    DEFAULT_CSS = """
    StatusBar {
        width: 100%;
        height: 1;
        background: #00a020;
        color: white;
    }

    StatusBar Horizontal {
        width: 100%;
        height: 100%;
    }

    StatusBar .status-section {
        width: auto;
        padding: 0 2;
    }

    StatusBar .phase-label {
        text-style: bold;
    }

    StatusBar .separator {
        width: 1;
        color: #80c080;
    }
    """

    def __init__(self) -> None:
        """Initialize the status bar."""
        super().__init__()
        self._phase = "unknown"
        self._message = ""

    def compose(self) -> ComposeResult:
        """Compose the status bar.

        Yields:
            UI components.
        """
        with Horizontal():
            yield Label(f"Phase: {self._phase}", classes="status-section phase-label", id="phase-label")
            yield Label("|", classes="separator")
            yield Label(
                self._message or "Press ? for help",
                classes="status-section message",
                id="message-label",
            )

    def update_phase(self, phase: str) -> None:
        """Update the displayed phase.

        Args:
            phase: New phase value to display.
        """
        self._phase = phase
        try:
            self.query_one("#phase-label", Label).update(f"Phase: {phase}")
        except Exception:
            # Widget might not be mounted yet
            pass

    def update_message(self, message: str) -> None:
        """Update the status message.

        Args:
            message: New message to display.
        """
        self._message = message
        try:
            self.query_one("#message-label", Label).update(message or "Press ? for help")
        except Exception:
            # Widget might not be mounted yet
            pass
