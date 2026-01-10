# Feature: F03-09 Override & Recovery Commands

## Status: Complete

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
- [x] Create `rice_factor/entrypoints/cli/commands/override.py`
  - [x] Require `--reason` option (non-empty string)
  - [x] Display warning about manual override
  - [x] Require explicit confirmation ("type OVERRIDE to confirm")
  - [x] Record override in audit trail with:
    - [x] Timestamp
    - [x] Reason provided
    - [x] What was overridden
  - [x] Flag for future reconciliation
  - [x] Display reconciliation warning

### Override Service
- [x] Create `rice_factor/domain/services/override_service.py`
  - [x] Define `OverrideService` class
  - [x] Implement `record_override(reason, target, context)`
  - [x] Implement `get_pending_overrides()` - list unreconciled
  - [x] Implement `mark_reconciled(override_id)`
  - [x] Store overrides in `audit/overrides.json`

### Override Scope
- [x] Define overridable operations:
  - [x] Phase gating (execute command out of order)
  - [x] Unapproved artifact usage
  - [x] Failed validation bypass

### Resume Command
- [x] Create `rice_factor/entrypoints/cli/commands/resume.py`
  - [x] Reconstruct state from artifacts
  - [x] Display current phase
  - [x] Display artifact counts by type
  - [x] Display state summary
  - [x] Display suggested next steps based on phase
  - [x] Check for pending overrides

### Rich Output
- [x] Display override warning in red panel
- [x] Display reconciliation needed indicator
- [x] Display resume state in structured format

### Unit Tests
- [x] Create `tests/unit/domain/services/test_override_service.py`
  - [x] Test record_override() saves correctly
  - [x] Test get_pending_overrides() returns unreconciled
  - [x] Test mark_reconciled() updates status
- [x] Create `tests/unit/entrypoints/cli/commands/test_override.py`
  - [x] Test override requires --reason
  - [x] Test override requires explicit confirmation
  - [x] Test override records in audit trail
- [x] Create `tests/unit/entrypoints/cli/commands/test_resume.py`
  - [x] Test resume shows state summary
  - [x] Test resume shows pending overrides
  - [x] Test resume when nothing to resume

### Deferred to Future Milestones
- [ ] User identity tracking (requires auth system)
- [ ] ResumeService with retry/rollback operations
- [ ] CheckpointService for operation state tracking
- [ ] Integration tests

## Acceptance Criteria

- [x] `rice-factor override create` overrides blocked operations with --reason
- [x] Override requires explicit "OVERRIDE" confirmation (or --yes flag)
- [x] Override records reason and flags for reconciliation
- [x] `rice-factor override list` shows pending overrides
- [x] `rice-factor override reconcile` marks overrides as reconciled
- [x] `rice-factor resume` shows current project state
- [x] Resume shows clear state summary with phase and artifacts
- [x] Resume shows pending override warnings
- [x] Audit trail captures all overrides
- [x] All tests pass (85 tests)
- [x] mypy passes
- [x] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/commands/override.py` | Override command with subcommands |
| `rice_factor/entrypoints/cli/commands/resume.py` | Resume command |
| `rice_factor/domain/services/override_service.py` | Override service |
| `rice_factor/domain/services/__init__.py` | Export new service |
| `rice_factor/entrypoints/cli/main.py` | Register override subcommand |
| `tests/unit/domain/services/test_override_service.py` | Override service tests (35 tests) |
| `tests/unit/entrypoints/cli/commands/test_override.py` | Override command tests (31 tests) |
| `tests/unit/entrypoints/cli/commands/test_resume.py` | Resume command tests (19 tests) |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implemented OverrideService with Override dataclass |
| 2026-01-10 | Implemented override command with create/list/reconcile subcommands |
| 2026-01-10 | Implemented resume command with phase and artifact display |
| 2026-01-10 | Created 85 unit tests, all passing |
| 2026-01-10 | Feature complete |
