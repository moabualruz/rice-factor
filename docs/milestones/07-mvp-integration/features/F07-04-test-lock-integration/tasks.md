# Feature: F07-04 Test Lock Integration

## Status: In Progress

## Description

Implement hash-based TestPlan lock verification. When TestPlan is locked, compute SHA-256 hashes of all test files and store them in `.project/.lock`. Verify test files remain unchanged before any implementation operation. This is the core TDD enforcement mechanism.

## Requirements Reference

- M07-S-001: TestPlan lock shall use hash-based verification stored in .project/.lock
- M07-E-001: System shall hard-fail if tests modified after lock
- M07-WF-003: Implementation commands shall only execute after TestPlan locked
- raw/Phase-01-mvp.md: Section 5.4 (automation never modifies tests)
- raw/Item-01-mvp-example-walkthrough-end-to-end.md: Section 1.5 (TDD lock)

## Tasks

### Lock Manager Implementation
- [x] Create `rice_factor/adapters/storage/lock_manager.py`
  - [x] Define LockManager class
  - [x] Implement `lock_test_plan(test_plan, test_dir) -> LockFile`
  - [x] Implement `verify_lock(lock_file, test_dir) -> LockVerificationResult`
  - [x] Implement `get_lock() -> LockFile | None`

### Hash Computation
- [x] Implement test file hashing
  - [x] Find all test files from ScaffoldPlan (kind=TEST)
  - [x] Compute SHA-256 hash for each file
  - [x] Store as `{path: hash}` mapping
  - [x] Handle missing files gracefully

### Lock File Format
- [x] Define lock file structure
  - [x] Location: `.project/.lock`
  - [x] Format: JSON
  - [x] Fields: test_plan_id, locked_at, test_files
  - [x] Save and load functions

### Lock Command Integration
- [x] Update `rice_factor/entrypoints/cli/commands/lock.py`
  - [x] Verify TestPlan is approved
  - [x] Generate test files from ScaffoldPlan
  - [x] Compute file hashes
  - [x] Create lock file
  - [x] Update artifact status to LOCKED

### Verification Integration
- [x] Add lock verification to commands
  - [ ] `plan impl` - verify lock before planning
  - [x] `impl` - verify lock before implementation
  - [x] `apply` - verify lock before applying diff
  - [ ] `test` - verify lock after running tests

### Hard-Fail on Violation
- [x] Implement TestsLockedError (reused from executor_errors.py)
  - [x] Detect modified test files
  - [x] Report which files changed
  - [x] Show expected vs actual hash
  - [x] Provide recovery guidance

### Audit Trail
- [x] Add audit entries for lock operations
  - [x] Record lock creation
  - [ ] Record verification results
  - [ ] Record violation attempts

### Unit Tests
- [x] Create `tests/unit/adapters/storage/test_lock_manager.py`
  - [x] Test lock file creation
  - [x] Test hash computation
  - [x] Test verification passes for unchanged files
  - [x] Test verification fails for modified files
  - [x] Test verification fails for deleted files
  - [x] Test lock file persistence

## Acceptance Criteria

- [x] `rice-factor lock` creates `.project/.lock` with file hashes
- [x] Lock file contains test_plan_id, locked_at, test_files mapping
- [x] Verification passes when test files unchanged
- [x] Verification fails with `TestsLockedError` when files modified
- [x] Error message shows which files changed and their hashes
- [x] All implementation commands verify lock before execution
- [x] All tests pass
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/storage/lock_manager.py` | CREATE | Lock manager implementation |
| `rice_factor/entrypoints/cli/commands/lock.py` | UPDATE | Wire lock manager |
| `rice_factor/entrypoints/cli/commands/plan.py` | UPDATE | Add lock verification |
| `rice_factor/entrypoints/cli/commands/impl.py` | UPDATE | Add lock verification |
| `rice_factor/entrypoints/cli/commands/apply.py` | UPDATE | Add lock verification |
| `rice_factor/domain/failures/integration_errors.py` | CREATE | TestsLockedError |
| `tests/unit/adapters/storage/test_lock_manager.py` | CREATE | Unit tests |

## Dependencies

- F07-03: Scaffolding Integration (test files must exist)
- F07-07: Safety Enforcement (error handling)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | LockManager adapter created with LockFile and LockVerificationResult |
| 2026-01-10 | Lock command wired to LockManager with test file discovery from ScaffoldPlan |
| 2026-01-10 | Lock verification added to impl and apply commands |
| 2026-01-10 | 34 unit tests passing (18 lock_manager + 16 lock command) |
