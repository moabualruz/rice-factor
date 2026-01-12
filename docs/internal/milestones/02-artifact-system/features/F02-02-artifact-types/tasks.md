# Feature: F02-02 Artifact Type Models

## Status: Complete

## Description

Implement Pydantic models for all 7 artifact payload types as defined in the formal artifact schemas.

## Requirements Reference

- M02-PP-001 through M02-PP-004: ProjectPlan requirements
- M02-AP-001 through M02-AP-003: ArchitecturePlan requirements
- M02-SP-001 through M02-SP-003: ScaffoldPlan requirements
- M02-TP-001 through M02-TP-005: TestPlan requirements
- M02-IP-001 through M02-IP-003: ImplementationPlan requirements
- M02-RP-001 through M02-RP-003: RefactorPlan requirements
- M02-VR-001 through M02-VR-003: ValidationResult requirements

## Tasks

### ProjectPlan
- [x] Create `rice_factor/domain/artifacts/payloads/project_plan.py`
- [x] Implement `Domain` model (name, responsibility)
- [x] Implement `Module` model (name, domain)
- [x] Implement `Constraints` model (architecture enum, languages list)
- [x] Implement `ProjectPlanPayload` model
- [x] Add validation: at least 1 domain, at least 1 module

### ArchitecturePlan (MVP: Minimal)
- [x] Create `rice_factor/domain/artifacts/payloads/architecture_plan.py`
- [x] Implement `ArchitecturePlanPayload` model
- [x] Define layer dependency rules enum
- [x] Add validation: rules must be mechanically enforceable

### ScaffoldPlan
- [x] Create `rice_factor/domain/artifacts/payloads/scaffold_plan.py`
- [x] Implement `FileKind` enum (source, test, config, doc)
- [x] Implement `FileEntry` model (path, description, kind)
- [x] Implement `ScaffoldPlanPayload` model
- [x] Add validation: at least 1 file

### TestPlan
- [x] Create `rice_factor/domain/artifacts/payloads/test_plan.py`
- [x] Implement `TestDefinition` model (id, target, assertions)
- [x] Implement `TestPlanPayload` model
- [x] Add validation: at least 1 test, at least 1 assertion per test
- [x] Add special lock behavior support (via ArtifactEnvelope)

### ImplementationPlan
- [x] Create `rice_factor/domain/artifacts/payloads/implementation_plan.py`
- [x] Implement `ImplementationPlanPayload` model
- [x] Add validation: exactly 1 target file, at least 1 step

### RefactorPlan
- [x] Create `rice_factor/domain/artifacts/payloads/refactor_plan.py`
- [x] Implement `RefactorOperationType` enum
- [x] Implement `RefactorOperation` model
- [x] Implement `RefactorConstraints` model
- [x] Implement `RefactorPlanPayload` model
- [x] Add validation: at least 1 operation

### ValidationResult
- [x] Create `rice_factor/domain/artifacts/payloads/validation_result.py`
- [x] Implement `ValidationStatus` enum (passed, failed)
- [x] Implement `ValidationResultPayload` model

### Common
- [x] Create `rice_factor/domain/artifacts/payloads/__init__.py` with exports
- [x] Write unit tests for each payload type
- [x] Test validation constraints (min items, required fields)

## Acceptance Criteria

- [x] All 7 payload types can be created programmatically
- [x] Invalid payloads raise ValidationError with clear messages
- [x] All constraints from original spec are enforced
- [x] Models are serializable to JSON

## Files Created

| File | Description |
|------|-------------|
| `rice_factor/domain/artifacts/payloads/__init__.py` | Package exports |
| `rice_factor/domain/artifacts/payloads/project_plan.py` | ProjectPlanPayload model |
| `rice_factor/domain/artifacts/payloads/architecture_plan.py` | ArchitecturePlanPayload model |
| `rice_factor/domain/artifacts/payloads/scaffold_plan.py` | ScaffoldPlanPayload model |
| `rice_factor/domain/artifacts/payloads/test_plan.py` | TestPlanPayload model |
| `rice_factor/domain/artifacts/payloads/implementation_plan.py` | ImplementationPlanPayload model |
| `rice_factor/domain/artifacts/payloads/refactor_plan.py` | RefactorPlanPayload model |
| `rice_factor/domain/artifacts/payloads/validation_result.py` | ValidationResultPayload model |
| `tests/unit/domain/artifacts/payloads/test_payloads.py` | 30 unit tests for payloads |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implementation complete, all tests passing (30 tests) |
