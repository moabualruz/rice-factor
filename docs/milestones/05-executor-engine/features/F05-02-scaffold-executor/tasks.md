# Feature: F05-02 Scaffold Executor

## Status: Pending

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
- [ ] Create `rice_factor/adapters/executors/scaffold_executor.py`
  - [ ] Define `ScaffoldExecutor` class implementing `ExecutorPort`
  - [ ] Implement `__init__(storage: StoragePort, validator: ValidatorPort)`
  - [ ] Implement `execute(artifact_path, repo_root, mode) -> ExecutionResult`

### 9-Step Pipeline Implementation
- [ ] Implement Step 1: Load artifact
  - [ ] Load ScaffoldPlan from artifact_path
  - [ ] Raise `ArtifactTypeError` if wrong type
- [ ] Implement Step 2: Validate schema
  - [ ] Use validator to check schema
  - [ ] Raise `ArtifactSchemaError` on failure
- [ ] Implement Step 3: Verify approval & lock status
  - [ ] Check artifact.status == APPROVED
  - [ ] Check approvals.json contains artifact_id
  - [ ] Raise `ArtifactNotApprovedError` if not approved
- [ ] Implement Step 4: Capability check
  - [ ] N/A for scaffold (always supported)
- [ ] Implement Step 5: Precondition checks
  - [ ] Check all paths are within repo_root
  - [ ] Raise `PathEscapesRepoError` if path escapes
- [ ] Implement Step 6: Generate diff
  - [ ] Compute which files would be created
  - [ ] Generate diff content for audit
  - [ ] Save diff to audit/diffs/
- [ ] Implement Step 7: Apply (if APPLY mode)
  - [ ] Create parent directories
  - [ ] Create files with TODO comments
  - [ ] Use existing ScaffoldService for file creation
- [ ] Implement Step 8: Emit audit logs
  - [ ] Call AuditLogger with execution details
- [ ] Implement Step 9: Return result
  - [ ] Build ExecutionResult with status, diffs, errors, logs

### Integration with Existing ScaffoldService
- [ ] Use `ScaffoldService.scaffold()` for actual file creation
- [ ] Use `ScaffoldService.generate_todo_comment()` for content
- [ ] Wrap service calls with proper error handling

### Diff Generation
- [ ] Implement `_generate_diff(files: list[FileEntry], repo_root: Path) -> str`
  - [ ] Generate unified diff format showing file creation
  - [ ] Include expected content (TODO comments)

### Path Security
- [ ] Implement `_path_escapes_repo(path: Path, repo_root: Path) -> bool`
  - [ ] Resolve symlinks
  - [ ] Check path is within repo_root
  - [ ] Reject `..` traversal

### Adapter Exports
- [ ] Update `rice_factor/adapters/executors/__init__.py`
  - [ ] Export `ScaffoldExecutor`

### Unit Tests
- [ ] Create `tests/unit/adapters/executors/test_scaffold_executor.py`
  - [ ] Test executor implements ExecutorPort protocol
  - [ ] Test DRY_RUN mode generates diff without creating files
  - [ ] Test APPLY mode creates files
  - [ ] Test skips existing files with warning
  - [ ] Test creates parent directories
  - [ ] Test rejects unapproved artifact
  - [ ] Test rejects wrong artifact type
  - [ ] Test rejects path escaping repo
  - [ ] Test generates audit log entry
  - [ ] Test ExecutionResult contains correct diffs list
  - [ ] Test ExecutionResult logs contain created files

## Acceptance Criteria

- [ ] ScaffoldExecutor implements ExecutorPort protocol
- [ ] Full 9-step pipeline implemented
- [ ] DRY_RUN mode generates diff without file creation
- [ ] APPLY mode creates files with TODO comments
- [ ] Existing files are skipped with warning
- [ ] Path escape is detected and rejected
- [ ] Unapproved artifacts are rejected
- [ ] Audit log entry is created
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

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
