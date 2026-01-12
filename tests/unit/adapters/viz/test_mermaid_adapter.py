"""Tests for MermaidAdapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from rice_factor.adapters.viz import (
    GraphGenerator,
    MermaidAdapter,
    MermaidDiagramType,
)
from rice_factor.adapters.viz.graph_generator import (
    DependencyGraph,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
)
from rice_factor.adapters.viz.mermaid_adapter import (
    generate_artifact_diagram,
    generate_project_diagram,
)


class TestMermaidAdapter:
    """Tests for MermaidAdapter."""

    def test_create_adapter(self) -> None:
        """Test creating a Mermaid adapter."""
        adapter = MermaidAdapter()
        assert adapter.diagram_type == MermaidDiagramType.FLOWCHART
        assert adapter.direction == "TD"

    def test_create_with_options(self) -> None:
        """Test creating adapter with custom options."""
        adapter = MermaidAdapter(
            diagram_type=MermaidDiagramType.GRAPH,
            direction="LR",
        )
        assert adapter.diagram_type == MermaidDiagramType.GRAPH
        assert adapter.direction == "LR"

    def test_export_empty_graph(self) -> None:
        """Test exporting an empty graph."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()

        output = adapter.export(graph)

        assert "flowchart TD" in output

    def test_export_with_nodes(self) -> None:
        """Test exporting graph with nodes."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="n1", label="Node 1", node_type=NodeType.ARTIFACT))
        graph.add_node(GraphNode(id="n2", label="Node 2", node_type=NodeType.MODULE))

        output = adapter.export(graph)

        assert "n1[Node 1]" in output
        assert "n2(Node 2)" in output

    def test_export_with_edges(self) -> None:
        """Test exporting graph with edges."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="n1", label="N1", node_type=NodeType.ARTIFACT))
        graph.add_node(GraphNode(id="n2", label="N2", node_type=NodeType.ARTIFACT))
        graph.add_edge(GraphEdge(source="n1", target="n2", edge_type=EdgeType.DEPENDS_ON))

        output = adapter.export(graph)

        assert "n1 --> n2" in output

    def test_export_edge_with_label(self) -> None:
        """Test exporting edge with label."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="n1", label="N1", node_type=NodeType.ARTIFACT))
        graph.add_node(GraphNode(id="n2", label="N2", node_type=NodeType.ARTIFACT))
        graph.add_edge(
            GraphEdge(
                source="n1",
                target="n2",
                edge_type=EdgeType.DEPENDS_ON,
                label="requires",
            )
        )

        output = adapter.export(graph)

        assert "|requires|" in output

    def test_export_different_edge_types(self) -> None:
        """Test exporting different edge types."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="n1", label="N1", node_type=NodeType.ARTIFACT))
        graph.add_node(GraphNode(id="n2", label="N2", node_type=NodeType.MODULE))
        graph.add_node(GraphNode(id="n3", label="N3", node_type=NodeType.TEST))

        graph.add_edge(GraphEdge(source="n1", target="n2", edge_type=EdgeType.DEPENDS_ON))
        graph.add_edge(GraphEdge(source="n2", target="n1", edge_type=EdgeType.BELONGS_TO))
        graph.add_edge(GraphEdge(source="n3", target="n2", edge_type=EdgeType.TESTS))

        output = adapter.export(graph)

        assert "-->" in output  # DEPENDS_ON
        assert "-.->" in output  # BELONGS_TO
        assert "==>" in output  # TESTS

    def test_export_with_title(self) -> None:
        """Test exporting graph with title."""
        adapter = MermaidAdapter()
        graph = DependencyGraph(title="My Graph")
        graph.add_node(GraphNode(id="n1", label="N1", node_type=NodeType.ARTIFACT))

        output = adapter.export(graph)

        assert "subgraph" in output
        assert "My Graph" in output

    def test_export_class_diagram(self) -> None:
        """Test exporting as class diagram."""
        adapter = MermaidAdapter(diagram_type=MermaidDiagramType.CLASS)
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="n1", label="Class1", node_type=NodeType.MODULE))
        graph.add_node(GraphNode(id="n2", label="Class2", node_type=NodeType.MODULE))
        graph.add_edge(GraphEdge(source="n1", target="n2", edge_type=EdgeType.DEPENDS_ON))

        output = adapter.export(graph)

        assert "classDiagram" in output
        assert "class n1" in output

    def test_sanitize_id_colons(self) -> None:
        """Test sanitizing IDs with colons."""
        adapter = MermaidAdapter()
        sanitized = adapter._sanitize_id("domain:core")
        assert ":" not in sanitized
        assert sanitized == "domain_core"

    def test_sanitize_id_slashes(self) -> None:
        """Test sanitizing IDs with slashes."""
        adapter = MermaidAdapter()
        sanitized = adapter._sanitize_id("file:src/main.py")
        assert "/" not in sanitized

    def test_export_to_file(self, tmp_path: Path) -> None:
        """Test exporting to file."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="n1", label="N1", node_type=NodeType.ARTIFACT))

        output_file = tmp_path / "diagram.md"
        adapter.export_to_file(graph, str(output_file))

        content = output_file.read_text()
        assert "```mermaid" in content
        assert "```" in content

    def test_export_to_file_no_code_block(self, tmp_path: Path) -> None:
        """Test exporting to file without code block."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="n1", label="N1", node_type=NodeType.ARTIFACT))

        output_file = tmp_path / "diagram.mmd"
        adapter.export_to_file(graph, str(output_file), wrap_in_code_block=False)

        content = output_file.read_text()
        assert "```mermaid" not in content

    def test_export_multiple(self) -> None:
        """Test exporting multiple graphs."""
        adapter = MermaidAdapter()

        graph1 = DependencyGraph()
        graph1.add_node(GraphNode(id="n1", label="G1", node_type=NodeType.ARTIFACT))

        graph2 = DependencyGraph()
        graph2.add_node(GraphNode(id="n2", label="G2", node_type=NodeType.MODULE))

        output = adapter.export_multiple([
            ("Graph 1", graph1),
            ("Graph 2", graph2),
        ])

        assert "## Graph 1" in output
        assert "## Graph 2" in output
        assert output.count("```mermaid") == 2


