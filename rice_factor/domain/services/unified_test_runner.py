"""Unified test runner service for polyglot repositories.

This module provides the UnifiedTestRunner that orchestrates test execution
across multiple programming languages and aggregates results.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from rice_factor.domain.services.language_detector import Language, LanguageDetector


class TestStatus(Enum):
    """Status of test execution."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"


class OutputFormat(Enum):
    """Test output format."""

    JUNIT_XML = "junit_xml"
    JSON = "json"
    TAP = "tap"
    TEXT = "text"


@dataclass
class TestRunnerConfig:
    """Configuration for a language-specific test runner.

    Attributes:
        language: Target language.
        command: Test command (e.g., pytest, npm).
        args: Command arguments.
        env: Environment variables.
        timeout: Timeout in seconds.
        working_dir: Working directory.
        output_format: Expected output format.
    """

    language: Language
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    timeout: int = 300  # 5 minutes default
    working_dir: str | None = None
    output_format: OutputFormat = OutputFormat.TEXT

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language.value,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "timeout": self.timeout,
            "working_dir": self.working_dir,
            "output_format": self.output_format.value,
        }


@dataclass
class TestResult:
    """Result of a single test run.

    Attributes:
        language: Language of the test.
        status: Overall status.
        passed: Number of passed tests.
        failed: Number of failed tests.
        skipped: Number of skipped tests.
        errors: Number of errored tests.
        duration: Duration in seconds.
        output: Raw test output.
        error_message: Error message if failed.
    """

    language: Language
    status: TestStatus
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    output: str = ""
    error_message: str | None = None

    @property
    def total(self) -> int:
        """Total number of tests."""
        return self.passed + self.failed + self.skipped + self.errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language.value,
            "status": self.status.value,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "total": self.total,
            "duration": round(self.duration, 2),
            "error_message": self.error_message,
        }


@dataclass
class AggregatedResult:
    """Aggregated results from multiple test runners.

    Attributes:
        results: Individual test results by language.
        total_passed: Total passed tests.
        total_failed: Total failed tests.
        total_skipped: Total skipped tests.
        total_errors: Total errored tests.
        overall_status: Overall test status.
        duration: Total duration.
        executed_at: When tests were executed.
    """

    results: list[TestResult] = field(default_factory=list)
    total_passed: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    total_errors: int = 0
    overall_status: TestStatus = TestStatus.PASSED
    duration: float = 0.0
    executed_at: datetime | None = None

    @property
    def total_tests(self) -> int:
        """Total number of tests across all languages."""
        return (
            self.total_passed
            + self.total_failed
            + self.total_skipped
            + self.total_errors
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "results": [r.to_dict() for r in self.results],
            "total_passed": self.total_passed,
            "total_failed": self.total_failed,
            "total_skipped": self.total_skipped,
            "total_errors": self.total_errors,
            "total_tests": self.total_tests,
            "overall_status": self.overall_status.value,
            "duration": round(self.duration, 2),
            "executed_at": (
                self.executed_at.isoformat() if self.executed_at else None
            ),
        }


# Default test runner configurations
DEFAULT_RUNNERS: dict[Language, TestRunnerConfig] = {
    Language.PYTHON: TestRunnerConfig(
        language=Language.PYTHON,
        command="pytest",
        args=["-v", "--tb=short"],
        timeout=300,
    ),
    Language.JAVASCRIPT: TestRunnerConfig(
        language=Language.JAVASCRIPT,
        command="npm",
        args=["test"],
        timeout=120,
    ),
    Language.TYPESCRIPT: TestRunnerConfig(
        language=Language.TYPESCRIPT,
        command="npm",
        args=["test"],
        timeout=120,
    ),
    Language.JAVA: TestRunnerConfig(
        language=Language.JAVA,
        command="mvn",
        args=["test"],
        timeout=600,
    ),
    Language.KOTLIN: TestRunnerConfig(
        language=Language.KOTLIN,
        command="./gradlew",
        args=["test"],
        timeout=600,
    ),
    Language.GO: TestRunnerConfig(
        language=Language.GO,
        command="go",
        args=["test", "./..."],
        timeout=300,
    ),
    Language.RUST: TestRunnerConfig(
        language=Language.RUST,
        command="cargo",
        args=["test"],
        timeout=300,
    ),
    Language.RUBY: TestRunnerConfig(
        language=Language.RUBY,
        command="bundle",
        args=["exec", "rspec"],
        timeout=300,
    ),
    Language.PHP: TestRunnerConfig(
        language=Language.PHP,
        command="./vendor/bin/phpunit",
        args=[],
        timeout=300,
    ),
    Language.CSHARP: TestRunnerConfig(
        language=Language.CSHARP,
        command="dotnet",
        args=["test"],
        timeout=300,
    ),
}


