# Feature: F03-09 Override & Recovery Commands

## Status: Pending

## Description

Implement override and recovery commands: `override`, `resume`, `review`, and `diagnose`. These commands provide escape hatches for blocked operations and recovery mechanisms for failures.

## Requirements Reference

- M03-U-004: All destructive commands shall require confirmation
- Commands Table:
  - `rice-factor override --reason` - Override blocked operations with audit (P1)
  - `rice-factor resume` - Resume after failure (P1)
  - `rice-factor review` - Show pending diff for approval (P0) [also in F03-05]
  - `rice-factor diagnose` - Analyze test/validation failures (P0) [also in F03-05]

## Tasks

### Override Command
- [ ] Create `rice_factor/entrypoints/cli/commands/override.py`
  - [ ] Require `--reason` option (non-empty string)
  - [ ] Display warning about manual override
  - [ ] Require explicit confirmation ("type OVERRIDE to confirm")
  - [ ] Record override in audit trail with:
    - [ ] Timestamp
    - [ ] Reason provided
    - [ ] User identity (if available)
    - [ ] What was overridden
  - [ ] Flag for future reconciliation
  - [ ] Display reconciliation warning

### Override Service
- [ ] Create `rice_factor/domain/services/override_service.py`
  - [ ] Define `OverrideService` class
  - [ ] Implement `record_override(reason, target, context)`
  - [ ] Implement `get_pending_overrides()` - list unreconciled
  - [ ] Implement `mark_reconciled(override_id)`
  - [ ] Store overrides in `audit/overrides.json`

### Override Scope
- [ ] Define overridable operations:
  - [ ] Phase gating (execute command out of order)
  - [ ] Unapproved artifact usage
  - [ ] Test modification (with strong warning)
  - [ ] Failed validation bypass
- [ ] Non-overridable operations (hard fail):
  - [ ] Schema validation errors
  - [ ] Missing required files
  - [ ] Corrupt artifacts

### Resume Command
- [ ] Create `rice_factor/entrypoints/cli/commands/resume.py`
  - [ ] Reconstruct state from artifacts + audit
  - [ ] Identify last successful operation
  - [ ] Identify interrupted operation
  - [ ] Display state summary
  - [ ] Prompt for resume action:
    - [ ] Retry last operation
    - [ ] Skip and continue
    - [ ] Abort and rollback (if possible)
  - [ ] Execute chosen action

### Resume Service
- [ ] Create `rice_factor/domain/services/resume_service.py`
  - [ ] Define `ResumeService` class
  - [ ] Implement `get_last_checkpoint()` - last safe point
  - [ ] Implement `get_interrupted_operation()` - what failed
  - [ ] Implement `can_retry()` - check if retry possible
  - [ ] Implement `can_rollback()` - check if rollback possible
  - [ ] Implement `resume_from(checkpoint)`
  - [ ] Implement `rollback_to(checkpoint)`

### Checkpoint System
- [ ] Create `rice_factor/domain/services/checkpoint_service.py`
  - [ ] Define `Checkpoint` model (operation, timestamp, artifacts_snapshot)
  - [ ] Implement `create_checkpoint(operation)` - save state
  - [ ] Implement `load_checkpoint(checkpoint_id)` - restore state
  - [ ] Store checkpoints in `audit/checkpoints/`

### Rich Output
- [ ] Display override warning in red panel
- [ ] Display reconciliation needed indicator
- [ ] Display resume state in structured format
- [ ] Display checkpoint history

### Unit Tests
- [ ] Create `tests/unit/domain/services/test_override_service.py`
  - [ ] Test record_override() saves correctly
  - [ ] Test get_pending_overrides() returns unreconciled
  - [ ] Test mark_reconciled() updates status
- [ ] Create `tests/unit/domain/services/test_resume_service.py`
  - [ ] Test get_last_checkpoint()
  - [ ] Test get_interrupted_operation()
  - [ ] Test can_retry() logic
  - [ ] Test can_rollback() logic
- [ ] Create `tests/unit/domain/services/test_checkpoint_service.py`
  - [ ] Test create_checkpoint() saves state
  - [ ] Test load_checkpoint() restores state
- [ ] Create `tests/unit/entrypoints/cli/commands/test_override.py`
  - [ ] Test override requires --reason
  - [ ] Test override requires explicit confirmation
  - [ ] Test override records in audit trail
  - [ ] Test non-overridable operations fail
- [ ] Create `tests/unit/entrypoints/cli/commands/test_resume.py`
  - [ ] Test resume shows state summary
  - [ ] Test resume retry action
  - [ ] Test resume skip action
  - [ ] Test resume when nothing to resume

### Integration Tests
- [ ] Create `tests/integration/cli/test_override_flow.py`
  - [ ] Test override bypass of phase gating
  - [ ] Test override recorded in audit
  - [ ] Test override flagged for reconciliation
- [ ] Create `tests/integration/cli/test_resume_flow.py`
  - [ ] Test resume after interrupted operation
  - [ ] Test checkpoint system works

## Acceptance Criteria

- [ ] `rice-factor override --reason` overrides blocked operations
- [ ] Override requires explicit "OVERRIDE" confirmation
- [ ] Override records reason and flags for reconciliation
- [ ] `rice-factor resume` recovers from interrupted operations
- [ ] Resume shows clear state summary
- [ ] Resume offers retry/skip/rollback options
- [ ] Checkpoint system tracks operation state
- [ ] Audit trail captures all overrides and resume actions
- [ ] All tests pass (30+ tests)
- [ ] mypy passes
- [ ] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/commands/override.py` | Override command |
| `rice_factor/entrypoints/cli/commands/resume.py` | Resume command |
| `rice_factor/domain/services/override_service.py` | Override service |
| `rice_factor/domain/services/resume_service.py` | Resume service |
| `rice_factor/domain/services/checkpoint_service.py` | Checkpoint service |
| `rice_factor/entrypoints/cli/main.py` | Register commands |
| `tests/unit/domain/services/test_override_service.py` | Override tests |
| `tests/unit/domain/services/test_resume_service.py` | Resume tests |
| `tests/unit/domain/services/test_checkpoint_service.py` | Checkpoint tests |
| `tests/unit/entrypoints/cli/commands/test_override.py` | Override command tests |
| `tests/unit/entrypoints/cli/commands/test_resume.py` | Resume command tests |
| `tests/integration/cli/test_override_flow.py` | Override integration |
| `tests/integration/cli/test_resume_flow.py` | Resume integration |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
