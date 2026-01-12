# Feature: F06-02 Lint Runner Adapter

## Status: Pending

## Description

Implement the LintRunnerAdapter that executes native linting commands for different programming languages. The adapter follows the same pattern as TestRunnerAdapter, detecting project language, running the appropriate lint command, and returning a ValidationResult with any lint errors.

## Requirements Reference

- M06-U-003: Never auto-fix issues
- M06-U-004: Provide actionable error messages
- M06-U-008: Support language-specific validators
- M06-LR-001: Detect language from project configuration
- M06-LR-002: Parse linter output for error locations
- M06-LR-003: Report all lint errors, not just first
- M06-LR-004: Support linters for Python, Rust, Go, JavaScript, TypeScript

## Tasks

### LintRunnerAdapter Implementation
- [ ] Create `rice_factor/adapters/validators/lint_runner_adapter.py`
  - [ ] Define `LintRunnerAdapter` class implementing `ValidatorPort`
  - [ ] Implement `name` property returning "lint_runner"
  - [ ] Implement `validate(target, context) -> ValidationResult`
    - [ ] Get lint command for language
    - [ ] Execute subprocess
    - [ ] Capture stdout/stderr
    - [ ] Determine pass/fail from exit code
    - [ ] Parse output for lint errors
    - [ ] Return ValidationResult

### Language Lint Command Registry
- [ ] Define lint commands mapping in `LintRunnerAdapter`
  - [ ] Python: `["ruff", "check", "."]`
  - [ ] Rust: `["cargo", "clippy", "--", "-D", "warnings"]`
  - [ ] Go: `["golint", "./..."]`
  - [ ] JavaScript: `["eslint", "."]`
  - [ ] TypeScript: `["eslint", "."]`
- [ ] Implement `get_lint_command(language: str) -> list[str] | None`
- [ ] Return None for unsupported languages (lint is optional)

### Lint Output Parsing
- [ ] Implement `parse_lint_output(stdout: str, stderr: str, language: str) -> list[str]`
  - [ ] Parse ruff output format (file:line:col: message)
  - [ ] Parse clippy output format
  - [ ] Parse golint output format
  - [ ] Parse eslint output format
  - [ ] Extract file, line, column, and message
  - [ ] Format as actionable error strings
  - [ ] Report ALL errors (not just first)

### Optional Lint Behavior
- [ ] If no linter command for language, return status="passed"
  - [ ] Lint is optional enhancement, not blocking
  - [ ] Log that lint was skipped
- [ ] If linter not installed (command not found), return status="passed"
  - [ ] Don't fail validation for missing linter
  - [ ] Include warning in result

### Subprocess Execution
- [ ] Use same subprocess pattern as TestRunnerAdapter
  - [ ] `subprocess.run` with `capture_output=True`
  - [ ] Set `cwd` to repo_root
  - [ ] No timeout needed for lint (fast operation)
  - [ ] Handle `FileNotFoundError` gracefully

### Exports
- [ ] Update `rice_factor/adapters/validators/__init__.py`
  - [ ] Export `LintRunnerAdapter`

### Unit Tests
- [ ] Create `tests/unit/adapters/validators/test_lint_runner_adapter.py`
  - [ ] Test `name` property returns "lint_runner"
  - [ ] Test `validate` returns ValidationResult
  - [ ] Test clean code returns status="passed"
  - [ ] Test lint errors return status="failed" with errors
  - [ ] Test missing linter returns status="passed" (optional)
  - [ ] Test unsupported language returns status="passed"
  - [ ] Test output parsing for each supported language

### Integration Tests
- [ ] Create `tests/integration/validators/test_lint_runner_integration.py`
  - [ ] Test with actual Python code (ruff)
  - [ ] Test with lint errors
  - [ ] Test with clean code

## Acceptance Criteria

- [ ] `LintRunnerAdapter` implements `ValidatorPort`
- [ ] Supports 5 languages: Python, Rust, Go, JavaScript, TypeScript
- [ ] Exit code 0 returns status="passed"
- [ ] Non-zero exit code returns status="failed" with parsed errors
- [ ] Missing linter does not block validation (returns passed)
- [ ] Unsupported language does not block validation
- [ ] All lint errors reported (not just first)
- [ ] Error messages include file/line information
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/validators/lint_runner_adapter.py` | CREATE | Lint runner adapter implementation |
| `rice_factor/adapters/validators/__init__.py` | UPDATE | Export LintRunnerAdapter |
| `tests/unit/adapters/validators/test_lint_runner_adapter.py` | CREATE | Unit tests |
| `tests/integration/validators/test_lint_runner_integration.py` | CREATE | Integration tests |

## Dependencies

- F06-05: ValidationResult Generator (ValidatorPort, ValidationResult, ValidationContext)
- F06-01: Test Runner Adapter (pattern reference)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
