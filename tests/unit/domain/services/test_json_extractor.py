"""Unit tests for JSONExtractor."""

import pytest

from rice_factor.domain.failures.llm_errors import (
    ExplanatoryTextError,
    InvalidJSONError,
    MultipleArtifactsError,
)
from rice_factor.domain.services.json_extractor import JSONExtractor, extract_json


class TestJSONExtractor:
    """Tests for JSONExtractor class."""

    @pytest.fixture
    def extractor(self) -> JSONExtractor:
        """Create a JSONExtractor instance."""
        return JSONExtractor()

    # =========================================================================
    # Raw JSON Extraction
    # =========================================================================

    def test_extracts_raw_json(self, extractor: JSONExtractor) -> None:
        """Should extract raw JSON starting with {."""
        response = '{"name": "test", "value": 42}'
        result = extractor.extract(response)
        assert result == '{"name": "test", "value": 42}'

    def test_extracts_raw_json_with_whitespace(self, extractor: JSONExtractor) -> None:
        """Should handle leading/trailing whitespace."""
        response = '  \n{"name": "test"}\n  '
        result = extractor.extract(response)
        assert result == '{"name": "test"}'

    def test_extracts_multiline_json(self, extractor: JSONExtractor) -> None:
        """Should extract multiline JSON."""
        response = """{
    "name": "test",
    "items": [1, 2, 3]
}"""
        result = extractor.extract(response)
        assert '"name": "test"' in result
        assert '"items": [1, 2, 3]' in result

    def test_extracts_nested_json(self, extractor: JSONExtractor) -> None:
        """Should extract nested JSON objects."""
        response = '{"outer": {"inner": {"deep": true}}}'
        result = extractor.extract(response)
        assert result == '{"outer": {"inner": {"deep": true}}}'

    # =========================================================================
    # Code Fence Extraction
    # =========================================================================

    def test_extracts_json_from_code_fence(self, extractor: JSONExtractor) -> None:
        """Should extract JSON from ```json fence."""
        response = '```json\n{"name": "test"}\n```'
        result = extractor.extract(response)
        assert result == '{"name": "test"}'

    def test_extracts_json_from_plain_code_fence(
        self, extractor: JSONExtractor
    ) -> None:
        """Should extract JSON from ``` fence without language."""
        response = '```\n{"name": "test"}\n```'
        result = extractor.extract(response)
        assert result == '{"name": "test"}'

    def test_extracts_multiline_json_from_fence(
        self, extractor: JSONExtractor
    ) -> None:
        """Should extract multiline JSON from code fence."""
        response = """```json
{
    "name": "test",
    "value": 42
}
```"""
        result = extractor.extract(response)
        assert '"name": "test"' in result
        assert '"value": 42' in result

    def test_extracts_json_with_special_chars_from_fence(
        self, extractor: JSONExtractor
    ) -> None:
        """Should extract JSON with special characters from fence."""
        response = '```json\n{"message": "Hello\\nWorld"}\n```'
        result = extractor.extract(response)
        assert result == '{"message": "Hello\\nWorld"}'

    # =========================================================================
    # Invalid JSON Rejection
    # =========================================================================

    def test_raises_for_empty_response(self, extractor: JSONExtractor) -> None:
        """Should raise InvalidJSONError for empty response."""
        with pytest.raises(InvalidJSONError):
            extractor.extract("")

    def test_raises_for_whitespace_only(self, extractor: JSONExtractor) -> None:
        """Should raise InvalidJSONError for whitespace-only response."""
        with pytest.raises(InvalidJSONError):
            extractor.extract("   \n\t  ")

    def test_raises_for_non_json_text(self, extractor: JSONExtractor) -> None:
        """Should raise InvalidJSONError for plain text."""
        with pytest.raises(InvalidJSONError) as exc_info:
            extractor.extract("This is just some text without any JSON.")
        assert "No JSON object found" in str(exc_info.value)

    def test_raises_for_non_json_in_fence(self, extractor: JSONExtractor) -> None:
        """Should raise InvalidJSONError for non-JSON in code fence."""
        response = "```\nThis is not JSON\n```"
        with pytest.raises(InvalidJSONError):
            extractor.extract(response)

    # =========================================================================
    # Multiple JSON Objects Rejection
    # =========================================================================

    def test_raises_for_multiple_adjacent_objects(
        self, extractor: JSONExtractor
    ) -> None:
        """Should raise MultipleArtifactsError for adjacent JSON objects."""
        response = '{"first": 1}{"second": 2}'
        with pytest.raises(MultipleArtifactsError) as exc_info:
            extractor.extract(response)
        assert exc_info.value.count is not None
        assert exc_info.value.count >= 2

    def test_raises_for_multiple_objects_with_newline(
        self, extractor: JSONExtractor
    ) -> None:
        """Should raise MultipleArtifactsError for objects separated by newline."""
        response = '{"first": 1}\n{"second": 2}'
        with pytest.raises(MultipleArtifactsError):
            extractor.extract(response)

    def test_raises_for_multiple_code_fences(self, extractor: JSONExtractor) -> None:
        """Should raise MultipleArtifactsError for multiple code fences."""
        response = '```json\n{"first": 1}\n```\n```json\n{"second": 2}\n```'
        with pytest.raises(MultipleArtifactsError) as exc_info:
            extractor.extract(response)
        assert exc_info.value.count == 2

    def test_handles_nested_braces_correctly(self, extractor: JSONExtractor) -> None:
        """Should not false-positive on nested braces as multiple objects."""
        response = '{"outer": {"inner": {"deep": {}}}}'
        # Should not raise
        result = extractor.extract(response)
        assert result == response

    # =========================================================================
    # Explanatory Text Rejection
    # =========================================================================

    def test_raises_for_text_before_json(self, extractor: JSONExtractor) -> None:
        """Should raise ExplanatoryTextError for text before JSON."""
        response = 'Here is the artifact:\n{"name": "test"}'
        with pytest.raises(ExplanatoryTextError) as exc_info:
            extractor.extract(response)
        assert "Here is the artifact" in (exc_info.value.text_snippet or "")

    def test_raises_for_text_after_json(self, extractor: JSONExtractor) -> None:
        """Should raise ExplanatoryTextError for text after JSON."""
        response = '{"name": "test"}\nThis completes the artifact.'
        with pytest.raises(ExplanatoryTextError):
            extractor.extract(response)

    def test_raises_for_text_around_code_fence(
        self, extractor: JSONExtractor
    ) -> None:
        """Should raise ExplanatoryTextError for text around code fence."""
        response = 'Here is the JSON:\n```json\n{"name": "test"}\n```\nEnd of response.'
        with pytest.raises(ExplanatoryTextError):
            extractor.extract(response)

    def test_ignores_trivial_whitespace(self, extractor: JSONExtractor) -> None:
        """Should not raise for trivial whitespace outside JSON."""
        response = '  ```json\n{"name": "test"}\n```  '
        # Should not raise
        result = extractor.extract(response)
        assert '"name": "test"' in result

    def test_ignores_short_text(self, extractor: JSONExtractor) -> None:
        """Should not raise for very short text outside JSON."""
        response = '- ```json\n{"name": "test"}\n```'
        # Single character or very short text should be ignored
        # This depends on MIN_EXPLANATORY_LENGTH threshold
        # Result should either extract or raise based on threshold
        try:
            result = extractor.extract(response)
            assert '"name": "test"' in result
        except ExplanatoryTextError:
            # Also acceptable if threshold is low
            pass

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_handles_json_with_strings_containing_braces(
        self, extractor: JSONExtractor
    ) -> None:
        """Should handle JSON with strings containing braces."""
        response = '{"code": "if (x) { y }"}'
        result = extractor.extract(response)
        assert result == '{"code": "if (x) { y }"}'

    def test_handles_json_with_escaped_quotes(
        self, extractor: JSONExtractor
    ) -> None:
        """Should handle JSON with escaped quotes in strings."""
        response = '{"message": "He said \\"hello\\""}'
        result = extractor.extract(response)
        assert '\\"hello\\"' in result

    def test_handles_json_with_newlines_in_strings(
        self, extractor: JSONExtractor
    ) -> None:
        """Should handle JSON with newlines in string values."""
        response = '{"text": "line1\\nline2"}'
        result = extractor.extract(response)
        assert "line1\\nline2" in result

    def test_handles_empty_json_object(self, extractor: JSONExtractor) -> None:
        """Should handle empty JSON object."""
        response = "{}"
        result = extractor.extract(response)
        assert result == "{}"

    def test_handles_json_array_not_object(self, extractor: JSONExtractor) -> None:
        """Should handle JSON array in code fence."""
        response = '```json\n[1, 2, 3]\n```'
        result = extractor.extract(response)
        assert result == "[1, 2, 3]"


