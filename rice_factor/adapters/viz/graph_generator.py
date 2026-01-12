"""Graph generator for artifact dependency visualization.

Generates graph representations of artifact dependencies for visualization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(Enum):
    """Types of nodes in the dependency graph."""

    ARTIFACT = "artifact"
    MODULE = "module"
    DOMAIN = "domain"
    FILE = "file"
    TEST = "test"


class EdgeType(Enum):
    """Types of edges in the dependency graph."""

    DEPENDS_ON = "depends_on"
    BELONGS_TO = "belongs_to"
    TESTS = "tests"
    IMPLEMENTS = "implements"


@dataclass
class GraphNode:
    """A node in the dependency graph.

    Attributes:
        id: Unique identifier for the node.
        label: Display label for the node.
        node_type: Type of the node.
        metadata: Additional metadata.
    """

    id: str
    label: str
    node_type: NodeType
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """An edge in the dependency graph.

    Attributes:
        source: Source node ID.
        target: Target node ID.
        edge_type: Type of the relationship.
        label: Optional edge label.
    """

    source: str
    target: str
    edge_type: EdgeType
    label: str | None = None


@dataclass
class DependencyGraph:
    """A complete dependency graph.

    Attributes:
        nodes: List of nodes in the graph.
        edges: List of edges in the graph.
        title: Optional title for the graph.
    """

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    title: str | None = None

    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph.

        Args:
            node: Node to add.
        """
        if not any(n.id == node.id for n in self.nodes):
            self.nodes.append(node)

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph.

        Args:
            edge: Edge to add.
        """
        self.edges.append(edge)

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID.

        Args:
            node_id: Node ID to find.

        Returns:
            Node if found, None otherwise.
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edges_from(self, node_id: str) -> list[GraphEdge]:
        """Get all edges originating from a node.

        Args:
            node_id: Source node ID.

        Returns:
            List of edges from the node.
        """
        return [e for e in self.edges if e.source == node_id]

    def get_edges_to(self, node_id: str) -> list[GraphEdge]:
        """Get all edges targeting a node.

        Args:
            node_id: Target node ID.

        Returns:
            List of edges to the node.
        """
        return [e for e in self.edges if e.target == node_id]


class GraphGenerator:
    """Generates dependency graphs from artifacts.

    Creates graph representations of artifact dependencies
    that can be exported to various formats.
    """

    def __init__(self) -> None:
        """Initialize the graph generator."""
        pass

    def from_artifacts(self, artifacts: list[dict[str, Any]]) -> DependencyGraph:
        """Generate a graph from a list of artifacts.

        Args:
            artifacts: List of artifact dictionaries with id, type, depends_on.

        Returns:
            Dependency graph representing the artifacts.
        """
        graph = DependencyGraph(title="Artifact Dependencies")

        # Add artifact nodes
        for artifact in artifacts:
            artifact_id = artifact.get("id", "")
            artifact_type = artifact.get("artifact_type", "Unknown")
            status = artifact.get("status", "unknown")

            node = GraphNode(
                id=artifact_id,
                label=f"{artifact_type}",
                node_type=NodeType.ARTIFACT,
                metadata={"status": status, "type": artifact_type},
            )
            graph.add_node(node)

        # Add dependency edges
        for artifact in artifacts:
            artifact_id = artifact.get("id", "")
            depends_on = artifact.get("depends_on", [])

            for dep_id in depends_on:
                edge = GraphEdge(
                    source=artifact_id,
                    target=dep_id,
                    edge_type=EdgeType.DEPENDS_ON,
                )
                graph.add_edge(edge)

        return graph

    def from_project_plan(self, project_plan: dict[str, Any]) -> DependencyGraph:
        """Generate a graph from a project plan payload.

        Args:
            project_plan: ProjectPlanPayload as dictionary.

        Returns:
            Dependency graph showing domains and modules.
        """
        graph = DependencyGraph(title="Project Structure")

        # Add domain nodes
        domains = project_plan.get("domains", [])
        for domain in domains:
            domain_name = domain.get("name", "")
            node = GraphNode(
                id=f"domain:{domain_name}",
                label=domain_name,
                node_type=NodeType.DOMAIN,
                metadata={"responsibility": domain.get("responsibility", "")},
            )
            graph.add_node(node)

        # Add module nodes and link to domains
        modules = project_plan.get("modules", [])
        for module in modules:
            module_name = module.get("name", "")
            module_domain = module.get("domain", "")

            node = GraphNode(
                id=f"module:{module_name}",
                label=module_name,
                node_type=NodeType.MODULE,
                metadata={"domain": module_domain},
            )
            graph.add_node(node)

            # Link to domain
            if module_domain:
                edge = GraphEdge(
                    source=f"module:{module_name}",
                    target=f"domain:{module_domain}",
                    edge_type=EdgeType.BELONGS_TO,
                )
                graph.add_edge(edge)

        return graph

    def from_test_plan(self, test_plan: dict[str, Any]) -> DependencyGraph:
        """Generate a graph from a test plan payload.

        Args:
            test_plan: TestPlanPayload as dictionary.

        Returns:
            Dependency graph showing tests and their targets.
        """
        graph = DependencyGraph(title="Test Coverage")

        tests = test_plan.get("tests", [])
        targets: set[str] = set()

        for test in tests:
            test_id = test.get("id", "")
            target = test.get("target", "")

            # Add test node
            test_node = GraphNode(
                id=f"test:{test_id}",
                label=test_id,
                node_type=NodeType.TEST,
                metadata={"assertions": test.get("assertions", [])},
            )
            graph.add_node(test_node)

            # Track unique targets
            if target:
                targets.add(target)

                # Link test to target
                edge = GraphEdge(
                    source=f"test:{test_id}",
                    target=f"target:{target}",
                    edge_type=EdgeType.TESTS,
                )
                graph.add_edge(edge)

        # Add target nodes
        for target in targets:
            target_node = GraphNode(
                id=f"target:{target}",
                label=target,
                node_type=NodeType.MODULE,
            )
            graph.add_node(target_node)

        return graph

    def from_scaffold_plan(self, scaffold_plan: dict[str, Any]) -> DependencyGraph:
        """Generate a graph from a scaffold plan payload.

        Args:
            scaffold_plan: ScaffoldPlanPayload as dictionary.

        Returns:
            Dependency graph showing file structure.
        """
        graph = DependencyGraph(title="File Structure")

        files = scaffold_plan.get("files", [])
        directories: set[str] = set()

        for file_entry in files:
            file_path = file_entry.get("path", "")
            file_kind = file_entry.get("kind", "source")

            # Extract directory
            if "/" in file_path:
                directory = "/".join(file_path.split("/")[:-1])
                directories.add(directory)

            # Add file node
            file_node = GraphNode(
                id=f"file:{file_path}",
                label=file_path.split("/")[-1],
                node_type=NodeType.FILE,
                metadata={"path": file_path, "kind": file_kind},
            )
            graph.add_node(file_node)

        # Add directory nodes and relationships
        for directory in sorted(directories):
            dir_node = GraphNode(
                id=f"dir:{directory}",
                label=directory,
                node_type=NodeType.DOMAIN,
                metadata={"type": "directory"},
            )
            graph.add_node(dir_node)

        # Link files to directories
        for file_entry in files:
            file_path = file_entry.get("path", "")
            if "/" in file_path:
                directory = "/".join(file_path.split("/")[:-1])
                edge = GraphEdge(
                    source=f"file:{file_path}",
                    target=f"dir:{directory}",
                    edge_type=EdgeType.BELONGS_TO,
                )
                graph.add_edge(edge)

        return graph

    def merge_graphs(self, *graphs: DependencyGraph) -> DependencyGraph:
        """Merge multiple graphs into one.

        Args:
            *graphs: Graphs to merge.

        Returns:
            Merged dependency graph.
        """
        merged = DependencyGraph(title="Merged Graph")

        for graph in graphs:
            for node in graph.nodes:
                merged.add_node(node)
            for edge in graph.edges:
                merged.add_edge(edge)

        return merged

    def filter_by_type(
        self, graph: DependencyGraph, node_types: list[NodeType]
    ) -> DependencyGraph:
        """Filter a graph to only include nodes of specific types.

        Args:
            graph: Source graph.
            node_types: Types of nodes to include.

        Returns:
            Filtered dependency graph.
        """
        filtered = DependencyGraph(title=graph.title)

        # Filter nodes
        included_ids: set[str] = set()
        for node in graph.nodes:
            if node.node_type in node_types:
                filtered.add_node(node)
                included_ids.add(node.id)

        # Filter edges (only if both endpoints are included)
        for edge in graph.edges:
            if edge.source in included_ids and edge.target in included_ids:
                filtered.add_edge(edge)

        return filtered
