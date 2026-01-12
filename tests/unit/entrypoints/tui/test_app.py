"""Tests for TUI application."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestRiceFactorTUI:
    """Tests for RiceFactorTUI class."""

    def test_tui_instantiation(self) -> None:
        """Test TUI app can be instantiated."""
        from rice_factor.entrypoints.tui.app import RiceFactorTUI

        app = RiceFactorTUI()
        assert app is not None
        assert app.project_root == Path.cwd()

    def test_tui_with_project_root(self, tmp_path: Path) -> None:
        """Test TUI with custom project root."""
        from rice_factor.entrypoints.tui.app import RiceFactorTUI

        app = RiceFactorTUI(project_root=tmp_path)
        assert app.project_root == tmp_path

    def test_tui_with_services(self, tmp_path: Path) -> None:
        """Test TUI with mock services."""
        from rice_factor.entrypoints.tui.app import RiceFactorTUI

        mock_phase_service = MagicMock()
        mock_artifact_service = MagicMock()

        app = RiceFactorTUI(
            project_root=tmp_path,
            phase_service=mock_phase_service,
            artifact_service=mock_artifact_service,
        )

        assert app.phase_service == mock_phase_service
        assert app.artifact_service == mock_artifact_service

    def test_tui_title(self) -> None:
        """Test TUI has correct title."""
        from rice_factor.entrypoints.tui.app import RiceFactorTUI

        assert RiceFactorTUI.TITLE == "Rice-Factor"

    def test_tui_bindings(self) -> None:
        """Test TUI has expected key bindings."""
        from rice_factor.entrypoints.tui.app import RiceFactorTUI

        binding_keys = [b.key for b in RiceFactorTUI.BINDINGS]
        assert "q" in binding_keys  # Quit
        assert "w" in binding_keys  # Workflow tab
        assert "a" in binding_keys  # Artifacts tab
        assert "r" in binding_keys  # Refresh
        assert "?" in binding_keys  # Help


class TestRunTUI:
    """Tests for run_tui function."""

    def test_run_tui_function_exists(self) -> None:
        """Test run_tui function exists and is callable."""
        from rice_factor.entrypoints.tui.app import run_tui

        assert callable(run_tui)


class TestTUICommand:
    """Tests for TUI CLI command."""

    def test_tui_command_registered(self) -> None:
        """Test TUI command is registered in main app."""
        from rice_factor.entrypoints.cli.main import app

        commands = [cmd.name for cmd in app.registered_commands]
        assert "tui" in commands

    def test_tui_command_help(self) -> None:
        """Test TUI command has help text."""
        from rice_factor.entrypoints.cli.commands.tui import tui

        assert tui.__doc__ is not None
        assert "TUI" in tui.__doc__ or "interactive" in tui.__doc__.lower()
