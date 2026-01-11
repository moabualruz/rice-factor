"""Tests for AuditLogger."""

import json
import time
from pathlib import Path

import pytest

from rice_factor.adapters.executors.audit_logger import (
    AuditLogger,
    AuditLoggerError,
    execution_timer,
)
from rice_factor.domain.artifacts.audit_types import AuditLogEntry


class TestAuditLoggerInit:
    """Tests for AuditLogger initialization."""

    def test_creates_audit_directory(self, tmp_path: Path) -> None:
        """Should create audit directory if not exists."""
        AuditLogger(project_root=tmp_path)
        assert (tmp_path / "audit").exists()
        assert (tmp_path / "audit").is_dir()

    def test_creates_diffs_directory(self, tmp_path: Path) -> None:
        """Should create audit/diffs directory."""
        AuditLogger(project_root=tmp_path)
        assert (tmp_path / "audit" / "diffs").exists()

    def test_sets_paths_correctly(self, tmp_path: Path) -> None:
        """Should set path attributes correctly."""
        logger = AuditLogger(project_root=tmp_path)
        assert logger.project_root == tmp_path
        assert logger.audit_dir == tmp_path / "audit"
        assert logger.log_path == tmp_path / "audit" / "executions.log"
        assert logger.diffs_dir == tmp_path / "audit" / "diffs"


class TestAuditLoggerLogExecution:
    """Tests for log_execution method."""

    def test_appends_to_log_file(self, tmp_path: Path) -> None:
        """Should append entry to log file."""
        logger = AuditLogger(project_root=tmp_path)
        entry = AuditLogEntry.success(
            executor="scaffold",
            artifact="test.json",
            mode="apply",
        )
        logger.log_execution(entry)

        assert logger.log_path.exists()
        content = logger.log_path.read_text()
        assert "scaffold" in content

    def test_multiple_entries_on_separate_lines(self, tmp_path: Path) -> None:
        """Should put each entry on its own line."""
        logger = AuditLogger(project_root=tmp_path)

        entry1 = AuditLogEntry.success(
            executor="scaffold",
            artifact="test1.json",
            mode="apply",
        )
        entry2 = AuditLogEntry.success(
            executor="diff",
            artifact="test2.json",
            mode="apply",
        )

        logger.log_execution(entry1)
        logger.log_execution(entry2)

        lines = logger.log_path.read_text().strip().split("\n")
        assert len(lines) == 2
        assert "scaffold" in lines[0]
        assert "diff" in lines[1]

    def test_entries_are_valid_json(self, tmp_path: Path) -> None:
        """Should write valid JSON on each line."""
        logger = AuditLogger(project_root=tmp_path)
        entry = AuditLogEntry.success(
            executor="scaffold",
            artifact="test.json",
            mode="apply",
        )
        logger.log_execution(entry)

        lines = logger.log_path.read_text().strip().split("\n")
        for line in lines:
            parsed = json.loads(line)
            assert "executor" in parsed


class TestAuditLoggerLogSuccess:
    """Tests for log_success method."""

    def test_creates_success_entry(self, tmp_path: Path) -> None:
        """Should create a success entry."""
        logger = AuditLogger(project_root=tmp_path)
        entry = logger.log_success(
            executor="scaffold",
            artifact="test.json",
            mode="apply",
            diff_path="audit/diffs/test.diff",
            files_affected=["a.py"],
            duration_ms=100,
        )

        assert entry.is_success
        assert entry.executor == "scaffold"
        assert entry.diff == "audit/diffs/test.diff"

    def test_writes_to_file(self, tmp_path: Path) -> None:
        """Should write entry to file."""
        logger = AuditLogger(project_root=tmp_path)
        logger.log_success(
            executor="scaffold",
            artifact="test.json",
            mode="apply",
        )

        assert logger.log_path.exists()
        content = logger.log_path.read_text()
        assert "success" in content

    def test_returns_entry(self, tmp_path: Path) -> None:
        """Should return the created entry."""
        logger = AuditLogger(project_root=tmp_path)
        entry = logger.log_success(
            executor="scaffold",
            artifact="test.json",
            mode="apply",
        )

        assert isinstance(entry, AuditLogEntry)


