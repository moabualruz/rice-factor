"""Unit tests for FailureParser."""

import json

import pytest

from rice_factor.domain.failures.llm_errors import (
    LLMError,
    LLMInvalidRequestError,
    LLMMissingInformationError,
)
from rice_factor.domain.services.failure_parser import FailureParser


class TestFailureParser:
    """Tests for FailureParser class."""

    @pytest.fixture
    def parser(self) -> FailureParser:
        """Create a parser instance."""
        return FailureParser()

    def test_parse_missing_information_error(self, parser: FailureParser) -> None:
        """Should parse missing_information error response."""
        response = json.dumps({
            "error": "missing_information",
            "details": "Domain 'User' not defined"
        })

        error = parser.parse(response)

        assert error is not None
        assert isinstance(error, LLMMissingInformationError)
        assert error.details == "Domain 'User' not defined"
        assert error.recoverable is False

    def test_parse_invalid_request_error(self, parser: FailureParser) -> None:
        """Should parse invalid_request error response."""
        response = json.dumps({
            "error": "invalid_request",
            "details": "Schema validation failed"
        })

        error = parser.parse(response)

        assert error is not None
        assert isinstance(error, LLMInvalidRequestError)
        assert error.invalid_reason == "Schema validation failed"
        assert error.recoverable is False

    def test_parse_unknown_error_type(self, parser: FailureParser) -> None:
        """Should parse unknown error types as generic LLMError."""
        response = json.dumps({
            "error": "unknown_error",
            "details": "Something went wrong"
        })

        error = parser.parse(response)

        assert error is not None
        assert isinstance(error, LLMError)
        assert "unknown_error" in str(error)

    def test_parse_non_error_response_returns_none(self, parser: FailureParser) -> None:
        """Should return None for valid non-error responses."""
        response = json.dumps({
            "goals": ["Goal 1"],
            "domains": []
        })

        error = parser.parse(response)

        assert error is None

    def test_parse_invalid_json_returns_none(self, parser: FailureParser) -> None:
        """Should return None for invalid JSON."""
        response = "not valid json {"

        error = parser.parse(response)

        assert error is None

    def test_parse_empty_string_returns_none(self, parser: FailureParser) -> None:
        """Should return None for empty string."""
        error = parser.parse("")

        assert error is None

    def test_parse_non_dict_json_returns_none(self, parser: FailureParser) -> None:
        """Should return None for non-dict JSON."""
        response = json.dumps(["array", "value"])

        error = parser.parse(response)

        assert error is None


class TestIsFailureResponse:
    """Tests for is_failure_response method."""

    @pytest.fixture
    def parser(self) -> FailureParser:
        """Create a parser instance."""
        return FailureParser()

    def test_is_failure_with_error_key(self, parser: FailureParser) -> None:
        """Should return True when error key present."""
        data = {"error": "missing_information", "details": "info"}

        assert parser.is_failure_response(data) is True

    def test_is_failure_without_error_key(self, parser: FailureParser) -> None:
        """Should return False when no error key."""
        data = {"goals": ["Goal 1"]}

        assert parser.is_failure_response(data) is False

    def test_is_failure_empty_dict(self, parser: FailureParser) -> None:
        """Should return False for empty dict."""
        assert parser.is_failure_response({}) is False


class TestErrorConstants:
    """Tests for error type constants."""

    def test_missing_info_constant(self) -> None:
        """Missing info constant should be correct."""
        assert FailureParser.ERROR_TYPE_MISSING_INFO == "missing_information"

    def test_invalid_request_constant(self) -> None:
        """Invalid request constant should be correct."""
        assert FailureParser.ERROR_TYPE_INVALID_REQUEST == "invalid_request"


class TestMissingItemsExtraction:
    """Tests for missing items extraction from details."""

    @pytest.fixture
    def parser(self) -> FailureParser:
        """Create a parser instance."""
        return FailureParser()

    def test_extracts_details_as_missing_item(self, parser: FailureParser) -> None:
        """Should extract details as a missing item."""
        response = json.dumps({
            "error": "missing_information",
            "details": "Domain 'Auth' not defined"
        })

        error = parser.parse(response)

        assert isinstance(error, LLMMissingInformationError)
        assert "Domain 'Auth' not defined" in error.missing_items

    def test_empty_details_gives_empty_list(self, parser: FailureParser) -> None:
        """Should give empty list for empty details."""
        response = json.dumps({
            "error": "missing_information",
            "details": ""
        })

        error = parser.parse(response)

        assert isinstance(error, LLMMissingInformationError)
        assert error.missing_items == []
