"""Documentation generation commands.

This module provides CLI commands for generating documentation from artifacts:
- rice-factor docs: Generate documentation from artifacts
"""

import json
from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel

from rice_factor.adapters.docs.doc_generator import (
    DocGenerator,
    DocumentationSpec,
)
from rice_factor.adapters.docs.markdown_adapter import (
    MarkdownAdapter,
    MarkdownStyle,
)
from rice_factor.entrypoints.cli.utils import (
    console,
    error,
    handle_errors,
    info,
    success,
    warning,
)


def _find_project_root(path: Path | None) -> Path:
    """Find the project root directory.

    Args:
        path: Starting path to search from. If None, uses CWD.

    Returns:
        Path to the project root.
    """
    start = path or Path.cwd()

    # Walk up looking for .project/ or artifacts/
    current = start
    for _ in range(10):
        if (current / ".project").is_dir() or (current / "artifacts").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent

    return start


def _load_artifact_by_type(
    artifacts_dir: Path, artifact_type: str
) -> dict[str, Any] | None:
    """Load the latest artifact of a specific type.

    Args:
        artifacts_dir: Directory containing artifact JSON files.
        artifact_type: Type of artifact to find.

    Returns:
        Artifact dictionary or None if not found.
    """
    type_map = {
        "project": "ProjectPlan",
        "test": "TestPlan",
        "scaffold": "ScaffoldPlan",
        "architecture": "ArchitecturePlan",
        "implementation": "ImplementationPlan",
        "refactor": "RefactorPlan",
    }

    target_type = type_map.get(artifact_type.lower())
    if not target_type:
        return None

    if not artifacts_dir.exists():
        return None

    # Find matching artifacts, sorted by modification time
    matching: list[tuple[Path, dict[str, Any]]] = []

    for file_path in artifacts_dir.glob("*.json"):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            if data.get("artifact_type") == target_type:
                matching.append((file_path, data))
        except (json.JSONDecodeError, OSError):
            continue

    if not matching:
        return None

    # Return most recently modified
    matching.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)
    return matching[0][1]


def _spec_to_json(spec: DocumentationSpec) -> dict[str, Any]:
    """Convert a documentation spec to JSON-serializable format.

    Args:
        spec: Documentation specification.

    Returns:
        JSON-serializable dictionary.
    """

    def section_to_dict(section: Any) -> dict[str, Any]:
        return {
            "title": section.title,
            "content": section.content,
            "level": section.level,
            "subsections": [section_to_dict(s) for s in section.subsections],
        }

    return {
        "title": spec.title,
        "description": spec.description,
        "metadata": spec.metadata,
        "sections": [section_to_dict(s) for s in spec.sections],
    }


@handle_errors
def docs(
    artifact_type: str = typer.Argument(
        None,
        help="Artifact type to document (project, test, scaffold, architecture)",
    ),
    path: Path = typer.Option(
        None, "--path", "-p", help="Project root path. Defaults to current directory."
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="Output file path. If not specified, outputs to stdout."
    ),
    style: str = typer.Option(
        "github",
        "--style",
        "-s",
        help="Markdown style: github, gitlab, standard.",
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: markdown, json.",
    ),
) -> None:
    """Generate documentation from artifacts.

    Creates readable documentation from artifact payloads in Markdown
    or JSON format.

    Examples:
        rice-factor docs project                # Document project plan
        rice-factor docs test --style gitlab   # GitLab-flavored markdown
        rice-factor docs project -o README.md  # Save to file
        rice-factor docs architecture --format json  # Output as JSON
    """
    project_root = _find_project_root(path)
    artifacts_dir = project_root / "artifacts"

    if not artifacts_dir.exists():
        warning(f"No artifacts directory found at {artifacts_dir}")
        info("Run 'rice-factor plan project' to create artifacts")
        raise typer.Exit(1)

    if artifact_type is None:
        error("Please specify an artifact type")
        info("Valid types: project, test, scaffold, architecture")
        raise typer.Exit(1)

    generator = DocGenerator()
    spec: DocumentationSpec | None = None

    # Load artifact and generate documentation
    if artifact_type.lower() == "project":
        artifact = _load_artifact_by_type(artifacts_dir, "project")
        if not artifact:
            warning("No ProjectPlan artifact found")
            raise typer.Exit(1)
        payload = artifact.get("payload", {})
        spec = generator.from_project_plan(payload)

    elif artifact_type.lower() == "test":
        artifact = _load_artifact_by_type(artifacts_dir, "test")
        if not artifact:
            warning("No TestPlan artifact found")
            raise typer.Exit(1)
        payload = artifact.get("payload", {})
        spec = generator.from_test_plan(payload)

    elif artifact_type.lower() == "scaffold":
        artifact = _load_artifact_by_type(artifacts_dir, "scaffold")
        if not artifact:
            warning("No ScaffoldPlan artifact found")
            raise typer.Exit(1)
        payload = artifact.get("payload", {})
        spec = generator.from_scaffold_plan(payload)

    elif artifact_type.lower() in ("architecture", "arch"):
        artifact = _load_artifact_by_type(artifacts_dir, "architecture")
        if not artifact:
            warning("No ArchitecturePlan artifact found")
            raise typer.Exit(1)
        payload = artifact.get("payload", {})
        spec = generator.from_architecture_plan(payload)

    elif artifact_type.lower() == "refactor":
        artifact = _load_artifact_by_type(artifacts_dir, "refactor")
        if not artifact:
            warning("No RefactorPlan artifact found")
            raise typer.Exit(1)
        payload = artifact.get("payload", {})
        spec = generator.from_refactor_plan(payload)

    else:
        error(f"Unknown artifact type: {artifact_type}")
        info("Valid types: project, test, scaffold, architecture, refactor")
        raise typer.Exit(1)

    if spec is None:
        warning("Failed to generate documentation")
        raise typer.Exit(1)

    # Generate output
    if format.lower() == "json":
        content = json.dumps(_spec_to_json(spec), indent=2)
    elif format.lower() == "markdown":
        # Determine markdown style
        style_map = {
            "github": MarkdownStyle.GITHUB,
            "gitlab": MarkdownStyle.GITLAB,
            "standard": MarkdownStyle.STANDARD,
        }
        md_style = style_map.get(style.lower(), MarkdownStyle.GITHUB)
        adapter = MarkdownAdapter(style=md_style)
        content = adapter.export(spec)
    else:
        error(f"Unknown format: {format}. Use 'markdown' or 'json'.")
        raise typer.Exit(1)

    # Output
    if output:
        output.write_text(content, encoding="utf-8")
        success(f"Generated documentation at {output}")
        info(f"Sections: {len(spec.sections)}")
    else:
        console.print()
        console.print(
            Panel(
                f"[bold]Generated Documentation[/bold]\n\n"
                f"Type: {artifact_type}\n"
                f"Style: {style}\n"
                f"Sections: {len(spec.sections)}",
                border_style="blue",
            )
        )
        console.print()
        console.print(content)
