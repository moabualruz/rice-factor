"""Tests for UnifiedTestRunner."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rice_factor.domain.services.language_detector import Language
from rice_factor.domain.services.unified_test_runner import (
    DEFAULT_RUNNERS,
    AggregatedResult,
    OutputFormat,
    TestResult,
    TestRunnerConfig,
    TestRunnerRegistry,
    TestStatus,
    UnifiedTestRunner,
)

if TYPE_CHECKING:
    pass


class TestTestStatus:
    """Tests for TestStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all statuses are defined."""
        assert TestStatus.PASSED
        assert TestStatus.FAILED
        assert TestStatus.SKIPPED
        assert TestStatus.ERROR
        assert TestStatus.TIMEOUT


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_all_formats_exist(self) -> None:
        """Test all formats are defined."""
        assert OutputFormat.JUNIT_XML
        assert OutputFormat.JSON
        assert OutputFormat.TAP
        assert OutputFormat.TEXT


class TestTestRunnerConfig:
    """Tests for TestRunnerConfig model."""

    def test_creation(self) -> None:
        """Test config creation."""
        config = TestRunnerConfig(
            language=Language.PYTHON,
            command="pytest",
            args=["-v"],
        )
        assert config.language == Language.PYTHON
        assert config.command == "pytest"
        assert config.timeout == 300  # default

    def test_with_all_options(self) -> None:
        """Test config with all options."""
        config = TestRunnerConfig(
            language=Language.JAVA,
            command="mvn",
            args=["test"],
            env={"JAVA_HOME": "/usr/lib/jvm"},
            timeout=600,
            working_dir="/app",
            output_format=OutputFormat.JUNIT_XML,
        )
        assert config.timeout == 600
        assert config.output_format == OutputFormat.JUNIT_XML

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        config = TestRunnerConfig(
            language=Language.GO,
            command="go",
            args=["test"],
        )
        d = config.to_dict()
        assert d["language"] == "go"
        assert d["command"] == "go"


class TestTestResult:
    """Tests for TestResult model."""

    def test_creation(self) -> None:
        """Test result creation."""
        result = TestResult(
            language=Language.PYTHON,
            status=TestStatus.PASSED,
            passed=10,
            failed=2,
        )
        assert result.passed == 10
        assert result.total == 12

    def test_total_property(self) -> None:
        """Test total property."""
        result = TestResult(
            language=Language.JAVASCRIPT,
            status=TestStatus.PASSED,
            passed=5,
            failed=2,
            skipped=1,
            errors=1,
        )
        assert result.total == 9

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        result = TestResult(
            language=Language.RUST,
            status=TestStatus.FAILED,
            passed=8,
            failed=2,
            duration=15.5,
        )
        d = result.to_dict()
        assert d["language"] == "rust"
        assert d["status"] == "failed"
        assert d["duration"] == 15.5


class TestAggregatedResult:
    """Tests for AggregatedResult model."""

    def test_creation(self) -> None:
        """Test result creation."""
        result = AggregatedResult()
        assert result.results == []
        assert result.total_tests == 0

    def test_total_tests_property(self) -> None:
        """Test total_tests property."""
        result = AggregatedResult(
            total_passed=10,
            total_failed=2,
            total_skipped=1,
            total_errors=0,
        )
        assert result.total_tests == 13

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        result = AggregatedResult(
            overall_status=TestStatus.PASSED,
            total_passed=100,
        )
        d = result.to_dict()
        assert d["overall_status"] == "passed"
        assert d["total_passed"] == 100


class TestDefaultRunners:
    """Tests for default runner configurations."""

    def test_python_runner_exists(self) -> None:
        """Test Python runner is configured."""
        assert Language.PYTHON in DEFAULT_RUNNERS
        config = DEFAULT_RUNNERS[Language.PYTHON]
        assert config.command == "pytest"

    def test_javascript_runner_exists(self) -> None:
        """Test JavaScript runner is configured."""
        assert Language.JAVASCRIPT in DEFAULT_RUNNERS
        config = DEFAULT_RUNNERS[Language.JAVASCRIPT]
        assert config.command == "npm"

    def test_java_runner_exists(self) -> None:
        """Test Java runner is configured."""
        assert Language.JAVA in DEFAULT_RUNNERS
        config = DEFAULT_RUNNERS[Language.JAVA]
        assert config.command == "mvn"

    def test_go_runner_exists(self) -> None:
        """Test Go runner is configured."""
        assert Language.GO in DEFAULT_RUNNERS
        config = DEFAULT_RUNNERS[Language.GO]
        assert config.command == "go"


class TestTestRunnerRegistry:
    """Tests for TestRunnerRegistry."""

    def test_creation_with_defaults(self) -> None:
        """Test registry creation with defaults."""
        registry = TestRunnerRegistry()
        assert Language.PYTHON in registry.configs
        assert Language.JAVASCRIPT in registry.configs

    def test_get_config(self) -> None:
        """Test getting configuration."""
        registry = TestRunnerRegistry()
        config = registry.get_config(Language.PYTHON)
        assert config is not None
        assert config.command == "pytest"

    def test_get_config_not_found(self) -> None:
        """Test getting non-existent configuration."""
        registry = TestRunnerRegistry()
        config = registry.get_config(Language.UNKNOWN)
        assert config is None

    def test_set_config(self) -> None:
        """Test setting configuration."""
        registry = TestRunnerRegistry()
        custom_config = TestRunnerConfig(
            language=Language.PYTHON,
            command="python",
            args=["-m", "unittest"],
        )
        registry.set_config(custom_config)

        config = registry.get_config(Language.PYTHON)
        assert config.command == "python"

    def test_remove_config(self) -> None:
        """Test removing configuration."""
        registry = TestRunnerRegistry()
        registry.remove_config(Language.PYTHON)
        assert registry.get_config(Language.PYTHON) is None

    def test_get_configured_languages(self) -> None:
        """Test getting configured languages."""
        registry = TestRunnerRegistry()
        languages = registry.get_configured_languages()
        assert Language.PYTHON in languages
        assert Language.JAVASCRIPT in languages

    def test_load_from_yaml(self) -> None:
        """Test loading from YAML dict."""
        registry = TestRunnerRegistry()
        yaml_content = {
            "runners": {
                "python": {
                    "command": "python",
                    "args": ["-m", "pytest"],
                    "timeout": 120,
                },
                "javascript": {
                    "command": "yarn",
                    "args": ["test"],
                },
            }
        }
        registry.load_from_yaml(yaml_content)

        py_config = registry.get_config(Language.PYTHON)
        assert py_config.command == "python"
        assert py_config.timeout == 120

        js_config = registry.get_config(Language.JAVASCRIPT)
        assert js_config.command == "yarn"


class TestUnifiedTestRunner:
    """Tests for UnifiedTestRunner."""

    def test_creation(self, tmp_path: Path) -> None:
        """Test runner creation."""
        runner = UnifiedTestRunner(repo_root=tmp_path)
        assert runner.repo_root == tmp_path
        assert runner.registry is not None

    def test_run_single_dry_run(self, tmp_path: Path) -> None:
        """Test running single test in dry run mode."""
        runner = UnifiedTestRunner(repo_root=tmp_path)
        runner._dry_run = True

        config = TestRunnerConfig(
            language=Language.PYTHON,
            command="pytest",
        )
        result = runner.run_single(config)

        assert result.status == TestStatus.PASSED
        assert result.passed == 10

    def test_run_for_languages_dry_run(self, tmp_path: Path) -> None:
        """Test running tests for multiple languages."""
        runner = UnifiedTestRunner(repo_root=tmp_path)
        runner._dry_run = True

        result = runner.run_for_languages(
            [Language.PYTHON, Language.JAVASCRIPT]
        )

        assert len(result.results) == 2
        assert result.overall_status == TestStatus.PASSED

    def test_run_for_unconfigured_language(self, tmp_path: Path) -> None:
        """Test running tests for unconfigured language."""
        runner = UnifiedTestRunner(repo_root=tmp_path)
        runner._dry_run = True

        # Remove config for a language
        runner.registry.remove_config(Language.PYTHON)

        result = runner.run_for_languages([Language.PYTHON])

        assert len(result.results) == 1
        assert result.results[0].status == TestStatus.SKIPPED

    def test_run_all_dry_run(self, tmp_path: Path) -> None:
        """Test running all tests."""
        runner = UnifiedTestRunner(repo_root=tmp_path)
        runner._dry_run = True

        # Create Python file so it gets detected
        (tmp_path / "test.py").write_text("def test_x(): pass\n")

        result = runner.run_all()

        assert result.executed_at is not None

    def test_aggregate_results(self, tmp_path: Path) -> None:
        """Test result aggregation."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        from datetime import UTC, datetime

        results = [
            TestResult(
                language=Language.PYTHON,
                status=TestStatus.PASSED,
                passed=10,
                failed=0,
                duration=5.0,
            ),
            TestResult(
                language=Language.JAVASCRIPT,
                status=TestStatus.FAILED,
                passed=8,
                failed=2,
                duration=3.0,
            ),
        ]

        aggregated = runner._aggregate_results(results, datetime.now(UTC))

        assert aggregated.total_passed == 18
        assert aggregated.total_failed == 2
        assert aggregated.overall_status == TestStatus.FAILED
        assert aggregated.duration == 8.0

    def test_aggregate_all_skipped(self, tmp_path: Path) -> None:
        """Test aggregation when all tests are skipped."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        from datetime import UTC, datetime

        results = [
            TestResult(
                language=Language.PYTHON,
                status=TestStatus.SKIPPED,
            ),
        ]

        aggregated = runner._aggregate_results(results, datetime.now(UTC))

        assert aggregated.overall_status == TestStatus.SKIPPED

    def test_parse_output_pytest(self, tmp_path: Path) -> None:
        """Test parsing pytest output."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        output = "collected 12 items\n... 10 passed, 2 failed"
        passed, failed, skipped, errors = runner._parse_output(
            output, OutputFormat.TEXT
        )

        assert passed == 10
        assert failed == 2

    def test_parse_output_pytest_with_skipped(self, tmp_path: Path) -> None:
        """Test parsing pytest output with skipped."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        output = "10 passed, 2 failed, 3 skipped"
        passed, failed, skipped, errors = runner._parse_output(
            output, OutputFormat.TEXT
        )

        assert passed == 10
        assert failed == 2
        assert skipped == 3

    def test_parse_output_maven(self, tmp_path: Path) -> None:
        """Test parsing Maven output."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        output = "Tests run: 15, Failures: 2, Errors: 1, Skipped: 2"
        passed, failed, skipped, errors = runner._parse_output(
            output, OutputFormat.TEXT
        )

        assert passed == 10  # 15 - 2 - 1 - 2
        assert failed == 2
        assert errors == 1
        assert skipped == 2

    def test_parse_output_go(self, tmp_path: Path) -> None:
        """Test parsing Go test output."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        output = "ok \t pkg/foo 1.5s\nok \t pkg/bar 2.0s\nFAIL\t pkg/baz 0.1s"
        passed, failed, skipped, errors = runner._parse_output(
            output, OutputFormat.TEXT
        )

        assert passed == 2
        assert failed == 1

    def test_generate_report_text(self, tmp_path: Path) -> None:
        """Test generating text report."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        aggregated = AggregatedResult(
            results=[
                TestResult(
                    language=Language.PYTHON,
                    status=TestStatus.PASSED,
                    passed=10,
                    failed=0,
                    duration=5.0,
                )
            ],
            total_passed=10,
            overall_status=TestStatus.PASSED,
            duration=5.0,
        )

        report = runner.generate_report(aggregated, "text")

        assert "UNIFIED TEST REPORT" in report
        assert "python" in report
        assert "[PASS]" in report

    def test_generate_report_json(self, tmp_path: Path) -> None:
        """Test generating JSON report."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        import json

        aggregated = AggregatedResult(
            total_passed=10,
            overall_status=TestStatus.PASSED,
        )

        report = runner.generate_report(aggregated, "json")
        data = json.loads(report)

        assert data["total_passed"] == 10
        assert data["overall_status"] == "passed"

    def test_generate_report_csv(self, tmp_path: Path) -> None:
        """Test generating CSV report."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        aggregated = AggregatedResult(
            results=[
                TestResult(
                    language=Language.PYTHON,
                    status=TestStatus.PASSED,
                    passed=10,
                    failed=0,
                    duration=5.0,
                )
            ],
        )

        report = runner.generate_report(aggregated, "csv")

        assert "language,status,passed,failed" in report
        assert "python,passed,10,0" in report

    def test_generate_report_with_error(self, tmp_path: Path) -> None:
        """Test generating report with error message."""
        runner = UnifiedTestRunner(repo_root=tmp_path)

        aggregated = AggregatedResult(
            results=[
                TestResult(
                    language=Language.PYTHON,
                    status=TestStatus.ERROR,
                    error_message="Command not found",
                )
            ],
            overall_status=TestStatus.FAILED,
        )

        report = runner.generate_report(aggregated, "text")

        assert "[ERR]" in report
        assert "Command not found" in report
