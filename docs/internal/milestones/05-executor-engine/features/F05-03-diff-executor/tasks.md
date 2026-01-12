# Feature: F05-03 Diff Executor

## Status: Complete

## Description

Implement the Diff Executor adapter that applies approved diffs to the codebase using git apply. This executor only applies diffs - it never generates them. The diff must be pre-approved and the executor verifies all preconditions before application.

## Requirements Reference

- M05-DI-001: Diff Executor shall accept approved diff files only
- M05-DI-002: Diff Executor shall use git apply to apply patches
- M05-DI-003: Diff Executor shall verify diff touches only declared files
- M05-DI-004: Diff Executor shall not generate diffs (only apply them)
- M05-DI-005: If patch fails to apply, then Diff Executor shall fail with details
- M05-S-001: While in DRY_RUN mode, executors shall generate diff without applying
- M05-S-002: While tests are locked, executors shall reject any test file modifications
- M05-I-002: If artifact is not approved, then executor shall reject it
- M05-I-004: If diff touches unauthorized files, then executor shall reject the diff
- raw/item-02-executor-design-and-pseudocode.md: Section 2.6 Diff Executor

## Tasks

### Diff Executor Adapter
- [x] Create `rice_factor/adapters/executors/diff_executor.py`
  - [x] Define `DiffExecutor` class implementing `ExecutorPort`
  - [x] Implement `__init__(storage: StoragePort)`
  - [x] Implement `execute(diff_path, repo_root, mode) -> ExecutionResult`

### 9-Step Pipeline Implementation
- [x] Implement Step 1: Load diff
  - [x] Load Diff from diff_path using DiffService
  - [x] Verify diff file exists
- [x] Implement Step 2: Validate diff format
  - [x] Ensure valid unified diff format
  - [x] Parse touched files from diff
- [x] Implement Step 3: Verify approval status
  - [x] Check diff.status == APPROVED
  - [x] Raise `ArtifactNotApprovedError` if not approved
- [x] Implement Step 4: Capability check
  - [x] N/A for diff (always supported)
- [x] Implement Step 5: Precondition checks
  - [x] Check diff touches only authorized files
  - [x] Check tests are not modified if locked
  - [x] Check no binary files in diff
- [x] Implement Step 6: N/A (diff is input, not generated)
- [x] Implement Step 7: Apply (if APPLY mode)
  - [x] Run `git apply` with diff
  - [x] Capture exit code and output
  - [x] Raise `GitApplyError` on failure
- [x] Implement Step 8: Emit audit logs
  - [x] Call AuditLogger with execution details
- [x] Implement Step 9: Return result
  - [x] Build ExecutionResult with status, diffs, errors, logs

### Git Apply Integration
- [x] Implement `_git_apply(diff_path: Path, repo_root: Path, dry_run: bool) -> tuple[bool, str]`
  - [x] Run `git apply --check` for dry run
  - [x] Run `git apply` for actual application
  - [x] Capture stdout/stderr
  - [x] Return (success, output)
- [x] Implement `_parse_git_apply_error(output: str) -> str`
  - [x] Extract meaningful error message from git output

### Diff Parsing
- [x] Implement `_parse_diff_files(diff_content: str) -> list[str]`
  - [x] Extract file paths from diff headers (--- a/... +++ b/...)
  - [x] Handle new file creation
  - [x] Handle file deletion

### Test File Lock Check
- [x] Implement `_check_test_lock(files: list[str], storage: StoragePort) -> bool`
  - [x] Check if TestPlan is locked
  - [x] Return True if any test file is in the diff
- [x] Implement `_is_test_file(path: str) -> bool`
  - [x] Pattern matching for test files (test_*.py, *_test.py, tests/, etc.)

### Adapter Exports
- [x] Update `rice_factor/adapters/executors/__init__.py`
  - [x] Export `DiffExecutor`

### Unit Tests
- [x] Create `tests/unit/adapters/executors/test_diff_executor.py`
  - [x] Test executor implements ExecutorPort protocol
  - [x] Test DRY_RUN mode uses git apply --check
  - [x] Test APPLY mode applies diff
  - [x] Test rejects unapproved diff
  - [x] Test rejects diff touching test files when locked
  - [x] Test rejects diff with unauthorized files
  - [x] Test handles git apply failure gracefully
  - [x] Test parses diff file paths correctly
  - [x] Test generates audit log entry
  - [x] Test ExecutionResult contains correct status

### Integration Tests
- [x] Create `tests/integration/adapters/executors/test_diff_executor_git.py`
  - [x] Test with real git repository (use tmp_path)
  - [x] Test applying valid diff
  - [x] Test applying conflicting diff
  - [x] Test git apply --check works correctly

## Acceptance Criteria

- [x] DiffExecutor implements ExecutorPort protocol
- [x] Full 9-step pipeline implemented (step 6 is N/A)
- [x] DRY_RUN mode uses git apply --check without modifying files
- [x] APPLY mode applies diff using git apply
- [x] Unapproved diffs are rejected
- [x] Test file modifications rejected when tests are locked
- [x] Unauthorized file modifications rejected
- [x] Git apply failures provide clear error messages
- [x] Audit log entry is created
- [x] All tests pass
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/executors/diff_executor.py` | CREATE | Diff executor adapter |
| `rice_factor/adapters/executors/__init__.py` | UPDATE | Export DiffExecutor |
| `tests/unit/adapters/executors/test_diff_executor.py` | CREATE | Unit tests |
| `tests/integration/adapters/executors/test_diff_executor_git.py` | CREATE | Integration tests |

## Dependencies

- F05-01: Executor Base Interface (ExecutorPort, ExecutionMode, ExecutionResult, errors)
- F05-06: Audit Logging (AuditLogger)
- M02: Artifact System (StoragePort, DiffService)
- Git: External dependency for git apply

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - all tasks implemented |
