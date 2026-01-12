"""Tests for GraphGenerator."""

from __future__ import annotations

import pytest

from rice_factor.adapters.viz import (
    GraphEdge,
    GraphGenerator,
    GraphNode,
)
from rice_factor.adapters.viz.graph_generator import (
    DependencyGraph,
    EdgeType,
    NodeType,
)


class TestGraphNode:
    """Tests for GraphNode."""

    def test_create_node(self) -> None:
        """Test creating a graph node."""
        node = GraphNode(
            id="test-1",
            label="Test Node",
            node_type=NodeType.ARTIFACT,
        )
        assert node.id == "test-1"
        assert node.label == "Test Node"
        assert node.node_type == NodeType.ARTIFACT
        assert node.metadata == {}

    def test_node_with_metadata(self) -> None:
        """Test creating node with metadata."""
        node = GraphNode(
            id="test-1",
            label="Test",
            node_type=NodeType.MODULE,
            metadata={"status": "draft"},
        )
        assert node.metadata["status"] == "draft"


class TestGraphEdge:
    """Tests for GraphEdge."""

    def test_create_edge(self) -> None:
        """Test creating a graph edge."""
        edge = GraphEdge(
            source="node-1",
            target="node-2",
            edge_type=EdgeType.DEPENDS_ON,
        )
        assert edge.source == "node-1"
        assert edge.target == "node-2"
        assert edge.edge_type == EdgeType.DEPENDS_ON
        assert edge.label is None

    def test_edge_with_label(self) -> None:
        """Test creating edge with label."""
        edge = GraphEdge(
            source="node-1",
            target="node-2",
            edge_type=EdgeType.TESTS,
            label="validates",
        )
        assert edge.label == "validates"


class TestDependencyGraph:
    """Tests for DependencyGraph."""

    def test_create_empty_graph(self) -> None:
        """Test creating an empty graph."""
        graph = DependencyGraph()
        assert graph.nodes == []
        assert graph.edges == []
        assert graph.title is None

    def test_add_node(self) -> None:
        """Test adding a node."""
        graph = DependencyGraph()
        node = GraphNode(id="n1", label="Node 1", node_type=NodeType.ARTIFACT)
        graph.add_node(node)
        assert len(graph.nodes) == 1

    def test_add_duplicate_node(self) -> None:
        """Test adding duplicate node is ignored."""
        graph = DependencyGraph()
        node1 = GraphNode(id="n1", label="Node 1", node_type=NodeType.ARTIFACT)
        node2 = GraphNode(id="n1", label="Node 1 Updated", node_type=NodeType.MODULE)

        graph.add_node(node1)
        graph.add_node(node2)

        assert len(graph.nodes) == 1
        assert graph.nodes[0].label == "Node 1"  # First one kept

    def test_add_edge(self) -> None:
        """Test adding an edge."""
        graph = DependencyGraph()
        edge = GraphEdge(source="n1", target="n2", edge_type=EdgeType.DEPENDS_ON)
        graph.add_edge(edge)
        assert len(graph.edges) == 1

    def test_get_node(self) -> None:
        """Test getting a node by ID."""
        graph = DependencyGraph()
        node = GraphNode(id="n1", label="Node 1", node_type=NodeType.ARTIFACT)
        graph.add_node(node)

        found = graph.get_node("n1")
        assert found is not None
        assert found.label == "Node 1"

    def test_get_node_not_found(self) -> None:
        """Test getting nonexistent node."""
        graph = DependencyGraph()
        assert graph.get_node("nonexistent") is None

    def test_get_edges_from(self) -> None:
        """Test getting edges from a node."""
        graph = DependencyGraph()
        edge1 = GraphEdge(source="n1", target="n2", edge_type=EdgeType.DEPENDS_ON)
        edge2 = GraphEdge(source="n1", target="n3", edge_type=EdgeType.DEPENDS_ON)
        edge3 = GraphEdge(source="n2", target="n3", edge_type=EdgeType.DEPENDS_ON)

        graph.add_edge(edge1)
        graph.add_edge(edge2)
        graph.add_edge(edge3)

        edges = graph.get_edges_from("n1")
        assert len(edges) == 2

    def test_get_edges_to(self) -> None:
        """Test getting edges to a node."""
        graph = DependencyGraph()
        edge1 = GraphEdge(source="n1", target="n3", edge_type=EdgeType.DEPENDS_ON)
        edge2 = GraphEdge(source="n2", target="n3", edge_type=EdgeType.DEPENDS_ON)

        graph.add_edge(edge1)
        graph.add_edge(edge2)

        edges = graph.get_edges_to("n3")
        assert len(edges) == 2


