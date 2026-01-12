"""Diff viewer screen for TUI.

This module provides a split-view diff viewer screen for reviewing
pending code changes with syntax highlighting.
"""

from __future__ import annotations

import json
from difflib import unified_diff
from pathlib import Path
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, ListItem, ListView, Static

if TYPE_CHECKING:
    from rice_factor.domain.services.artifact_service import ArtifactService


class DiffListItem(ListItem):
    """A list item representing a diff.

    Attributes:
        diff_id: UUID of the diff artifact.
        file_path: Target file path.
        status: Current status (pending, approved, rejected).
    """

    def __init__(
        self,
        diff_id: str,
        file_path: str,
        status: str,
    ) -> None:
        """Initialize a diff list item.

        Args:
            diff_id: UUID of the diff artifact.
            file_path: Target file path.
            status: Current status.
        """
        super().__init__()
        self._diff_id = diff_id
        self._file_path = file_path
        self._status = status

    @property
    def diff_id(self) -> str:
        """Get the diff ID."""
        return self._diff_id

    @property
    def file_path(self) -> str:
        """Get the file path."""
        return self._file_path

    @property
    def status(self) -> str:
        """Get the diff status."""
        return self._status

    def compose(self) -> ComposeResult:
        """Compose the list item display.

        Yields:
            UI components.
        """
        status_icon = {
            "pending": "[?]",
            "approved": "[OK]",
            "rejected": "[X]",
        }.get(self._status.lower(), "[?]")

        yield Label(
            f"{status_icon} {self._file_path}",
            classes=f"status-{self._status.lower()}",
        )


class DiffContentPanel(Static):
    """Panel showing unified diff content with syntax highlighting.

    Displays the diff in a side-by-side or unified format with color coding
    for additions, deletions, and context lines.
    """

    DEFAULT_CSS = """
    DiffContentPanel {
        width: 100%;
        height: 100%;
        border: solid #009e20;
        padding: 1;
        overflow-y: auto;
        overflow-x: auto;
        background: #0a1a0a;
    }

    DiffContentPanel .diff-header {
        text-style: bold;
        margin-bottom: 1;
        color: #00a020;
    }

    DiffContentPanel .diff-meta {
        color: #808080;
        margin-bottom: 1;
    }

    DiffContentPanel .diff-line {
        font-family: monospace;
    }

    DiffContentPanel .diff-add {
        color: #00ff00;
        background: #002200;
    }

    DiffContentPanel .diff-del {
        color: #ff6666;
        background: #220000;
    }

    DiffContentPanel .diff-hunk {
        color: #00c0ff;
        margin-top: 1;
    }

    DiffContentPanel .diff-context {
        color: #c0c0c0;
    }

    DiffContentPanel .no-diff {
        color: #808080;
        text-align: center;
        margin-top: 2;
    }
    """

    def __init__(self) -> None:
        """Initialize the diff content panel."""
        super().__init__()
        self._diff_data: dict[str, Any] | None = None

    def set_diff(self, diff_data: dict[str, Any]) -> None:
        """Set the diff to display.

        Args:
            diff_data: Diff data dictionary.
        """
        self._diff_data = diff_data
        self.refresh_display()

    def clear(self) -> None:
        """Clear the displayed diff."""
        self._diff_data = None
        self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the display with current diff data."""
        self.remove_children()
        self.mount_all(list(self.compose()))

    def compose(self) -> ComposeResult:
        """Compose the diff content panel.

        Yields:
            UI components.
        """
        if self._diff_data is None:
            yield Label("Select a diff to view changes", classes="no-diff")
            return

        file_path = self._diff_data.get("file_path", "Unknown")
        yield Label(f"Changes to: {file_path}", classes="diff-header")

        # Show metadata
        status = self._diff_data.get("status", "unknown")
        diff_id = self._diff_data.get("id", "")[:8]
        yield Label(f"Status: {status} | ID: {diff_id}...", classes="diff-meta")

        # Get the diff content
        diff_content = self._diff_data.get("diff_content", "")
        if not diff_content:
            # Try to generate diff from old/new content
            old_content = self._diff_data.get("old_content", "")
            new_content = self._diff_data.get("new_content", "")
            if old_content or new_content:
                diff_content = self._generate_unified_diff(
                    old_content, new_content, file_path
                )

        if not diff_content:
            yield Label("No diff content available", classes="no-diff")
            return

        # Render diff lines with syntax highlighting
        for line in diff_content.split("\n"):
            css_class = self._get_line_class(line)
            yield Label(line, classes=f"diff-line {css_class}")

    def _generate_unified_diff(
        self,
        old_content: str,
        new_content: str,
        file_path: str,
    ) -> str:
        """Generate unified diff from old and new content.

        Args:
            old_content: Original file content.
            new_content: New file content.
            file_path: Path to the file.

        Returns:
            Unified diff string.
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff_lines = unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )

        return "".join(diff_lines)

    def _get_line_class(self, line: str) -> str:
        """Get CSS class for a diff line.

        Args:
            line: Diff line content.

        Returns:
            CSS class name.
        """
        if line.startswith("+++") or line.startswith("---"):
            return "diff-meta"
        elif line.startswith("@@"):
            return "diff-hunk"
        elif line.startswith("+"):
            return "diff-add"
        elif line.startswith("-"):
            return "diff-del"
        else:
            return "diff-context"


