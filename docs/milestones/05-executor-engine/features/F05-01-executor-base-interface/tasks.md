# Feature: F05-01 Executor Base Interface

## Status: Pending

## Description

Define the abstract ExecutorPort protocol that all executor adapters must implement. This is the core port in the hexagonal architecture that decouples the domain from specific execution strategies. Also define the execution types (ExecutionMode, ExecutionResult) and executor error hierarchy.

## Requirements Reference

- M05-U-001: Executors shall be stateless
- M05-U-002: Executors shall be deterministic
- M05-U-003: Executors shall fail fast on precondition violations
- M05-U-004: Executors shall emit diffs rather than direct writes
- M05-U-009: Executors shall accept artifacts as input
- M05-U-010: Executors shall fail loudly on any error
- raw/item-02-executor-design-and-pseudocode.md: Section 2.2 Universal Interface

## Tasks

### ExecutorPort Protocol Definition
- [ ] Create `rice_factor/domain/ports/executor.py`
  - [ ] Define `ExecutorPort` Protocol class
  - [ ] Define `execute(artifact_path, repo_root, mode) -> ExecutionResult` method signature
  - [ ] Include docstrings with contract specification
  - [ ] No external dependencies (Protocol from typing only)

### Execution Types Module
- [ ] Create `rice_factor/domain/artifacts/execution_types.py`
  - [ ] Define `ExecutionMode` enum
    - [ ] `DRY_RUN` - Generate diff without applying
    - [ ] `APPLY` - Generate diff and apply
  - [ ] Define `ExecutionResult` dataclass
    - [ ] `status: Literal["success", "failure"]`
    - [ ] `diffs: list[Path]` (audit/diffs paths)
    - [ ] `errors: list[str]`
    - [ ] `logs: list[str]`
  - [ ] Implement `success` property
  - [ ] Implement `to_dict()` method for serialization

### Executor Error Types
- [ ] Create `rice_factor/domain/failures/executor_errors.py`
  - [ ] Define `ExecutorError(RiceFactorError)` base class
  - [ ] Define `ExecutorPreconditionError(ExecutorError)`
    - [ ] `ArtifactNotApprovedError`
    - [ ] `FileAlreadyExistsError`
    - [ ] `FileNotFoundError`
    - [ ] `PathEscapesRepoError`
    - [ ] `TestsLockedError`
  - [ ] Define `ExecutorCapabilityError(ExecutorError)`
    - [ ] `UnsupportedOperationError`
  - [ ] Define `ExecutorArtifactError(ExecutorError)`
    - [ ] `ArtifactSchemaError`
    - [ ] `ArtifactTypeError`
  - [ ] Define `ExecutorApplyError(ExecutorError)`
    - [ ] `GitApplyError`
    - [ ] `FileWriteError`

### Port Exports
- [ ] Update `rice_factor/domain/ports/__init__.py`
  - [ ] Export `ExecutorPort`
- [ ] Update `rice_factor/domain/artifacts/__init__.py`
  - [ ] Export `ExecutionMode`
  - [ ] Export `ExecutionResult`
- [ ] Update `rice_factor/domain/failures/__init__.py`
  - [ ] Export all executor error types

### Unit Tests
- [ ] Create `tests/unit/domain/ports/test_executor.py`
  - [ ] Test `ExecutorPort` is a valid Protocol
  - [ ] Test protocol methods are defined
- [ ] Create `tests/unit/domain/artifacts/test_execution_types.py`
  - [ ] Test `ExecutionMode` enum has DRY_RUN and APPLY values
  - [ ] Test `ExecutionResult` creation for success case
  - [ ] Test `ExecutionResult` creation for failure case
  - [ ] Test `ExecutionResult.success` property
  - [ ] Test `ExecutionResult.to_dict()` serialization
- [ ] Create `tests/unit/domain/failures/test_executor_errors.py`
  - [ ] Test error hierarchy (all errors inherit correctly)
  - [ ] Test each error type can be instantiated
  - [ ] Test error messages include relevant details

## Acceptance Criteria

- [ ] `ExecutorPort` Protocol defined in `domain/ports/executor.py`
- [ ] `ExecutionMode` enum with DRY_RUN and APPLY values
- [ ] `ExecutionResult` dataclass handles both success and error cases
- [ ] Complete executor error hierarchy defined
- [ ] Protocol has no external dependencies (stdlib only)
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/domain/ports/executor.py` | CREATE | Executor port protocol definition |
| `rice_factor/domain/artifacts/execution_types.py` | CREATE | Execution mode and result types |
| `rice_factor/domain/failures/executor_errors.py` | CREATE | Executor error hierarchy |
| `rice_factor/domain/ports/__init__.py` | UPDATE | Export ExecutorPort |
| `rice_factor/domain/artifacts/__init__.py` | UPDATE | Export execution types |
| `rice_factor/domain/failures/__init__.py` | UPDATE | Export executor errors |
| `tests/unit/domain/ports/test_executor.py` | CREATE | Port tests |
| `tests/unit/domain/artifacts/test_execution_types.py` | CREATE | Execution types tests |
| `tests/unit/domain/failures/test_executor_errors.py` | CREATE | Error tests |

## Dependencies

- None (foundation feature)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
