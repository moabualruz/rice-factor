"""Main TUI application for Rice-Factor.

This module provides the main Textual application for the interactive
terminal user interface.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from rice_factor.entrypoints.tui.screens.browser import ArtifactBrowserScreen
from rice_factor.entrypoints.tui.screens.config_editor import ConfigEditorScreen
from rice_factor.entrypoints.tui.screens.diff_viewer import DiffViewerScreen
from rice_factor.entrypoints.tui.screens.graph import GraphScreen
from rice_factor.entrypoints.tui.screens.history import HistoryScreen
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

    # Rice-Factor brand colors from .branding/
    # Primary: #00a020 (bright green)
    # Secondary: #009e20 (darker green)
    # Recommended font: Terminus (Nerd Font) from .branding/Terminus/

    CSS = """
    /* Rice-Factor Brand Theme */
    $rf-primary: #00a020;
    $rf-secondary: #009e20;
    $rf-accent: #00c030;
    $rf-bg-dark: #0a1a0a;
    $rf-bg-light: #102010;

    Screen {
        background: $rf-bg-dark;
    }

    Header {
        background: $rf-secondary;
        color: white;
    }

    Footer {
        background: $rf-secondary;
    }

    TabbedContent {
        background: $rf-bg-dark;
    }

    TabPane {
        background: $rf-bg-dark;
    }

    Tab {
        background: $rf-bg-light;
        color: $rf-primary;
    }

    Tab.-active {
        background: $rf-primary;
        color: white;
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
        border-right: solid $rf-primary;
    }

    #main-panel {
        width: 1fr;
        height: 100%;
    }

    .phase-display {
        text-align: center;
        padding: 1;
        background: $rf-primary;
        color: white;
    }

    .info-panel {
        padding: 1;
        border: solid $rf-secondary;
        margin: 1;
    }

    StatusBar {
        dock: bottom;
        height: 1;
        background: $rf-primary;
        color: white;
    }

    .artifact-item {
        padding: 0 1;
    }

    .artifact-item:hover {
        background: $rf-accent;
        color: black;
    }

    .artifact-item.selected {
        background: $rf-primary;
        color: white;
    }

    .status-draft {
        color: #ffcc00;
    }

    .status-approved {
        color: $rf-accent;
    }

    .status-locked {
        color: #ff6666;
    }

    /* Workflow step styling */
    WorkflowStep {
        border: solid $rf-secondary;
    }

    WorkflowStep.current {
        border: double $rf-primary;
        background: $rf-bg-light;
    }

    WorkflowStep.complete {
        border: solid $rf-accent;
    }

    /* List and tree styling */
    ListView {
        background: $rf-bg-dark;
    }

    ListItem {
        background: $rf-bg-dark;
    }

    ListItem:hover {
        background: $rf-bg-light;
    }

    Tree {
        background: $rf-bg-dark;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("w", "switch_tab('workflow')", "Workflow"),
        Binding("a", "switch_tab('artifacts')", "Artifacts"),
        Binding("d", "switch_tab('diffs')", "Diffs"),
        Binding("c", "switch_tab('config')", "Config"),
        Binding("h", "switch_tab('history')", "History"),
        Binding("g", "switch_tab('graph')", "Graph"),
        Binding("r", "refresh", "Refresh"),
        Binding("enter", "execute_step", "Execute"),
        Binding("?", "help", "Help"),
    ]

    def action_execute_step(self) -> None:
        """Execute the current step in the active screen."""
        tabs = self.query_one(TabbedContent)
        if tabs.active == "workflow-tab":
            workflow = self.query_one(WorkflowScreen)
            # We need to await it, but action handlers in Textual can be async
            # However, looking at the base App class, we might need to be careful.
            # Let's delegate to the screen.
            # workflow.action_execute_step() # This isn't how actions work in Textual usually.
            # We can define the action on the specific widget and let bubbling handle it, 
            # OR explicitly call it.
            # Since I added `action_execute_step` to WorkflowScreen, I should let the app delegate it.
            
            # Actually, better pattern:
            # If the focus is on the WorkflowScreen, it should catch the action?
            # But WorkflowScreen is a Static, might not have focus.
            # Let's manually call the method on the screen instance.
            import asyncio
            asyncio.create_task(workflow.action_execute_step())

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

        with TabbedContent(id="tabs"):
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
            with TabPane("Diffs", id="diffs-tab"):
                yield DiffViewerScreen(
                    project_root=self._project_root,
                    artifact_service=self._artifact_service,
                )
            with TabPane("Config", id="config-tab"):
                yield ConfigEditorScreen(
                    project_root=self._project_root,
                )
            with TabPane("History", id="history-tab"):
                yield HistoryScreen(
                    project_root=self._project_root,
                )
            with TabPane("Graph", id="graph-tab"):
                yield GraphScreen(
                    project_root=self._project_root,
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
        tab_map = {
            "workflow": "workflow-tab",
            "artifacts": "artifacts-tab",
            "diffs": "diffs-tab",
            "config": "config-tab",
            "history": "history-tab",
            "graph": "graph-tab",
        }
        if tab_id in tab_map:
            tabs.active = tab_map[tab_id]

    async def action_refresh(self) -> None:
        """Refresh the current view."""
        self.refresh_status()

        # Refresh the active screen
        tabs = self.query_one(TabbedContent)
        active_tab = tabs.active

        refresh_map = {
            "workflow-tab": (WorkflowScreen, "refresh_view"),
            "artifacts-tab": (ArtifactBrowserScreen, "refresh_view"),
            "diffs-tab": (DiffViewerScreen, "refresh_view"),
            "config-tab": (ConfigEditorScreen, "refresh_view"),
            "history-tab": (HistoryScreen, "refresh_view"),
            "graph-tab": (GraphScreen, "refresh_view"),
        }

        if active_tab in refresh_map:
            screen_class, method_name = refresh_map[active_tab]
            try:
                screen = self.query_one(screen_class)
                method = getattr(screen, method_name)
                await method()
            except Exception:
                pass

    def action_help(self) -> None:
        """Show help information."""
        self.notify(
            "Keyboard shortcuts:\n"
            "  q - Quit\n"
            "  w - Workflow tab\n"
            "  a - Artifacts tab\n"
            "  d - Diffs tab\n"
            "  c - Config tab\n"
            "  h - History tab\n"
            "  g - Graph tab\n"
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
