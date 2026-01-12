"""Main TUI application for Rice-Factor.

This module provides the main Textual application for the interactive
terminal user interface.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, TabbedContent, TabPane

from rice_factor.entrypoints.tui.screens.browser import ArtifactBrowserScreen
from rice_factor.entrypoints.tui.screens.workflow import WorkflowScreen
from rice_factor.entrypoints.tui.widgets.status_bar import StatusBar

if TYPE_CHECKING:
    from rice_factor.domain.services.artifact_service import ArtifactService
    from rice_factor.domain.services.phase_service import PhaseService


class RiceFactorTUI(App[None]):
    """Interactive TUI for Rice-Factor.

    Provides workflow navigation and artifact browsing in a terminal UI.

    Attributes:
        project_root: Root directory of the project.
        phase_service: Service for phase detection.
        artifact_service: Service for artifact operations.
    """

    TITLE = "Rice-Factor"
    SUB_TITLE = "LLM-Assisted Development System"

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #content-area {
        width: 100%;
        height: 1fr;
    }

    #sidebar {
        width: 30;
        height: 100%;
        border-right: solid $primary;
    }

    #main-panel {
        width: 1fr;
        height: 100%;
    }

    .phase-display {
        text-align: center;
        padding: 1;
        background: $primary;
        color: $text;
    }

    .info-panel {
        padding: 1;
        border: solid $secondary;
        margin: 1;
    }

    StatusBar {
        dock: bottom;
        height: 1;
        background: $primary;
    }

    .artifact-item {
        padding: 0 1;
    }

    .artifact-item:hover {
        background: $accent;
    }

    .artifact-item.selected {
        background: $primary;
    }

    .status-draft {
        color: $warning;
    }

    .status-approved {
        color: $success;
    }

    .status-locked {
        color: $error;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("w", "switch_tab('workflow')", "Workflow"),
        Binding("a", "switch_tab('artifacts')", "Artifacts"),
        Binding("r", "refresh", "Refresh"),
        Binding("?", "help", "Help"),
    ]

    def __init__(
        self,
        project_root: Path | None = None,
        phase_service: PhaseService | None = None,
        artifact_service: ArtifactService | None = None,
    ) -> None:
        """Initialize the TUI application.

        Args:
            project_root: Root directory of the project.
            phase_service: Service for phase detection.
            artifact_service: Service for artifact operations.
        """
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._phase_service = phase_service
        self._artifact_service = artifact_service

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    @property
    def phase_service(self) -> PhaseService | None:
        """Get the phase service."""
        return self._phase_service

    @property
    def artifact_service(self) -> ArtifactService | None:
        """Get the artifact service."""
        return self._artifact_service

    def compose(self) -> ComposeResult:
        """Compose the UI layout.

        Yields:
            UI components.
        """
        yield Header()

        with Container(id="main-container"), TabbedContent(id="tabs"):
            with TabPane("Workflow", id="workflow-tab"):
                yield WorkflowScreen(
                    project_root=self._project_root,
                    phase_service=self._phase_service,
                )
            with TabPane("Artifacts", id="artifacts-tab"):
                yield ArtifactBrowserScreen(
                    project_root=self._project_root,
                    artifact_service=self._artifact_service,
                )

        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        """Handle app mount event."""
        self.refresh_status()

    def refresh_status(self) -> None:
        """Refresh the status bar with current phase info."""
        status_bar = self.query_one(StatusBar)
        if self._phase_service is not None:
            phase = self._phase_service.get_current_phase()
            status_bar.update_phase(phase.value)
        else:
            status_bar.update_phase("unknown")

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab.

        Args:
            tab_id: ID of the tab to switch to.
        """
        tabs = self.query_one(TabbedContent)
        if tab_id == "workflow":
            tabs.active = "workflow-tab"
        elif tab_id == "artifacts":
            tabs.active = "artifacts-tab"

    def action_refresh(self) -> None:
        """Refresh the current view."""
        self.refresh_status()

        # Refresh the active screen
        tabs = self.query_one(TabbedContent)
        if tabs.active == "workflow-tab":
            workflow = self.query_one(WorkflowScreen)
            workflow.refresh_view()
        elif tabs.active == "artifacts-tab":
            browser = self.query_one(ArtifactBrowserScreen)
            browser.refresh_view()

    def action_help(self) -> None:
        """Show help information."""
        self.notify(
            "Keyboard shortcuts:\n"
            "  q - Quit\n"
            "  w - Workflow tab\n"
            "  a - Artifacts tab\n"
            "  r - Refresh\n"
            "  ? - This help",
            title="Help",
            timeout=5,
        )


def run_tui(
    project_root: Path | None = None,
    phase_service: PhaseService | None = None,
    artifact_service: ArtifactService | None = None,
) -> None:
    """Run the TUI application.

    Args:
        project_root: Root directory of the project.
        phase_service: Service for phase detection.
        artifact_service: Service for artifact operations.
    """
    app = RiceFactorTUI(
        project_root=project_root,
        phase_service=phase_service,
        artifact_service=artifact_service,
    )
    app.run()
