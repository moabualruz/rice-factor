"""Tests for DiffExecutor."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from rice_factor.adapters.executors.audit_logger import AuditLogger
from rice_factor.adapters.executors.diff_executor import DiffExecutor
from rice_factor.domain.artifacts.enums import ArtifactStatus
from rice_factor.domain.artifacts.execution_types import ExecutionMode
from rice_factor.domain.ports.executor import ExecutorPort
from rice_factor.domain.services.diff_service import Diff, DiffService, DiffStatus


def create_diff(
    status: DiffStatus = DiffStatus.APPROVED,
    target_file: str = "src/main.py",
    content: str | None = None,
) -> Diff:
    """Create a diff for testing."""
    if content is None:
        content = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+# New comment
 def main():
     pass
"""
    return Diff(
        id=uuid4(),
        target_file=target_file,
        content=content,
        status=status,
        created_at=datetime.now(UTC),
        plan_id=uuid4(),
    )


class TestDiffExecutorProtocol:
    """Tests for DiffExecutor protocol compliance."""

    def test_implements_executor_port(self, tmp_path: Path) -> None:
        """DiffExecutor should implement ExecutorPort protocol."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )
        assert isinstance(executor, ExecutorPort)

    def test_has_execute_method(self, tmp_path: Path) -> None:
        """DiffExecutor should have execute method."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )
        assert hasattr(executor, "execute")


class TestDiffExecutorDryRun:
    """Tests for DRY_RUN mode."""

    def test_dry_run_uses_git_apply_check(self, tmp_path: Path) -> None:
        """DRY_RUN mode should use git apply --check."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        # Create a diff file
        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.DRY_RUN,
            )

            # Verify git apply was called with dry_run=True
            mock_git_apply.assert_called_once()
            _, kwargs = mock_git_apply.call_args
            assert kwargs.get("dry_run") is True or mock_git_apply.call_args[0][2] is True

    def test_dry_run_does_not_modify_files(self, tmp_path: Path) -> None:
        """DRY_RUN mode should not modify any files."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        # Create the source file and diff file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "main.py"
        src_file.write_text("def main():\n    pass\n")
        original_content = src_file.read_text()

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.DRY_RUN,
            )

        # File should remain unchanged
        assert src_file.read_text() == original_content

    def test_dry_run_logs_would_modify(self, tmp_path: Path) -> None:
        """DRY_RUN mode should log what would be modified."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            result = executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.DRY_RUN,
            )

        assert any("Would modify" in log or "would apply" in log.lower() for log in result.logs)


class TestDiffExecutorApply:
    """Tests for APPLY mode."""

    def test_apply_calls_git_apply(self, tmp_path: Path) -> None:
        """APPLY mode should call git apply."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

            # Verify git apply was called with dry_run=False
            mock_git_apply.assert_called_once()
            _, kwargs = mock_git_apply.call_args
            if "dry_run" in kwargs:
                assert kwargs["dry_run"] is False
            else:
                # Positional argument
                assert mock_git_apply.call_args[0][2] is False

    def test_apply_marks_diff_as_applied(self, tmp_path: Path) -> None:
        """APPLY mode should mark the diff as applied."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        # Name the file with the diff ID so it will be matched
        diff_file = tmp_path / f"{diff.id}.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

        diff_service.mark_applied.assert_called_once_with(diff.id)

    def test_apply_logs_modified_files(self, tmp_path: Path) -> None:
        """APPLY mode should log modified files."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            result = executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

        assert any("Modified" in log or "Applied" in log for log in result.logs)


