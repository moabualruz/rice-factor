"""End-to-end TUI tests for Rice-Factor.

These tests verify TUI functionality through component and integration tests.

Test Categories:
1. Module Imports - TUI modules import correctly
2. App Creation - App instantiates correctly
3. Screen Components - Screens instantiate correctly
4. Graph Renderer - Graph visualization works
5. Audit Panel - Audit detail panel works
6. Diff Panel - Diff content panel works
7. Config Editor - Config editor panel works
"""

import json
from pathlib import Path

import pytest

# Check if textual is available
try:
    from textual.widgets import Static, TabbedContent
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not TEXTUAL_AVAILABLE,
    reason="Textual not installed"
)


@pytest.fixture
def tui_project(tmp_path: Path) -> Path:
    """Create a project structure for TUI testing."""
    project_dir = tmp_path / "tui_test_project"
    project_dir.mkdir()

    # Create .project directory
    project_subdir = project_dir / ".project"
    project_subdir.mkdir()
    (project_subdir / "requirements.md").write_text("# Requirements\n\nTUI test project.")
    (project_subdir / "constraints.md").write_text("# Constraints\n\nNo constraints.")
    (project_subdir / "glossary.md").write_text("# Glossary\n\n- **Term**: Definition")
    (project_subdir / ".phase").write_text("INITIALIZED")

    # Create artifacts directory with sample artifacts
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir()

    # Create a sample ProjectPlan artifact
    sample_artifact = {
        "id": "project-plan-001",
        "type": "ProjectPlan",
        "version": "1.0.0",
        "created_at": "2024-01-01T00:00:00Z",
        "status": "approved",
        "payload": {
            "name": "Test Project",
            "description": "A test project for TUI testing",
            "goals": ["Goal 1", "Goal 2"],
        },
    }
    (artifacts_dir / "project-plan-001.json").write_text(json.dumps(sample_artifact, indent=2))

    # Create audit directory with sample entries
    audit_dir = project_dir / "audit"
    audit_dir.mkdir()
    audit_entries = [
        {"timestamp": "2024-01-01T00:00:00Z", "action": "init", "actor": "user", "target": "project", "status": "success"},
        {"timestamp": "2024-01-01T01:00:00Z", "action": "plan", "actor": "system", "target": "ProjectPlan", "status": "success"},
    ]
    (audit_dir / "trail.json").write_text(json.dumps(audit_entries))

    # Create audit log for history screen
    audit_log_dir = project_subdir / "audit"
    audit_log_dir.mkdir()
    audit_log_lines = [json.dumps(entry) for entry in audit_entries]
    (audit_log_dir / "audit-log.jsonl").write_text("\n".join(audit_log_lines))

    # Create pending diffs directory
    diffs_dir = project_dir / ".project" / "pending-diffs"
    diffs_dir.mkdir()
    sample_diff = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+# New comment
 def main():
     pass
