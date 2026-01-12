# Feature F09-02: ReconciliationPlan Artifact - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-02-01 | Define ReconciliationAction enum | **Complete** | P0 |
| T09-02-02 | Create ReconciliationStep model | **Complete** | P0 |
| T09-02-03 | Create ReconciliationPlanPayload model | **Complete** | P0 |
| T09-02-04 | Create JSON Schema | **Complete** | P0 |
| T09-02-05 | Register artifact type | **Complete** | P0 |
| T09-02-06 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T09-02-01: Define ReconciliationAction Enum

**Objective**: Define allowed actions in reconciliation plans.

**Files Created**:
- [x] `rice_factor/domain/artifacts/payloads/reconciliation_plan.py`

**Implementation**:
- [x] ReconciliationAction enum with 6 action types
- [x] String-based enum for JSON serialization

**Acceptance Criteria**:
- [x] All 6 action types defined
- [x] Enum is string-based for JSON

---

### T09-02-02: Create ReconciliationStep Model

**Objective**: Define individual reconciliation steps.

**Files Modified**:
- [x] `rice_factor/domain/artifacts/payloads/reconciliation_plan.py`

**Implementation**:
- [x] Pydantic model with action, target, reason, drift_signal_id, priority
- [x] Priority validation (ge=1)
- [x] Extra fields forbidden

**Acceptance Criteria**:
- [x] All required fields present
- [x] Priority is positive integer
- [x] Model is JSON-serializable

---

### T09-02-03: Create ReconciliationPlanPayload Model

**Objective**: Define the full payload structure.

**Files Modified**:
- [x] `rice_factor/domain/artifacts/payloads/reconciliation_plan.py`

**Implementation**:
- [x] Pydantic model with drift_report_id, steps, freeze_new_work
- [x] Default freeze_new_work = True
- [x] Extra fields forbidden

**Acceptance Criteria**:
- [x] Links to drift report
- [x] Contains ordered steps
- [x] Default freeze behavior

---

### T09-02-04: Create JSON Schema

**Objective**: Define formal schema for validation.

**Files Created**:
- [x] `schemas/reconciliation_plan.schema.json`

**Schema Features**:
- [x] Required fields: drift_report_id, steps
- [x] Steps array with action, target, reason, drift_signal_id, priority
- [x] Action enum values validated
- [x] Priority minimum: 1
- [x] freeze_new_work default: true

**Acceptance Criteria**:
- [x] Schema validates correctly
- [x] Invalid payloads rejected
- [x] Matches Python model

---

### T09-02-05: Register Artifact Type

**Objective**: Add ReconciliationPlan to artifact registry.

**Files Modified**:
- [x] `rice_factor/domain/artifacts/enums.py` - Added RECONCILIATION_PLAN
- [x] `rice_factor/adapters/validators/schema.py` - Added to PAYLOAD_TYPE_MAP and SCHEMA_FILE_MAP
- [x] `rice_factor/adapters/storage/filesystem.py` - Added to TYPE_DIR_MAP
- [x] `rice_factor/domain/prompts/schema_injector.py` - Added to SCHEMA_FILENAMES
- [x] `rice_factor/domain/artifacts/payloads/__init__.py` - Added exports

**Acceptance Criteria**:
- [x] ArtifactValidator can validate ReconciliationPlan
- [x] Validation uses schema
- [x] Storage works correctly

---

### T09-02-06: Write Unit Tests

**Objective**: Test ReconciliationPlan artifact.

**Files Created**:
- [x] `tests/unit/domain/artifacts/payloads/test_reconciliation_plan.py` (12 tests)

**Test Cases** (12 tests total):
- [x] test_has_all_action_types
- [x] test_create_valid_step
- [x] test_priority_must_be_positive
- [x] test_invalid_action_rejected
- [x] test_extra_fields_forbidden (step)
- [x] test_serialization (step)
- [x] test_create_valid_payload
- [x] test_empty_steps_allowed
- [x] test_default_freeze_new_work
- [x] test_extra_fields_forbidden (payload)
- [x] test_serialization (payload)
- [x] test_json_serialization

**Acceptance Criteria**:
- [x] All model methods tested
- [x] Validation tested
- [x] Edge cases covered
- [x] 12 tests passing

---

## 3. Task Dependencies

```
T09-02-01 (Enum) ──→ T09-02-02 (Step) ──→ T09-02-03 (Payload)
                                                │
                                                ↓
                                        T09-02-04 (Schema)
                                                │
                                                ↓
                                        T09-02-05 (Register)
                                                │
                                                ↓
                                        T09-02-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T09-02-01 | Low | Enum definition |
| T09-02-02 | Low | Pydantic model |
| T09-02-03 | Low | Container model |
| T09-02-04 | Medium | Schema design |
| T09-02-05 | Low | Multiple registry updates |
| T09-02-06 | Medium | Validation tests |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.0.1 | 2026-01-11 | Implementation | All tasks complete - 12 tests passing |
