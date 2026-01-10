"""Unit tests for plan commands."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.commands.plan import app

runner = CliRunner()


class TestPlanCommandHelp:
    """Tests for plan command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Generate planning artifacts" in result.stdout

    def test_help_shows_project_subcommand(self) -> None:
        """--help should show project subcommand."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "project" in result.stdout

    def test_help_shows_architecture_subcommand(self) -> None:
        """--help should show architecture subcommand."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "architecture" in result.stdout

    def test_help_shows_tests_subcommand(self) -> None:
        """--help should show tests subcommand."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "tests" in result.stdout

    def test_help_shows_impl_subcommand(self) -> None:
        """--help should show impl subcommand."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "impl" in result.stdout

    def test_help_shows_refactor_subcommand(self) -> None:
        """--help should show refactor subcommand."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "refactor" in result.stdout


class TestProjectCommand:
    """Tests for plan project command."""

    def test_project_help(self) -> None:
        """plan project --help should show description."""
        result = runner.invoke(app, ["project", "--help"])
        assert result.exit_code == 0
        assert "ProjectPlan" in result.stdout

    def test_project_requires_init(self, tmp_path: Path) -> None:
        """plan project should fail if project not initialized."""
        result = runner.invoke(app, ["project", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    def test_project_dry_run(self, tmp_path: Path) -> None:
        """plan project --dry-run should show what would be created."""
        (tmp_path / ".project").mkdir()
        result = runner.invoke(
            app, ["project", "--path", str(tmp_path), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Dry run" in result.stdout or "Would create" in result.stdout


class TestArchitectureCommand:
    """Tests for plan architecture command."""

    def test_architecture_help(self) -> None:
        """plan architecture --help should show description."""
        result = runner.invoke(app, ["architecture", "--help"])
        assert result.exit_code == 0
        assert "ArchitecturePlan" in result.stdout

    def test_architecture_requires_init(self, tmp_path: Path) -> None:
        """plan architecture should fail if project not initialized."""
        result = runner.invoke(app, ["architecture", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestTestsCommand:
    """Tests for plan tests command."""

    def test_tests_help(self) -> None:
        """plan tests --help should show description."""
        result = runner.invoke(app, ["tests", "--help"])
        assert result.exit_code == 0
        assert "TestPlan" in result.stdout

    def test_tests_requires_init(self, tmp_path: Path) -> None:
        """plan tests should fail if project not initialized."""
        result = runner.invoke(app, ["tests", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestImplCommand:
    """Tests for plan impl command."""

    def test_impl_help(self) -> None:
        """plan impl --help should show description."""
        result = runner.invoke(app, ["impl", "--help"])
        assert result.exit_code == 0
        assert "ImplementationPlan" in result.stdout

    def test_impl_requires_target(self) -> None:
        """plan impl should require a target file argument."""
        result = runner.invoke(app, ["impl"])
        assert result.exit_code != 0
        # Missing required argument

    def test_impl_requires_init(self, tmp_path: Path) -> None:
        """plan impl should fail if project not initialized."""
        result = runner.invoke(
            app, ["impl", "src/main.py", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestRefactorCommand:
    """Tests for plan refactor command."""

    def test_refactor_help(self) -> None:
        """plan refactor --help should show description."""
        result = runner.invoke(app, ["refactor", "--help"])
        assert result.exit_code == 0
        assert "RefactorPlan" in result.stdout

    def test_refactor_requires_goal(self) -> None:
        """plan refactor should require a goal argument."""
        result = runner.invoke(app, ["refactor"])
        assert result.exit_code != 0
        # Missing required argument

    def test_refactor_requires_init(self, tmp_path: Path) -> None:
        """plan refactor should fail if project not initialized."""
        result = runner.invoke(
            app, ["refactor", "Extract interface", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestDryRunMode:
    """Tests for --dry-run mode across all commands."""

    def test_project_dry_run_does_not_create_files(self, tmp_path: Path) -> None:
        """plan project --dry-run should not create any files."""
        (tmp_path / ".project").mkdir()
        result = runner.invoke(
            app, ["project", "--path", str(tmp_path), "--dry-run"]
        )
        assert result.exit_code == 0
        assert not (tmp_path / "artifacts").exists()

    def test_architecture_dry_run_does_not_create_files(
        self, tmp_path: Path
    ) -> None:
        """plan architecture --dry-run should not create any files."""
        (tmp_path / ".project").mkdir()

        # Mock the phase check to allow architecture planning
        with patch(
            "rice_factor.entrypoints.cli.commands.plan._check_phase"
        ):
            result = runner.invoke(
                app, ["architecture", "--path", str(tmp_path), "--dry-run"]
            )

        assert result.exit_code == 0
        assert not (tmp_path / "artifacts").exists()


class TestPathOption:
    """Tests for --path option across all commands."""

    def test_project_uses_path_option(self, tmp_path: Path) -> None:
        """plan project should use the specified path."""
        (tmp_path / ".project").mkdir()
        result = runner.invoke(
            app, ["project", "--path", str(tmp_path), "--dry-run"]
        )
        # Should not error about the path
        assert result.exit_code == 0
