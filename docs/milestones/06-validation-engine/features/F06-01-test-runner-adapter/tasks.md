# Feature: F06-01 Test Runner Adapter

## Status: Pending

## Description

Implement the TestRunnerAdapter that executes native test commands for different programming languages. The adapter detects the project language, runs the appropriate test command, captures output, and returns a ValidationResult. This is the core P0 feature for the validation engine.

## Requirements Reference

- M06-U-001: Use native test runners
- M06-U-002: Emit ValidationResult artifacts
- M06-U-006: Be deterministic and reproducible
- M06-U-007: Fail fast on first validation failure
- M06-U-008: Support language-specific validators
- M06-TR-001: Detect language from project configuration
- M06-TR-002: Use exit code to determine pass/fail
- M06-TR-003: Capture stdout/stderr for error messages
- M06-TR-004: Support timeout configuration
- M06-TR-005: Support test commands for Python, Rust, Go, JavaScript, TypeScript, Java
- raw/item-02-executor-design-and-pseudocode.md: Section 2.8 Test Runner

## Tasks

### TestRunnerAdapter Implementation
- [ ] Create `rice_factor/adapters/validators/test_runner_adapter.py`
  - [ ] Define `TestRunnerAdapter` class implementing `ValidatorPort`
  - [ ] Implement `name` property returning "test_runner"
  - [ ] Implement `validate(target, context) -> ValidationResult`
    - [ ] Get test command for language
    - [ ] Execute subprocess with timeout
    - [ ] Capture stdout/stderr
    - [ ] Determine pass/fail from exit code
    - [ ] Parse output for error messages
    - [ ] Return ValidationResult

### Language Test Command Registry
- [ ] Define test commands mapping in `TestRunnerAdapter`
  - [ ] Python: `["pytest"]` or `["python", "-m", "pytest"]`
  - [ ] Rust: `["cargo", "test"]`
  - [ ] Go: `["go", "test", "./..."]`
  - [ ] JavaScript: `["npm", "test"]`
  - [ ] TypeScript: `["npm", "test"]`
  - [ ] Java: `["mvn", "test"]`
- [ ] Implement `get_test_command(language: str) -> list[str] | None`
- [ ] Return None for unsupported languages

### Test Output Parsing
- [ ] Implement `parse_test_output(stdout: str, stderr: str, language: str) -> list[str]`
  - [ ] Extract test failure messages
  - [ ] Format errors with file/line information when available
  - [ ] Limit error count to prevent huge outputs
  - [ ] Handle language-specific output formats

### Subprocess Execution
- [ ] Implement safe subprocess execution
  - [ ] Use `subprocess.run` with `capture_output=True`
  - [ ] Set `cwd` to repo_root
  - [ ] Apply timeout from config (default 5 minutes)
  - [ ] Handle `TimeoutExpired` exception
  - [ ] Handle `FileNotFoundError` for missing commands

### Configuration Support
- [ ] Support timeout configuration via ValidationContext
- [ ] Support custom test command override via context.config
- [ ] Support test path/filter arguments

### Exports
- [ ] Update `rice_factor/adapters/validators/__init__.py`
  - [ ] Export `TestRunnerAdapter`

### Unit Tests
- [ ] Create `tests/unit/adapters/validators/test_test_runner_adapter.py`
  - [ ] Test `name` property returns "test_runner"
  - [ ] Test `validate` returns ValidationResult
  - [ ] Test passing tests return status="passed"
  - [ ] Test failing tests return status="failed" with errors
  - [ ] Test timeout handling
  - [ ] Test missing command handling
  - [ ] Test each supported language command

### Integration Tests
- [ ] Create `tests/integration/validators/test_test_runner_integration.py`
  - [ ] Test with actual Python project (pytest)
  - [ ] Test with actual test failures
  - [ ] Test timeout behavior

## Acceptance Criteria

- [ ] `TestRunnerAdapter` implements `ValidatorPort`
- [ ] Supports all 6 languages: Python, Rust, Go, JavaScript, TypeScript, Java
- [ ] Exit code 0 returns status="passed"
- [ ] Non-zero exit code returns status="failed" with error messages
- [ ] Timeout configuration works
- [ ] Missing command returns clear error
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/validators/test_runner_adapter.py` | CREATE | Test runner adapter implementation |
| `rice_factor/adapters/validators/__init__.py` | UPDATE | Export TestRunnerAdapter |
| `tests/unit/adapters/validators/test_test_runner_adapter.py` | CREATE | Unit tests |
| `tests/integration/validators/test_test_runner_integration.py` | CREATE | Integration tests |

## Dependencies

- F06-05: ValidationResult Generator (ValidatorPort, ValidationResult, ValidationContext)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
