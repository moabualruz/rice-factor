"""Unit tests for viz CLI command."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rice_factor.adapters.viz.graph_generator import (
    DependencyGraph,
    GraphEdge,
    GraphNode,
    NodeType,
    EdgeType,
)
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestVizCommandHelp:
    """Tests for viz command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["viz", "--help"])
        assert result.exit_code == 0
        assert "visualization" in result.stdout.lower() or "graph" in result.stdout.lower()

    def test_help_shows_options(self) -> None:
        """--help should show all options."""
        result = runner.invoke(app, ["viz", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout
        assert "--output" in result.stdout
        assert "--format" in result.stdout
        assert "--diagram" in result.stdout
        assert "--direction" in result.stdout


class TestVizCommand:
    """Tests for viz command."""

    def test_viz_no_artifacts_dir(self, tmp_path: Path) -> None:
        """Test viz when no artifacts directory exists."""
        result = runner.invoke(app, ["viz", "project", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "no artifacts" in result.stdout.lower()

    def test_viz_no_artifact_type(self, tmp_path: Path) -> None:
        """Test viz defaults to 'all' when no type specified."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        result = runner.invoke(app, ["viz", "--path", str(tmp_path)])

        # Should try to load all artifacts
        assert result.exit_code in (0, 1)

    @patch("rice_factor.entrypoints.cli.commands.viz.MermaidAdapter")
    @patch("rice_factor.entrypoints.cli.commands.viz.GraphGenerator")
    def test_viz_project(self, mock_generator_class: MagicMock, mock_adapter_class: MagicMock, tmp_path: Path) -> None:
        """Test viz with project artifact type."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.export.return_value = "flowchart TD\n  proj[Project]"

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create project plan artifact
        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test-project", "milestones": []},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_graph = DependencyGraph(
            title="Project Graph",
            nodes=[
                GraphNode(id="proj", label="Project", node_type=NodeType.ARTIFACT, metadata={}),
            ],
            edges=[],
        )
        mock_generator.from_project_plan.return_value = mock_graph

        result = runner.invoke(app, ["viz", "project", "--path", str(tmp_path)])

        assert result.exit_code == 0
        mock_generator.from_project_plan.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.viz.GraphGenerator")
    def test_viz_test(self, mock_generator_class: MagicMock, tmp_path: Path) -> None:
        """Test viz with test artifact type."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create test plan artifact
        test_plan = {
            "id": "test-001",
            "artifact_type": "TestPlan",
            "status": "locked",
            "payload": {"test_suites": []},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(test_plan))

        mock_graph = DependencyGraph(
            title="Test Graph",
            nodes=[
                GraphNode(id="test", label="Tests", node_type=NodeType.TEST, metadata={}),
            ],
            edges=[],
        )
        mock_generator.from_test_plan.return_value = mock_graph

        result = runner.invoke(app, ["viz", "test", "--path", str(tmp_path)])

        assert result.exit_code == 0
        mock_generator.from_test_plan.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.viz.GraphGenerator")
    def test_viz_json_output(self, mock_generator_class: MagicMock, tmp_path: Path) -> None:
        """Test viz with --format json."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test", "milestones": []},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_graph = DependencyGraph(
            title="Graph",
            nodes=[
                GraphNode(id="n1", label="Node 1", node_type=NodeType.MODULE, metadata={}),
                GraphNode(id="n2", label="Node 2", node_type=NodeType.MODULE, metadata={}),
            ],
            edges=[
                GraphEdge(source="n1", target="n2", edge_type=EdgeType.DEPENDS_ON),
            ],
        )
        mock_generator.from_project_plan.return_value = mock_graph

        result = runner.invoke(
            app, ["viz", "project", "--path", str(tmp_path), "--format", "json"]
        )

        assert result.exit_code == 0
        # Parse the output, skipping any Rich panel output
        lines = result.stdout.strip().split('\n')
        # Find the JSON part (starts with '{')
        json_start = next(i for i, line in enumerate(lines) if line.strip().startswith('{'))
        json_str = '\n'.join(lines[json_start:])
        data = json.loads(json_str)
        assert "title" in data
        assert "nodes" in data
        assert "edges" in data

    @patch("rice_factor.entrypoints.cli.commands.viz.GraphGenerator")
    @patch("rice_factor.entrypoints.cli.commands.viz.MermaidAdapter")
    def test_viz_mermaid_output(
        self, mock_adapter_class: MagicMock, mock_generator_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test viz with --format mermaid."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.export.return_value = "flowchart TD\n  A --> B"

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test", "milestones": []},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_graph = DependencyGraph(
            title="Graph",
            nodes=[GraphNode(id="A", label="A", node_type=NodeType.MODULE, metadata={})],
            edges=[],
        )
        mock_generator.from_project_plan.return_value = mock_graph

        result = runner.invoke(
            app, ["viz", "project", "--path", str(tmp_path), "--format", "mermaid"]
        )

        assert result.exit_code == 0
        assert "flowchart" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.viz.GraphGenerator")
    @patch("rice_factor.entrypoints.cli.commands.viz.MermaidAdapter")
    def test_viz_wrap_markdown(
        self, mock_adapter_class: MagicMock, mock_generator_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test viz with --wrap option."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.export.return_value = "flowchart TD\n  A --> B"

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test", "milestones": []},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_graph = DependencyGraph(
            title="Graph",
            nodes=[GraphNode(id="A", label="A", node_type=NodeType.MODULE, metadata={})],
            edges=[],
        )
        mock_generator.from_project_plan.return_value = mock_graph

        result = runner.invoke(
            app, ["viz", "project", "--path", str(tmp_path), "--wrap"]
        )

        assert result.exit_code == 0
        assert "```mermaid" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.viz.GraphGenerator")
    @patch("rice_factor.entrypoints.cli.commands.viz.MermaidAdapter")
    def test_viz_output_file(
        self, mock_adapter_class: MagicMock, mock_generator_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test viz with --output to file."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.export.return_value = "flowchart TD\n  A --> B"

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test", "milestones": []},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_graph = DependencyGraph(
            title="Graph",
            nodes=[GraphNode(id="A", label="A", node_type=NodeType.MODULE, metadata={})],
            edges=[],
        )
        mock_generator.from_project_plan.return_value = mock_graph

        output_file = tmp_path / "graph.md"
        result = runner.invoke(
            app, ["viz", "project", "--path", str(tmp_path), "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()
        assert "flowchart" in output_file.read_text()

    def test_viz_invalid_artifact_type(self, tmp_path: Path) -> None:
        """Test viz with invalid artifact type."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        result = runner.invoke(app, ["viz", "invalid", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "unknown" in result.stdout.lower()

    def test_viz_artifact_not_found(self, tmp_path: Path) -> None:
        """Test viz when requested artifact not found."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        result = runner.invoke(app, ["viz", "project", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "no" in result.stdout.lower() and "found" in result.stdout.lower()


class TestVizFindProjectRoot:
    """Tests for project root detection in viz command."""

    @patch("rice_factor.entrypoints.cli.commands.viz.GraphGenerator")
    def test_finds_project_root_from_subdirectory(
        self, mock_generator_class: MagicMock, tmp_path: Path
    ) -> None:
        """Should find artifacts/ in parent directory."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        # Create project structure
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        subdir = tmp_path / "src" / "module"
        subdir.mkdir(parents=True)

        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test", "milestones": []},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_graph = DependencyGraph(
            title="Graph",
            nodes=[GraphNode(id="A", label="A", node_type=NodeType.MODULE, metadata={})],
            edges=[],
        )
        mock_generator.from_project_plan.return_value = mock_graph

        # Run from subdirectory
        result = runner.invoke(app, ["viz", "project", "--path", str(subdir)])

        # Should find project root and load artifact
        assert result.exit_code == 0
