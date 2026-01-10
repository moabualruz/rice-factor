# Feature: F03-05 Implementation Commands

## Status: Pending

## Description

Implement the core implementation workflow commands: `impl`, `review`, `apply`, `test`, and `diagnose`. These commands handle the daily development loop of generating diffs, reviewing, applying, and validating implementations.

## Requirements Reference

- M03-U-003: All commands shall support `--dry-run` where applicable
- M03-U-004: All destructive commands shall require confirmation
- Commands Table:
  - `rice-factor impl <file>` - Generate implementation diff (P0)
  - `rice-factor review` - Show pending diff for approval (P0)
  - `rice-factor apply` - Apply approved diff (P0)
  - `rice-factor test` - Run test suite (P0)
  - `rice-factor diagnose` - Analyze test/validation failures (P0)

## Tasks

### Impl Command
- [ ] Create `rice_factor/entrypoints/cli/commands/impl.py`
  - [ ] Accept `file` argument (target file path)
  - [ ] Check phase (must be TEST_LOCKED+)
  - [ ] Load ImplementationPlan for the file
  - [ ] Stub: Generate placeholder diff
  - [ ] Save diff to `audit/diffs/<timestamp>_<file>.diff`
  - [ ] Display diff preview with syntax highlighting
  - [ ] Support `--dry-run` option

### Diff Service (Stub)
- [ ] Create `rice_factor/domain/services/diff_service.py`
  - [ ] Define `DiffService` class
  - [ ] Implement `generate_diff(plan, file)` - stub returns mock diff
  - [ ] Implement `save_diff(diff, file)` - save to audit/diffs/
  - [ ] Implement `load_pending_diff()` - get latest unapproved diff
  - [ ] Implement `approve_diff(diff_id)` - mark diff as approved
  - [ ] Implement `get_diff_status(diff_id)` - check if approved

### Review Command
- [ ] Create `rice_factor/entrypoints/cli/commands/review.py`
  - [ ] Load latest unapproved diff
  - [ ] Display diff with syntax highlighting
  - [ ] Display related plan steps
  - [ ] Display related test expectations
  - [ ] Prompt: approve / reject / re-plan
  - [ ] Update diff status based on choice

### Apply Command
- [ ] Create `rice_factor/entrypoints/cli/commands/apply.py`
  - [ ] Check for approved diff
  - [ ] Display diff preview
  - [ ] Require confirmation
  - [ ] Stub: Apply diff (log operation, no actual changes)
  - [ ] Record in audit log
  - [ ] Support `--dry-run` option

### Test Command
- [ ] Create `rice_factor/entrypoints/cli/commands/test.py`
  - [ ] Stub: Run native test runner
  - [ ] Create ValidationResult artifact with mock results
  - [ ] Save ValidationResult via ArtifactService
  - [ ] Display results with Rich table
  - [ ] Return exit code based on pass/fail

### Diagnose Command
- [ ] Create `rice_factor/entrypoints/cli/commands/diagnose.py`
  - [ ] Load latest ValidationResult artifact
  - [ ] Analyze failures (stub analysis)
  - [ ] Display failure summary
  - [ ] Suggest next steps
  - [ ] Create FailureReport for audit

### Audit Trail
- [ ] Create `rice_factor/adapters/audit/trail.py`
  - [ ] Define `AuditTrail` class
  - [ ] Implement `record_diff_generated(file, diff_path)`
  - [ ] Implement `record_diff_approved(diff_id, approver)`
  - [ ] Implement `record_diff_applied(diff_id)`
  - [ ] Implement `record_test_run(result)`
  - [ ] Save to `audit/trail.json` (append-only)

### Unit Tests
- [ ] Create `tests/unit/domain/services/test_diff_service.py`
  - [ ] Test `generate_diff()` returns valid diff format
  - [ ] Test `save_diff()` creates file in correct location
  - [ ] Test `load_pending_diff()` returns latest unapproved
  - [ ] Test `approve_diff()` updates status
- [ ] Create `tests/unit/entrypoints/cli/commands/test_impl.py`
  - [ ] Test impl command requires ImplementationPlan
  - [ ] Test impl command generates and saves diff
  - [ ] Test `--dry-run` doesn't save diff
- [ ] Create `tests/unit/entrypoints/cli/commands/test_review.py`
  - [ ] Test review shows pending diff
  - [ ] Test approve choice updates status
  - [ ] Test reject choice clears pending
- [ ] Create `tests/unit/entrypoints/cli/commands/test_apply.py`
  - [ ] Test apply requires approved diff
  - [ ] Test apply requires confirmation
  - [ ] Test `--dry-run` doesn't apply
- [ ] Create `tests/unit/entrypoints/cli/commands/test_test.py`
  - [ ] Test test command creates ValidationResult
  - [ ] Test results displayed correctly
- [ ] Create `tests/unit/entrypoints/cli/commands/test_diagnose.py`
  - [ ] Test diagnose loads ValidationResult
  - [ ] Test failure analysis output
- [ ] Create `tests/unit/adapters/audit/test_trail.py`
  - [ ] Test audit trail appends correctly
  - [ ] Test all record methods

### Integration Tests
- [ ] Create `tests/integration/cli/test_impl_flow.py`
  - [ ] Test full impl -> review -> apply flow
  - [ ] Test audit trail records all steps
  - [ ] Test artifacts are created correctly

## Acceptance Criteria

- [ ] `rice-factor impl <file>` generates diff and saves to audit/diffs/
- [ ] `rice-factor review` shows pending diff with approval options
- [ ] `rice-factor apply` applies approved diff with confirmation
- [ ] `rice-factor test` runs tests and creates ValidationResult
- [ ] `rice-factor diagnose` analyzes failures from ValidationResult
- [ ] All commands respect phase gating
- [ ] Audit trail records all operations
- [ ] `--dry-run` works for impl and apply
- [ ] All tests pass (45+ tests)
- [ ] mypy passes
- [ ] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/commands/impl.py` | Impl command |
| `rice_factor/entrypoints/cli/commands/review.py` | Review command |
| `rice_factor/entrypoints/cli/commands/apply.py` | Apply command |
| `rice_factor/entrypoints/cli/commands/test.py` | Test command |
| `rice_factor/entrypoints/cli/commands/diagnose.py` | Diagnose command |
| `rice_factor/domain/services/diff_service.py` | Diff service (stub) |
| `rice_factor/adapters/audit/trail.py` | Audit trail adapter |
| `rice_factor/entrypoints/cli/main.py` | Register new commands |
| `tests/unit/domain/services/test_diff_service.py` | Diff service tests |
| `tests/unit/entrypoints/cli/commands/test_impl.py` | Impl tests |
| `tests/unit/entrypoints/cli/commands/test_review.py` | Review tests |
| `tests/unit/entrypoints/cli/commands/test_apply.py` | Apply tests |
| `tests/unit/entrypoints/cli/commands/test_test.py` | Test command tests |
| `tests/unit/entrypoints/cli/commands/test_diagnose.py` | Diagnose tests |
| `tests/unit/adapters/audit/test_trail.py` | Audit trail tests |
| `tests/integration/cli/test_impl_flow.py` | Integration tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
