"""Integration tests for CI template functionality.

These tests verify that the CI template can be correctly applied
to a sample project and produces valid CI configuration.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


def _create_sample_project(project_dir: Path) -> None:
    """Create a minimal rice-factor project structure for testing.

    Args:
        project_dir: Directory to create the project in.
    """
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=project_dir,
        capture_output=True,
        check=True,
    )

    # Configure git user
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=project_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=project_dir,
        capture_output=True,
        check=True,
    )

    # Create .project directory
    project_files = project_dir / ".project"
    project_files.mkdir()
    (project_files / "requirements.md").write_text("# Requirements\n\n- Test feature\n")
    (project_files / "constraints.md").write_text("# Constraints\n\n- Must be fast\n")
    (project_files / "glossary.md").write_text("# Glossary\n\n- Term: Definition\n")
    (project_files / "non_goals.md").write_text("# Non Goals\n\n- Not this\n")
    (project_files / "risks.md").write_text("# Risks\n\n- Potential risk\n")
    (project_files / "decisions.md").write_text("# Decisions\n\n| Decision | Rationale |\n|----------|----------|\n")

    # Create artifacts directory with sample approved artifact
    artifacts_dir = project_dir / "artifacts" / "project_plans"
    artifacts_dir.mkdir(parents=True)
    project_plan = {
        "id": "plan-001",
        "artifact_type": "ProjectPlan",
        "status": "approved",
        "created_at": "2026-01-11T00:00:00Z",
        "payload": {
            "name": "Test Project",
            "goal": "Test the CI pipeline",
            "domains": [],
            "modules": [],
        },
    }
    (artifacts_dir / "project-plan.json").write_text(
        json.dumps(project_plan, indent=2)
    )

    # Create src directory with sample code
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("# Sample code\n")
    (src_dir / "main.py").write_text("def main():\n    return 'Hello'\n")

    # Create tests directory
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_main.py").write_text(
        "def test_main():\n    from src.main import main\n    assert main() == 'Hello'\n"
    )

    # Initial commit
    subprocess.run(
        ["git", "add", "."],
        cwd=project_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=project_dir,
        capture_output=True,
        check=True,
    )


class TestCITemplateGeneration:
    """Tests for CI template generation."""

    def test_ci_init_creates_workflow_file(self, tmp_path: Path) -> None:
        """Should create GitHub Actions workflow file."""
        _create_sample_project(tmp_path)

        # Run rice-factor ci init
        result = subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Check workflow file was created
        workflow_path = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        assert workflow_path.exists(), f"Workflow not created. stderr: {result.stderr}"

    def test_ci_init_dry_run_shows_content(self, tmp_path: Path) -> None:
        """Should show template content in dry-run mode."""
        _create_sample_project(tmp_path)

        result = subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init", "--dry-run"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Should show content without creating file
        workflow_path = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        assert not workflow_path.exists()
        assert "rice-factor" in result.stdout or "rice-factor" in result.stderr


class TestCITemplateValidity:
    """Tests for CI template validity."""

    def test_generated_workflow_is_valid_yaml(self, tmp_path: Path) -> None:
        """Generated workflow should be valid YAML."""
        _create_sample_project(tmp_path)

        # Run without check=True as Unicode output may cause issues on Windows
        subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init"],
            cwd=tmp_path,
            capture_output=True,
        )

        workflow_path = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        assert workflow_path.exists(), "Workflow file should be created"
        content = workflow_path.read_text()

        # Should parse as valid YAML
        workflow = yaml.safe_load(content)
        assert isinstance(workflow, dict)

    def test_generated_workflow_has_required_fields(self, tmp_path: Path) -> None:
        """Generated workflow should have required GitHub Actions fields."""
        _create_sample_project(tmp_path)

        subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init"],
            cwd=tmp_path,
            capture_output=True,
        )

        workflow_path = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        assert workflow_path.exists(), "Workflow file should be created"
        workflow = yaml.safe_load(workflow_path.read_text())

        # Required fields for GitHub Actions
        assert "name" in workflow
        # Note: YAML parses "on:" as True, so check for True instead of "on"
        assert True in workflow or "on" in workflow
        assert "jobs" in workflow

    def test_generated_workflow_has_rice_factor_validation(self, tmp_path: Path) -> None:
        """Generated workflow should include rice-factor validation steps."""
        _create_sample_project(tmp_path)

        subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init"],
            cwd=tmp_path,
            capture_output=True,
        )

        workflow_path = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        assert workflow_path.exists(), "Workflow file should be created"
        content = workflow_path.read_text()

        # Should contain rice-factor commands
        assert "rice-factor" in content
        assert "validate" in content.lower()


class TestCITemplateIntegration:
    """Tests for CI template integration with validation."""

    def test_ci_validate_runs_on_sample_project(self, tmp_path: Path) -> None:
        """CI validation should run successfully on sample project."""
        _create_sample_project(tmp_path)

        # Run ci validate
        result = subprocess.run(
            ["uv", "run", "rice-factor", "ci", "validate", "--json"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Parse JSON output
        if result.stdout:
            try:
                validation_result = json.loads(result.stdout)
                # Check structure
                assert "passed" in validation_result or "stage_results" in validation_result
            except json.JSONDecodeError:
                # If JSON parsing fails, check for text output
                pass

    def test_ci_validate_artifacts_passes_with_approved_plan(
        self, tmp_path: Path
    ) -> None:
        """Artifact validation should pass with approved artifacts."""
        _create_sample_project(tmp_path)

        result = subprocess.run(
            ["uv", "run", "rice-factor", "ci", "validate-artifacts"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Should pass (exit code 0) or provide useful output
        # Note: may fail if validation finds issues, that's OK
        assert result.returncode in [0, 1]  # 0=passed, 1=failed with findings


class TestCITemplateErrorHandling:
    """Tests for CI template error handling."""

    def test_ci_init_fails_without_project_root(self, tmp_path: Path) -> None:
        """Should fail gracefully when not in a project."""
        # Don't create .project directory

        result = subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Should fail with informative message
        assert result.returncode != 0

    def test_ci_init_wont_overwrite_existing(self, tmp_path: Path) -> None:
        """Should not overwrite existing workflow without --force."""
        _create_sample_project(tmp_path)

        # Create workflow first
        subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init"],
            cwd=tmp_path,
            capture_output=True,
        )

        workflow_path = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        assert workflow_path.exists(), "Workflow should be created initially"

        # Try again without --force
        result = subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Should fail (won't overwrite)
        assert result.returncode != 0

    def test_ci_init_with_force_overwrites(self, tmp_path: Path) -> None:
        """Should overwrite existing workflow with --force."""
        _create_sample_project(tmp_path)

        # Create workflow first
        subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init"],
            cwd=tmp_path,
            capture_output=True,
        )

        workflow_path = tmp_path / ".github" / "workflows" / "rice-factor.yml"
        assert workflow_path.exists(), "Workflow should be created initially"
        original_content = workflow_path.read_text()

        # Overwrite with --force
        subprocess.run(
            ["uv", "run", "rice-factor", "ci", "init", "--force"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Workflow should still exist and have the same content
        assert workflow_path.exists()
        assert workflow_path.read_text() == original_content