class TestAuditLoggerLogFailure:
    """Tests for log_failure method."""

    def test_creates_failure_entry(self, tmp_path: Path) -> None:
        """Should create a failure entry."""
        logger = AuditLogger(project_root=tmp_path)
        entry = logger.log_failure(
            executor="diff",
            artifact="test.json",
            mode="apply",
            error="Test error",
        )

        assert entry.is_failure
        assert entry.error == "Test error"

    def test_writes_to_file(self, tmp_path: Path) -> None:
        """Should write entry to file."""
        logger = AuditLogger(project_root=tmp_path)
        logger.log_failure(
            executor="diff",
            artifact="test.json",
            mode="apply",
            error="Test error",
        )

        content = logger.log_path.read_text()
        assert "failure" in content
        assert "Test error" in content


class TestAuditLoggerSaveDiff:
    """Tests for save_diff method."""

    def test_saves_diff_file(self, tmp_path: Path) -> None:
        """Should save diff content to file."""
        logger = AuditLogger(project_root=tmp_path)
        diff_content = "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new"

        path = logger.save_diff(diff_content, "scaffold")

        full_path = tmp_path / path
        assert full_path.exists()
        assert full_path.read_text() == diff_content

    def test_returns_relative_path(self, tmp_path: Path) -> None:
        """Should return path relative to project root."""
        logger = AuditLogger(project_root=tmp_path)
        path = logger.save_diff("diff content", "scaffold")

        assert path.startswith("audit")
        assert "diffs" in path
        assert path.endswith(".diff")

    def test_filename_includes_executor(self, tmp_path: Path) -> None:
        """Should include executor name in filename."""
        logger = AuditLogger(project_root=tmp_path)
        path = logger.save_diff("diff content", "scaffold")

        assert "scaffold" in path

    def test_unique_filenames(self, tmp_path: Path) -> None:
        """Should generate unique filenames."""
        logger = AuditLogger(project_root=tmp_path)

        path1 = logger.save_diff("diff 1", "scaffold")
        # Small delay to ensure different timestamp
        time.sleep(0.001)
        path2 = logger.save_diff("diff 2", "scaffold")

        assert path1 != path2


class TestAuditLoggerReadRecentEntries:
    """Tests for read_recent_entries method."""

    def test_returns_empty_for_new_log(self, tmp_path: Path) -> None:
        """Should return empty list if no log file."""
        logger = AuditLogger(project_root=tmp_path)
        entries = logger.read_recent_entries()
        assert entries == []

    def test_returns_entries_newest_first(self, tmp_path: Path) -> None:
        """Should return entries with newest first."""
        logger = AuditLogger(project_root=tmp_path)

        logger.log_success(executor="first", artifact="1.json", mode="apply")
        logger.log_success(executor="second", artifact="2.json", mode="apply")
        logger.log_success(executor="third", artifact="3.json", mode="apply")

        entries = logger.read_recent_entries(limit=3)

        assert len(entries) == 3
        assert entries[0].executor == "third"
        assert entries[1].executor == "second"
        assert entries[2].executor == "first"

    def test_respects_limit(self, tmp_path: Path) -> None:
        """Should only return up to limit entries."""
        logger = AuditLogger(project_root=tmp_path)

        for i in range(5):
            logger.log_success(executor=f"exec{i}", artifact=f"{i}.json", mode="apply")

        entries = logger.read_recent_entries(limit=2)
        assert len(entries) == 2

    def test_default_limit_is_10(self, tmp_path: Path) -> None:
        """Should default to 10 entries."""
        logger = AuditLogger(project_root=tmp_path)

        for i in range(15):
            logger.log_success(executor=f"exec{i}", artifact=f"{i}.json", mode="apply")

        entries = logger.read_recent_entries()
        assert len(entries) == 10


