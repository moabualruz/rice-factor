# Feature F11-02: Blocking Questionnaire Enforcement - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T11-02-01 | Create IntakeValidator service | **Complete** | P0 |
| T11-02-02 | Implement file existence check | **Complete** | P0 |
| T11-02-03 | Implement empty file detection | **Complete** | P0 |
| T11-02-04 | Integrate with plan commands | **Complete** | P0 |
| T11-02-05 | Add CLI error formatting | **Complete** | P1 |
| T11-02-06 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T11-02-01: Create IntakeValidator Service

**Objective**: Create the intake validation service.

**Files to Create**:
- [x] `rice_factor/domain/services/intake_validator.py`

**Implementation**:
- [x] Create `IntakeValidator` class
- [x] Define `REQUIRED_FILES` list (6 files)
- [x] Define `BLOCKING_FILES` list (requirements, constraints, glossary)
- [x] Create `validate(project_dir)` method
- [x] Return `IntakeValidationResult`

**Acceptance Criteria**:
- [x] Service follows domain patterns
- [x] No external dependencies

---

### T11-02-02: Implement File Existence Check

**Objective**: Verify all required files exist.

**Implementation**:
- [x] Iterate through REQUIRED_FILES
- [x] Check each file exists in .project/
- [x] Create FILE_MISSING error for missing files
- [x] Include file path in error

**Acceptance Criteria**:
- [x] All 6 files checked
- [x] Clear error messages

---

### T11-02-03: Implement Empty File Detection

**Objective**: Reject empty blocking files.

**Implementation**:
- [x] For each file in BLOCKING_FILES
- [x] Read file content
- [x] Check if content is empty or whitespace only
- [x] Create FILE_EMPTY error

**Acceptance Criteria**:
- [x] Empty files detected
- [x] Only blocking files cause failure

---

### T11-02-04: Integrate with Plan Commands

**Objective**: Block planning on invalid intake.

**Files to Modify**:
- [x] `rice_factor/entrypoints/cli/commands/plan.py`

**Implementation**:
- [x] Add intake validation before LLM invocation
- [x] Display validation errors
- [x] Exit with code 1 on failure
- [x] Apply to all plan subcommands

**Acceptance Criteria**:
- [x] `rice-factor plan project` validates intake
- [x] `rice-factor plan tests` validates intake
- [x] Clear error output

---

### T11-02-05: Add CLI Error Formatting

**Objective**: Format intake errors for CLI display.

**Implementation**:
- [x] Create `format_errors()` method on result
- [x] Use rich formatting for colors
- [x] Group errors by type
- [x] Show remediation hints

**Acceptance Criteria**:
- [x] Errors are readable
- [x] Actionable guidance provided

---

### T11-02-06: Write Unit Tests

**Objective**: Test intake validation logic.

**Files to Create**:
- [x] `tests/unit/domain/services/test_intake_validator.py`

**Test Cases**:
- [x] Test all files present passes
- [x] Test missing file fails
- [x] Test empty blocking file fails
- [x] Test empty non-blocking file passes
- [x] Test multiple errors collected

**Acceptance Criteria**:
- [x] All scenarios covered
- [x] Uses temp directory fixtures

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
