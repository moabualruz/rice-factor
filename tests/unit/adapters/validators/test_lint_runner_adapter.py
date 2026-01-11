"""Tests for LintRunnerAdapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.validators.lint_runner_adapter import LintRunnerAdapter
from rice_factor.domain.artifacts.validation_types import ValidationContext
from rice_factor.domain.failures.validation_errors import ValidationTimeoutError


@pytest.fixture
def adapter() -> LintRunnerAdapter:
    """Create a LintRunnerAdapter instance."""
    return LintRunnerAdapter()


@pytest.fixture
def context() -> ValidationContext:
    """Create a validation context."""
    return ValidationContext(
        repo_root=Path("/test/repo"),
        language="python",
        config={},
    )


class TestLintRunnerAdapter:
    """Tests for LintRunnerAdapter."""

    def test_name_property(self, adapter: LintRunnerAdapter) -> None:
        """Test that name returns 'lint_runner'."""
        assert adapter.name == "lint_runner"

    def test_supported_languages(self, adapter: LintRunnerAdapter) -> None:
        """Test supported languages list."""
        expected = ["python", "rust", "go", "javascript", "typescript"]
        assert set(adapter.supported_languages) == set(expected)

    def test_get_lint_command_python(self, adapter: LintRunnerAdapter) -> None:
        """Test getting lint command for Python."""
        assert adapter.get_lint_command("python") == ["ruff", "check", "."]

    def test_get_lint_command_rust(self, adapter: LintRunnerAdapter) -> None:
        """Test getting lint command for Rust."""
        assert adapter.get_lint_command("rust") == [
            "cargo",
            "clippy",
            "--",
            "-D",
            "warnings",
        ]

    def test_get_lint_command_go(self, adapter: LintRunnerAdapter) -> None:
        """Test getting lint command for Go."""
        assert adapter.get_lint_command("go") == ["golint", "./..."]

    def test_get_lint_command_javascript(self, adapter: LintRunnerAdapter) -> None:
        """Test getting lint command for JavaScript."""
        assert adapter.get_lint_command("javascript") == ["eslint", "."]

    def test_get_lint_command_typescript(self, adapter: LintRunnerAdapter) -> None:
        """Test getting lint command for TypeScript."""
        assert adapter.get_lint_command("typescript") == ["eslint", "."]

    def test_get_lint_command_unsupported(self, adapter: LintRunnerAdapter) -> None:
        """Test getting lint command for unsupported language."""
        assert adapter.get_lint_command("java") is None

    @patch.object(LintRunnerAdapter, "_command_exists", return_value=True)
    @patch.object(LintRunnerAdapter, "_run_command")
    def test_validate_passing_lint(
        self,
        mock_run: MagicMock,
        _mock_exists: MagicMock,
        adapter: LintRunnerAdapter,
        context: ValidationContext,
        tmp_path: Path,
    ) -> None:
        """Test validation with passing lint."""
        mock_run.return_value = (0, "", "")

        result = adapter.validate(tmp_path, context)

        assert result.passed
        assert result.status == "passed"
        assert result.errors == []
        assert result.validator == "lint_runner"

    @patch.object(LintRunnerAdapter, "_command_exists", return_value=True)
    @patch.object(LintRunnerAdapter, "_run_command")
    def test_validate_failing_lint(
        self,
        mock_run: MagicMock,
        _mock_exists: MagicMock,
        adapter: LintRunnerAdapter,
        context: ValidationContext,
        tmp_path: Path,
    ) -> None:
        """Test validation with failing lint."""
        mock_run.return_value = (
            1,
            "src/foo.py:10:5: E501 Line too long (100 > 88 characters)",
            "",
        )

        result = adapter.validate(tmp_path, context)

        assert result.failed
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert result.validator == "lint_runner"

    def test_validate_unsupported_language_passes(
        self, adapter: LintRunnerAdapter, tmp_path: Path
    ) -> None:
        """Test that unsupported language returns passed (lint is optional)."""
        context = ValidationContext(
            repo_root=tmp_path,
            language="java",  # Not in LINT_COMMANDS
            config={},
        )

        result = adapter.validate(tmp_path, context)

        # Unlike test runner, lint is optional - missing linter = pass
        assert result.passed
        assert result.status == "passed"

    @patch.object(LintRunnerAdapter, "_command_exists", return_value=False)
    def test_validate_missing_command_passes(
        self, _mock_exists: MagicMock, adapter: LintRunnerAdapter, tmp_path: Path
    ) -> None:
        """Test that missing linter command returns passed (lint is optional)."""
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={},
        )

        result = adapter.validate(tmp_path, context)

        # Missing linter = pass (lint is optional)
        assert result.passed
        assert result.status == "passed"

    @patch.object(LintRunnerAdapter, "_command_exists", return_value=True)
    @patch.object(LintRunnerAdapter, "_run_command")
    def test_validate_timeout(
        self,
        mock_run: MagicMock,
        _mock_exists: MagicMock,
        adapter: LintRunnerAdapter,
        context: ValidationContext,
        tmp_path: Path,
    ) -> None:
        """Test validation timeout."""
        mock_run.side_effect = ValidationTimeoutError("ruff check .", 120)

        with pytest.raises(ValidationTimeoutError) as exc_info:
            adapter.validate(tmp_path, context)

        assert exc_info.value.timeout_seconds == 120

    @patch.object(LintRunnerAdapter, "_command_exists", return_value=True)
    @patch.object(LintRunnerAdapter, "_run_command")
    def test_validate_custom_timeout(
        self,
        mock_run: MagicMock,
        _mock_exists: MagicMock,
        adapter: LintRunnerAdapter,
        tmp_path: Path,
    ) -> None:
        """Test validation with custom timeout from config."""
        mock_run.return_value = (0, "", "")
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={"lint_timeout": 30},
        )

        adapter.validate(tmp_path, context)

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1]["timeout_seconds"] == 30


class TestLintOutputParsing:
    """Tests for lint output parsing."""

    @pytest.fixture
    def adapter(self) -> LintRunnerAdapter:
        """Create adapter for parsing tests."""
        return LintRunnerAdapter()

    def test_parse_ruff_output(self, adapter: LintRunnerAdapter) -> None:
        """Test parsing ruff output."""
        stdout = """
        src/foo.py:10:5: E501 Line too long (100 > 88 characters)
        src/bar.py:20:1: F401 'os' imported but unused
        """
        errors = adapter.parse_lint_output(stdout, "", "python")

        assert len(errors) >= 2

    def test_parse_clippy_output(self, adapter: LintRunnerAdapter) -> None:
        """Test parsing clippy output."""
        stdout = """
        warning: unused variable: `x`
        error: mismatched types
        """
        errors = adapter.parse_lint_output(stdout, "", "rust")

        assert len(errors) >= 2
        assert any("warning" in e for e in errors)
        assert any("error" in e for e in errors)

    def test_parse_eslint_output(self, adapter: LintRunnerAdapter) -> None:
        """Test parsing eslint output."""
        stdout = """
        /src/foo.js
          1:10  error  'x' is defined but never used  no-unused-vars
          5:1   warning  Unexpected console statement  no-console
        """
        errors = adapter.parse_lint_output(stdout, "", "javascript")

        assert len(errors) >= 2

    def test_parse_empty_output(self, adapter: LintRunnerAdapter) -> None:
        """Test parsing empty output."""
        errors = adapter.parse_lint_output("", "", "python")

        assert len(errors) == 1
        assert "no output" in errors[0].lower()

    def test_parse_output_limit(self, adapter: LintRunnerAdapter) -> None:
        """Test that output is limited to 20 errors."""
        # Create 30 lines of lint errors
        stdout = "\n".join(
            [f"src/file{i}.py:{i}:1: E501 Error" for i in range(30)]
        )
        errors = adapter.parse_lint_output(stdout, "", "python")

        # Should be limited to 20
        assert len(errors) <= 20
