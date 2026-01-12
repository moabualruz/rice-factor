"""Template registry for project templates.

Provides a registry of project templates that can be used with `rice-factor init --template`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class TemplateConfig:
    """Configuration for a project template.

    Attributes:
        name: Template name (e.g., 'python-clean', 'rust-hexagonal').
        description: Human-readable description of the template.
        language: Primary programming language.
        architecture: Architecture pattern (clean, hexagonal, ddd, custom).
        version: Template version.
        author: Template author.
        tags: Searchable tags.
    """

    name: str
    description: str
    language: str
    architecture: str
    version: str = "1.0.0"
    author: str = "rice-factor"
    tags: list[str] = field(default_factory=list)


@dataclass
class FileTemplate:
    """A file to be created from the template.

    Attributes:
        path: Relative path for the file.
        content: File content (can include placeholders).
        description: Description of the file's purpose.
        is_optional: Whether the file is optional.
    """

    path: str
    content: str
    description: str = ""
    is_optional: bool = False


@dataclass
class DirectoryTemplate:
    """A directory to be created from the template.

    Attributes:
        path: Relative path for the directory.
        description: Description of the directory's purpose.
    """

    path: str
    description: str = ""


@dataclass
class ProjectTemplate:
    """Complete project template definition.

    Attributes:
        config: Template configuration.
        directories: Directories to create.
        files: Files to create.
        project_context: Default values for .project/ context.
        dependencies: Package dependencies.
        dev_dependencies: Development dependencies.
    """

    config: TemplateConfig
    directories: list[DirectoryTemplate] = field(default_factory=list)
    files: list[FileTemplate] = field(default_factory=list)
    project_context: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)

    def render_file(self, template: FileTemplate, variables: dict[str, str]) -> str:
        """Render a file template with variable substitution.

        Args:
            template: The file template to render.
            variables: Variables to substitute.

        Returns:
            Rendered file content.
        """
        content = template.content
        for key, value in variables.items():
            placeholder = f"{{{{ {key} }}}}"
            content = content.replace(placeholder, value)
        return content


class TemplateProvider(Protocol):
    """Protocol for template providers."""

    def get_template(self, name: str) -> ProjectTemplate | None:
        """Get a template by name."""
        ...

    def list_templates(self) -> list[TemplateConfig]:
        """List all available templates."""
        ...


class TemplateRegistry:
    """Registry for project templates.

    Manages built-in and custom templates.
    """

    def __init__(self) -> None:
        """Initialize the template registry."""
        self._templates: dict[str, ProjectTemplate] = {}

    def register(self, template: ProjectTemplate) -> None:
        """Register a template.

        Args:
            template: Template to register.
        """
        self._templates[template.config.name] = template

    def unregister(self, name: str) -> bool:
        """Unregister a template.

        Args:
            name: Template name to unregister.

        Returns:
            True if template was removed, False if not found.
        """
        if name in self._templates:
            del self._templates[name]
            return True
        return False

    def get(self, name: str) -> ProjectTemplate | None:
        """Get a template by name.

        Args:
            name: Template name.

        Returns:
            Template if found, None otherwise.
        """
        return self._templates.get(name)

    def list_templates(self) -> list[TemplateConfig]:
        """List all registered templates.

        Returns:
            List of template configurations.
        """
        return [t.config for t in self._templates.values()]

    def list_by_language(self, language: str) -> list[TemplateConfig]:
        """List templates by programming language.

        Args:
            language: Language to filter by.

        Returns:
            List of matching template configurations.
        """
        return [
            t.config
            for t in self._templates.values()
            if t.config.language.lower() == language.lower()
        ]

    def list_by_architecture(self, architecture: str) -> list[TemplateConfig]:
        """List templates by architecture pattern.

        Args:
            architecture: Architecture to filter by.

        Returns:
            List of matching template configurations.
        """
        return [
            t.config
            for t in self._templates.values()
            if t.config.architecture.lower() == architecture.lower()
        ]

    def search(self, query: str) -> list[TemplateConfig]:
        """Search templates by name, description, or tags.

        Args:
            query: Search query.

        Returns:
            List of matching template configurations.
        """
        query_lower = query.lower()
        results = []
        for template in self._templates.values():
            config = template.config
            if (
                query_lower in config.name.lower()
                or query_lower in config.description.lower()
                or any(query_lower in tag.lower() for tag in config.tags)
            ):
                results.append(config)
        return results

    def apply_template(
        self,
        name: str,
        target_dir: Path,
        variables: dict[str, str] | None = None,
        create_directories: bool = True,
    ) -> list[Path]:
        """Apply a template to a target directory.

        Args:
            name: Template name.
            target_dir: Directory to create template files in.
            variables: Variables for template substitution.
            create_directories: Whether to create directories.

        Returns:
            List of created file paths.

        Raises:
            ValueError: If template not found.
        """
        template = self.get(name)
        if template is None:
            raise ValueError(f"Template not found: {name}")

        variables = variables or {}
        created_files: list[Path] = []

        # Create directories
        if create_directories:
            for dir_template in template.directories:
                dir_path = target_dir / dir_template.path
                dir_path.mkdir(parents=True, exist_ok=True)

        # Create files
        for file_template in template.files:
            file_path = target_dir / file_template.path

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Render and write content
            content = template.render_file(file_template, variables)
            file_path.write_text(content, encoding="utf-8")
            created_files.append(file_path)

        return created_files

    def validate_template(self, template: ProjectTemplate) -> list[str]:
        """Validate a template for correctness.

        Args:
            template: Template to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors: list[str] = []

        # Check config
        if not template.config.name:
            errors.append("Template name is required")
        if not template.config.language:
            errors.append("Template language is required")
        if not template.config.architecture:
            errors.append("Template architecture is required")

        # Check for duplicate file paths
        file_paths = [f.path for f in template.files]
        if len(file_paths) != len(set(file_paths)):
            errors.append("Duplicate file paths in template")

        return errors
