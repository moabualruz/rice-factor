# Feature: F03-05 Implementation Commands

## Status: Complete

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
- [x] Create `rice_factor/entrypoints/cli/commands/impl.py`
  - [x] Accept `file` argument (target file path)
  - [x] Check phase (must be TEST_LOCKED+)
  - [x] Load ImplementationPlan for the file
  - [x] Stub: Generate placeholder diff
  - [x] Save diff to `audit/diffs/<timestamp>_<file>.diff`
  - [x] Display diff preview with syntax highlighting
  - [x] Support `--dry-run` option

### Diff Service (Stub)
- [x] Create `rice_factor/domain/services/diff_service.py`
  - [x] Define `DiffService` class
  - [x] Implement `generate_diff(plan, file)` - stub returns mock diff
  - [x] Implement `save_diff(diff, file)` - save to audit/diffs/
  - [x] Implement `load_pending_diff()` - get latest unapproved diff
  - [x] Implement `approve_diff(diff_id)` - mark diff as approved
  - [x] Implement `get_diff_status(diff_id)` - check if approved
  - [x] Implement `reject_diff(diff_id)` - mark diff as rejected
  - [x] Implement `mark_applied(diff_id)` - mark diff as applied
  - [x] Implement `load_approved_diff()` - get latest approved diff
  - [x] Implement `list_diffs(status)` - list diffs by status

### Review Command
- [x] Create `rice_factor/entrypoints/cli/commands/review.py`
  - [x] Load latest unapproved diff
  - [x] Display diff with syntax highlighting
  - [x] Prompt: approve / reject / skip
  - [x] Update diff status based on choice
  - [x] Record in audit trail

### Apply Command
- [x] Create `rice_factor/entrypoints/cli/commands/apply.py`
  - [x] Check for approved diff
  - [x] Display diff preview
  - [x] Require confirmation (--yes to skip)
  - [x] Stub: Apply diff (log operation)
  - [x] Record in audit log
  - [x] Support `--dry-run` option

### Test Command
- [x] Create `rice_factor/entrypoints/cli/commands/test.py`
  - [x] Stub: Run native test runner
  - [x] Create ValidationResult artifact with mock results
  - [x] Save ValidationResult via ArtifactService
  - [x] Display results with Rich table
  - [x] Return exit code based on pass/fail
  - [x] Record in audit trail

### Diagnose Command
- [x] Create `rice_factor/entrypoints/cli/commands/diagnose.py`
  - [x] Load latest ValidationResult artifact
  - [x] Analyze failures (stub analysis)
  - [x] Display failure summary
  - [x] Suggest next steps

### Audit Trail
- [x] Create `rice_factor/adapters/audit/trail.py`
  - [x] Define `AuditTrail` class with `AuditEntry` and `AuditAction` enums
  - [x] Implement `record_diff_generated(file, diff_path, diff_id)`
  - [x] Implement `record_diff_approved(diff_id, approver)`
  - [x] Implement `record_diff_rejected(diff_id, reason)`
  - [x] Implement `record_diff_applied(diff_id)`
  - [x] Implement `record_test_run(passed, total_tests, failed_tests, result_id)`
  - [x] Implement `record_artifact_created(artifact_id, artifact_type)`
  - [x] Implement `record_artifact_approved(artifact_id, approver)`
  - [x] Implement `record_scaffold_created(files_created, files_skipped)`
  - [x] Implement `record_override(resource, reason, approver)`
  - [x] Save to `audit/trail.json` (append-only)

### Unit Tests
- [x] Create `tests/unit/domain/services/test_diff_service.py` (17 tests)
  - [x] Test `generate_diff()` returns valid diff format
  - [x] Test `save_diff()` creates file in correct location
  - [x] Test `load_pending_diff()` returns latest unapproved
  - [x] Test `approve_diff()` updates status
  - [x] Test `reject_diff()` updates status
  - [x] Test `mark_applied()` updates status
  - [x] Test `load_approved_diff()` returns latest approved
  - [x] Test `list_diffs()` with status filter
- [x] Create `tests/unit/entrypoints/cli/commands/test_impl.py` (10 tests)
  - [x] Test impl command help
  - [x] Test impl command requires initialization
  - [x] Test impl command requires TEST_LOCKED phase
  - [x] Test impl generates and saves diff
  - [x] Test impl creates audit entry
  - [x] Test `--dry-run` doesn't save diff
