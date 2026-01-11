"""Test runner adapter for executing native test commands.

This adapter implements the ValidationRunnerPort protocol to run
language-specific test commands (pytest, cargo test, go test, etc.)
and return validation results.
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
    CommandNotFoundError,
    LanguageNotSupportedError,
    ValidationTimeoutError,
)


class TestRunnerAdapter:
    """Adapter for running native test commands.

    Executes language-specific test commands and captures results.
    Implements the ValidationRunnerPort protocol.

    Attributes:
        TEST_COMMANDS: Mapping of language to test command.
        DEFAULT_TIMEOUT: Default timeout in seconds (5 minutes).
    """

    TEST_COMMANDS: ClassVar[dict[str, list[str]]] = {
        "python": ["pytest"],
        "rust": ["cargo", "test"],
        "go": ["go", "test", "./..."],
        "javascript": ["npm", "test"],
        "typescript": ["npm", "test"],
        "java": ["mvn", "test"],
    }

    DEFAULT_TIMEOUT: ClassVar[int] = 300  # 5 minutes

    @property
    def name(self) -> str:
        """Get the validator name.

        Returns:
            The identifier "test_runner".
        """
        return "test_runner"

    @property
    def supported_languages(self) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language identifiers.
        """
        return list(self.TEST_COMMANDS.keys())

    def validate(
        self,
        target: Path,
        context: ValidationContext,
    ) -> ValidationResult:
        """Run tests and return validation result.

        Args:
            target: Path to the repository root to test.
            context: Validation context with language and config.

        Returns:
            ValidationResult with test status and any errors.

        Raises:
            LanguageNotSupportedError: If the language has no test command.
            CommandNotFoundError: If the test command is not installed.
            ValidationTimeoutError: If tests exceed the timeout.
        """
        start_time = time.time()
        language = context.language.lower()

        # Get the test command for this language
        command = self.get_test_command(language)
        if command is None:
            raise LanguageNotSupportedError(
                language=language,
                supported_languages=self.supported_languages,
            )

        # Check if command exists
        if not self._command_exists(command[0]):
            raise CommandNotFoundError(command=command[0], validator=self.name)

        # Get timeout from config or use default
        timeout = context.get_config("test_timeout", self.DEFAULT_TIMEOUT)

        # Run the test command
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
            errors = self.parse_test_output(stdout, stderr, language)
            return ValidationResult.failed_result(
                target=str(target),
                errors=errors,
                validator=self.name,
                duration_ms=duration_ms,
            )

    def get_test_command(self, language: str) -> list[str] | None:
        """Get the test command for a language.

        Args:
            language: The programming language.

        Returns:
            The test command as a list, or None if not supported.
        """
        return self.TEST_COMMANDS.get(language.lower())

    def parse_test_output(
        self,
        stdout: str,
        stderr: str,
        language: str,
    ) -> list[str]:
        """Parse test output for error messages.

        Args:
            stdout: Standard output from test command.
            stderr: Standard error from test command.
            language: The programming language (for language-specific parsing).

        Returns:
            List of error messages extracted from output.
        """
        errors: list[str] = []

        # Combine output
        output = f"{stdout}\n{stderr}".strip()

        if not output:
            errors.append("Tests failed with no output")
            return errors

        # Language-specific parsing
        if language == "python":
            errors.extend(self._parse_pytest_output(stdout, stderr))
        elif language == "rust":
            errors.extend(self._parse_cargo_test_output(stdout, stderr))
        elif language == "go":
            errors.extend(self._parse_go_test_output(stdout, stderr))
        else:
            # Generic parsing - take last few lines of output
            lines = output.split("\n")
            # Filter to non-empty lines and take last 10
            relevant_lines = [line for line in lines if line.strip()][-10:]
            if relevant_lines:
                errors.append("\n".join(relevant_lines))
            else:
                errors.append("Tests failed")

        return errors

    def _parse_pytest_output(self, stdout: str, stderr: str) -> list[str]:
        """Parse pytest output for failures.

        Args:
            stdout: Standard output from pytest.
            stderr: Standard error from pytest.

        Returns:
            List of extracted error messages.
        """
        errors: list[str] = []
        output = stdout + "\n" + stderr

        # Look for FAILED lines
        for line in output.split("\n"):
            if "FAILED" in line or "ERROR" in line:
                errors.append(line.strip())

        # Look for summary line
        for line in output.split("\n"):
            if "failed" in line.lower() and ("passed" in line.lower() or "error" in line.lower()):
                errors.append(line.strip())
                break

        if not errors:
            # Fall back to last few lines
            lines = [line for line in output.split("\n") if line.strip()][-5:]
            if lines:
                errors.append("\n".join(lines))

        return errors

    def _parse_cargo_test_output(self, stdout: str, stderr: str) -> list[str]:
        """Parse cargo test output for failures.

        Args:
            stdout: Standard output from cargo test.
            stderr: Standard error from cargo test.

        Returns:
            List of extracted error messages.
        """
        errors: list[str] = []
        output = stdout + "\n" + stderr

        # Look for test failure lines
        in_failure_section = False
        for line in output.split("\n"):
            if "failures:" in line.lower():
                in_failure_section = True
                continue
            if in_failure_section:
                if line.strip() and not line.startswith("note:"):
                    errors.append(line.strip())
                if line.startswith("test result:"):
                    break

        # Look for FAILED lines
        if not errors:
            for line in output.split("\n"):
                if "FAILED" in line:
                    errors.append(line.strip())

        return errors if errors else ["Cargo tests failed"]

    def _parse_go_test_output(self, stdout: str, stderr: str) -> list[str]:
        """Parse go test output for failures.

        Args:
            stdout: Standard output from go test.
            stderr: Standard error from go test.

        Returns:
            List of extracted error messages.
        """
        errors: list[str] = []
        output = stdout + "\n" + stderr

        # Look for FAIL lines
        for line in output.split("\n"):
            if (line.startswith("---") and "FAIL" in line) or line.startswith("FAIL"):
                errors.append(line.strip())

        return errors if errors else ["Go tests failed"]

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
