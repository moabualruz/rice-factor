"""Schema injection utility for prompts.

This module provides the SchemaInjector class for loading JSON schemas
and injecting them into prompts.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar

from rice_factor.domain.artifacts.enums import ArtifactType


class SchemaNotFoundError(Exception):
    """Raised when a schema file cannot be found."""

    def __init__(self, artifact_type: ArtifactType, path: Path) -> None:
        self.artifact_type = artifact_type
        self.path = path
        super().__init__(f"Schema not found for {artifact_type.value} at {path}")


class SchemaInjector:
    """Loads and injects JSON schemas into prompts.

    Schemas are cached for performance after first load.
    """

    # Mapping from ArtifactType to schema filename
    SCHEMA_FILENAMES: ClassVar[dict[ArtifactType, str]] = {
        ArtifactType.PROJECT_PLAN: "project_plan.schema.json",
        ArtifactType.ARCHITECTURE_PLAN: "architecture_plan.schema.json",
        ArtifactType.SCAFFOLD_PLAN: "scaffold_plan.schema.json",
        ArtifactType.TEST_PLAN: "test_plan.schema.json",
        ArtifactType.IMPLEMENTATION_PLAN: "implementation_plan.schema.json",
        ArtifactType.REFACTOR_PLAN: "refactor_plan.schema.json",
        ArtifactType.VALIDATION_RESULT: "validation_result.schema.json",
        ArtifactType.FAILURE_REPORT: "failure_report.schema.json",
        ArtifactType.RECONCILIATION_PLAN: "reconciliation_plan.schema.json",
    }

    def __init__(self, schemas_dir: Path | None = None) -> None:
        """Initialize the schema injector.

        Args:
            schemas_dir: Path to the schemas directory. If None, uses
                        the default location (project root/schemas).
        """
        if schemas_dir is None:
            # Default to project root/schemas
            # This assumes we're running from within the project
            self._schemas_dir = Path(__file__).parent.parent.parent.parent / "schemas"
        else:
            self._schemas_dir = schemas_dir

    def load_schema(self, artifact_type: ArtifactType) -> dict[str, Any]:
        """Load a JSON schema for an artifact type.

        Args:
            artifact_type: The type of artifact to load schema for.

        Returns:
            The parsed JSON schema as a dictionary.

        Raises:
            SchemaNotFoundError: If the schema file doesn't exist.
            json.JSONDecodeError: If the schema is invalid JSON.
        """
        return self._load_schema_cached(artifact_type, self._schemas_dir)

    @staticmethod
    @lru_cache(maxsize=16)
    def _load_schema_cached(
        artifact_type: ArtifactType, schemas_dir: Path
    ) -> dict[str, Any]:
        """Load and cache a schema.

        Uses lru_cache for performance.

        Args:
            artifact_type: The artifact type.
            schemas_dir: Path to schemas directory.

        Returns:
            The parsed schema.
        """
        filename = SchemaInjector.SCHEMA_FILENAMES.get(artifact_type)
        if filename is None:
            raise SchemaNotFoundError(
                artifact_type,
                schemas_dir / f"<unknown_{artifact_type.value}>",
            )

        schema_path = schemas_dir / filename
        if not schema_path.exists():
            raise SchemaNotFoundError(artifact_type, schema_path)

        with schema_path.open(encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result

    def inject_schema(
        self,
        prompt: str,
        artifact_type: ArtifactType,
        *,
        placeholder: str = "{{SCHEMA}}",
    ) -> str:
        """Inject a schema into a prompt at the placeholder location.

        If the placeholder is not found, the schema is appended to the prompt.

        Args:
            prompt: The prompt text to inject into.
            artifact_type: The type of artifact to inject schema for.
            placeholder: The placeholder string to replace with the schema.

        Returns:
            The prompt with the schema injected.
        """
        schema = self.load_schema(artifact_type)
        schema_json = json.dumps(schema, indent=2)

        schema_section = f"""
JSON SCHEMA:
```json
{schema_json}
```

Your output MUST conform exactly to this schema."""

        if placeholder in prompt:
            return prompt.replace(placeholder, schema_section)
        else:
            return f"{prompt}\n{schema_section}"

    def format_schema_for_prompt(self, artifact_type: ArtifactType) -> str:
        """Format a schema as a string suitable for including in a prompt.

        Args:
            artifact_type: The type of artifact.

        Returns:
            Formatted schema string.
        """
        schema = self.load_schema(artifact_type)
        return json.dumps(schema, indent=2)

    def clear_cache(self) -> None:
        """Clear the schema cache.

        Useful for testing or when schemas are modified at runtime.
        """
        self._load_schema_cached.cache_clear()