class DiffViewerScreen(Static):
    """Diff viewer screen.

    Shows pending diffs and allows reviewing changes in a split view.

    Attributes:
        project_root: Root directory of the project.
        artifact_service: Service for artifact operations.
    """

    DEFAULT_CSS = """
    DiffViewerScreen {
        width: 100%;
        height: 100%;
        background: #0a1a0a;
    }

    #diff-header {
        height: auto;
        padding: 1;
        text-align: center;
        background: #009e20;
        color: white;
    }

    #diff-content {
        width: 100%;
        height: 1fr;
    }

    #diff-list-panel {
        width: 30%;
        height: 100%;
        border-right: solid #00a020;
    }

    #diff-detail-panel {
        width: 70%;
        height: 100%;
    }

    #diff-list {
        height: 100%;
        background: #0a1a0a;
    }

    .list-header {
        padding: 1;
        background: #102010;
        text-style: bold;
        color: #00a020;
    }

    .no-diffs {
        padding: 2;
        text-align: center;
        color: #808080;
    }

    #diff-actions {
        height: auto;
        padding: 1;
        background: #102010;
        border-top: solid #009e20;
    }

    .action-hint {
        color: #00c030;
    }
    """

    def __init__(
        self,
        project_root: Path | None = None,
        artifact_service: ArtifactService | None = None,
    ) -> None:
        """Initialize the diff viewer screen.

        Args:
            project_root: Root directory of the project.
            artifact_service: Service for artifact operations.
        """
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._artifact_service = artifact_service
        self._diffs: list[dict[str, Any]] = []
        self._selected_diff: dict[str, Any] | None = None

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    @property
    def artifact_service(self) -> ArtifactService | None:
        """Get the artifact service."""
        return self._artifact_service

    def compose(self) -> ComposeResult:
        """Compose the diff viewer.

        Yields:
            UI components.
        """
        yield Static("Diff Viewer", id="diff-header")

        with Horizontal(id="diff-content"):
            with Vertical(id="diff-list-panel"):
                yield Label("Pending Diffs", classes="list-header")
                yield self._create_diff_list()

            with Vertical(id="diff-detail-panel"):
                yield DiffContentPanel()
                yield Static(
                    "[a] Approve  [r] Reject  [n] Next  [p] Previous",
                    id="diff-actions",
                    classes="action-hint",
                )

    def _create_diff_list(self) -> ListView:
        """Create the diff list view.

        Returns:
            ListView with diffs.
        """
        self._load_diffs()

        list_view = ListView(id="diff-list")

        if not self._diffs:
            pass  # Empty list handled in compose
        else:
            for diff in self._diffs:
                item = DiffListItem(
                    diff_id=str(diff.get("id", "")),
                    file_path=str(diff.get("file_path", "unknown")),
                    status=str(diff.get("status", "pending")),
                )
                list_view.mount(item)

        return list_view

    def _load_diffs(self) -> None:
        """Load diffs from storage."""
        self._diffs = []

        # Try to load from artifacts directory
        artifacts_dir = self._project_root / "artifacts"
        if not artifacts_dir.exists():
            return

        # Look for diff files
        for diff_file in artifacts_dir.rglob("*.diff.json"):
            try:
                data = json.loads(diff_file.read_text(encoding="utf-8"))
                self._diffs.append({
                    "id": str(data.get("id", diff_file.stem)),
                    "file_path": data.get("target_file", str(diff_file)),
                    "status": data.get("status", "pending"),
                    "diff_content": data.get("diff_content", ""),
                    "old_content": data.get("old_content", ""),
                    "new_content": data.get("new_content", ""),
                })
            except (json.JSONDecodeError, OSError):
                continue

        # Also check for pending diffs in implementation plans
        for artifact_file in artifacts_dir.rglob("*.json"):
            if "_meta" in str(artifact_file) or ".diff." in str(artifact_file):
                continue

            try:
                data = json.loads(artifact_file.read_text(encoding="utf-8"))
                if data.get("artifact_type") == "ImplementationPlan":
                    payload = data.get("payload", {})
                    diff_content = payload.get("diff", "")
                    if diff_content:
                        self._diffs.append({
                            "id": str(data.get("id", artifact_file.stem)),
                            "file_path": payload.get("target_file", "unknown"),
                            "status": data.get("status", "draft"),
                            "diff_content": diff_content,
                        })
            except (json.JSONDecodeError, OSError):
                continue

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle diff selection.

        Args:
            event: Selection event.
        """
        if isinstance(event.item, DiffListItem):
            diff_id = event.item.diff_id
            for diff in self._diffs:
                if diff.get("id") == diff_id:
                    self._selected_diff = diff
                    content_panel = self.query_one(DiffContentPanel)
                    content_panel.set_diff(diff)
                    break

    async def action_approve_diff(self) -> None:
        """Approve the selected diff."""
        if self._selected_diff:
            self.notify(f"Approved diff for: {self._selected_diff.get('file_path')}")
            # In a real implementation, this would call the approval service

    async def action_reject_diff(self) -> None:
        """Reject the selected diff."""
        if self._selected_diff:
            self.notify(f"Rejected diff for: {self._selected_diff.get('file_path')}")
            # In a real implementation, this would call the rejection service

    async def refresh_view(self) -> None:
        """Refresh the diff viewer."""
        self._load_diffs()
        await self.remove_children()
        await self.mount_all(list(self.compose()))
