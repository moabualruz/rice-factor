# Feature: F02-01 Artifact Envelope Model

## Status: Complete

## Description

Implement the universal artifact envelope that wraps all artifact types. This is the base structure that all artifacts must conform to.

## Requirements Reference

- M02-U-001: All artifacts shall conform to the universal artifact envelope schema
- M02-U-003: All artifacts shall have a unique UUID identifier
- M02-U-004: All artifacts shall track creation timestamp and creator (llm/human)
- M02-U-005: All artifacts shall have a status field (draft/approved/locked)

## Tasks

- [x] Create `rice_factor/domain/artifacts/__init__.py`
- [x] Create `rice_factor/domain/artifacts/enums.py` with:
  - [x] `ArtifactStatus` enum (draft, approved, locked)
  - [x] `ArtifactType` enum (7 types)
  - [x] `CreatedBy` enum (human, llm)
- [x] Create `rice_factor/domain/artifacts/envelope.py` with:
  - [x] `ArtifactEnvelope` generic Pydantic model
  - [x] UUID auto-generation
  - [x] Timestamp auto-generation
  - [x] `depends_on` list field
- [x] Add status transition methods:
  - [x] `approve()` - draft -> approved
  - [x] `lock()` - approved -> locked (TestPlan only)
- [x] Add immutability checks:
  - [x] `is_modifiable()` method
  - [x] `is_executable()` method
  - [x] Validator prevents LOCKED status for non-TestPlan
- [x] Create `rice_factor/domain/failures/errors.py` with error types
- [x] Write unit tests:
  - [x] Test envelope creation with defaults
  - [x] Test UUID uniqueness
  - [x] Test status transitions
  - [x] Test immutability enforcement

## Acceptance Criteria

- [x] `ArtifactEnvelope` can be instantiated with any payload type
- [x] UUID is automatically generated if not provided
- [x] Timestamp is automatically set to current time
- [x] Status defaults to "draft"
- [x] Status transitions follow: draft -> approved -> locked
- [x] Locked artifacts cannot be modified
- [x] All tests pass (20 tests)
- [x] mypy passes
- [x] ruff passes

## Files Created

| File | Description |
|------|-------------|
| `rice_factor/domain/artifacts/enums.py` | ArtifactStatus, ArtifactType, CreatedBy enums |
| `rice_factor/domain/artifacts/envelope.py` | ArtifactEnvelope generic Pydantic model |
| `rice_factor/domain/failures/errors.py` | RiceFactorError, ArtifactError, ArtifactStatusError, etc. |
| `tests/unit/domain/artifacts/test_envelope.py` | 20 unit tests for envelope |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implementation complete, all tests passing |
