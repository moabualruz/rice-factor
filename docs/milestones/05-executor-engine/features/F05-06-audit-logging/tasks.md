# Feature: F05-06 Audit Logging

## Status: Pending

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
- [ ] Create `rice_factor/domain/artifacts/audit_types.py`
  - [ ] Define `AuditLogEntry` dataclass
    - [ ] `timestamp: datetime` (ISO-8601)
    - [ ] `executor: str` (executor name)
    - [ ] `artifact: str` (artifact path)
    - [ ] `status: Literal["success", "failure"]`
    - [ ] `mode: str` (dry_run or apply)
    - [ ] `diff: str | None` (diff path if successful)
    - [ ] `files_affected: list[str]`
    - [ ] `duration_ms: int`
    - [ ] `error: str | None` (error message if failed)
  - [ ] Implement `to_json() -> str`
    - [ ] Serialize to single-line JSON
  - [ ] Implement `from_json(json_str: str) -> AuditLogEntry`
    - [ ] Deserialize from JSON

### Audit Logger Class
- [ ] Create `rice_factor/adapters/executors/audit_logger.py`
  - [ ] Define `AuditLogger` class
  - [ ] Implement `__init__(project_root: Path)`
    - [ ] Set audit directory path
    - [ ] Ensure directory exists
  - [ ] Implement `log_execution(entry: AuditLogEntry) -> None`
    - [ ] Append entry to executions.log
    - [ ] Use file locking for concurrent access
  - [ ] Implement `log_success(...) -> AuditLogEntry`
    - [ ] Create success entry
    - [ ] Call log_execution
    - [ ] Return entry
  - [ ] Implement `log_failure(...) -> AuditLogEntry`
    - [ ] Create failure entry
    - [ ] Call log_execution
    - [ ] Return entry

### Append-Only File Operations
- [ ] Implement `_append_log(log_path: Path, entry: str) -> None`
  - [ ] Open file in append mode
  - [ ] Write JSON line
  - [ ] Flush to disk
- [ ] Implement `_ensure_directory(path: Path) -> None`
  - [ ] Create audit directory if not exists

### Diff File Management
- [ ] Implement `save_diff(content: str, executor: str) -> Path`
  - [ ] Generate filename with timestamp and executor name
  - [ ] Save to audit/diffs/
  - [ ] Return path for logging
- [ ] Implement `_generate_diff_filename(executor: str) -> str`
  - [ ] Format: `YYYYMMDD_HHMMSS_<executor>.diff`

### Log Reading (for debugging/display)
- [ ] Implement `read_recent_entries(limit: int = 10) -> list[AuditLogEntry]`
  - [ ] Read last N entries from log
  - [ ] Parse JSON lines
- [ ] Implement `read_entries_for_artifact(artifact_path: str) -> list[AuditLogEntry]`
  - [ ] Filter entries by artifact path

### Context Manager for Timing
- [ ] Implement `execution_timer` context manager
  - [ ] Record start time on enter
  - [ ] Calculate duration on exit
  - [ ] Provide duration_ms for logging

### Type Exports
- [ ] Update `rice_factor/domain/artifacts/__init__.py`
  - [ ] Export `AuditLogEntry`
- [ ] Update `rice_factor/adapters/executors/__init__.py`
  - [ ] Export `AuditLogger`

### Unit Tests
- [ ] Create `tests/unit/domain/artifacts/test_audit_types.py`
  - [ ] Test AuditLogEntry creation
  - [ ] Test to_json serialization
  - [ ] Test from_json deserialization
  - [ ] Test timestamp is ISO-8601 format
- [ ] Create `tests/unit/adapters/executors/test_audit_logger.py`
  - [ ] Test log_execution appends to file
  - [ ] Test log_success creates correct entry
  - [ ] Test log_failure creates correct entry
  - [ ] Test multiple entries are appended
  - [ ] Test save_diff creates file with correct name
  - [ ] Test read_recent_entries returns correct count
  - [ ] Test read_entries_for_artifact filters correctly
  - [ ] Test execution_timer calculates duration

### Integration Tests
- [ ] Create `tests/integration/adapters/executors/test_audit_logger_file.py`
  - [ ] Test creates audit directory if missing
  - [ ] Test handles concurrent writes (multiprocessing)
  - [ ] Test log file grows correctly
  - [ ] Test log survives process restart

## Acceptance Criteria

- [ ] AuditLogEntry dataclass defined with all required fields
- [ ] JSON serialization produces single-line output
- [ ] Log entries appended to audit/executions.log
- [ ] Diff files saved to audit/diffs/
- [ ] Timestamp in ISO-8601 format with milliseconds
- [ ] Duration tracked accurately
- [ ] Append-only behavior enforced
- [ ] Log reading works for debugging
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

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
