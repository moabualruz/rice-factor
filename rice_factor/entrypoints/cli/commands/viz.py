"""Artifact visualization commands.

This module provides CLI commands for visualizing artifact dependencies:
- rice-factor viz: Generate dependency graphs from artifacts
"""

import json
from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel

from rice_factor.adapters.viz.graph_generator import (
    DependencyGraph,
    GraphGenerator,
)
from rice_factor.adapters.viz.mermaid_adapter import (
    MermaidAdapter,
    MermaidDiagramType,
)
from rice_factor.entrypoints.cli.utils import (
    console,
    error,
    handle_errors,
    info,
    success,
    warning,
)


def _find_project_root(path: Path | None) -> Path:
    """Find the project root directory.

    Args:
        path: Starting path to search from. If None, uses CWD.

    Returns:
        Path to the project root.
    """
    start = path or Path.cwd()

    # Walk up looking for .project/ or artifacts/
    current = start
    for _ in range(10):
        if (current / ".project").is_dir() or (current / "artifacts").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent

    return start


def _load_artifacts(artifacts_dir: Path) -> list[dict[str, Any]]:
    """Load all artifacts from a directory.

    Args:
        artifacts_dir: Directory containing artifact JSON files.

    Returns:
        List of artifact dictionaries.
    """
    artifacts: list[dict[str, Any]] = []

    if not artifacts_dir.exists():
        return artifacts

    for file_path in artifacts_dir.glob("*.json"):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            artifacts.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    return artifacts


def _load_artifact_by_type(
    artifacts_dir: Path, artifact_type: str
) -> dict[str, Any] | None:
    """Load the latest artifact of a specific type.

    Args:
        artifacts_dir: Directory containing artifact JSON files.
        artifact_type: Type of artifact to find.

    Returns:
        Artifact dictionary or None if not found.
    """
    type_map = {
        "project": "ProjectPlan",
        "test": "TestPlan",
        "scaffold": "ScaffoldPlan",
        "architecture": "ArchitecturePlan",
        "implementation": "ImplementationPlan",
        "refactor": "RefactorPlan",
    }

    target_type = type_map.get(artifact_type.lower())
    if not target_type:
        return None

    if not artifacts_dir.exists():
        return None

    # Find matching artifacts, sorted by modification time
    matching: list[tuple[Path, dict[str, Any]]] = []

    for file_path in artifacts_dir.glob("*.json"):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            if data.get("artifact_type") == target_type:
                matching.append((file_path, data))
        except (json.JSONDecodeError, OSError):
            continue

    if not matching:
        return None

    # Return most recently modified
    matching.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)
    return matching[0][1]


def _graph_to_json(graph: DependencyGraph) -> dict[str, Any]:
    """Convert a dependency graph to JSON-serializable format.

    Args:
        graph: Graph to convert.

    Returns:
        JSON-serializable dictionary.
    """
    return {
        "title": graph.title,
        "nodes": [
            {
                "id": n.id,
                "label": n.label,
                "type": n.node_type.value,
                "metadata": n.metadata,
            }
            for n in graph.nodes
        ],
        "edges": [
            {
                "source": e.source,
                "target": e.target,
                "type": e.edge_type.value,
                "label": e.label,
            }
            for e in graph.edges
        ],
    }


