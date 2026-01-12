# Feature: F06-05 ValidationResult Generator

## Status: Pending

## Description

Define the ValidatorPort protocol and validation types that form the foundation for all validators. This feature establishes the core abstractions (ValidatorPort, ValidationResult, ValidationContext) and implements the ValidationResultGenerator service that aggregates results and creates ValidationResult artifacts.

## Requirements Reference

- M06-U-002: Emit ValidationResult artifacts
- M06-U-004: Provide actionable error messages
- M06-U-005: Log all validation actions to audit trail
- M06-VR-001: ValidationResult shall conform to schema
- M06-VR-002: ValidationResult shall include target identifier
- M06-VR-003: ValidationResult shall include status (passed/failed)
- M06-VR-004: ValidationResult shall include error array for failures
- M06-VR-005: ValidationResult shall be saved to artifacts/validation/
- raw/02-Formal-Artifact-Schemas.md: Section 2.9 ValidationResult Schema
- raw/item-02-executor-design-and-pseudocode.md: Section 2.10 Audit Logging

## Tasks

### ValidatorPort Protocol Definition
- [ ] Create `rice_factor/domain/ports/validator.py`
  - [ ] Define `ValidatorPort` Protocol class
  - [ ] Define `name` property (unique validator identifier)
  - [ ] Define `validate(target, context) -> ValidationResult` method signature
  - [ ] Include docstrings with contract specification
  - [ ] No external dependencies (Protocol from typing only)

### Validation Types Module
- [ ] Create `rice_factor/domain/artifacts/validation_types.py`
  - [ ] Define `ValidationContext` dataclass
    - [ ] `repo_root: Path`
    - [ ] `language: str`
    - [ ] `config: dict` (optional settings)
  - [ ] Define `ValidationResult` dataclass
    - [ ] `target: str` (required)
    - [ ] `status: Literal["passed", "failed"]` (required)
    - [ ] `errors: list[str]` (optional, empty list default)
    - [ ] `validator: str` (which validator produced this)
    - [ ] `duration_ms: int` (execution time)
  - [ ] Implement `passed` property
  - [ ] Implement `to_dict()` method for serialization
  - [ ] Implement `to_payload()` method for artifact payload format

### Validation Error Types
- [ ] Create `rice_factor/domain/failures/validation_errors.py`
  - [ ] Define `ValidationError(RiceFactorError)` base class
  - [ ] Define `ValidatorConfigError(ValidationError)`
    - [ ] `LanguageNotSupportedError`
    - [ ] `ValidatorNotFoundError`
  - [ ] Define `ValidatorExecutionError(ValidationError)`
    - [ ] `CommandNotFoundError`
    - [ ] `ValidationTimeoutError`
    - [ ] `ProcessError`
  - [ ] Define `InvariantViolationError(ValidationError)`
    - [ ] `TestPlanNotLockedError`
    - [ ] `InvalidStatusError`
    - [ ] `MissingApprovalError`
    - [ ] `MissingDependencyError`

### ValidationResultGenerator Service
- [ ] Create `rice_factor/adapters/validators/validation_result_generator.py`
  - [ ] Define `ValidationResultGenerator` class
  - [ ] Implement `aggregate_results(results: list[ValidationResult]) -> ValidationResult`
    - [ ] Overall status = "passed" only if ALL pass
    - [ ] Combine all error messages
  - [ ] Implement `generate_artifact(result: ValidationResult, artifacts_dir: Path) -> Path`
    - [ ] Create ValidationResult artifact with envelope
    - [ ] Save to `artifacts/validation/<uuid>.json`
    - [ ] Return path to saved artifact
  - [ ] Implement `emit_audit_log(result: ValidationResult, audit_dir: Path)`
    - [ ] Append to `audit/validation.log`
    - [ ] Include timestamp, validator, target, status, duration

### Port and Type Exports
- [ ] Update `rice_factor/domain/ports/__init__.py`
  - [ ] Export `ValidatorPort`
- [ ] Update `rice_factor/domain/artifacts/__init__.py`
  - [ ] Export `ValidationContext`
  - [ ] Export `ValidationResult`
- [ ] Update `rice_factor/domain/failures/__init__.py`
  - [ ] Export all validation error types
- [ ] Create `rice_factor/adapters/validators/__init__.py`
  - [ ] Export `ValidationResultGenerator`

### Unit Tests
- [ ] Create `tests/unit/domain/ports/test_validator.py`
  - [ ] Test `ValidatorPort` is a valid Protocol
  - [ ] Test protocol methods are defined
- [ ] Create `tests/unit/domain/artifacts/test_validation_types.py`
  - [ ] Test `ValidationContext` creation
  - [ ] Test `ValidationResult` creation for pass case
  - [ ] Test `ValidationResult` creation for fail case
  - [ ] Test `ValidationResult.passed` property
  - [ ] Test `ValidationResult.to_dict()` serialization
  - [ ] Test `ValidationResult.to_payload()` artifact format
- [ ] Create `tests/unit/domain/failures/test_validation_errors.py`
  - [ ] Test error hierarchy (all errors inherit correctly)
  - [ ] Test each error type can be instantiated
  - [ ] Test error messages include relevant details
- [ ] Create `tests/unit/adapters/validators/test_validation_result_generator.py`
  - [ ] Test `aggregate_results` with all pass
  - [ ] Test `aggregate_results` with one fail
  - [ ] Test `aggregate_results` with multiple fails
  - [ ] Test `generate_artifact` creates valid artifact
  - [ ] Test `generate_artifact` saves to correct path
  - [ ] Test `emit_audit_log` appends log entry

## Acceptance Criteria

- [ ] `ValidatorPort` Protocol defined in `domain/ports/validator.py`
- [ ] `ValidationContext` and `ValidationResult` types defined
- [ ] Complete validation error hierarchy defined
- [ ] `ValidationResultGenerator` aggregates and saves results
- [ ] Audit logging implemented
- [ ] Protocol has no external dependencies (stdlib only)
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/domain/ports/validator.py` | CREATE | Validator port protocol definition |
| `rice_factor/domain/artifacts/validation_types.py` | CREATE | Validation context and result types |
| `rice_factor/domain/failures/validation_errors.py` | CREATE | Validation error hierarchy |
| `rice_factor/adapters/validators/__init__.py` | CREATE | Export validators |
| `rice_factor/adapters/validators/validation_result_generator.py` | CREATE | Result aggregation and artifact generation |
| `rice_factor/domain/ports/__init__.py` | UPDATE | Export ValidatorPort |
| `rice_factor/domain/artifacts/__init__.py` | UPDATE | Export validation types |
| `rice_factor/domain/failures/__init__.py` | UPDATE | Export validation errors |
| `tests/unit/domain/ports/test_validator.py` | CREATE | Port tests |
| `tests/unit/domain/artifacts/test_validation_types.py` | CREATE | Validation types tests |
| `tests/unit/domain/failures/test_validation_errors.py` | CREATE | Error tests |
| `tests/unit/adapters/validators/test_validation_result_generator.py` | CREATE | Generator tests |

## Dependencies

- None (foundation feature)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
