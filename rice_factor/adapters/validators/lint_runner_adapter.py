"""Lint runner adapter for executing native lint commands.

This adapter implements the ValidationRunnerPort protocol to run
language-specific lint commands (ruff, clippy, eslint, etc.)
and return validation results.

Note: Missing linter returns status="passed" (lint is optional).
"""

import shutil
import subprocess
import time
from pathlib import Path
from typing import ClassVar

from rice_factor.domain.artifacts.validation_types import (
    ValidationContext,
    ValidationResult,
)
from rice_factor.domain.failures.validation_errors import (
    ValidationTimeoutError,
)


class LintRunnerAdapter:
    """Adapter for running native lint commands.

    Executes language-specific lint commands and captures results.
    Implements the ValidationRunnerPort protocol.

    Unlike TestRunnerAdapter, missing linters return a passing result
    since linting is considered optional.

    Attributes:
        LINT_COMMANDS: Mapping of language to lint command.
        DEFAULT_TIMEOUT: Default timeout in seconds (2 minutes).
    """

    LINT_COMMANDS: ClassVar[dict[str, list[str]]] = {
        "python": ["ruff", "check", "."],
        "rust": ["cargo", "clippy", "--", "-D", "warnings"],
        "go": ["golint", "./..."],
        "javascript": ["eslint", "."],
        "typescript": ["eslint", "."],
    }

    DEFAULT_TIMEOUT: ClassVar[int] = 120  # 2 minutes

    @property
    def name(self) -> str:
        """Get the validator name.

        Returns:
            The identifier "lint_runner".
        """
        return "lint_runner"

    @property
    def supported_languages(self) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language identifiers.
        """
        return list(self.LINT_COMMANDS.keys())

    def validate(
        self,
        target: Path,
        context: ValidationContext,
    ) -> ValidationResult:
        """Run linter and return validation result.

        Args:
            target: Path to the repository root to lint.
            context: Validation context with language and config.

        Returns:
            ValidationResult with lint status and any errors.
            Returns passed if linter is not available (lint is optional).

        Raises:
            ValidationTimeoutError: If linting exceeds the timeout.
        """
        start_time = time.time()
        language = context.language.lower()

        # Get the lint command for this language
        command = self.get_lint_command(language)
        if command is None:
            # No linter for this language - that's OK, lint is optional
            return ValidationResult.passed_result(
                target=str(target),
                validator=self.name,
                duration_ms=0,
            )

        # Check if command exists - if not, lint passes (optional)
        if not self._command_exists(command[0]):
            return ValidationResult.passed_result(
                target=str(target),
                validator=self.name,
                duration_ms=0,
            )

        # Get timeout from config or use default
        timeout = context.get_config("lint_timeout", self.DEFAULT_TIMEOUT)

        # Run the lint command
        try:
            exit_code, stdout, stderr = self._run_command(
                command=command,
                cwd=target,
                timeout_seconds=timeout,
            )
        except ValidationTimeoutError:
            raise

        duration_ms = int((time.time() - start_time) * 1000)

        # Determine pass/fail based on exit code
        if exit_code == 0:
            return ValidationResult.passed_result(
                target=str(target),
                validator=self.name,
                duration_ms=duration_ms,
            )
        else:
            errors = self.parse_lint_output(stdout, stderr, language)
            return ValidationResult.failed_result(
                target=str(target),
                errors=errors,
                validator=self.name,
                duration_ms=duration_ms,
            )

    def get_lint_command(self, language: str) -> list[str] | None:
        """Get the lint command for a language.

        Args:
            language: The programming language.

        Returns:
            The lint command as a list, or None if not supported.
        """
        return self.LINT_COMMANDS.get(language.lower())

    def parse_lint_output(
        self,
        stdout: str,
        stderr: str,
        language: str,
    ) -> list[str]:
        """Parse lint output for error messages.

        Args:
            stdout: Standard output from lint command.
            stderr: Standard error from lint command.
            language: The programming language (for language-specific parsing).

        Returns:
            List of error messages extracted from output.
        """
        errors: list[str] = []

        # Combine output
        output = f"{stdout}\n{stderr}".strip()

        if not output:
            errors.append("Linting failed with no output")
            return errors

        # Language-specific parsing
        if language == "python":
            errors.extend(self._parse_ruff_output(stdout, stderr))
        elif language == "rust":
            errors.extend(self._parse_clippy_output(stdout, stderr))
        elif language in ("javascript", "typescript"):
            errors.extend(self._parse_eslint_output(stdout, stderr))
        else:
            # Generic parsing
            lines = output.split("\n")
            relevant_lines = [line for line in lines if line.strip()][:20]
            if relevant_lines:
                errors.extend(relevant_lines)
            else:
                errors.append("Linting failed")

        return errors

    def _parse_ruff_output(self, stdout: str, stderr: str) -> list[str]:
        """Parse ruff output for lint violations.

        Args:
            stdout: Standard output from ruff.
            stderr: Standard error from ruff.

        Returns:
            List of extracted lint violations.
        """
        errors: list[str] = []
        output = stdout + "\n" + stderr

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Ruff outputs lines like: path/file.py:10:5: E501 Line too long
            if ":" in line and any(c.isdigit() for c in line):
                errors.append(line)

        # Limit to first 20 errors
        return errors[:20] if errors else ["Ruff check failed"]

    def _parse_clippy_output(self, stdout: str, stderr: str) -> list[str]:
        """Parse clippy output for lint violations.

        Args:
            stdout: Standard output from clippy.
            stderr: Standard error from clippy.

        Returns:
            List of extracted lint violations.
        """
        errors: list[str] = []
        output = stdout + "\n" + stderr

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("warning:") or line.startswith("error:"):
                errors.append(line)

        return errors[:20] if errors else ["Clippy check failed"]

    def _parse_eslint_output(self, stdout: str, stderr: str) -> list[str]:
        """Parse eslint output for lint violations.

        Args:
            stdout: Standard output from eslint.
            stderr: Standard error from eslint.

        Returns:
            List of extracted lint violations.
        """
        errors: list[str] = []
        output = stdout + "\n" + stderr

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            # ESLint outputs lines with file paths and line numbers
            if "error" in line.lower() or "warning" in line.lower() or (line and line[0].isdigit() and ":" in line):
                errors.append(line)

        return errors[:20] if errors else ["ESLint check failed"]

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH.

        Args:
            command: The command to check.

        Returns:
            True if command exists, False otherwise.
        """
        return shutil.which(command) is not None

    def _run_command(
        self,
        command: list[str],
        cwd: Path,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        """Execute a command and return results.

        Args:
            command: The command to run as a list.
            cwd: Working directory for the command.
            timeout_seconds: Timeout in seconds.

        Returns:
            Tuple of (exit_code, stdout, stderr).

        Raises:
            ValidationTimeoutError: If command times out.
        """
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            return (result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired as e:
            raise ValidationTimeoutError(
                command=" ".join(command),
                timeout_seconds=timeout_seconds,
            ) from e
