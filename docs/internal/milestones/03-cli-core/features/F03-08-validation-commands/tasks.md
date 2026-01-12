# Feature: F03-08 Validation Commands

## Status: Complete

## Description

Implement the `rice-factor validate` command to run all validations including schema validation, architecture rules, tests, and linting. Aggregates results into a ValidationResult artifact.

## Requirements Reference

- M03-U-005: The CLI shall provide colored, formatted output via Rich
- Commands Table: `rice-factor validate` - Run all validations (P1)

## Tasks

### Validation Orchestrator
- [x] Create `rice_factor/domain/services/validation_orchestrator.py`
  - [x] Define `ValidationOrchestrator` class
  - [x] Define `ValidationStep` enum (SCHEMA, ARCHITECTURE, TESTS, LINT)
  - [x] Define `StepResult` dataclass for per-step results
  - [x] Define `ValidationResult` dataclass for aggregated results
  - [x] Implement `run_all()` - execute all validation steps
  - [x] Implement `run_step(step)` - execute single step
  - [x] Aggregate results with overall_status, step_results
  - [x] Handle partial failures (continue after failures)

### Schema Validation
- [x] Implement schema validation step
  - [x] Use FilesystemStorageAdapter to list artifacts
  - [x] Load artifacts (validates via ArtifactValidator on load)
  - [x] Collect validation errors
  - [x] Return per-artifact validation results

### Architecture Rules (Stub)
- [x] Implement architecture validation step (stub)
  - [x] Return PASSED with stub details
  - [x] Mark as "pending M06" in output

### Test Execution (Stub)
- [x] Implement test execution step (stub)
  - [x] Return PASSED with stub details
  - [x] Mark as "pending M06" in output

### Lint Execution (Stub)
- [x] Implement lint execution step (stub)
  - [x] Return PASSED with stub details
  - [x] Mark as "pending M06" in output

### Validate Command
- [x] Update `rice_factor/entrypoints/cli/commands/validate.py`
  - [x] Support running all validations (default)
  - [x] Support `--step` option to run specific step
  - [x] Support `--path` option for project root
  - [x] Support `--save/--no-save` option for artifact saving
  - [x] Check phase (must be initialized)
  - [x] Display results in Rich Table
  - [x] Create ValidationResult artifact
  - [x] Save artifact via storage adapter
  - [x] Return non-zero exit code if any failures

### Rich Output
- [x] Display validation results in Rich Table
  - [x] Columns: Step, Status, Errors, Details
  - [x] Color-coded by status (green/red)
  - [x] Show "stubbed" indicator for stub steps
- [x] Display detailed errors for failed steps
- [x] Display summary with pass/fail counts
- [x] Display ValidationResult artifact ID when saved

### ValidationResult Payload
- [x] Use existing ValidationResultPayload
  - [x] target: "project"
  - [x] status: PASSED/FAILED
  - [x] errors: aggregated error list

### Unit Tests
- [x] Create `tests/unit/domain/services/test_validation_orchestrator.py` (22 tests)
  - [x] Test orchestrator initialization
  - [x] Test project_path property
  - [x] Test run_all() returns ValidationResult
  - [x] Test run_all() includes all steps
  - [x] Test run_all() has 4 step results
  - [x] Test run_all() returns PASSED when all pass
  - [x] Test run_step() for each step type
  - [x] Test schema validation with no artifacts dir
  - [x] Test schema validation with empty artifacts dir
  - [x] Test StepResult creation and properties
  - [x] Test ValidationResult creation and properties
  - [x] Test passed property
  - [x] Test failed_steps property
  - [x] Test error_count property
  - [x] Test ValidationStep enum values
- [x] Create `tests/unit/entrypoints/cli/commands/test_validate.py` (19 tests)
  - [x] Test validate --help shows description
  - [x] Test validate --help shows --step option
  - [x] Test validate --help shows --path option
  - [x] Test validate --help shows --save option
  - [x] Test validate requires initialization
  - [x] Test validate runs all validations
  - [x] Test validate shows results table
  - [x] Test validate shows passed summary
  - [x] Test --step schema runs only schema
  - [x] Test --step architecture runs only architecture
  - [x] Test --step tests runs only tests
  - [x] Test --step lint runs only lint
  - [x] Test invalid step fails
  - [x] Test validate saves artifact by default
  - [x] Test --no-save skips artifact
  - [x] Test artifact saved in artifacts dir
  - [x] Test stubbed steps show indicator

### Integration Tests
- [ ] Create `tests/integration/cli/test_validate_flow.py` (Deferred to M07)
  - [ ] Test full validation with artifacts present
  - [ ] Test validation results saved to artifacts/
  - [ ] Test schema validation catches invalid artifacts

## Acceptance Criteria

- [x] `rice-factor validate` runs all validation steps
- [x] `--step` option allows running specific validations
- [x] Schema validation lists artifacts via storage adapter
- [x] Architecture, tests, and lint are stubbed with clear messages
- [x] Results displayed in clear, formatted tables
- [x] ValidationResult artifact created and saved
- [x] Non-zero exit code on any failure
- [x] Partial failures don't prevent other validations
- [x] All tests pass (41 new tests: 22 orchestrator + 19 command)
- [x] mypy passes
- [x] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/services/validation_orchestrator.py` | Validation orchestrator (created) |
| `rice_factor/domain/services/__init__.py` | Export new classes |
| `rice_factor/entrypoints/cli/commands/validate.py` | Validate command (rewritten) |
| `tests/unit/domain/services/test_validation_orchestrator.py` | Orchestrator tests (22 tests) |
| `tests/unit/entrypoints/cli/commands/test_validate.py` | Command tests (19 tests) |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - 672 total tests passing |
