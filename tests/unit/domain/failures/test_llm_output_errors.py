"""Unit tests for LLM output error types."""

import pytest

from rice_factor.domain.failures.llm_errors import (
    CodeInOutputError,
    ExplanatoryTextError,
    InvalidJSONError,
    LLMError,
    LLMOutputError,
    MultipleArtifactsError,
    SchemaViolationError,
)


class TestLLMOutputErrorHierarchy:
    """Tests for LLM output error class hierarchy."""

    def test_llm_output_error_is_llm_error(self) -> None:
        """LLMOutputError should inherit from LLMError."""
        error = LLMOutputError("test")
        assert isinstance(error, LLMError)

    def test_invalid_json_error_is_output_error(self) -> None:
        """InvalidJSONError should inherit from LLMOutputError."""
        error = InvalidJSONError()
        assert isinstance(error, LLMOutputError)
        assert isinstance(error, LLMError)

    def test_schema_violation_error_is_output_error(self) -> None:
        """SchemaViolationError should inherit from LLMOutputError."""
        error = SchemaViolationError()
        assert isinstance(error, LLMOutputError)
        assert isinstance(error, LLMError)

    def test_code_in_output_error_is_output_error(self) -> None:
        """CodeInOutputError should inherit from LLMOutputError."""
        error = CodeInOutputError()
        assert isinstance(error, LLMOutputError)
        assert isinstance(error, LLMError)

    def test_multiple_artifacts_error_is_output_error(self) -> None:
        """MultipleArtifactsError should inherit from LLMOutputError."""
        error = MultipleArtifactsError()
        assert isinstance(error, LLMOutputError)
        assert isinstance(error, LLMError)

    def test_explanatory_text_error_is_output_error(self) -> None:
        """ExplanatoryTextError should inherit from LLMOutputError."""
        error = ExplanatoryTextError()
        assert isinstance(error, LLMOutputError)
        assert isinstance(error, LLMError)


class TestLLMOutputError:
    """Tests for LLMOutputError base class."""

    def test_default_message(self) -> None:
        """Should have a message."""
        error = LLMOutputError("Test error")
        assert str(error) == "Test error"

    def test_with_raw_snippet(self) -> None:
        """Should include raw snippet in message."""
        error = LLMOutputError("Test error", raw_snippet='{"broken": json}')
        assert '{"broken": json}' in str(error)

    def test_raw_snippet_truncation(self) -> None:
        """Should truncate long raw snippets."""
        long_snippet = "x" * 200
        error = LLMOutputError("Test error", raw_snippet=long_snippet)
        message = str(error)
        assert "..." in message
        assert len(message) < 250

    def test_not_recoverable(self) -> None:
        """Output errors should not be recoverable by default."""
        error = LLMOutputError("Test")
        assert error.recoverable is False


class TestInvalidJSONError:
    """Tests for InvalidJSONError."""

    def test_default_message(self) -> None:
        """Should have default message."""
        error = InvalidJSONError()
        assert "not valid JSON" in str(error)

    def test_custom_message(self) -> None:
        """Should support custom message."""
        error = InvalidJSONError("Custom JSON error")
        assert "Custom JSON error" in str(error)

    def test_with_parse_error(self) -> None:
        """Should include parse error in message."""
        error = InvalidJSONError(
            parse_error="Unexpected token at position 10"
        )
        assert "Unexpected token at position 10" in str(error)

    def test_with_raw_snippet(self) -> None:
        """Should include raw snippet."""
        error = InvalidJSONError(
            raw_snippet='{"broken": }'
        )
        assert '{"broken": }' in str(error)

    def test_attributes(self) -> None:
        """Should have correct attributes."""
        error = InvalidJSONError(
            "Test",
            parse_error="parse failed",
            raw_snippet="snippet",
            details="extra details",
        )
        assert error.parse_error == "parse failed"
        assert error.raw_snippet == "snippet"
        assert error.details == "extra details"


class TestSchemaViolationError:
    """Tests for SchemaViolationError."""

    def test_default_message(self) -> None:
        """Should have default message."""
        error = SchemaViolationError()
        assert "schema" in str(error).lower()

    def test_with_schema_path(self) -> None:
        """Should include schema path."""
        error = SchemaViolationError(schema_path="payload.name")
        assert "payload.name" in str(error)

    def test_with_validation_errors(self) -> None:
        """Should include validation errors."""
        error = SchemaViolationError(
            validation_errors=[
                "'name' is required",
                "'description' is required",
            ]
        )
        message = str(error)
        assert "'name' is required" in message
        assert "'description' is required" in message

    def test_validation_errors_truncation(self) -> None:
        """Should truncate many validation errors."""
        errors = [f"Error {i}" for i in range(10)]
        error = SchemaViolationError(validation_errors=errors)
        message = str(error)
        # Should show first 3 and indicate more
        assert "+7 more" in message

    def test_attributes(self) -> None:
        """Should have correct attributes."""
        error = SchemaViolationError(
            "Test",
            schema_path="$.payload",
            validation_errors=["err1", "err2"],
        )
        assert error.schema_path == "$.payload"
        assert error.validation_errors == ["err1", "err2"]


