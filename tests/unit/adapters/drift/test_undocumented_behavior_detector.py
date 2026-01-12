"""Unit tests for UndocumentedBehaviorDetector adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from rice_factor.adapters.drift.undocumented_behavior_detector import (
    AnalysisReport,
    BehaviorCategory,
    DetectedBehavior,
    DetectionConfidence,
    RequirementMatch,
    UndocumentedBehaviorDetector,
)


class TestDetectedBehavior:
    """Tests for DetectedBehavior dataclass."""

    def test_creation(self) -> None:
        """DetectedBehavior should be creatable."""
        behavior = DetectedBehavior(
            test_file="tests/test_main.py",
            test_name="test_edge_case_empty_input",
            line_number=42,
            description="Edge case test: empty input",
            category=BehaviorCategory.EDGE_CASE,
            confidence=DetectionConfidence.MEDIUM,
        )
        assert behavior.test_name == "test_edge_case_empty_input"
        assert behavior.category == BehaviorCategory.EDGE_CASE

    def test_with_suggestion(self) -> None:
        """DetectedBehavior should accept suggestion."""
        behavior = DetectedBehavior(
            test_file="tests/test_api.py",
            test_name="test_timeout_handling",
            line_number=100,
            description="Error handling test: timeout handling",
            category=BehaviorCategory.ERROR_HANDLING,
            confidence=DetectionConfidence.HIGH,
            suggested_requirement="The system shall handle timeout gracefully",
        )
        assert behavior.suggested_requirement is not None


class TestRequirementMatch:
    """Tests for RequirementMatch dataclass."""

    def test_creation(self) -> None:
        """RequirementMatch should be creatable."""
        match = RequirementMatch(
            test_name="test_fr_001_user_login",
            requirement_id="FR-001",
            requirement_text="User shall be able to login",
            match_score=1.0,
        )
        assert match.requirement_id == "FR-001"
        assert match.match_score == 1.0


class TestAnalysisReport:
    """Tests for AnalysisReport dataclass."""

    def test_creation(self) -> None:
        """AnalysisReport should be creatable."""
        report = AnalysisReport(
            analyzed_at=datetime.now(UTC),
            repo_root="/test/repo",
            test_files_scanned=10,
            requirements_loaded=50,
            total_tests=100,
            matched_tests=80,
            undocumented_behaviors=[],
            matches=[],
        )
        assert report.coverage_percentage == 80.0
        assert report.undocumented_count == 0

    def test_coverage_percentage(self) -> None:
        """should calculate coverage percentage."""
        report = AnalysisReport(
            analyzed_at=datetime.now(UTC),
            repo_root="/test/repo",
            test_files_scanned=5,
            requirements_loaded=20,
            total_tests=50,
            matched_tests=25,
            undocumented_behaviors=[],
            matches=[],
        )
        assert report.coverage_percentage == 50.0

    def test_coverage_empty(self) -> None:
        """should handle zero tests."""
        report = AnalysisReport(
            analyzed_at=datetime.now(UTC),
            repo_root="/test/repo",
            test_files_scanned=0,
            requirements_loaded=0,
            total_tests=0,
            matched_tests=0,
            undocumented_behaviors=[],
            matches=[],
        )
        assert report.coverage_percentage == 100.0

    def test_to_dict(self) -> None:
        """should serialize to dict."""
        behavior = DetectedBehavior(
            test_file="test.py",
            test_name="test_edge",
            line_number=1,
            description="Test",
            category=BehaviorCategory.EDGE_CASE,
            confidence=DetectionConfidence.HIGH,
        )
        report = AnalysisReport(
            analyzed_at=datetime.now(UTC),
            repo_root="/test",
            test_files_scanned=1,
            requirements_loaded=10,
            total_tests=5,
            matched_tests=3,
            undocumented_behaviors=[behavior],
            matches=[],
        )
        result = report.to_dict()
        assert result["total_tests"] == 5
        assert result["undocumented_count"] == 1
        assert result["by_category"]["edge_case"] == 1


class TestUndocumentedBehaviorDetector:
    """Tests for UndocumentedBehaviorDetector adapter."""

    def test_creation(self, tmp_path: Path) -> None:
        """UndocumentedBehaviorDetector should be creatable."""
        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        assert detector.repo_root == tmp_path

    def test_analyze_empty_repo(self, tmp_path: Path) -> None:
        """should handle empty repository."""
        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()
        assert report.test_files_scanned == 0
        assert report.total_tests == 0

    def test_analyze_with_requirements(self, tmp_path: Path) -> None:
        """should load requirements and match tests."""
        # Create requirements file
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text("""
# Requirements

## FR-001: User Authentication
- Users shall be able to login with username and password
- Users shall be able to logout

## FR-002: Data Export
- Users shall be able to export data to CSV
""")

        # Create test file with matching test
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_auth.py").write_text("""
def test_fr_001_user_login():
    \"\"\"Test that users can login.\"\"\"
    pass

def test_authentication_flow():
    \"\"\"Test the authentication flow.\"\"\"
    pass

def test_edge_case_empty_password():
    \"\"\"Test empty password handling.\"\"\"
    pass
