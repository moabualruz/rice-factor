"""Unit tests for OverrideScopeManager service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from rice_factor.domain.services.override_scope_manager import (
    CIFlag,
    OverrideRecord,
    OverrideScope,
    OverrideScopeManager,
    ScopeLimit,
    ScopeLimitViolation,
    ScopeReport,
)


class TestScopeLimit:
    """Tests for ScopeLimit dataclass."""

    def test_default_values(self) -> None:
        """ScopeLimit should have sensible defaults."""
        limits = ScopeLimit()
        assert limits.max_file_overrides == 10
        assert limits.max_directory_overrides == 3
        assert limits.max_project_overrides == 1
        assert limits.max_override_age_days == 30
        assert limits.require_reason_min_length == 20

    def test_custom_values(self) -> None:
        """ScopeLimit should accept custom values."""
        limits = ScopeLimit(
            max_file_overrides=5,
            max_directory_overrides=2,
            max_project_overrides=0,
        )
        assert limits.max_file_overrides == 5
        assert limits.max_directory_overrides == 2
        assert limits.max_project_overrides == 0


class TestOverrideRecord:
    """Tests for OverrideRecord dataclass."""

    def test_creation(self) -> None:
        """OverrideRecord should be creatable."""
        now = datetime.now(UTC)
        record = OverrideRecord(
            override_id="test-123",
            scope=OverrideScope.FILE,
            target_path="src/main.py",
            reason="Testing override functionality",
            created_at=now,
        )
        assert record.override_id == "test-123"
        assert record.scope == OverrideScope.FILE
        assert record.reconciled is False

    def test_with_all_fields(self) -> None:
        """OverrideRecord should accept all fields."""
        now = datetime.now(UTC)
        record = OverrideRecord(
            override_id="test-456",
            scope=OverrideScope.DIRECTORY,
            target_path="src/",
            reason="Directory level override for testing",
            created_at=now,
            created_by="test-user",
            reconciled=True,
            reconciled_at=now,
            ci_flagged=True,
            ci_flag_commit="abc123",
        )
        assert record.created_by == "test-user"
        assert record.reconciled is True


class TestCIFlag:
    """Tests for CIFlag dataclass."""

    def test_creation(self) -> None:
        """CIFlag should be creatable."""
        now = datetime.now(UTC)
        flag = CIFlag(
            file_path="src/main.py",
            override_id="test-123",
            flagged_at=now,
            flagged_commit="abc123",
            message="Override active",
        )
        assert flag.severity == "warning"
        assert flag.file_path == "src/main.py"


class TestScopeReport:
    """Tests for ScopeReport dataclass."""

    def test_creation(self) -> None:
        """ScopeReport should be creatable."""
        now = datetime.now(UTC)
        report = ScopeReport(
            generated_at=now,
            file_overrides=5,
            directory_overrides=2,
            project_overrides=0,
            artifact_overrides=1,
            violations=[],
            expiring_soon=[],
            ci_flags=[],
        )
        assert report.total_overrides == 8
        assert report.has_violations is False

    def test_with_violations(self) -> None:
        """ScopeReport should detect violations."""
        now = datetime.now(UTC)
        report = ScopeReport(
            generated_at=now,
            file_overrides=0,
            directory_overrides=0,
            project_overrides=0,
            artifact_overrides=0,
            violations=["Test violation"],
            expiring_soon=[],
            ci_flags=[],
        )
        assert report.has_violations is True

    def test_to_dict(self) -> None:
        """ScopeReport should serialize to dict."""
        now = datetime.now(UTC)
        report = ScopeReport(
            generated_at=now,
            file_overrides=3,
            directory_overrides=1,
            project_overrides=0,
            artifact_overrides=0,
            violations=[],
            expiring_soon=[],
            ci_flags=[],
        )
        result = report.to_dict()
        assert result["total_overrides"] == 4
        assert result["file_overrides"] == 3


class TestOverrideScopeManager:
    """Tests for OverrideScopeManager service."""

    def test_creation(self, tmp_path: Path) -> None:
        """OverrideScopeManager should be creatable."""
        manager = OverrideScopeManager(repo_root=tmp_path)
        assert manager.repo_root == tmp_path

    def test_register_override(self, tmp_path: Path) -> None:
        """should register a valid override."""
        manager = OverrideScopeManager(repo_root=tmp_path)
        record = manager.register_override(
            override_id="test-001",
            scope=OverrideScope.FILE,
            target_path="src/main.py",
            reason="This is a valid reason with enough characters for the test",
        )
        assert record.override_id == "test-001"
        assert record.scope == OverrideScope.FILE

    def test_register_override_short_reason(self, tmp_path: Path) -> None:
        """should reject override with short reason."""
        manager = OverrideScopeManager(repo_root=tmp_path)
        with pytest.raises(ValueError, match="at least"):
            manager.register_override(
                override_id="test-001",
                scope=OverrideScope.FILE,
                target_path="src/main.py",
                reason="Too short",
            )

    def test_scope_limit_file_override(self, tmp_path: Path) -> None:
        """should enforce file override limit."""
        limits = ScopeLimit(max_file_overrides=2)
        manager = OverrideScopeManager(repo_root=tmp_path, limits=limits)

        # Register up to limit
        for i in range(2):
            manager.register_override(
                override_id=f"test-{i}",
                scope=OverrideScope.FILE,
                target_path=f"src/file{i}.py",
                reason="This is a sufficiently long reason for testing purposes",
            )

        # Should fail on the third
        with pytest.raises(ScopeLimitViolation) as exc_info:
            manager.register_override(
                override_id="test-3",
                scope=OverrideScope.FILE,
                target_path="src/file3.py",
                reason="This is a sufficiently long reason for testing purposes",
            )
        assert exc_info.value.limit == "max_file_overrides"
        assert exc_info.value.max_allowed == 2

    def test_scope_limit_directory_override(self, tmp_path: Path) -> None:
        """should enforce directory override limit."""
        limits = ScopeLimit(max_directory_overrides=1)
        manager = OverrideScopeManager(repo_root=tmp_path, limits=limits)

        # Register one directory override
        manager.register_override(
            override_id="test-dir-1",
            scope=OverrideScope.DIRECTORY,
            target_path="src/utils/",
            reason="This is a sufficiently long reason for testing purposes",
        )

        # Should fail on the second
        with pytest.raises(ScopeLimitViolation) as exc_info:
            manager.register_override(
                override_id="test-dir-2",
                scope=OverrideScope.DIRECTORY,
                target_path="src/services/",
                reason="This is a sufficiently long reason for testing purposes",
            )
        assert exc_info.value.limit == "max_directory_overrides"

    def test_scope_limit_project_override(self, tmp_path: Path) -> None:
        """should enforce project override limit."""
        limits = ScopeLimit(max_project_overrides=0)
        manager = OverrideScopeManager(repo_root=tmp_path, limits=limits)

        # Should fail immediately
        with pytest.raises(ScopeLimitViolation) as exc_info:
            manager.register_override(
                override_id="test-proj",
                scope=OverrideScope.PROJECT,
                target_path=".",
                reason="This is a sufficiently long reason for testing purposes",
            )
        assert exc_info.value.limit == "max_project_overrides"

    def test_get_active_overrides(self, tmp_path: Path) -> None:
        """should return only non-reconciled overrides."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        # Register two overrides
        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.FILE,
            target_path="src/a.py",
            reason="This is a sufficiently long reason for testing purposes",
        )
        manager.register_override(
            override_id="test-2",
            scope=OverrideScope.FILE,
            target_path="src/b.py",
            reason="This is a sufficiently long reason for testing purposes",
        )

        # Reconcile one
        manager.reconcile_override("test-1")

        active = manager.get_active_overrides()
        assert len(active) == 1
        assert active[0].override_id == "test-2"

    def test_reconcile_override(self, tmp_path: Path) -> None:
        """should mark override as reconciled."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.FILE,
            target_path="src/main.py",
            reason="This is a sufficiently long reason for testing purposes",
        )

        result = manager.reconcile_override("test-1")
        assert result is True

        record = manager._records.get("test-1")
        assert record is not None
        assert record.reconciled is True
        assert record.reconciled_at is not None

    def test_reconcile_nonexistent_override(self, tmp_path: Path) -> None:
        """should return False for nonexistent override."""
        manager = OverrideScopeManager(repo_root=tmp_path)
        result = manager.reconcile_override("nonexistent")
        assert result is False

    def test_flag_for_ci(self, tmp_path: Path) -> None:
        """should create CI flag for override."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.FILE,
            target_path="src/main.py",
            reason="This is a sufficiently long reason for testing purposes",
        )

        flag = manager.flag_for_ci("test-1", "abc123def")
        assert flag is not None
        assert flag.flagged_commit == "abc123def"
        assert flag.file_path == "src/main.py"

    def test_flag_for_ci_nonexistent(self, tmp_path: Path) -> None:
        """should return None for nonexistent override."""
        manager = OverrideScopeManager(repo_root=tmp_path)
        flag = manager.flag_for_ci("nonexistent", "abc123")
        assert flag is None

    def test_flag_for_ci_already_flagged(self, tmp_path: Path) -> None:
        """should return existing flag if already flagged."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.FILE,
            target_path="src/main.py",
            reason="This is a sufficiently long reason for testing purposes",
        )

        flag1 = manager.flag_for_ci("test-1", "abc123")
        flag2 = manager.flag_for_ci("test-1", "def456")

        # Should return the same flag
        assert flag1 is not None
        assert flag2 is not None
        assert flag1.flagged_commit == flag2.flagged_commit

    def test_get_ci_flags(self, tmp_path: Path) -> None:
        """should return only flags for active overrides."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        # Register and flag two overrides
        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.FILE,
            target_path="src/a.py",
            reason="This is a sufficiently long reason for testing purposes",
        )
        manager.register_override(
            override_id="test-2",
            scope=OverrideScope.FILE,
            target_path="src/b.py",
            reason="This is a sufficiently long reason for testing purposes",
        )

        manager.flag_for_ci("test-1", "abc123")
        manager.flag_for_ci("test-2", "abc123")

        # Reconcile one
        manager.reconcile_override("test-1")

        flags = manager.get_ci_flags()
        assert len(flags) == 1
        assert flags[0].override_id == "test-2"

    def test_is_path_overridden_file(self, tmp_path: Path) -> None:
        """should detect file override."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.FILE,
            target_path="src/main.py",
            reason="This is a sufficiently long reason for testing purposes",
        )

        assert manager.is_path_overridden("src/main.py") is True
        assert manager.is_path_overridden("src/other.py") is False

    def test_is_path_overridden_directory(self, tmp_path: Path) -> None:
        """should detect directory override."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.DIRECTORY,
            target_path="src/utils",
            reason="This is a sufficiently long reason for testing purposes",
        )

        assert manager.is_path_overridden("src/utils/helper.py") is True
        assert manager.is_path_overridden("src/utils") is True
        assert manager.is_path_overridden("src/main.py") is False

    def test_is_path_overridden_project(self, tmp_path: Path) -> None:
        """should detect project override."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.PROJECT,
            target_path=".",
            reason="This is a sufficiently long reason for testing purposes",
        )

        assert manager.is_path_overridden("src/main.py") is True
        assert manager.is_path_overridden("tests/test_main.py") is True

    def test_generate_report(self, tmp_path: Path) -> None:
        """should generate accurate report."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.FILE,
            target_path="src/a.py",
            reason="This is a sufficiently long reason for testing purposes",
        )
        manager.register_override(
            override_id="test-2",
            scope=OverrideScope.DIRECTORY,
            target_path="src/utils/",
            reason="This is a sufficiently long reason for testing purposes",
        )

        report = manager.generate_report()
        assert report.file_overrides == 1
        assert report.directory_overrides == 1
        assert report.total_overrides == 2
        assert report.has_violations is False

    def test_persistence(self, tmp_path: Path) -> None:
        """should persist and reload records."""
        # Create manager and register override
        manager1 = OverrideScopeManager(repo_root=tmp_path)
        manager1.register_override(
            override_id="test-persist",
            scope=OverrideScope.FILE,
            target_path="src/main.py",
            reason="This is a sufficiently long reason for testing purposes",
        )

        # Create new manager instance
        manager2 = OverrideScopeManager(repo_root=tmp_path)
        active = manager2.get_active_overrides()

        assert len(active) == 1
        assert active[0].override_id == "test-persist"

    def test_get_override_for_path(self, tmp_path: Path) -> None:
        """should return the override affecting a path."""
        manager = OverrideScopeManager(repo_root=tmp_path)

        manager.register_override(
            override_id="test-1",
            scope=OverrideScope.DIRECTORY,
            target_path="src/utils",
            reason="This is a sufficiently long reason for testing purposes",
        )

        record = manager.get_override_for_path("src/utils/helper.py")
        assert record is not None
        assert record.override_id == "test-1"

        record2 = manager.get_override_for_path("src/main.py")
        assert record2 is None

    def test_check_scope_violations(self, tmp_path: Path) -> None:
        """should detect scope violations."""
        # Start with permissive limits
        limits = ScopeLimit(max_file_overrides=10)
        manager = OverrideScopeManager(repo_root=tmp_path, limits=limits)

        # Register some overrides
        for i in range(3):
            manager.register_override(
                override_id=f"test-{i}",
                scope=OverrideScope.FILE,
                target_path=f"src/file{i}.py",
                reason="This is a sufficiently long reason for testing purposes",
            )

        # Change limits to be more restrictive
        manager.limits = ScopeLimit(max_file_overrides=2)

        violations = manager.check_scope_violations()
        assert len(violations) > 0
        assert "File override limit exceeded" in violations[0]
