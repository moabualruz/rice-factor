"""Artifact browser screen for TUI.

This module provides the artifact browser screen for viewing and
managing artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, ListItem, ListView, Static

if TYPE_CHECKING:
    from rice_factor.domain.services.artifact_service import ArtifactService


class ArtifactListItem(ListItem):
    """A list item representing an artifact.

    Attributes:
        artifact_id: UUID of the artifact.
        artifact_type: Type of the artifact.
        status: Current status of the artifact.
    """

    def __init__(
        self,
        artifact_id: str,
        artifact_type: str,
        status: str,
    ) -> None:
        """Initialize an artifact list item.

        Args:
            artifact_id: UUID of the artifact.
            artifact_type: Type of the artifact.
            status: Current status of the artifact.
        """
        super().__init__()
        self._artifact_id = artifact_id
        self._artifact_type = artifact_type
        self._status = status

    @property
    def artifact_id(self) -> str:
        """Get the artifact ID."""
        return self._artifact_id

    @property
    def artifact_type(self) -> str:
        """Get the artifact type."""
        return self._artifact_type

    @property
    def status(self) -> str:
        """Get the artifact status."""
        return self._status

    def compose(self) -> ComposeResult:
        """Compose the list item display.

        Yields:
            UI components.
        """
        status_class = f"status-{self._status.lower()}"
        yield Label(
            f"[{self._status}] {self._artifact_type} ({self._artifact_id[:8]}...)",
            classes=status_class,
        )


class ArtifactDetailPanel(Static):
    """Panel showing artifact details.

    Displays the full details of a selected artifact.
    """

    # Rice-Factor brand colors
    DEFAULT_CSS = """
    ArtifactDetailPanel {
        width: 100%;
        height: 100%;
        border: solid #009e20;
        padding: 1;
        overflow-y: auto;
        background: #0a1a0a;
    }

    ArtifactDetailPanel .detail-header {
        text-style: bold;
        margin-bottom: 1;
        color: #00a020;
    }

    ArtifactDetailPanel .detail-field {
        margin: 0 0 1 0;
    }

    ArtifactDetailPanel .field-label {
        color: #808080;
    }

    ArtifactDetailPanel .field-value {
        margin-left: 2;
        color: #00c030;
    }
    """

    def __init__(self) -> None:
        """Initialize the detail panel."""
        super().__init__()
        self._artifact_data: dict[str, Any] | None = None

    def set_artifact(self, artifact_data: dict[str, Any]) -> None:
        """Set the artifact to display.

        Args:
            artifact_data: Artifact data dictionary.
        """
        self._artifact_data = artifact_data
        self.refresh_display()

    def clear(self) -> None:
        """Clear the displayed artifact."""
        self._artifact_data = None
        self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the display with current artifact data."""
        self.remove_children()
        self.mount_all(list(self.compose()))

    def compose(self) -> ComposeResult:
        """Compose the detail panel.

        Yields:
            UI components.
        """
        if self._artifact_data is None:
            yield Label("Select an artifact to view details", classes="detail-header")
            return

        yield Label("Artifact Details", classes="detail-header")

        # Display artifact fields
        fields = [
            ("ID", str(self._artifact_data.get("id", ""))),
            ("Type", str(self._artifact_data.get("artifact_type", ""))),
            ("Status", str(self._artifact_data.get("status", ""))),
            ("Version", str(self._artifact_data.get("version", ""))),
            ("Created", str(self._artifact_data.get("created_at", ""))),
        ]

        for label, value in fields:
            with Container(classes="detail-field"):
                yield Label(f"{label}:", classes="field-label")
                yield Label(value, classes="field-value")

        # Show payload summary
        payload = self._artifact_data.get("payload", {})
        if payload:
            yield Label("Payload:", classes="field-label")
            payload_str = json.dumps(payload, indent=2)
            # Truncate long payloads
            if len(payload_str) > 500:
                payload_str = payload_str[:500] + "\n... (truncated)"
            yield Label(payload_str, classes="field-value")