@dataclass
class TestRunnerRegistry:
    """Registry of test runner configurations.

    Manages per-language test runner configurations with defaults.

    Attributes:
        configs: Dict of language to configuration.
    """

    configs: dict[Language, TestRunnerConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize with default runners."""
        if not self.configs:
            self.configs = dict(DEFAULT_RUNNERS)

    def get_config(self, language: Language) -> TestRunnerConfig | None:
        """Get configuration for a language.

        Args:
            language: Target language.

        Returns:
            TestRunnerConfig or None if not configured.
        """
        return self.configs.get(language)

    def set_config(self, config: TestRunnerConfig) -> None:
        """Set configuration for a language.

        Args:
            config: Test runner configuration.
        """
        self.configs[config.language] = config

    def remove_config(self, language: Language) -> None:
        """Remove configuration for a language.

        Args:
            language: Language to remove.
        """
        self.configs.pop(language, None)

    def get_configured_languages(self) -> list[Language]:
        """Get list of configured languages.

        Returns:
            List of languages with configurations.
        """
        return list(self.configs.keys())

    def load_from_yaml(self, yaml_content: dict[str, Any]) -> None:
        """Load configurations from YAML dict.

        Args:
            yaml_content: YAML content as dict.
        """
        runners = yaml_content.get("runners", {})

        for lang_name, config in runners.items():
            try:
                language = Language(lang_name)
            except ValueError:
                continue

            self.configs[language] = TestRunnerConfig(
                language=language,
                command=config.get("command", ""),
                args=config.get("args", []),
                env=config.get("env", {}),
                timeout=config.get("timeout", 300),
                working_dir=config.get("working_dir"),
                output_format=OutputFormat(
                    config.get("output_format", "text")
                ),
            )


@dataclass
class UnifiedTestRunner:
    """Service for running tests across multiple languages.

    Orchestrates test execution, handles failures gracefully,
    and aggregates results.

    Attributes:
        repo_root: Root directory of the repository.
        registry: Test runner registry.
        language_detector: Language detector instance.
        parallel: Whether to run tests in parallel.
    """

    repo_root: Path
    registry: TestRunnerRegistry | None = None
    language_detector: LanguageDetector | None = None
    parallel: bool = False
    _dry_run: bool = False  # For testing

    def __post_init__(self) -> None:
        """Initialize dependencies."""
        if self.registry is None:
            self.registry = TestRunnerRegistry()
        if self.language_detector is None:
            self.language_detector = LanguageDetector(repo_root=self.repo_root)

    def run_all(self) -> AggregatedResult:
        """Run tests for all detected languages.

        Returns:
            AggregatedResult with all test results.
        """
        detection = self.language_detector.detect()
        languages = [s.language for s in detection.languages]

        return self.run_for_languages(languages)

    def run_for_languages(
        self,
        languages: list[Language],
    ) -> AggregatedResult:
        """Run tests for specific languages.

        Args:
            languages: List of languages to test.

        Returns:
            AggregatedResult with test results.
        """
        results: list[TestResult] = []
        start_time = datetime.now(UTC)

        for language in languages:
            config = self.registry.get_config(language)
            if config is None:
                # No runner configured, skip
                results.append(
                    TestResult(
                        language=language,
                        status=TestStatus.SKIPPED,
                        error_message="No test runner configured",
                    )
                )
                continue

            result = self.run_single(config)
            results.append(result)

        return self._aggregate_results(results, start_time)

    def run_single(self, config: TestRunnerConfig) -> TestResult:
        """Run tests for a single language.

        Args:
            config: Test runner configuration.

        Returns:
            TestResult for this language.
        """
        start_time = datetime.now(UTC)

        if self._dry_run:
            # For testing, return mock result
            return TestResult(
                language=config.language,
                status=TestStatus.PASSED,
                passed=10,
                failed=0,
                duration=1.0,
                output="dry run",
            )

        try:
            # Build command
            cmd = [config.command] + config.args

            # Set working directory
            cwd = config.working_dir
            if cwd is None:
                cwd = str(self.repo_root)

            # Build environment
            env = dict(config.env)

            # Execute command
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=config.timeout,
                env=env if env else None,
            )

            duration = (datetime.now(UTC) - start_time).total_seconds()

            # Parse output to get counts
            passed, failed, skipped, errors = self._parse_output(
                result.stdout, config.output_format
            )

            # Determine status
            if result.returncode == 0:
                status = TestStatus.PASSED
            else:
                status = TestStatus.FAILED

            return TestResult(
                language=config.language,
                status=status,
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                duration=duration,
                output=result.stdout + result.stderr,
                error_message=result.stderr if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            duration = config.timeout
            return TestResult(
                language=config.language,
                status=TestStatus.TIMEOUT,
                duration=duration,
                error_message=f"Test execution timed out after {config.timeout}s",
            )

        except FileNotFoundError:
            return TestResult(
                language=config.language,
                status=TestStatus.ERROR,
                error_message=f"Command not found: {config.command}",
            )

        except Exception as e:
            return TestResult(
                language=config.language,
                status=TestStatus.ERROR,
                error_message=str(e),
            )

    def _parse_output(
        self,
        output: str,
        output_format: OutputFormat,
    ) -> tuple[int, int, int, int]:
        """Parse test output to extract counts.

        Args:
            output: Raw test output.
            output_format: Expected format.

        Returns:
            Tuple of (passed, failed, skipped, errors).
        """
        import re

        passed = failed = skipped = errors = 0

        if output_format == OutputFormat.TEXT:
            # Try common patterns

            # pytest: "X passed, Y failed"
            pytest_match = re.search(
                r"(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?",
                output,
            )
            if pytest_match:
                passed = int(pytest_match.group(1)) if pytest_match.group(1) else 0
                failed = int(pytest_match.group(2)) if pytest_match.group(2) else 0
                skipped = int(pytest_match.group(3)) if pytest_match.group(3) else 0
                return passed, failed, skipped, errors

            # Jest/npm: "Tests: X passed, Y failed"
            jest_match = re.search(
                r"Tests:\s*(?:(\d+) passed)?(?:,\s*(\d+) failed)?",
                output,
            )
            if jest_match:
                passed = int(jest_match.group(1)) if jest_match.group(1) else 0
                failed = int(jest_match.group(2)) if jest_match.group(2) else 0
                return passed, failed, skipped, errors

            # Go: "ok" or "FAIL"
            go_ok = len(re.findall(r"^ok\s+", output, re.MULTILINE))
            go_fail = len(re.findall(r"^FAIL\s+", output, re.MULTILINE))
            if go_ok or go_fail:
                passed = go_ok
                failed = go_fail
                return passed, failed, skipped, errors

            # Maven: "Tests run: X, Failures: Y"
            mvn_match = re.search(
                r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)",
                output,
            )
            if mvn_match:
                total = int(mvn_match.group(1))
                failed = int(mvn_match.group(2))
                errors = int(mvn_match.group(3))
                skipped = int(mvn_match.group(4))
                passed = total - failed - errors - skipped
                return passed, failed, skipped, errors

        return passed, failed, skipped, errors

    def _aggregate_results(
        self,
        results: list[TestResult],
        start_time: datetime,
    ) -> AggregatedResult:
        """Aggregate individual results.

        Args:
            results: List of TestResult objects.
            start_time: When execution started.

        Returns:
            AggregatedResult.
        """
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        total_skipped = sum(r.skipped for r in results)
        total_errors = sum(r.errors for r in results)
        duration = sum(r.duration for r in results)

        # Determine overall status
        if any(r.status in (TestStatus.FAILED, TestStatus.ERROR) for r in results):
            overall_status = TestStatus.FAILED
        elif all(r.status == TestStatus.SKIPPED for r in results):
            overall_status = TestStatus.SKIPPED
        else:
            overall_status = TestStatus.PASSED

        return AggregatedResult(
            results=results,
            total_passed=total_passed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            total_errors=total_errors,
            overall_status=overall_status,
            duration=duration,
            executed_at=start_time,
        )

    def generate_report(
        self,
        result: AggregatedResult,
        format_type: str = "text",
    ) -> str:
        """Generate a report from aggregated results.

        Args:
            result: Aggregated result.
            format_type: Output format (text, json, csv).

        Returns:
            Formatted report string.
        """
        import json

        if format_type == "json":
            return json.dumps(result.to_dict(), indent=2)

        elif format_type == "csv":
            lines = [
                "language,status,passed,failed,skipped,errors,duration"
            ]
            for r in result.results:
                lines.append(
                    f"{r.language.value},{r.status.value},{r.passed},{r.failed},{r.skipped},{r.errors},{r.duration}"
                )
            return "\n".join(lines)

        else:  # text
            lines = [
                "=" * 60,
                "UNIFIED TEST REPORT",
                "=" * 60,
                "",
            ]

            for r in result.results:
                status_symbol = (
                    "[PASS]"
                    if r.status == TestStatus.PASSED
                    else "[FAIL]"
                    if r.status == TestStatus.FAILED
                    else "[SKIP]"
                    if r.status == TestStatus.SKIPPED
                    else "[ERR]"
                )
                lines.append(
                    f"{status_symbol} {r.language.value}: "
                    f"{r.passed} passed, {r.failed} failed, {r.skipped} skipped "
                    f"({r.duration:.2f}s)"
                )
                if r.error_message:
                    lines.append(f"       Error: {r.error_message}")

            lines.extend(
                [
                    "",
                    "-" * 60,
                    f"TOTAL: {result.total_passed} passed, {result.total_failed} failed, "
                    f"{result.total_skipped} skipped, {result.total_errors} errors",
                    f"DURATION: {result.duration:.2f}s",
                    f"STATUS: {result.overall_status.value.upper()}",
                    "=" * 60,
                ]
            )

            return "\n".join(lines)
