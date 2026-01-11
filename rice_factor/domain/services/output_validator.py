"""Output validation service.

This module provides the OutputValidator class for validating LLM output
against JSON schemas and checking for code in the output.
"""

import json
from pathlib import Path
from typing import Any

import jsonschema

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.failures.llm_errors import (
    CodeInOutputError,
    InvalidJSONError,
    SchemaViolationError,
)
from rice_factor.domain.services.code_detector import CodeDetector

# Mapping from ArtifactType to schema filename
SCHEMA_FILE_MAP: dict[ArtifactType, str] = {
    ArtifactType.PROJECT_PLAN: "project_plan.schema.json",
    ArtifactType.ARCHITECTURE_PLAN: "architecture_plan.schema.json",
    ArtifactType.SCAFFOLD_PLAN: "scaffold_plan.schema.json",
    ArtifactType.TEST_PLAN: "test_plan.schema.json",
    ArtifactType.IMPLEMENTATION_PLAN: "implementation_plan.schema.json",
    ArtifactType.REFACTOR_PLAN: "refactor_plan.schema.json",
    ArtifactType.VALIDATION_RESULT: "validation_result.schema.json",
    ArtifactType.FAILURE_REPORT: "failure_report.schema.json",
}


class OutputValidator:
    """Validates LLM output against JSON schemas.

    Performs:
    - JSON parsing
    - Schema validation
    - Code detection
    """

    def __init__(
        self,
        schema_dir: Path | None = None,
        *,
        check_code: bool = True,
    ) -> None:
        """Initialize the output validator.

        Args:
            schema_dir: Directory containing JSON Schema files.
                       Defaults to 'schemas/' in the project root.
            check_code: Whether to check for code in output.
        """
        if schema_dir is None:
            # Default to schemas/ in project root
            schema_dir = Path(__file__).parent.parent.parent.parent / "schemas"
        self._schema_dir = schema_dir
        self._check_code = check_code
        self._code_detector = CodeDetector() if check_code else None
        self._schema_cache: dict[str, dict[str, Any]] = {}

    def validate(
        self,
        json_str: str,
        artifact_type: ArtifactType,
    ) -> dict[str, Any]:
        """Validate JSON string against schema for artifact type.

        Args:
            json_str: The JSON string to validate.
            artifact_type: The type of artifact to validate against.

        Returns:
            The parsed and validated data dictionary.

        Raises:
            InvalidJSONError: If JSON parsing fails.
            SchemaViolationError: If schema validation fails.
            CodeInOutputError: If code is detected in output.
        """
        # Parse JSON
        data = self._parse_json(json_str)

        # Validate against schema
        self._validate_schema(data, artifact_type)

        # Check for code
        if self._check_code:
            self._check_for_code(data)

        return data

    def validate_envelope(
        self,
        json_str: str,
    ) -> dict[str, Any]:
        """Validate JSON string as an artifact envelope.

        Validates against the envelope schema and extracts artifact type
        to validate the payload.

        Args:
            json_str: The JSON string to validate.

        Returns:
            The parsed and validated envelope dictionary.

        Raises:
            InvalidJSONError: If JSON parsing fails.
            SchemaViolationError: If schema validation fails.
            CodeInOutputError: If code is detected in output.
        """
        # Parse JSON
        data = self._parse_json(json_str)

        # Validate envelope structure
        self._validate_envelope_schema(data)

        # Get artifact type and validate payload
        artifact_type_str = data.get("artifact_type")
        if artifact_type_str:
            try:
                artifact_type = ArtifactType(artifact_type_str)
                payload = data.get("payload")
                if payload:
                    self._validate_schema(payload, artifact_type)
            except ValueError:
                # Invalid artifact type - will be caught by envelope validation
                pass

        # Check for code
        if self._check_code:
            self._check_for_code(data)

        return data

    def _parse_json(self, json_str: str) -> dict[str, Any]:
        """Parse JSON string to dictionary.

        Args:
            json_str: The JSON string.

        Returns:
            Parsed dictionary.

        Raises:
            InvalidJSONError: If parsing fails.
        """
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise InvalidJSONError(
                    "Expected JSON object, got " + type(data).__name__,
                    raw_snippet=json_str[:200],
                )
            return data
        except json.JSONDecodeError as e:
            raise InvalidJSONError(
                parse_error=str(e),
                raw_snippet=json_str[:200],
            ) from e

    def _validate_schema(
        self,
        data: dict[str, Any],
        artifact_type: ArtifactType,
    ) -> None:
        """Validate data against artifact schema.

        Args:
            data: The data to validate.
            artifact_type: The artifact type.

        Raises:
            SchemaViolationError: If validation fails.
        """
        schema_file = SCHEMA_FILE_MAP.get(artifact_type)
        if schema_file is None:
            raise SchemaViolationError(
                f"No schema defined for artifact type: {artifact_type.value}",
            )

        schema = self._load_schema(schema_file)
        self._run_validation(data, schema)

    def _validate_envelope_schema(self, data: dict[str, Any]) -> None:
        """Validate data against envelope schema.

        Args:
            data: The data to validate.

        Raises:
            SchemaViolationError: If validation fails.
        """
        schema = self._load_schema("artifact.schema.json")
        self._run_validation(data, schema)

    def _run_validation(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
    ) -> None:
        """Run jsonschema validation.

        Args:
            data: Data to validate.
            schema: Schema to validate against.

        Raises:
            SchemaViolationError: If validation fails.
        """
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            # Collect all validation errors
            validator = jsonschema.Draft7Validator(schema)
            errors = list(validator.iter_errors(data))

            error_messages = [
                f"{'.'.join(str(p) for p in err.absolute_path) or '$'}: {err.message}"
                for err in errors[:5]  # Limit to first 5 errors
            ]

            schema_path = ".".join(str(p) for p in e.absolute_path) or "$"

            raise SchemaViolationError(
                schema_path=schema_path,
                validation_errors=error_messages,
                raw_snippet=json.dumps(data)[:200],
            ) from e

    def _load_schema(self, schema_file: str) -> dict[str, Any]:
        """Load a JSON schema file.

        Args:
            schema_file: Name of the schema file.

        Returns:
            The parsed schema.

        Raises:
            SchemaViolationError: If schema file not found.
        """
        if schema_file in self._schema_cache:
            return self._schema_cache[schema_file]

        schema_path = self._schema_dir / schema_file
        try:
            with schema_path.open(encoding="utf-8") as f:
                schema: dict[str, Any] = json.load(f)
                self._schema_cache[schema_file] = schema
                return schema
        except FileNotFoundError as e:
            raise SchemaViolationError(
                f"Schema file not found: {schema_file}",
                details=str(schema_path),
            ) from e

    def _check_for_code(self, data: dict[str, Any]) -> None:
        """Check for code in the data.

        Args:
            data: Data to check.

        Raises:
            CodeInOutputError: If code is detected.
        """
        if self._code_detector is None:
            return

        found, location = self._code_detector.contains_code(data)
        if found:
            # Try to get the code snippet
            code_snippet = None
            if location:
                try:
                    value = self._get_value_at_path(data, location)
                    if isinstance(value, str):
                        code_snippet = value[:100]
                except (KeyError, IndexError, TypeError):
                    pass

            raise CodeInOutputError(
                location=location,
                code_snippet=code_snippet,
                raw_snippet=json.dumps(data)[:200],
            )

    def _get_value_at_path(
        self,
        data: Any,
        path: str,
    ) -> Any:
        """Get value at a path in the data structure.

        Args:
            data: The data structure.
            path: Dot-separated path (e.g., "foo.bar[0].baz").

        Returns:
            The value at the path.
        """
        if not path or path == "$":
            return data

        current = data
        # Split by dots, handling array indices
        parts = path.replace("[", ".[").split(".")
        parts = [p for p in parts if p]

        for part in parts:
            if part.startswith("[") and part.endswith("]"):
                # Array index
                index = int(part[1:-1])
                current = current[index]
            else:
                current = current[part]

        return current


def validate_llm_output(
    json_str: str,
    artifact_type: ArtifactType,
    schema_dir: Path | None = None,
) -> dict[str, Any]:
    """Convenience function to validate LLM output.

    Args:
        json_str: The JSON string to validate.
        artifact_type: The artifact type to validate against.
        schema_dir: Optional schema directory.

    Returns:
        The validated data dictionary.

    Raises:
        InvalidJSONError: If JSON parsing fails.
        SchemaViolationError: If schema validation fails.
        CodeInOutputError: If code is detected.
    """
    validator = OutputValidator(schema_dir)
    return validator.validate(json_str, artifact_type)