class TestGraphGenerator:
    """Tests for GraphGenerator."""

    def test_from_artifacts(self) -> None:
        """Test generating graph from artifacts."""
        generator = GraphGenerator()

        artifacts = [
            {"id": "art-1", "artifact_type": "ProjectPlan", "status": "approved", "depends_on": []},
            {"id": "art-2", "artifact_type": "TestPlan", "status": "draft", "depends_on": ["art-1"]},
        ]

        graph = generator.from_artifacts(artifacts)

        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.edges[0].source == "art-2"
        assert graph.edges[0].target == "art-1"

    def test_from_artifacts_multiple_deps(self) -> None:
        """Test graph with multiple dependencies."""
        generator = GraphGenerator()

        artifacts = [
            {"id": "a1", "artifact_type": "ProjectPlan", "depends_on": []},
            {"id": "a2", "artifact_type": "ArchPlan", "depends_on": ["a1"]},
            {"id": "a3", "artifact_type": "TestPlan", "depends_on": ["a1", "a2"]},
        ]

        graph = generator.from_artifacts(artifacts)

        assert len(graph.nodes) == 3
        assert len(graph.edges) == 3

    def test_from_project_plan(self) -> None:
        """Test generating graph from project plan."""
        generator = GraphGenerator()

        project_plan = {
            "domains": [
                {"name": "core", "responsibility": "Business logic"},
                {"name": "infra", "responsibility": "Infrastructure"},
            ],
            "modules": [
                {"name": "auth", "domain": "core"},
                {"name": "db", "domain": "infra"},
            ],
        }

        graph = generator.from_project_plan(project_plan)

        assert len(graph.nodes) == 4  # 2 domains + 2 modules
        assert len(graph.edges) == 2  # module->domain links

    def test_from_test_plan(self) -> None:
        """Test generating graph from test plan."""
        generator = GraphGenerator()

        test_plan = {
            "tests": [
                {"id": "test-1", "target": "auth.login", "assertions": ["works"]},
                {"id": "test-2", "target": "auth.login", "assertions": ["handles errors"]},
                {"id": "test-3", "target": "auth.logout", "assertions": ["clears session"]},
            ]
        }

        graph = generator.from_test_plan(test_plan)

        # 3 tests + 2 unique targets
        assert len(graph.nodes) == 5
        assert len(graph.edges) == 3

    def test_from_scaffold_plan(self) -> None:
        """Test generating graph from scaffold plan."""
        generator = GraphGenerator()

        scaffold_plan = {
            "files": [
                {"path": "src/main.py", "kind": "source"},
                {"path": "src/auth/login.py", "kind": "source"},
                {"path": "tests/test_main.py", "kind": "test"},
            ]
        }

        graph = generator.from_scaffold_plan(scaffold_plan)

        # 3 files + directories (src, src/auth, tests)
        assert len(graph.nodes) >= 3

    def test_merge_graphs(self) -> None:
        """Test merging multiple graphs."""
        generator = GraphGenerator()

        graph1 = DependencyGraph()
        graph1.add_node(GraphNode(id="n1", label="N1", node_type=NodeType.ARTIFACT))

        graph2 = DependencyGraph()
        graph2.add_node(GraphNode(id="n2", label="N2", node_type=NodeType.MODULE))

        merged = generator.merge_graphs(graph1, graph2)

        assert len(merged.nodes) == 2

    def test_filter_by_type(self) -> None:
        """Test filtering graph by node type."""
        generator = GraphGenerator()

        graph = DependencyGraph()
        graph.add_node(GraphNode(id="a1", label="Art", node_type=NodeType.ARTIFACT))
        graph.add_node(GraphNode(id="m1", label="Mod", node_type=NodeType.MODULE))
        graph.add_node(GraphNode(id="t1", label="Test", node_type=NodeType.TEST))
        graph.add_edge(GraphEdge(source="a1", target="m1", edge_type=EdgeType.DEPENDS_ON))
        graph.add_edge(GraphEdge(source="t1", target="m1", edge_type=EdgeType.TESTS))

        filtered = generator.filter_by_type(graph, [NodeType.ARTIFACT, NodeType.MODULE])

        assert len(filtered.nodes) == 2
        assert len(filtered.edges) == 1  # Only a1->m1, not t1->m1


class TestNodeTypes:
    """Tests for NodeType enum."""

    def test_all_node_types(self) -> None:
        """Test all node types exist."""
        assert NodeType.ARTIFACT.value == "artifact"
        assert NodeType.MODULE.value == "module"
        assert NodeType.DOMAIN.value == "domain"
        assert NodeType.FILE.value == "file"
        assert NodeType.TEST.value == "test"


class TestEdgeTypes:
    """Tests for EdgeType enum."""

    def test_all_edge_types(self) -> None:
        """Test all edge types exist."""
        assert EdgeType.DEPENDS_ON.value == "depends_on"
        assert EdgeType.BELONGS_TO.value == "belongs_to"
        assert EdgeType.TESTS.value == "tests"
        assert EdgeType.IMPLEMENTS.value == "implements"
