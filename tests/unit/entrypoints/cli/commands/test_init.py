"""Unit tests for init command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.commands.init import app

runner = CliRunner()


class TestInitCommandHelp:
    """Tests for init command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Initialize" in result.stdout or "initialize" in result.stdout

    def test_help_shows_force_option(self) -> None:
        """--help should show --force option."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--force" in result.stdout

    def test_help_shows_dry_run_option(self) -> None:
        """--help should show --dry-run option."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.stdout

    def test_help_shows_skip_questionnaire_option(self) -> None:
        """--help should show --skip-questionnaire option."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--skip-questionnaire" in result.stdout

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout


class TestInitCommandOnFreshDirectory:
    """Tests for init command on fresh directory."""

    def test_creates_project_dir_with_skip_questionnaire(
        self, tmp_path: Path
    ) -> None:
        """init with --skip-questionnaire should create .project/ dir."""
        with patch(
            "rice_factor.entrypoints.cli.commands.init._display_welcome"
        ):
            result = runner.invoke(
                app, ["--path", str(tmp_path), "--skip-questionnaire"]
            )

        # Should succeed (exit code 0)
        assert result.exit_code == 0
        assert (tmp_path / ".project").exists()

    def test_creates_all_template_files(self, tmp_path: Path) -> None:
        """init should create all 5 template files."""
        with patch(
            "rice_factor.entrypoints.cli.commands.init._display_welcome"
        ):
            result = runner.invoke(
                app, ["--path", str(tmp_path), "--skip-questionnaire"]
            )

        assert result.exit_code == 0
        expected_files = [
            "requirements.md",
            "constraints.md",
            "glossary.md",
            "non_goals.md",
            "risks.md",
        ]
        for filename in expected_files:
            assert (tmp_path / ".project" / filename).exists()


class TestInitCommandOnExistingProject:
    """Tests for init command on existing project."""

    def test_fails_when_already_initialized(self, tmp_path: Path) -> None:
        """init should fail if .project/ already exists."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["--path", str(tmp_path), "--skip-questionnaire"]
        )

        assert result.exit_code == 1
        assert "already initialized" in result.stdout

    def test_suggests_force_flag(self, tmp_path: Path) -> None:
        """init should suggest --force when already initialized."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["--path", str(tmp_path), "--skip-questionnaire"]
        )

        assert "--force" in result.stdout

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        """init with --force should overwrite existing .project/."""
        (tmp_path / ".project").mkdir()
        (tmp_path / ".project" / "requirements.md").write_text("old content")

        with patch(
            "rice_factor.entrypoints.cli.commands.init._display_welcome"
        ):
            result = runner.invoke(
                app,
                ["--path", str(tmp_path), "--force", "--skip-questionnaire"],
            )

        assert result.exit_code == 0
        content = (tmp_path / ".project" / "requirements.md").read_text()
        assert "old content" not in content


class TestInitCommandDryRun:
    """Tests for init command dry-run mode."""

    def test_dry_run_does_not_create_files(self, tmp_path: Path) -> None:
        """--dry-run should not create any files."""
        with patch(
            "rice_factor.entrypoints.cli.commands.init._display_welcome"
        ):
            result = runner.invoke(
                app,
                ["--path", str(tmp_path), "--dry-run", "--skip-questionnaire"],
            )

        assert result.exit_code == 0
        assert not (tmp_path / ".project").exists()

    def test_dry_run_shows_what_would_be_created(self, tmp_path: Path) -> None:
        """--dry-run should show preview of what would be created."""
        with patch(
            "rice_factor.entrypoints.cli.commands.init._display_welcome"
        ):
            result = runner.invoke(
                app,
                ["--path", str(tmp_path), "--dry-run", "--skip-questionnaire"],
            )

        assert result.exit_code == 0
        assert (
            "Would create" in result.stdout
            or "dry-run" in result.stdout.lower()
        )


class TestInitCommandQuestionnaire:
    """Tests for init command questionnaire integration."""

    def test_runs_questionnaire_by_default(self, tmp_path: Path) -> None:
        """init should run questionnaire by default."""
        mock_runner = MagicMock()
        mock_runner.run.return_value = MagicMock(responses={})

        with (
            patch(
                "rice_factor.entrypoints.cli.commands.init._display_welcome"
            ),
            patch(
                "rice_factor.entrypoints.cli.commands.init._run_questionnaire"
            ) as mock_run_q,
        ):
            mock_run_q.return_value = MagicMock(responses={})
            result = runner.invoke(app, ["--path", str(tmp_path)])

            mock_run_q.assert_called_once()
            assert result.exit_code == 0

    def test_skip_questionnaire_uses_defaults(self, tmp_path: Path) -> None:
        """--skip-questionnaire should use default templates."""
        with patch(
            "rice_factor.entrypoints.cli.commands.init._display_welcome"
        ):
            result = runner.invoke(
                app, ["--path", str(tmp_path), "--skip-questionnaire"]
            )

        assert result.exit_code == 0
        # Default templates should have placeholder text
        content = (tmp_path / ".project" / "requirements.md").read_text()
        assert "[Not provided]" in content


class TestInitCommandOutput:
    """Tests for init command output formatting."""

    def test_shows_success_message(self, tmp_path: Path) -> None:
        """init should show success message on completion."""
        with patch(
            "rice_factor.entrypoints.cli.commands.init._display_welcome"
        ):
            result = runner.invoke(
                app, ["--path", str(tmp_path), "--skip-questionnaire"]
            )

        assert result.exit_code == 0
        # Should mention created files or initialization
        assert (
            "initialized" in result.stdout.lower()
            or "created" in result.stdout.lower()
        )

    def test_shows_next_steps_hint(self, tmp_path: Path) -> None:
        """init should show hint about next steps."""
        with patch(
            "rice_factor.entrypoints.cli.commands.init._display_welcome"
        ):
            result = runner.invoke(
                app, ["--path", str(tmp_path), "--skip-questionnaire"]
            )

        assert result.exit_code == 0
        # Should mention editing files or next command
        assert "Edit" in result.stdout or "plan" in result.stdout.lower()


class TestInitCommandDefaultPath:
    """Tests for init command with default path."""

    def test_uses_current_directory_by_default(self, tmp_path: Path) -> None:
        """init without --path should use current directory."""
        import os

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            with patch(
                "rice_factor.entrypoints.cli.commands.init._display_welcome"
            ):
                result = runner.invoke(app, ["--skip-questionnaire"])

            assert result.exit_code == 0
            assert (tmp_path / ".project").exists()
        finally:
            os.chdir(original_dir)
