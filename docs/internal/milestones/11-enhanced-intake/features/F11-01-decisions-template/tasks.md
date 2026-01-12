# Feature F11-01: Decisions.md Template - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T11-01-01 | Create decisions.md template function | **Complete** | P0 |
| T11-01-02 | Add decisions.md to TEMPLATE_FILES | **Complete** | P0 |
| T11-01-03 | Update InitService for 6 files | **Complete** | P0 |
| T11-01-04 | Update tests | **Complete** | P0 |

---

## 2. Task Details

### T11-01-01: Create Decisions.md Template Function

**Objective**: Create template generator for decisions.md.

**Files to Modify**:
- [x] `rice_factor/domain/services/init_service.py`

**Implementation**:
- [x] Add `_decisions_template(responses)` function
- [x] Include Architecture Choices section
- [x] Include Rejected Approaches section
- [x] Include Tradeoffs Accepted section
- [x] Include Future Considerations section

**Template Content**:
```markdown
# Decision Log

## Architecture Choices

| Decision | Alternatives Considered | Rationale |
|----------|------------------------|-----------|
| [Decision 1] | [Alt A, Alt B] | [Why this choice] |

## Rejected Approaches

| Approach | Reason for Rejection |
|----------|---------------------|
| [Approach 1] | [Reason] |

## Tradeoffs Accepted

| Tradeoff | Benefit | Cost |
|----------|---------|------|
| [Tradeoff 1] | [Benefit] | [Cost] |

## Future Considerations

<!-- Items that may be revisited based on new information -->
```

**Acceptance Criteria**:
- [x] Template follows existing patterns
- [x] Matches spec section 2.2

---

### T11-01-02: Add Decisions.md to TEMPLATE_FILES

**Objective**: Register decisions.md in template system.

**Files to Modify**:
- [x] `rice_factor/domain/services/init_service.py`

**Implementation**:
- [x] Add "decisions.md" to `TEMPLATE_FILES` list
- [x] Add entry to `TEMPLATE_GENERATORS` dict

**Acceptance Criteria**:
- [x] TEMPLATE_FILES has 6 entries
- [x] Generator is registered

---

### T11-01-03: Update InitService for 6 Files

**Objective**: Ensure initialize() creates all 6 files.

**Files to Modify**:
- [x] `rice_factor/domain/services/init_service.py`

**Implementation**:
- [x] Verify TEMPLATE_FILES order
- [x] Update docstrings to mention 6 files
- [x] Ensure consistent creation

**Acceptance Criteria**:
- [x] `initialize()` creates 6 files
- [x] Files are created in consistent order

---

### T11-01-04: Update Tests

**Objective**: Update tests for 6-file initialization.

**Files to Modify**:
- [x] `tests/unit/domain/services/test_init_service.py`

**Test Cases**:
- [x] Test 6 files created
- [x] Test decisions.md content
- [x] Test template markers present

**Acceptance Criteria**:
- [x] All existing tests still pass
- [x] New tests for decisions.md

---

## 3. Task Dependencies

```
T11-01-01 (Template) ──→ T11-01-02 (Register) ──→ T11-01-03 (Update) ──→ T11-01-04 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T11-01-01 | Low | Template string |
| T11-01-02 | Low | Dict entry |
| T11-01-03 | Low | Minor updates |
| T11-01-04 | Low | Test adjustments |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
