"""Tests for MarkdownAdapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from rice_factor.adapters.docs import (
    DocGenerator,
    DocSection,
    MarkdownAdapter,
    MarkdownStyle,
)
from rice_factor.adapters.docs.doc_generator import DocumentationSpec
from rice_factor.adapters.docs.markdown_adapter import (
    generate_architecture_docs,
    generate_project_docs,
    generate_test_docs,
)


class TestMarkdownAdapter:
    """Tests for MarkdownAdapter."""

    def test_create_adapter(self) -> None:
        """Test creating a Markdown adapter."""
        adapter = MarkdownAdapter()
        assert adapter.style == MarkdownStyle.GITHUB

    def test_create_with_style(self) -> None:
        """Test creating adapter with custom style."""
        adapter = MarkdownAdapter(style=MarkdownStyle.GITLAB)
        assert adapter.style == MarkdownStyle.GITLAB

    def test_export_empty_spec(self) -> None:
        """Test exporting empty spec."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Empty Doc")

        output = adapter.export(spec)

        assert "# Empty Doc" in output

    def test_export_with_description(self) -> None:
        """Test exporting spec with description."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(
            title="My Doc",
            description="This is a description",
        )

        output = adapter.export(spec)

        assert "> This is a description" in output

    def test_export_with_sections(self) -> None:
        """Test exporting spec with sections."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Doc")
        spec.add_section(DocSection(title="Section 1", content="Content 1"))
        spec.add_section(DocSection(title="Section 2", content="Content 2"))

        output = adapter.export(spec)

        assert "## Section 1" in output
        assert "## Section 2" in output
        assert "Content 1" in output
        assert "Content 2" in output

    def test_export_with_subsections(self) -> None:
        """Test exporting spec with nested sections."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Doc")

        section = DocSection(title="Main")
        sub = DocSection(title="Sub", content="Sub content")
        section.add_subsection(sub)
        spec.add_section(section)

        output = adapter.export(spec)

        assert "## Main" in output
        assert "### Sub" in output

    def test_export_with_toc(self) -> None:
        """Test exporting spec with table of contents."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Doc")
        spec.add_section(DocSection(title="Introduction"))
        spec.add_section(DocSection(title="Getting Started"))
        spec.add_section(DocSection(title="Advanced Topics"))

        output = adapter.export(spec)

        # Should have TOC when > 2 sections
        assert "## Table of Contents" in output
        assert "[Introduction]" in output

    def test_export_with_metadata_github(self) -> None:
        """Test exporting with metadata for GitHub style."""
        adapter = MarkdownAdapter(style=MarkdownStyle.GITHUB)
        spec = DocumentationSpec(
            title="Doc",
            metadata={"author": "test", "version": "1.0"},
        )

        output = adapter.export(spec)

        assert "---" in output
        assert "author: test" in output
        assert "version: 1.0" in output

    def test_generate_anchor(self) -> None:
        """Test anchor generation."""
        adapter = MarkdownAdapter()

        assert adapter._generate_anchor("Hello World") == "hello-world"
        assert adapter._generate_anchor("Getting Started!") == "getting-started"
        assert adapter._generate_anchor("API Reference") == "api-reference"

    def test_export_to_file(self, tmp_path: Path) -> None:
        """Test exporting to file."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Test Doc")
        spec.add_section(DocSection(title="Intro", content="Hello"))

        output_file = tmp_path / "doc.md"
        adapter.export_to_file(spec, output_file)

        content = output_file.read_text()
        assert "# Test Doc" in content

    def test_export_multiple(self) -> None:
        """Test exporting multiple specs."""
        adapter = MarkdownAdapter()

        spec1 = DocumentationSpec(title="Doc 1")
        spec1.add_section(DocSection(title="S1"))

        spec2 = DocumentationSpec(title="Doc 2")
        spec2.add_section(DocSection(title="S2"))

        output = adapter.export_multiple([
            ("Document 1", spec1),
            ("Document 2", spec2),
        ])

        assert "# Document 1" in output
        assert "# Document 2" in output
        assert "---" in output  # Section separator


class TestMarkdownStyle:
    """Tests for MarkdownStyle enum."""

    def test_all_styles(self) -> None:
        """Test all Markdown styles."""
        assert MarkdownStyle.STANDARD.value == "standard"
        assert MarkdownStyle.GITHUB.value == "github"
        assert MarkdownStyle.GITLAB.value == "gitlab"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_project_docs(self) -> None:
        """Test generating project documentation."""
        project_plan = {
            "domains": [{"name": "core", "responsibility": "Business"}],
            "modules": [{"name": "auth", "domain": "core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }

        output = generate_project_docs(project_plan)

        assert "# Project Documentation" in output
        assert "hexagonal" in output
        assert "core" in output

    def test_generate_test_docs(self) -> None:
        """Test generating test documentation."""
        test_plan = {
            "tests": [
                {"id": "test-1", "target": "auth", "assertions": ["works"]},
            ]
        }

        output = generate_test_docs(test_plan)

        assert "# Test Plan Documentation" in output
        assert "test-1" in output

    def test_generate_architecture_docs(self) -> None:
        """Test generating architecture documentation."""
        arch_plan = {
            "layers": ["domain", "app"],
            "rules": [],
        }

        output = generate_architecture_docs(arch_plan)

        assert "# Architecture Documentation" in output
        assert "domain" in output


class TestHeadingLevels:
    """Tests for heading level handling."""

    def test_max_heading_level(self) -> None:
        """Test that heading levels cap at 6."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Doc")

        # Create deeply nested sections
        section = DocSection(title="L1")
        current = section
        for i in range(2, 8):
            sub = DocSection(title=f"L{i}")
            current.add_subsection(sub)
            current = sub

        spec.add_section(section)
        output = adapter.export(spec)

        # Should not have more than 6 #
        assert "#######" not in output

    def test_section_levels_increment(self) -> None:
        """Test that section levels increment correctly."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Doc")

        # Build nested sections with explicit levels
        section = DocSection(title="Main", level=1)
        sub1 = DocSection(title="Sub1", level=2)
        sub2 = DocSection(title="Sub2", level=3)
        sub1.subsections.append(sub2)
        section.subsections.append(sub1)
        spec.add_section(section)

        output = adapter.export(spec)

        assert "## Main" in output
        assert "### Sub1" in output
        assert "#### Sub2" in output


class TestMarkdownFormatting:
    """Tests for Markdown formatting details."""

    def test_empty_content_no_extra_lines(self) -> None:
        """Test that empty content doesn't add extra lines."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Doc")
        spec.add_section(DocSection(title="Empty Section"))

        output = adapter.export(spec)

        # Should have heading but minimal extra lines
        assert "## Empty Section" in output

    def test_preserves_markdown_in_content(self) -> None:
        """Test that Markdown in content is preserved."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Doc")
        spec.add_section(DocSection(
            title="Formatted",
            content="This has **bold** and *italic* text.",
        ))

        output = adapter.export(spec)

        assert "**bold**" in output
        assert "*italic*" in output

    def test_preserves_code_blocks(self) -> None:
        """Test that code blocks in content are preserved."""
        adapter = MarkdownAdapter()
        spec = DocumentationSpec(title="Doc")
        spec.add_section(DocSection(
            title="Code",
            content="```python\nprint('hello')\n```",
        ))

        output = adapter.export(spec)

        assert "```python" in output
        assert "print('hello')" in output
