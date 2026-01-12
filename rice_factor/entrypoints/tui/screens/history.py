"""History screen for TUI.

This module provides an audit trail viewer screen for viewing and
filtering audit log entries with export functionality.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, ListItem, ListView, Static


class AuditLogItem(ListItem):
    """A list item representing an audit log entry.

    Attributes:
        entry_id: ID of the entry.
        timestamp: When the action occurred.
        action: Type of action performed.
        summary: Brief summary of the action.
    """

    def __init__(
        self,
        entry_id: str,
        timestamp: str,
        action: str,
        summary: str,
    ) -> None:
        """Initialize an audit log list item.

        Args:
            entry_id: ID of the entry.
            timestamp: When the action occurred.
            action: Type of action performed.
            summary: Brief summary of the action.
        """
        super().__init__()
        self._entry_id = entry_id
        self._timestamp = timestamp
        self._action = action
        self._summary = summary

    @property
    def entry_id(self) -> str:
        """Get the entry ID."""
        return self._entry_id

    @property
    def timestamp(self) -> str:
        """Get the timestamp."""
        return self._timestamp

    @property
    def action(self) -> str:
        """Get the action."""
        return self._action

    @property
    def summary(self) -> str:
        """Get the summary."""
        return self._summary

    def compose(self) -> ComposeResult:
        """Compose the list item display.

        Yields:
            UI components.
        """
        # Format timestamp to be shorter
        ts_display = self._timestamp[:19] if len(self._timestamp) > 19 else self._timestamp
        yield Label(f"[{ts_display}] {self._action}: {self._summary[:40]}...")


class AuditDetailPanel(Static):
    """Panel showing audit entry details.

    Displays the full details of a selected audit log entry.
    """

    DEFAULT_CSS = """
    AuditDetailPanel {
        width: 100%;
        height: 100%;
        border: solid #009e20;
        padding: 1;
        overflow-y: auto;
        background: #0a1a0a;
    }

    AuditDetailPanel .detail-header {
        text-style: bold;
        margin-bottom: 1;
        color: #00a020;
    }

    AuditDetailPanel .field-label {
        color: #808080;
    }

    AuditDetailPanel .field-value {
        margin-left: 2;
        color: #00c030;
        margin-bottom: 1;
    }

    AuditDetailPanel .json-content {
        color: #c0c0c0;
        margin-top: 1;
    }

    AuditDetailPanel .no-entry {
        color: #808080;
        text-align: center;
        margin-top: 2;
    }
    """

    def __init__(self) -> None:
        """Initialize the audit detail panel."""
        super().__init__()
        self._entry_data: dict[str, Any] | None = None

    def set_entry(self, entry_data: dict[str, Any]) -> None:
        """Set the entry to display.

        Args:
            entry_data: Audit entry data dictionary.
        """
        self._entry_data = entry_data
        self.refresh_display()

    def clear(self) -> None:
        """Clear the displayed entry."""
        self._entry_data = None
        self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the display with current entry data."""
        self.remove_children()
        self.mount_all(list(self.compose()))

    def compose(self) -> ComposeResult:
        """Compose the detail panel.

        Yields:
            UI components.
        """
        if self._entry_data is None:
            yield Label("Select an entry to view details", classes="no-entry")
            return

        yield Label("Audit Entry Details", classes="detail-header")

        # Display entry fields
        fields = [
            ("Timestamp", str(self._entry_data.get("timestamp", ""))),
            ("Action", str(self._entry_data.get("action", ""))),
            ("Actor", str(self._entry_data.get("actor", "unknown"))),
            ("Target", str(self._entry_data.get("target", ""))),
            ("Status", str(self._entry_data.get("status", ""))),
        ]

        for label, value in fields:
            yield Label(f"{label}:", classes="field-label")
            yield Label(value, classes="field-value")

        # Show additional data
        details = self._entry_data.get("details", {})
        if details:
            yield Label("Additional Details:", classes="field-label")
            details_str = json.dumps(details, indent=2)
            if len(details_str) > 500:
                details_str = details_str[:500] + "\n... (truncated)"
            yield Label(details_str, classes="json-content")

        # Show hash if present (for audit chain integrity)
        entry_hash = self._entry_data.get("hash", "")
        if entry_hash:
            yield Label("Entry Hash:", classes="field-label")
            yield Label(entry_hash[:32] + "...", classes="field-value")