class TestAuditLoggerReadEntriesForArtifact:
    """Tests for read_entries_for_artifact method."""

    def test_filters_by_artifact(self, tmp_path: Path) -> None:
        """Should only return entries for specified artifact."""
        logger = AuditLogger(project_root=tmp_path)

        logger.log_success(executor="exec1", artifact="a.json", mode="apply")
        logger.log_success(executor="exec2", artifact="b.json", mode="apply")
        logger.log_success(executor="exec3", artifact="a.json", mode="apply")

        entries = logger.read_entries_for_artifact("a.json")

        assert len(entries) == 2
        assert all(e.artifact == "a.json" for e in entries)

    def test_returns_oldest_first(self, tmp_path: Path) -> None:
        """Should return entries in chronological order."""
        logger = AuditLogger(project_root=tmp_path)

        logger.log_success(executor="first", artifact="a.json", mode="apply")
        logger.log_success(executor="second", artifact="a.json", mode="apply")

        entries = logger.read_entries_for_artifact("a.json")

        assert entries[0].executor == "first"
        assert entries[1].executor == "second"

    def test_returns_empty_for_unknown_artifact(self, tmp_path: Path) -> None:
        """Should return empty list for unknown artifact."""
        logger = AuditLogger(project_root=tmp_path)
        logger.log_success(executor="exec", artifact="a.json", mode="apply")

        entries = logger.read_entries_for_artifact("unknown.json")
        assert entries == []


class TestAuditLoggerReadAllEntries:
    """Tests for read_all_entries method."""

    def test_returns_all_entries(self, tmp_path: Path) -> None:
        """Should return all entries."""
        logger = AuditLogger(project_root=tmp_path)

        for i in range(5):
            logger.log_success(executor=f"exec{i}", artifact=f"{i}.json", mode="apply")

        entries = logger.read_all_entries()
        assert len(entries) == 5

    def test_returns_oldest_first(self, tmp_path: Path) -> None:
        """Should return entries in chronological order."""
        logger = AuditLogger(project_root=tmp_path)

        logger.log_success(executor="first", artifact="1.json", mode="apply")
        logger.log_success(executor="second", artifact="2.json", mode="apply")

        entries = logger.read_all_entries()
        assert entries[0].executor == "first"
        assert entries[1].executor == "second"


class TestExecutionTimer:
    """Tests for execution_timer context manager."""

    def test_calculates_duration(self) -> None:
        """Should calculate execution duration."""
        with execution_timer() as timer:
            time.sleep(0.01)  # 10ms

        # Should be at least 10ms
        assert timer["duration_ms"] >= 10

    def test_duration_in_milliseconds(self) -> None:
        """Should return duration in milliseconds."""
        with execution_timer() as timer:
            time.sleep(0.1)  # 100ms

        # Should be roughly 100ms (allow some variance)
        assert 90 <= timer["duration_ms"] <= 200

    def test_zero_duration_for_instant(self) -> None:
        """Should handle very fast operations."""
        with execution_timer() as timer:
            pass  # Almost instant

        # Should be a non-negative integer
        assert timer["duration_ms"] >= 0
        assert isinstance(timer["duration_ms"], int)

    def test_timer_survives_exception(self) -> None:
        """Should record duration even if exception occurs."""
        timer_result: dict[str, int] = {}

        with pytest.raises(ValueError), execution_timer() as timer:
            timer_result = timer
            time.sleep(0.01)
            raise ValueError("test error")

        assert timer_result["duration_ms"] >= 10


class TestAuditLoggerError:
    """Tests for AuditLoggerError exception."""

    def test_error_is_exception(self) -> None:
        """AuditLoggerError should be an Exception."""
        assert issubclass(AuditLoggerError, Exception)

    def test_error_message_preserved(self) -> None:
        """Should preserve error message."""
        error = AuditLoggerError("Test error message")
        assert str(error) == "Test error message"
