"""Unit tests for OutputValidator."""

import json
from pathlib import Path

import pytest

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.failures.llm_errors import (
    CodeInOutputError,
    InvalidJSONError,
    SchemaViolationError,
)
from rice_factor.domain.services.output_validator import (
    OutputValidator,
    validate_llm_output,
)


class TestOutputValidator:
    """Tests for OutputValidator class."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    @pytest.fixture
    def validator(self, schemas_dir: Path) -> OutputValidator:
        """Create an OutputValidator with actual schemas."""
        return OutputValidator(schemas_dir)

    @pytest.fixture
    def validator_no_code_check(self, schemas_dir: Path) -> OutputValidator:
        """Create an OutputValidator without code checking."""
        return OutputValidator(schemas_dir, check_code=False)

    # =========================================================================
    # Valid JSON Parsing
    # =========================================================================

    def test_parses_valid_json(self, validator: OutputValidator) -> None:
        """Should parse valid JSON."""
        json_str = '{"name": "test", "description": "A test project"}'
        # This will fail schema validation but should parse JSON successfully
        with pytest.raises(SchemaViolationError):
            validator.validate(json_str, ArtifactType.PROJECT_PLAN)

    def test_rejects_invalid_json_syntax(self, validator: OutputValidator) -> None:
        """Should reject invalid JSON syntax."""
        json_str = '{"name": "test"'  # Missing closing brace
        with pytest.raises(InvalidJSONError) as exc_info:
            validator.validate(json_str, ArtifactType.PROJECT_PLAN)
        assert exc_info.value.parse_error is not None

    def test_rejects_non_object_json(self, validator: OutputValidator) -> None:
        """Should reject JSON that isn't an object."""
        json_str = '[1, 2, 3]'  # Array, not object
        with pytest.raises(InvalidJSONError) as exc_info:
            validator.validate(json_str, ArtifactType.PROJECT_PLAN)
        assert "Expected JSON object" in str(exc_info.value)

    def test_rejects_string_json(self, validator: OutputValidator) -> None:
        """Should reject JSON that is just a string."""
        json_str = '"just a string"'
        with pytest.raises(InvalidJSONError):
            validator.validate(json_str, ArtifactType.PROJECT_PLAN)

    # =========================================================================
    # Schema Validation - Matching actual schema definitions
    # =========================================================================

    def test_validates_valid_project_plan(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should validate a valid project plan payload."""
        # Schema: domains, modules, constraints required
        payload = {
            "domains": [
                {"name": "Core", "responsibility": "Core domain functionality"}
            ],
            "modules": [
                {"name": "auth", "domain": "Core"}
            ],
            "constraints": {
                "architecture": "hexagonal",
                "languages": ["python"]
            }
        }
        json_str = json.dumps(payload)
        result = validator_no_code_check.validate(
            json_str, ArtifactType.PROJECT_PLAN
        )
        assert result["domains"][0]["name"] == "Core"

    def test_rejects_missing_required_field(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should reject payload missing required fields."""
        payload = {
            "domains": [{"name": "Core", "responsibility": "Test"}],
            # Missing 'modules' and 'constraints'
        }
        json_str = json.dumps(payload)
        with pytest.raises(SchemaViolationError) as exc_info:
            validator_no_code_check.validate(json_str, ArtifactType.PROJECT_PLAN)
        assert len(exc_info.value.validation_errors) > 0

    def test_rejects_wrong_type_field(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should reject payload with wrong field types."""
        payload = {
            "domains": "not an array",  # Should be array
            "modules": [],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }
        json_str = json.dumps(payload)
        with pytest.raises(SchemaViolationError):
            validator_no_code_check.validate(json_str, ArtifactType.PROJECT_PLAN)

    def test_validates_architecture_plan(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should validate architecture plan payload."""
        # Schema: layers, rules required
        payload = {
            "layers": ["domain", "application", "infrastructure"],
            "rules": [
                {"rule": "domain_cannot_import_infrastructure"}
            ]
        }
        json_str = json.dumps(payload)
        result = validator_no_code_check.validate(
            json_str, ArtifactType.ARCHITECTURE_PLAN
        )
        assert len(result["layers"]) == 3

    def test_validates_scaffold_plan(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should validate scaffold plan payload."""
        # Schema: files required
        payload = {
            "files": [
                {
                    "path": "src/main.py",
                    "description": "Main entry point",
                    "kind": "source"
                }
            ]
        }
        json_str = json.dumps(payload)
        result = validator_no_code_check.validate(
            json_str, ArtifactType.SCAFFOLD_PLAN
        )
        assert result["files"][0]["path"] == "src/main.py"

    def test_validates_test_plan(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should validate test plan payload."""
        # Schema: tests required with id, target, assertions
        payload = {
            "tests": [
                {
                    "id": "test_auth_login",
                    "target": "auth.login",
                    "assertions": ["Should authenticate valid user"]
                }
            ]
        }
        json_str = json.dumps(payload)
        result = validator_no_code_check.validate(json_str, ArtifactType.TEST_PLAN)
        assert result["tests"][0]["id"] == "test_auth_login"

    def test_validates_implementation_plan(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should validate implementation plan payload."""
        # Schema: target, steps, related_tests required
        payload = {
            "target": "src/auth.py",
            "steps": ["Add login function", "Add logout function"],
            "related_tests": ["test_auth_login"]
        }
        json_str = json.dumps(payload)
        result = validator_no_code_check.validate(
            json_str, ArtifactType.IMPLEMENTATION_PLAN
        )
        assert result["target"] == "src/auth.py"

    def test_validates_refactor_plan(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should validate refactor plan payload."""
        # Schema: goal, operations required
        payload = {
            "goal": "Extract common utilities",
            "operations": [
                {"type": "move_file", "from": "src/old.py", "to": "src/new.py"}
            ]
        }
        json_str = json.dumps(payload)
        result = validator_no_code_check.validate(
            json_str, ArtifactType.REFACTOR_PLAN
        )
        assert result["goal"] == "Extract common utilities"

    def test_validates_validation_result(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should validate validation result payload."""
        # Schema: target, status required
        payload = {
            "target": "src/auth.py",
            "status": "passed",
            "errors": []
        }
        json_str = json.dumps(payload)
        result = validator_no_code_check.validate(
            json_str, ArtifactType.VALIDATION_RESULT
        )
        assert result["status"] == "passed"

    # =========================================================================
    # Code Detection
    # =========================================================================

    def test_rejects_code_in_output(
        self, validator: OutputValidator
    ) -> None:
        """Should reject output containing code."""
        # Use a valid structure but with code in a description
        payload = {
            "domains": [
                {
                    "name": "Core",
                    "responsibility": "def authenticate(user):\n    return check_password(user)"
                }
            ],
            "modules": [{"name": "auth", "domain": "Core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]}
        }
        json_str = json.dumps(payload)
        with pytest.raises(CodeInOutputError) as exc_info:
            validator.validate(json_str, ArtifactType.PROJECT_PLAN)
        assert exc_info.value.location is not None

    def test_rejects_code_in_nested_field(self, validator: OutputValidator) -> None:
        """Should reject code in nested fields."""
        payload = {
            "tests": [
                {
                    "id": "test1",
                    "target": "auth",
                    "assertions": ["import os\nclass Auth:\n    pass"]
                }
            ]
        }
        json_str = json.dumps(payload)
        with pytest.raises(CodeInOutputError):
            validator.validate(json_str, ArtifactType.TEST_PLAN)

    def test_allows_code_when_check_disabled(
        self, validator_no_code_check: OutputValidator
    ) -> None:
        """Should allow code when code check is disabled."""
        payload = {
            "tests": [
                {
                    "id": "test1",
                    "target": "auth",
                    "assertions": ["def test():\n    pass"]
                }
            ]
        }
        json_str = json.dumps(payload)
        # Should not raise CodeInOutputError
        result = validator_no_code_check.validate(json_str, ArtifactType.TEST_PLAN)
        assert result["tests"][0]["id"] == "test1"

    # =========================================================================
    # Unknown Artifact Type / Missing Schema
    # =========================================================================

    def test_rejects_missing_schema_file(self, validator: OutputValidator) -> None:
        """Should reject when schema file doesn't exist."""
        json_str = '{"test": "data"}'

        # Point to nonexistent directory
        validator._schema_dir = Path("/nonexistent/path")
        with pytest.raises(SchemaViolationError) as exc_info:
            validator.validate(json_str, ArtifactType.PROJECT_PLAN)
        assert "Schema file not found" in str(exc_info.value)


class TestOutputValidatorEnvelope:
    """Tests for envelope validation."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    @pytest.fixture
    def validator(self, schemas_dir: Path) -> OutputValidator:
        """Create an OutputValidator."""
        return OutputValidator(schemas_dir, check_code=False)

    def test_validates_full_envelope(self, validator: OutputValidator) -> None:
        """Should validate a full artifact envelope."""
        # Schema: artifact_type, artifact_version, id, status, created_at, created_by, payload
        envelope = {
            "artifact_type": "ProjectPlan",
            "artifact_version": "1.0",
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "draft",
            "created_at": "2024-01-01T00:00:00Z",
            "created_by": "llm",
            "payload": {
                "domains": [{"name": "Core", "responsibility": "Core"}],
                "modules": [{"name": "auth", "domain": "Core"}],
                "constraints": {"architecture": "hexagonal", "languages": ["python"]}
            },
        }
        json_str = json.dumps(envelope)
        result = validator.validate_envelope(json_str)
        assert result["artifact_type"] == "ProjectPlan"


class TestValidateLLMOutputFunction:
    """Tests for the validate_llm_output convenience function."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    def test_convenience_function_validates(self, schemas_dir: Path) -> None:
        """Should validate via convenience function."""
        payload = {
            "domains": [{"name": "Core", "responsibility": "Core"}],
            "modules": [{"name": "auth", "domain": "Core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]}
        }
        json_str = json.dumps(payload)
        result = validate_llm_output(
            json_str, ArtifactType.PROJECT_PLAN, schemas_dir
        )
        assert result["domains"][0]["name"] == "Core"

    def test_convenience_function_raises_on_invalid(
        self, schemas_dir: Path
    ) -> None:
        """Should raise via convenience function."""
        json_str = "not valid json"
        with pytest.raises(InvalidJSONError):
            validate_llm_output(
                json_str, ArtifactType.PROJECT_PLAN, schemas_dir
            )


class TestSchemaValidationErrors:
    """Tests for schema validation error details."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    @pytest.fixture
    def validator(self, schemas_dir: Path) -> OutputValidator:
        """Create an OutputValidator."""
        return OutputValidator(schemas_dir, check_code=False)

    def test_includes_schema_path_in_error(
        self, validator: OutputValidator
    ) -> None:
        """Should include schema path in error."""
        payload = {"domains": "not an array"}  # Wrong type
        json_str = json.dumps(payload)
        with pytest.raises(SchemaViolationError) as exc_info:
            validator.validate(json_str, ArtifactType.PROJECT_PLAN)
        assert exc_info.value.schema_path is not None

    def test_includes_validation_errors_list(
        self, validator: OutputValidator
    ) -> None:
        """Should include list of validation errors."""
        payload = {}  # Missing all required fields
        json_str = json.dumps(payload)
        with pytest.raises(SchemaViolationError) as exc_info:
            validator.validate(json_str, ArtifactType.PROJECT_PLAN)
        assert len(exc_info.value.validation_errors) > 0

    def test_limits_validation_errors(self, validator: OutputValidator) -> None:
        """Should limit validation errors to prevent huge messages."""
        # An empty payload will have many errors
        payload = {}
        json_str = json.dumps(payload)
        with pytest.raises(SchemaViolationError) as exc_info:
            validator.validate(json_str, ArtifactType.PROJECT_PLAN)
        # Should have at most 5 errors in the list
        assert len(exc_info.value.validation_errors) <= 5
