"""Tests for TemplateRegistry."""

from __future__ import annotations

from pathlib import Path

import pytest

from rice_factor.adapters.templates import (
    BUILTIN_TEMPLATES,
    ProjectTemplate,
    TemplateConfig,
    TemplateRegistry,
)
from rice_factor.adapters.templates.template_registry import (
    DirectoryTemplate,
    FileTemplate,
)


class TestTemplateConfig:
    """Tests for TemplateConfig."""

    def test_create_config(self) -> None:
        """Test creating a template config."""
        config = TemplateConfig(
            name="test-template",
            description="Test template",
            language="python",
            architecture="clean",
        )
        assert config.name == "test-template"
        assert config.language == "python"
        assert config.architecture == "clean"
        assert config.version == "1.0.0"

    def test_config_with_tags(self) -> None:
        """Test config with tags."""
        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
            tags=["python", "testing"],
        )
        assert config.tags == ["python", "testing"]


class TestFileTemplate:
    """Tests for FileTemplate."""

    def test_create_file_template(self) -> None:
        """Test creating a file template."""
        template = FileTemplate(
            path="src/main.py",
            content="print('hello')",
            description="Main file",
        )
        assert template.path == "src/main.py"
        assert template.content == "print('hello')"
        assert template.is_optional is False


class TestDirectoryTemplate:
    """Tests for DirectoryTemplate."""

    def test_create_directory_template(self) -> None:
        """Test creating a directory template."""
        template = DirectoryTemplate(path="src/domain", description="Domain layer")
        assert template.path == "src/domain"
        assert template.description == "Domain layer"


class TestProjectTemplate:
    """Tests for ProjectTemplate."""

    def test_create_template(self) -> None:
        """Test creating a project template."""
        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(config=config)
        assert template.config.name == "test"
        assert template.directories == []
        assert template.files == []

    def test_render_file_with_variables(self) -> None:
        """Test rendering a file with variable substitution."""
        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(config=config)

        file_template = FileTemplate(
            path="pyproject.toml",
            content='name = "{{ project_name }}"',
        )

        rendered = template.render_file(
            file_template, {"project_name": "my-project"}
        )
        assert rendered == 'name = "my-project"'

    def test_render_file_multiple_variables(self) -> None:
        """Test rendering with multiple variables."""
        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(config=config)

        file_template = FileTemplate(
            path="readme.md",
            content="# {{ project_name }}\n\n{{ description }}",
        )

        rendered = template.render_file(
            file_template,
            {"project_name": "MyProject", "description": "A great project"},
        )
        assert "# MyProject" in rendered
        assert "A great project" in rendered


