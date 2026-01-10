"""LLM failure response parser.

This module provides the FailureParser service that parses LLM responses
to detect explicit failure responses (missing_information, invalid_request).
"""

import json
from typing import Any

from rice_factor.domain.failures.llm_errors import (
    LLMError,
    LLMInvalidRequestError,
    LLMMissingInformationError,
)


class FailureParser:
    """Parser for LLM failure responses.

    Detects and parses explicit failure responses from the LLM that
    follow the format: {"error": "<type>", "details": "<description>"}
    """

    # Known error types that the LLM can return
    ERROR_TYPE_MISSING_INFO = "missing_information"
    ERROR_TYPE_INVALID_REQUEST = "invalid_request"

    def parse(self, response: str) -> LLMError | None:
        """Parse an LLM response to detect failure responses.

        Args:
            response: Raw LLM response string (expected to be JSON)

        Returns:
            Appropriate LLMError subclass if response is a failure,
            None if response is not a failure.
        """
        try:
            data = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            # Not valid JSON - not a structured failure
            return None

        if not isinstance(data, dict):
            return None

        if not self.is_failure_response(data):
            return None

        error_type = data.get("error", "")
        details = data.get("details", "")

        return self._create_error(error_type, details)

    def is_failure_response(self, data: dict[str, Any]) -> bool:
        """Check if a parsed response dict represents a failure.

        Args:
            data: Parsed JSON response as a dict

        Returns:
            True if the response has an 'error' key indicating failure.
        """
        return "error" in data

    def _create_error(self, error_type: str, details: str) -> LLMError:
        """Create appropriate error type from error string.

        Args:
            error_type: The error type string from the response
            details: The error details string from the response

        Returns:
            Appropriate LLMError subclass instance.
        """
        if error_type == self.ERROR_TYPE_MISSING_INFO:
            # Try to parse missing items from details
            missing_items = self._extract_missing_items(details)
            return LLMMissingInformationError(
                message="LLM reported missing information",
                missing_items=missing_items,
                details=details,
            )
        elif error_type == self.ERROR_TYPE_INVALID_REQUEST:
            return LLMInvalidRequestError(
                message="LLM reported invalid request",
                invalid_reason=details,
                details=details,
            )
        else:
            # Unknown error type - return generic LLM error
            return LLMError(
                message=f"LLM error: {error_type}",
                details=details,
                recoverable=False,
            )

    def _extract_missing_items(self, details: str) -> list[str]:
        """Extract missing item names from error details.

        Attempts to parse out specific missing items from the details string.
        This is a best-effort extraction.

        Args:
            details: The error details string

        Returns:
            List of extracted missing item names, may be empty.
        """
        # Simple heuristic: if details contains specific patterns,
        # try to extract them. Otherwise return the whole details as one item.
        if not details:
            return []

        # Common patterns:
        # "Missing: X, Y, Z"
        # "Domain 'X' not defined"
        # "Required field 'X' missing"

        # For now, return the details as a single item if present
        # More sophisticated parsing can be added later
        return [details] if details else []
