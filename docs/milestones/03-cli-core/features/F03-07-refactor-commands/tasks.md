# Feature: F03-07 Refactor Commands

## Status: Complete

## Description

Implement the `rice-factor refactor` subcommand app with check, dry-run, and apply commands for structural refactoring operations. Includes capability verification and full test suite integration.

## Requirements Reference

- M03-U-003: All commands shall support `--dry-run` where applicable
- M03-U-004: All destructive commands shall require confirmation
- Commands Table:
  - `rice-factor plan refactor <goal>` - Generate RefactorPlan (P1) [in F03-03]
  - `rice-factor refactor check` - Verify refactor capability support (P1)
  - `rice-factor refactor dry-run` - Preview refactor (P1)
  - `rice-factor refactor apply` - Apply refactor (P1)

## Tasks

### Refactor Subcommand App
- [x] Update `rice_factor/entrypoints/cli/commands/refactor.py`
  - [x] Create `app = typer.Typer()` subcommand app
  - [x] Register app in main.py with `app.add_typer(refactor.app, name="refactor")`

### Capability Service (Stub)
- [x] Create `rice_factor/domain/services/capability_service.py`
  - [x] Define `CapabilityService` class
  - [x] Define `CAPABILITY_MATRIX` - supported operations per language
  - [x] Implement `check_capabilities(plan)` - verify all operations supported
  - [x] Implement `get_unsupported_operations(plan)` - list unsupported
  - [x] Implement `is_operation_supported(operation)` - single check
  - [x] Implement `get_supported_operations()` - all supported for language
  - [x] Implement `get_capability_summary(plan)` - dict mapping operation to status

### Refactor Check Command
- [x] Implement `@app.command("check")`
  - [x] Check phase (must be TEST_LOCKED+)
  - [x] Load RefactorPlan artifact via ArtifactResolver
  - [x] Call CapabilityService for capability checks
  - [x] Display capability table with Rich Table
  - [x] Display supported operations with green checkmarks
  - [x] Display unsupported operations with red X
  - [x] Return non-zero exit if any unsupported
  - [x] Display helpful message for unsupported operations

### Refactor Dry-Run Command
- [x] Implement `@app.command("dry-run")`
  - [x] Check phase (must be TEST_LOCKED+)
  - [x] Load RefactorPlan artifact
  - [x] Check capabilities (fail early if unsupported)
  - [x] Generate refactor diffs via RefactorExecutor.preview()
  - [x] Display diffs with syntax highlighting (Rich Syntax)
  - [x] Display summary of changes
  - [x] No actual file modifications

### Refactor Apply Command
- [x] Implement `@app.command("apply")`
  - [x] Check phase (must be TEST_LOCKED+)
  - [x] Load RefactorPlan artifact
  - [x] Verify RefactorPlan is approved
  - [x] Check capabilities (fail early if unsupported)
  - [x] Display preview of changes with Rich Panel
  - [x] Require confirmation (typer.confirm)
  - [x] Execute refactor operations via RefactorExecutor
  - [x] Display test suite message (stub)
  - [x] Record in audit trail
  - [x] Support `--dry-run` option
  - [x] Support `--yes` to skip confirmation

### Refactor Executor (Stub)
- [x] Create `rice_factor/domain/services/refactor_executor.py`
  - [x] Define `RefactorExecutor` class
  - [x] Define `RefactorDiff` dataclass (file_path, before, after, operation)
  - [x] Define `RefactorResult` dataclass (success, operations_applied, diffs, error_message)
  - [x] Implement `preview(plan)` - generate preview diffs
  - [x] Implement `execute(plan)` - stub execution, returns RefactorResult
  - [x] Implement `execute_operation(operation)` - stub single operation

### Rich Output
- [x] Display capability check results in Rich Table
  - [x] Columns: Operation, Type, Status
  - [x] Color-coded status (green for supported, red for unsupported)
- [x] Display refactor preview in Rich Panel
- [x] Display diffs with Rich Syntax highlighting
- [x] Summary messages with counts

