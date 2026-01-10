# Feature: F07-06 Refactoring Integration

## Status: Pending

## Description

Wire the RefactorExecutor to the refactor CLI commands. Generate RefactorPlan from a goal, check capabilities via CapabilityRegistry, execute dry-run preview, and optionally apply refactoring. MVP supports only rename_symbol and move_file operations.

## Requirements Reference

- M07-S-004: Refactor executor shall verify capabilities before execution
- M07-WF-007: Refactor shall only execute after implementation tests pass
- raw/Phase-01-mvp.md: Section 6 (minimal refactor - move/rename only)
- raw/Item-01-mvp-example-walkthrough-end-to-end.md: Section 1.7

## Tasks

### RefactorPlan Generation
- [ ] Update `rice_factor/entrypoints/cli/commands/plan.py` (refactor subcommand)
  - [ ] Verify TestPlan is locked
  - [ ] Verify tests currently pass
  - [ ] Read goal and target files as context
  - [ ] Call refactor_planner pass
  - [ ] Validate RefactorPlan against schema
  - [ ] Save RefactorPlan artifact

### Capability Checking
- [ ] Wire CapabilityRegistry to refactor commands
  - [ ] Load capability registry YAML
  - [ ] Check if operations supported for language
  - [ ] Hard-fail if unsupported operation requested
  - [ ] Display supported operations on failure

### Refactor Dry-Run
- [ ] Update `rice_factor/entrypoints/cli/commands/refactor.py` (dry-run)
  - [ ] Load approved RefactorPlan
  - [ ] Wire RefactorExecutorAdapter
  - [ ] Execute in DRY_RUN mode
  - [ ] Display preview diff
  - [ ] Do not modify files

### Refactor Apply
- [ ] Update `rice_factor/entrypoints/cli/commands/refactor.py` (apply)
  - [ ] Verify dry-run was successful
  - [ ] Execute in APPLY mode
  - [ ] Apply refactoring changes
  - [ ] Run tests to verify behavior preserved
  - [ ] Rollback on test failure

### MVP Operations Support
- [ ] Verify MVP operation support
  - [ ] `rename_symbol` - Rename across project
  - [ ] `move_file` - Relocate file with updates
  - [ ] Other operations → "not supported in MVP"

### Audit Trail
- [ ] Add audit entries for refactor operations
  - [ ] Record RefactorPlan ID
  - [ ] Record operation type
  - [ ] Record dry-run/apply mode
  - [ ] Record files affected
  - [ ] Record test results after apply

### Unit Tests
- [ ] Create `tests/unit/entrypoints/cli/commands/test_refactor_integration.py`
  - [ ] Test refactor requires locked TestPlan
  - [ ] Test refactor checks capabilities
  - [ ] Test dry-run produces preview without changes
  - [ ] Test apply modifies files
  - [ ] Test unsupported operation causes hard-fail

## Acceptance Criteria

- [ ] `rice-factor plan refactor <goal>` generates RefactorPlan
- [ ] Capability check rejects unsupported operations
- [ ] `rice-factor refactor dry-run` shows preview without file changes
- [ ] `rice-factor refactor apply` applies changes and runs tests
- [ ] MVP supports rename_symbol and move_file only
- [ ] Audit trail records refactor operations
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/entrypoints/cli/commands/plan.py` | UPDATE | Wire refactor planning |
| `rice_factor/entrypoints/cli/commands/refactor.py` | UPDATE | Wire RefactorExecutor |
| `tests/unit/entrypoints/cli/commands/test_refactor_integration.py` | CREATE | Integration tests |

## Dependencies

- F07-05: Implementation Loop (tests must pass before refactor)
- F07-07: Safety Enforcement (capability checking)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
