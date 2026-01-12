"""Configuration editor screen for TUI.

This module provides a YAML configuration editor screen for editing
project and user configuration files with validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, ListItem, ListView, Static, TextArea


class ConfigFileItem(ListItem):
    """A list item representing a configuration file.

    Attributes:
        file_path: Path to the configuration file.
        file_name: Display name of the file.
        exists: Whether the file exists.
    """

    def __init__(
        self,
        file_path: Path,
        file_name: str,
        exists: bool = True,
    ) -> None:
        """Initialize a config file list item.

        Args:
            file_path: Path to the configuration file.
            file_name: Display name of the file.
            exists: Whether the file exists.
        """
        super().__init__()
        self._file_path = file_path
        self._file_name = file_name
        self._exists = exists

    @property
    def file_path(self) -> Path:
        """Get the file path."""
        return self._file_path

    @property
    def file_name(self) -> str:
        """Get the file name."""
        return self._file_name

    @property
    def exists(self) -> bool:
        """Get whether the file exists."""
        return self._exists

    def compose(self) -> ComposeResult:
        """Compose the list item display.

        Yields:
            UI components.
        """
        status = "" if self._exists else " [NEW]"
        yield Label(f"{self._file_name}{status}")


class ConfigEditorPanel(Static):
    """Panel for editing configuration content.

    Provides a YAML editor with syntax validation.
    """

    DEFAULT_CSS = """
    ConfigEditorPanel {
        width: 100%;
        height: 100%;
        background: #0a1a0a;
    }

    ConfigEditorPanel .editor-header {
        text-style: bold;
        padding: 1;
        background: #102010;
        color: #00a020;
    }

    ConfigEditorPanel #config-editor {
        width: 100%;
        height: 1fr;
        background: #0a1a0a;
        color: #00c030;
    }

    ConfigEditorPanel #validation-status {
        height: auto;
        padding: 1;
        background: #102010;
    }

    ConfigEditorPanel .valid {
        color: #00ff00;
    }

    ConfigEditorPanel .invalid {
        color: #ff6666;
    }

    ConfigEditorPanel #editor-actions {
        height: auto;
        padding: 1;
        background: #102010;
    }
    """

    def __init__(self) -> None:
        """Initialize the config editor panel."""
        super().__init__()
        self._file_path: Path | None = None
        self._original_content: str = ""
        self._is_valid: bool = True
        self._validation_message: str = "No file loaded"

    def set_file(self, file_path: Path) -> None:
        """Load a configuration file for editing.

        Args:
            file_path: Path to the configuration file.
        """
        self._file_path = file_path

        if file_path.exists():
            try:
                self._original_content = file_path.read_text(encoding="utf-8")
            except OSError as e:
                self._original_content = ""
                self._validation_message = f"Error reading file: {e}"
                self._is_valid = False
        else:
            self._original_content = self._get_default_config(file_path)

        self._validate_yaml(self._original_content)
        self.refresh_display()

    def _get_default_config(self, file_path: Path) -> str:
        """Get default configuration content for a new file.

        Args:
            file_path: Path to determine the config type.

        Returns:
            Default YAML content.
        """
        if ".rice-factor" in str(file_path):
            return """# Rice-Factor Project Configuration
# Documentation: https://rice-factor.dev/reference/configuration/

llm:
  provider: claude
  model: claude-3-5-sonnet-20241022
  temperature: 0.0

execution:
  dry_run: false
  auto_approve: false

paths:
  artifacts_dir: .project/artifacts
  audit_dir: .project/audit