""")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        assert report.test_files_scanned == 1
        assert report.total_tests == 3
        assert report.matched_tests >= 1  # At least FR-001 match

    def test_categorize_edge_case(self, tmp_path: Path) -> None:
        """should categorize edge case tests."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_edges.py").write_text("""
def test_empty_input():
    pass

def test_boundary_value():
    pass

def test_null_handling():
    pass
""")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        edge_cases = [
            b for b in report.undocumented_behaviors
            if b.category == BehaviorCategory.EDGE_CASE
        ]
        assert len(edge_cases) >= 2

    def test_categorize_error_handling(self, tmp_path: Path) -> None:
        """should categorize error handling tests."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_errors.py").write_text("""
def test_exception_handling():
    pass

def test_invalid_input_error():
    pass

def test_timeout_retry():
    pass
""")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        error_handling = [
            b for b in report.undocumented_behaviors
            if b.category == BehaviorCategory.ERROR_HANDLING
        ]
        assert len(error_handling) >= 2

    def test_match_requirement_id_in_name(self, tmp_path: Path) -> None:
        """should match requirement ID in test name."""
        # Create requirements
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text("""
## REQ-123: Some Requirement
Description here.
""")

        # Create test with requirement ID in name
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_reqs.py").write_text("""
def test_req_123_implementation():
    pass
""")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        assert report.matched_tests >= 1
        assert any(m.requirement_id == "REQ-123" for m in report.matches)

    def test_match_requirement_id_in_docstring(self, tmp_path: Path) -> None:
        """should match requirement ID in docstring."""
        # Create requirements
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text("""
## US-456: User Story
Some user story.
""")

        # Create test with requirement ID in docstring
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_user.py").write_text('''
def test_user_feature():
    """Test for US-456."""
    pass
''')

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        assert report.matched_tests >= 1
        assert any(m.requirement_id == "US-456" for m in report.matches)

    def test_suggest_requirement(self, tmp_path: Path) -> None:
        """should generate requirement suggestions."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_features.py").write_text("""
def test_edge_case_empty_list():
    pass
""")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        assert len(report.undocumented_behaviors) >= 1
        behavior = report.undocumented_behaviors[0]
        assert behavior.suggested_requirement is not None
        assert "handle" in behavior.suggested_requirement.lower()

    def test_confidence_levels(self, tmp_path: Path) -> None:
        """should assign appropriate confidence levels."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_mixed.py").write_text('''
def test_unknown_behavior():
    pass

def test_regression_bug_fix():
    """This is a detailed docstring explaining the regression test.
    It has multiple lines and provides context about why this test exists.
    """
    pass
''')

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        # Unknown category should have low confidence
        unknown = [
            b for b in report.undocumented_behaviors
            if b.category == BehaviorCategory.UNKNOWN
        ]
        if unknown:
            assert unknown[0].confidence == DetectionConfidence.LOW

    def test_get_high_confidence_behaviors(self, tmp_path: Path) -> None:
        """should filter high-confidence behaviors."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_api.py").write_text("""
def test_api_integration():
    pass

def test_some_unknown_thing():
    pass
""")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        high_conf = detector.get_high_confidence_behaviors()

        # All returned should be high confidence
        for behavior in high_conf:
            assert behavior.confidence == DetectionConfidence.HIGH

    def test_get_behaviors_by_category(self, tmp_path: Path) -> None:
        """should filter behaviors by category."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_perf.py").write_text("""
def test_performance_benchmark():
    pass

def test_cache_speed():
    pass

def test_empty_input():
    pass
""")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        perf_behaviors = detector.get_behaviors_by_category(BehaviorCategory.PERFORMANCE)

        assert len(perf_behaviors) >= 1
        for behavior in perf_behaviors:
            assert behavior.category == BehaviorCategory.PERFORMANCE

    def test_handle_syntax_error_in_test(self, tmp_path: Path) -> None:
        """should handle files with syntax errors."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_broken.py").write_text("""
def test_broken(
    # This is invalid Python syntax
""")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        # Should not crash, just skip the file
        assert report.test_files_scanned == 1
        assert report.total_tests == 0

    def test_multiple_test_patterns(self, tmp_path: Path) -> None:
        """should find tests in different directories."""
        # Create tests in 'tests/' directory
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_a.py").write_text("def test_a(): pass")

        # Create tests in 'test/' directory
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test_b.py").write_text("def test_b(): pass")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        assert report.test_files_scanned == 2
        assert report.total_tests == 2

    def test_keyword_matching(self, tmp_path: Path) -> None:
        """should match tests to requirements by keywords."""
        # Create requirements with keywords
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text("""
# Requirements

- User authentication with password
- Data export functionality
- Dashboard visualization
""")

        # Create test with matching keywords
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_auth.py").write_text("""
def test_password_validation():
    \"\"\"Test password validation.\"\"\"
    pass

def test_unrelated_feature():
    pass
""")

        detector = UndocumentedBehaviorDetector(repo_root=tmp_path)
        report = detector.analyze()

        # Password test should match due to keyword
        assert report.matched_tests >= 1