class TestCodeInOutputError:
    """Tests for CodeInOutputError."""

    def test_default_message(self) -> None:
        """Should have default message."""
        error = CodeInOutputError()
        assert "code" in str(error).lower()

    def test_with_location(self) -> None:
        """Should include location."""
        error = CodeInOutputError(location="payload.description")
        assert "payload.description" in str(error)

    def test_with_code_snippet(self) -> None:
        """Should include code snippet."""
        error = CodeInOutputError(code_snippet="def foo():\n    pass")
        assert "def foo():" in str(error)

    def test_code_snippet_truncation(self) -> None:
        """Should truncate long code snippets."""
        long_code = "def test():\n" + "    x = 1\n" * 20
        error = CodeInOutputError(code_snippet=long_code)
        message = str(error)
        assert "..." in message

    def test_attributes(self) -> None:
        """Should have correct attributes."""
        error = CodeInOutputError(
            "Test",
            location="field.path",
            code_snippet="code here",
        )
        assert error.location == "field.path"
        assert error.code_snippet == "code here"


class TestMultipleArtifactsError:
    """Tests for MultipleArtifactsError."""

    def test_default_message(self) -> None:
        """Should have default message."""
        error = MultipleArtifactsError()
        assert "multiple" in str(error).lower()

    def test_with_count(self) -> None:
        """Should include count."""
        error = MultipleArtifactsError(count=3)
        assert "3" in str(error)

    def test_attributes(self) -> None:
        """Should have correct attributes."""
        error = MultipleArtifactsError("Test", count=5)
        assert error.count == 5


class TestExplanatoryTextError:
    """Tests for ExplanatoryTextError."""

    def test_default_message(self) -> None:
        """Should have default message."""
        error = ExplanatoryTextError()
        assert "explanatory text" in str(error).lower()

    def test_with_text_snippet(self) -> None:
        """Should include text snippet."""
        error = ExplanatoryTextError(
            text_snippet="Here is the JSON output:"
        )
        assert "Here is the JSON output:" in str(error)

    def test_text_snippet_truncation(self) -> None:
        """Should truncate long text snippets."""
        long_text = "This is some explanatory text. " * 10
        error = ExplanatoryTextError(text_snippet=long_text)
        message = str(error)
        assert "..." in message

    def test_attributes(self) -> None:
        """Should have correct attributes."""
        error = ExplanatoryTextError("Test", text_snippet="text here")
        assert error.text_snippet == "text here"


class TestErrorRecoverability:
    """Tests for error recoverability flags."""

    def test_all_output_errors_not_recoverable(self) -> None:
        """All output errors should be non-recoverable."""
        errors = [
            LLMOutputError("test"),
            InvalidJSONError(),
            SchemaViolationError(),
            CodeInOutputError(),
            MultipleArtifactsError(),
            ExplanatoryTextError(),
        ]
        for error in errors:
            assert error.recoverable is False, f"{type(error).__name__} should not be recoverable"


class TestErrorMessageFormatting:
    """Tests for error message formatting."""

    def test_invalid_json_full_message(self) -> None:
        """Should format InvalidJSONError with all details."""
        error = InvalidJSONError(
            "Invalid JSON received",
            parse_error="Unexpected EOF",
            raw_snippet='{"incomplete":',
        )
        message = str(error)
        assert "Invalid JSON received" in message
        assert "Unexpected EOF" in message
        assert '{"incomplete":' in message

    def test_schema_violation_full_message(self) -> None:
        """Should format SchemaViolationError with all details."""
        error = SchemaViolationError(
            "Schema validation failed",
            schema_path="payload.name",
            validation_errors=["'name' must be a string"],
        )
        message = str(error)
        assert "Schema validation failed" in message
        assert "payload.name" in message
        assert "'name' must be a string" in message

    def test_code_in_output_full_message(self) -> None:
        """Should format CodeInOutputError with all details."""
        error = CodeInOutputError(
            "Found source code",
            location="payload.impl",
            code_snippet="def test():",
        )
        message = str(error)
        assert "Found source code" in message
        assert "payload.impl" in message
        assert "def test():" in message
