"""Unit tests for validate command."""

from pathlib import Path

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestValidateHelp:
    """Tests for validate command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "validation" in result.stdout.lower()

    def test_help_shows_step_option(self) -> None:
        """--help should show --step option."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--step" in result.stdout

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout

    def test_help_shows_save_option(self) -> None:
        """--help should show --save/--no-save option."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--save" in result.stdout or "--no-save" in result.stdout


class TestValidateRequiresInit:
    """Tests for validate phase requirements."""

    def test_validate_requires_init(self, tmp_path: Path) -> None:
        """validate should fail if project not initialized."""
        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path), "--no-save"]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestValidateRunsAllSteps:
    """Tests for validate running all steps."""

    def test_validate_runs_all_validations(self, tmp_path: Path) -> None:
        """validate should run all validation steps."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path), "--no-save"]
        )

        assert result.exit_code == 0
        assert "schema" in result.stdout.lower()
        assert "architecture" in result.stdout.lower()
        assert "tests" in result.stdout.lower()
        assert "lint" in result.stdout.lower()

    def test_validate_shows_results_table(self, tmp_path: Path) -> None:
        """validate should show results in a table."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path), "--no-save"]
        )

        assert result.exit_code == 0
        assert "Validation Results" in result.stdout

    def test_validate_shows_passed_summary(self, tmp_path: Path) -> None:
        """validate should show passed summary when all pass."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path), "--no-save"]
        )

        assert result.exit_code == 0
        assert "passed" in result.stdout.lower()


class TestValidateStepOption:
    """Tests for --step option."""

    def test_step_schema_runs_only_schema(self, tmp_path: Path) -> None:
        """--step schema should run only schema validation."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "schema", "--no-save"],
        )

        assert result.exit_code == 0
        assert "schema" in result.stdout.lower()

    def test_step_architecture_runs_only_architecture(self, tmp_path: Path) -> None:
        """--step architecture should run only architecture validation."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "architecture", "--no-save"],
        )

        assert result.exit_code == 0
        assert "architecture" in result.stdout.lower()

    def test_step_tests_runs_only_tests(self, tmp_path: Path) -> None:
        """--step tests should run only test validation."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "tests", "--no-save"],
        )

        assert result.exit_code == 0

    def test_step_lint_runs_only_lint(self, tmp_path: Path) -> None:
        """--step lint should run only lint validation."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "lint", "--no-save"],
        )

        assert result.exit_code == 0

    def test_invalid_step_fails(self, tmp_path: Path) -> None:
        """Invalid --step value should fail with error."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "invalid", "--no-save"],
        )

        assert result.exit_code == 1
        assert "invalid" in result.stdout.lower()


class TestValidateSaveArtifact:
    """Tests for ValidationResult artifact saving."""

    def test_validate_saves_artifact_by_default(self, tmp_path: Path) -> None:
        """validate should save ValidationResult artifact by default."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "ValidationResult saved" in result.stdout

    def test_validate_no_save_skips_artifact(self, tmp_path: Path) -> None:
        """--no-save should not save ValidationResult artifact."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path), "--no-save"]
        )

        assert result.exit_code == 0
        assert "ValidationResult saved" not in result.stdout

    def test_validate_artifact_in_artifacts_dir(self, tmp_path: Path) -> None:
        """ValidationResult should be saved in artifacts directory."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        validation_dir = tmp_path / "artifacts" / "validation_results"
        assert validation_dir.exists()
        assert len(list(validation_dir.glob("*.json"))) == 1


class TestValidateStubbedSteps:
    """Tests for stubbed validation steps."""

    def test_architecture_shows_stubbed(self, tmp_path: Path) -> None:
        """Architecture validation should indicate it's stubbed."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path), "--no-save"]
        )

        assert result.exit_code == 0
        assert "stubbed" in result.stdout.lower()

    def test_tests_shows_stubbed(self, tmp_path: Path) -> None:
        """Tests validation should indicate it's stubbed."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "tests", "--no-save"],
        )

        assert result.exit_code == 0

    def test_lint_shows_stubbed(self, tmp_path: Path) -> None:
        """Lint validation should indicate it's stubbed."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "lint", "--no-save"],
        )

        assert result.exit_code == 0
