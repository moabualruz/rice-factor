"""Markdown adapter for documentation export.

Converts documentation specs to Markdown format.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from rice_factor.adapters.docs.doc_generator import (
    DocSection,
    DocumentationSpec,
)


class MarkdownStyle(Enum):
    """Markdown style variants."""

    STANDARD = "standard"
    GITHUB = "github"
    GITLAB = "gitlab"


class MarkdownAdapter:
    """Converts documentation specs to Markdown format.

    Generates Markdown documents from documentation specifications
    with support for different Markdown flavors.
    """

    def __init__(self, style: MarkdownStyle = MarkdownStyle.GITHUB) -> None:
        """Initialize the Markdown adapter.

        Args:
            style: Markdown style variant.
        """
        self.style = style

    def export(self, spec: DocumentationSpec) -> str:
        """Export a documentation spec to Markdown.

        Args:
            spec: Documentation specification.

        Returns:
            Markdown string.
        """
        lines: list[str] = []

        # Title
        lines.append(f"# {spec.title}")
        lines.append("")

        # Description
        if spec.description:
            lines.append(f"> {spec.description}")
            lines.append("")

        # Metadata as frontmatter for GitHub style
        if self.style == MarkdownStyle.GITHUB and spec.metadata:
            lines.insert(0, "---")
            for key, value in spec.metadata.items():
                lines.insert(1, f"{key}: {value}")
            lines.insert(1 + len(spec.metadata), "---")
            lines.insert(2 + len(spec.metadata), "")

        # Table of contents
        if len(spec.sections) > 2:
            lines.append("## Table of Contents")
            lines.append("")
            for section in spec.sections:
                anchor = self._generate_anchor(section.title)
                lines.append(f"- [{section.title}](#{anchor})")
            lines.append("")

        # Sections
        for section in spec.sections:
            section_lines = self._render_section(section)
            lines.extend(section_lines)

        return "\n".join(lines)

    def _render_section(self, section: DocSection) -> list[str]:
        """Render a section to Markdown lines.

        Args:
            section: Section to render.

        Returns:
            List of Markdown lines.
        """
        lines: list[str] = []

        # Heading
        heading_prefix = "#" * min(section.level + 1, 6)  # +1 because title is #
        lines.append(f"{heading_prefix} {section.title}")
        lines.append("")

        # Content
        if section.content:
            lines.append(section.content)
            lines.append("")

        # Subsections
        for subsection in section.subsections:
            subsection_lines = self._render_section(subsection)
            lines.extend(subsection_lines)

        return lines

    def _generate_anchor(self, title: str) -> str:
        """Generate a Markdown anchor from a title.

        Args:
            title: Section title.

        Returns:
            Anchor string.
        """
        # Convert to lowercase, replace spaces with hyphens
        anchor = title.lower()
        anchor = anchor.replace(" ", "-")
        # Remove special characters except hyphens
        anchor = "".join(c for c in anchor if c.isalnum() or c == "-")
        return anchor

    def export_to_file(
        self,
        spec: DocumentationSpec,
        filepath: str | Path,
    ) -> None:
        """Export documentation to a file.

        Args:
            spec: Documentation specification.
            filepath: Output file path.
        """
        content = self.export(spec)
        Path(filepath).write_text(content, encoding="utf-8")

    def export_multiple(
        self,
        specs: list[tuple[str, DocumentationSpec]],
    ) -> str:
        """Export multiple documentation specs as a single document.

        Args:
            specs: List of (title, spec) tuples.

        Returns:
            Combined Markdown document.
        """
        sections: list[str] = []

        for title, spec in specs:
            content = self.export(spec)
            # Replace main title with section reference
            content = content.replace(f"# {spec.title}", f"# {title}")
            sections.append(content)

        return "\n\n---\n\n".join(sections)


def generate_project_docs(project_plan: dict[str, Any]) -> str:
    """Convenience function to generate project documentation.

    Args:
        project_plan: ProjectPlanPayload as dictionary.

    Returns:
        Markdown documentation.
    """
    from rice_factor.adapters.docs.doc_generator import DocGenerator

    generator = DocGenerator()
    adapter = MarkdownAdapter()

    spec = generator.from_project_plan(project_plan)
    return adapter.export(spec)


def generate_test_docs(test_plan: dict[str, Any]) -> str:
    """Convenience function to generate test documentation.

    Args:
        test_plan: TestPlanPayload as dictionary.

    Returns:
        Markdown documentation.
    """
    from rice_factor.adapters.docs.doc_generator import DocGenerator

    generator = DocGenerator()
    adapter = MarkdownAdapter()

    spec = generator.from_test_plan(test_plan)
    return adapter.export(spec)


def generate_architecture_docs(arch_plan: dict[str, Any]) -> str:
    """Convenience function to generate architecture documentation.

    Args:
        arch_plan: ArchitecturePlanPayload as dictionary.

    Returns:
        Markdown documentation.
    """
    from rice_factor.adapters.docs.doc_generator import DocGenerator

    generator = DocGenerator()
    adapter = MarkdownAdapter()

    spec = generator.from_architecture_plan(arch_plan)
    return adapter.export(spec)
