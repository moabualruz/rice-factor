import pytest
from typer.testing import CliRunner
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()

def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "rice-factor version" in result.stdout

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "LLM-Assisted Development System" in result.stdout

def test_init_help():
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize a new rice-factor project" in result.stdout

def test_web_help():
    result = runner.invoke(app, ["web", "--help"])
    assert result.exit_code == 0
    assert "Web interface commands" in result.stdout

def test_tui_help():
    result = runner.invoke(app, ["tui", "--help"])
    assert result.exit_code == 0
    assert "Start the TUI" in result.stdout

# Add a test that actually runs init in a temp dir if possible?
# For now, just verifying entry points as requested "test everything and anything that is an entry point"
