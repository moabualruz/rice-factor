"""Unit tests for SafetyEnforcer service."""

import json
from pathlib import Path

import pytest

from rice_factor.domain.failures.executor_errors import (
    TestsLockedError,
    UnauthorizedFileModificationError,
)
from rice_factor.domain.services.safety_enforcer import SafetyEnforcer


class TestSafetyEnforcerTestLock:
    """Tests for test lock verification."""

    def test_check_lock_no_lock_file(self, tmp_path: Path) -> None:
        """No lock file means valid state."""
        enforcer = SafetyEnforcer(project_root=tmp_path)
        result = enforcer.check_test_lock_intact()
        assert result.is_valid
        assert result.modified_files == []

    def test_check_lock_empty_test_files(self, tmp_path: Path) -> None:
        """Lock file with no test files is valid."""
        (tmp_path / ".project").mkdir(parents=True)
        lock_data = {
            "test_plan_id": "test-123",
            "locked_at": "2026-01-10T12:00:00Z",
            "test_files": {},
        }
        (tmp_path / ".project" / ".lock").write_text(json.dumps(lock_data))

        enforcer = SafetyEnforcer(project_root=tmp_path)
        result = enforcer.check_test_lock_intact()
        assert result.is_valid

    def test_check_lock_unchanged_files(self, tmp_path: Path) -> None:
        """Lock verification passes for unchanged files."""
        # Create test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_user.py"
        test_file.write_text("def test_user(): pass")

        # Compute expected hash
        import hashlib

        content = test_file.read_bytes()
        expected_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"

        # Create lock file
        (tmp_path / ".project").mkdir(parents=True)
        lock_data = {
            "test_plan_id": "test-123",
            "locked_at": "2026-01-10T12:00:00Z",
            "test_files": {"tests/test_user.py": expected_hash},
        }
        (tmp_path / ".project" / ".lock").write_text(json.dumps(lock_data))

        enforcer = SafetyEnforcer(project_root=tmp_path)
        result = enforcer.check_test_lock_intact()
        assert result.is_valid
        assert result.modified_files == []

    def test_check_lock_modified_file(self, tmp_path: Path) -> None:
        """Lock verification fails for modified files."""
        # Create test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_user.py"
        test_file.write_text("def test_user(): pass")

        # Create lock file with different hash
        (tmp_path / ".project").mkdir(parents=True)
        lock_data = {
            "test_plan_id": "test-123",
            "locked_at": "2026-01-10T12:00:00Z",
            "test_files": {"tests/test_user.py": "sha256:different_hash"},
        }
        (tmp_path / ".project" / ".lock").write_text(json.dumps(lock_data))

        enforcer = SafetyEnforcer(project_root=tmp_path)
        result = enforcer.check_test_lock_intact()
        assert not result.is_valid
        assert "tests/test_user.py" in result.modified_files

    def test_check_lock_missing_file(self, tmp_path: Path) -> None:
        """Lock verification fails for missing files."""
        # Create lock file for non-existent file
        (tmp_path / ".project").mkdir(parents=True)
        lock_data = {
            "test_plan_id": "test-123",
            "locked_at": "2026-01-10T12:00:00Z",
            "test_files": {"tests/test_missing.py": "sha256:some_hash"},
        }
        (tmp_path / ".project" / ".lock").write_text(json.dumps(lock_data))

        enforcer = SafetyEnforcer(project_root=tmp_path)
        result = enforcer.check_test_lock_intact()
        assert not result.is_valid
        assert "tests/test_missing.py" in result.modified_files

    def test_require_lock_intact_raises_on_modification(self, tmp_path: Path) -> None:
        """require_test_lock_intact raises TestsLockedError on modification."""
        # Create test file
        (tmp_path / "tests").mkdir()
        test_file = tmp_path / "tests" / "test_user.py"
        test_file.write_text("def test_user(): pass")

        # Create lock file with different hash
        (tmp_path / ".project").mkdir(parents=True)
        lock_data = {
            "test_plan_id": "test-123",
            "locked_at": "2026-01-10T12:00:00Z",
            "test_files": {"tests/test_user.py": "sha256:different_hash"},
        }
        (tmp_path / ".project" / ".lock").write_text(json.dumps(lock_data))

        enforcer = SafetyEnforcer(project_root=tmp_path)
        with pytest.raises(TestsLockedError) as exc_info:
            enforcer.require_test_lock_intact()

        assert "tests/test_user.py" in str(exc_info.value)
        assert "TestPlan lock violated" in str(exc_info.value)


