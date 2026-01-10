# Feature: F03-08 Validation Commands

## Status: Pending

## Description

Implement the `rice-factor validate` command to run all validations including schema validation, architecture rules, tests, and linting. Aggregates results into a ValidationResult artifact.

## Requirements Reference

- M03-U-005: The CLI shall provide colored, formatted output via Rich
- Commands Table: `rice-factor validate` - Run all validations (P1)

## Tasks

### Validation Orchestrator
- [ ] Create `rice_factor/domain/services/validation_orchestrator.py`
  - [ ] Define `ValidationOrchestrator` class
  - [ ] Define `ValidationStep` enum (SCHEMA, ARCHITECTURE, TESTS, LINT)
  - [ ] Implement `run_all()` - execute all validation steps
  - [ ] Implement `run_step(step)` - execute single step
  - [ ] Aggregate results into ValidationResult payload
  - [ ] Handle partial failures (continue after failures)

### Schema Validation
- [ ] Implement schema validation step
  - [ ] Use M02 ArtifactValidator
  - [ ] Validate all artifacts in artifacts/ directory
  - [ ] Collect schema validation errors
  - [ ] Return per-artifact validation results

### Architecture Rules (Stub)
- [ ] Implement architecture validation step (stub)
  - [ ] Stub: Load ArchitecturePlan
  - [ ] Stub: Check dependency rules
  - [ ] Stub: Return mock validation results
  - [ ] Mark as "pending M06" in output

### Test Execution (Stub)
- [ ] Implement test execution step (stub)
  - [ ] Stub: Detect test framework
  - [ ] Stub: Run test suite
  - [ ] Stub: Return mock test results
  - [ ] Mark as "pending M06" in output

### Lint Execution (Stub)
- [ ] Implement lint execution step (stub)
  - [ ] Stub: Detect linter configuration
  - [ ] Stub: Run linter
  - [ ] Stub: Return mock lint results
  - [ ] Mark as "pending M06" in output

### Validate Command
- [ ] Create `rice_factor/entrypoints/cli/commands/validate.py`
  - [ ] Support running all validations (default)
  - [ ] Support `--step` option to run specific step
  - [ ] Display progress for each validation step
  - [ ] Display results in Rich tables
  - [ ] Create ValidationResult artifact
  - [ ] Save artifact via ArtifactService
  - [ ] Return non-zero exit code if any failures

### Rich Output
- [ ] Display validation progress with Rich Progress
  - [ ] Spinner for each step
  - [ ] Success/failure status
- [ ] Display results in Rich Table
  - [ ] Columns: Step, Status, Errors, Duration
  - [ ] Color-coded by status (green/red/yellow)
- [ ] Display detailed errors in collapsible panels
- [ ] Display summary with pass/fail counts

### Validation Result
- [ ] Create comprehensive ValidationResult payload
  - [ ] Overall status (passed/failed)
  - [ ] Per-step results
  - [ ] Error details with file/line references
  - [ ] Timing information
  - [ ] Recommendations for fixing

### Unit Tests
- [ ] Create `tests/unit/domain/services/test_validation_orchestrator.py`
  - [ ] Test run_all() executes all steps
  - [ ] Test run_step() for each step
  - [ ] Test partial failure handling
  - [ ] Test result aggregation
- [ ] Create `tests/unit/entrypoints/cli/commands/test_validate.py`
  - [ ] Test validate runs all validations
  - [ ] Test `--step schema` runs only schema
  - [ ] Test `--step tests` runs only tests
  - [ ] Test results displayed correctly
  - [ ] Test ValidationResult artifact created
  - [ ] Test exit code on failure
  - [ ] Test `--help` shows documentation

### Integration Tests
- [ ] Create `tests/integration/cli/test_validate_flow.py`
  - [ ] Test full validation with artifacts present
  - [ ] Test validation results saved to artifacts/
  - [ ] Test schema validation catches invalid artifacts

## Acceptance Criteria

- [ ] `rice-factor validate` runs all validation steps
- [ ] `--step` option allows running specific validations
- [ ] Schema validation uses M02 validators
- [ ] Architecture, tests, and lint are stubbed with clear messages
- [ ] Results displayed in clear, formatted tables
- [ ] ValidationResult artifact created and saved
- [ ] Non-zero exit code on any failure
- [ ] Partial failures don't prevent other validations
- [ ] All tests pass (20+ tests)
- [ ] mypy passes
- [ ] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/services/validation_orchestrator.py` | Validation orchestrator |
| `rice_factor/entrypoints/cli/commands/validate.py` | Validate command |
| `rice_factor/entrypoints/cli/main.py` | Register command |
| `tests/unit/domain/services/test_validation_orchestrator.py` | Orchestrator tests |
| `tests/unit/entrypoints/cli/commands/test_validate.py` | Command tests |
| `tests/integration/cli/test_validate_flow.py` | Integration tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
