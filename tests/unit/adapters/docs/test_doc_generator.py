"""Tests for DocGenerator."""

from __future__ import annotations

import pytest

from rice_factor.adapters.docs import (
    DocFormat,
    DocGenerator,
    DocSection,
)
from rice_factor.adapters.docs.doc_generator import DocumentationSpec


class TestDocSection:
    """Tests for DocSection."""

    def test_create_section(self) -> None:
        """Test creating a documentation section."""
        section = DocSection(title="Introduction", content="Welcome to the docs.")
        assert section.title == "Introduction"
        assert section.content == "Welcome to the docs."
        assert section.level == 1
        assert section.subsections == []

    def test_add_subsection(self) -> None:
        """Test adding subsections."""
        section = DocSection(title="Main")
        sub = DocSection(title="Sub", content="Content")
        section.add_subsection(sub)

        assert len(section.subsections) == 1
        assert section.subsections[0].level == 2  # Auto-incremented


class TestDocumentationSpec:
    """Tests for DocumentationSpec."""

    def test_create_spec(self) -> None:
        """Test creating a documentation spec."""
        spec = DocumentationSpec(
            title="My Docs",
            description="Documentation for my project",
        )
        assert spec.title == "My Docs"
        assert spec.description == "Documentation for my project"
        assert spec.sections == []

    def test_add_section(self) -> None:
        """Test adding sections."""
        spec = DocumentationSpec(title="Docs")
        spec.add_section(DocSection(title="Section 1"))
        spec.add_section(DocSection(title="Section 2"))

        assert len(spec.sections) == 2


class TestDocFormat:
    """Tests for DocFormat enum."""

    def test_all_formats(self) -> None:
        """Test all documentation formats."""
        assert DocFormat.MARKDOWN.value == "markdown"
        assert DocFormat.HTML.value == "html"
        assert DocFormat.RST.value == "rst"
        assert DocFormat.ASCIIDOC.value == "asciidoc"


class TestDocGeneratorProjectPlan:
    """Tests for DocGenerator.from_project_plan."""

    def test_basic_project_plan(self) -> None:
        """Test generating docs from basic project plan."""
        generator = DocGenerator()
        payload = {
            "domains": [
                {"name": "core", "responsibility": "Business logic"},
            ],
            "modules": [
                {"name": "auth", "domain": "core"},
            ],
            "constraints": {
                "architecture": "hexagonal",
                "languages": ["python"],
            },
        }

        spec = generator.from_project_plan(payload)

        assert spec.title == "Project Documentation"
        assert len(spec.sections) >= 3  # Overview, Domains, Modules

    def test_project_plan_with_polyglot(self) -> None:
        """Test project plan with polyglot configuration."""
        generator = DocGenerator()
        payload = {
            "domains": [{"name": "core", "responsibility": "Business"}],
            "modules": [{"name": "api", "domain": "core"}],
            "constraints": {"architecture": "clean", "languages": ["python", "go"]},
            "polyglot": {
                "primary_language": "python",
                "language_configs": [
                    {"name": "python", "version": "3.11", "test_runner": "pytest"},
                    {"name": "go", "version": "1.21"},
                ],
            },
        }

        spec = generator.from_project_plan(payload)

        # Should have polyglot section
        section_titles = [s.title for s in spec.sections]
        assert "Polyglot Configuration" in section_titles


class TestDocGeneratorArchitecturePlan:
    """Tests for DocGenerator.from_architecture_plan."""

    def test_basic_architecture_plan(self) -> None:
        """Test generating docs from architecture plan."""
        generator = DocGenerator()
        payload = {
            "layers": ["domain", "application", "infrastructure"],
            "rules": [
                {"rule": "DOMAIN_CANNOT_IMPORT_INFRASTRUCTURE"},
            ],
        }

        spec = generator.from_architecture_plan(payload)

        assert spec.title == "Architecture Documentation"
        assert len(spec.sections) >= 1

    def test_architecture_plan_layers(self) -> None:
        """Test architecture plan includes layers."""
        generator = DocGenerator()
        payload = {
            "layers": ["domain", "app", "infra"],
            "rules": [],
        }

        spec = generator.from_architecture_plan(payload)

        layers_section = spec.sections[0]
        assert layers_section.title == "Layers"
        assert len(layers_section.subsections) == 3


