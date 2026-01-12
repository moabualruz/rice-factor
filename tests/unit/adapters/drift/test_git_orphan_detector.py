"""Unit tests for GitOrphanDetector adapter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from rice_factor.adapters.drift.git_orphan_detector import (
    CleanupPriority,
    CleanupRecommendation,
    GitOrphanDetector,
    OrphanDetectionReport,
    OrphanedCode,
    OrphanType,
)


class TestOrphanedCode:
    """Tests for OrphanedCode dataclass."""

    def test_creation(self) -> None:
        """OrphanedCode should be creatable."""
        now = datetime.now(UTC)
        orphan = OrphanedCode(
            path="src/old_module.py",
            orphan_type=OrphanType.OBSOLETE_FILE,
            last_commit_hash="abc123",
            last_commit_date=now,
            last_commit_message="Last commit",
            evidence=["Not modified in 200 days"],
            days_since_modified=200,
        )
        assert orphan.path == "src/old_module.py"
        assert orphan.orphan_type == OrphanType.OBSOLETE_FILE

    def test_age_category_very_old(self) -> None:
        """should categorize as very_old."""
        orphan = OrphanedCode(
            path="test.py",
            orphan_type=OrphanType.OBSOLETE_FILE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=[],
            days_since_modified=400,
        )
        assert orphan.age_category == "very_old"

    def test_age_category_old(self) -> None:
        """should categorize as old."""
        orphan = OrphanedCode(
            path="test.py",
            orphan_type=OrphanType.OBSOLETE_FILE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=[],
            days_since_modified=200,
        )
        assert orphan.age_category == "old"

    def test_age_category_stale(self) -> None:
        """should categorize as stale."""
        orphan = OrphanedCode(
            path="test.py",
            orphan_type=OrphanType.OBSOLETE_FILE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=[],
            days_since_modified=100,
        )
        assert orphan.age_category == "stale"

    def test_age_category_recent(self) -> None:
        """should categorize as recent."""
        orphan = OrphanedCode(
            path="test.py",
            orphan_type=OrphanType.OBSOLETE_FILE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=[],
            days_since_modified=30,
        )
        assert orphan.age_category == "recent"


class TestCleanupRecommendation:
    """Tests for CleanupRecommendation dataclass."""

    def test_creation(self) -> None:
        """CleanupRecommendation should be creatable."""
        orphan = OrphanedCode(
            path="test.py",
            orphan_type=OrphanType.OBSOLETE_FILE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=[],
            days_since_modified=200,
        )
        rec = CleanupRecommendation(
            path="test.py",
            priority=CleanupPriority.HIGH,
            action="archive",
            reason="Not modified in 200 days",
            orphan=orphan,
            estimated_impact="none",
        )
        assert rec.priority == CleanupPriority.HIGH
        assert rec.action == "archive"

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        orphan = OrphanedCode(
            path="test.py",
            orphan_type=OrphanType.OBSOLETE_FILE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=[],
            days_since_modified=200,
        )
        rec = CleanupRecommendation(
            path="test.py",
            priority=CleanupPriority.MEDIUM,
            action="review",
            reason="Old file",
            orphan=orphan,
            estimated_impact="low",
        )
        result = rec.to_dict()
        assert result["priority"] == "medium"
        assert result["action"] == "review"
        assert result["age_category"] == "old"


class TestOrphanDetectionReport:
    """Tests for OrphanDetectionReport dataclass."""

    def test_creation(self) -> None:
        """OrphanDetectionReport should be creatable."""
        report = OrphanDetectionReport(
            analyzed_at=datetime.now(UTC),
            repo_root="/test/repo",
            commits_analyzed=100,
            files_analyzed=50,
            orphans_detected=[],
            recommendations=[],
            git_available=True,
        )
        assert report.orphan_count == 0
        assert report.critical_count == 0

    def test_orphan_count(self) -> None:
        """should count orphans."""
        orphan = OrphanedCode(
            path="test.py",
            orphan_type=OrphanType.OBSOLETE_FILE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=[],
            days_since_modified=200,
        )
        report = OrphanDetectionReport(
            analyzed_at=datetime.now(UTC),
            repo_root="/test",
            commits_analyzed=10,
            files_analyzed=5,
            orphans_detected=[orphan],
            recommendations=[],
            git_available=True,
        )
        assert report.orphan_count == 1

    def test_critical_count(self) -> None:
        """should count critical recommendations."""
        orphan = OrphanedCode(
            path="test.py",
            orphan_type=OrphanType.DELETED_REFERENCE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=[],
            days_since_modified=0,
        )
        rec = CleanupRecommendation(
            path="test.py",
            priority=CleanupPriority.CRITICAL,
            action="review",
            reason="Broken reference",
            orphan=orphan,
            estimated_impact="high",
        )
        report = OrphanDetectionReport(
            analyzed_at=datetime.now(UTC),
            repo_root="/test",
            commits_analyzed=10,
            files_analyzed=5,
            orphans_detected=[orphan],
            recommendations=[rec],
            git_available=True,
        )
        assert report.critical_count == 1

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        report = OrphanDetectionReport(
            analyzed_at=datetime.now(UTC),
            repo_root="/test",
            commits_analyzed=50,
            files_analyzed=25,
            orphans_detected=[],
            recommendations=[],
            git_available=True,
        )
        result = report.to_dict()
        assert result["commits_analyzed"] == 50
        assert result["files_analyzed"] == 25


class TestGitOrphanDetector:
    """Tests for GitOrphanDetector adapter."""

    def test_creation(self, tmp_path: Path) -> None:
        """GitOrphanDetector should be creatable."""
        detector = GitOrphanDetector(repo_root=tmp_path)
        assert detector.repo_root == tmp_path
        assert detector.staleness_threshold_days == 180

    def test_custom_threshold(self, tmp_path: Path) -> None:
        """should accept custom staleness threshold."""
        detector = GitOrphanDetector(
            repo_root=tmp_path,
            staleness_threshold_days=90,
        )
        assert detector.staleness_threshold_days == 90

    def test_detect_no_git(self, tmp_path: Path) -> None:
        """should handle non-git directory."""
        detector = GitOrphanDetector(repo_root=tmp_path)
        report = detector.detect()
        assert report.git_available is False
        assert report.orphan_count == 0

    def test_is_source_file(self, tmp_path: Path) -> None:
        """should detect source file extensions."""
        detector = GitOrphanDetector(repo_root=tmp_path)

        assert detector._is_source_file("main.py") is True
        assert detector._is_source_file("app.js") is True
        assert detector._is_source_file("Main.java") is True
        assert detector._is_source_file("README.md") is False
        assert detector._is_source_file("config.yaml") is False

    def test_is_excluded(self, tmp_path: Path) -> None:
        """should exclude common directories."""
        detector = GitOrphanDetector(repo_root=tmp_path)

        assert detector._is_excluded(tmp_path / ".git" / "config") is True
        assert detector._is_excluded(tmp_path / "node_modules" / "pkg" / "index.js") is True
        assert detector._is_excluded(tmp_path / ".venv" / "lib" / "site.py") is True
        assert detector._is_excluded(tmp_path / "src" / "main.py") is False

    def test_generate_recommendation_obsolete(self, tmp_path: Path) -> None:
        """should generate archive recommendation for very old files."""
        detector = GitOrphanDetector(repo_root=tmp_path)

        orphan = OrphanedCode(
            path="old_module.py",
            orphan_type=OrphanType.OBSOLETE_FILE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=[],
            days_since_modified=400,
        )

        rec = detector._generate_recommendation(orphan)
        assert rec.priority == CleanupPriority.HIGH
        assert rec.action == "archive"

    def test_generate_recommendation_deleted_ref(self, tmp_path: Path) -> None:
        """should generate review recommendation for deleted references."""
        detector = GitOrphanDetector(repo_root=tmp_path)

        orphan = OrphanedCode(
            path="deleted.py",
            orphan_type=OrphanType.DELETED_REFERENCE,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=["Referenced in: main.py"],
            days_since_modified=0,
        )

        rec = detector._generate_recommendation(orphan)
        assert rec.priority == CleanupPriority.HIGH
        assert rec.action == "review"
        assert rec.estimated_impact == "medium"

    def test_generate_recommendation_orphan_test(self, tmp_path: Path) -> None:
        """should generate medium priority for orphan tests."""
        detector = GitOrphanDetector(repo_root=tmp_path)

        orphan = OrphanedCode(
            path="test_old.py",
            orphan_type=OrphanType.ORPHAN_TEST,
            last_commit_hash=None,
            last_commit_date=None,
            last_commit_message=None,
            evidence=["Missing imports: old_module"],
            days_since_modified=50,
        )

        rec = detector._generate_recommendation(orphan)
        assert rec.priority == CleanupPriority.MEDIUM
        assert rec.action == "review"

    def test_is_internal_module(self, tmp_path: Path) -> None:
        """should detect internal modules."""
        detector = GitOrphanDetector(repo_root=tmp_path)

        # Create a directory to simulate internal package
        (tmp_path / "mypackage").mkdir()

        assert detector._is_internal_module("rice_factor.utils") is True
        assert detector._is_internal_module("mypackage.helpers") is True
        assert detector._is_internal_module("os.path") is False
        assert detector._is_internal_module("pytest") is False

    def test_module_exists(self, tmp_path: Path) -> None:
        """should check if module exists."""
        detector = GitOrphanDetector(repo_root=tmp_path)

        # Create a module file
        pkg_dir = tmp_path / "mypackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "utils.py").write_text("")

        assert detector._module_exists("mypackage.utils") is True
        assert detector._module_exists("mypackage") is True
        assert detector._module_exists("mypackage.missing") is False


class TestOrphanTypes:
    """Tests for OrphanType enum."""

    def test_all_types_exist(self) -> None:
        """All expected orphan types should exist."""
        assert OrphanType.DELETED_REFERENCE.value == "deleted_reference"
        assert OrphanType.UNUSED_EXPORT.value == "unused_export"
        assert OrphanType.DEAD_CODE.value == "dead_code"
        assert OrphanType.OBSOLETE_FILE.value == "obsolete_file"
        assert OrphanType.ORPHAN_TEST.value == "orphan_test"
        assert OrphanType.ORPHAN_IMPORT.value == "orphan_import"


class TestCleanupPriorities:
    """Tests for CleanupPriority enum."""

    def test_all_priorities_exist(self) -> None:
        """All expected priorities should exist."""
        assert CleanupPriority.CRITICAL.value == "critical"
        assert CleanupPriority.HIGH.value == "high"
        assert CleanupPriority.MEDIUM.value == "medium"
        assert CleanupPriority.LOW.value == "low"
