# Feature: F07-05 Implementation Loop

## Status: Complete

## Description

Wire the complete plan → impl → apply → test cycle for file implementation. This is the core MVP workflow where LLM generates ImplementationPlan, then generates diffs, which are applied and tested. The loop repeats until tests pass.

## Requirements Reference

- M07-WF-003: Implementation commands shall only execute after TestPlan locked
- M07-WF-005: Apply command shall verify diff against approved ImplementationPlan
- M07-WF-006: Test command shall run after each apply to verify correctness
- M07-E-004: System shall hard-fail if diff touches unauthorized files
- raw/Phase-01-mvp.md: Section 5.5 (small-context generation, diff-first)
- raw/Item-01-mvp-example-walkthrough-end-to-end.md: Section 1.6

## Tasks

### Implementation Plan Generation
- [x] Update `rice_factor/entrypoints/cli/commands/plan.py` (impl subcommand)
  - [x] Verify TestPlan is locked (via PhaseService)
  - [x] Read target file and TestPlan assertions as context (via ContextBuilder)
  - [x] Call implementation_planner pass (via ArtifactBuilder)
  - [x] Validate ImplementationPlan against schema (via ArtifactBuilder)
  - [x] Save ImplementationPlan artifact

### Diff Generation
- [x] Update `rice_factor/entrypoints/cli/commands/impl.py`
  - [x] Wire ArtifactBuilder with LLM
  - [x] Add --stub flag for testing without API calls
  - [x] Generate ImplementationPlan via LLM or stub
  - [x] Save ImplementationPlan artifact
  - [x] Generate diff via DiffService
  - [x] Save diff to audit/diffs/
  - [x] Record in audit trail

### Diff Authorization
- [x] DiffExecutor implements authorization checking
  - [x] Parse files touched by diff
  - [x] Check against test file patterns (TestsLockedError)
  - [x] Hard-fail if test files modified when locked

### Apply Command Integration
- [x] Update `rice_factor/entrypoints/cli/commands/apply.py`
  - [x] Verify TestPlan lock via SafetyEnforcer
  - [x] Load approved diff
  - [x] Wire DiffExecutor for execution
  - [x] Apply diff via git apply (ExecutionMode.APPLY)
  - [x] Dry-run via git apply --check (ExecutionMode.DRY_RUN)
  - [x] Handle apply errors

### Test Command Integration
- [x] Existing `rice_factor/entrypoints/cli/commands/test.py`
  - [x] Uses stub test results (real runner deferred to M06)
  - [x] Emit ValidationResult artifact
  - [x] Display pass/fail status
  - [x] Record in audit trail

### Audit Trail
- [x] Audit entries for implementation loop
  - [x] record_diff_generated() in impl.py
  - [x] record_diff_applied() in apply.py
  - [x] record_test_run() in test.py

### Unit Tests
- [x] `tests/unit/entrypoints/cli/commands/test_impl.py`
  - [x] 12 tests passing
  - [x] Test --stub flag
  - [x] Test artifact creation
- [x] `tests/unit/entrypoints/cli/commands/test_apply.py`
  - [x] 12 tests passing
  - [x] Test DiffExecutor mocking
- [x] `tests/unit/entrypoints/cli/commands/test_test.py`
  - [x] 9 tests passing

## Acceptance Criteria

- [x] `rice-factor plan impl <file>` generates ImplementationPlan (via ArtifactBuilder)
- [x] `rice-factor impl <file>` generates code diff via LLM or --stub
- [x] `rice-factor apply` applies diff via DiffExecutor
- [x] `rice-factor test` runs tests (stub) and emits ValidationResult
- [x] Audit trail records all operations
- [x] --stub flag allows testing without real LLM calls
- [x] All tests pass (33 tests)
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/entrypoints/cli/commands/impl.py` | UPDATED | Wire ArtifactBuilder with LLM and --stub |
| `rice_factor/entrypoints/cli/commands/apply.py` | UPDATED | Wire DiffExecutor |
| `tests/unit/entrypoints/cli/commands/test_impl.py` | UPDATED | Added --stub flag to tests |
| `tests/unit/entrypoints/cli/commands/test_apply.py` | UPDATED | Mock DiffExecutor in tests |

## Dependencies

- F07-04: Test Lock Integration (TestPlan must be locked) ✓
- F07-07: Safety Enforcement (diff authorization) ✓

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-11 | Updated impl.py with ArtifactBuilder integration and --stub flag |
| 2026-01-11 | Updated apply.py to use DiffExecutor |
| 2026-01-11 | Updated tests with mocks for DiffExecutor |
| 2026-01-11 | 33 tests passing across impl, apply, and test commands |
| 2026-01-11 | Feature complete |
