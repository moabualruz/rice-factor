"""Tests for CLI commands."""

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


def test_help_command() -> None:
    """CLI should display help text."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "LLM-Assisted Development System" in result.stdout


def test_version_flag() -> None:
    """CLI should display version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "rice-factor version" in result.stdout


def test_plan_help() -> None:
    """Plan command should have help."""
    result = runner.invoke(app, ["plan", "--help"])
    assert result.exit_code == 0
    assert "Generate a planning artifact" in result.stdout


def test_init_help() -> None:
    """Init command should have help."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize a new rice-factor project" in result.stdout