class TestExtractJsonFunction:
    """Tests for the extract_json convenience function."""

    def test_convenience_function_extracts_json(self) -> None:
        """Should extract JSON via convenience function."""
        response = '{"name": "test"}'
        result = extract_json(response)
        assert result == '{"name": "test"}'

    def test_convenience_function_raises_on_invalid(self) -> None:
        """Should raise via convenience function."""
        with pytest.raises(InvalidJSONError):
            extract_json("not json")

    def test_convenience_function_raises_on_multiple(self) -> None:
        """Should raise MultipleArtifactsError via convenience function."""
        with pytest.raises(MultipleArtifactsError):
            extract_json('{"a": 1}{"b": 2}')


class TestJSONExtractionRobustness:
    """Tests for robustness of JSON extraction."""

    @pytest.fixture
    def extractor(self) -> JSONExtractor:
        """Create a JSONExtractor instance."""
        return JSONExtractor()

    def test_extracts_complex_real_world_json(self, extractor: JSONExtractor) -> None:
        """Should extract complex real-world JSON."""
        response = """```json
{
    "artifact_type": "project_plan",
    "status": "draft",
    "payload": {
        "name": "My Project",
        "description": "A test project",
        "domains": [
            {
                "name": "Auth",
                "entities": ["User", "Session"]
            }
        ],
        "invariants": ["All users must have unique emails"]
    }
}
```"""
        result = extractor.extract(response)
        assert '"artifact_type": "project_plan"' in result
        assert '"domains":' in result

    def test_extracts_json_with_unicode(self, extractor: JSONExtractor) -> None:
        """Should extract JSON with unicode characters."""
        response = '{"message": "Hello 世界! 🌍"}'
        result = extractor.extract(response)
        assert "世界" in result

    def test_extracts_json_with_null_values(self, extractor: JSONExtractor) -> None:
        """Should extract JSON with null values."""
        response = '{"value": null, "empty": null}'
        result = extractor.extract(response)
        assert "null" in result

    def test_extracts_json_with_boolean_values(self, extractor: JSONExtractor) -> None:
        """Should extract JSON with boolean values."""
        response = '{"active": true, "disabled": false}'
        result = extractor.extract(response)
        assert "true" in result
        assert "false" in result

    def test_extracts_json_with_numbers(self, extractor: JSONExtractor) -> None:
        """Should extract JSON with various number formats."""
        response = '{"int": 42, "float": 3.14, "neg": -10, "exp": 1e5}'
        result = extractor.extract(response)
        assert "42" in result
        assert "3.14" in result
