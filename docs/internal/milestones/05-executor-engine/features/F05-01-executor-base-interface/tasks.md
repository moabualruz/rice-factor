# Feature: F05-01 Executor Base Interface

## Status: Complete

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
- [x] Create `rice_factor/domain/ports/executor.py`
  - [x] Define `ExecutorPort` Protocol class
  - [x] Define `execute(artifact_path, repo_root, mode) -> ExecutionResult` method signature
  - [x] Include docstrings with contract specification
  - [x] No external dependencies (Protocol from typing only)

### Execution Types Module
- [x] Create `rice_factor/domain/artifacts/execution_types.py`
  - [x] Define `ExecutionMode` enum
    - [x] `DRY_RUN` - Generate diff without applying
    - [x] `APPLY` - Generate diff and apply
  - [x] Define `ExecutionResult` dataclass
    - [x] `status: Literal["success", "failure"]`
    - [x] `diffs: list[Path]` (audit/diffs paths)
    - [x] `errors: list[str]`
    - [x] `logs: list[str]`
  - [x] Implement `success` property
  - [x] Implement `to_dict()` method for serialization

### Executor Error Types
- [x] Create `rice_factor/domain/failures/executor_errors.py`
  - [x] Define `ExecutorError(RiceFactorError)` base class
  - [x] Define `ExecutorPreconditionError(ExecutorError)`
    - [x] `ArtifactNotApprovedError`
    - [x] `FileAlreadyExistsError`
    - [x] `FileNotFoundError`
    - [x] `PathEscapesRepoError`
    - [x] `TestsLockedError`
  - [x] Define `ExecutorCapabilityError(ExecutorError)`
    - [x] `UnsupportedOperationError`
  - [x] Define `ExecutorArtifactError(ExecutorError)`
    - [x] `ArtifactSchemaError`
    - [x] `ArtifactTypeError`
  - [x] Define `ExecutorApplyError(ExecutorError)`
    - [x] `GitApplyError`
    - [x] `FileWriteError`

### Port Exports
- [x] Update `rice_factor/domain/ports/__init__.py`
  - [x] Export `ExecutorPort`
- [x] Update `rice_factor/domain/artifacts/__init__.py`
  - [x] Export `ExecutionMode`
  - [x] Export `ExecutionResult`
- [x] Update `rice_factor/domain/failures/__init__.py`
  - [x] Export all executor error types

### Unit Tests
- [x] Create `tests/unit/domain/ports/test_executor.py`
  - [x] Test `ExecutorPort` is a valid Protocol
  - [x] Test protocol methods are defined
- [x] Create `tests/unit/domain/artifacts/test_execution_types.py`
  - [x] Test `ExecutionMode` enum has DRY_RUN and APPLY values
  - [x] Test `ExecutionResult` creation for success case
  - [x] Test `ExecutionResult` creation for failure case
  - [x] Test `ExecutionResult.success` property
  - [x] Test `ExecutionResult.to_dict()` serialization
- [x] Create `tests/unit/domain/failures/test_executor_errors.py`
  - [x] Test error hierarchy (all errors inherit correctly)
  - [x] Test each error type can be instantiated
  - [x] Test error messages include relevant details

## Acceptance Criteria

- [x] `ExecutorPort` Protocol defined in `domain/ports/executor.py`
- [x] `ExecutionMode` enum with DRY_RUN and APPLY values
- [x] `ExecutionResult` dataclass handles both success and error cases
- [x] Complete executor error hierarchy defined
- [x] Protocol has no external dependencies (stdlib only)
- [x] All tests pass
- [x] mypy passes
- [x] ruff passes

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
| 2026-01-10 | Feature completed - all tasks implemented |
