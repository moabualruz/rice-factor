# Feature: F05-03 Diff Executor

## Status: Pending

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
- [ ] Create `rice_factor/adapters/executors/diff_executor.py`
  - [ ] Define `DiffExecutor` class implementing `ExecutorPort`
  - [ ] Implement `__init__(storage: StoragePort)`
  - [ ] Implement `execute(diff_path, repo_root, mode) -> ExecutionResult`

### 9-Step Pipeline Implementation
- [ ] Implement Step 1: Load diff
  - [ ] Load Diff from diff_path using DiffService
  - [ ] Verify diff file exists
- [ ] Implement Step 2: Validate diff format
  - [ ] Ensure valid unified diff format
  - [ ] Parse touched files from diff
- [ ] Implement Step 3: Verify approval status
  - [ ] Check diff.status == APPROVED
  - [ ] Raise `ArtifactNotApprovedError` if not approved
- [ ] Implement Step 4: Capability check
  - [ ] N/A for diff (always supported)
- [ ] Implement Step 5: Precondition checks
  - [ ] Check diff touches only authorized files
  - [ ] Check tests are not modified if locked
  - [ ] Check no binary files in diff
- [ ] Implement Step 6: N/A (diff is input, not generated)
- [ ] Implement Step 7: Apply (if APPLY mode)
  - [ ] Run `git apply` with diff
  - [ ] Capture exit code and output
  - [ ] Raise `GitApplyError` on failure
- [ ] Implement Step 8: Emit audit logs
  - [ ] Call AuditLogger with execution details
- [ ] Implement Step 9: Return result
  - [ ] Build ExecutionResult with status, diffs, errors, logs

### Git Apply Integration
- [ ] Implement `_git_apply(diff_path: Path, repo_root: Path, dry_run: bool) -> tuple[bool, str]`
  - [ ] Run `git apply --check` for dry run
  - [ ] Run `git apply` for actual application
  - [ ] Capture stdout/stderr
  - [ ] Return (success, output)
- [ ] Implement `_parse_git_apply_error(output: str) -> str`
  - [ ] Extract meaningful error message from git output

### Diff Parsing
- [ ] Implement `_parse_diff_files(diff_content: str) -> list[str]`
  - [ ] Extract file paths from diff headers (--- a/... +++ b/...)
  - [ ] Handle new file creation
  - [ ] Handle file deletion

### Test File Lock Check
- [ ] Implement `_check_test_lock(files: list[str], storage: StoragePort) -> bool`
  - [ ] Check if TestPlan is locked
  - [ ] Return True if any test file is in the diff
- [ ] Implement `_is_test_file(path: str) -> bool`
  - [ ] Pattern matching for test files (test_*.py, *_test.py, tests/, etc.)

### Adapter Exports
- [ ] Update `rice_factor/adapters/executors/__init__.py`
  - [ ] Export `DiffExecutor`

### Unit Tests
- [ ] Create `tests/unit/adapters/executors/test_diff_executor.py`
  - [ ] Test executor implements ExecutorPort protocol
  - [ ] Test DRY_RUN mode uses git apply --check
  - [ ] Test APPLY mode applies diff
  - [ ] Test rejects unapproved diff
  - [ ] Test rejects diff touching test files when locked
  - [ ] Test rejects diff with unauthorized files
  - [ ] Test handles git apply failure gracefully
  - [ ] Test parses diff file paths correctly
  - [ ] Test generates audit log entry
  - [ ] Test ExecutionResult contains correct status

### Integration Tests
- [ ] Create `tests/integration/adapters/executors/test_diff_executor_git.py`
  - [ ] Test with real git repository (use tmp_path)
  - [ ] Test applying valid diff
  - [ ] Test applying conflicting diff
  - [ ] Test git apply --check works correctly

## Acceptance Criteria

- [ ] DiffExecutor implements ExecutorPort protocol
- [ ] Full 9-step pipeline implemented (step 6 is N/A)
- [ ] DRY_RUN mode uses git apply --check without modifying files
- [ ] APPLY mode applies diff using git apply
- [ ] Unapproved diffs are rejected
- [ ] Test file modifications rejected when tests are locked
- [ ] Unauthorized file modifications rejected
- [ ] Git apply failures provide clear error messages
- [ ] Audit log entry is created
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

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
