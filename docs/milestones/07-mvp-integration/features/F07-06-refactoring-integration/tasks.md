# Feature: F07-06 Refactoring Integration

## Status: Complete

## Description

Wire the RefactorExecutor to the refactor CLI commands. Generate RefactorPlan from a goal, check capabilities via CapabilityRegistry, execute dry-run preview, and optionally apply refactoring. MVP supports only rename_symbol and move_file operations.

## Requirements Reference

- M07-S-004: Refactor executor shall verify capabilities before execution
- M07-WF-007: Refactor shall only execute after implementation tests pass
- raw/Phase-01-mvp.md: Section 6 (minimal refactor - move/rename only)
- raw/Item-01-mvp-example-walkthrough-end-to-end.md: Section 1.7

## Tasks

### RefactorPlan Generation
- [x] `rice_factor/entrypoints/cli/commands/plan.py` (refactor subcommand)
  - [x] Verify TestPlan is locked (via PhaseService)
  - [x] Read goal and target files as context (via ContextBuilder)
  - [x] Call refactor_planner pass (via ArtifactBuilder)
  - [x] Validate RefactorPlan against schema
  - [x] Save RefactorPlan artifact
  - [x] --stub flag for testing without API calls

### Capability Checking
- [x] Wire CapabilityService to refactor commands
  - [x] CapabilityService checks operation support
  - [x] get_unsupported_operations() identifies invalid ops
  - [x] Hard-fail if unsupported operation requested
  - [x] Display capability table with status

### Refactor Dry-Run
- [x] `rice_factor/entrypoints/cli/commands/refactor.py` (dry-run)
  - [x] Load latest RefactorPlan via ArtifactResolver
  - [x] Wire RefactorExecutor
  - [x] Execute preview()
  - [x] Display preview diff
  - [x] No file modifications

### Refactor Apply
- [x] `rice_factor/entrypoints/cli/commands/refactor.py` (apply)
  - [x] Require approved RefactorPlan
  - [x] Confirmation prompt (--yes to skip)
  - [x] Execute refactoring via executor
  - [x] Display success/failure message
  - [x] Record in audit trail

### MVP Operations Support
- [x] CapabilityService.MVP_SUPPORTED_OPERATIONS
  - [x] `rename_symbol` - Rename across project
  - [x] `move_file` - Relocate file with updates

### Audit Trail
- [x] record_artifact_approved() records refactor apply

### Unit Tests
- [x] `tests/unit/entrypoints/cli/commands/test_refactor.py`
  - [x] Test refactor requires TEST_LOCKED phase
  - [x] Test check shows capabilities
  - [x] Test dry-run produces preview
  - [x] Test apply requires approval
  - [x] 20 tests passing

## Acceptance Criteria

- [x] `rice-factor plan refactor <goal>` generates RefactorPlan
- [x] Capability check rejects unsupported operations
- [x] `rice-factor refactor dry-run` shows preview without file changes
- [x] `rice-factor refactor apply` applies changes
- [x] MVP supports rename_symbol and move_file
- [x] All tests pass (24 tests: 20 refactor + 4 plan refactor)
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/entrypoints/cli/commands/plan.py` | EXISTS | Already wired with ArtifactBuilder and --stub |
| `rice_factor/entrypoints/cli/commands/refactor.py` | EXISTS | Already wired with RefactorExecutor |
| `tests/unit/entrypoints/cli/commands/test_refactor.py` | EXISTS | 20 tests already passing |

## Dependencies

- F07-05: Implementation Loop (tests must pass before refactor) ✓
- F07-07: Safety Enforcement (capability checking) ✓

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-11 | Verified all refactor commands already wired |
| 2026-01-11 | 24 tests passing (20 refactor + 4 plan refactor) |
| 2026-01-11 | Feature already complete from previous work |