class TestMermaidDiagramTypes:
    """Tests for MermaidDiagramType enum."""

    def test_all_types(self) -> None:
        """Test all diagram types."""
        assert MermaidDiagramType.FLOWCHART.value == "flowchart"
        assert MermaidDiagramType.GRAPH.value == "graph"
        assert MermaidDiagramType.CLASS.value == "classDiagram"
        assert MermaidDiagramType.SEQUENCE.value == "sequenceDiagram"
        assert MermaidDiagramType.STATE.value == "stateDiagram-v2"
        assert MermaidDiagramType.ER.value == "erDiagram"


class TestNodeShapes:
    """Tests for node shape rendering."""

    def test_artifact_shape(self) -> None:
        """Test artifact uses square brackets."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="a1", label="Artifact", node_type=NodeType.ARTIFACT))

        output = adapter.export(graph)
        assert "a1[Artifact]" in output

    def test_module_shape(self) -> None:
        """Test module uses rounded brackets."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="m1", label="Module", node_type=NodeType.MODULE))

        output = adapter.export(graph)
        assert "m1(Module)" in output

    def test_domain_shape(self) -> None:
        """Test domain uses hexagon."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="d1", label="Domain", node_type=NodeType.DOMAIN))

        output = adapter.export(graph)
        assert "d1{{Domain}}" in output

    def test_file_shape(self) -> None:
        """Test file uses parallelogram."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="f1", label="File", node_type=NodeType.FILE))

        output = adapter.export(graph)
        assert "f1[/File/]" in output

    def test_test_shape(self) -> None:
        """Test test uses stadium."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="t1", label="Test", node_type=NodeType.TEST))

        output = adapter.export(graph)
        assert "t1([Test])" in output


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_artifact_diagram(self) -> None:
        """Test generating artifact diagram."""
        artifacts = [
            {"id": "a1", "artifact_type": "ProjectPlan", "depends_on": []},
            {"id": "a2", "artifact_type": "TestPlan", "depends_on": ["a1"]},
        ]

        output = generate_artifact_diagram(artifacts)

        assert "flowchart" in output
        assert "a1" in output
        assert "a2" in output
        assert "-->" in output

    def test_generate_project_diagram(self) -> None:
        """Test generating project diagram."""
        project_plan = {
            "domains": [{"name": "core", "responsibility": "Business"}],
            "modules": [{"name": "auth", "domain": "core"}],
        }

        output = generate_project_diagram(project_plan)

        assert "flowchart LR" in output
        assert "core" in output
        assert "auth" in output


class TestStyleGeneration:
    """Tests for style generation."""

    def test_generates_class_defs(self) -> None:
        """Test that class definitions are generated."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="a1", label="A1", node_type=NodeType.ARTIFACT))
        graph.add_node(GraphNode(id="m1", label="M1", node_type=NodeType.MODULE))

        output = adapter.export(graph)

        assert "classDef class_artifact" in output
        assert "classDef class_module" in output

    def test_applies_classes_to_nodes(self) -> None:
        """Test that classes are applied to nodes."""
        adapter = MermaidAdapter()
        graph = DependencyGraph()
        graph.add_node(GraphNode(id="a1", label="A1", node_type=NodeType.ARTIFACT))
        graph.add_node(GraphNode(id="a2", label="A2", node_type=NodeType.ARTIFACT))

        output = adapter.export(graph)

        assert "class a1,a2 class_artifact" in output or "class a2,a1 class_artifact" in output
