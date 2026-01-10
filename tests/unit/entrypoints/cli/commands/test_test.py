"""Unit tests for test command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestTestCommandHelp:
    """Tests for test command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["test", "--help"])
        assert result.exit_code == 0
        assert "test" in result.stdout.lower()

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["test", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout

    def test_help_shows_verbose_option(self) -> None:
        """--help should show --verbose option."""
        result = runner.invoke(app, ["test", "--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.stdout


class TestTestRequiresInit:
    """Tests for test phase requirements."""

    def test_test_requires_init(self, tmp_path: Path) -> None:
        """test should fail if project not initialized."""
        result = runner.invoke(app, ["test", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestTestExecution:
    """Tests for test command execution."""

    def test_test_runs_tests(self, tmp_path: Path) -> None:
        """test should run tests and show results."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.test._check_phase"
        ):
            result = runner.invoke(app, ["test", "--path", str(tmp_path)])

        assert result.exit_code == 0
        # Should show test results
        assert "pass" in result.stdout.lower() or "test" in result.stdout.lower()

    def test_test_verbose_shows_details(self, tmp_path: Path) -> None:
        """--verbose should show detailed test output."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.test._check_phase"
        ):
            result = runner.invoke(
                app, ["test", "--path", str(tmp_path), "--verbose"]
            )

        assert result.exit_code == 0
        # Verbose should show more detail
        assert "test" in result.stdout.lower()


class TestTestCreatesArtifact:
    """Tests for test command artifact creation."""

    def test_test_creates_validation_result(self, tmp_path: Path) -> None:
        """test should create ValidationResult artifact."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.test._check_phase"
        ):
            result = runner.invoke(app, ["test", "--path", str(tmp_path)])

        assert result.exit_code == 0
        artifacts_dir = tmp_path / "artifacts"
        assert artifacts_dir.exists()
        # Should have a validation result artifact
        artifact_files = list(artifacts_dir.glob("**/*.json"))
        assert len(artifact_files) >= 1


class TestTestCreatesAuditEntry:
    """Tests for test audit trail."""

    def test_test_creates_audit_entry(self, tmp_path: Path) -> None:
        """Running tests should create an audit entry."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.test._check_phase"
        ):
            result = runner.invoke(app, ["test", "--path", str(tmp_path)])

        assert result.exit_code == 0
        # Audit trail should exist
        trail_file = tmp_path / "audit" / "trail.json"
        assert trail_file.exists()


class TestTestWithFailures:
    """Tests for test command with failing tests."""

    def test_test_shows_failure_count(self, tmp_path: Path) -> None:
        """test should show failure count if tests fail."""
        (tmp_path / ".project").mkdir()

        # Mock the stub runner to return failures
        # _run_stub_tests returns (total, failed, error_messages)
        with (
            patch("rice_factor.entrypoints.cli.commands.test._check_phase"),
            patch("rice_factor.entrypoints.cli.commands.test._run_stub_tests") as mock_run,
        ):
            mock_run.return_value = (5, 2, ["Error 1", "Error 2"])
            result = runner.invoke(app, ["test", "--path", str(tmp_path)])

        # Command exits 1 when tests fail
        assert result.exit_code == 1
        # Should show some indication of failures
        assert "fail" in result.stdout.lower() or "2" in result.stdout
