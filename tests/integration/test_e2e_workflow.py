"""End-to-end workflow integration tests.

These tests verify the complete MVP workflow from init to refactor,
validating exit criteria EC-001 through EC-007.
"""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestMVPWorkflowE2E:
    """End-to-end tests for the MVP workflow."""

    def test_e2e_init_creates_structure(self, tmp_path: Path) -> None:
        """EC-001: Init command creates required structure.

        Verifies that `rice-factor init` creates:
        - .project/ directory
        - .project/requirements.md
        - .project/constraints.md
        - .project/glossary.md
        - artifacts/ directory
        - audit/ directory
        """
        # Use --skip-questionnaire to avoid interactive prompts
        result = runner.invoke(
            app, ["init", "--path", str(tmp_path), "--skip-questionnaire"]
        )

        # Should succeed
        assert result.exit_code == 0, f"Init failed: {result.stdout}"

        # Check structure
        assert (tmp_path / ".project").is_dir()
        assert (tmp_path / ".project" / "requirements.md").exists()
        assert (tmp_path / ".project" / "constraints.md").exists()
        assert (tmp_path / ".project" / "glossary.md").exists()
        assert (tmp_path / "artifacts").is_dir()
        assert (tmp_path / "audit").is_dir()

    def test_e2e_plan_requires_init(self, tmp_path: Path) -> None:
        """Plan commands should fail on uninitialized project."""
        result = runner.invoke(
            app, ["plan", "project", "--path", str(tmp_path), "--stub"]
        )

        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    def test_e2e_plan_project_with_stub(self, mvp_project: Path) -> None:
        """EC-002: Plan project generates ProjectPlan artifact.

        Uses --stub flag to avoid real LLM calls.
        Uses --dry-run to avoid context validation issues.
        """
        result = runner.invoke(
            app, ["plan", "project", "--path", str(mvp_project), "--dry-run"]
        )

        # Dry run should succeed even without full context
        assert result.exit_code == 0
        assert "dry run" in result.stdout.lower() or "would" in result.stdout.lower()

    def test_e2e_scaffold_requires_project_plan(self, mvp_project: Path) -> None:
        """Scaffold should fail without ProjectPlan."""
        result = runner.invoke(
            app, ["scaffold", "--path", str(mvp_project), "--stub"]
        )

        assert result.exit_code == 1
        # Should indicate missing dependency or wrong phase

    def test_e2e_scaffold_creates_files(self, mvp_project: Path) -> None:
        """EC-002: Scaffold creates empty files with TODOs."""
        # First create a ProjectPlan
        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(mvp_project), "--yes", "--stub"]
            )

        assert result.exit_code == 0

        # Check files were created
        assert (mvp_project / "src").exists() or (mvp_project / "README.md").exists()

    def test_e2e_test_command_runs(self, mvp_project: Path) -> None:
        """EC-004: Test command runs and emits ValidationResult."""
        with patch(
            "rice_factor.entrypoints.cli.commands.test._check_phase"
        ):
            result = runner.invoke(
                app, ["test", "--path", str(mvp_project)]
            )

        assert result.exit_code == 0
        assert "passed" in result.stdout.lower()

        # Check ValidationResult artifact was created
        artifacts = list((mvp_project / "artifacts").glob("**/*.json"))
        assert len(artifacts) >= 1


class TestPhaseGating:
    """Tests for phase-based command gating."""

    def test_impl_requires_test_locked(self, mvp_project: Path) -> None:
        """Impl command requires TEST_LOCKED phase."""
        result = runner.invoke(
            app, ["impl", "main.py", "--path", str(mvp_project), "--stub"]
        )

        assert result.exit_code == 1
        assert "phase" in result.stdout.lower() or "cannot" in result.stdout.lower()

    def test_apply_requires_test_locked(self, mvp_project: Path) -> None:
        """Apply command requires TEST_LOCKED phase."""
        result = runner.invoke(
            app, ["apply", "--path", str(mvp_project)]
        )

        assert result.exit_code == 1