"""
    (diffs_dir / "main.py.diff").write_text(sample_diff)

    return project_dir


class TestTUIModuleImports:
    """Test TUI module imports work correctly."""

    def test_can_import_tui_app(self) -> None:
        """TUI app can be imported."""
        from rice_factor.entrypoints.tui.app import RiceFactorTUI
        assert RiceFactorTUI is not None

    def test_can_import_screens(self) -> None:
        """TUI screens can be imported."""
        from rice_factor.entrypoints.tui.screens import (
            ArtifactBrowserScreen,
            ConfigEditorScreen,
            DiffViewerScreen,
            GraphScreen,
            HistoryScreen,
            WorkflowScreen,
        )
        assert ArtifactBrowserScreen is not None
        assert ConfigEditorScreen is not None
        assert DiffViewerScreen is not None
        assert GraphScreen is not None
        assert HistoryScreen is not None
        assert WorkflowScreen is not None

    def test_app_has_expected_bindings(self) -> None:
        """App has expected key bindings."""
        from rice_factor.entrypoints.tui.app import RiceFactorTUI

        app = RiceFactorTUI()
        # Check bindings exist
        binding_keys = [b.key for b in app.BINDINGS]
        assert "q" in binding_keys  # Quit
        assert "w" in binding_keys  # Workflow
        assert "a" in binding_keys  # Artifacts
        assert "d" in binding_keys  # Diffs
        assert "c" in binding_keys  # Config
        assert "h" in binding_keys  # History
        assert "g" in binding_keys  # Graph
        assert "r" in binding_keys  # Refresh


class TestTUIAppCreation:
    """Test TUI app can be created."""

    def test_app_creation_default(self) -> None:
        """App can be created with defaults."""
        from rice_factor.entrypoints.tui.app import RiceFactorTUI

        app = RiceFactorTUI()
        assert app is not None
        assert app.TITLE == "Rice-Factor"

    def test_app_creation_with_project(self, tui_project: Path) -> None:
        """App can be created with project root."""
        from rice_factor.entrypoints.tui.app import RiceFactorTUI

        app = RiceFactorTUI(project_root=tui_project)
        assert app is not None
        assert app.project_root == tui_project


class TestTUIScreenComponents:
    """Test TUI screen components individually."""

    def test_workflow_screen_instantiates(self, tui_project: Path) -> None:
        """WorkflowScreen can be instantiated."""
        from rice_factor.entrypoints.tui.screens.workflow import WorkflowScreen

        screen = WorkflowScreen(project_root=tui_project)
        assert screen is not None

    def test_artifact_browser_instantiates(self, tui_project: Path) -> None:
        """ArtifactBrowserScreen can be instantiated."""
        from rice_factor.entrypoints.tui.screens.browser import ArtifactBrowserScreen

        screen = ArtifactBrowserScreen(project_root=tui_project)
        assert screen is not None

    def test_diff_viewer_instantiates(self, tui_project: Path) -> None:
        """DiffViewerScreen can be instantiated."""
        from rice_factor.entrypoints.tui.screens.diff_viewer import DiffViewerScreen

        screen = DiffViewerScreen(project_root=tui_project)
        assert screen is not None

    def test_config_editor_instantiates(self, tui_project: Path) -> None:
        """ConfigEditorScreen can be instantiated."""
        from rice_factor.entrypoints.tui.screens.config_editor import ConfigEditorScreen

        screen = ConfigEditorScreen(project_root=tui_project)
        assert screen is not None

    def test_history_screen_instantiates(self, tui_project: Path) -> None:
        """HistoryScreen can be instantiated."""
        from rice_factor.entrypoints.tui.screens.history import HistoryScreen

        screen = HistoryScreen(project_root=tui_project)
        assert screen is not None

    def test_graph_screen_instantiates(self, tui_project: Path) -> None:
        """GraphScreen can be instantiated."""
        from rice_factor.entrypoints.tui.screens.graph import GraphScreen

        screen = GraphScreen(project_root=tui_project)
        assert screen is not None


class TestTUIGraphRenderer:
    """Test graph renderer functionality."""

    def test_graph_renderer_empty(self) -> None:
        """Graph renderer handles empty nodes."""
        from rice_factor.entrypoints.tui.screens.graph import GraphRenderer

        renderer = GraphRenderer({})
        result = renderer.render()
        assert "No artifacts" in result

    def test_graph_renderer_with_nodes(self) -> None:
        """Graph renderer handles nodes."""
        from rice_factor.entrypoints.tui.screens.graph import GraphNode, GraphRenderer

        nodes = {
            "project-001": GraphNode("project-001", "ProjectPlan", "approved"),
            "test-001": GraphNode("test-001", "TestPlan", "draft"),
        }
        nodes["test-001"].depends_on.append("project-001")

        renderer = GraphRenderer(nodes)
        result = renderer.render()
        assert "ProjectPlan" in result or "project" in result.lower()

    def test_graph_mermaid_export(self) -> None:
        """Graph renderer can export mermaid format."""
        from rice_factor.entrypoints.tui.screens.graph import GraphNode, GraphRenderer

        nodes = {
            "project-001": GraphNode("project-001", "ProjectPlan", "approved"),
        }
        renderer = GraphRenderer(nodes)
        result = renderer.render_mermaid()
        assert "graph" in result.lower() or "mermaid" in result.lower() or "project" in result.lower()


class TestTUIAuditDetailPanel:
    """Test audit detail panel."""

    def test_detail_panel_instantiates(self) -> None:
        """AuditDetailPanel can be instantiated."""
        from rice_factor.entrypoints.tui.screens.history import AuditDetailPanel

        panel = AuditDetailPanel()
        assert panel is not None


class TestTUIDiffContentPanel:
    """Test diff content panel."""

    def test_diff_panel_instantiates(self) -> None:
        """DiffContentPanel can be instantiated."""
        from rice_factor.entrypoints.tui.screens.diff_viewer import DiffContentPanel

        panel = DiffContentPanel()
        assert panel is not None


class TestTUIConfigEditorPanel:
    """Test config editor panel."""

    def test_config_panel_instantiates(self) -> None:
        """ConfigEditorPanel can be instantiated."""
        from rice_factor.entrypoints.tui.screens.config_editor import ConfigEditorPanel

        panel = ConfigEditorPanel()
        assert panel is not None


class TestTUIGraphPanel:
    """Test graph panel."""

    def test_graph_panel_instantiates(self) -> None:
        """GraphPanel can be instantiated."""
        from rice_factor.entrypoints.tui.screens.graph import GraphPanel

        panel = GraphPanel()
        assert panel is not None


class TestTUIListItems:
    """Test custom list items."""

    def test_diff_list_item(self) -> None:
        """DiffListItem can be created."""
        from rice_factor.entrypoints.tui.screens.diff_viewer import DiffListItem

        item = DiffListItem(
            diff_id="diff-001",
            file_path="src/main.py",
            status="pending",
        )
        assert item.diff_id == "diff-001"
        assert item.file_path == "src/main.py"
        assert item.status == "pending"

    def test_audit_log_item(self) -> None:
        """AuditLogItem can be created."""
        from rice_factor.entrypoints.tui.screens.history import AuditLogItem

        item = AuditLogItem(
            entry_id="entry-001",
            timestamp="2024-01-01T00:00:00Z",
            action="init",
            summary="Initialize project",
        )
        assert item.entry_id == "entry-001"
        assert item.action == "init"

    def test_config_file_item(self) -> None:
        """ConfigFileItem can be created."""
        from rice_factor.entrypoints.tui.screens.config_editor import ConfigFileItem

        item = ConfigFileItem(
            file_path=Path("/test/.rice-factor.yaml"),
            file_name="Project Config",
            exists=True,
        )
        assert item.file_path == Path("/test/.rice-factor.yaml")
        assert item.file_name == "Project Config"
        assert item.exists is True
