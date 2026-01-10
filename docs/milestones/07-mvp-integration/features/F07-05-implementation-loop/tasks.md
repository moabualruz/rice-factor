# Feature: F07-05 Implementation Loop

## Status: Pending

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
- [ ] Update `rice_factor/entrypoints/cli/commands/plan.py` (impl subcommand)
  - [ ] Verify TestPlan is locked
  - [ ] Read target file and TestPlan assertions as context
  - [ ] Call implementation_planner pass
  - [ ] Validate ImplementationPlan against schema
  - [ ] Save ImplementationPlan artifact

### Diff Generation
- [ ] Update `rice_factor/entrypoints/cli/commands/impl.py`
  - [ ] Load approved ImplementationPlan
  - [ ] Read target file content
  - [ ] Assemble tiny context for LLM
  - [ ] Generate code diff via LLM
  - [ ] Validate diff format
  - [ ] Save diff to audit/diffs/

### Diff Authorization
- [ ] Implement diff authorization checking
  - [ ] Parse files touched by diff
  - [ ] Compare to ImplementationPlan target
  - [ ] Hard-fail if unauthorized files touched
  - [ ] Log authorization check result

### Apply Command Integration
- [ ] Update `rice_factor/entrypoints/cli/commands/apply.py`
  - [ ] Verify TestPlan lock
  - [ ] Load pending diff
  - [ ] Verify diff authorization
  - [ ] Wire DiffExecutor
  - [ ] Apply diff via git apply
  - [ ] Handle apply conflicts

### Test Command Integration
- [ ] Update `rice_factor/entrypoints/cli/commands/test.py`
  - [ ] Wire TestRunnerAdapter
  - [ ] Run tests for target language
  - [ ] Emit ValidationResult artifact
  - [ ] Display pass/fail status
  - [ ] Suggest next action on failure

### Implementation Loop State
- [ ] Track implementation progress
  - [ ] Record which files have been implemented
  - [ ] Track test pass/fail per file
  - [ ] Suggest next file to implement

### Audit Trail
- [ ] Add audit entries for implementation loop
  - [ ] Record plan generation
  - [ ] Record diff generation
  - [ ] Record diff authorization check
  - [ ] Record apply operation
  - [ ] Record test results

### Unit Tests
- [ ] Create `tests/unit/entrypoints/cli/commands/test_impl_integration.py`
  - [ ] Test plan impl requires locked TestPlan
  - [ ] Test impl generates diff from ImplementationPlan
  - [ ] Test apply verifies diff authorization
  - [ ] Test apply uses DiffExecutor
  - [ ] Test test runs TestRunnerAdapter
  - [ ] Test unauthorized diff causes hard-fail

## Acceptance Criteria

- [ ] `rice-factor plan impl <file>` generates ImplementationPlan
- [ ] `rice-factor impl <file>` generates code diff via real LLM
- [ ] Diff authorization checks target matches ImplementationPlan
- [ ] `rice-factor apply` applies diff via DiffExecutor
- [ ] `rice-factor test` runs tests via TestRunnerAdapter
- [ ] Unauthorized diffs cause hard-fail with clear error
- [ ] Audit trail records all operations
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/entrypoints/cli/commands/plan.py` | UPDATE | Wire impl planning |
| `rice_factor/entrypoints/cli/commands/impl.py` | UPDATE | Wire diff generation |
| `rice_factor/entrypoints/cli/commands/apply.py` | UPDATE | Wire DiffExecutor |
| `rice_factor/entrypoints/cli/commands/test.py` | UPDATE | Wire TestRunnerAdapter |
| `rice_factor/domain/services/diff_authorization.py` | CREATE | Diff authorization service |
| `tests/unit/entrypoints/cli/commands/test_impl_integration.py` | CREATE | Integration tests |

## Dependencies

- F07-04: Test Lock Integration (TestPlan must be locked)
- F07-07: Safety Enforcement (diff authorization)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