class TestSafetyEnforcerDiffAuthorization:
    """Tests for diff authorization."""

    def test_diff_authorized_valid(self, tmp_path: Path) -> None:
        """Diff authorization passes for authorized files."""
        enforcer = SafetyEnforcer(project_root=tmp_path)

        diff_content = """
--- a/src/user.py
+++ b/src/user.py
@@ -1 +1 @@
-old content
+new content
"""
        authorized_files = {"src/user.py"}
        is_authorized, unauthorized = enforcer.check_diff_authorized(diff_content, authorized_files)
        assert is_authorized
        assert unauthorized == set()

    def test_diff_unauthorized_file(self, tmp_path: Path) -> None:
        """Diff authorization fails for unauthorized files."""
        enforcer = SafetyEnforcer(project_root=tmp_path)

        diff_content = """
--- a/src/user.py
+++ b/src/user.py
@@ -1 +1 @@
-old content
+new content
--- a/src/other.py
+++ b/src/other.py
@@ -1 +1 @@
-other old
+other new
"""
        authorized_files = {"src/user.py"}
        is_authorized, unauthorized = enforcer.check_diff_authorized(diff_content, authorized_files)
        assert not is_authorized
        assert "src/other.py" in unauthorized

    def test_require_diff_authorized_raises(self, tmp_path: Path) -> None:
        """require_diff_authorized raises on unauthorized files."""
        enforcer = SafetyEnforcer(project_root=tmp_path)

        diff_content = """
--- a/src/user.py
+++ b/src/user.py
@@ -1 +1 @@
-old
+new
--- a/src/other.py
+++ b/src/other.py
@@ -1 +1 @@
-old
+new
"""
        authorized_files = {"src/user.py"}

        with pytest.raises(UnauthorizedFileModificationError) as exc_info:
            enforcer.require_diff_authorized(diff_content, authorized_files)

        assert "src/other.py" in str(exc_info.value)

    def test_diff_with_dev_null(self, tmp_path: Path) -> None:
        """Diff with /dev/null (new file) is handled correctly."""
        enforcer = SafetyEnforcer(project_root=tmp_path)

        diff_content = """
--- /dev/null
+++ b/src/new_file.py
@@ -0,0 +1 @@
+new content
"""
        authorized_files = {"src/new_file.py"}
        is_authorized, _unauthorized = enforcer.check_diff_authorized(diff_content, authorized_files)
        assert is_authorized


class TestSafetyEnforcerParseDiff:
    """Tests for diff parsing."""

    def test_parse_unified_diff(self, tmp_path: Path) -> None:
        """Parse standard unified diff format."""
        enforcer = SafetyEnforcer(project_root=tmp_path)

        diff_content = """
--- a/file1.py
+++ b/file1.py
@@ -1 +1 @@
-old
+new
--- a/file2.py
+++ b/file2.py
@@ -1 +1 @@
-old
+new
"""
        files = enforcer._parse_diff_files(diff_content)
        assert files == {"file1.py", "file2.py"}

    def test_parse_diff_without_ab_prefix(self, tmp_path: Path) -> None:
        """Parse diff without a/ b/ prefix."""
        enforcer = SafetyEnforcer(project_root=tmp_path)

        diff_content = """
--- file1.py
+++ file1.py
@@ -1 +1 @@
-old
+new
"""
        files = enforcer._parse_diff_files(diff_content)
        assert "file1.py" in files

    def test_parse_git_stat_format(self, tmp_path: Path) -> None:
        """Parse git diff --stat format."""
        enforcer = SafetyEnforcer(project_root=tmp_path)

        diff_content = """
 src/file1.py | 2 +-
 src/file2.py | 4 ++--
 2 files changed, 3 insertions(+), 3 deletions(-)
"""
        files = enforcer._parse_diff_files(diff_content)
        assert "src/file1.py" in files
        assert "src/file2.py" in files
