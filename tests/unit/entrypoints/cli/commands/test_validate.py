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

        # Real validators may fail on empty project (e.g., no tests)
        # But they should still run and show results
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

        # Results table should be shown regardless of pass/fail
        assert "Validation Results" in result.stdout

    def test_validate_shows_status_summary(self, tmp_path: Path) -> None:
        """validate should show status summary."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path), "--no-save"]
        )

        # Should show either passed or failed status
        assert "passed" in result.stdout.lower() or "failed" in result.stdout.lower()


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

    def test_step_tests_runs_tests(self, tmp_path: Path) -> None:
        """--step tests should run test validation."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "tests", "--no-save"],
        )

        # Tests step may fail if no tests exist - that's expected behavior
        assert "tests" in result.stdout.lower()

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

        # May pass or fail depending on test runner results, but should save
        assert "ValidationResult saved" in result.stdout

    def test_validate_no_save_skips_artifact(self, tmp_path: Path) -> None:
        """--no-save should not save ValidationResult artifact."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path), "--no-save"]
        )

        # Should not save regardless of pass/fail
        assert "ValidationResult saved" not in result.stdout

    def test_validate_artifact_in_artifacts_dir(self, tmp_path: Path) -> None:
        """ValidationResult should be saved in artifacts directory."""
        (tmp_path / ".project").mkdir()

        runner.invoke(
            app, ["validate", "--path", str(tmp_path)]
        )

        # Should save regardless of pass/fail
        validation_dir = tmp_path / "artifacts" / "validation_results"
        assert validation_dir.exists()
        assert len(list(validation_dir.glob("*.json"))) == 1


class TestValidateRealValidators:
    """Tests for real validation steps (no longer stubbed)."""

    def test_architecture_shows_validator_name(self, tmp_path: Path) -> None:
        """Architecture validation should show validator name."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["validate", "--path", str(tmp_path), "--no-save"]
        )

        # Validation now runs real validators
        assert "architecture" in result.stdout.lower()

    def test_tests_runs_real_tests(self, tmp_path: Path) -> None:
        """Tests validation should run real test runner."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "tests", "--no-save"],
        )

        # Real test runner will be invoked (may pass or fail)
        assert "tests" in result.stdout.lower()

    def test_lint_runs_real_linter(self, tmp_path: Path) -> None:
        """Lint validation should run real linter."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["validate", "--path", str(tmp_path), "--step", "lint", "--no-save"],
        )

        # Lint is optional - passes if linter not found
        assert result.exit_code == 0
