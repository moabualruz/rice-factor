"""Unit tests for SchemaInjector."""

import json
from pathlib import Path

import pytest

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.prompts.schema_injector import (
    SchemaInjector,
    SchemaNotFoundError,
)


class TestSchemaInjector:
    """Tests for SchemaInjector class."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    @pytest.fixture
    def injector(self, schemas_dir: Path) -> SchemaInjector:
        """Create a SchemaInjector with actual schemas directory."""
        return SchemaInjector(schemas_dir)

    def test_load_project_plan_schema(self, injector: SchemaInjector) -> None:
        """Should load project plan schema."""
        schema = injector.load_schema(ArtifactType.PROJECT_PLAN)
        assert isinstance(schema, dict)
        assert "$schema" in schema or "type" in schema

    def test_load_architecture_plan_schema(self, injector: SchemaInjector) -> None:
        """Should load architecture plan schema."""
        schema = injector.load_schema(ArtifactType.ARCHITECTURE_PLAN)
        assert isinstance(schema, dict)

    def test_load_scaffold_plan_schema(self, injector: SchemaInjector) -> None:
        """Should load scaffold plan schema."""
        schema = injector.load_schema(ArtifactType.SCAFFOLD_PLAN)
        assert isinstance(schema, dict)

    def test_load_test_plan_schema(self, injector: SchemaInjector) -> None:
        """Should load test plan schema."""
        schema = injector.load_schema(ArtifactType.TEST_PLAN)
        assert isinstance(schema, dict)

    def test_load_implementation_plan_schema(self, injector: SchemaInjector) -> None:
        """Should load implementation plan schema."""
        schema = injector.load_schema(ArtifactType.IMPLEMENTATION_PLAN)
        assert isinstance(schema, dict)

    def test_load_refactor_plan_schema(self, injector: SchemaInjector) -> None:
        """Should load refactor plan schema."""
        schema = injector.load_schema(ArtifactType.REFACTOR_PLAN)
        assert isinstance(schema, dict)


class TestSchemaNotFound:
    """Tests for schema not found scenarios."""

    @pytest.fixture
    def empty_dir(self, tmp_path: Path) -> Path:
        """Create an empty directory for testing."""
        return tmp_path

    def test_raises_for_missing_schema(self, empty_dir: Path) -> None:
        """Should raise SchemaNotFoundError for missing schema."""
        injector = SchemaInjector(empty_dir)

        with pytest.raises(SchemaNotFoundError) as exc_info:
            injector.load_schema(ArtifactType.PROJECT_PLAN)

        assert exc_info.value.artifact_type == ArtifactType.PROJECT_PLAN

    def test_error_includes_path(self, empty_dir: Path) -> None:
        """Error should include the expected path."""
        injector = SchemaInjector(empty_dir)

        with pytest.raises(SchemaNotFoundError) as exc_info:
            injector.load_schema(ArtifactType.PROJECT_PLAN)

        assert "project_plan.schema.json" in str(exc_info.value)


class TestInjectSchema:
    """Tests for inject_schema method."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    @pytest.fixture
    def injector(self, schemas_dir: Path) -> SchemaInjector:
        """Create a SchemaInjector."""
        return SchemaInjector(schemas_dir)

    def test_replaces_placeholder(self, injector: SchemaInjector) -> None:
        """Should replace placeholder with schema."""
        prompt = "Instructions here\n\n{{SCHEMA}}\n\nMore instructions"

        result = injector.inject_schema(prompt, ArtifactType.PROJECT_PLAN)

        assert "{{SCHEMA}}" not in result
        assert "JSON SCHEMA" in result

    def test_appends_if_no_placeholder(self, injector: SchemaInjector) -> None:
        """Should append schema if no placeholder found."""
        prompt = "Instructions without placeholder"

        result = injector.inject_schema(prompt, ArtifactType.PROJECT_PLAN)

        assert "Instructions without placeholder" in result
        assert "JSON SCHEMA" in result
        # Schema should come after original prompt
        assert result.index("Instructions") < result.index("JSON SCHEMA")

    def test_custom_placeholder(self, injector: SchemaInjector) -> None:
        """Should support custom placeholder."""
        prompt = "Here: [INSERT_SCHEMA]"

        result = injector.inject_schema(
            prompt, ArtifactType.PROJECT_PLAN, placeholder="[INSERT_SCHEMA]"
        )

        assert "[INSERT_SCHEMA]" not in result
        assert "JSON SCHEMA" in result


class TestFormatSchemaForPrompt:
    """Tests for format_schema_for_prompt method."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    @pytest.fixture
    def injector(self, schemas_dir: Path) -> SchemaInjector:
        """Create a SchemaInjector."""
        return SchemaInjector(schemas_dir)

    def test_returns_json_string(self, injector: SchemaInjector) -> None:
        """Should return a valid JSON string."""
        result = injector.format_schema_for_prompt(ArtifactType.PROJECT_PLAN)

        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_is_indented(self, injector: SchemaInjector) -> None:
        """Should be indented for readability."""
        result = injector.format_schema_for_prompt(ArtifactType.PROJECT_PLAN)

        # Indented JSON has newlines
        assert "\n" in result
        assert "  " in result  # Has indentation


class TestSchemaCaching:
    """Tests for schema caching behavior."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    @pytest.fixture
    def injector(self, schemas_dir: Path) -> SchemaInjector:
        """Create a SchemaInjector."""
        return SchemaInjector(schemas_dir)

    def test_multiple_loads_return_same_content(
        self, injector: SchemaInjector
    ) -> None:
        """Multiple loads should return equivalent content."""
        schema1 = injector.load_schema(ArtifactType.PROJECT_PLAN)
        schema2 = injector.load_schema(ArtifactType.PROJECT_PLAN)

        assert schema1 == schema2

    def test_clear_cache_works(self, injector: SchemaInjector) -> None:
        """clear_cache should not raise."""
        # Load something first
        injector.load_schema(ArtifactType.PROJECT_PLAN)

        # Clear cache
        injector.clear_cache()

        # Should still work after clearing
        schema = injector.load_schema(ArtifactType.PROJECT_PLAN)
        assert isinstance(schema, dict)


class TestSchemaFilenames:
    """Tests for SCHEMA_FILENAMES mapping."""

    def test_all_artifact_types_mapped(self) -> None:
        """All artifact types should have a filename mapping."""
        for artifact_type in ArtifactType:
            assert (
                artifact_type in SchemaInjector.SCHEMA_FILENAMES
            ), f"Missing filename for {artifact_type}"

    def test_filenames_have_correct_extension(self) -> None:
        """All filenames should end with .schema.json."""
        for filename in SchemaInjector.SCHEMA_FILENAMES.values():
            assert filename.endswith(
                ".schema.json"
            ), f"Filename {filename} has wrong extension"
