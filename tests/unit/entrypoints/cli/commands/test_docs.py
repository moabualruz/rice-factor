"""Unit tests for docs CLI command."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rice_factor.adapters.docs.doc_generator import (
    DocumentationSpec,
    DocSection,
)
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestDocsCommandHelp:
    """Tests for docs command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["docs", "--help"])
        assert result.exit_code == 0
        assert "documentation" in result.stdout.lower()

    def test_help_shows_options(self) -> None:
        """--help should show all options."""
        result = runner.invoke(app, ["docs", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout
        assert "--output" in result.stdout
        assert "--style" in result.stdout
        assert "--format" in result.stdout


class TestDocsCommand:
    """Tests for docs command."""

    def test_docs_no_artifacts_dir(self, tmp_path: Path) -> None:
        """Test docs when no artifacts directory exists."""
        result = runner.invoke(app, ["docs", "project", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "no artifacts" in result.stdout.lower()

    def test_docs_no_artifact_type(self, tmp_path: Path) -> None:
        """Test docs when no artifact type specified."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        result = runner.invoke(app, ["docs", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "specify" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.docs.DocGenerator")
    def test_docs_project(self, mock_generator_class: MagicMock, tmp_path: Path) -> None:
        """Test docs with project artifact type."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create project plan artifact
        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test-project", "description": "A test project"},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_spec = DocumentationSpec(
            title="Test Project",
            description="A test project",
            metadata={},
            sections=[
                DocSection(title="Overview", content="Project overview", level=1, subsections=[]),
            ],
        )
        mock_generator.from_project_plan.return_value = mock_spec

        result = runner.invoke(app, ["docs", "project", "--path", str(tmp_path)])

        assert result.exit_code == 0
        mock_generator.from_project_plan.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.docs.DocGenerator")
    def test_docs_test(self, mock_generator_class: MagicMock, tmp_path: Path) -> None:
        """Test docs with test artifact type."""
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

        mock_spec = DocumentationSpec(
            title="Test Plan",
            description="Test plan documentation",
            metadata={},
            sections=[
                DocSection(title="Test Suites", content="List of suites", level=1, subsections=[]),
            ],
        )
        mock_generator.from_test_plan.return_value = mock_spec

        result = runner.invoke(app, ["docs", "test", "--path", str(tmp_path)])

        assert result.exit_code == 0
        mock_generator.from_test_plan.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.docs.DocGenerator")
    def test_docs_architecture(self, mock_generator_class: MagicMock, tmp_path: Path) -> None:
        """Test docs with architecture artifact type."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        arch_plan = {
            "id": "arch-001",
            "artifact_type": "ArchitecturePlan",
            "status": "approved",
            "payload": {"layers": [], "components": []},
        }
        (artifacts_dir / "arch.json").write_text(json.dumps(arch_plan))

        mock_spec = DocumentationSpec(
            title="Architecture",
            description="Architecture documentation",
            metadata={},
            sections=[
                DocSection(title="Layers", content="System layers", level=1, subsections=[]),
            ],
        )
        mock_generator.from_architecture_plan.return_value = mock_spec

        result = runner.invoke(app, ["docs", "architecture", "--path", str(tmp_path)])

        assert result.exit_code == 0
        mock_generator.from_architecture_plan.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.docs.DocGenerator")
    def test_docs_json_output(self, mock_generator_class: MagicMock, tmp_path: Path) -> None:
        """Test docs with --format json."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test"},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_spec = DocumentationSpec(
            title="Test",
            description="Description",
            metadata={"version": "1.0"},
            sections=[
                DocSection(title="Overview", content="Content", level=1, subsections=[]),
            ],
        )
        mock_generator.from_project_plan.return_value = mock_spec

        result = runner.invoke(
            app, ["docs", "project", "--path", str(tmp_path), "--format", "json"]
        )

        assert result.exit_code == 0
        # Parse the output, skipping any Rich panel output
        lines = result.stdout.strip().split('\n')
        # Find the JSON part (starts with '{')
        json_start = next(i for i, line in enumerate(lines) if line.strip().startswith('{'))
        json_str = '\n'.join(lines[json_start:])
        data = json.loads(json_str)
        assert "title" in data
        assert "sections" in data

    @patch("rice_factor.entrypoints.cli.commands.docs.DocGenerator")
    @patch("rice_factor.entrypoints.cli.commands.docs.MarkdownAdapter")
    def test_docs_markdown_output(
        self, mock_adapter_class: MagicMock, mock_generator_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test docs with --format markdown."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.export.return_value = "# Test Project\n\nOverview content"

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test"},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_spec = DocumentationSpec(
            title="Test Project",
            description="",
            metadata={},
            sections=[],
        )
        mock_generator.from_project_plan.return_value = mock_spec

        result = runner.invoke(
            app, ["docs", "project", "--path", str(tmp_path), "--format", "markdown"]
        )

        assert result.exit_code == 0
        assert "#" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.docs.DocGenerator")
    @patch("rice_factor.entrypoints.cli.commands.docs.MarkdownAdapter")
    def test_docs_style_github(
        self, mock_adapter_class: MagicMock, mock_generator_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test docs with --style github."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.export.return_value = "# Doc"

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test"},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_spec = DocumentationSpec(
            title="Doc", description="", metadata={}, sections=[]
        )
        mock_generator.from_project_plan.return_value = mock_spec

        result = runner.invoke(
            app, ["docs", "project", "--path", str(tmp_path), "--style", "github"]
        )

        assert result.exit_code == 0
        # Verify adapter was called with github style
        from rice_factor.adapters.docs.markdown_adapter import MarkdownStyle
        mock_adapter_class.assert_called_once()
        call_kwargs = mock_adapter_class.call_args.kwargs
        assert call_kwargs.get("style") == MarkdownStyle.GITHUB

    @patch("rice_factor.entrypoints.cli.commands.docs.DocGenerator")
    @patch("rice_factor.entrypoints.cli.commands.docs.MarkdownAdapter")
    def test_docs_output_file(
        self, mock_adapter_class: MagicMock, mock_generator_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test docs with --output to file."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.export.return_value = "# Test Project\n\nContent here."

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        project_plan = {
            "id": "proj-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "payload": {"name": "test"},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_spec = DocumentationSpec(
            title="Test Project",
            description="",
            metadata={},
            sections=[],
        )
        mock_generator.from_project_plan.return_value = mock_spec

        output_file = tmp_path / "README.md"
        result = runner.invoke(
            app, ["docs", "project", "--path", str(tmp_path), "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()
        assert "#" in output_file.read_text()

    def test_docs_invalid_artifact_type(self, tmp_path: Path) -> None:
        """Test docs with invalid artifact type."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        result = runner.invoke(app, ["docs", "invalid", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "unknown" in result.stdout.lower()

    def test_docs_artifact_not_found(self, tmp_path: Path) -> None:
        """Test docs when requested artifact not found."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        result = runner.invoke(app, ["docs", "project", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "no" in result.stdout.lower() and "found" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.docs.DocGenerator")
    def test_docs_refactor(self, mock_generator_class: MagicMock, tmp_path: Path) -> None:
        """Test docs with refactor artifact type."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        refactor_plan = {
            "id": "refactor-001",
            "artifact_type": "RefactorPlan",
            "status": "approved",
            "payload": {"goal": "Extract interface"},
        }
        (artifacts_dir / "refactor.json").write_text(json.dumps(refactor_plan))

        mock_spec = DocumentationSpec(
            title="Refactor Plan",
            description="Refactoring documentation",
            metadata={},
            sections=[
                DocSection(title="Goal", content="Extract interface", level=1, subsections=[]),
            ],
        )
        mock_generator.from_refactor_plan.return_value = mock_spec

        result = runner.invoke(app, ["docs", "refactor", "--path", str(tmp_path)])

        assert result.exit_code == 0
        mock_generator.from_refactor_plan.assert_called_once()


class TestDocsFindProjectRoot:
    """Tests for project root detection in docs command."""

    @patch("rice_factor.entrypoints.cli.commands.docs.DocGenerator")
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
            "payload": {"name": "test"},
        }
        (artifacts_dir / "project.json").write_text(json.dumps(project_plan))

        mock_spec = DocumentationSpec(
            title="Test",
            description="",
            metadata={},
            sections=[DocSection(title="Sec", content="", level=1, subsections=[])],
        )
        mock_generator.from_project_plan.return_value = mock_spec

        # Run from subdirectory
        result = runner.invoke(app, ["docs", "project", "--path", str(subdir)])

        # Should find project root and load artifact
        assert result.exit_code == 0


class TestDocsHelperFunctions:
    """Tests for docs helper functions."""

    def test_spec_to_json(self) -> None:
        """Test DocumentationSpec to JSON conversion."""
        from rice_factor.entrypoints.cli.commands.docs import _spec_to_json

        spec = DocumentationSpec(
            title="Test",
            description="Desc",
            metadata={"key": "value"},
            sections=[
                DocSection(
                    title="Section 1",
                    content="Content 1",
                    level=1,
                    subsections=[
                        DocSection(
                            title="Subsection",
                            content="Sub content",
                            level=2,
                            subsections=[],
                        ),
                    ],
                ),
            ],
        )

        result = _spec_to_json(spec)

        assert result["title"] == "Test"
        assert result["description"] == "Desc"
        assert result["metadata"]["key"] == "value"
        assert len(result["sections"]) == 1
        assert result["sections"][0]["title"] == "Section 1"
        assert len(result["sections"][0]["subsections"]) == 1
