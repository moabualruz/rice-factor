"""Audit Logger for executor operations.

This module provides the AuditLogger class that records all executor actions
to an append-only log file. Every execution must produce an audit entry.

Example:
    >>> logger = AuditLogger(project_root=Path("."))
    >>> entry = logger.log_success(
    ...     executor="scaffold",
    ...     artifact="artifacts/scaffold_plan.json",
    ...     mode="apply",
    ...     diff_path="audit/diffs/20260110_120000_scaffold.diff",
    ...     files_affected=["src/user.py"],
    ...     duration_ms=150,
    ... )
"""

from __future__ import annotations

import contextlib
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

from rice_factor.domain.artifacts.audit_types import AuditLogEntry


class AuditLoggerError(Exception):
    """Raised when audit logging operations fail."""

    pass


class AuditLogger:
    """Logger for executor audit trail.

    Records all executor actions to an append-only log file at
    `audit/executions.log`. Every execution produces an audit entry
    that is immediately persisted to disk.

    Attributes:
        project_root: Path to the project root directory.
        audit_dir: Path to the audit directory.
        log_path: Path to the executions.log file.
        diffs_dir: Path to the diffs directory.
    """

    LOG_FILENAME = "executions.log"
    DIFFS_DIRNAME = "diffs"

    def __init__(self, project_root: Path) -> None:
        """Initialize the audit logger.

        Args:
            project_root: Path to the project root directory.
                The audit directory will be at `project_root/audit/`.
        """
        # Import Path at runtime to avoid TYPE_CHECKING issues
        from pathlib import Path as PathClass

        self.project_root = PathClass(project_root)
        self.audit_dir = self.project_root / "audit"
        self.log_path = self.audit_dir / self.LOG_FILENAME
        self.diffs_dir = self.audit_dir / self.DIFFS_DIRNAME

        # Ensure directories exist
        self._ensure_directory(self.audit_dir)
        self._ensure_directory(self.diffs_dir)

    def _ensure_directory(self, path: Path) -> None:
        """Ensure a directory exists, creating it if necessary.

        Args:
            path: Directory path to ensure.
        """
        from pathlib import Path as PathClass

        PathClass(path).mkdir(parents=True, exist_ok=True)

    def log_execution(self, entry: AuditLogEntry) -> None:
        """Append an audit log entry to the log file.

        Args:
            entry: The audit log entry to record.

        Raises:
            AuditLoggerError: If the log entry cannot be written.
        """
        try:
            self._append_log(self.log_path, entry.to_json())
        except OSError as e:
            raise AuditLoggerError(f"Failed to write audit log: {e}") from e

    def _append_log(self, log_path: Path, entry_json: str) -> None:
        """Append a JSON line to the log file.

        Args:
            log_path: Path to the log file.
            entry_json: JSON string to append.
        """
        from pathlib import Path as PathClass

        with PathClass(log_path).open("a", encoding="utf-8") as f:
            f.write(entry_json + "\n")
            f.flush()

    def log_success(
        self,
        executor: str,
        artifact: str,
        mode: str,
        diff_path: str | None = None,
        files_affected: list[str] | None = None,
        duration_ms: int = 0,
    ) -> AuditLogEntry:
        """Create and log a success audit entry.

        Args:
            executor: Name of the executor.
            artifact: Path to the executed artifact.
            mode: Execution mode (dry_run or apply).
            diff_path: Path to the generated diff file.
            files_affected: List of affected file paths.
            duration_ms: Execution duration in milliseconds.

        Returns:
            The created and logged AuditLogEntry.
        """
        entry = AuditLogEntry.success(
            executor=executor,
            artifact=artifact,
            mode=mode,
            diff=diff_path,
            files_affected=files_affected,
            duration_ms=duration_ms,
        )
        self.log_execution(entry)
        return entry

    def log_failure(
        self,
        executor: str,
        artifact: str,
        mode: str,
        error: str,
        files_affected: list[str] | None = None,
        duration_ms: int = 0,
    ) -> AuditLogEntry:
        """Create and log a failure audit entry.

        Args:
            executor: Name of the executor.
            artifact: Path to the executed artifact.
            mode: Execution mode (dry_run or apply).
            error: Error message describing the failure.
            files_affected: List of affected file paths.
            duration_ms: Execution duration in milliseconds.

        Returns:
            The created and logged AuditLogEntry.
        """
        entry = AuditLogEntry.failure(
            executor=executor,
            artifact=artifact,
            mode=mode,
            error=error,
            files_affected=files_affected,
            duration_ms=duration_ms,
        )
        self.log_execution(entry)
        return entry

    def save_diff(self, content: str, executor: str) -> str:
        """Save diff content to a file.

        Args:
            content: The diff content to save.
            executor: Name of the executor for filename.

        Returns:
            Path to the saved diff file (relative to project root).

        Raises:
            AuditLoggerError: If the diff cannot be saved.
        """
        from pathlib import Path as PathClass

        filename = self._generate_diff_filename(executor)
        diff_path = self.diffs_dir / filename

        try:
            PathClass(diff_path).write_text(content, encoding="utf-8")
        except OSError as e:
            raise AuditLoggerError(f"Failed to save diff: {e}") from e

        # Return relative path from project root
        return str(diff_path.relative_to(self.project_root))

    def _generate_diff_filename(self, executor: str) -> str:
        """Generate a unique diff filename.

        Args:
            executor: Name of the executor.

        Returns:
            Filename in format: YYYYMMDD_HHMMSS_<executor>.diff
        """
        now = datetime.now(UTC)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        # Add microseconds for uniqueness
        micros = f"{now.microsecond:06d}"
        return f"{timestamp}_{micros}_{executor}.diff"

    def read_recent_entries(self, limit: int = 10) -> list[AuditLogEntry]:
        """Read the most recent audit log entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of the most recent entries, newest first.
        """
        if not self.log_path.exists():
            return []

        entries: list[AuditLogEntry] = []
        lines = self.log_path.read_text(encoding="utf-8").strip().split("\n")

        # Read from end, up to limit
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                entry = AuditLogEntry.from_json(line)
                entries.append(entry)
                if len(entries) >= limit:
                    break
            except (ValueError, KeyError):
                # Skip malformed entries
                continue

        return entries

    def read_entries_for_artifact(self, artifact_path: str) -> list[AuditLogEntry]:
        """Read all audit log entries for a specific artifact.

        Args:
            artifact_path: Path to the artifact to filter by.

        Returns:
            List of entries for the artifact, oldest first.
        """
        if not self.log_path.exists():
            return []

        entries: list[AuditLogEntry] = []
        lines = self.log_path.read_text(encoding="utf-8").strip().split("\n")

        for line in lines:
            if not line.strip():
                continue
            try:
                entry = AuditLogEntry.from_json(line)
                if entry.artifact == artifact_path:
                    entries.append(entry)
            except (ValueError, KeyError):
                # Skip malformed entries
                continue

        return entries

    def read_all_entries(self) -> list[AuditLogEntry]:
        """Read all audit log entries.

        Returns:
            List of all entries, oldest first.
        """
        if not self.log_path.exists():
            return []

        entries: list[AuditLogEntry] = []
        lines = self.log_path.read_text(encoding="utf-8").strip().split("\n")

        for line in lines:
            if not line.strip():
                continue
            try:
                entry = AuditLogEntry.from_json(line)
                entries.append(entry)
            except (ValueError, KeyError):
                # Skip malformed entries
                continue

        return entries


@contextlib.contextmanager
def execution_timer() -> Iterator[dict[str, int]]:
    """Context manager for timing executor operations.

    Yields a dictionary that will contain 'duration_ms' after the context exits.

    Example:
        >>> with execution_timer() as timer:
        ...     do_something()
        >>> print(f"Took {timer['duration_ms']}ms")

    Yields:
        Dictionary with 'duration_ms' key set after context exit.
    """
    result: dict[str, int] = {"duration_ms": 0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        end = time.perf_counter()
        result["duration_ms"] = int((end - start) * 1000)