### Unit Tests
- [x] Create `tests/unit/domain/services/test_capability_service.py` (22 tests)
  - [x] Test initialization with language
  - [x] Test initialization normalizes language to lowercase
  - [x] Test default language is python
  - [x] Test is_operation_supported() for each operation type
  - [x] Test unsupported language returns False
  - [x] Test get_supported_operations() returns all for python
  - [x] Test get_supported_operations() returns subset for go
  - [x] Test get_supported_operations() returns empty for unknown
  - [x] Test get_unsupported_operations() returns empty when all supported
  - [x] Test get_unsupported_operations() returns unsupported list
  - [x] Test get_unsupported_operations() deduplicates
  - [x] Test check_capabilities() returns True when all supported
  - [x] Test check_capabilities() returns False when unsupported
  - [x] Test get_capability_summary() returns dict
  - [x] Test CAPABILITY_MATRIX has all expected languages
- [x] Create `tests/unit/domain/services/test_refactor_executor.py` (14 tests)
  - [x] Test initialization with project_path
  - [x] Test preview() returns list of diffs
  - [x] Test preview() generates diff for each operation
  - [x] Test preview() with no operations
  - [x] Test execute() returns RefactorResult
  - [x] Test execute() success property
  - [x] Test execute() tracks operations
  - [x] Test execute() counts applied operations
  - [x] Test execute() includes diffs
  - [x] Test execute_operation() returns True
  - [x] Test RefactorDiff has required fields
  - [x] Test RefactorResult has required fields
  - [x] Test RefactorResult with error
- [x] Create `tests/unit/entrypoints/cli/commands/test_refactor.py` (20 tests)
  - [x] Test `refactor --help` shows subcommands
  - [x] Test `refactor check --help` shows description
  - [x] Test `refactor check` requires init
  - [x] Test `refactor check` requires RefactorPlan
  - [x] Test `refactor check` shows supported operations
  - [x] Test `refactor dry-run --help` shows description
  - [x] Test `refactor dry-run` requires init
  - [x] Test `refactor dry-run` requires RefactorPlan
  - [x] Test `refactor dry-run` shows preview
  - [x] Test `refactor apply --help` shows description
  - [x] Test `refactor apply --help` shows --dry-run option
  - [x] Test `refactor apply` requires init
  - [x] Test `refactor apply` requires RefactorPlan
  - [x] Test `refactor apply` requires approved plan
  - [x] Test `refactor apply` requires confirmation
  - [x] Test `refactor apply --dry-run` doesn't execute
  - [x] Test `refactor apply --yes` skips confirmation
  - [x] Test phase gating for check command
  - [x] Test phase gating for dry-run command
  - [x] Test phase gating for apply command

### Integration Tests
- [ ] Create `tests/integration/cli/test_refactor_flow.py` (Deferred to M07)
  - [ ] Test full plan refactor -> check -> dry-run -> apply flow
  - [ ] Test audit trail records operations
  - [ ] Test test suite runs after apply

## Acceptance Criteria

- [x] `rice-factor refactor --help` shows all refactor subcommands
- [x] `rice-factor refactor check` verifies capability support
- [x] `rice-factor refactor dry-run` shows preview without changes
- [x] `rice-factor refactor apply` applies with confirmation
- [x] Apply command displays test suite message (stub)
- [x] Unsupported operations fail early with helpful messages
- [x] Phase gating prevents execution before TEST_LOCKED
- [x] All tests pass (56 new tests: 22 capability + 14 executor + 20 commands)
- [x] mypy passes
- [x] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/services/capability_service.py` | Capability verification service (created) |
| `rice_factor/domain/services/refactor_executor.py` | Refactor execution stub (created) |
| `rice_factor/domain/services/__init__.py` | Export new services |
| `rice_factor/entrypoints/cli/commands/refactor.py` | Refactor subcommand app (rewritten) |
| `rice_factor/entrypoints/cli/main.py` | Register refactor.app |
| `schemas/refactor_plan.schema.json` | Fixed null constraints and from_path/to_path |
| `pyproject.toml` | Added B008 ignore, TC002 per-file ignore for tests |
| `tests/unit/domain/services/test_capability_service.py` | Capability tests (22 tests) |
| `tests/unit/domain/services/test_refactor_executor.py` | Executor tests (14 tests) |
| `tests/unit/entrypoints/cli/commands/test_refactor.py` | Command tests (20 tests) |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - 631 total tests passing |