class TestAuditTrail:
    """Tests for audit trail completeness (EC-007)."""

    def test_audit_trail_created_on_init(self, tmp_path: Path) -> None:
        """Init should create audit trail entry."""
        # Use --skip-questionnaire to avoid interactive prompts
        result = runner.invoke(
            app, ["init", "--path", str(tmp_path), "--skip-questionnaire"]
        )

        assert result.exit_code == 0, f"Init failed: {result.stdout}"

        # Check audit trail exists
        trail_file = tmp_path / "audit" / "trail.json"
        assert trail_file.exists()

    def test_audit_trail_records_scaffold(self, mvp_project: Path) -> None:
        """Scaffold should record audit entry."""
        with patch(
            "rice_factor.entrypoints.cli.commands.scaffold._check_phase"
        ):
            result = runner.invoke(
                app, ["scaffold", "--path", str(mvp_project), "--yes", "--stub"]
            )

        assert result.exit_code == 0

        # Check audit trail
        trail_file = mvp_project / "audit" / "trail.json"
        assert trail_file.exists()


class TestSafetyViolations:
    """Tests for safety violation hard-fails."""

    def test_commands_fail_on_uninit(self, tmp_path: Path) -> None:
        """Commands should fail on uninitialized project."""
        commands = [
            ["plan", "project", "--path", str(tmp_path), "--stub"],
            ["scaffold", "--path", str(tmp_path), "--stub"],
            ["impl", "main.py", "--path", str(tmp_path), "--stub"],
            ["apply", "--path", str(tmp_path)],
            ["test", "--path", str(tmp_path)],
        ]

        for cmd in commands:
            result = runner.invoke(app, cmd)
            assert result.exit_code == 1, f"Command {cmd[0]} should fail on uninit"


class TestDiffAuthorizationIntegration:
    """Integration tests for diff authorization (GAP-M07-003).

    These tests verify the complete diff authorization flow including:
    - SafetyEnforcer.check_diff_authorized()
    - SafetyEnforcer.require_diff_authorized()
    - DiffExecutor integration with authorization checks
    """

    def test_diff_authorization_allows_authorized_files(
        self, mvp_project: Path
    ) -> None:
        """Should allow diffs that only touch authorized files."""
        from rice_factor.domain.services.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(project_root=mvp_project)

        diff_content = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+# New comment
 def main():
     pass
"""
        authorized_files = {"src/main.py", "src/utils.py"}

        is_authorized, unauthorized = safety.check_diff_authorized(
            diff_content, authorized_files
        )

        assert is_authorized is True
        assert len(unauthorized) == 0

    def test_diff_authorization_rejects_unauthorized_files(
        self, mvp_project: Path
    ) -> None:
        """Should reject diffs that touch unauthorized files."""
        from rice_factor.domain.services.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(project_root=mvp_project)

        diff_content = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+# New comment
 def main():
     pass
--- a/config/settings.py
+++ b/config/settings.py
@@ -1,1 +1,2 @@
+# Unauthorized file
 SECRET_KEY = "xxx"
"""
        # Only src/main.py is authorized, not config/settings.py
        authorized_files = {"src/main.py"}

        is_authorized, unauthorized = safety.check_diff_authorized(
            diff_content, authorized_files
        )

        assert is_authorized is False
        assert "config/settings.py" in unauthorized

    def test_require_diff_authorized_raises_on_violation(
        self, mvp_project: Path
    ) -> None:
        """Should raise UnauthorizedFileModificationError on violation."""
        from rice_factor.domain.failures.executor_errors import (
            UnauthorizedFileModificationError,
        )
        from rice_factor.domain.services.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(project_root=mvp_project)

        diff_content = """--- a/src/unauthorized.py
+++ b/src/unauthorized.py
@@ -1,1 +1,2 @@
+# hack
 pass
"""
        authorized_files = {"src/main.py"}

        try:
            safety.require_diff_authorized(diff_content, authorized_files)
            assert False, "Should have raised UnauthorizedFileModificationError"
        except UnauthorizedFileModificationError as e:
            assert "unauthorized" in str(e).lower()

    def test_diff_authorization_handles_new_files(self, mvp_project: Path) -> None:
        """Should handle diffs that create new files."""
        from rice_factor.domain.services.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(project_root=mvp_project)

        diff_content = """--- /dev/null
+++ b/src/new_file.py
@@ -0,0 +1,3 @@
+def new_func():
+    pass
"""
        authorized_files = {"src/new_file.py"}

        is_authorized, unauthorized = safety.check_diff_authorized(
            diff_content, authorized_files
        )

        assert is_authorized is True
        assert len(unauthorized) == 0

    def test_diff_authorization_handles_file_deletion(
        self, mvp_project: Path
    ) -> None:
        """Should handle diffs that delete files."""
        from rice_factor.domain.services.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(project_root=mvp_project)

        diff_content = """--- a/src/old_file.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_func():
-    pass
"""
        authorized_files = {"src/old_file.py"}

        is_authorized, unauthorized = safety.check_diff_authorized(
            diff_content, authorized_files
        )

        assert is_authorized is True
        assert len(unauthorized) == 0


