"""Unit tests for CI commands."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from rice_factor.entrypoints.cli.commands.ci import app

runner = CliRunner()


class TestCICommandHelp:
    """Tests for CI command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "CI" in result.stdout or "validation" in result.stdout

    def test_help_shows_validate_command(self) -> None:
        """--help should list validate command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "validate" in result.stdout

    def test_help_shows_init_command(self) -> None:
        """--help should list init command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.stdout


class TestCIInitCommand:
    """Tests for ci init command."""

    def test_init_creates_workflow_file(self, tmp_path: Path) -> None:
        """init should create GitHub Actions workflow file."""
        result = runner.invoke(app, ["init", "--path", str(tmp_path)])

        assert result.exit_code == 0
        workflow_file = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        assert workflow_file.exists()

    def test_init_workflow_contains_rice_factor_commands(self, tmp_path: Path) -> None:
        """Generated workflow should contain rice-factor commands."""
        runner.invoke(app, ["init", "--path", str(tmp_path)])

        workflow_file = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        content = workflow_file.read_text()

        assert "rice-factor" in content
        assert "ci validate" in content

    def test_init_fails_if_workflow_exists(self, tmp_path: Path) -> None:
        """init should fail if workflow file already exists."""
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "rice-factor.yml").write_text("existing")

        result = runner.invoke(app, ["init", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_init_force_overwrites_existing(self, tmp_path: Path) -> None:
        """init with --force should overwrite existing workflow."""
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "rice-factor.yml").write_text("old content")

        result = runner.invoke(app, ["init", "--path", str(tmp_path), "--force"])

        assert result.exit_code == 0
        content = (workflows_dir / "rice-factor.yml").read_text()
        assert "old content" not in content

    def test_init_dry_run_does_not_create_file(self, tmp_path: Path) -> None:
        """init with --dry-run should not create files."""
        result = runner.invoke(app, ["init", "--path", str(tmp_path), "--dry-run"])

        assert result.exit_code == 0
        workflow_file = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        assert not workflow_file.exists()

    def test_init_dry_run_shows_template(self, tmp_path: Path) -> None:
        """init with --dry-run should show template content."""
        result = runner.invoke(app, ["init", "--path", str(tmp_path), "--dry-run"])

        assert result.exit_code == 0
        assert "Would create" in result.stdout
        assert "rice-factor" in result.stdout


class TestCIValidateCommand:
    """Tests for ci validate command."""

    def test_validate_help_shows_options(self) -> None:
        """validate --help should show options."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout
        assert "--json" in result.stdout

    def test_validate_passes_on_empty_project(self, tmp_path: Path) -> None:
        """validate should pass when no artifacts exist."""
        result = runner.invoke(app, ["validate", "--path", str(tmp_path)])

        # No artifacts = passes (nothing to validate)
        assert result.exit_code == 0

    def test_validate_json_output(self, tmp_path: Path) -> None:
        """validate --json should output valid JSON."""
        result = runner.invoke(app, ["validate", "--path", str(tmp_path), "--json"])

        assert result.exit_code == 0
        # Output should be valid JSON
        data = json.loads(result.stdout)
        assert "passed" in data
        assert data["passed"] is True


class TestCIValidateArtifactsCommand:
    """Tests for ci validate-artifacts command."""

    def test_validate_artifacts_passes_on_empty(self, tmp_path: Path) -> None:
        """validate-artifacts should pass when no artifacts exist."""
        result = runner.invoke(app, ["validate-artifacts", "--path", str(tmp_path)])

        assert result.exit_code == 0


class TestCIValidateApprovalsCommand:
    """Tests for ci validate-approvals command."""

    def test_validate_approvals_passes_on_empty(self, tmp_path: Path) -> None:
        """validate-approvals should pass when no artifacts exist."""
        result = runner.invoke(app, ["validate-approvals", "--path", str(tmp_path)])

        assert result.exit_code == 0


class TestCIValidateInvariantsCommand:
    """Tests for ci validate-invariants command."""

    def test_validate_invariants_passes_on_empty(self, tmp_path: Path) -> None:
        """validate-invariants should pass when no locked artifacts exist."""
        result = runner.invoke(app, ["validate-invariants", "--path", str(tmp_path)])

        assert result.exit_code == 0


class TestCIValidateAuditCommand:
    """Tests for ci validate-audit command."""

    def test_validate_audit_passes_on_empty(self, tmp_path: Path) -> None:
        """validate-audit should pass when no audit directory exists."""
        result = runner.invoke(app, ["validate-audit", "--path", str(tmp_path)])

        assert result.exit_code == 0


class TestCIFindProjectRoot:
    """Tests for project root detection."""

    def test_finds_project_root_from_subdirectory(self, tmp_path: Path) -> None:
        """Should find .project/ in parent directory."""
        # Create project structure
        (tmp_path / ".project").mkdir()
        subdir = tmp_path / "src" / "module"
        subdir.mkdir(parents=True)

        # Run from subdirectory
        result = runner.invoke(app, ["validate", "--path", str(subdir)])

        # Should find project root and pass
        assert result.exit_code == 0
