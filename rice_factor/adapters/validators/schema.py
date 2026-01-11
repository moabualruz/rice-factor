"""Schema-based artifact validator.

This module implements artifact validation using both Pydantic models
(for Python type safety) and JSON Schema (for language-agnostic validation).
"""

import json
from pathlib import Path
from typing import Any, cast

import jsonschema
from pydantic import BaseModel, ValidationError

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads import (
    ArchitecturePlanPayload,
    ImplementationPlanPayload,
    ProjectPlanPayload,
    ReconciliationPlanPayload,
    RefactorPlanPayload,
    ScaffoldPlanPayload,
    TestPlanPayload,
    ValidationResultPayload,
)
from rice_factor.domain.failures.errors import ArtifactValidationError

# Module-level schema cache to avoid memory leaks from instance-method caching
_SCHEMA_CACHE: dict[tuple[str, str], dict[str, Any]] = {}

# Mapping from ArtifactType to payload model class
PAYLOAD_TYPE_MAP: dict[ArtifactType, type[BaseModel]] = {
    ArtifactType.PROJECT_PLAN: ProjectPlanPayload,
    ArtifactType.ARCHITECTURE_PLAN: ArchitecturePlanPayload,
    ArtifactType.SCAFFOLD_PLAN: ScaffoldPlanPayload,
    ArtifactType.TEST_PLAN: TestPlanPayload,
    ArtifactType.IMPLEMENTATION_PLAN: ImplementationPlanPayload,
    ArtifactType.REFACTOR_PLAN: RefactorPlanPayload,
    ArtifactType.VALIDATION_RESULT: ValidationResultPayload,
    ArtifactType.RECONCILIATION_PLAN: ReconciliationPlanPayload,
}

# Mapping from ArtifactType to schema filename
SCHEMA_FILE_MAP: dict[ArtifactType, str] = {
    ArtifactType.PROJECT_PLAN: "project_plan.schema.json",
    ArtifactType.ARCHITECTURE_PLAN: "architecture_plan.schema.json",
    ArtifactType.SCAFFOLD_PLAN: "scaffold_plan.schema.json",
    ArtifactType.TEST_PLAN: "test_plan.schema.json",
    ArtifactType.IMPLEMENTATION_PLAN: "implementation_plan.schema.json",
    ArtifactType.REFACTOR_PLAN: "refactor_plan.schema.json",
    ArtifactType.VALIDATION_RESULT: "validation_result.schema.json",
    ArtifactType.RECONCILIATION_PLAN: "reconciliation_plan.schema.json",
}


