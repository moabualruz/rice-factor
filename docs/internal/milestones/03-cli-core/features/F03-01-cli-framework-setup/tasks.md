# Feature: F03-01 CLI Framework Setup

## Status: Complete

## Description

Set up the CLI framework foundation including shared utilities, phase gating service, global options, and Rich console integration for consistent user experience across all commands.

## Requirements Reference

- M03-U-001: The CLI shall be invoked via the `rice-factor` command
- M03-U-002: All commands shall support `--help` for documentation
- M03-U-003: All commands shall support `--dry-run` where applicable
- M03-U-004: All destructive commands shall require confirmation
- M03-U-005: The CLI shall provide colored, formatted output via Rich

## Tasks

### CLI Utilities Module
- [x] Create `rice_factor/entrypoints/cli/utils.py`
  - [x] Implement Rich console singleton
  - [x] Implement `success(message)` - green checkmark output
  - [x] Implement `warning(message)` - yellow warning output
  - [x] Implement `error(message)` - red X output
  - [x] Implement `info(message)` - blue info output
  - [x] Implement `confirm(message, default)` - confirmation prompt
  - [x] Implement `confirm_destructive(action, target)` - explicit confirmation
  - [x] Implement `display_error(title, message, hint)` - Rich panel error
  - [x] Implement `display_table(title, columns, rows)` - Rich table helper
  - [x] Implement `display_panel(title, content)` - Rich panel helper

### Error Handler Decorator
- [x] Implement `@handle_errors` decorator in utils.py
  - [x] Catch `PhaseError` and display user-friendly message
  - [x] Catch `ArtifactNotFoundError` and display helpful hint
  - [x] Catch `ArtifactValidationError` and display details
  - [x] Catch `ConfirmationRequired` and exit gracefully
  - [x] Catch generic exceptions with stack trace in verbose mode

### Dry-Run Decorator
- [x] Implement `@supports_dry_run` decorator
  - [x] Intercept execution when `--dry-run` is True
  - [x] Display "would do" message instead of executing
  - [x] Return early without side effects

### Phase Gating Service
- [x] Create `rice_factor/domain/services/phase_service.py`
  - [x] Define `Phase` enum (UNINIT, INIT, PLANNING, SCAFFOLDED, TEST_LOCKED, IMPLEMENTING)
  - [x] Implement `PhaseService` class
  - [x] Implement `get_current_phase()` - determine phase from artifacts
  - [x] Implement `can_execute(command)` - check if command is allowed
  - [x] Implement `get_blocking_reason(command)` - return user-friendly message
  - [x] Define command-to-phase prerequisites mapping

### CLI Error Types
- [x] Create `rice_factor/domain/failures/cli_errors.py`
  - [x] Define `CLIError` base class
  - [x] Define `PhaseError` for phase violations
  - [x] Define `MissingPrerequisiteError` for missing requirements
  - [x] Define `ConfirmationRequired` for unconfirmed actions

### Global Options
- [x] Add global `--verbose` option to main app
- [x] Add global `--quiet` option for minimal output
- [x] Wire global options through Typer callback

### Main CLI App Enhancement
- [x] Update `rice_factor/entrypoints/cli/main.py`
  - [x] Import and use console from utils
  - [x] Add version callback (`--version`)
  - [x] Add global options callback
  - [x] Ensure `--help` works for all commands

### Unit Tests
- [x] Create `tests/unit/entrypoints/cli/test_utils.py`
  - [x] Test `success()` output format
  - [x] Test `warning()` output format
  - [x] Test `error()` output format
  - [x] Test `confirm()` behavior
  - [x] Test `confirm_destructive()` behavior
  - [x] Test `@handle_errors` decorator
  - [x] Test `@supports_dry_run` decorator
- [x] Create `tests/unit/domain/services/test_phase_service.py`
  - [x] Test phase detection for UNINIT (no .project/)
  - [x] Test phase detection for INIT (.project/ exists)
  - [x] Test phase detection for PLANNING (ProjectPlan approved)
  - [x] Test phase detection for SCAFFOLDED (scaffold executed)
  - [x] Test phase detection for TEST_LOCKED (TestPlan locked)
  - [x] Test `can_execute()` for valid phase transitions
  - [x] Test `can_execute()` for blocked commands
  - [x] Test `get_blocking_reason()` messages
- [x] Create `tests/unit/domain/failures/test_cli_errors.py`
  - [x] Test error class hierarchy
  - [x] Test error message formatting

## Acceptance Criteria

- [x] `rice-factor --help` displays all available commands
- [x] `rice-factor --version` displays version
- [x] All output uses consistent Rich formatting
- [x] Phase gating correctly blocks commands based on project state
- [x] Error messages are clear and actionable
- [x] All tests pass (77 new tests, 274 total)
- [x] mypy passes
- [x] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/utils.py` | Shared CLI utilities and Rich helpers |
| `rice_factor/domain/services/phase_service.py` | Phase gating service |
| `rice_factor/domain/failures/cli_errors.py` | CLI-specific error types |
| `rice_factor/domain/failures/__init__.py` | Updated exports for CLI errors |
| `rice_factor/domain/services/__init__.py` | Updated exports for Phase service |
| `rice_factor/entrypoints/cli/main.py` | Enhanced with global options |
| `tests/unit/entrypoints/cli/test_utils.py` | Utils unit tests (26 tests) |
| `tests/unit/domain/services/test_phase_service.py` | Phase service tests (31 tests) |
| `tests/unit/domain/failures/test_cli_errors.py` | Error types tests (20 tests) |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implementation complete - all tasks done, 77 new tests passing |