class ArtifactBrowserScreen(Static):
    """Artifact browser screen.

    Shows a list of artifacts and allows viewing details.

    Attributes:
        project_root: Root directory of the project.
        artifact_service: Service for artifact operations.
    """

    # Rice-Factor brand colors
    DEFAULT_CSS = """
    ArtifactBrowserScreen {
        width: 100%;
        height: 100%;
        background: #0a1a0a;
    }

    #browser-header {
        height: auto;
        padding: 1;
        text-align: center;
        background: #009e20;
        color: white;
    }

    #browser-content {
        width: 100%;
        height: 1fr;
    }

    #artifact-list-panel {
        width: 40%;
        height: 100%;
        border-right: solid #00a020;
    }

    #artifact-detail-panel {
        width: 60%;
        height: 100%;
    }

    #artifact-list {
        height: 100%;
        background: #0a1a0a;
    }

    .list-header {
        padding: 1;
        background: #102010;
        text-style: bold;
        color: #00a020;
    }

    .no-artifacts {
        padding: 2;
        text-align: center;
        color: #808080;
    }
    """

    def __init__(
        self,
        project_root: Path | None = None,
        artifact_service: ArtifactService | None = None,
    ) -> None:
        """Initialize the artifact browser screen.

        Args:
            project_root: Root directory of the project.
            artifact_service: Service for artifact operations.
        """
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._artifact_service = artifact_service
        self._artifacts: list[dict[str, Any]] = []

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    @property
    def artifact_service(self) -> ArtifactService | None:
        """Get the artifact service."""
        return self._artifact_service

    def compose(self) -> ComposeResult:
        """Compose the browser view.

        Yields:
            UI components.
        """
        yield Static("Artifact Browser", id="browser-header")

        with Horizontal(id="browser-content"):
            with Vertical(id="artifact-list-panel"):
                yield Label("Artifacts", classes="list-header")
                yield self._create_artifact_list()

            with Vertical(id="artifact-detail-panel"):
                yield ArtifactDetailPanel()

    def _create_artifact_list(self) -> ListView:
        """Create the artifact list view.

        Returns:
            ListView with artifacts.
        """
        self._load_artifacts()

        list_view = ListView(id="artifact-list")

        if not self._artifacts:
            # No artifacts - add placeholder
            pass
        else:
            for artifact in self._artifacts:
                item = ArtifactListItem(
                    artifact_id=str(artifact.get("id", "")),
                    artifact_type=str(artifact.get("artifact_type", "")),
                    status=str(artifact.get("status", "")),
                )
                list_view.mount(item)

        return list_view

    def _load_artifacts(self) -> None:
        """Load artifacts from storage."""
        self._artifacts = []

        if self._artifact_service is None:
            return

        try:
            storage = self._artifact_service.storage
            # Try to load all artifact types
            from rice_factor.domain.artifacts.enums import ArtifactType

            for artifact_type in ArtifactType:
                try:
                    artifacts = storage.list_by_type(artifact_type)
                    for artifact in artifacts:
                        self._artifacts.append({
                            "id": str(artifact.id),
                            "artifact_type": artifact.artifact_type.value,
                            "status": artifact.status.value,
                            "version": artifact.artifact_version,
                            "created_at": str(artifact.created_at),
                            "payload": artifact.payload.model_dump() if artifact.payload else {},
                        })
                except Exception:
                    continue
        except Exception:
            pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle artifact selection.

        Args:
            event: Selection event.
        """
        if isinstance(event.item, ArtifactListItem):
            # Find the artifact data
            artifact_id = event.item.artifact_id
            for artifact in self._artifacts:
                if artifact.get("id") == artifact_id:
                    detail_panel = self.query_one(ArtifactDetailPanel)
                    detail_panel.set_artifact(artifact)
                    break

    def refresh_view(self) -> None:
        """Refresh the artifact browser view."""
        self._load_artifacts()
        self.remove_children()
        self.mount_all(list(self.compose()))
