# Feature: F05-04 Refactor Executor

## Status: Complete

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
- [x] Create `rice_factor/adapters/executors/refactor_executor_adapter.py`
  - [x] Define `RefactorExecutorAdapter` class implementing `ExecutorPort`
  - [x] Implement `__init__(storage: StoragePort, capability_registry: CapabilityRegistry)`
  - [x] Implement `execute(artifact_path, repo_root, mode) -> ExecutionResult`

### 9-Step Pipeline Implementation
- [x] Implement Step 1: Load artifact
  - [x] Load RefactorPlan from artifact_path
  - [x] Raise `ArtifactTypeError` if wrong type
- [x] Implement Step 2: Validate schema
  - [x] Use validator to check schema
  - [x] Raise `ArtifactSchemaError` on failure
- [x] Implement Step 3: Verify approval & lock status
  - [x] Check artifact.status == APPROVED
  - [x] Check approvals.json contains artifact_id
  - [x] Raise `ArtifactNotApprovedError` if not approved
- [x] Implement Step 4: Capability check
  - [x] Detect language from repo/files
  - [x] For each operation, check capability registry
  - [x] Raise `UnsupportedOperationError` if not supported
- [x] Implement Step 5: Precondition checks
  - [x] For move_file: check source exists, dest doesn't exist
  - [x] For rename_symbol: check file exists
  - [x] Raise appropriate errors on failure
- [x] Implement Step 6: Generate diff
  - [x] Plan operations (don't execute yet)
  - [x] Generate unified diff from planned changes
  - [x] Save diff to audit/diffs/
- [x] Implement Step 7: Apply (if APPLY mode)
  - [x] Apply diff using git apply
  - [x] OR directly execute operations
- [x] Implement Step 8: Emit audit logs
  - [x] Call AuditLogger with execution details
- [x] Implement Step 9: Return result
  - [x] Build ExecutionResult with status, diffs, errors, logs

### Move File Operation
- [x] Implement `_execute_move_file(op: RefactorOperation, repo_root: Path) -> str`
  - [x] Validate source exists
  - [x] Validate destination doesn't exist
  - [x] Generate diff showing file move
  - [x] Actually move file (in APPLY mode)

### Rename Symbol Operation
- [x] Implement `_execute_rename_symbol(op: RefactorOperation, repo_root: Path) -> str`
  - [x] Find all occurrences of symbol in file(s)
  - [x] Generate diff with replacements
  - [x] Simple textual replace (not AST-aware for MVP)

### Language Detection
- [x] Implement `_detect_language(repo_root: Path) -> str`
  - [x] Check for pyproject.toml, Cargo.toml, go.mod, package.json
  - [x] Fallback to file extension analysis
  - [x] Return language string matching capability registry keys

### Diff Generation from Operations
- [x] Implement `_generate_diff_from_operations(operations: list, repo_root: Path) -> str`
  - [x] Combine diffs from all operations
  - [x] Create unified diff format

### Integration with Existing RefactorExecutor Service
- [x] Wrap existing `RefactorExecutor` service (domain/services/refactor_executor.py)
  - [x] Use `preview()` for diff generation
  - [x] Use `execute()` for actual execution

### Adapter Exports
- [x] Update `rice_factor/adapters/executors/__init__.py`
  - [x] Export `RefactorExecutorAdapter` (renamed to avoid collision)

### Unit Tests
- [x] Create `tests/unit/adapters/executors/test_refactor_executor_adapter.py`
  - [x] Test executor implements ExecutorPort protocol
  - [x] Test DRY_RUN mode generates diff without moving files
  - [x] Test APPLY mode moves files
  - [x] Test rejects unapproved artifact
  - [x] Test rejects wrong artifact type
  - [x] Test rejects unsupported operation
  - [x] Test move_file checks source exists
  - [x] Test move_file checks dest doesn't exist
  - [x] Test rename_symbol performs textual replace
  - [x] Test language detection
  - [x] Test capability registry integration
  - [x] Test generates audit log entry

## Acceptance Criteria

- [x] RefactorExecutor implements ExecutorPort protocol
- [x] Full 9-step pipeline implemented
- [x] DRY_RUN mode generates diff without modifying files
- [x] APPLY mode executes refactor operations
- [x] move_file operation supported
- [x] rename_symbol operation supported (simple textual)
- [x] Capability registry is checked before execution
- [x] Unsupported operations are rejected with clear error
- [x] Source file existence verified
- [x] Destination non-existence verified
- [x] Language detection works for major languages
- [x] Audit log entry is created
- [x] All tests pass
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/executors/refactor_executor_adapter.py` | CREATE | Refactor executor adapter |
| `rice_factor/adapters/executors/__init__.py` | UPDATE | Export RefactorExecutorAdapter |
| `tests/unit/adapters/executors/test_refactor_executor_adapter.py` | CREATE | Executor tests |

## Dependencies

- F05-01: Executor Base Interface (ExecutorPort, ExecutionMode, ExecutionResult, errors)
- F05-05: Capability Registry (CapabilityRegistry)
- F05-06: Audit Logging (AuditLogger)
- M02: Artifact System (StoragePort, RefactorPlanPayload)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - all tasks implemented |
