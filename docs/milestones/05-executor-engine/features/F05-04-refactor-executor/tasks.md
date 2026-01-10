# Feature: F05-04 Refactor Executor

## Status: Pending

## Description

Implement the Refactor Executor adapter that performs mechanical refactoring operations (move_file, rename_symbol) from an approved RefactorPlan artifact. This executor generates diffs from the operations and applies them. It integrates with the capability registry to check operation support per language.

## Requirements Reference

- M05-RF-001: Refactor Executor shall accept RefactorPlan artifacts only
- M05-RF-002: Refactor Executor shall support move_file operation
- M05-RF-003: Refactor Executor shall support rename_symbol operation (simple textual)
- M05-RF-004: Refactor Executor shall check capability registry before execution
- M05-RF-005: Refactor Executor shall generate diff from operations
- M05-RF-006: If source file missing, then Refactor Executor shall fail
- M05-RF-007: If destination exists, then Refactor Executor shall fail
- M05-S-001: While in DRY_RUN mode, executors shall generate diff without applying
- M05-I-003: If operation is unsupported for language, then executor shall fail explicitly
- raw/item-02-executor-design-and-pseudocode.md: Section 2.7 Refactor Executor

## Tasks

### Refactor Executor Adapter
- [ ] Create `rice_factor/adapters/executors/refactor_executor.py`
  - [ ] Define `RefactorExecutor` class implementing `ExecutorPort`
  - [ ] Implement `__init__(storage: StoragePort, capability_registry: CapabilityRegistry)`
  - [ ] Implement `execute(artifact_path, repo_root, mode) -> ExecutionResult`

### 9-Step Pipeline Implementation
- [ ] Implement Step 1: Load artifact
  - [ ] Load RefactorPlan from artifact_path
  - [ ] Raise `ArtifactTypeError` if wrong type
- [ ] Implement Step 2: Validate schema
  - [ ] Use validator to check schema
  - [ ] Raise `ArtifactSchemaError` on failure
- [ ] Implement Step 3: Verify approval & lock status
  - [ ] Check artifact.status == APPROVED
  - [ ] Check approvals.json contains artifact_id
  - [ ] Raise `ArtifactNotApprovedError` if not approved
- [ ] Implement Step 4: Capability check
  - [ ] Detect language from repo/files
  - [ ] For each operation, check capability registry
  - [ ] Raise `UnsupportedOperationError` if not supported
- [ ] Implement Step 5: Precondition checks
  - [ ] For move_file: check source exists, dest doesn't exist
  - [ ] For rename_symbol: check file exists
  - [ ] Raise appropriate errors on failure
- [ ] Implement Step 6: Generate diff
  - [ ] Plan operations (don't execute yet)
  - [ ] Generate unified diff from planned changes
  - [ ] Save diff to audit/diffs/
- [ ] Implement Step 7: Apply (if APPLY mode)
  - [ ] Apply diff using git apply
  - [ ] OR directly execute operations
- [ ] Implement Step 8: Emit audit logs
  - [ ] Call AuditLogger with execution details
- [ ] Implement Step 9: Return result
  - [ ] Build ExecutionResult with status, diffs, errors, logs

### Move File Operation
- [ ] Implement `_execute_move_file(op: RefactorOperation, repo_root: Path) -> str`
  - [ ] Validate source exists
  - [ ] Validate destination doesn't exist
  - [ ] Generate diff showing file move
  - [ ] Actually move file (in APPLY mode)

### Rename Symbol Operation
- [ ] Implement `_execute_rename_symbol(op: RefactorOperation, repo_root: Path) -> str`
  - [ ] Find all occurrences of symbol in file(s)
  - [ ] Generate diff with replacements
  - [ ] Simple textual replace (not AST-aware for MVP)

### Language Detection
- [ ] Implement `_detect_language(repo_root: Path) -> str`
  - [ ] Check for pyproject.toml, Cargo.toml, go.mod, package.json
  - [ ] Fallback to file extension analysis
  - [ ] Return language string matching capability registry keys

### Diff Generation from Operations
- [ ] Implement `_generate_diff_from_operations(operations: list, repo_root: Path) -> str`
  - [ ] Combine diffs from all operations
  - [ ] Create unified diff format

### Integration with Existing RefactorExecutor Service
- [ ] Wrap existing `RefactorExecutor` service (domain/services/refactor_executor.py)
  - [ ] Use `preview()` for diff generation
  - [ ] Use `execute()` for actual execution

### Adapter Exports
- [ ] Update `rice_factor/adapters/executors/__init__.py`
  - [ ] Export `RefactorExecutorAdapter` (renamed to avoid collision)

### Unit Tests
- [ ] Create `tests/unit/adapters/executors/test_refactor_executor.py`
  - [ ] Test executor implements ExecutorPort protocol
  - [ ] Test DRY_RUN mode generates diff without moving files
  - [ ] Test APPLY mode moves files
  - [ ] Test rejects unapproved artifact
  - [ ] Test rejects wrong artifact type
  - [ ] Test rejects unsupported operation
  - [ ] Test move_file checks source exists
  - [ ] Test move_file checks dest doesn't exist
  - [ ] Test rename_symbol performs textual replace
  - [ ] Test language detection
  - [ ] Test capability registry integration
  - [ ] Test generates audit log entry

## Acceptance Criteria

- [ ] RefactorExecutor implements ExecutorPort protocol
- [ ] Full 9-step pipeline implemented
- [ ] DRY_RUN mode generates diff without modifying files
- [ ] APPLY mode executes refactor operations
- [ ] move_file operation supported
- [ ] rename_symbol operation supported (simple textual)
- [ ] Capability registry is checked before execution
- [ ] Unsupported operations are rejected with clear error
- [ ] Source file existence verified
- [ ] Destination non-existence verified
- [ ] Language detection works for major languages
- [ ] Audit log entry is created
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/executors/refactor_executor.py` | CREATE | Refactor executor adapter |
| `rice_factor/adapters/executors/__init__.py` | UPDATE | Export RefactorExecutor |
| `tests/unit/adapters/executors/test_refactor_executor.py` | CREATE | Executor tests |

## Dependencies

- F05-01: Executor Base Interface (ExecutorPort, ExecutionMode, ExecutionResult, errors)
- F05-05: Capability Registry (CapabilityRegistry)
- F05-06: Audit Logging (AuditLogger)
- M02: Artifact System (StoragePort, RefactorPlanPayload)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
