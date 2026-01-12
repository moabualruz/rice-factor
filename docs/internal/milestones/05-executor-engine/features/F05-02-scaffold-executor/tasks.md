# Feature: F05-02 Scaffold Executor

## Status: Complete

## Description

Implement the Scaffold Executor adapter that creates empty files and directories from an approved ScaffoldPlan artifact. This executor wraps the existing ScaffoldService and implements the ExecutorPort protocol with the full 9-step pipeline.

## Requirements Reference

- M05-SC-001: Scaffold Executor shall accept ScaffoldPlan artifacts only
- M05-SC-002: Scaffold Executor shall create empty files with TODO comments
- M05-SC-003: Scaffold Executor shall skip files that already exist
- M05-SC-004: Scaffold Executor shall create parent directories as needed
- M05-SC-005: If file already exists, then Scaffold Executor shall skip with warning
- M05-S-001: While in DRY_RUN mode, executors shall generate diff without applying
- M05-I-001: If artifact is draft, then executor shall reject it
- M05-I-005: If path escapes repository root, then executor shall reject operation
- raw/item-02-executor-design-and-pseudocode.md: Section 2.5 Scaffold Executor

## Tasks

### Scaffold Executor Adapter
- [x] Create `rice_factor/adapters/executors/scaffold_executor.py`
  - [x] Define `ScaffoldExecutor` class implementing `ExecutorPort`
  - [x] Implement `__init__(storage: StoragePort, validator: ValidatorPort)`
  - [x] Implement `execute(artifact_path, repo_root, mode) -> ExecutionResult`

### 9-Step Pipeline Implementation
- [x] Implement Step 1: Load artifact
  - [x] Load ScaffoldPlan from artifact_path
  - [x] Raise `ArtifactTypeError` if wrong type
- [x] Implement Step 2: Validate schema
  - [x] Use validator to check schema
  - [x] Raise `ArtifactSchemaError` on failure
- [x] Implement Step 3: Verify approval & lock status
  - [x] Check artifact.status == APPROVED
  - [x] Check approvals.json contains artifact_id
  - [x] Raise `ArtifactNotApprovedError` if not approved
- [x] Implement Step 4: Capability check
  - [x] N/A for scaffold (always supported)
- [x] Implement Step 5: Precondition checks
  - [x] Check all paths are within repo_root
  - [x] Raise `PathEscapesRepoError` if path escapes
- [x] Implement Step 6: Generate diff
  - [x] Compute which files would be created
  - [x] Generate diff content for audit
  - [x] Save diff to audit/diffs/
- [x] Implement Step 7: Apply (if APPLY mode)
  - [x] Create parent directories
  - [x] Create files with TODO comments
  - [x] Use existing ScaffoldService for file creation
- [x] Implement Step 8: Emit audit logs
  - [x] Call AuditLogger with execution details
- [x] Implement Step 9: Return result
  - [x] Build ExecutionResult with status, diffs, errors, logs

### Integration with Existing ScaffoldService
- [x] Use `ScaffoldService.scaffold()` for actual file creation
- [x] Use `ScaffoldService.generate_todo_comment()` for content
- [x] Wrap service calls with proper error handling

### Diff Generation
- [x] Implement `_generate_diff(files: list[FileEntry], repo_root: Path) -> str`
  - [x] Generate unified diff format showing file creation
  - [x] Include expected content (TODO comments)

### Path Security
- [x] Implement `_path_escapes_repo(path: Path, repo_root: Path) -> bool`
  - [x] Resolve symlinks
  - [x] Check path is within repo_root
  - [x] Reject `..` traversal

### Adapter Exports
- [x] Update `rice_factor/adapters/executors/__init__.py`
  - [x] Export `ScaffoldExecutor`

### Unit Tests
- [x] Create `tests/unit/adapters/executors/test_scaffold_executor.py`
  - [x] Test executor implements ExecutorPort protocol
  - [x] Test DRY_RUN mode generates diff without creating files
  - [x] Test APPLY mode creates files
  - [x] Test skips existing files with warning
  - [x] Test creates parent directories
  - [x] Test rejects unapproved artifact
  - [x] Test rejects wrong artifact type
  - [x] Test rejects path escaping repo
  - [x] Test generates audit log entry
  - [x] Test ExecutionResult contains correct diffs list
  - [x] Test ExecutionResult logs contain created files

## Acceptance Criteria

- [x] ScaffoldExecutor implements ExecutorPort protocol
- [x] Full 9-step pipeline implemented
- [x] DRY_RUN mode generates diff without file creation
- [x] APPLY mode creates files with TODO comments
- [x] Existing files are skipped with warning
- [x] Path escape is detected and rejected
- [x] Unapproved artifacts are rejected
- [x] Audit log entry is created
- [x] All tests pass
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/executors/scaffold_executor.py` | CREATE | Scaffold executor adapter |
| `rice_factor/adapters/executors/__init__.py` | UPDATE | Export ScaffoldExecutor |
| `tests/unit/adapters/executors/test_scaffold_executor.py` | CREATE | Executor tests |

## Dependencies

- F05-01: Executor Base Interface (ExecutorPort, ExecutionMode, ExecutionResult, errors)
- F05-06: Audit Logging (AuditLogger)
- M02: Artifact System (StoragePort, ValidatorPort, ScaffoldPlanPayload)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - all tasks implemented |