class TestDocGeneratorTestPlan:
    """Tests for DocGenerator.from_test_plan."""

    def test_basic_test_plan(self) -> None:
        """Test generating docs from test plan."""
        generator = DocGenerator()
        payload = {
            "tests": [
                {"id": "test-1", "target": "auth.login", "assertions": ["works"]},
                {"id": "test-2", "target": "auth.logout", "assertions": ["clears"]},
            ]
        }

        spec = generator.from_test_plan(payload)

        assert spec.title == "Test Plan Documentation"
        assert len(spec.sections) >= 2

    def test_test_plan_groups_by_target(self) -> None:
        """Test that tests are grouped by target."""
        generator = DocGenerator()
        payload = {
            "tests": [
                {"id": "test-1", "target": "auth.login", "assertions": ["a1"]},
                {"id": "test-2", "target": "auth.login", "assertions": ["a2"]},
                {"id": "test-3", "target": "auth.logout", "assertions": ["a3"]},
            ]
        }

        spec = generator.from_test_plan(payload)

        # Tests by Target section
        tests_section = spec.sections[1]
        assert tests_section.title == "Tests by Target"
        assert len(tests_section.subsections) == 2  # 2 unique targets


class TestDocGeneratorScaffoldPlan:
    """Tests for DocGenerator.from_scaffold_plan."""

    def test_basic_scaffold_plan(self) -> None:
        """Test generating docs from scaffold plan."""
        generator = DocGenerator()
        payload = {
            "files": [
                {"path": "src/main.py", "kind": "source", "description": "Entry point"},
                {"path": "tests/test_main.py", "kind": "test"},
            ]
        }

        spec = generator.from_scaffold_plan(payload)

        assert spec.title == "File Structure Documentation"
        assert len(spec.sections) >= 2

    def test_scaffold_plan_groups_by_directory(self) -> None:
        """Test that files are grouped by directory."""
        generator = DocGenerator()
        payload = {
            "files": [
                {"path": "src/main.py", "kind": "source"},
                {"path": "src/utils.py", "kind": "source"},
                {"path": "tests/test_main.py", "kind": "test"},
            ]
        }

        spec = generator.from_scaffold_plan(payload)

        # Directory Structure section
        structure_section = spec.sections[1]
        assert structure_section.title == "Directory Structure"
        assert len(structure_section.subsections) == 2  # src, tests


class TestDocGeneratorRefactorPlan:
    """Tests for DocGenerator.from_refactor_plan."""

    def test_basic_refactor_plan(self) -> None:
        """Test generating docs from refactor plan."""
        generator = DocGenerator()
        payload = {
            "goal": "Reorganize auth module",
            "operations": [
                {"type": "move_file", "from": "auth.py", "to": "auth/core.py"},
            ],
        }

        spec = generator.from_refactor_plan(payload)

        assert spec.title == "Refactoring Plan Documentation"
        assert len(spec.sections) >= 2

    def test_refactor_plan_with_constraints(self) -> None:
        """Test refactor plan includes constraints."""
        generator = DocGenerator()
        payload = {
            "goal": "Rename symbol",
            "operations": [{"type": "rename_symbol", "symbol": "foo"}],
            "constraints": {
                "preserve_behavior": True,
                "preserve_tests": True,
            },
        }

        spec = generator.from_refactor_plan(payload)

        section_titles = [s.title for s in spec.sections]
        assert "Constraints" in section_titles


class TestDocGeneratorEdgeCases:
    """Tests for edge cases."""

    def test_empty_project_plan(self) -> None:
        """Test handling empty project plan."""
        generator = DocGenerator()
        payload = {
            "domains": [],
            "modules": [],
            "constraints": {"architecture": "unknown", "languages": []},
        }

        spec = generator.from_project_plan(payload)
        assert spec.title == "Project Documentation"

    def test_missing_optional_fields(self) -> None:
        """Test handling missing optional fields."""
        generator = DocGenerator()
        payload = {
            "domains": [{"name": "core"}],  # missing responsibility
            "modules": [{"name": "auth"}],  # missing domain
            "constraints": {"architecture": "clean", "languages": ["python"]},
        }

        # Should not raise
        spec = generator.from_project_plan(payload)
        assert spec is not None
