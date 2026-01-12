"""Documentation generator from artifacts.

Generates documentation from artifact payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DocFormat(Enum):
    """Supported documentation formats."""

    MARKDOWN = "markdown"
    HTML = "html"
    RST = "rst"
    ASCIIDOC = "asciidoc"


@dataclass
class DocSection:
    """A section of documentation.

    Attributes:
        title: Section title.
        content: Section content.
        level: Heading level (1-6).
        subsections: Child sections.
    """

    title: str
    content: str = ""
    level: int = 1
    subsections: list["DocSection"] = field(default_factory=list)

    def add_subsection(self, section: "DocSection") -> None:
        """Add a subsection.

        Args:
            section: Subsection to add.
        """
        section.level = self.level + 1
        self.subsections.append(section)


@dataclass
class DocumentationSpec:
    """Complete documentation specification.

    Attributes:
        title: Document title.
        description: Document description.
        sections: Top-level sections.
        metadata: Additional metadata.
    """

    title: str
    description: str = ""
    sections: list[DocSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_section(self, section: DocSection) -> None:
        """Add a top-level section.

        Args:
            section: Section to add.
        """
        self.sections.append(section)


class DocGenerator:
    """Generates documentation from artifacts.

    Creates structured documentation from artifact payloads
    that can be exported to various formats.
    """

    def __init__(self) -> None:
        """Initialize the documentation generator."""
        pass

    def from_project_plan(self, payload: dict[str, Any]) -> DocumentationSpec:
        """Generate documentation from a ProjectPlan payload.

        Args:
            payload: ProjectPlanPayload as dictionary.

        Returns:
            Documentation specification.
        """
        doc = DocumentationSpec(
            title="Project Documentation",
            description="Generated from ProjectPlan artifact",
        )

        # Overview section
        constraints = payload.get("constraints", {})
        arch = constraints.get("architecture", "unknown")
        languages = constraints.get("languages", [])

        overview = DocSection(
            title="Overview",
            content=f"This project uses **{arch}** architecture with {', '.join(languages)}.",
        )
        doc.add_section(overview)

        # Domains section
        domains_section = DocSection(title="Domains")
        for domain in payload.get("domains", []):
            domain_sub = DocSection(
                title=domain.get("name", "Unknown"),
                content=domain.get("responsibility", ""),
            )
            domains_section.add_subsection(domain_sub)
        doc.add_section(domains_section)

        # Modules section
        modules_section = DocSection(title="Modules")
        for module in payload.get("modules", []):
            name = module.get("name", "Unknown")
            domain = module.get("domain", "Unknown")
            module_sub = DocSection(
                title=name,
                content=f"Belongs to domain: **{domain}**",
            )
            modules_section.add_subsection(module_sub)
        doc.add_section(modules_section)

        # Polyglot section if present
        polyglot = payload.get("polyglot")
        if polyglot and polyglot.get("language_configs"):
            polyglot_section = DocSection(title="Polyglot Configuration")
            primary = polyglot.get("primary_language", "")
            if primary:
                polyglot_section.content = f"Primary language: **{primary}**"

            for lang_config in polyglot.get("language_configs", []):
                lang_sub = DocSection(
                    title=lang_config.get("name", "Unknown"),
                    content=self._format_language_config(lang_config),
                )
                polyglot_section.add_subsection(lang_sub)
            doc.add_section(polyglot_section)

        return doc

    def from_architecture_plan(self, payload: dict[str, Any]) -> DocumentationSpec:
        """Generate documentation from an ArchitecturePlan payload.

        Args:
            payload: ArchitecturePlanPayload as dictionary.

        Returns:
            Documentation specification.
        """
        doc = DocumentationSpec(
            title="Architecture Documentation",
            description="Generated from ArchitecturePlan artifact",
        )

        # Layers section
        layers = payload.get("layers", [])
        layers_section = DocSection(
            title="Layers",
            content=f"The system is organized into {len(layers)} layers.",
        )
        for i, layer in enumerate(layers, 1):
            layer_sub = DocSection(
                title=f"Layer {i}: {layer}",
                content=f"Description of the {layer} layer.",
            )
            layers_section.add_subsection(layer_sub)
        doc.add_section(layers_section)

        # Rules section
        rules = payload.get("rules", [])
        if rules:
            rules_section = DocSection(
                title="Dependency Rules",
                content="The following dependency rules are enforced:",
            )
            for rule in rules:
                rule_value = rule.get("rule", "")
                rule_sub = DocSection(
                    title=rule_value.replace("_", " ").title(),
                    content=f"Rule: `{rule_value}`",
                )
                rules_section.add_subsection(rule_sub)
            doc.add_section(rules_section)

        return doc

    def from_test_plan(self, payload: dict[str, Any]) -> DocumentationSpec:
        """Generate documentation from a TestPlan payload.

        Args:
            payload: TestPlanPayload as dictionary.

        Returns:
            Documentation specification.
        """
        doc = DocumentationSpec(
            title="Test Plan Documentation",
            description="Generated from TestPlan artifact",
        )

        tests = payload.get("tests", [])

        # Summary section
        summary = DocSection(
            title="Summary",
            content=f"This test plan contains **{len(tests)}** test definitions.",
        )
        doc.add_section(summary)

        # Group tests by target
        targets: dict[str, list[dict[str, Any]]] = {}
        for test in tests:
            target = test.get("target", "Unknown")
            if target not in targets:
                targets[target] = []
            targets[target].append(test)

        # Tests by target
        tests_section = DocSection(title="Tests by Target")
        for target, target_tests in sorted(targets.items()):
            target_sub = DocSection(
                title=target,
                content=f"**{len(target_tests)}** tests for this target.",
            )

            for test in target_tests:
                test_id = test.get("id", "Unknown")
                assertions = test.get("assertions", [])
                assertions_text = "\n".join(f"- {a}" for a in assertions)
                test_sub = DocSection(
                    title=test_id,
                    content=f"**Assertions:**\n{assertions_text}" if assertions else "",
                )
                target_sub.add_subsection(test_sub)

            tests_section.add_subsection(target_sub)

        doc.add_section(tests_section)

        return doc

    def from_scaffold_plan(self, payload: dict[str, Any]) -> DocumentationSpec:
        """Generate documentation from a ScaffoldPlan payload.

        Args:
            payload: ScaffoldPlanPayload as dictionary.

        Returns:
            Documentation specification.
        """
        doc = DocumentationSpec(
            title="File Structure Documentation",
            description="Generated from ScaffoldPlan artifact",
        )

        files = payload.get("files", [])

        # Summary
        summary = DocSection(
            title="Summary",
            content=f"This scaffold defines **{len(files)}** files.",
        )
        doc.add_section(summary)

        # Group by directory
        directories: dict[str, list[dict[str, Any]]] = {}
        for file_entry in files:
            path = file_entry.get("path", "")
            if "/" in path:
                directory = "/".join(path.split("/")[:-1])
            else:
                directory = "root"
            if directory not in directories:
                directories[directory] = []
            directories[directory].append(file_entry)

        # Files by directory
        structure_section = DocSection(title="Directory Structure")
        for directory, dir_files in sorted(directories.items()):
            dir_sub = DocSection(
                title=f"`{directory}/`",
            )

            for file_entry in dir_files:
                path = file_entry.get("path", "")
                filename = path.split("/")[-1]
                kind = file_entry.get("kind", "source")
                desc = file_entry.get("description", "")

                file_sub = DocSection(
                    title=f"`{filename}`",
                    content=f"**Kind:** {kind}\n\n{desc}" if desc else f"**Kind:** {kind}",
                )
                dir_sub.add_subsection(file_sub)

            structure_section.add_subsection(dir_sub)

        doc.add_section(structure_section)

        return doc

    def from_refactor_plan(self, payload: dict[str, Any]) -> DocumentationSpec:
        """Generate documentation from a RefactorPlan payload.

        Args:
            payload: RefactorPlanPayload as dictionary.

        Returns:
            Documentation specification.
        """
        doc = DocumentationSpec(
            title="Refactoring Plan Documentation",
            description="Generated from RefactorPlan artifact",
        )

        goal = payload.get("goal", "")
        operations = payload.get("operations", [])

        # Goal section
        goal_section = DocSection(
            title="Goal",
            content=goal,
        )
        doc.add_section(goal_section)

        # Operations section
        ops_section = DocSection(
            title="Operations",
            content=f"**{len(operations)}** operations to perform:",
        )

        for i, op in enumerate(operations, 1):
            op_type = op.get("type", "unknown")
            from_path = op.get("from", op.get("from_path", ""))
            to_path = op.get("to", op.get("to_path", ""))
            symbol = op.get("symbol", "")

            content_parts = [f"**Type:** {op_type}"]
            if from_path:
                content_parts.append(f"**From:** `{from_path}`")
            if to_path:
                content_parts.append(f"**To:** `{to_path}`")
            if symbol:
                content_parts.append(f"**Symbol:** `{symbol}`")

            op_sub = DocSection(
                title=f"Operation {i}",
                content="\n\n".join(content_parts),
            )
            ops_section.add_subsection(op_sub)

        doc.add_section(ops_section)

        # Constraints if present
        constraints = payload.get("constraints")
        if constraints:
            constraints_section = DocSection(
                title="Constraints",
                content="",
            )
            if constraints.get("preserve_behavior"):
                constraints_section.content += "- Behavior must be preserved\n"
            if constraints.get("preserve_tests"):
                constraints_section.content += "- Tests must continue to pass\n"
            doc.add_section(constraints_section)

        return doc

    def _format_language_config(self, config: dict[str, Any]) -> str:
        """Format a language configuration as content.

        Args:
            config: Language configuration dictionary.

        Returns:
            Formatted content string.
        """
        parts = []

        if config.get("version"):
            parts.append(f"**Version:** {config['version']}")
        if config.get("framework"):
            parts.append(f"**Framework:** {config['framework']}")
        if config.get("package_manager"):
            parts.append(f"**Package Manager:** {config['package_manager']}")
        if config.get("test_runner"):
            parts.append(f"**Test Runner:** {config['test_runner']}")

        return "\n\n".join(parts) if parts else "No additional configuration."