class ArtifactValidator:
    """Validator for artifact envelopes and payloads.

    Uses both Pydantic models and JSON Schema for validation.
    Schemas are cached for performance.
    """

    def __init__(self, schema_dir: Path | None = None) -> None:
        """Initialize the validator.

        Args:
            schema_dir: Directory containing JSON Schema files.
                       Defaults to 'schemas/' in the project root.
        """
        if schema_dir is None:
            # Default to schemas/ in project root
            schema_dir = Path(__file__).parent.parent.parent.parent / "schemas"
        self._schema_dir = schema_dir

    def _load_schema(self, schema_file: str) -> dict[str, Any]:
        """Load and cache a JSON Schema file.

        Args:
            schema_file: Name of the schema file.

        Returns:
            Parsed JSON Schema dictionary.

        Raises:
            FileNotFoundError: If schema file doesn't exist.
        """
        # Use module-level cache with (schema_dir, schema_file) as key
        cache_key = (str(self._schema_dir), schema_file)
        if cache_key in _SCHEMA_CACHE:
            return _SCHEMA_CACHE[cache_key]

        schema_path = self._schema_dir / schema_file
        with schema_path.open("r", encoding="utf-8") as f:
            schema = cast("dict[str, Any]", json.load(f))
            _SCHEMA_CACHE[cache_key] = schema
            return schema

    def validate(self, data: dict[str, Any]) -> ArtifactEnvelope[BaseModel]:
        """Validate artifact data and return an ArtifactEnvelope.

        Performs both JSON Schema and Pydantic validation.

        Args:
            data: Raw artifact data dictionary.

        Returns:
            Validated ArtifactEnvelope instance.

        Raises:
            ArtifactValidationError: If validation fails.
        """
        # First validate against JSON Schema
        self.validate_json_schema(data)

        # Get the artifact type
        artifact_type_str = data.get("artifact_type")
        if artifact_type_str is None:
            raise ArtifactValidationError(
                "Missing required field 'artifact_type'",
                field_path="artifact_type",
            )

        try:
            artifact_type = ArtifactType(artifact_type_str)
        except ValueError as e:
            raise ArtifactValidationError(
                f"Invalid artifact type: {artifact_type_str}",
                field_path="artifact_type",
                expected=list(ArtifactType),
                actual=artifact_type_str,
            ) from e

        # Validate payload against its schema
        payload_data = data.get("payload")
        if payload_data is None:
            raise ArtifactValidationError(
                "Missing required field 'payload'",
                field_path="payload",
            )

        self.validate_json_schema(payload_data, artifact_type)

        # Validate with Pydantic
        payload = self.validate_payload(payload_data, artifact_type)

        # Build the envelope
        try:
            envelope_data = {**data, "payload": payload}
            # Create ArtifactEnvelope with the validated payload
            envelope: ArtifactEnvelope[BaseModel] = ArtifactEnvelope(**envelope_data)
            return envelope
        except ValidationError as e:
            raise self._pydantic_to_validation_error(e) from e

    def validate_payload(
        self, data: dict[str, Any], artifact_type: ArtifactType
    ) -> BaseModel:
        """Validate payload data for a specific artifact type.

        Args:
            data: Raw payload data dictionary.
            artifact_type: The type of artifact this payload belongs to.

        Returns:
            Validated payload model instance.

        Raises:
            ArtifactValidationError: If validation fails.
        """
        payload_class = PAYLOAD_TYPE_MAP.get(artifact_type)
        if payload_class is None:
            raise ArtifactValidationError(
                f"Unknown artifact type: {artifact_type}",
                field_path="artifact_type",
            )

        try:
            return payload_class(**data)
        except ValidationError as e:
            raise self._pydantic_to_validation_error(e, prefix="payload") from e

    def validate_json_schema(
        self, data: dict[str, Any], artifact_type: ArtifactType | None = None
    ) -> None:
        """Validate data against JSON Schema only.

        Args:
            data: Data to validate.
            artifact_type: If provided, validates payload against payload schema.
                          If None, validates against envelope schema.

        Raises:
            ArtifactValidationError: If validation fails.
        """
        schema_file: str
        if artifact_type is None:
            schema_file = "artifact.schema.json"
        else:
            maybe_schema_file = SCHEMA_FILE_MAP.get(artifact_type)
            if maybe_schema_file is None:
                raise ArtifactValidationError(
                    f"No schema for artifact type: {artifact_type}",
                    field_path="artifact_type",
                )
            schema_file = maybe_schema_file

        try:
            schema = self._load_schema(schema_file)
        except FileNotFoundError as e:
            raise ArtifactValidationError(
                f"Schema file not found: {schema_file}",
                field_path="$schema",
            ) from e

        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            raise self._jsonschema_to_validation_error(e) from e

    def _pydantic_to_validation_error(
        self, error: ValidationError, prefix: str = ""
    ) -> ArtifactValidationError:
        """Convert Pydantic ValidationError to ArtifactValidationError.

        Args:
            error: Pydantic validation error.
            prefix: Optional prefix for field paths.

        Returns:
            ArtifactValidationError with field-level details.
        """
        errors = error.errors()
        if not errors:
            return ArtifactValidationError(str(error))

        # Use the first error for the main message
        first_error = errors[0]
        field_path = ".".join(str(loc) for loc in first_error.get("loc", []))
        if prefix:
            field_path = f"{prefix}.{field_path}" if field_path else prefix

        message = first_error.get("msg", str(error))

        # Build details from all errors
        details: list[dict[str, object]] = [
            {
                "path": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in errors
        ]

        return ArtifactValidationError(
            message,
            field_path=field_path,
            details=details,
        )

    def _jsonschema_to_validation_error(
        self, error: jsonschema.ValidationError
    ) -> ArtifactValidationError:
        """Convert jsonschema ValidationError to ArtifactValidationError.

        Args:
            error: JSON Schema validation error.

        Returns:
            ArtifactValidationError with field-level details.
        """
        field_path = ".".join(str(p) for p in error.absolute_path)
        # error.schema can be a dict, bool, or Unset - only dicts have .get()
        expected = None
        if isinstance(error.schema, dict):
            expected = error.schema.get("type")
        return ArtifactValidationError(
            error.message,
            field_path=field_path or "$",
            expected=expected,
            actual=error.instance if error.instance is not None else None,
        )
