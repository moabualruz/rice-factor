"""Artifact tree widget for TUI.

This module provides a tree view widget for displaying artifacts
in a hierarchical structure.
"""

from __future__ import annotations

from typing import Any

from textual.widgets import Tree


class ArtifactTree(Tree[dict[str, Any]]):
    """A tree widget for displaying artifacts.

    Shows artifacts organized by type in a collapsible tree structure.
    """

    DEFAULT_CSS = """
    ArtifactTree {
        width: 100%;
        height: 100%;
    }

    ArtifactTree > .tree--label {
        color: $text;
    }

    ArtifactTree > .tree--guides {
        color: $secondary;
    }
    """

    def __init__(self, label: str = "Artifacts") -> None:
        """Initialize the artifact tree.

        Args:
            label: Root label for the tree.
        """
        super().__init__(label)
        self._artifacts_by_type: dict[str, list[dict[str, Any]]] = {}

    def set_artifacts(self, artifacts: list[dict[str, Any]]) -> None:
        """Set the artifacts to display.

        Args:
            artifacts: List of artifact data dictionaries.
        """
        # Group artifacts by type
        self._artifacts_by_type = {}
        for artifact in artifacts:
            artifact_type = artifact.get("artifact_type", "Unknown")
            if artifact_type not in self._artifacts_by_type:
                self._artifacts_by_type[artifact_type] = []
            self._artifacts_by_type[artifact_type].append(artifact)

        # Rebuild tree
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        """Rebuild the tree from current artifacts."""
        self.clear()

        for artifact_type, artifacts in sorted(self._artifacts_by_type.items()):
            type_node = self.root.add(f"{artifact_type} ({len(artifacts)})")

            for artifact in artifacts:
                artifact_id = artifact.get("id", "")[:8]
                status = artifact.get("status", "")
                label = f"[{status}] {artifact_id}..."
                type_node.add_leaf(label, data=artifact)

    def get_selected_artifact(self) -> dict[str, Any] | None:
        """Get the currently selected artifact.

        Returns:
            Artifact data if a leaf is selected, None otherwise.
        """
        if self.cursor_node is not None and self.cursor_node.data is not None:
            return self.cursor_node.data
        return None
