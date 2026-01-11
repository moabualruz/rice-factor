# Feature F11-02: Blocking Questionnaire Enforcement - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T11-02-01 | Create IntakeValidator service | Pending | P0 |
| T11-02-02 | Implement file existence check | Pending | P0 |
| T11-02-03 | Implement empty file detection | Pending | P0 |
| T11-02-04 | Integrate with plan commands | Pending | P0 |
| T11-02-05 | Add CLI error formatting | Pending | P1 |
| T11-02-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T11-02-01: Create IntakeValidator Service

**Objective**: Create the intake validation service.

**Files to Create**:
- [ ] `rice_factor/domain/services/intake_validator.py`

**Implementation**:
- [ ] Create `IntakeValidator` class
- [ ] Define `REQUIRED_FILES` list (6 files)
- [ ] Define `BLOCKING_FILES` list (requirements, constraints, glossary)
- [ ] Create `validate(project_dir)` method
- [ ] Return `IntakeValidationResult`

**Acceptance Criteria**:
- [ ] Service follows domain patterns
- [ ] No external dependencies

---

### T11-02-02: Implement File Existence Check

**Objective**: Verify all required files exist.

**Implementation**:
- [ ] Iterate through REQUIRED_FILES
- [ ] Check each file exists in .project/
- [ ] Create FILE_MISSING error for missing files
- [ ] Include file path in error

**Acceptance Criteria**:
- [ ] All 6 files checked
- [ ] Clear error messages

---

### T11-02-03: Implement Empty File Detection

**Objective**: Reject empty blocking files.

**Implementation**:
- [ ] For each file in BLOCKING_FILES
- [ ] Read file content
- [ ] Check if content is empty or whitespace only
- [ ] Create FILE_EMPTY error

**Acceptance Criteria**:
- [ ] Empty files detected
- [ ] Only blocking files cause failure

---

### T11-02-04: Integrate with Plan Commands

**Objective**: Block planning on invalid intake.

**Files to Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/plan.py`

**Implementation**:
- [ ] Add intake validation before LLM invocation
- [ ] Display validation errors
- [ ] Exit with code 1 on failure
- [ ] Apply to all plan subcommands

**Acceptance Criteria**:
- [ ] `rice-factor plan project` validates intake
- [ ] `rice-factor plan tests` validates intake
- [ ] Clear error output

---

### T11-02-05: Add CLI Error Formatting

**Objective**: Format intake errors for CLI display.

**Implementation**:
- [ ] Create `format_errors()` method on result
- [ ] Use rich formatting for colors
- [ ] Group errors by type
- [ ] Show remediation hints

**Acceptance Criteria**:
- [ ] Errors are readable
- [ ] Actionable guidance provided

---

### T11-02-06: Write Unit Tests

**Objective**: Test intake validation logic.

**Files to Create**:
- [ ] `tests/unit/domain/services/test_intake_validator.py`

**Test Cases**:
- [ ] Test all files present passes
- [ ] Test missing file fails
- [ ] Test empty blocking file fails
- [ ] Test empty non-blocking file passes
- [ ] Test multiple errors collected

**Acceptance Criteria**:
- [ ] All scenarios covered
- [ ] Uses temp directory fixtures

---

## 3. Task Dependencies

```
T11-02-01 (Service) ──┬──→ T11-02-02 (Existence)
                      │
                      └──→ T11-02-03 (Empty) ──→ T11-02-04 (Integrate)
                                                       │
                                                       ↓
                                             T11-02-05 (Format)
                                                       │
                                                       ↓
                                             T11-02-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T11-02-01 | Low | Service skeleton |
| T11-02-02 | Low | File checks |
| T11-02-03 | Low | Content checks |
| T11-02-04 | Medium | CLI integration |
| T11-02-05 | Low | Formatting |
| T11-02-06 | Medium | Multiple scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