class TestDiffExecutorApprovalValidation:
    """Tests for approval status validation."""

    def test_rejects_unapproved_diff(self, tmp_path: Path) -> None:
        """Should reject diffs that are not approved."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff(status=DiffStatus.PENDING)
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        # Name the file with the diff ID so it will be matched
        diff_file = tmp_path / f"{diff.id}.diff"
        diff_file.write_text(diff.content)

        result = executor.execute(
            artifact_path=diff_file,
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any("not approved" in error.lower() or "pending" in error.lower() for error in result.errors)

    def test_rejects_rejected_diff(self, tmp_path: Path) -> None:
        """Should reject diffs that have been rejected."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff(status=DiffStatus.REJECTED)
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        # Name the file with the diff ID so it will be matched
        diff_file = tmp_path / f"{diff.id}.diff"
        diff_file.write_text(diff.content)

        result = executor.execute(
            artifact_path=diff_file,
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any("not approved" in error.lower() or "rejected" in error.lower() for error in result.errors)


class TestDiffExecutorTestLock:
    """Tests for test lock check."""

    def test_rejects_test_file_modification_when_locked(self, tmp_path: Path) -> None:
        """Should reject diff modifying test files when tests are locked."""
        diff_service = MagicMock(spec=DiffService)
        # Diff that modifies a test file
        test_diff_content = """--- a/tests/test_main.py
+++ b/tests/test_main.py
@@ -1,3 +1,4 @@
+# New test
 def test_main():
     pass
"""
        diff = create_diff(
            target_file="tests/test_main.py",
            content=test_diff_content,
        )
        diff_service.list_diffs.return_value = [diff]

        # Mock storage that returns a locked TestPlan
        storage = MagicMock()
        locked_test_plan = MagicMock()
        locked_test_plan.status = ArtifactStatus.LOCKED
        storage.list_by_type.return_value = [locked_test_plan]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
            storage=storage,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(test_diff_content)

        result = executor.execute(
            artifact_path=diff_file,
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any("lock" in error.lower() or "test" in error.lower() for error in result.errors)

    def test_allows_test_file_modification_when_not_locked(self, tmp_path: Path) -> None:
        """Should allow diff modifying test files when tests are not locked."""
        diff_service = MagicMock(spec=DiffService)
        test_diff_content = """--- a/tests/test_main.py
+++ b/tests/test_main.py
@@ -1,3 +1,4 @@
+# New test
 def test_main():
     pass
"""
        diff = create_diff(
            target_file="tests/test_main.py",
            content=test_diff_content,
        )
        diff_service.list_diffs.return_value = [diff]

        # No locked TestPlan
        storage = MagicMock()
        storage.list_by_type.return_value = []

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
            storage=storage,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(test_diff_content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            result = executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

        assert result.success


class TestDiffExecutorGitApply:
    """Tests for git apply integration."""

    def test_handles_git_apply_failure(self, tmp_path: Path) -> None:
        """Should handle git apply failure gracefully."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (False, "error: patch does not apply")
            result = executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

        assert result.failure
        assert any("apply" in error.lower() or "patch" in error.lower() for error in result.errors)

    def test_git_apply_with_timeout(self, tmp_path: Path) -> None:
        """Should handle git apply timeout."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text("dummy diff content")

        with patch("subprocess.run") as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git apply", timeout=60)
            success, output = executor._git_apply(diff_file, tmp_path, dry_run=False)

        assert success is False
        assert "timed out" in output.lower()

    def test_git_apply_command_not_found(self, tmp_path: Path) -> None:
        """Should handle git command not found."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text("dummy diff content")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            success, output = executor._git_apply(diff_file, tmp_path, dry_run=False)

        assert success is False
        assert "not found" in output.lower()


class TestDiffParsing:
    """Tests for diff file parsing."""

    def test_parse_diff_files_standard_format(self, tmp_path: Path) -> None:
        """Should parse file paths from standard diff format."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_content = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+# comment
 def main():
     pass
"""
        files = executor._parse_diff_files(diff_content)
        assert "src/main.py" in files

    def test_parse_diff_files_new_file(self, tmp_path: Path) -> None:
        """Should parse new file creation."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_content = """--- /dev/null
+++ b/src/new_file.py
@@ -0,0 +1,3 @@
+def new_func():
+    pass
"""
        files = executor._parse_diff_files(diff_content)
        assert "src/new_file.py" in files
        assert "/dev/null" not in files

    def test_parse_diff_files_file_deletion(self, tmp_path: Path) -> None:
        """Should parse file deletion."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_content = """--- a/src/old_file.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_func():
-    pass
"""
        files = executor._parse_diff_files(diff_content)
        assert "src/old_file.py" in files
        assert "/dev/null" not in files

    def test_parse_diff_files_multiple_files(self, tmp_path: Path) -> None:
        """Should parse multiple files from diff."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_content = """--- a/src/file1.py
+++ b/src/file1.py
@@ -1,1 +1,2 @@
+# comment
 pass
--- a/src/file2.py
+++ b/src/file2.py
@@ -1,1 +1,2 @@
+# comment
 pass
"""
        files = executor._parse_diff_files(diff_content)
        assert "src/file1.py" in files
        assert "src/file2.py" in files
        assert len(files) == 2


class TestTestFileDetection:
    """Tests for test file detection."""

    def test_is_test_file_tests_directory(self, tmp_path: Path) -> None:
        """Should detect files in tests/ directory."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        assert executor._is_test_file("tests/test_main.py") is True
        assert executor._is_test_file("tests/unit/test_foo.py") is True
        assert executor._is_test_file("test/test_main.py") is True

    def test_is_test_file_test_prefix(self, tmp_path: Path) -> None:
        """Should detect test_*.py files."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        assert executor._is_test_file("test_main.py") is True
        assert executor._is_test_file("test_foo.py") is True

    def test_is_test_file_test_suffix(self, tmp_path: Path) -> None:
        """Should detect *_test.py files."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        assert executor._is_test_file("main_test.py") is True
        assert executor._is_test_file("foo_test.py") is True
        assert executor._is_test_file("bar_tests.py") is True

    def test_is_test_file_js_patterns(self, tmp_path: Path) -> None:
        """Should detect JavaScript/TypeScript test files."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        assert executor._is_test_file("main.test.js") is True
        assert executor._is_test_file("main.test.ts") is True
        assert executor._is_test_file("main.spec.js") is True
        assert executor._is_test_file("main.spec.tsx") is True

    def test_is_test_file_non_test(self, tmp_path: Path) -> None:
        """Should not detect non-test files."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        assert executor._is_test_file("src/main.py") is False
        assert executor._is_test_file("lib/utils.py") is False
        assert executor._is_test_file("app.js") is False

    def test_has_test_files(self, tmp_path: Path) -> None:
        """Should detect if any file is a test file."""
        diff_service = MagicMock(spec=DiffService)
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        assert executor._has_test_files(["src/main.py", "tests/test_main.py"]) is True
        assert executor._has_test_files(["src/main.py", "src/utils.py"]) is False


class TestDiffExecutorAuditLogging:
    """Tests for audit logging."""

    def test_generates_audit_log_entry_on_success(self, tmp_path: Path) -> None:
        """Should create audit log entry on success."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

        # Check audit log exists and has entry
        log_path = tmp_path / "audit" / "executions.log"
        assert log_path.exists()
        entries = audit_logger.read_all_entries()
        assert len(entries) >= 1
        assert entries[-1].executor == "diff"
        assert entries[-1].is_success

    def test_generates_audit_log_entry_on_failure(self, tmp_path: Path) -> None:
        """Should create audit log entry on failure."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff(status=DiffStatus.PENDING)
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        executor.execute(
            artifact_path=diff_file,
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        entries = audit_logger.read_all_entries()
        assert len(entries) >= 1
        assert entries[-1].is_failure


class TestDiffExecutorResult:
    """Tests for ExecutionResult."""

    def test_result_contains_diffs_list(self, tmp_path: Path) -> None:
        """Result should contain list of diff paths."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            result = executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

        assert isinstance(result.diffs, list)

    def test_result_contains_logs(self, tmp_path: Path) -> None:
        """Result should contain execution logs."""
        diff_service = MagicMock(spec=DiffService)
        diff = create_diff()
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff.content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            result = executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

        assert isinstance(result.logs, list)
        assert len(result.logs) > 0


class TestDiffExecutorWithoutStorage:
    """Tests for DiffExecutor without storage (test lock disabled)."""

    def test_allows_test_file_modification_without_storage(self, tmp_path: Path) -> None:
        """Should allow test file modification when no storage is provided."""
        diff_service = MagicMock(spec=DiffService)
        test_diff_content = """--- a/tests/test_main.py
+++ b/tests/test_main.py
@@ -1,3 +1,4 @@
+# New test
 def test_main():
     pass
"""
        diff = create_diff(
            target_file="tests/test_main.py",
            content=test_diff_content,
        )
        diff_service.list_diffs.return_value = [diff]

        audit_logger = AuditLogger(project_root=tmp_path)
        # No storage provided
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_file = tmp_path / "test.diff"
        diff_file.write_text(test_diff_content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            result = executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

        # Should succeed because no storage means no lock check
        assert result.success


class TestDiffExecutorDirectDiffFile:
    """Tests for executing diff directly from file (no DiffService match)."""

    def test_executes_diff_file_directly(self, tmp_path: Path) -> None:
        """Should execute diff file directly when no DiffService match."""
        diff_service = MagicMock(spec=DiffService)
        # No diffs in service
        diff_service.list_diffs.return_value = []

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = DiffExecutor(
            diff_service=diff_service,
            audit_logger=audit_logger,
        )

        diff_content = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+# New comment
 def main():
     pass
"""
        diff_file = tmp_path / "test.diff"
        diff_file.write_text(diff_content)

        with patch.object(executor, "_git_apply") as mock_git_apply:
            mock_git_apply.return_value = (True, "")
            result = executor.execute(
                artifact_path=diff_file,
                repo_root=tmp_path,
                mode=ExecutionMode.APPLY,
            )

        # Should succeed by reading diff directly from file
        assert result.success