@handle_errors
def viz(
    artifact_type: str = typer.Argument(
        None,
        help="Artifact type to visualize (project, test, scaffold, architecture, all)",
    ),
    path: Path = typer.Option(
        None, "--path", "-p", help="Project root path. Defaults to current directory."
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="Output file path. If not specified, outputs to stdout."
    ),
    format: str = typer.Option(
        "mermaid",
        "--format",
        "-f",
        help="Output format: mermaid, json.",
    ),
    diagram_type: str = typer.Option(
        "flowchart",
        "--diagram",
        "-d",
        help="Mermaid diagram type: flowchart, class.",
    ),
    direction: str = typer.Option(
        "TD",
        "--direction",
        help="Graph direction: TD (top-down), BT (bottom-top), LR (left-right), RL (right-left).",
    ),
    wrap_markdown: bool = typer.Option(
        False, "--wrap", "-w", help="Wrap Mermaid output in markdown code block."
    ),
) -> None:
    """Generate dependency graphs from artifacts.

    Creates visual representations of artifact dependencies as Mermaid
    diagrams or JSON graphs.

    Examples:
        rice-factor viz project                # Visualize project plan
        rice-factor viz all                    # Visualize all artifacts
        rice-factor viz test --format json     # Output as JSON
        rice-factor viz project -o graph.md   # Save to file
    """
    project_root = _find_project_root(path)
    artifacts_dir = project_root / "artifacts"

    if not artifacts_dir.exists():
        warning(f"No artifacts directory found at {artifacts_dir}")
        info("Run 'rice-factor plan project' to create artifacts")
        raise typer.Exit(1)

    generator = GraphGenerator()
    graph: DependencyGraph | None = None

    # Handle different artifact types
    if artifact_type is None or artifact_type.lower() == "all":
        # Load all artifacts
        artifacts = _load_artifacts(artifacts_dir)
        if not artifacts:
            warning("No artifacts found")
            raise typer.Exit(1)
        graph = generator.from_artifacts(artifacts)

    elif artifact_type.lower() == "project":
        artifact = _load_artifact_by_type(artifacts_dir, "project")
        if not artifact:
            warning("No ProjectPlan artifact found")
            raise typer.Exit(1)
        payload = artifact.get("payload", {})
        graph = generator.from_project_plan(payload)

    elif artifact_type.lower() == "test":
        artifact = _load_artifact_by_type(artifacts_dir, "test")
        if not artifact:
            warning("No TestPlan artifact found")
            raise typer.Exit(1)
        payload = artifact.get("payload", {})
        graph = generator.from_test_plan(payload)

    elif artifact_type.lower() == "scaffold":
        artifact = _load_artifact_by_type(artifacts_dir, "scaffold")
        if not artifact:
            warning("No ScaffoldPlan artifact found")
            raise typer.Exit(1)
        payload = artifact.get("payload", {})
        graph = generator.from_scaffold_plan(payload)

    elif artifact_type.lower() in ("architecture", "arch"):
        artifact = _load_artifact_by_type(artifacts_dir, "architecture")
        if not artifact:
            warning("No ArchitecturePlan artifact found")
            raise typer.Exit(1)
        payload = artifact.get("payload", {})
        graph = generator.from_architecture_plan(payload)

    else:
        error(f"Unknown artifact type: {artifact_type}")
        info("Valid types: project, test, scaffold, architecture, all")
        raise typer.Exit(1)

    if graph is None or (not graph.nodes and not graph.edges):
        warning("Generated graph is empty")
        raise typer.Exit(1)

    # Generate output
    if format.lower() == "json":
        content = json.dumps(_graph_to_json(graph), indent=2)
    elif format.lower() == "mermaid":
        # Determine mermaid diagram type
        if diagram_type.lower() == "class":
            mermaid_type = MermaidDiagramType.CLASS
        else:
            mermaid_type = MermaidDiagramType.FLOWCHART

        adapter = MermaidAdapter(diagram_type=mermaid_type, direction=direction)
        content = adapter.export(graph)

        if wrap_markdown:
            content = f"```mermaid\n{content}\n```"
    else:
        error(f"Unknown format: {format}. Use 'mermaid' or 'json'.")
        raise typer.Exit(1)

    # Output
    if output:
        output.write_text(content, encoding="utf-8")
        success(f"Generated visualization at {output}")
        info(f"Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}")
    else:
        console.print()
        console.print(
            Panel(
                f"[bold]Artifact Visualization[/bold]\n\n"
                f"Type: {artifact_type or 'all'}\n"
                f"Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}",
                border_style="blue",
            )
        )
        console.print()
        console.print(content)
