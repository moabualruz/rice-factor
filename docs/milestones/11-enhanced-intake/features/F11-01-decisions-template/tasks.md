# Feature F11-01: Decisions.md Template - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T11-01-01 | Create decisions.md template function | Pending | P0 |
| T11-01-02 | Add decisions.md to TEMPLATE_FILES | Pending | P0 |
| T11-01-03 | Update InitService for 6 files | Pending | P0 |
| T11-01-04 | Update tests | Pending | P0 |

---

## 2. Task Details

### T11-01-01: Create Decisions.md Template Function

**Objective**: Create template generator for decisions.md.

**Files to Modify**:
- [ ] `rice_factor/domain/services/init_service.py`

**Implementation**:
- [ ] Add `_decisions_template(responses)` function
- [ ] Include Architecture Choices section
- [ ] Include Rejected Approaches section
- [ ] Include Tradeoffs Accepted section
- [ ] Include Future Considerations section

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
- [ ] Template follows existing patterns
- [ ] Matches spec section 2.2

---

### T11-01-02: Add Decisions.md to TEMPLATE_FILES

**Objective**: Register decisions.md in template system.

**Files to Modify**:
- [ ] `rice_factor/domain/services/init_service.py`

**Implementation**:
- [ ] Add "decisions.md" to `TEMPLATE_FILES` list
- [ ] Add entry to `TEMPLATE_GENERATORS` dict

**Acceptance Criteria**:
- [ ] TEMPLATE_FILES has 6 entries
- [ ] Generator is registered

---

### T11-01-03: Update InitService for 6 Files

**Objective**: Ensure initialize() creates all 6 files.

**Files to Modify**:
- [ ] `rice_factor/domain/services/init_service.py`

**Implementation**:
- [ ] Verify TEMPLATE_FILES order
- [ ] Update docstrings to mention 6 files
- [ ] Ensure consistent creation

**Acceptance Criteria**:
- [ ] `initialize()` creates 6 files
- [ ] Files are created in consistent order

---

### T11-01-04: Update Tests

**Objective**: Update tests for 6-file initialization.

**Files to Modify**:
- [ ] `tests/unit/domain/services/test_init_service.py`

**Test Cases**:
- [ ] Test 6 files created
- [ ] Test decisions.md content
- [ ] Test template markers present

**Acceptance Criteria**:
- [ ] All existing tests still pass
- [ ] New tests for decisions.md

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
