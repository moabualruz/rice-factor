"""Code detection service.

This module provides the CodeDetector class for detecting source code
in LLM output. The LLM should only output structured JSON, not code.
"""

import re
from typing import Any, ClassVar


class CodeDetector:
    """Detects source code in artifact data.

    Used to ensure LLM outputs are structured plans, not actual code.
    Recursively checks all string values in a data structure.
    """

    # Patterns that strongly indicate code
    CODE_PATTERNS: ClassVar[list[tuple[str, re.Pattern[str]]]] = [
        # Python
        ("python", re.compile(r"^\s*def\s+\w+\s*\(", re.MULTILINE)),
        ("python", re.compile(r"^\s*class\s+\w+\s*[:\(]", re.MULTILINE)),
        ("python", re.compile(r"^\s*import\s+\w+", re.MULTILINE)),
        ("python", re.compile(r"^\s*from\s+\w+\s+import\s+", re.MULTILINE)),
        ("python", re.compile(r"^\s*async\s+def\s+", re.MULTILINE)),
        ("python", re.compile(r"^\s*@\w+(\.\w+)*\s*(\(.*\))?\s*$", re.MULTILINE)),
        # JavaScript/TypeScript
        ("javascript", re.compile(r"^\s*function\s+\w+\s*\(", re.MULTILINE)),
        ("javascript", re.compile(r"^\s*const\s+\w+\s*=\s*\(.*\)\s*=>", re.MULTILINE)),
        ("javascript", re.compile(r"^\s*let\s+\w+\s*=\s*\(.*\)\s*=>", re.MULTILINE)),
        ("javascript", re.compile(r"^\s*var\s+\w+\s*=\s*function", re.MULTILINE)),
        ("javascript", re.compile(r"^\s*export\s+(default\s+)?(function|class|const)", re.MULTILINE)),
        ("javascript", re.compile(r"^\s*import\s+.*\s+from\s+['\"]", re.MULTILINE)),
        # Rust
        ("rust", re.compile(r"^\s*fn\s+\w+\s*(<.*>)?\s*\(", re.MULTILINE)),
        ("rust", re.compile(r"^\s*impl\s+(<.*>)?\s*\w+", re.MULTILINE)),
        ("rust", re.compile(r"^\s*struct\s+\w+", re.MULTILINE)),
        ("rust", re.compile(r"^\s*enum\s+\w+", re.MULTILINE)),
        ("rust", re.compile(r"^\s*mod\s+\w+", re.MULTILINE)),
        ("rust", re.compile(r"^\s*use\s+\w+::", re.MULTILINE)),
        # Go
        ("go", re.compile(r"^\s*func\s+(\(\w+\s+\*?\w+\)\s*)?\w+\s*\(", re.MULTILINE)),
        ("go", re.compile(r"^\s*package\s+\w+", re.MULTILINE)),
        ("go", re.compile(r"^\s*type\s+\w+\s+(struct|interface)", re.MULTILINE)),
        # Java/Kotlin
        ("java", re.compile(r"^\s*(public|private|protected)\s+(static\s+)?(class|interface|void|int|String)", re.MULTILINE)),
        # Code block markers
        ("markdown", re.compile(r"```\w*\n", re.MULTILINE)),
    ]

    # Minimum length for a string to be checked for code
    MIN_CHECK_LENGTH = 20

    # Minimum code likelihood to trigger detection
    CODE_THRESHOLD = 0.6

    def contains_code(self, data: Any) -> tuple[bool, str | None]:
        """Check if data contains source code.

        Recursively traverses the data structure and checks all string
        values for code patterns.

        Args:
            data: The data structure to check (dict, list, or string).

        Returns:
            Tuple of (found, location) where:
            - found: True if code was detected
            - location: Path to the location where code was found, or None
        """
        return self._check_recursive(data, "")

    def _check_recursive(
        self, data: Any, path: str
    ) -> tuple[bool, str | None]:
        """Recursively check for code in data.

        Args:
            data: Data to check.
            path: Current path in the data structure.

        Returns:
            Tuple of (found, location).
        """
        if isinstance(data, str):
            if self._is_code_snippet(data):
                return True, path or "$"
            return False, None

        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                found, location = self._check_recursive(value, new_path)
                if found:
                    return True, location
            return False, None

        if isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                found, location = self._check_recursive(item, new_path)
                if found:
                    return True, location
            return False, None

        # Other types (int, float, bool, None) don't contain code
        return False, None

    def _is_code_snippet(self, text: str) -> bool:
        """Check if text appears to be code.

        Args:
            text: Text to check.

        Returns:
            True if text appears to be code.
        """
        # Skip short strings
        if len(text) < self.MIN_CHECK_LENGTH:
            return False

        # Check likelihood score
        likelihood = self._is_likely_code(text)
        return likelihood >= self.CODE_THRESHOLD

    def _is_likely_code(self, text: str) -> float:
        """Calculate likelihood that text is source code.

        Args:
            text: Text to analyze.

        Returns:
            Confidence score from 0.0 to 1.0.
        """
        # Check for explicit code block markers (highest confidence)
        if "```" in text:
            return 1.0

        # Check for code patterns
        pattern_matches = 0
        for _lang, pattern in self.CODE_PATTERNS:
            if pattern.search(text):
                pattern_matches += 1
                # Multiple pattern matches = very likely code
                if pattern_matches >= 2:
                    return 0.9

        # Single pattern match
        if pattern_matches == 1:
            # Check for additional code indicators
            score = 0.5

            # Indentation patterns (common in code)
            if re.search(r"^\s{2,}\w", text, re.MULTILINE):
                score += 0.1

            # Semicolons at end of lines
            if re.search(r";\s*$", text, re.MULTILINE):
                score += 0.1

            # Curly braces
            if "{" in text and "}" in text:
                score += 0.1

            # Parentheses after words (function calls)
            if re.search(r"\w+\([^)]*\)", text):
                score += 0.05

            return min(score, 1.0)

        # No pattern matches - check syntax density
        return self._calculate_syntax_density(text)

    def _calculate_syntax_density(self, text: str) -> float:
        """Calculate code syntax density score.

        High density of special characters often indicates code.

        Args:
            text: Text to analyze.

        Returns:
            Score from 0.0 to 1.0.
        """
        if not text:
            return 0.0

        # Count syntax characters
        syntax_chars = set("{}[]();=<>+-*/&|^~!")
        syntax_count = sum(1 for c in text if c in syntax_chars)

        # Calculate density
        density = syntax_count / len(text)

        # Code typically has 5-15% syntax characters
        # Prose typically has < 2%
        if density > 0.08:
            return 0.5
        if density > 0.05:
            return 0.3
        return 0.0


def detect_code(data: Any) -> tuple[bool, str | None]:
    """Convenience function to detect code in data.

    Args:
        data: Data structure to check.

    Returns:
        Tuple of (found, location).
    """
    detector = CodeDetector()
    return detector.contains_code(data)
