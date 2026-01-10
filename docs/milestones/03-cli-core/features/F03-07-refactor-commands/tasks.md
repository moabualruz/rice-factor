# Feature: F03-07 Refactor Commands

## Status: Pending

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
- [ ] Update `rice_factor/entrypoints/cli/commands/refactor.py`
  - [ ] Create `refactor_app = typer.Typer()` subcommand app
  - [ ] Register refactor_app in main.py with `app.add_typer(refactor_app, name="refactor")`

### Capability Service (Stub)
- [ ] Create `rice_factor/domain/services/capability_service.py`
  - [ ] Define `CapabilityService` class
  - [ ] Define supported operations per language (stub matrix)
  - [ ] Implement `check_capabilities(plan)` - verify all operations supported
  - [ ] Implement `get_unsupported_operations(plan)` - list unsupported
  - [ ] Implement `is_operation_supported(language, operation)` - single check

### Refactor Check Command
- [ ] Implement `@refactor_app.command("check")`
  - [ ] Check phase (must be TEST_LOCKED+)
  - [ ] Load RefactorPlan artifact
  - [ ] Call CapabilityService.check_capabilities()
  - [ ] Display supported operations with green checkmarks
  - [ ] Display unsupported operations with red X
  - [ ] Return non-zero exit if any unsupported
  - [ ] Display helpful message for unsupported operations

### Refactor Dry-Run Command
- [ ] Implement `@refactor_app.command("dry-run")`
  - [ ] Check phase (must be TEST_LOCKED+)
  - [ ] Load RefactorPlan artifact
  - [ ] Check capabilities (fail early if unsupported)
  - [ ] Stub: Generate refactor diffs for each operation
  - [ ] Display diffs with syntax highlighting
  - [ ] Display summary of changes
  - [ ] No actual file modifications

### Refactor Apply Command
- [ ] Implement `@refactor_app.command("apply")`
  - [ ] Check phase (must be TEST_LOCKED+)
  - [ ] Load RefactorPlan artifact
  - [ ] Verify RefactorPlan is approved
  - [ ] Check capabilities (fail early if unsupported)
  - [ ] Display preview of changes
  - [ ] Require confirmation
  - [ ] Stub: Apply refactor operations
  - [ ] Run full test suite after apply
  - [ ] Display test results
  - [ ] Record in audit trail
  - [ ] Support `--dry-run` option

### Refactor Operations (Stub)
- [ ] Create `rice_factor/domain/services/refactor_executor.py`
  - [ ] Define `RefactorExecutor` class
  - [ ] Implement `preview(plan)` - generate preview diffs
  - [ ] Implement `execute(plan)` - stub execution
  - [ ] Define operation handlers for each RefactorOperationType:
    - [ ] MOVE_FILE - stub file move
    - [ ] RENAME_SYMBOL - stub symbol rename
    - [ ] EXTRACT_INTERFACE - stub interface extraction
    - [ ] ENFORCE_DEPENDENCY - stub dependency enforcement

### Rich Output
- [ ] Display refactor operations in Rich Table
  - [ ] Columns: Operation, From, To, Status
  - [ ] Color-coded by operation type
- [ ] Display capability matrix
- [ ] Progress bar for multi-operation refactors
- [ ] Summary panel with totals

### Unit Tests
- [ ] Create `tests/unit/domain/services/test_capability_service.py`
  - [ ] Test check_capabilities() with all supported
  - [ ] Test check_capabilities() with unsupported operations
  - [ ] Test is_operation_supported() for each operation type
  - [ ] Test get_unsupported_operations()
- [ ] Create `tests/unit/domain/services/test_refactor_executor.py`
  - [ ] Test preview() generates diffs
  - [ ] Test execute() logs operations
  - [ ] Test each operation handler
- [ ] Create `tests/unit/entrypoints/cli/commands/test_refactor.py`
  - [ ] Test `refactor check` with supported operations
  - [ ] Test `refactor check` fails with unsupported
  - [ ] Test `refactor dry-run` shows preview
  - [ ] Test `refactor apply` requires approved plan
  - [ ] Test `refactor apply` requires confirmation
  - [ ] Test `refactor apply --dry-run` doesn't execute
  - [ ] Test phase gating for all commands
  - [ ] Test `--help` for all subcommands

### Integration Tests
- [ ] Create `tests/integration/cli/test_refactor_flow.py`
  - [ ] Test full plan refactor -> check -> dry-run -> apply flow
  - [ ] Test audit trail records operations
  - [ ] Test test suite runs after apply

## Acceptance Criteria

- [ ] `rice-factor refactor --help` shows all refactor subcommands
- [ ] `rice-factor refactor check` verifies capability support
- [ ] `rice-factor refactor dry-run` shows preview without changes
- [ ] `rice-factor refactor apply` applies with confirmation
- [ ] Apply command runs full test suite after completion
- [ ] Unsupported operations fail early with helpful messages
- [ ] Phase gating prevents execution before TEST_LOCKED
- [ ] All tests pass (30+ tests)
- [ ] mypy passes
- [ ] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/commands/refactor.py` | Refactor subcommand app |
| `rice_factor/domain/services/capability_service.py` | Capability verification |
| `rice_factor/domain/services/refactor_executor.py` | Refactor execution (stub) |
| `rice_factor/entrypoints/cli/main.py` | Register refactor_app |
| `tests/unit/domain/services/test_capability_service.py` | Capability tests |
| `tests/unit/domain/services/test_refactor_executor.py` | Executor tests |
| `tests/unit/entrypoints/cli/commands/test_refactor.py` | Command tests |
| `tests/integration/cli/test_refactor_flow.py` | Integration tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
