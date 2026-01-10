"""Unit tests for ArtifactValidator."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from rice_factor.adapters.validators import ArtifactValidator
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.payloads import (
    ProjectPlanPayload,
    TestPlanPayload,
)
from rice_factor.domain.failures.errors import ArtifactValidationError


@pytest.fixture
def validator() -> ArtifactValidator:
    """Create a validator instance."""
    return ArtifactValidator()


@pytest.fixture
def valid_project_plan_data() -> dict:
    """Create valid project plan artifact data."""
    return {
        "artifact_type": "ProjectPlan",
        "artifact_version": "1.0",
        "id": str(uuid4()),
        "status": "draft",
        "created_at": datetime.now(UTC).isoformat(),
        "created_by": "llm",
        "depends_on": [],
        "payload": {
            "domains": [{"name": "core", "responsibility": "Business logic"}],
            "modules": [{"name": "auth", "domain": "core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        },
    }


@pytest.fixture
def valid_test_plan_data() -> dict:
    """Create valid test plan artifact data."""
    return {
        "artifact_type": "TestPlan",
        "artifact_version": "1.0",
        "id": str(uuid4()),
        "status": "draft",
        "created_at": datetime.now(UTC).isoformat(),
        "created_by": "llm",
        "depends_on": [],
        "payload": {
            "tests": [
                {
                    "id": "test-001",
                    "target": "auth.login",
                    "assertions": ["returns token", "handles errors"],
                }
            ]
        },
    }


class TestValidateFullArtifact:
    """Tests for full artifact validation."""

    def test_valid_project_plan(
        self, validator: ArtifactValidator, valid_project_plan_data: dict
    ) -> None:
        """Test validation of valid project plan artifact."""
        envelope = validator.validate(valid_project_plan_data)
        assert envelope.artifact_type == ArtifactType.PROJECT_PLAN
        assert envelope.status == ArtifactStatus.DRAFT
        assert isinstance(envelope.payload, ProjectPlanPayload)

    def test_valid_test_plan(
        self, validator: ArtifactValidator, valid_test_plan_data: dict
    ) -> None:
        """Test validation of valid test plan artifact."""
        envelope = validator.validate(valid_test_plan_data)
        assert envelope.artifact_type == ArtifactType.TEST_PLAN
        assert isinstance(envelope.payload, TestPlanPayload)

    def test_missing_artifact_type(self, validator: ArtifactValidator) -> None:
        """Test validation fails for missing artifact_type."""
        data = {
            "artifact_version": "1.0",
            "id": str(uuid4()),
            "status": "draft",
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": "llm",
            "payload": {},
        }
        with pytest.raises(ArtifactValidationError) as exc_info:
            validator.validate(data)
        assert "artifact_type" in str(exc_info.value)

    def test_invalid_artifact_type(
        self, validator: ArtifactValidator, valid_project_plan_data: dict
    ) -> None:
        """Test validation fails for invalid artifact_type."""
        valid_project_plan_data["artifact_type"] = "InvalidType"
        with pytest.raises(ArtifactValidationError) as exc_info:
            validator.validate(valid_project_plan_data)
        assert exc_info.value.field_path == "artifact_type"

    def test_missing_payload(self, validator: ArtifactValidator) -> None:
        """Test validation fails for missing payload."""
        data = {
            "artifact_type": "ProjectPlan",
            "artifact_version": "1.0",
            "id": str(uuid4()),
            "status": "draft",
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": "llm",
        }
        with pytest.raises(ArtifactValidationError) as exc_info:
            validator.validate(data)
        assert "payload" in str(exc_info.value)

    def test_invalid_status(
        self, validator: ArtifactValidator, valid_project_plan_data: dict
    ) -> None:
        """Test validation fails for invalid status."""
        valid_project_plan_data["status"] = "invalid"
        with pytest.raises(ArtifactValidationError):
            validator.validate(valid_project_plan_data)


class TestValidatePayload:
    """Tests for payload-only validation."""

    def test_valid_project_plan_payload(self, validator: ArtifactValidator) -> None:
        """Test validation of valid project plan payload."""
        payload_data = {
            "domains": [{"name": "core", "responsibility": "Business logic"}],
            "modules": [{"name": "auth", "domain": "core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }
        payload = validator.validate_payload(payload_data, ArtifactType.PROJECT_PLAN)
        assert isinstance(payload, ProjectPlanPayload)

    def test_invalid_payload_missing_domains(
        self, validator: ArtifactValidator
    ) -> None:
        """Test validation fails for missing required field."""
        payload_data = {
            "modules": [{"name": "auth", "domain": "core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }
        with pytest.raises(ArtifactValidationError):
            validator.validate_payload(payload_data, ArtifactType.PROJECT_PLAN)

    def test_invalid_payload_empty_domains(self, validator: ArtifactValidator) -> None:
        """Test validation fails for empty required list."""
        payload_data = {
            "domains": [],
            "modules": [{"name": "auth", "domain": "core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }
        with pytest.raises(ArtifactValidationError):
            validator.validate_payload(payload_data, ArtifactType.PROJECT_PLAN)


class TestValidateJsonSchema:
    """Tests for JSON Schema-only validation."""

    def test_valid_envelope_schema(
        self, validator: ArtifactValidator, valid_project_plan_data: dict
    ) -> None:
        """Test valid envelope passes JSON Schema validation."""
        validator.validate_json_schema(valid_project_plan_data)

    def test_invalid_envelope_extra_field(
        self, validator: ArtifactValidator, valid_project_plan_data: dict
    ) -> None:
        """Test extra field fails JSON Schema validation."""
        valid_project_plan_data["extra"] = "not allowed"
        with pytest.raises(ArtifactValidationError):
            validator.validate_json_schema(valid_project_plan_data)

    def test_valid_payload_schema(self, validator: ArtifactValidator) -> None:
        """Test valid payload passes JSON Schema validation."""
        payload_data = {
            "domains": [{"name": "core", "responsibility": "Business logic"}],
            "modules": [{"name": "auth", "domain": "core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }
        validator.validate_json_schema(payload_data, ArtifactType.PROJECT_PLAN)

    def test_invalid_payload_schema(self, validator: ArtifactValidator) -> None:
        """Test invalid payload fails JSON Schema validation."""
        payload_data = {
            "domains": [],  # minItems: 1
            "modules": [{"name": "auth", "domain": "core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }
        with pytest.raises(ArtifactValidationError):
            validator.validate_json_schema(payload_data, ArtifactType.PROJECT_PLAN)


class TestErrorMessages:
    """Tests for error message quality."""

    def test_error_includes_field_path(self, validator: ArtifactValidator) -> None:
        """Test validation error includes field path."""
        payload_data = {
            "domains": [{"name": "core"}],  # missing responsibility
            "modules": [{"name": "auth", "domain": "core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }
        with pytest.raises(ArtifactValidationError) as exc_info:
            validator.validate_payload(payload_data, ArtifactType.PROJECT_PLAN)
        assert exc_info.value.field_path is not None

    def test_error_str_formatting(self, validator: ArtifactValidator) -> None:
        """Test error string formatting."""
        payload_data = {
            "domains": [],  # minItems: 1
            "modules": [{"name": "auth", "domain": "core"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }
        with pytest.raises(ArtifactValidationError) as exc_info:
            validator.validate_payload(payload_data, ArtifactType.PROJECT_PLAN)
        error_str = str(exc_info.value)
        assert "Field:" in error_str


class TestAllArtifactTypes:
    """Test validation for all artifact types."""

    def test_architecture_plan(self, validator: ArtifactValidator) -> None:
        """Test ArchitecturePlan validation."""
        payload = validator.validate_payload(
            {"layers": ["domain", "app"], "rules": []},
            ArtifactType.ARCHITECTURE_PLAN,
        )
        assert payload is not None

    def test_scaffold_plan(self, validator: ArtifactValidator) -> None:
        """Test ScaffoldPlan validation."""
        payload = validator.validate_payload(
            {
                "files": [
                    {"path": "src/main.py", "description": "Entry point", "kind": "source"}
                ]
            },
            ArtifactType.SCAFFOLD_PLAN,
        )
        assert payload is not None

    def test_implementation_plan(self, validator: ArtifactValidator) -> None:
        """Test ImplementationPlan validation."""
        payload = validator.validate_payload(
            {"target": "src/main.py", "steps": ["Implement main"], "related_tests": []},
            ArtifactType.IMPLEMENTATION_PLAN,
        )
        assert payload is not None

    def test_refactor_plan(self, validator: ArtifactValidator) -> None:
        """Test RefactorPlan validation."""
        payload = validator.validate_payload(
            {"goal": "Reorganize", "operations": [{"type": "move_file"}]},
            ArtifactType.REFACTOR_PLAN,
        )
        assert payload is not None

    def test_validation_result(self, validator: ArtifactValidator) -> None:
        """Test ValidationResult validation."""
        payload = validator.validate_payload(
            {"target": "src/main.py", "status": "passed"},
            ArtifactType.VALIDATION_RESULT,
        )
        assert payload is not None
