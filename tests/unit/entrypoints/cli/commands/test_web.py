"""Tests for web CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app


runner = CliRunner()


class TestWebServe:
    """Tests for rice-factor web serve command."""

    def test_serve_command_exists(self) -> None:
        """Test that serve command is registered."""
        result = runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "serve" in result.output

    def test_serve_without_web_deps(self) -> None:
        """Test serve fails gracefully without web dependencies."""
        with patch(
            "rice_factor.entrypoints.cli.commands.web._check_web_dependencies",
            return_value=False,
        ):
            result = runner.invoke(app, ["web", "serve"])
            assert result.exit_code == 1
            assert "Web dependencies not installed" in result.output

    def test_serve_help(self) -> None:
        """Test serve command help."""
        result = runner.invoke(app, ["web", "serve", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--host" in result.output
        assert "--reload" in result.output

    @patch("rice_factor.entrypoints.cli.commands.web._check_web_dependencies")
    @patch("uvicorn.run")
    def test_serve_with_custom_port(
        self,
        mock_uvicorn: MagicMock,
        mock_deps: MagicMock,
    ) -> None:
        """Test serve with custom port."""
        mock_deps.return_value = True

        result = runner.invoke(app, ["web", "serve", "--port", "9000"])
        # uvicorn.run will be called
        mock_uvicorn.assert_called_once()
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["port"] == 9000


class TestWebBuild:
    """Tests for rice-factor web build command."""

    def test_build_command_exists(self) -> None:
        """Test that build command is registered."""
        result = runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "build" in result.output

    def test_build_help(self) -> None:
        """Test build command help."""
        result = runner.invoke(app, ["web", "build", "--help"])
        assert result.exit_code == 0
        assert "--outdir" in result.output
        assert "--install" in result.output

    def test_build_without_node(self) -> None:
        """Test build fails gracefully without Node.js."""
        with patch(
            "rice_factor.entrypoints.cli.commands.web._check_node_npm",
            return_value=False,
        ):
            result = runner.invoke(app, ["web", "build"])
            assert result.exit_code == 1
            assert "Node.js" in result.output

    @patch("rice_factor.entrypoints.cli.commands.web._check_node_npm")
    @patch("rice_factor.entrypoints.cli.commands.web._get_frontend_dir")
    def test_build_frontend_not_found(
        self,
        mock_frontend: MagicMock,
        mock_node: MagicMock,
    ) -> None:
        """Test build fails when frontend directory not found."""
        mock_node.return_value = True
        mock_frontend.return_value = Path("/nonexistent/frontend")

        result = runner.invoke(app, ["web", "build"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestWebStatus:
    """Tests for rice-factor web status command."""

    def test_status_command_exists(self) -> None:
        """Test that status command is registered."""
        result = runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "status" in result.output

    @patch("rice_factor.entrypoints.cli.commands.web._check_web_dependencies")
    @patch("rice_factor.entrypoints.cli.commands.web._check_node_npm")
    @patch("rice_factor.entrypoints.cli.commands.web._get_frontend_dir")
    def test_status_shows_dependency_info(
        self,
        mock_frontend: MagicMock,
        mock_node: MagicMock,
        mock_deps: MagicMock,
    ) -> None:
        """Test status shows dependency information."""
        mock_deps.return_value = True
        mock_node.return_value = True
        mock_frontend.return_value = Path("/some/path")

        result = runner.invoke(app, ["web", "status"])
        assert result.exit_code == 0
        assert "Python web dependencies" in result.output
        assert "Node.js" in result.output

    @patch("rice_factor.entrypoints.cli.commands.web._check_web_dependencies")
    @patch("rice_factor.entrypoints.cli.commands.web._check_node_npm")
    @patch("rice_factor.entrypoints.cli.commands.web._get_frontend_dir")
    def test_status_missing_deps(
        self,
        mock_frontend: MagicMock,
        mock_node: MagicMock,
        mock_deps: MagicMock,
    ) -> None:
        """Test status shows missing dependencies."""
        mock_deps.return_value = False
        mock_node.return_value = False
        mock_frontend.return_value = Path("/nonexistent")

        result = runner.invoke(app, ["web", "status"])
        assert result.exit_code == 0
        assert "not installed" in result.output or "not available" in result.output
