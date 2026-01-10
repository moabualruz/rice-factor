"""Unit tests for scaffold command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestScaffoldCommandHelp:
    """Tests for scaffold command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["scaffold", "--help"])
        assert result.exit_code == 0
        assert "Create file structure" in result.stdout

    def test_help_shows_dry_run_option(self) -> None:
        """--help should show --dry-run option."""
        result = runner.invoke(app, ["scaffold", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.stdout

    def test_help_shows_yes_option(self) -> None:
        """--help should show --yes option."""
        result = runner.invoke(app, ["scaffold", "--help"])
        assert result.exit_code == 0
        assert "--yes" in result.stdout

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["scaffold", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout


class TestScaffoldRequiresInit:
    """Tests for scaffold phase requirements."""

    def test_scaffold_requires_init(self, tmp_path: Path) -> None:
        """scaffold should fail if project not initialized."""
        result = runner.invoke(app, ["scaffold", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    def test_scaffold_requires_planning_phase(self, tmp_path: Path) -> None:
        """scaffold should require at least PLANNING phase."""
        # Create .project directory (INIT phase)
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["scaffold", "--path", str(tmp_path)])
        assert result.exit_code == 1
        # Should fail because we need PLANNING phase (ProjectPlan approved)
        assert "phase" in result.stdout.lower() or "cannot" in result.stdout.lower()


class TestScaffoldDryRun:
    """Tests for scaffold --dry-run mode."""

    def test_dry_run_does_not_create_files(self, tmp_path: Path) -> None:
        """--dry-run should not create any files."""
        (tmp_path / ".project").mkdir()

        # Mock phase check to allow execution
        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--dry-run"]
            )

        assert result.exit_code == 0
        # No src directory should be created
        assert not (tmp_path / "src").exists()

    def test_dry_run_shows_preview(self, tmp_path: Path) -> None:
        """--dry-run should show what would be created."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--dry-run"]
            )

        assert result.exit_code == 0
        # Should show files that would be created
        assert "create" in result.stdout.lower() or "would" in result.stdout.lower()

    def test_dry_run_does_not_save_artifact(self, tmp_path: Path) -> None:
        """--dry-run should not save artifact to filesystem."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--dry-run"]
            )

        assert result.exit_code == 0
        artifacts_dir = tmp_path / "artifacts"
        # Artifacts directory may not exist or should be empty
        if artifacts_dir.exists():
            assert len(list(artifacts_dir.iterdir())) == 0


class TestScaffoldConfirmation:
    """Tests for scaffold confirmation prompt."""

    def test_scaffold_prompts_for_confirmation(self, tmp_path: Path) -> None:
        """scaffold should prompt for confirmation."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            # Simulate user typing 'n' for no
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path)], input="n\n"
            )

        # Should exit cleanly when user declines
        assert result.exit_code == 0
        # No files should be created
        assert not (tmp_path / "src").exists()

    def test_scaffold_yes_skips_confirmation(self, tmp_path: Path) -> None:
        """--yes should skip confirmation prompt."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--yes"]
            )

        # Should complete without asking
        assert result.exit_code == 0
        # Files should be created
        assert (tmp_path / "src").exists()


class TestScaffoldExecution:
    """Tests for scaffold execution."""

    def test_scaffold_creates_files(self, tmp_path: Path) -> None:
        """scaffold should create files when confirmed."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        # Check that files were created (stub creates src/main.py etc)
        assert (tmp_path / "src" / "main.py").exists()
        assert (tmp_path / "src" / "__init__.py").exists()

    def test_scaffold_creates_test_files(self, tmp_path: Path) -> None:
        """scaffold should create test files."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        assert (tmp_path / "tests" / "test_main.py").exists()

    def test_scaffold_creates_readme(self, tmp_path: Path) -> None:
        """scaffold should create README.md."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        assert (tmp_path / "README.md").exists()

    def test_scaffold_files_have_todo_content(self, tmp_path: Path) -> None:
        """scaffold should create files with TODO comments."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        content = (tmp_path / "src" / "main.py").read_text()
        assert "TODO" in content

    def test_scaffold_creates_artifact(self, tmp_path: Path) -> None:
        """scaffold should create ScaffoldPlan artifact."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        artifacts_dir = tmp_path / "artifacts"
        assert artifacts_dir.exists()
        # Artifacts are stored in subdirectories (e.g., scaffold_plans/)
        artifact_files = list(artifacts_dir.glob("**/*.json"))
        assert len(artifact_files) >= 1


class TestScaffoldSkipsExisting:
    """Tests for scaffold handling of existing files."""

    def test_scaffold_skips_existing_files(self, tmp_path: Path) -> None:
        """scaffold should skip existing files."""
        (tmp_path / ".project").mkdir()
        (tmp_path / "src").mkdir(parents=True)
        existing_file = tmp_path / "src" / "main.py"
        existing_file.write_text("existing content")

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        # Existing content should be preserved
        assert existing_file.read_text() == "existing content"
        # Should mention skip in output
        assert "skip" in result.stdout.lower()

    def test_scaffold_warns_all_exist(self, tmp_path: Path) -> None:
        """scaffold should warn if all files already exist."""
        (tmp_path / ".project").mkdir()

        # Create all files the stub would create
        (tmp_path / "src").mkdir(parents=True)
        (tmp_path / "src" / "__init__.py").write_text("existing")
        (tmp_path / "src" / "main.py").write_text("existing")
        (tmp_path / "tests").mkdir(parents=True)
        (tmp_path / "tests" / "__init__.py").write_text("existing")
        (tmp_path / "tests" / "test_main.py").write_text("existing")
        (tmp_path / "README.md").write_text("existing")

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        # Should warn that no new files were created
        assert "no new files" in result.stdout.lower() or "already exist" in result.stdout.lower()


class TestScaffoldSummary:
    """Tests for scaffold summary output."""

    def test_scaffold_shows_summary(self, tmp_path: Path) -> None:
        """scaffold should show summary of created/skipped files."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        # Should show some form of summary
        assert "created" in result.stdout.lower() or "complete" in result.stdout.lower()