class TestTemplateRegistry:
    """Tests for TemplateRegistry."""

    def test_create_registry(self) -> None:
        """Test creating an empty registry."""
        registry = TemplateRegistry()
        assert registry.list_templates() == []

    def test_register_template(self) -> None:
        """Test registering a template."""
        registry = TemplateRegistry()
        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(config=config)

        registry.register(template)

        assert len(registry.list_templates()) == 1
        assert registry.get("test") is not None

    def test_unregister_template(self) -> None:
        """Test unregistering a template."""
        registry = TemplateRegistry()
        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(config=config)
        registry.register(template)

        result = registry.unregister("test")

        assert result is True
        assert registry.get("test") is None

    def test_unregister_nonexistent(self) -> None:
        """Test unregistering nonexistent template."""
        registry = TemplateRegistry()
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_nonexistent(self) -> None:
        """Test getting nonexistent template."""
        registry = TemplateRegistry()
        assert registry.get("nonexistent") is None

    def test_list_by_language(self) -> None:
        """Test listing templates by language."""
        registry = TemplateRegistry()

        py_config = TemplateConfig(
            name="py-test",
            description="Python test",
            language="python",
            architecture="clean",
        )
        go_config = TemplateConfig(
            name="go-test",
            description="Go test",
            language="go",
            architecture="hexagonal",
        )

        registry.register(ProjectTemplate(config=py_config))
        registry.register(ProjectTemplate(config=go_config))

        py_templates = registry.list_by_language("python")
        assert len(py_templates) == 1
        assert py_templates[0].name == "py-test"

    def test_list_by_architecture(self) -> None:
        """Test listing templates by architecture."""
        registry = TemplateRegistry()

        clean_config = TemplateConfig(
            name="clean-test",
            description="Clean test",
            language="python",
            architecture="clean",
        )
        hex_config = TemplateConfig(
            name="hex-test",
            description="Hex test",
            language="go",
            architecture="hexagonal",
        )

        registry.register(ProjectTemplate(config=clean_config))
        registry.register(ProjectTemplate(config=hex_config))

        hex_templates = registry.list_by_architecture("hexagonal")
        assert len(hex_templates) == 1
        assert hex_templates[0].name == "hex-test"

    def test_search_by_name(self) -> None:
        """Test searching templates by name."""
        registry = TemplateRegistry()

        config = TemplateConfig(
            name="python-clean",
            description="Python clean architecture",
            language="python",
            architecture="clean",
        )
        registry.register(ProjectTemplate(config=config))

        results = registry.search("python")
        assert len(results) == 1
        assert results[0].name == "python-clean"

    def test_search_by_tag(self) -> None:
        """Test searching templates by tag."""
        registry = TemplateRegistry()

        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
            tags=["tdd", "pydantic"],
        )
        registry.register(ProjectTemplate(config=config))

        results = registry.search("tdd")
        assert len(results) == 1

    def test_search_case_insensitive(self) -> None:
        """Test search is case insensitive."""
        registry = TemplateRegistry()

        config = TemplateConfig(
            name="Python-Clean",
            description="Python clean architecture",
            language="python",
            architecture="clean",
        )
        registry.register(ProjectTemplate(config=config))

        results = registry.search("PYTHON")
        assert len(results) == 1

    def test_apply_template(self, tmp_path: Path) -> None:
        """Test applying a template."""
        registry = TemplateRegistry()

        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(
            config=config,
            directories=[DirectoryTemplate("src", "Source")],
            files=[
                FileTemplate("src/main.py", "# Main\n"),
                FileTemplate("readme.md", "# {{ project_name }}"),
            ],
        )
        registry.register(template)

        created = registry.apply_template(
            "test",
            tmp_path,
            variables={"project_name": "MyProject"},
        )

        assert len(created) == 2
        assert (tmp_path / "src").is_dir()
        assert (tmp_path / "src" / "main.py").exists()
        assert (tmp_path / "readme.md").read_text() == "# MyProject"

    def test_apply_template_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test applying template creates parent directories."""
        registry = TemplateRegistry()

        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(
            config=config,
            files=[
                FileTemplate("src/deep/nested/file.py", "# Nested\n"),
            ],
        )
        registry.register(template)

        registry.apply_template("test", tmp_path)

        assert (tmp_path / "src" / "deep" / "nested" / "file.py").exists()

    def test_apply_nonexistent_template_raises(self, tmp_path: Path) -> None:
        """Test applying nonexistent template raises error."""
        registry = TemplateRegistry()

        with pytest.raises(ValueError, match="Template not found"):
            registry.apply_template("nonexistent", tmp_path)

    def test_validate_template_valid(self) -> None:
        """Test validating a valid template."""
        registry = TemplateRegistry()

        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(config=config)

        errors = registry.validate_template(template)
        assert errors == []

    def test_validate_template_missing_name(self) -> None:
        """Test validating template with missing name."""
        registry = TemplateRegistry()

        config = TemplateConfig(
            name="",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(config=config)

        errors = registry.validate_template(template)
        assert "Template name is required" in errors

    def test_validate_template_duplicate_files(self) -> None:
        """Test validating template with duplicate file paths."""
        registry = TemplateRegistry()

        config = TemplateConfig(
            name="test",
            description="Test",
            language="python",
            architecture="clean",
        )
        template = ProjectTemplate(
            config=config,
            files=[
                FileTemplate("src/main.py", "# Main"),
                FileTemplate("src/main.py", "# Duplicate"),
            ],
        )

        errors = registry.validate_template(template)
        assert "Duplicate file paths in template" in errors


class TestBuiltinTemplates:
    """Tests for built-in templates."""

    def test_python_clean_exists(self) -> None:
        """Test python-clean template exists."""
        assert "python-clean" in BUILTIN_TEMPLATES
        template = BUILTIN_TEMPLATES["python-clean"]
        assert template.config.language == "python"
        assert template.config.architecture == "clean"

    def test_go_hexagonal_exists(self) -> None:
        """Test go-hexagonal template exists."""
        assert "go-hexagonal" in BUILTIN_TEMPLATES
        template = BUILTIN_TEMPLATES["go-hexagonal"]
        assert template.config.language == "go"
        assert template.config.architecture == "hexagonal"

    def test_rust_ddd_exists(self) -> None:
        """Test rust-ddd template exists."""
        assert "rust-ddd" in BUILTIN_TEMPLATES
        template = BUILTIN_TEMPLATES["rust-ddd"]
        assert template.config.language == "rust"
        assert template.config.architecture == "ddd"

    def test_typescript_react_exists(self) -> None:
        """Test typescript-react template exists."""
        assert "typescript-react" in BUILTIN_TEMPLATES
        template = BUILTIN_TEMPLATES["typescript-react"]
        assert template.config.language == "typescript"

    def test_java_spring_exists(self) -> None:
        """Test java-spring template exists."""
        assert "java-spring" in BUILTIN_TEMPLATES
        template = BUILTIN_TEMPLATES["java-spring"]
        assert template.config.language == "java"

    def test_all_templates_have_files(self) -> None:
        """Test all templates have at least one file."""
        for name, template in BUILTIN_TEMPLATES.items():
            assert len(template.files) > 0, f"Template {name} has no files"

    def test_all_templates_valid(self) -> None:
        """Test all built-in templates pass validation."""
        registry = TemplateRegistry()
        for name, template in BUILTIN_TEMPLATES.items():
            errors = registry.validate_template(template)
            assert errors == [], f"Template {name} has errors: {errors}"

    def test_python_clean_has_pyproject(self) -> None:
        """Test python-clean template has pyproject.toml."""
        template = BUILTIN_TEMPLATES["python-clean"]
        file_paths = [f.path for f in template.files]
        assert "pyproject.toml" in file_paths

    def test_go_hexagonal_has_go_mod(self) -> None:
        """Test go-hexagonal template has go.mod."""
        template = BUILTIN_TEMPLATES["go-hexagonal"]
        file_paths = [f.path for f in template.files]
        assert "go.mod" in file_paths

    def test_rust_ddd_has_cargo_toml(self) -> None:
        """Test rust-ddd template has Cargo.toml."""
        template = BUILTIN_TEMPLATES["rust-ddd"]
        file_paths = [f.path for f in template.files]
        assert "Cargo.toml" in file_paths