class HistoryScreen(Static):
    """History/Audit trail viewer screen.

    Shows audit log entries with filtering and export capabilities.

    Attributes:
        project_root: Root directory of the project.
    """

    DEFAULT_CSS = """
    HistoryScreen {
        width: 100%;
        height: 100%;
        background: #0a1a0a;
    }

    #history-header {
        height: auto;
        padding: 1;
        text-align: center;
        background: #009e20;
        color: white;
    }

    #filter-bar {
        height: auto;
        padding: 1;
        background: #102010;
    }

    #filter-input {
        width: 50%;
    }

    #history-content {
        width: 100%;
        height: 1fr;
    }

    #history-list-panel {
        width: 50%;
        height: 100%;
        border-right: solid #00a020;
    }

    #history-detail-panel {
        width: 50%;
        height: 100%;
    }

    #history-list {
        height: 100%;
        background: #0a1a0a;
    }

    .list-header {
        padding: 1;
        background: #102010;
        text-style: bold;
        color: #00a020;
    }

    .no-entries {
        padding: 2;
        text-align: center;
        color: #808080;
    }

    #export-bar {
        height: auto;
        padding: 1;
        background: #102010;
        border-top: solid #009e20;
    }

    .stats-label {
        color: #808080;
        margin-right: 2;
    }
    """

    def __init__(
        self,
        project_root: Path | None = None,
    ) -> None:
        """Initialize the history screen.

        Args:
            project_root: Root directory of the project.
        """
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._entries: list[dict[str, Any]] = []
        self._filtered_entries: list[dict[str, Any]] = []
        self._filter_text: str = ""

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    def compose(self) -> ComposeResult:
        """Compose the history viewer.

        Yields:
            UI components.
        """
        yield Static("Audit History", id="history-header")

        # Filter bar
        with Horizontal(id="filter-bar"):
            yield Label("Filter: ", classes="stats-label")
            yield Input(
                placeholder="Search actions, targets...",
                id="filter-input",
            )
            yield Button("Clear", id="clear-filter-btn")

        with Horizontal(id="history-content"):
            with Vertical(id="history-list-panel"):
                count = len(self._filtered_entries)
                yield Label(f"Entries ({count})", classes="list-header")
                yield self._create_history_list()

            with Vertical(id="history-detail-panel"):
                yield AuditDetailPanel()

        # Export bar
        with Horizontal(id="export-bar"):
            yield Label(f"Total: {len(self._entries)} entries", classes="stats-label")
            yield Button("Export JSON", id="export-json-btn")
            yield Button("Export CSV", id="export-csv-btn")
            yield Button("Refresh", id="refresh-btn")

    def _create_history_list(self) -> ListView:
        """Create the history list view.

        Returns:
            ListView with audit entries.
        """
        self._load_entries()
        self._apply_filter()

        list_view = ListView(id="history-list")

        for entry in self._filtered_entries:
            item = AuditLogItem(
                entry_id=str(entry.get("id", "")),
                timestamp=str(entry.get("timestamp", "")),
                action=str(entry.get("action", "")),
                summary=str(entry.get("summary", entry.get("target", ""))),
            )
            list_view.mount(item)

        return list_view

    def _load_entries(self) -> None:
        """Load audit log entries from storage."""
        self._entries = []

        # Try multiple audit file locations
        audit_paths = [
            self._project_root / ".project" / "audit" / "audit-log.jsonl",
            self._project_root / "audit" / "audit-log.jsonl",
            self._project_root / ".project" / "audit.jsonl",
        ]

        for audit_path in audit_paths:
            if audit_path.exists():
                try:
                    with audit_path.open("r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    entry = json.loads(line)
                                    self._entries.append(entry)
                                except json.JSONDecodeError:
                                    continue
                except OSError:
                    continue
                break  # Use first found audit file

        # Sort by timestamp, newest first
        self._entries.sort(
            key=lambda e: e.get("timestamp", ""),
            reverse=True,
        )

    def _apply_filter(self) -> None:
        """Apply the current filter to entries."""
        if not self._filter_text:
            self._filtered_entries = self._entries.copy()
            return

        search = self._filter_text.lower()
        self._filtered_entries = [
            entry for entry in self._entries
            if (
                search in str(entry.get("action", "")).lower()
                or search in str(entry.get("target", "")).lower()
                or search in str(entry.get("summary", "")).lower()
                or search in str(entry.get("actor", "")).lower()
            )
        ]

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes.

        Args:
            event: Input change event.
        """
        if event.input.id == "filter-input":
            self._filter_text = event.value
            self._apply_filter()
            # Refresh the list
            list_view = self.query_one("#history-list", ListView)
            list_view.clear()
            for entry in self._filtered_entries:
                item = AuditLogItem(
                    entry_id=str(entry.get("id", "")),
                    timestamp=str(entry.get("timestamp", "")),
                    action=str(entry.get("action", "")),
                    summary=str(entry.get("summary", entry.get("target", ""))),
                )
                list_view.mount(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle entry selection.

        Args:
            event: Selection event.
        """
        if isinstance(event.item, AuditLogItem):
            entry_id = event.item.entry_id
            for entry in self._entries:
                if str(entry.get("id", "")) == entry_id:
                    detail_panel = self.query_one(AuditDetailPanel)
                    detail_panel.set_entry(entry)
                    break

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button press event.
        """
        if event.button.id == "clear-filter-btn":
            self._filter_text = ""
            filter_input = self.query_one("#filter-input", Input)
            filter_input.value = ""
            self._apply_filter()

        elif event.button.id == "export-json-btn":
            self._export_json()

        elif event.button.id == "export-csv-btn":
            self._export_csv()

        elif event.button.id == "refresh-btn":
            self._load_entries()
            self._apply_filter()
            self.notify("Audit log refreshed")

    def _export_json(self) -> None:
        """Export entries to JSON file."""
        export_path = self._project_root / "audit-export.json"
        try:
            with export_path.open("w", encoding="utf-8") as f:
                json.dump(self._filtered_entries, f, indent=2)
            self.notify(f"Exported to {export_path}")
        except OSError as e:
            self.notify(f"Export failed: {e}", severity="error")

    def _export_csv(self) -> None:
        """Export entries to CSV file."""
        export_path = self._project_root / "audit-export.csv"
        try:
            with export_path.open("w", encoding="utf-8") as f:
                # Header
                f.write("timestamp,action,actor,target,status\n")
                # Entries
                for entry in self._filtered_entries:
                    row = [
                        str(entry.get("timestamp", "")),
                        str(entry.get("action", "")),
                        str(entry.get("actor", "")),
                        str(entry.get("target", "")),
                        str(entry.get("status", "")),
                    ]
                    # Escape commas and quotes
                    row = [f'"{v.replace('"', '""')}"' for v in row]
                    f.write(",".join(row) + "\n")
            self.notify(f"Exported to {export_path}")
        except OSError as e:
            self.notify(f"Export failed: {e}", severity="error")

    async def refresh_view(self) -> None:
        """Refresh the history viewer."""
        self._load_entries()
        self._apply_filter()
        await self.remove_children()
        await self.mount_all(list(self.compose()))
