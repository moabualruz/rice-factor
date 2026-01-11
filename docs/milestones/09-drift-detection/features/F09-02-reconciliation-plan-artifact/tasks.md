# Feature F09-02: ReconciliationPlan Artifact - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-02-01 | Define ReconciliationAction enum | Pending | P0 |
| T09-02-02 | Create ReconciliationStep model | Pending | P0 |
| T09-02-03 | Create ReconciliationPlanPayload model | Pending | P0 |
| T09-02-04 | Create JSON Schema | Pending | P0 |
| T09-02-05 | Register artifact type | Pending | P0 |
| T09-02-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T09-02-01: Define ReconciliationAction Enum

**Objective**: Define allowed actions in reconciliation plans.

**Files to Create**:
- [ ] `rice_factor/domain/artifacts/reconciliation_plan.py`

**Implementation**:
```python
class ReconciliationAction(str, Enum):
    UPDATE_ARTIFACT = "update_artifact"
    ARCHIVE_ARTIFACT = "archive_artifact"
    CREATE_ARTIFACT = "create_artifact"
    UPDATE_REQUIREMENTS = "update_requirements"
    REVIEW_CODE = "review_code"
    DELETE_CODE = "delete_code"
```

**Acceptance Criteria**:
- [ ] All 6 action types defined
- [ ] Enum is string-based for JSON

---

### T09-02-02: Create ReconciliationStep Model

**Objective**: Define individual reconciliation steps.

**Files to Modify**:
- [ ] `rice_factor/domain/artifacts/reconciliation_plan.py`

**Implementation**:
```python
@dataclass
class ReconciliationStep:
    action: ReconciliationAction
    target: str
    reason: str
    drift_signal_id: str
    priority: int
```

**Acceptance Criteria**:
- [ ] All required fields present
- [ ] Priority is positive integer
- [ ] Has to_dict() method

---

### T09-02-03: Create ReconciliationPlanPayload Model

**Objective**: Define the full payload structure.

**Files to Modify**:
- [ ] `rice_factor/domain/artifacts/reconciliation_plan.py`

**Implementation**:
```python
@dataclass
class ReconciliationPlanPayload:
    drift_report_id: str
    steps: list[ReconciliationStep]
    freeze_new_work: bool = True
```

**Acceptance Criteria**:
- [ ] Links to drift report
- [ ] Contains ordered steps
- [ ] Default freeze behavior

---

### T09-02-04: Create JSON Schema

**Objective**: Define formal schema for validation.

**Files to Create**:
- [ ] `schemas/reconciliation_plan.schema.json`

**Schema Requirements**:
- [ ] Required fields: drift_report_id, steps, freeze_new_work
- [ ] Steps array with action, target, reason, priority
- [ ] Action enum values validated
- [ ] Priority minimum: 1

**Acceptance Criteria**:
- [ ] Schema validates correctly
- [ ] Invalid payloads rejected
- [ ] Matches Python model

---

### T09-02-05: Register Artifact Type

**Objective**: Add ReconciliationPlan to artifact registry.

**Files to Modify**:
- [ ] `rice_factor/domain/artifacts/__init__.py`
- [ ] `rice_factor/adapters/validators/artifact_validator.py`

**Implementation**:
- [ ] Add to ARTIFACT_TYPES list
- [ ] Register schema for validation
- [ ] Add to artifact factory

**Acceptance Criteria**:
- [ ] ArtifactService can create ReconciliationPlan
- [ ] Validation uses schema
- [ ] Storage works correctly

---

### T09-02-06: Write Unit Tests

**Objective**: Test ReconciliationPlan artifact.

**Files to Create**:
- [ ] `tests/unit/domain/artifacts/test_reconciliation_plan.py`

**Test Cases**:
- [ ] Create valid payload
- [ ] Serialize to JSON
- [ ] Validate against schema
- [ ] Invalid action rejected
- [ ] Invalid priority rejected
- [ ] Empty steps allowed

**Acceptance Criteria**:
- [ ] All model methods tested
- [ ] Schema validation tested
- [ ] Edge cases covered

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
| T09-02-02 | Low | Simple dataclass |
| T09-02-03 | Low | Container model |
| T09-02-04 | Medium | Schema design |
| T09-02-05 | Low | Registry update |
| T09-02-06 | Medium | Validation tests |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
