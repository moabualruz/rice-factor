"""Tests for TUI screens."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestWorkflowScreen:
    """Tests for WorkflowScreen."""

    def test_workflow_screen_instantiation(self) -> None:
        """Test WorkflowScreen can be instantiated."""
        from rice_factor.entrypoints.tui.screens.workflow import WorkflowScreen

        screen = WorkflowScreen()
        assert screen is not None
        assert screen.project_root == Path.cwd()

    def test_workflow_screen_with_project_root(self, tmp_path: Path) -> None:
        """Test WorkflowScreen with custom project root."""
        from rice_factor.entrypoints.tui.screens.workflow import WorkflowScreen

        screen = WorkflowScreen(project_root=tmp_path)
        assert screen.project_root == tmp_path

    def test_workflow_screen_with_phase_service(self, tmp_path: Path) -> None:
        """Test WorkflowScreen with mock phase service."""
        from rice_factor.entrypoints.tui.screens.workflow import WorkflowScreen

        mock_phase_service = MagicMock()
        screen = WorkflowScreen(
            project_root=tmp_path,
            phase_service=mock_phase_service,
        )
        assert screen.phase_service == mock_phase_service


class TestWorkflowStep:
    """Tests for WorkflowStep widget."""

    def test_workflow_step_instantiation(self) -> None:
        """Test WorkflowStep can be instantiated."""
        from rice_factor.entrypoints.tui.screens.workflow import WorkflowStep

        step = WorkflowStep(
            step_name="init",
            title="Initialize",
            description="Create project",
        )
        assert step is not None

    def test_workflow_step_current(self) -> None:
        """Test WorkflowStep with current flag."""
        from rice_factor.entrypoints.tui.screens.workflow import WorkflowStep

        step = WorkflowStep(
            step_name="init",
            title="Initialize",
            description="Create project",
            is_current=True,
        )
        assert step._is_current is True

    def test_workflow_step_complete(self) -> None:
        """Test WorkflowStep with complete flag."""
        from rice_factor.entrypoints.tui.screens.workflow import WorkflowStep

        step = WorkflowStep(
            step_name="init",
            title="Initialize",
            description="Create project",
            is_complete=True,
        )
        assert step._is_complete is True


class TestArtifactBrowserScreen:
    """Tests for ArtifactBrowserScreen."""

    def test_artifact_browser_instantiation(self) -> None:
        """Test ArtifactBrowserScreen can be instantiated."""
        from rice_factor.entrypoints.tui.screens.browser import ArtifactBrowserScreen

        screen = ArtifactBrowserScreen()
        assert screen is not None
        assert screen.project_root == Path.cwd()

    def test_artifact_browser_with_project_root(self, tmp_path: Path) -> None:
        """Test ArtifactBrowserScreen with custom project root."""
        from rice_factor.entrypoints.tui.screens.browser import ArtifactBrowserScreen

        screen = ArtifactBrowserScreen(project_root=tmp_path)
        assert screen.project_root == tmp_path

    def test_artifact_browser_with_service(self, tmp_path: Path) -> None:
        """Test ArtifactBrowserScreen with mock artifact service."""
        from rice_factor.entrypoints.tui.screens.browser import ArtifactBrowserScreen

        mock_service = MagicMock()
        screen = ArtifactBrowserScreen(
            project_root=tmp_path,
            artifact_service=mock_service,
        )
        assert screen.artifact_service == mock_service


class TestArtifactListItem:
    """Tests for ArtifactListItem widget."""

    def test_artifact_list_item_instantiation(self) -> None:
        """Test ArtifactListItem can be instantiated."""
        from rice_factor.entrypoints.tui.screens.browser import ArtifactListItem

        item = ArtifactListItem(
            artifact_id="12345678-1234-1234-1234-123456789012",
            artifact_type="PROJECT_PLAN",
            status="DRAFT",
        )
        assert item is not None
        assert item.artifact_type == "PROJECT_PLAN"
        assert item.status == "DRAFT"


class TestArtifactDetailPanel:
    """Tests for ArtifactDetailPanel widget."""

    def test_artifact_detail_panel_instantiation(self) -> None:
        """Test ArtifactDetailPanel can be instantiated."""
        from rice_factor.entrypoints.tui.screens.browser import ArtifactDetailPanel

        panel = ArtifactDetailPanel()
        assert panel is not None

    def test_artifact_detail_panel_data_attribute(self) -> None:
        """Test ArtifactDetailPanel has data attribute."""
        from rice_factor.entrypoints.tui.screens.browser import ArtifactDetailPanel

        panel = ArtifactDetailPanel()
        # Just verify the attribute exists and is initially None
        # set_artifact/clear require an active app context
        assert panel._artifact_data is None
