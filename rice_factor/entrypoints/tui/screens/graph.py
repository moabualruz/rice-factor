"""Graph screen for TUI.

This module provides an artifact dependency graph viewer screen using
ASCII/box-drawing characters for visualization.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Static


class GraphNode:
    """A node in the artifact dependency graph.

    Attributes:
        artifact_id: UUID of the artifact.
        artifact_type: Type of the artifact.
        status: Current status.
        depends_on: List of artifact IDs this depends on.
        dependents: List of artifact IDs that depend on this.
    """

    def __init__(
        self,
        artifact_id: str,
        artifact_type: str,
        status: str,
    ) -> None:
        """Initialize a graph node.

        Args:
            artifact_id: UUID of the artifact.
            artifact_type: Type of the artifact.
            status: Current status.
        """
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.status = status
        self.depends_on: list[str] = []
        self.dependents: list[str] = []


class GraphRenderer:
    """Renders artifact graphs using ASCII box-drawing characters."""

    # Box drawing characters
    HORIZONTAL = "─"
    VERTICAL = "│"
    CORNER_TL = "┌"
    CORNER_TR = "┐"
    CORNER_BL = "└"
    CORNER_BR = "┘"
    TEE_LEFT = "├"
    TEE_RIGHT = "┤"
    TEE_DOWN = "┬"
    TEE_UP = "┴"
    CROSS = "┼"
    ARROW_RIGHT = "→"
    ARROW_DOWN = "↓"

    def __init__(self, nodes: dict[str, GraphNode]) -> None:
        """Initialize the graph renderer.

        Args:
            nodes: Dictionary of artifact ID to GraphNode.
        """
        self._graph_nodes = nodes

    def render(self) -> str:
        """Render the graph as ASCII art.

        Returns:
            ASCII representation of the graph.
        """
        if not self._graph_nodes:
            return "No artifacts to display"

        lines: list[str] = []

        # Group nodes by type for better visualization
        types_order = [
            "ProjectPlan",
            "ArchitecturePlan",
            "ScaffoldPlan",
            "TestPlan",
            "ImplementationPlan",
            "RefactorPlan",
            "ValidationResult",
            "FailureReport",
            "ReconciliationPlan",
        ]

        nodes_by_type: dict[str, list[GraphNode]] = {}
        for node in self._graph_nodes.values():
            if node.artifact_type not in nodes_by_type:
                nodes_by_type[node.artifact_type] = []
            nodes_by_type[node.artifact_type].append(node)

        # Render header
        lines.append(f"{self.CORNER_TL}{self.HORIZONTAL * 60}{self.CORNER_TR}")
        lines.append(f"{self.VERTICAL} Artifact Dependency Graph" + " " * 34 + self.VERTICAL)
        lines.append(f"{self.TEE_LEFT}{self.HORIZONTAL * 60}{self.TEE_RIGHT}")

        # Render by type in logical order
        rendered_count = 0
        for artifact_type in types_order:
            if artifact_type in nodes_by_type:
                nodes = nodes_by_type[artifact_type]

                # Type header
                type_display = artifact_type.replace("Plan", " Plan")
                lines.append(f"{self.VERTICAL} ")
                lines.append(
                    f"{self.VERTICAL} {self.TEE_DOWN}{self.HORIZONTAL * 2} {type_display}"
                    + " " * (55 - len(type_display)) + self.VERTICAL
                )

                # Render each node
                for i, node in enumerate(nodes):
                    is_last = (i == len(nodes) - 1)
                    prefix = self.CORNER_BL if is_last else self.TEE_LEFT

                    # Status indicator
                    status_char = {
                        "draft": "?",
                        "approved": "+",
                        "locked": "#",
                    }.get(node.status.lower(), "?")

                    # Format node display
                    node_id = node.artifact_id[:8]
                    node_line = (
                        f"{self.VERTICAL}    {prefix}{self.HORIZONTAL} [{status_char}] {node_id}"
                    )

                    # Add dependency arrows if any
                    if node.depends_on:
                        deps = ", ".join(d[:6] for d in node.depends_on[:3])
                        if len(node.depends_on) > 3:
                            deps += "..."
                        node_line += f" {self.ARROW_RIGHT} depends on: {deps}"

                    # Pad to box width
                    padding = 61 - len(node_line)
                    if padding > 0:
                        node_line += " " * padding
                    elif padding < 0:
                        node_line = node_line[:60] + self.VERTICAL
                    else:
                        node_line += self.VERTICAL

                    lines.append(node_line)
                    rendered_count += 1

        # Handle any types not in our order
        for artifact_type, nodes in nodes_by_type.items():
            if artifact_type not in types_order:
                lines.append(f"{self.VERTICAL} ")
                lines.append(
                    f"{self.VERTICAL} {self.TEE_DOWN}{self.HORIZONTAL * 2} {artifact_type}"
                    + " " * (55 - len(artifact_type)) + self.VERTICAL
                )

                for i, node in enumerate(nodes):
                    is_last = (i == len(nodes) - 1)
                    prefix = self.CORNER_BL if is_last else self.TEE_LEFT

                    status_char = {
                        "draft": "?",
                        "approved": "+",
                        "locked": "#",
                    }.get(node.status.lower(), "?")

                    node_id = node.artifact_id[:8]
                    node_line = (
                        f"{self.VERTICAL}    {prefix}{self.HORIZONTAL} [{status_char}] {node_id}"
                    )

                    padding = 61 - len(node_line)
                    if padding > 0:
                        node_line += " " * padding
                    node_line += self.VERTICAL

                    lines.append(node_line)
                    rendered_count += 1

        # Footer
        lines.append(f"{self.VERTICAL} ")
        lines.append(f"{self.CORNER_BL}{self.HORIZONTAL * 60}{self.CORNER_BR}")

        # Legend
        lines.append("")
        lines.append("Legend: [?] Draft  [+] Approved  [#] Locked")
        lines.append(f"Total artifacts: {rendered_count}")

        return "\n".join(lines)

    def render_mermaid(self) -> str:
        """Render the graph as Mermaid diagram syntax.

        Returns:
            Mermaid diagram syntax.
        """
        lines = ["```mermaid", "graph TD"]

        # Define nodes
        for node in self._graph_nodes.values():
            node_id = node.artifact_id[:8]
            label = f"{node.artifact_type}\\n{node_id}"
            style = ""

            if node.status.lower() == "approved":
                style = ":::approved"
            elif node.status.lower() == "locked":
                style = ":::locked"
            else:
                style = ":::draft"

            lines.append(f"    {node_id}[{label}]{style}")

        # Define edges
        for node in self._graph_nodes.values():
            src_id = node.artifact_id[:8]
            for dep_id in node.depends_on:
                if dep_id in self._graph_nodes:
                    lines.append(f"    {self._graph_nodes[dep_id].artifact_id[:8]} --> {src_id}")

        # Define styles
        lines.extend([
            "",
            "    classDef draft fill:#ffcc00,color:#000",
            "    classDef approved fill:#00c030,color:#fff",
            "    classDef locked fill:#ff6666,color:#fff",
        ])

        lines.append("```")
        return "\n".join(lines)


class GraphPanel(Static):
    """Panel displaying the artifact graph."""

    DEFAULT_CSS = """
    GraphPanel {
        width: 100%;
        height: 100%;
        padding: 1;
        overflow-y: auto;
        overflow-x: auto;
        background: #0a1a0a;
    }

    GraphPanel .graph-content {
        color: #00c030;
    }

    GraphPanel .graph-header {
        text-style: bold;
        color: #00a020;
        margin-bottom: 1;
    }

    GraphPanel .graph-legend {
        color: #808080;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the graph panel."""
        super().__init__()
        self._graph_content: str = "Loading graph..."
        self._format: str = "ascii"

    def set_content(self, content: str) -> None:
        """Set the graph content to display.

        Args:
            content: Rendered graph content.
        """
        self._graph_content = content
        if self.is_attached:
            self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the display."""
        if self.is_attached:
            self.remove_children()
            self.mount_all(list(self.compose()))

    def compose(self) -> ComposeResult:
        """Compose the graph panel.

        Yields:
            UI components.
        """
        yield Label(self._graph_content, classes="graph-content")


class GraphScreen(Container):
    """Graph screen for visualizing artifact dependencies.

    Shows artifact relationships using ASCII box-drawing characters.

    Attributes:
        project_root: Root directory of the project.
    """

    DEFAULT_CSS = """
    GraphScreen {
        width: 100%;
        height: 100%;
        background: #0a1a0a;
    }

    #graph-header {
        height: auto;
        padding: 1;
        text-align: center;
        background: #009e20;
        color: white;
    }

    #graph-toolbar {
        height: auto;
        padding: 1;
        background: #102010;
    }

    #graph-content {
        width: 100%;
        height: 1fr;
    }

    #stats-bar {
        height: auto;
        padding: 1;
        background: #102010;
        border-top: solid #009e20;
    }

    .stats-label {
        color: #808080;
        margin-right: 2;
    }

    .format-label {
        color: #00c030;
        margin-left: 1;
    }
    """

    def __init__(
        self,
        project_root: Path | None = None,
    ) -> None:
        """Initialize the graph screen.

        Args:
            project_root: Root directory of the project.
        """
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._graph_nodes: dict[str, GraphNode] = {}
        self._display_format: str = "ascii"

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    def compose(self) -> ComposeResult:
        """Compose the graph viewer.

        Yields:
            UI components.
        """
        yield Static("Artifact Dependency Graph", id="graph-header")

        # Toolbar - don't use context managers
        yield Horizontal(
            Button("Refresh", id="refresh-btn"),
            Button("ASCII View", id="ascii-btn", variant="primary"),
            Button("Mermaid", id="mermaid-btn"),
            Button("Export", id="export-btn"),
            Label(f"Format: {self._display_format}", classes="format-label"),
            id="graph-toolbar",
        )

        # Graph content
        self._load_artifacts()
        renderer = GraphRenderer(self._graph_nodes)

        if self._display_format == "mermaid":
            content = renderer.render_mermaid()
        else:
            content = renderer.render()

        # Create panel with content already set
        panel = GraphPanel()
        panel._graph_content = content

        yield Vertical(panel, id="graph-content")

        # Stats bar
        artifact_count = len(self._graph_nodes)
        dependency_count = sum(len(n.depends_on) for n in self._graph_nodes.values())
        yield Horizontal(
            Label(
                f"Artifacts: {artifact_count} | Dependencies: {dependency_count}",
                classes="stats-label",
            ),
            id="stats-bar",
        )

    def _load_artifacts(self) -> None:
        """Load artifacts and build dependency graph."""
        self._graph_nodes = {}

        artifacts_dir = self._project_root / "artifacts"
        if not artifacts_dir.exists():
            return

        # Load all artifacts
        for artifact_file in artifacts_dir.rglob("*.json"):
            if "_meta" in str(artifact_file):
                continue

            try:
                data = json.loads(artifact_file.read_text(encoding="utf-8"))
                artifact_id = str(data.get("id", ""))
                artifact_type = str(data.get("artifact_type", ""))
                status = str(data.get("status", "draft"))

                if not artifact_id:
                    continue

                node = GraphNode(artifact_id, artifact_type, status)

                # Extract dependencies from payload
                payload = data.get("payload", {})
                if isinstance(payload, dict):
                    # Check common dependency fields
                    for dep_field in ["depends_on", "parent_artifact", "source_artifact"]:
                        dep_value = payload.get(dep_field)
                        if dep_value:
                            if isinstance(dep_value, list):
                                node.depends_on.extend(str(d) for d in dep_value)
                            else:
                                node.depends_on.append(str(dep_value))

                self._graph_nodes[artifact_id] = node

            except (json.JSONDecodeError, OSError):
                continue

        # Build reverse dependencies
        for node in self._graph_nodes.values():
            for dep_id in node.depends_on:
                if dep_id in self._graph_nodes:
                    self._graph_nodes[dep_id].dependents.append(node.artifact_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button press event.
        """
        if event.button.id == "refresh-btn":
            self._load_artifacts()
            self.notify("Graph refreshed")

        elif event.button.id == "ascii-btn":
            self._display_format = "ascii"
            self.refresh_graph()

        elif event.button.id == "mermaid-btn":
            self._display_format = "mermaid"
            self.refresh_graph()

        elif event.button.id == "export-btn":
            self._export_graph()

    def refresh_graph(self) -> None:
        """Refresh the graph display with current format."""
        try:
            panel = self.query_one(GraphPanel)
            renderer = GraphRenderer(self._graph_nodes)

            if self._display_format == "mermaid":
                content = renderer.render_mermaid()
            else:
                content = renderer.render()

            panel.set_content(content)
        except Exception:
            pass

    def _export_graph(self) -> None:
        """Export the graph to a file."""
        renderer = GraphRenderer(self._graph_nodes)

        if self._display_format == "mermaid":
            export_path = self._project_root / "artifact-graph.md"
            content = renderer.render_mermaid()
        else:
            export_path = self._project_root / "artifact-graph.txt"
            content = renderer.render()

        try:
            export_path.write_text(content, encoding="utf-8")
            self.notify(f"Exported to {export_path}")
        except OSError as e:
            self.notify(f"Export failed: {e}", severity="error")

    async def refresh_view(self) -> None:
        """Refresh the graph viewer."""
        self._load_artifacts()
        await self.remove_children()
        await self.mount_all(list(self.compose()))
