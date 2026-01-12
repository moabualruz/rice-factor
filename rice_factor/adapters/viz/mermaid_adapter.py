"""Mermaid diagram adapter for graph export.

Converts dependency graphs to Mermaid diagram syntax.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from rice_factor.adapters.viz.graph_generator import (
    DependencyGraph,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
)


class MermaidDiagramType(Enum):
    """Types of Mermaid diagrams."""

    FLOWCHART = "flowchart"
    GRAPH = "graph"
    CLASS = "classDiagram"
    SEQUENCE = "sequenceDiagram"
    STATE = "stateDiagram-v2"
    ER = "erDiagram"


class MermaidAdapter:
    """Converts dependency graphs to Mermaid diagram syntax.

    Generates Mermaid markdown that can be rendered in documentation,
    GitHub, or visualization tools.
    """

    # Node shape mapping
    NODE_SHAPES: dict[NodeType, tuple[str, str]] = {
        NodeType.ARTIFACT: ("[", "]"),  # Square
        NodeType.MODULE: ("(", ")"),  # Rounded
        NodeType.DOMAIN: ("{{", "}}"),  # Hexagon
        NodeType.FILE: ("[/", "/]"),  # Parallelogram
        NodeType.TEST: ("([", "])"),  # Stadium
    }

    # Edge arrow mapping
    EDGE_ARROWS: dict[EdgeType, str] = {
        EdgeType.DEPENDS_ON: "-->",
        EdgeType.BELONGS_TO: "-.->",
        EdgeType.TESTS: "==>",
        EdgeType.IMPLEMENTS: "--o",
    }

    # Node style classes
    NODE_STYLES: dict[NodeType, str] = {
        NodeType.ARTIFACT: "fill:#e1f5fe,stroke:#01579b",
        NodeType.MODULE: "fill:#fff3e0,stroke:#e65100",
        NodeType.DOMAIN: "fill:#f3e5f5,stroke:#7b1fa2",
        NodeType.FILE: "fill:#e8f5e9,stroke:#2e7d32",
        NodeType.TEST: "fill:#fce4ec,stroke:#c2185b",
    }

    def __init__(
        self,
        diagram_type: MermaidDiagramType = MermaidDiagramType.FLOWCHART,
        direction: str = "TD",
    ) -> None:
        """Initialize the Mermaid adapter.

        Args:
            diagram_type: Type of Mermaid diagram to generate.
            direction: Graph direction (TD, BT, LR, RL).
        """
        self.diagram_type = diagram_type
        self.direction = direction

    def export(self, graph: DependencyGraph) -> str:
        """Export a dependency graph to Mermaid syntax.

        Args:
            graph: Graph to export.

        Returns:
            Mermaid diagram string.
        """
        if self.diagram_type == MermaidDiagramType.CLASS:
            return self._export_class_diagram(graph)
        return self._export_flowchart(graph)

    def _export_flowchart(self, graph: DependencyGraph) -> str:
        """Export as flowchart/graph.

        Args:
            graph: Graph to export.

        Returns:
            Mermaid flowchart string.
        """
        lines: list[str] = []

        # Header
        header = f"{self.diagram_type.value} {self.direction}"
        lines.append(header)

        # Title as subgraph if present
        if graph.title:
            lines.append(f"    subgraph {self._sanitize_id(graph.title)}[{graph.title}]")
            indent = "        "
        else:
            indent = "    "

        # Nodes
        for node in graph.nodes:
            node_line = self._format_node(node, indent)
            lines.append(node_line)

        # Edges
        for edge in graph.edges:
            edge_line = self._format_edge(edge, indent)
            lines.append(edge_line)

        # Close subgraph
        if graph.title:
            lines.append("    end")

        # Style definitions
        style_lines = self._generate_styles(graph)
        if style_lines:
            lines.extend(style_lines)

        return "\n".join(lines)

    def _export_class_diagram(self, graph: DependencyGraph) -> str:
        """Export as class diagram.

        Args:
            graph: Graph to export.

        Returns:
            Mermaid class diagram string.
        """
        lines: list[str] = [self.diagram_type.value]

        # Classes (nodes)
        for node in graph.nodes:
            class_name = self._sanitize_id(node.id)
            lines.append(f"    class {class_name} {{")
            lines.append(f"        +{node.node_type.value} type")
            if node.metadata:
                for key, value in node.metadata.items():
                    if isinstance(value, str):
                        lines.append(f"        +String {key}")
            lines.append("    }")

        # Relationships (edges)
        for edge in graph.edges:
            source = self._sanitize_id(edge.source)
            target = self._sanitize_id(edge.target)

            if edge.edge_type == EdgeType.DEPENDS_ON:
                lines.append(f"    {source} --> {target}")
            elif edge.edge_type == EdgeType.BELONGS_TO:
                lines.append(f"    {target} o-- {source}")
            elif edge.edge_type == EdgeType.IMPLEMENTS:
                lines.append(f"    {source} ..|> {target}")
            else:
                lines.append(f"    {source} -- {target}")

        return "\n".join(lines)

    def _format_node(self, node: GraphNode, indent: str = "    ") -> str:
        """Format a node as Mermaid syntax.

        Args:
            node: Node to format.
            indent: Line indentation.

        Returns:
            Formatted node string.
        """
        node_id = self._sanitize_id(node.id)
        shape_start, shape_end = self.NODE_SHAPES.get(
            node.node_type, ("[", "]")
        )
        return f"{indent}{node_id}{shape_start}{node.label}{shape_end}"

    def _format_edge(self, edge: GraphEdge, indent: str = "    ") -> str:
        """Format an edge as Mermaid syntax.

        Args:
            edge: Edge to format.
            indent: Line indentation.

        Returns:
            Formatted edge string.
        """
        source = self._sanitize_id(edge.source)
        target = self._sanitize_id(edge.target)
        arrow = self.EDGE_ARROWS.get(edge.edge_type, "-->")

        if edge.label:
            return f"{indent}{source} {arrow}|{edge.label}| {target}"
        return f"{indent}{source} {arrow} {target}"

    def _generate_styles(self, graph: DependencyGraph) -> list[str]:
        """Generate style definitions for the graph.

        Args:
            graph: Graph to style.

        Returns:
            List of style definition lines.
        """
        lines: list[str] = []
        styled_types: set[NodeType] = set()

        for node in graph.nodes:
            if node.node_type not in styled_types:
                styled_types.add(node.node_type)
                style = self.NODE_STYLES.get(node.node_type)
                if style:
                    class_name = f"class_{node.node_type.value}"
                    lines.append(f"    classDef {class_name} {style}")

        # Apply classes to nodes
        for node_type in styled_types:
            class_name = f"class_{node_type.value}"
            node_ids = [
                self._sanitize_id(n.id)
                for n in graph.nodes
                if n.node_type == node_type
            ]
            if node_ids:
                lines.append(f"    class {','.join(node_ids)} {class_name}")

        return lines

    def _sanitize_id(self, node_id: str) -> str:
        """Sanitize a node ID for Mermaid.

        Args:
            node_id: Original node ID.

        Returns:
            Sanitized ID safe for Mermaid.
        """
        # Replace problematic characters
        sanitized = node_id.replace(":", "_")
        sanitized = sanitized.replace("/", "_")
        sanitized = sanitized.replace("-", "_")
        sanitized = sanitized.replace(".", "_")
        sanitized = sanitized.replace(" ", "_")
        return sanitized

    def export_to_file(
        self,
        graph: DependencyGraph,
        filepath: str,
        wrap_in_code_block: bool = True,
    ) -> None:
        """Export a graph to a file.

        Args:
            graph: Graph to export.
            filepath: Output file path.
            wrap_in_code_block: Whether to wrap in markdown code block.
        """
        content = self.export(graph)

        if wrap_in_code_block:
            content = f"```mermaid\n{content}\n```"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def export_multiple(
        self,
        graphs: list[tuple[str, DependencyGraph]],
    ) -> str:
        """Export multiple graphs as a single document.

        Args:
            graphs: List of (title, graph) tuples.

        Returns:
            Combined Mermaid document with sections.
        """
        sections: list[str] = []

        for title, graph in graphs:
            section = f"## {title}\n\n```mermaid\n{self.export(graph)}\n```"
            sections.append(section)

        return "\n\n".join(sections)


def generate_artifact_diagram(artifacts: list[dict[str, Any]]) -> str:
    """Convenience function to generate an artifact dependency diagram.

    Args:
        artifacts: List of artifact dictionaries.

    Returns:
        Mermaid diagram string.
    """
    from rice_factor.adapters.viz.graph_generator import GraphGenerator

    generator = GraphGenerator()
    adapter = MermaidAdapter()

    graph = generator.from_artifacts(artifacts)
    return adapter.export(graph)


def generate_project_diagram(project_plan: dict[str, Any]) -> str:
    """Convenience function to generate a project structure diagram.

    Args:
        project_plan: ProjectPlanPayload as dictionary.

    Returns:
        Mermaid diagram string.
    """
    from rice_factor.adapters.viz.graph_generator import GraphGenerator

    generator = GraphGenerator()
    adapter = MermaidAdapter(direction="LR")

    graph = generator.from_project_plan(project_plan)
    return adapter.export(graph)
