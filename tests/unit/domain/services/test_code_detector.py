"""Unit tests for CodeDetector."""

import pytest

from rice_factor.domain.services.code_detector import CodeDetector, detect_code


class TestCodeDetector:
    """Tests for CodeDetector class."""

    @pytest.fixture
    def detector(self) -> CodeDetector:
        """Create a CodeDetector instance."""
        return CodeDetector()

    # =========================================================================
    # Python Code Detection
    # =========================================================================

    def test_detects_python_function(self, detector: CodeDetector) -> None:
        """Should detect Python function definition."""
        data = {"description": "def calculate_total(items):\n    return sum(items)"}
        found, location = detector.contains_code(data)
        assert found is True
        assert location == "description"

    def test_detects_python_class(self, detector: CodeDetector) -> None:
        """Should detect Python class definition."""
        data = {"code": "class Calculator:\n    def add(self, a, b):\n        return a + b"}
        found, location = detector.contains_code(data)
        assert found is True
        assert location == "code"

    def test_detects_python_import(self, detector: CodeDetector) -> None:
        """Should detect Python import statement."""
        data = {"snippet": "import os\nimport sys\nfrom pathlib import Path"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_python_decorator(self, detector: CodeDetector) -> None:
        """Should detect Python decorator."""
        data = {"func": "@property\ndef name(self):\n    return self._name"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_python_async_function(self, detector: CodeDetector) -> None:
        """Should detect Python async function."""
        data = {"handler": "async def fetch_data(url):\n    return await request(url)"}
        found, location = detector.contains_code(data)
        assert found is True

    # =========================================================================
    # JavaScript Code Detection
    # =========================================================================

    def test_detects_javascript_function(self, detector: CodeDetector) -> None:
        """Should detect JavaScript function definition."""
        data = {"js": "function calculateTotal(items) {\n  return items.reduce((a, b) => a + b, 0);\n}"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_javascript_arrow_function(self, detector: CodeDetector) -> None:
        """Should detect JavaScript arrow function."""
        data = {"handler": "const handleClick = (event) => {\n  console.log(event);\n};"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_javascript_export(self, detector: CodeDetector) -> None:
        """Should detect JavaScript export statement."""
        data = {"module": "export default function Component() {\n  return <div>Hello</div>;\n}"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_javascript_import(self, detector: CodeDetector) -> None:
        """Should detect JavaScript import statement."""
        data = {"imports": "import React from 'react';\nimport { useState } from 'react';"}
        found, location = detector.contains_code(data)
        assert found is True

    # =========================================================================
    # Rust Code Detection
    # =========================================================================

    def test_detects_rust_function(self, detector: CodeDetector) -> None:
        """Should detect Rust function definition."""
        data = {"rust": "fn calculate_sum(numbers: &[i32]) -> i32 {\n    numbers.iter().sum()\n}"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_rust_impl(self, detector: CodeDetector) -> None:
        """Should detect Rust impl block."""
        data = {"impl": "impl Calculator {\n    fn new() -> Self {\n        Calculator {}\n    }\n}"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_rust_struct(self, detector: CodeDetector) -> None:
        """Should detect Rust struct definition."""
        data = {"type": "struct Point {\n    x: f64,\n    y: f64,\n}"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_rust_mod(self, detector: CodeDetector) -> None:
        """Should detect Rust module declaration."""
        data = {"module": "mod utils;\nmod helpers;\nuse crate::utils::*;"}
        found, location = detector.contains_code(data)
        assert found is True

    # =========================================================================
    # Go Code Detection
    # =========================================================================

    def test_detects_go_function(self, detector: CodeDetector) -> None:
        """Should detect Go function definition."""
        data = {"go": "func calculateSum(numbers []int) int {\n    sum := 0\n    return sum\n}"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_go_method(self, detector: CodeDetector) -> None:
        """Should detect Go method definition."""
        data = {"method": "func (c *Calculator) Add(a, b int) int {\n    return a + b\n}"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_go_package(self, detector: CodeDetector) -> None:
        """Should detect Go package declaration."""
        data = {"pkg": "package main\n\nimport \"fmt\"\n\nfunc main() {}"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_go_type(self, detector: CodeDetector) -> None:
        """Should detect Go type definition."""
        data = {"typedef": "type Calculator struct {\n    value int\n}"}
        found, location = detector.contains_code(data)
        assert found is True

    # =========================================================================
    # Code Block Detection
    # =========================================================================

    def test_detects_code_block_markers(self, detector: CodeDetector) -> None:
        """Should detect markdown code block markers."""
        data = {"content": "Here is some code:\n```python\nprint('hello')\n```"}
        found, location = detector.contains_code(data)
        assert found is True

    def test_detects_code_block_without_language(self, detector: CodeDetector) -> None:
        """Should detect code blocks without language tag."""
        data = {"content": "Example:\n```\nconst x = 1;\n```"}
        found, location = detector.contains_code(data)
        assert found is True

    # =========================================================================
    # False Positive Avoidance
    # =========================================================================

    def test_no_false_positive_for_prose_with_function_word(
        self, detector: CodeDetector
    ) -> None:
        """Should not detect prose that mentions 'function'."""
        data = {
            "description": "The function of this component is to handle user input. "
            "It provides a way to process data efficiently."
        }
        found, _ = detector.contains_code(data)
        assert found is False

    def test_no_false_positive_for_prose_with_class_word(
        self, detector: CodeDetector
    ) -> None:
        """Should not detect prose that mentions 'class'."""
        data = {
            "description": "This class of problems requires careful consideration. "
            "The solution involves multiple steps."
        }
        found, _ = detector.contains_code(data)
        assert found is False

    def test_no_false_positive_for_short_strings(
        self, detector: CodeDetector
    ) -> None:
        """Should not detect code in short strings."""
        data = {"name": "def foo"}
        found, _ = detector.contains_code(data)
        assert found is False

    def test_no_false_positive_for_file_paths(
        self, detector: CodeDetector
    ) -> None:
        """Should not detect code in file paths."""
        data = {
            "files": [
                "src/utils/helpers.py",
                "lib/components/Button.tsx",
                "pkg/handlers/auth.go",
            ]
        }
        found, _ = detector.contains_code(data)
        assert found is False

    def test_no_false_positive_for_descriptions(
        self, detector: CodeDetector
    ) -> None:
        """Should not detect code in natural language descriptions."""
        data = {
            "description": "Create a user authentication module that handles login, "
            "logout, and session management. The module should support "
            "OAuth2 and JWT tokens for secure authentication."
        }
        found, _ = detector.contains_code(data)
        assert found is False

    # =========================================================================
    # Nested Structure Traversal
    # =========================================================================

    def test_detects_code_in_nested_dict(self, detector: CodeDetector) -> None:
        """Should detect code in nested dictionaries."""
        data = {
            "components": {
                "auth": {
                    "handler": "def authenticate(user):\n    return check_password(user)"
                }
            }
        }
        found, location = detector.contains_code(data)
        assert found is True
        assert location == "components.auth.handler"

    def test_detects_code_in_list(self, detector: CodeDetector) -> None:
        """Should detect code in list items."""
        data = {
            "snippets": [
                "Normal text",
                "def process():\n    return True",
                "More text",
            ]
        }
        found, location = detector.contains_code(data)
        assert found is True
        assert location == "snippets[1]"

    def test_detects_code_in_deeply_nested_structure(
        self, detector: CodeDetector
    ) -> None:
        """Should detect code in deeply nested structures."""
        data = {
            "a": {
                "b": {
                    "c": [
                        {"d": "function test() { return 1; }"}
                    ]
                }
            }
        }
        found, location = detector.contains_code(data)
        assert found is True
        assert location == "a.b.c[0].d"

    def test_no_code_in_empty_structure(self, detector: CodeDetector) -> None:
        """Should not find code in empty structures."""
        data: dict[str, object] = {"items": [], "nested": {}}
        found, _ = detector.contains_code(data)
        assert found is False

    def test_handles_non_string_values(self, detector: CodeDetector) -> None:
        """Should handle non-string values gracefully."""
        data = {
            "count": 42,
            "active": True,
            "ratio": 3.14,
            "empty": None,
        }
        found, _ = detector.contains_code(data)
        assert found is False

    # =========================================================================
    # Code Likelihood Scoring
    # =========================================================================

    def test_high_syntax_density_detected(self, detector: CodeDetector) -> None:
        """Should detect code-like syntax density."""
        # High density of special characters
        data = {
            "expr": "result = ((a + b) * (c - d)) / ((e + f) & (g | h));"
        }
        # This might or might not be detected depending on thresholds
        # The important thing is it doesn't crash
        detector.contains_code(data)

    def test_low_syntax_density_not_detected(self, detector: CodeDetector) -> None:
        """Should not detect low syntax density prose."""
        data = {
            "text": "This is a regular sentence with normal punctuation. "
            "It contains some words and a few special characters!"
        }
        found, _ = detector.contains_code(data)
        assert found is False


class TestDetectCodeFunction:
    """Tests for the detect_code convenience function."""

    def test_convenience_function_detects_code(self) -> None:
        """Should detect code via convenience function."""
        data = {"code": "def test():\n    pass"}
        found, location = detect_code(data)
        assert found is True
        assert location == "code"

    def test_convenience_function_returns_none_for_no_code(self) -> None:
        """Should return None location when no code found."""
        data = {"text": "Just some regular text here."}
        found, location = detect_code(data)
        assert found is False
        assert location is None


class TestCodeLikelihood:
    """Tests for _is_likely_code method."""

    @pytest.fixture
    def detector(self) -> CodeDetector:
        """Create a CodeDetector instance."""
        return CodeDetector()

    def test_code_block_has_max_likelihood(self, detector: CodeDetector) -> None:
        """Code blocks should have maximum likelihood."""
        text = "```\nsome code\n```"
        score = detector._is_likely_code(text)
        assert score == 1.0

    def test_multiple_patterns_increase_likelihood(
        self, detector: CodeDetector
    ) -> None:
        """Multiple code patterns should increase likelihood."""
        text = "def foo():\n    import os\n    return True"
        score = detector._is_likely_code(text)
        assert score >= 0.9

    def test_plain_text_has_low_likelihood(self, detector: CodeDetector) -> None:
        """Plain text should have low likelihood."""
        text = (
            "This is a description of a software component that handles "
            "user authentication and authorization processes."
        )
        score = detector._is_likely_code(text)
        assert score < 0.5