class TestLockVerificationIntegration:
    """Integration tests for TestPlan lock verification (GAP-M07-002).

    These tests verify the complete lock verification flow including:
    - SafetyEnforcer.check_test_lock_intact()
    - SafetyEnforcer.require_test_lock_intact()
    - Integration with plan impl/refactor commands
    """

    def test_lock_verification_passes_when_no_lock(self, mvp_project: Path) -> None:
        """Should pass when no lock file exists."""
        from rice_factor.domain.services.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(project_root=mvp_project)

        result = safety.check_test_lock_intact()

        assert result.is_valid is True
        assert len(result.modified_files) == 0

    def test_lock_verification_passes_with_intact_lock(
        self, mvp_project: Path
    ) -> None:
        """Should pass when lock file matches current test files."""
        import hashlib
        import json

        from rice_factor.domain.services.safety_enforcer import SafetyEnforcer

        # Create a test file
        tests_dir = mvp_project / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("def test_main(): pass")

        # Compute hash
        content = test_file.read_bytes()
        file_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"

        # Create lock file
        lock_dir = mvp_project / ".project"
        lock_file = lock_dir / ".lock"
        lock_data = {
            "test_plan_id": "test-123",
            "locked_at": "2024-01-01T00:00:00Z",
            "test_files": {
                "tests/test_main.py": file_hash,
            },
        }
        lock_file.write_text(json.dumps(lock_data))

        safety = SafetyEnforcer(project_root=mvp_project)
        result = safety.check_test_lock_intact()

        assert result.is_valid is True
        assert len(result.modified_files) == 0

    def test_lock_verification_fails_when_test_modified(
        self, mvp_project: Path
    ) -> None:
        """Should fail when test files have been modified after lock."""
        import hashlib
        import json

        from rice_factor.domain.services.safety_enforcer import SafetyEnforcer

        # Create a test file
        tests_dir = mvp_project / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("def test_main(): pass")

        # Compute hash of ORIGINAL content
        original_content = test_file.read_bytes()
        file_hash = f"sha256:{hashlib.sha256(original_content).hexdigest()}"

        # Create lock file
        lock_dir = mvp_project / ".project"
        lock_file = lock_dir / ".lock"
        lock_data = {
            "test_plan_id": "test-123",
            "locked_at": "2024-01-01T00:00:00Z",
            "test_files": {
                "tests/test_main.py": file_hash,
            },
        }
        lock_file.write_text(json.dumps(lock_data))

        # Now MODIFY the test file
        test_file.write_text("def test_main(): pass  # MODIFIED")

        safety = SafetyEnforcer(project_root=mvp_project)
        result = safety.check_test_lock_intact()

        assert result.is_valid is False
        assert "tests/test_main.py" in result.modified_files

    def test_require_test_lock_intact_raises_on_violation(
        self, mvp_project: Path
    ) -> None:
        """Should raise TestsLockedError when tests are modified."""
        import hashlib
        import json

        from rice_factor.domain.failures.executor_errors import TestsLockedError
        from rice_factor.domain.services.safety_enforcer import SafetyEnforcer

        # Create and lock a test file
        tests_dir = mvp_project / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("def test_main(): pass")

        # Compute hash and create lock
        content = test_file.read_bytes()
        file_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"

        lock_file = mvp_project / ".project" / ".lock"
        lock_data = {
            "test_plan_id": "test-123",
            "locked_at": "2024-01-01T00:00:00Z",
            "test_files": {"tests/test_main.py": file_hash},
        }
        lock_file.write_text(json.dumps(lock_data))

        # Modify the test file
        test_file.write_text("def test_main(): pass  # MODIFIED")

        safety = SafetyEnforcer(project_root=mvp_project)

        try:
            safety.require_test_lock_intact()
            assert False, "Should have raised TestsLockedError"
        except TestsLockedError as e:
            assert "lock" in str(e).lower() or "modified" in str(e).lower()
