# Feature: F02-04 Schema Validation Engine

## Status: Complete

## Description

Implement the dual validation strategy using both Pydantic (Python type safety) and JSON Schema (language-agnostic validation).

## Requirements Reference

- M02-E-001: As soon as an artifact is loaded, the system shall validate it against its schema
- M02-E-002: As soon as validation fails, the system shall emit a detailed error with field-level messages
- M02-I-001: If an artifact fails schema validation, then the system shall reject the artifact

## Tasks

### Validator Port
- [x] Create `rice_factor/domain/ports/validator.py`
- [x] Define `ValidatorPort` protocol with:
  - [x] `validate(data: dict) -> ArtifactEnvelope`
  - [x] `validate_payload(data: dict, artifact_type: ArtifactType) -> BaseModel`
  - [x] `validate_json_schema(data: dict, artifact_type: ArtifactType | None) -> None`

### Validator Adapter
- [x] Create `rice_factor/adapters/validators/__init__.py`
- [x] Create `rice_factor/adapters/validators/schema.py`
- [x] Implement `ArtifactValidator` class:
  - [x] `validate()` method (full validation)
  - [x] `validate_payload()` method (payload only)
  - [x] `validate_json_schema()` method (JSON Schema only)
- [x] Load schemas from `schemas/` directory
- [x] Cache loaded schemas for performance (module-level cache)

### Error Handling
- [x] Update `rice_factor/domain/failures/errors.py`
- [x] Enhance `ArtifactValidationError` with:
  - [x] Field-level error messages (`field_path`)
  - [x] Expected vs actual value
  - [x] Details list for multiple errors
- [x] Convert Pydantic ValidationError to ArtifactValidationError
- [x] Convert jsonschema ValidationError to ArtifactValidationError

### Testing
- [x] Write unit tests for Pydantic validation
- [x] Write unit tests for JSON Schema validation
- [x] Write tests for full artifact validation
- [x] Test error messages are actionable

## Acceptance Criteria

- [x] Valid artifacts pass both Pydantic and JSON Schema validation
- [x] Invalid artifacts are rejected with clear error messages
- [x] Error messages include field path and expected type
- [x] Validation is fast (schemas cached)

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/ports/validator.py` | ValidatorPort protocol |
| `rice_factor/domain/ports/__init__.py` | Updated with ValidatorPort export |
| `rice_factor/adapters/validators/__init__.py` | Package exports |
| `rice_factor/adapters/validators/schema.py` | ArtifactValidator implementation |
| `rice_factor/domain/failures/errors.py` | Enhanced ArtifactValidationError |
| `tests/unit/adapters/validators/test_schema_validator.py` | 20 unit tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implementation complete, all tests passing (20 tests) |