"""
        else:
            return "# Configuration file\n"

    def _validate_yaml(self, content: str) -> None:
        """Validate YAML content.

        Args:
            content: YAML content to validate.
        """
        try:
            yaml.safe_load(content)
            self._is_valid = True
            self._validation_message = "Valid YAML"
        except yaml.YAMLError as e:
            self._is_valid = False
            self._validation_message = f"Invalid YAML: {e}"

    def refresh_display(self) -> None:
        """Refresh the editor display."""
        self.remove_children()
        self.mount_all(list(self.compose()))

    def compose(self) -> ComposeResult:
        """Compose the editor panel.

        Yields:
            UI components.
        """
        file_name = self._file_path.name if self._file_path else "No file"
        yield Label(f"Editing: {file_name}", classes="editor-header")

        # Text editor for YAML content
        editor = TextArea(
            self._original_content,
            id="config-editor",
            language="yaml",
        )
        yield editor

        # Validation status
        status_class = "valid" if self._is_valid else "invalid"
        yield Label(
            self._validation_message,
            id="validation-status",
            classes=status_class,
        )

        # Action buttons
        with Horizontal(id="editor-actions"):
            yield Button("Save", id="save-btn", variant="primary")
            yield Button("Revert", id="revert-btn", variant="default")
            yield Button("Validate", id="validate-btn", variant="default")

    def get_content(self) -> str:
        """Get the current editor content.

        Returns:
            Current text content.
        """
        try:
            editor = self.query_one("#config-editor", TextArea)
            return editor.text
        except Exception:
            return self._original_content

    def save_file(self) -> bool:
        """Save the current content to file.

        Returns:
            True if save was successful.
        """
        if self._file_path is None:
            return False

        content = self.get_content()

        # Validate before saving
        self._validate_yaml(content)
        if not self._is_valid:
            return False

        try:
            # Create parent directories if needed
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(content, encoding="utf-8")
            self._original_content = content
            return True
        except OSError:
            return False

    def revert_content(self) -> None:
        """Revert to original content."""
        try:
            editor = self.query_one("#config-editor", TextArea)
            editor.text = self._original_content
            self._validate_yaml(self._original_content)
            self.refresh_display()
        except Exception:
            pass


class ConfigEditorScreen(Static):
    """Configuration editor screen.

    Shows available configuration files and allows editing them.

    Attributes:
        project_root: Root directory of the project.
    """

    DEFAULT_CSS = """
    ConfigEditorScreen {
        width: 100%;
        height: 100%;
        background: #0a1a0a;
    }

    #config-header {
        height: auto;
        padding: 1;
        text-align: center;
        background: #009e20;
        color: white;
    }

    #config-content {
        width: 100%;
        height: 1fr;
    }

    #config-list-panel {
        width: 30%;
        height: 100%;
        border-right: solid #00a020;
    }

    #config-editor-panel {
        width: 70%;
        height: 100%;
    }

    #config-list {
        height: 100%;
        background: #0a1a0a;
    }

    .list-header {
        padding: 1;
        background: #102010;
        text-style: bold;
        color: #00a020;
    }

    .section-label {
        padding: 1 0 0 1;
        color: #808080;
        text-style: italic;
    }
    """

    def __init__(
        self,
        project_root: Path | None = None,
    ) -> None:
        """Initialize the configuration editor screen.

        Args:
            project_root: Root directory of the project.
        """
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._config_files: list[dict[str, Any]] = []

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    def compose(self) -> ComposeResult:
        """Compose the configuration editor.

        Yields:
            UI components.
        """
        yield Static("Configuration Editor", id="config-header")

        with Horizontal(id="config-content"):
            with Vertical(id="config-list-panel"):
                yield Label("Config Files", classes="list-header")
                yield self._create_config_list()

            with Vertical(id="config-editor-panel"):
                yield ConfigEditorPanel()

    def _create_config_list(self) -> ListView:
        """Create the configuration file list.

        Returns:
            ListView with config files.
        """
        self._load_config_files()

        list_view = ListView(id="config-list")

        for config in self._config_files:
            item = ConfigFileItem(
                file_path=Path(config["path"]),
                file_name=config["name"],
                exists=config["exists"],
            )
            list_view.mount(item)

        return list_view

    def _load_config_files(self) -> None:
        """Load list of configuration files."""
        self._config_files = []

        # Project configuration
        project_config = self._project_root / ".rice-factor.yaml"
        self._config_files.append({
            "name": ".rice-factor.yaml (Project)",
            "path": str(project_config),
            "exists": project_config.exists(),
            "section": "Project",
        })

        # User configuration
        user_config = Path.home() / ".rice-factor" / "config.yaml"
        self._config_files.append({
            "name": "config.yaml (User)",
            "path": str(user_config),
            "exists": user_config.exists(),
            "section": "User",
        })

        # Additional config files in .project/
        project_dir = self._project_root / ".project"
        if project_dir.exists():
            for yaml_file in project_dir.glob("*.yaml"):
                if yaml_file.name not in ("requirements.yaml",):
                    self._config_files.append({
                        "name": yaml_file.name,
                        "path": str(yaml_file),
                        "exists": True,
                        "section": ".project",
                    })

            for yaml_file in project_dir.glob("*.yml"):
                self._config_files.append({
                    "name": yaml_file.name,
                    "path": str(yaml_file),
                    "exists": True,
                    "section": ".project",
                })

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle config file selection.

        Args:
            event: Selection event.
        """
        if isinstance(event.item, ConfigFileItem):
            editor_panel = self.query_one(ConfigEditorPanel)
            editor_panel.set_file(event.item.file_path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button press event.
        """
        editor_panel = self.query_one(ConfigEditorPanel)

        if event.button.id == "save-btn":
            if editor_panel.save_file():
                self.notify("Configuration saved successfully")
            else:
                self.notify("Failed to save configuration", severity="error")

        elif event.button.id == "revert-btn":
            editor_panel.revert_content()
            self.notify("Reverted to original content")

        elif event.button.id == "validate-btn":
            content = editor_panel.get_content()
            editor_panel._validate_yaml(content)
            editor_panel.refresh_display()

            if editor_panel._is_valid:
                self.notify("YAML is valid")
            else:
                self.notify("YAML validation failed", severity="error")

    async def refresh_view(self) -> None:
        """Refresh the configuration editor."""
        self._load_config_files()
        await self.remove_children()
        await self.mount_all(list(self.compose()))
