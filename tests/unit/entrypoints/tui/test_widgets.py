"""Tests for TUI widgets."""

from __future__ import annotations

import pytest


class TestArtifactTree:
    """Tests for ArtifactTree widget."""

    def test_artifact_tree_instantiation(self) -> None:
        """Test ArtifactTree can be instantiated."""
        from rice_factor.entrypoints.tui.widgets.artifact_tree import ArtifactTree

        tree = ArtifactTree()
        assert tree is not None

    def test_artifact_tree_with_label(self) -> None:
        """Test ArtifactTree with custom label."""
        from rice_factor.entrypoints.tui.widgets.artifact_tree import ArtifactTree

        tree = ArtifactTree(label="My Artifacts")
        assert tree is not None

    def test_artifact_tree_set_artifacts(self) -> None:
        """Test setting artifacts on tree."""
        from rice_factor.entrypoints.tui.widgets.artifact_tree import ArtifactTree

        tree = ArtifactTree()
        artifacts = [
            {"id": "1", "artifact_type": "PROJECT_PLAN", "status": "DRAFT"},
            {"id": "2", "artifact_type": "TEST_PLAN", "status": "APPROVED"},
        ]
        tree.set_artifacts(artifacts)

        assert "PROJECT_PLAN" in tree._artifacts_by_type
        assert "TEST_PLAN" in tree._artifacts_by_type

    def test_artifact_tree_get_selected_none(self) -> None:
        """Test getting selected artifact when none selected."""
        from rice_factor.entrypoints.tui.widgets.artifact_tree import ArtifactTree

        tree = ArtifactTree()
        assert tree.get_selected_artifact() is None


class TestStatusBar:
    """Tests for StatusBar widget."""

    def test_status_bar_instantiation(self) -> None:
        """Test StatusBar can be instantiated."""
        from rice_factor.entrypoints.tui.widgets.status_bar import StatusBar

        bar = StatusBar()
        assert bar is not None

    def test_status_bar_initial_state(self) -> None:
        """Test StatusBar initial state."""
        from rice_factor.entrypoints.tui.widgets.status_bar import StatusBar

        bar = StatusBar()
        # Just verify attributes exist - update methods require app context
        assert bar._phase == "unknown"
        assert bar._message == ""
