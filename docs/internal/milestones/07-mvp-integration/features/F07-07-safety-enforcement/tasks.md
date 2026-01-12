# Feature: F07-07 Safety Enforcement

## Status: In Progress

## Description

Implement the safety enforcement layer that ensures hard-fail on any safety violation. This is the foundation feature that provides safety guarantees for all other features. Create SafetyEnforcer service and wire it to all CLI commands.

## Requirements Reference

- M07-U-003: Safety violations shall cause immediate hard-fail with clear error
- M07-S-001: TestPlan lock shall use hash-based verification
- M07-S-002: Diff application shall verify target files match plan
- M07-E-001 through M07-E-005: Hard-fail conditions
- raw/Phase-01-mvp.md: Section 7 (safety guarantees)
- design.md: Section 4 (Safety Enforcement Design)

## Tasks

### SafetyEnforcer Service
- [x] Create `rice_factor/domain/services/safety_enforcer.py`
  - [x] Define SafetyEnforcer class
  - [x] Implement `check_test_lock_intact() -> LockVerificationResult`
  - [x] Implement `require_test_lock_intact() -> None`
  - [x] Implement `check_artifact_exists(artifact_type, status) -> bool`
  - [x] Implement `require_artifact_exists(artifact_type, status, command) -> None`
  - [x] Implement `check_diff_authorized(diff_content, authorized_files) -> tuple`
  - [x] Implement `require_diff_authorized(diff_content, authorized_files) -> None`
  - [x] Implement `check_phase_valid(command) -> bool`
  - [x] Implement `require_phase_valid(command) -> None`

### Integration Error Types
- [x] Reuse existing error types from `rice_factor/domain/failures/`
  - [x] `TestsLockedError` in executor_errors.py (with modified files list)
  - [x] `UnauthorizedFileModificationError` in executor_errors.py (with touched files)
  - [x] `MissingPrerequisiteError` in cli_errors.py (with artifact details)
  - [x] Add recovery guidance to error messages

### Pre-Command Safety Checks
- [x] Wire safety checks to CLI commands
  - [ ] `plan impl` - check TestPlan locked
  - [x] `impl` - check TestPlan locked
  - [x] `apply` - check TestPlan locked
  - [ ] `test` - check TestPlan locked
  - [ ] `refactor` - check TestPlan locked, capability valid

### Schema Validation Enforcement
- [x] Wire schema validation to artifact loading (already done via Pydantic)
  - [x] Validate on artifact load
  - [x] Hard-fail with validation error on invalid
  - [x] Display validation errors clearly

### Hard-Fail Behavior
- [x] Implement consistent hard-fail behavior
  - [x] Exit with non-zero code
  - [x] Display error message with context
  - [x] Display recovery guidance
  - [ ] Log to audit trail

### Safety Audit Trail
- [ ] Add audit entries for safety checks
  - [ ] Record check type
  - [ ] Record pass/fail result
  - [ ] Record violation details on failure

### Unit Tests
- [x] Create `tests/unit/domain/services/test_safety_enforcer.py`
  - [x] Test TestPlan lock check passes when unchanged
  - [x] Test TestPlan lock check fails when modified
  - [x] Test diff authorization passes for target file
  - [x] Test diff authorization fails for unauthorized file
  - [x] Test artifact existence check
  - [x] Test phase validation

### Integration Tests
- [ ] Create `tests/integration/test_safety_enforcement.py`
  - [ ] Test hard-fail on modified tests
  - [ ] Test hard-fail on missing artifact
  - [ ] Test hard-fail on unauthorized diff
  - [ ] Test hard-fail on wrong phase
  - [ ] Test recovery guidance is displayed

## Acceptance Criteria

- [x] SafetyEnforcer service implements all safety checks
- [x] All integration errors include recovery guidance
- [x] Hard-fail exits with non-zero code
- [x] Hard-fail displays clear error message
- [x] CLI commands `impl` and `apply` wire safety checks
- [ ] Audit trail records safety check results
- [x] All tests pass
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/domain/services/safety_enforcer.py` | CREATE | Safety enforcement service |
| `rice_factor/domain/failures/integration_errors.py` | CREATE | Integration error types |
| `rice_factor/entrypoints/cli/commands/*.py` | UPDATE | Wire safety checks |
| `tests/unit/domain/services/test_safety_enforcer.py` | CREATE | Unit tests |
| `tests/integration/test_safety_enforcement.py` | CREATE | Integration tests |

## Dependencies

- None (foundation feature)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | SafetyEnforcer service created with all check methods |
| 2026-01-10 | Reused existing error types from executor_errors.py and cli_errors.py |
| 2026-01-10 | Wired safety checks to impl and apply commands |
| 2026-01-10 | 13 unit tests for SafetyEnforcer passing |