- [x] Create `tests/unit/entrypoints/cli/commands/test_review.py` (10 tests)
  - [x] Test review shows pending diff
  - [x] Test approve choice updates status
  - [x] Test reject choice updates status
  - [x] Test skip leaves pending
  - [x] Test creates audit entries
- [x] Create `tests/unit/entrypoints/cli/commands/test_apply.py` (12 tests)
  - [x] Test apply requires approved diff
  - [x] Test apply requires confirmation
  - [x] Test --yes skips confirmation
  - [x] Test apply marks diff as applied
  - [x] Test `--dry-run` doesn't apply
  - [x] Test creates audit entry
- [x] Create `tests/unit/entrypoints/cli/commands/test_test.py` (9 tests)
  - [x] Test test command help
  - [x] Test test command requires initialization
  - [x] Test test runs and shows results
  - [x] Test test creates ValidationResult artifact
  - [x] Test test creates audit entry
  - [x] Test failure count displayed
- [x] Create `tests/unit/entrypoints/cli/commands/test_diagnose.py` (8 tests)
  - [x] Test diagnose loads ValidationResult
  - [x] Test failure analysis output
  - [x] Test no results message
  - [x] Test structured output
- [x] Create `tests/unit/adapters/audit/test_trail.py` (16 tests)
  - [x] Test audit trail creation
  - [x] Test all record methods
  - [x] Test get_entries filtering
  - [x] Test append-only behavior

### Integration Tests
- [ ] Create `tests/integration/cli/test_impl_flow.py` (Deferred to M07)
  - [ ] Test full impl -> review -> apply flow
  - [ ] Test audit trail records all steps
  - [ ] Test artifacts are created correctly

## Acceptance Criteria

- [x] `rice-factor impl <file>` generates diff and saves to audit/diffs/
- [x] `rice-factor review` shows pending diff with approval options
- [x] `rice-factor apply` applies approved diff with confirmation
- [x] `rice-factor test` runs tests and creates ValidationResult
- [x] `rice-factor diagnose` analyzes failures from ValidationResult
- [x] All commands respect phase gating
- [x] Audit trail records all operations
- [x] `--dry-run` works for impl and apply
- [x] All tests pass (103 new tests: 17 diff service + 16 audit + 10 impl + 10 review + 12 apply + 9 test + 8 diagnose + 21 existing)
- [x] mypy passes
- [x] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/commands/impl.py` | Impl command (rewritten) |
| `rice_factor/entrypoints/cli/commands/review.py` | Review command (created) |
| `rice_factor/entrypoints/cli/commands/apply.py` | Apply command (rewritten) |
| `rice_factor/entrypoints/cli/commands/test.py` | Test command (rewritten) |
| `rice_factor/entrypoints/cli/commands/diagnose.py` | Diagnose command (created) |
| `rice_factor/domain/services/diff_service.py` | Diff service (created) |
| `rice_factor/domain/services/__init__.py` | Export DiffService |
| `rice_factor/adapters/audit/__init__.py` | Audit adapters package (created) |
| `rice_factor/adapters/audit/trail.py` | Audit trail adapter (created) |
| `rice_factor/domain/artifacts/enums.py` | Added SYSTEM to CreatedBy |
| `rice_factor/entrypoints/cli/main.py` | Register review, diagnose commands |
| `schemas/artifact.schema.json` | Added 'system' to created_by enum |
| `tests/unit/domain/services/test_diff_service.py` | Diff service tests (17 tests) |
| `tests/unit/adapters/audit/__init__.py` | Audit tests package (created) |
| `tests/unit/adapters/audit/test_trail.py` | Audit trail tests (16 tests) |
| `tests/unit/entrypoints/cli/commands/test_impl.py` | Impl tests (10 tests) |
| `tests/unit/entrypoints/cli/commands/test_review.py` | Review tests (10 tests) |
| `tests/unit/entrypoints/cli/commands/test_apply.py` | Apply tests (12 tests) |
| `tests/unit/entrypoints/cli/commands/test_test.py` | Test command tests (9 tests) |
| `tests/unit/entrypoints/cli/commands/test_diagnose.py` | Diagnose tests (8 tests) |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - 533 total tests passing |
