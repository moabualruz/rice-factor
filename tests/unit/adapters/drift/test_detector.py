"""Unit tests for DriftDetectorAdapter."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from rice_factor.adapters.drift.detector import DriftDetectorAdapter
from rice_factor.domain.drift.models import (
    DriftConfig,
    DriftSeverity,
    DriftSignalType,
)


def _create_implementation_plan(
    artifacts_dir: Path,
    artifact_id: str,
    target: str,
) -> Path:
    """Create an ImplementationPlan artifact file."""
    impl_plans_dir = artifacts_dir / "implementation_plans"
    impl_plans_dir.mkdir(parents=True, exist_ok=True)

    artifact_data = {
        "id": artifact_id,
        "artifact_type": "ImplementationPlan",
        "artifact_version": "1.0",
        "status": "approved",
        "created_by": "llm",
        "created_at": "2026-01-11T10:00:00Z",
        "payload": {
            "target": target,
            "description": "Test implementation plan",
            "approach": "TDD",
            "steps": [],
        },
    }

    path = impl_plans_dir / f"{artifact_id}.json"
    path.write_text(json.dumps(artifact_data, indent=2))
    return path


def _create_refactor_plan(
    artifacts_dir: Path,
    artifact_id: str,
    from_path: str,
    to_path: str,
) -> Path:
    """Create a RefactorPlan artifact file."""
    refactor_plans_dir = artifacts_dir / "refactor_plans"
    refactor_plans_dir.mkdir(parents=True, exist_ok=True)

    artifact_data = {
        "id": artifact_id,
        "artifact_type": "RefactorPlan",
        "artifact_version": "1.0",
        "status": "approved",
        "created_by": "llm",
        "created_at": "2026-01-11T10:00:00Z",
        "payload": {
            "from_path": from_path,
            "to_path": to_path,
            "scope": "file_move",
            "steps": [],
        },
    }

    path = refactor_plans_dir / f"{artifact_id}.json"
    path.write_text(json.dumps(artifact_data, indent=2))
    return path


def _create_audit_entry(
    executor: str,
    files_affected: list[str],
    days_ago: int = 0,
) -> str:
    """Create an audit log entry JSON string."""
    timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago)
    entry = {
        "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "executor": executor,
        "artifact": "test.json",
        "status": "success",
        "mode": "apply",
        "files_affected": files_affected,
        "duration_ms": 100,
    }
    return json.dumps(entry)


class TestDriftDetectorAdapter:
    """Tests for DriftDetectorAdapter."""

    def test_detects_orphan_code(self, tmp_path: Path) -> None:
        """Should detect code files not covered by any plan."""
        # Create code files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")
        (src_dir / "orphan.py").write_text("print('orphan')")

        # Create an implementation plan for main.py only
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(artifacts_dir, "plan-1", "src/main.py")

        config = DriftConfig(source_dirs=["src"])
        detector = DriftDetectorAdapter(config=config)

        signals = detector.detect_orphan_code(src_dir, tmp_path)

        assert len(signals) == 1
        assert signals[0].signal_type == DriftSignalType.ORPHAN_CODE
        assert "orphan.py" in signals[0].path
        assert signals[0].severity == DriftSeverity.MEDIUM

    def test_no_orphan_code_when_all_covered(self, tmp_path: Path) -> None:
        """Should not report orphans when all code is covered."""
        # Create code file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")

        # Create implementation plan
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(artifacts_dir, "plan-1", "src/main.py")

        config = DriftConfig(source_dirs=["src"])
        detector = DriftDetectorAdapter(config=config)

        signals = detector.detect_orphan_code(src_dir, tmp_path)

        assert len(signals) == 0

    def test_ignores_test_files(self, tmp_path: Path) -> None:
        """Should ignore test files when scanning for orphans."""
        # Create code and test files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")
        (src_dir / "test_main.py").write_text("def test(): pass")

        # Create implementation plan for main.py
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(artifacts_dir, "plan-1", "src/main.py")

        config = DriftConfig(source_dirs=["src"])
        detector = DriftDetectorAdapter(config=config)

        signals = detector.detect_orphan_code(src_dir, tmp_path)

        # test_main.py should be ignored
        assert len(signals) == 0


class TestOrphanPlanDetection:
    """Tests for orphan plan detection."""

    def test_detects_orphan_plan(self, tmp_path: Path) -> None:
        """Should detect plans targeting non-existent files."""
        # Create implementation plan for non-existent file
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(
            artifacts_dir, "orphan-plan", "src/nonexistent.py"
        )

        detector = DriftDetectorAdapter()

        signals = detector.detect_orphan_plans(tmp_path)

        assert len(signals) == 1
        assert signals[0].signal_type == DriftSignalType.ORPHAN_PLAN
        assert signals[0].severity == DriftSeverity.HIGH
        assert "nonexistent.py" in signals[0].path
        assert signals[0].related_artifact_id == "orphan-plan"

    def test_no_orphan_plan_when_target_exists(self, tmp_path: Path) -> None:
        """Should not report orphan when target file exists."""
        # Create target file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")

        # Create implementation plan
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(artifacts_dir, "plan-1", "src/main.py")

        detector = DriftDetectorAdapter()

        signals = detector.detect_orphan_plans(tmp_path)

        assert len(signals) == 0

    def test_detects_orphan_refactor_plan(self, tmp_path: Path) -> None:
        """Should detect refactor plans with missing files."""
        # Create refactor plan for non-existent files
        artifacts_dir = tmp_path / "artifacts"
        _create_refactor_plan(
            artifacts_dir, "refactor-1", "src/old.py", "src/new.py"
        )

        detector = DriftDetectorAdapter()

        signals = detector.detect_orphan_plans(tmp_path)

        assert len(signals) == 1
        assert signals[0].signal_type == DriftSignalType.ORPHAN_PLAN
        assert signals[0].related_artifact_id == "refactor-1"


class TestRefactorHotspotDetection:
    """Tests for refactor hotspot detection."""

    def test_detects_refactor_hotspot(self, tmp_path: Path) -> None:
        """Should detect frequently refactored files."""
        # Create audit log with multiple refactors
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()

        entries = [
            _create_audit_entry("refactor", ["src/hot.py"], days_ago=i)
            for i in range(5)
        ]
        (audit_dir / "executions.log").write_text("\n".join(entries))

        detector = DriftDetectorAdapter(config=DriftConfig(refactor_threshold=3))

        signals = detector.detect_refactor_hotspots(tmp_path)

        assert len(signals) == 1
        assert signals[0].signal_type == DriftSignalType.REFACTOR_HOTSPOT
        assert signals[0].path == "src/hot.py"
        assert "5 times" in signals[0].description

    def test_no_hotspot_below_threshold(self, tmp_path: Path) -> None:
        """Should not report hotspot when below threshold."""
        # Create audit log with few refactors
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()

        entries = [
            _create_audit_entry("refactor", ["src/file.py"], days_ago=i)
            for i in range(2)
        ]
        (audit_dir / "executions.log").write_text("\n".join(entries))

        detector = DriftDetectorAdapter(config=DriftConfig(refactor_threshold=3))

        signals = detector.detect_refactor_hotspots(tmp_path)

        assert len(signals) == 0

    def test_ignores_old_refactors(self, tmp_path: Path) -> None:
        """Should ignore refactors outside time window."""
        # Create audit log with old refactors
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()

        entries = [
            _create_audit_entry("refactor", ["src/old.py"], days_ago=i)
            for i in range(60, 65)  # 60-65 days ago
        ]
        (audit_dir / "executions.log").write_text("\n".join(entries))

        detector = DriftDetectorAdapter(
            config=DriftConfig(refactor_threshold=3, refactor_window_days=30)
        )

        signals = detector.detect_refactor_hotspots(tmp_path)

        assert len(signals) == 0

    def test_ignores_non_refactor_entries(self, tmp_path: Path) -> None:
        """Should ignore non-refactor audit entries."""
        # Create audit log with scaffold entries
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()

        entries = [
            _create_audit_entry("scaffold", ["src/file.py"], days_ago=i)
            for i in range(5)
        ]
        (audit_dir / "executions.log").write_text("\n".join(entries))

        detector = DriftDetectorAdapter(config=DriftConfig(refactor_threshold=3))

        signals = detector.detect_refactor_hotspots(tmp_path)

        assert len(signals) == 0


class TestFullAnalysis:
    """Tests for full drift analysis."""

    def test_full_analysis_returns_report(self, tmp_path: Path) -> None:
        """Should return complete drift report."""
        # Create minimal project
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")

        config = DriftConfig(source_dirs=["src"])
        detector = DriftDetectorAdapter(config=config)

        report = detector.full_analysis(tmp_path)

        assert report.analyzed_at is not None
        assert report.threshold == config.drift_threshold
        assert report.code_files_scanned >= 1

    def test_full_analysis_aggregates_signals(self, tmp_path: Path) -> None:
        """Should aggregate signals from all detectors."""
        # Create orphan code
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "orphan.py").write_text("orphan")

        # Create orphan plan
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(
            artifacts_dir, "orphan-plan", "src/nonexistent.py"
        )

        # Create refactor hotspot
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        entries = [
            _create_audit_entry("refactor", ["src/hot.py"], days_ago=i)
            for i in range(5)
        ]
        (audit_dir / "executions.log").write_text("\n".join(entries))

        config = DriftConfig(source_dirs=["src"], refactor_threshold=3)
        detector = DriftDetectorAdapter(config=config)

        report = detector.full_analysis(tmp_path)

        # Should have signals from each detector
        assert len(report.by_type(DriftSignalType.ORPHAN_CODE)) >= 1
        assert len(report.by_type(DriftSignalType.ORPHAN_PLAN)) == 1
        assert len(report.by_type(DriftSignalType.REFACTOR_HOTSPOT)) == 1

    def test_full_analysis_empty_project(self, tmp_path: Path) -> None:
        """Should handle empty project gracefully."""
        config = DriftConfig(source_dirs=["src"])
        detector = DriftDetectorAdapter(config=config)

        report = detector.full_analysis(tmp_path)

        assert report.signal_count == 0
        assert report.requires_reconciliation is False


class TestUndocumentedBehaviorDetection:
    """Tests for undocumented behavior detection."""

    def test_no_signals_without_requirements(self, tmp_path: Path) -> None:
        """Should return empty list when no requirements.md exists."""
        # Create test file
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").write_text(
            "def test_something():\n    pass\n"
        )

        detector = DriftDetectorAdapter()
        signals = detector.detect_undocumented_behavior(tmp_path)

        assert len(signals) == 0

    def test_no_signals_when_tests_match_requirements(self, tmp_path: Path) -> None:
        """Should not flag tests that match documented requirements."""
        # Create requirements
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text(
            "# Requirements\n\n- User authentication\n- Login functionality\n"
        )

        # Create test that matches requirements
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_auth.py").write_text(
            'def test_user_login():\n    """Test user login."""\n    pass\n'
        )

        detector = DriftDetectorAdapter()
        signals = detector.detect_undocumented_behavior(tmp_path)

        assert len(signals) == 0

    def test_flags_tests_not_in_requirements(self, tmp_path: Path) -> None:
        """Should flag tests for undocumented behavior."""
        # Create requirements with limited scope
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text(
            "# Requirements\n\n- User authentication\n"
        )

        # Create test for undocumented feature
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_billing.py").write_text(
            "def test_payment_processing():\n    pass\n"
        )

        detector = DriftDetectorAdapter()
        signals = detector.detect_undocumented_behavior(tmp_path)

        assert len(signals) == 1
        assert signals[0].signal_type == DriftSignalType.UNDOCUMENTED_BEHAVIOR
        assert "test_payment_processing" in signals[0].description
        assert signals[0].severity == DriftSeverity.LOW

    def test_matches_requirement_from_docstring(self, tmp_path: Path) -> None:
        """Should check docstrings for requirement matches."""
        # Create requirements
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text(
            "# Requirements\n\n- Password validation\n"
        )

        # Create test with matching docstring
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_misc.py").write_text(
            'def test_xyz():\n    """Test password validation rules."""\n    pass\n'
        )

        detector = DriftDetectorAdapter()
        signals = detector.detect_undocumented_behavior(tmp_path)

        # Should not flag because docstring mentions "password" and "validation"
        assert len(signals) == 0

    def test_extracts_feature_ids(self, tmp_path: Path) -> None:
        """Should extract feature IDs from requirements."""
        # Create requirements with feature IDs
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text(
            "# Requirements\n\n- FR-001: User login\n- REQ-123: Password reset\n"
        )

        # Create test referencing feature ID
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_features.py").write_text(
            'def test_fr_001():\n    """Test FR-001."""\n    pass\n'
        )

        detector = DriftDetectorAdapter()
        signals = detector.detect_undocumented_behavior(tmp_path)

        # Should not flag because test matches feature ID
        assert len(signals) == 0

    def test_handles_syntax_errors_gracefully(self, tmp_path: Path) -> None:
        """Should handle test files with syntax errors."""
        # Create requirements
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text(
            "# Requirements\n\n- Some feature\n"
        )

        # Create test with syntax error
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_broken.py").write_text("def test_broken(\n    pass\n")

        detector = DriftDetectorAdapter()
        signals = detector.detect_undocumented_behavior(tmp_path)

        # Should not crash, just return empty
        assert len(signals) == 0

    def test_scans_nested_test_directories(self, tmp_path: Path) -> None:
        """Should find tests in nested directories."""
        # Create requirements
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        (project_dir / "requirements.md").write_text(
            "# Requirements\n\n- User management\n"
        )

        # Create nested test
        nested_dir = tmp_path / "tests" / "unit" / "services"
        nested_dir.mkdir(parents=True)
        (nested_dir / "test_unknown.py").write_text(
            "def test_mystery_feature():\n    pass\n"
        )

        detector = DriftDetectorAdapter()
        signals = detector.detect_undocumented_behavior(tmp_path)

        assert len(signals) == 1
        assert "mystery_feature" in signals[0].description


class TestKeywordExtraction:
    """Tests for requirement keyword extraction."""

    def test_extracts_from_bullets(self, tmp_path: Path) -> None:
        """Should extract keywords from bullet points."""
        detector = DriftDetectorAdapter()
        text = "# Requirements\n\n- User authentication\n- Password reset\n"
        keywords = detector._extract_requirement_keywords(text)

        assert "user" in keywords
        assert "authentication" in keywords
        assert "password" in keywords
        assert "reset" in keywords

    def test_extracts_from_numbered_list(self, tmp_path: Path) -> None:
        """Should extract keywords from numbered lists."""
        detector = DriftDetectorAdapter()
        text = "# Requirements\n\n1. Email verification\n2. Token generation\n"
        keywords = detector._extract_requirement_keywords(text)

        assert "email" in keywords
        assert "verification" in keywords
        assert "token" in keywords
        assert "generation" in keywords

    def test_extracts_from_headers(self, tmp_path: Path) -> None:
        """Should extract keywords from section headers."""
        detector = DriftDetectorAdapter()
        text = "# Authentication\n\n## Login Flow\n\n### Password Rules\n"
        keywords = detector._extract_requirement_keywords(text)

        assert "authentication" in keywords
        assert "login" in keywords
        assert "flow" in keywords
        assert "password" in keywords
        assert "rules" in keywords

    def test_excludes_stop_words(self, tmp_path: Path) -> None:
        """Should exclude common stop words."""
        detector = DriftDetectorAdapter()
        text = "- The user should have the ability to login\n"
        keywords = detector._extract_requirement_keywords(text)

        assert "the" not in keywords
        assert "should" not in keywords
        assert "have" not in keywords
        assert "user" in keywords  # Not a stop word
        assert "ability" in keywords
        assert "login" in keywords

    def test_excludes_short_words(self, tmp_path: Path) -> None:
        """Should exclude very short words."""
        detector = DriftDetectorAdapter()
        text = "- A to do list for the app\n"
        keywords = detector._extract_requirement_keywords(text)

        # 1-2 char words excluded
        assert "a" not in keywords
        assert "to" not in keywords
        # 3+ char words included
        assert "list" in keywords
        assert "app" in keywords

    def test_removes_code_blocks(self, tmp_path: Path) -> None:
        """Should ignore content in code blocks."""
        detector = DriftDetectorAdapter()
        text = "# Requirements\n\n```python\ndef secret_function():\n    pass\n```\n\n- Real requirement\n"
        keywords = detector._extract_requirement_keywords(text)

        assert "secret" not in keywords
        assert "function" not in keywords
        assert "real" in keywords
        assert "requirement" in keywords


class TestDriftConfig:
    """Tests for drift configuration."""

    def test_custom_config(self) -> None:
        """Should accept custom configuration."""
        config = DriftConfig(
            drift_threshold=5,
            refactor_threshold=10,
            source_dirs=["lib", "bin"],
        )
        detector = DriftDetectorAdapter(config=config)

        assert detector._config.drift_threshold == 5
        assert detector._config.refactor_threshold == 10
        assert "lib" in detector._config.source_dirs
