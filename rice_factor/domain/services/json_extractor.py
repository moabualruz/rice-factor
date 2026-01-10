"""JSON extraction service.

This module provides the JSONExtractor class for extracting JSON from
LLM responses. Handles various formats including raw JSON, markdown
code fences, and detects invalid outputs.
"""

import re

from rice_factor.domain.failures.llm_errors import (
    ExplanatoryTextError,
    InvalidJSONError,
    MultipleArtifactsError,
)


class JSONExtractor:
    """Extracts JSON from LLM response text.

    Handles various response formats:
    - Raw JSON (starts with `{`)
    - Markdown code fences (```json ... ```)
    - Code fences without language tag (``` ... ```)

    Validates that:
    - Response contains valid JSON
    - Only one JSON object is present
    - No significant explanatory text outside JSON
    """

    # Pattern for markdown code fences with optional language tag
    CODE_FENCE_PATTERN = re.compile(
        r"```(?:json)?\s*\n([\s\S]*?)\n```",
        re.MULTILINE,
    )

    # Pattern for detecting multiple top-level JSON objects
    # Looks for `}{` or `}\n{` patterns
    MULTIPLE_JSON_PATTERN = re.compile(r"\}\s*\{")

    # Minimum length of text outside JSON to consider as explanatory
    MIN_EXPLANATORY_LENGTH = 20

    def extract(self, raw_response: str) -> str:
        """Extract JSON from LLM response.

        Args:
            raw_response: The raw LLM response text.

        Returns:
            The extracted JSON string.

        Raises:
            InvalidJSONError: If no JSON is found in the response.
            MultipleArtifactsError: If multiple JSON objects are found.
            ExplanatoryTextError: If significant text exists outside JSON.
        """
        response = raw_response.strip()

        if not response:
            raise InvalidJSONError(
                "Empty response",
                raw_snippet=raw_response[:100] if raw_response else None,
            )

        # Try to find JSON in code fences first
        json_str = self._find_json_in_fences(response)

        if json_str is not None:
            # Check for explanatory text outside fences
            if self._has_explanatory_text(response, json_str):
                # Find the text outside
                text_outside = response.replace(f"```json\n{json_str}\n```", "")
                text_outside = text_outside.replace(f"```\n{json_str}\n```", "")
                text_outside = text_outside.strip()
                raise ExplanatoryTextError(
                    text_snippet=text_outside[:100] if text_outside else None,
                    raw_snippet=raw_response[:200],
                )
            return json_str

        # Try raw JSON (starts with {)
        if response.startswith("{"):
            # Check for multiple JSON objects
            if self._has_multiple_json_objects(response):
                # Count approximate number of objects
                count = len(self.MULTIPLE_JSON_PATTERN.findall(response)) + 1
                raise MultipleArtifactsError(
                    count=count,
                    raw_snippet=raw_response[:200],
                )
            # Find the actual JSON object and check for trailing text
            json_str = self._find_json_object(response)
            if json_str:
                if self._has_explanatory_text(response, json_str):
                    text_after = response[len(json_str):].strip()
                    raise ExplanatoryTextError(
                        text_snippet=text_after[:100] if text_after else None,
                        raw_snippet=raw_response[:200],
                    )
                return json_str
            return response

        # Try to find JSON object anywhere in the response
        json_match = self._find_json_object(response)
        if json_match:
            json_str = json_match
            # Check for explanatory text
            if self._has_explanatory_text(response, json_str):
                text_before = response[:response.find(json_str)].strip()
                text_after = response[response.find(json_str) + len(json_str):].strip()
                text_outside = f"{text_before} {text_after}".strip()
                raise ExplanatoryTextError(
                    text_snippet=text_outside[:100] if text_outside else None,
                    raw_snippet=raw_response[:200],
                )
            return json_str

        # No JSON found
        raise InvalidJSONError(
            "No JSON object found in response",
            raw_snippet=raw_response[:200],
        )

    def _find_json_in_fences(self, response: str) -> str | None:
        """Find JSON within markdown code fences.

        Args:
            response: The response text.

        Returns:
            The JSON string if found, None otherwise.
        """
        matches = self.CODE_FENCE_PATTERN.findall(response)

        if not matches:
            return None

        if len(matches) > 1:
            # Multiple code fences - check if they're all JSON
            raise MultipleArtifactsError(
                count=len(matches),
                raw_snippet=response[:200],
            )

        json_str: str = matches[0].strip()
        if not json_str:
            return None

        # Verify it looks like JSON
        if json_str.startswith("{") or json_str.startswith("["):
            return json_str

        return None

    def _find_json_object(self, response: str) -> str | None:
        """Find a JSON object by matching braces.

        Args:
            response: The response text.

        Returns:
            The JSON string if found, None otherwise.
        """
        # Find the first `{`
        start = response.find("{")
        if start == -1:
            return None

        # Match braces to find the end
        depth = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(response[start:], start=start):
            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    json_str = response[start:i + 1]
                    # Check for multiple objects after this one
                    remaining = response[i + 1:].strip()
                    if remaining.startswith("{"):
                        raise MultipleArtifactsError(
                            count=2,
                            raw_snippet=response[:200],
                        )
                    return json_str

        # Unmatched braces
        return None

    def _has_multiple_json_objects(self, response: str) -> bool:
        """Check if response contains multiple JSON objects.

        Args:
            response: The response text.

        Returns:
            True if multiple objects are found.
        """
        # Simple check for `}{` pattern (adjacent objects)
        if self.MULTIPLE_JSON_PATTERN.search(response):
            return True

        # Count top-level braces
        depth = 0
        objects = 0
        in_string = False
        escape_next = False

        for char in response:
            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                if depth == 0:
                    objects += 1
                    if objects > 1:
                        return True
                depth += 1
            elif char == "}":
                depth -= 1

        return False

    def _has_explanatory_text(self, response: str, json_str: str) -> bool:
        """Check if response has significant text outside the JSON.

        Args:
            response: The full response.
            json_str: The extracted JSON string.

        Returns:
            True if significant explanatory text is found.
        """
        # Remove the JSON and code fence markers
        remaining = response

        # Remove code fence version
        for fence in [f"```json\n{json_str}\n```", f"```\n{json_str}\n```"]:
            remaining = remaining.replace(fence, "")

        # Remove raw JSON
        remaining = remaining.replace(json_str, "")

        # Remove whitespace
        remaining = remaining.strip()

        # Check if remaining text is significant
        if len(remaining) < self.MIN_EXPLANATORY_LENGTH:
            return False

        # Check if it's just whitespace or punctuation
        return any(c.isalpha() for c in remaining)


def extract_json(raw_response: str) -> str:
    """Convenience function to extract JSON from response.

    Args:
        raw_response: The raw LLM response text.

    Returns:
        The extracted JSON string.

    Raises:
        InvalidJSONError: If no JSON is found.
        MultipleArtifactsError: If multiple JSON objects found.
        ExplanatoryTextError: If text exists outside JSON.
    """
    extractor = JSONExtractor()
    return extractor.extract(raw_response)
