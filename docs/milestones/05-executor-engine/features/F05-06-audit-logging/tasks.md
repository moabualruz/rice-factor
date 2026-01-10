# Feature: F05-06 Audit Logging

## Status: Complete

## Description

Implement the Audit Logger that records all executor actions to an append-only log file. Every execution must produce an audit entry with timestamp, executor name, artifact path, status, and diff location. No execution is valid without an audit log entry.

## Requirements Reference

- M05-AU-001: Audit Logger shall write JSON log entries to `audit/executions.log`
- M05-AU-002: Audit Logger shall record timestamp, executor name, artifact path, status
- M05-AU-003: Audit Logger shall record diff location for successful executions
- M05-AU-004: Audit Logger shall be append-only
- M05-AU-005: If no audit log written, then execution shall be considered invalid
- M05-U-005: Executors shall log every action to the audit trail
- raw/item-02-executor-design-and-pseudocode.md: Section 2.10 Audit Logging

## Tasks

### Audit Log Entry Model
- [x] Create `rice_factor/domain/artifacts/audit_types.py`
  - [x] Define `AuditLogEntry` dataclass
    - [x] `timestamp: datetime` (ISO-8601)
    - [x] `executor: str` (executor name)
    - [x] `artifact: str` (artifact path)
    - [x] `status: Literal["success", "failure"]`
    - [x] `mode: str` (dry_run or apply)
    - [x] `diff: str | None` (diff path if successful)
    - [x] `files_affected: list[str]`
    - [x] `duration_ms: int`
    - [x] `error: str | None` (error message if failed)
  - [x] Implement `to_json() -> str`
    - [x] Serialize to single-line JSON
  - [x] Implement `from_json(json_str: str) -> AuditLogEntry`
    - [x] Deserialize from JSON

### Audit Logger Class
- [x] Create `rice_factor/adapters/executors/audit_logger.py`
  - [x] Define `AuditLogger` class
  - [x] Implement `__init__(project_root: Path)`
    - [x] Set audit directory path
    - [x] Ensure directory exists
  - [x] Implement `log_execution(entry: AuditLogEntry) -> None`
    - [x] Append entry to executions.log
    - [x] Use file locking for concurrent access
  - [x] Implement `log_success(...) -> AuditLogEntry`
    - [x] Create success entry
    - [x] Call log_execution
    - [x] Return entry
  - [x] Implement `log_failure(...) -> AuditLogEntry`
    - [x] Create failure entry
    - [x] Call log_execution
    - [x] Return entry

### Append-Only File Operations
- [x] Implement `_append_log(log_path: Path, entry: str) -> None`
  - [x] Open file in append mode
  - [x] Write JSON line
  - [x] Flush to disk
- [x] Implement `_ensure_directory(path: Path) -> None`
  - [x] Create audit directory if not exists

### Diff File Management
- [x] Implement `save_diff(content: str, executor: str) -> Path`
  - [x] Generate filename with timestamp and executor name
  - [x] Save to audit/diffs/
  - [x] Return path for logging
- [x] Implement `_generate_diff_filename(executor: str) -> str`
  - [x] Format: `YYYYMMDD_HHMMSS_<executor>.diff`

### Log Reading (for debugging/display)
- [x] Implement `read_recent_entries(limit: int = 10) -> list[AuditLogEntry]`
  - [x] Read last N entries from log
  - [x] Parse JSON lines
- [x] Implement `read_entries_for_artifact(artifact_path: str) -> list[AuditLogEntry]`
  - [x] Filter entries by artifact path

### Context Manager for Timing
- [x] Implement `execution_timer` context manager
  - [x] Record start time on enter
  - [x] Calculate duration on exit
  - [x] Provide duration_ms for logging

### Type Exports
- [x] Update `rice_factor/domain/artifacts/__init__.py`
  - [x] Export `AuditLogEntry`
- [x] Update `rice_factor/adapters/executors/__init__.py`
  - [x] Export `AuditLogger`

### Unit Tests
- [x] Create `tests/unit/domain/artifacts/test_audit_types.py`
  - [x] Test AuditLogEntry creation
  - [x] Test to_json serialization
  - [x] Test from_json deserialization
  - [x] Test timestamp is ISO-8601 format
- [x] Create `tests/unit/adapters/executors/test_audit_logger.py`
  - [x] Test log_execution appends to file
  - [x] Test log_success creates correct entry
  - [x] Test log_failure creates correct entry
  - [x] Test multiple entries are appended
  - [x] Test save_diff creates file with correct name
  - [x] Test read_recent_entries returns correct count
  - [x] Test read_entries_for_artifact filters correctly
  - [x] Test execution_timer calculates duration

### Integration Tests
- [x] Create `tests/integration/adapters/executors/test_audit_logger_file.py`
  - [x] Test creates audit directory if missing
  - [x] Test handles concurrent writes (multiprocessing)
  - [x] Test log file grows correctly
  - [x] Test log survives process restart

## Acceptance Criteria

- [x] AuditLogEntry dataclass defined with all required fields
- [x] JSON serialization produces single-line output
- [x] Log entries appended to audit/executions.log
- [x] Diff files saved to audit/diffs/
- [x] Timestamp in ISO-8601 format with milliseconds
- [x] Duration tracked accurately
- [x] Append-only behavior enforced
- [x] Log reading works for debugging
- [x] All tests pass
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/domain/artifacts/audit_types.py` | CREATE | AuditLogEntry dataclass |
| `rice_factor/adapters/executors/audit_logger.py` | CREATE | AuditLogger class |
| `rice_factor/domain/artifacts/__init__.py` | UPDATE | Export AuditLogEntry |
| `rice_factor/adapters/executors/__init__.py` | UPDATE | Export AuditLogger |
| `tests/unit/domain/artifacts/test_audit_types.py` | CREATE | Audit types tests |
| `tests/unit/adapters/executors/test_audit_logger.py` | CREATE | Logger unit tests |
| `tests/integration/adapters/executors/test_audit_logger_file.py` | CREATE | Logger integration tests |

## Dependencies

- F05-01: Executor Base Interface (ExecutionResult for status)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - all tasks implemented |
