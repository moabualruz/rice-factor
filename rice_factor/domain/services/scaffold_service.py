"""Scaffold service for creating file structure from ScaffoldPlan.

This module provides the ScaffoldService for executing scaffold operations,
creating directories and files with appropriate TODO comments.
"""

from dataclasses import dataclass
from pathlib import Path

from rice_factor.domain.artifacts.payloads.scaffold_plan import (
    FileEntry,
    FileKind,
    ScaffoldPlanPayload,
)

# TODO comment templates by file kind and extension
TODO_TEMPLATES: dict[FileKind, dict[str, str]] = {
    FileKind.SOURCE: {
        ".py": '"""TODO: Implement {description}."""\n',
        ".js": "// TODO: Implement {description}\n",
        ".ts": "// TODO: Implement {description}\n",
        ".go": "// TODO: Implement {description}\n",
        ".rs": "// TODO: Implement {description}\n",
        ".java": "// TODO: Implement {description}\n",
        ".c": "// TODO: Implement {description}\n",
        ".cpp": "// TODO: Implement {description}\n",
        ".h": "// TODO: Implement {description}\n",
        ".rb": "# TODO: Implement {description}\n",
        ".sh": "# TODO: Implement {description}\n",
        "default": "# TODO: Implement {description}\n",
    },
    FileKind.TEST: {
        ".py": '"""TODO: Implement tests for {description}."""\n',
        ".js": "// TODO: Implement tests for {description}\n",
        ".ts": "// TODO: Implement tests for {description}\n",
        ".go": "// TODO: Implement tests for {description}\n",
        ".rs": "// TODO: Implement tests for {description}\n",
        ".java": "// TODO: Implement tests for {description}\n",
        "default": "# TODO: Implement tests for {description}\n",
    },
    FileKind.CONFIG: {
        ".yaml": "# TODO: Configure {description}\n",
        ".yml": "# TODO: Configure {description}\n",
        ".toml": "# TODO: Configure {description}\n",
        ".ini": "; TODO: Configure {description}\n",
        ".json": "",  # JSON doesn't support comments
        ".xml": "<!-- TODO: Configure {description} -->\n",
        "default": "# TODO: Configure {description}\n",
    },
    FileKind.DOC: {
        ".md": "<!-- TODO: Document {description} -->\n\n# {description}\n",
        ".rst": ".. TODO: Document {description}\n\n{description}\n",
        ".txt": "TODO: Document {description}\n",
        ".html": "<!-- TODO: Document {description} -->\n",
        "default": "<!-- TODO: Document {description} -->\n",
    },
}


@dataclass
class ScaffoldResult:
    """Result of a scaffold operation.

    Attributes:
        created: List of files that were created.
        skipped: List of files that were skipped (already existed).
        errors: List of (path, error) tuples for files that failed.
    """

    created: list[str]
    skipped: list[str]
    errors: list[tuple[str, str]]

    @property
    def success(self) -> bool:
        """Check if scaffold completed without errors."""
        return len(self.errors) == 0


class ScaffoldService:
    """Service for executing scaffold operations.

    The ScaffoldService creates directories and files based on a ScaffoldPlan,
    adding appropriate TODO comments based on file type.

    Attributes:
        project_root: Root directory for scaffold operations.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the scaffold service.

        Args:
            project_root: Root directory where files will be created.
        """
        self._project_root = project_root

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    def generate_todo_comment(self, entry: FileEntry) -> str:
        """Generate a TODO comment for a file entry.

        Args:
            entry: The file entry to generate a comment for.

        Returns:
            A TODO comment string appropriate for the file type.
        """
        ext = Path(entry.path).suffix.lower()
        templates = TODO_TEMPLATES.get(entry.kind, TODO_TEMPLATES[FileKind.SOURCE])
        template = templates.get(ext, templates.get("default", ""))
        return template.format(description=entry.description)

    def scaffold(
        self,
        plan: ScaffoldPlanPayload,
        *,
        dry_run: bool = False,
    ) -> ScaffoldResult:
        """Execute scaffold operations from a plan.

        Creates directories and files according to the scaffold plan.
        Existing files are skipped with a warning.

        Args:
            plan: The ScaffoldPlan to execute.
            dry_run: If True, don't actually create files.

        Returns:
            ScaffoldResult with created, skipped, and error information.
        """
        created: list[str] = []
        skipped: list[str] = []
        errors: list[tuple[str, str]] = []

        for entry in plan.files:
            file_path = self._project_root / entry.path

            # Skip existing files
            if file_path.exists():
                skipped.append(entry.path)
                continue

            if dry_run:
                created.append(entry.path)
                continue

            try:
                # Create parent directories
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Generate content with TODO comment
                content = self.generate_todo_comment(entry)

                # Write file
                file_path.write_text(content, encoding="utf-8")
                created.append(entry.path)

            except OSError as e:
                errors.append((entry.path, str(e)))

        return ScaffoldResult(
            created=created,
            skipped=skipped,
            errors=errors,
        )

    def preview(self, plan: ScaffoldPlanPayload) -> list[tuple[str, FileKind, bool]]:
        """Preview scaffold operations.

        Args:
            plan: The ScaffoldPlan to preview.

        Returns:
            List of (path, kind, would_create) tuples.
        """
        result: list[tuple[str, FileKind, bool]] = []
        for entry in plan.files:
            file_path = self._project_root / entry.path
            would_create = not file_path.exists()
            result.append((entry.path, entry.kind, would_create))
        return result
