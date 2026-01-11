"""Tests for TestRunnerAdapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.validators.test_runner_adapter import TestRunnerAdapter
from rice_factor.domain.artifacts.validation_types import ValidationContext
from rice_factor.domain.failures.validation_errors import (
    CommandNotFoundError,
    LanguageNotSupportedError,
    ValidationTimeoutError,
)


@pytest.fixture
def adapter() -> TestRunnerAdapter:
    """Create a TestRunnerAdapter instance."""
    return TestRunnerAdapter()


@pytest.fixture
def context() -> ValidationContext:
    """Create a validation context."""
    return ValidationContext(
        repo_root=Path("/test/repo"),
        language="python",
        config={},
    )


class TestTestRunnerAdapter:
    """Tests for TestRunnerAdapter."""

    def test_name_property(self, adapter: TestRunnerAdapter) -> None:
        """Test that name returns 'test_runner'."""
        assert adapter.name == "test_runner"

    def test_supported_languages(self, adapter: TestRunnerAdapter) -> None:
        """Test supported languages list."""
        expected = ["python", "rust", "go", "javascript", "typescript", "java"]
        assert set(adapter.supported_languages) == set(expected)

    def test_get_test_command_python(self, adapter: TestRunnerAdapter) -> None:
        """Test getting test command for Python."""
        assert adapter.get_test_command("python") == ["pytest"]

    def test_get_test_command_rust(self, adapter: TestRunnerAdapter) -> None:
        """Test getting test command for Rust."""
        assert adapter.get_test_command("rust") == ["cargo", "test"]

    def test_get_test_command_go(self, adapter: TestRunnerAdapter) -> None:
        """Test getting test command for Go."""
        assert adapter.get_test_command("go") == ["go", "test", "./..."]

    def test_get_test_command_javascript(self, adapter: TestRunnerAdapter) -> None:
        """Test getting test command for JavaScript."""
        assert adapter.get_test_command("javascript") == ["npm", "test"]

    def test_get_test_command_typescript(self, adapter: TestRunnerAdapter) -> None:
        """Test getting test command for TypeScript."""
        assert adapter.get_test_command("typescript") == ["npm", "test"]

    def test_get_test_command_java(self, adapter: TestRunnerAdapter) -> None:
        """Test getting test command for Java."""
        assert adapter.get_test_command("java") == ["mvn", "test"]

    def test_get_test_command_unsupported(self, adapter: TestRunnerAdapter) -> None:
        """Test getting test command for unsupported language."""
        assert adapter.get_test_command("cobol") is None

    def test_get_test_command_case_insensitive(
        self, adapter: TestRunnerAdapter
    ) -> None:
        """Test that language matching is case insensitive."""
        assert adapter.get_test_command("Python") == ["pytest"]
        assert adapter.get_test_command("PYTHON") == ["pytest"]

    @patch.object(TestRunnerAdapter, "_command_exists", return_value=True)
    @patch.object(TestRunnerAdapter, "_run_command")
    def test_validate_passing_tests(
        self,
        mock_run: MagicMock,
        _mock_exists: MagicMock,
        adapter: TestRunnerAdapter,
        context: ValidationContext,
        tmp_path: Path,
    ) -> None:
        """Test validation with passing tests."""
        mock_run.return_value = (0, "All tests passed", "")

        result = adapter.validate(tmp_path, context)

        assert result.passed
        assert result.status == "passed"
        assert result.errors == []
        assert result.validator == "test_runner"
        mock_run.assert_called_once()

    @patch.object(TestRunnerAdapter, "_command_exists", return_value=True)
    @patch.object(TestRunnerAdapter, "_run_command")
    def test_validate_failing_tests(
        self,
        mock_run: MagicMock,
        _mock_exists: MagicMock,
        adapter: TestRunnerAdapter,
        context: ValidationContext,
        tmp_path: Path,
    ) -> None:
        """Test validation with failing tests."""
        mock_run.return_value = (1, "FAILED test_foo", "AssertionError")

        result = adapter.validate(tmp_path, context)

        assert result.failed
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert result.validator == "test_runner"

    def test_validate_unsupported_language(
        self, adapter: TestRunnerAdapter, tmp_path: Path
    ) -> None:
        """Test validation with unsupported language raises error."""
        context = ValidationContext(
            repo_root=tmp_path,
            language="cobol",
            config={},
        )

        with pytest.raises(LanguageNotSupportedError) as exc_info:
            adapter.validate(tmp_path, context)

        assert exc_info.value.language == "cobol"
        assert "python" in exc_info.value.supported_languages

    @patch.object(TestRunnerAdapter, "_command_exists", return_value=False)
    def test_validate_missing_command(
        self, _mock_exists: MagicMock, adapter: TestRunnerAdapter, tmp_path: Path
    ) -> None:
        """Test validation when test command is not found."""
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={},
        )

        with pytest.raises(CommandNotFoundError) as exc_info:
            adapter.validate(tmp_path, context)

        assert exc_info.value.command == "pytest"
        assert exc_info.value.validator == "test_runner"

    @patch.object(TestRunnerAdapter, "_command_exists", return_value=True)
    @patch.object(TestRunnerAdapter, "_run_command")
    def test_validate_timeout(
        self,
        mock_run: MagicMock,
        _mock_exists: MagicMock,
        adapter: TestRunnerAdapter,
        context: ValidationContext,
        tmp_path: Path,
    ) -> None:
        """Test validation timeout."""
        mock_run.side_effect = ValidationTimeoutError("pytest", 300)

        with pytest.raises(ValidationTimeoutError) as exc_info:
            adapter.validate(tmp_path, context)

        assert exc_info.value.timeout_seconds == 300

    @patch.object(TestRunnerAdapter, "_command_exists", return_value=True)
    @patch.object(TestRunnerAdapter, "_run_command")
    def test_validate_custom_timeout(
        self,
        mock_run: MagicMock,
        _mock_exists: MagicMock,
        adapter: TestRunnerAdapter,
        tmp_path: Path,
    ) -> None:
        """Test validation with custom timeout from config."""
        mock_run.return_value = (0, "", "")
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={"test_timeout": 60},
        )

        adapter.validate(tmp_path, context)

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1]["timeout_seconds"] == 60


class TestTestOutputParsing:
    """Tests for test output parsing."""

    @pytest.fixture
    def adapter(self) -> TestRunnerAdapter:
        """Create adapter for parsing tests."""
        return TestRunnerAdapter()

    def test_parse_pytest_output_with_failures(
        self, adapter: TestRunnerAdapter
    ) -> None:
        """Test parsing pytest output with failures."""
        stdout = """
        tests/test_foo.py::test_bar FAILED
        tests/test_foo.py::test_baz FAILED

        ===== 2 failed, 10 passed =====
        """
        errors = adapter.parse_test_output(stdout, "", "python")

        assert len(errors) > 0
        assert any("FAILED" in e for e in errors)

    def test_parse_pytest_output_with_errors(
        self, adapter: TestRunnerAdapter
    ) -> None:
        """Test parsing pytest output with errors."""
        stdout = """
        ERROR tests/test_foo.py

        ===== 1 error =====
        """
        errors = adapter.parse_test_output(stdout, "", "python")

        assert len(errors) > 0
        assert any("ERROR" in e for e in errors)

    def test_parse_cargo_test_output(self, adapter: TestRunnerAdapter) -> None:
        """Test parsing cargo test output."""
        stdout = """
        running 5 tests
        test test_foo ... FAILED
        test test_bar ... ok

        failures:
            test_foo

        test result: FAILED. 1 failed; 4 passed
        """
        errors = adapter.parse_test_output(stdout, "", "rust")

        assert len(errors) > 0

    def test_parse_go_test_output(self, adapter: TestRunnerAdapter) -> None:
        """Test parsing go test output."""
        stdout = """--- FAIL: TestFoo (0.00s)
FAIL    example.com/foo   0.001s
"""
        errors = adapter.parse_test_output(stdout, "", "go")

        assert len(errors) > 0
        assert any("FAIL" in e for e in errors)

    def test_parse_empty_output(self, adapter: TestRunnerAdapter) -> None:
        """Test parsing empty output."""
        errors = adapter.parse_test_output("", "", "python")

        assert len(errors) == 1
        assert "no output" in errors[0].lower()
