# Feature F11-03: Vague Answer Rejection - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T11-03-01 | Define vague pattern list | Pending | P0 |
| T11-03-02 | Implement pattern detection | Pending | P0 |
| T11-03-03 | Add line number tracking | Pending | P1 |
| T11-03-04 | Create detailed error messages | Pending | P1 |
| T11-03-05 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T11-03-01: Define Vague Pattern List

**Objective**: Define comprehensive list of vague patterns.

**Files to Modify**:
- [ ] `rice_factor/domain/services/intake_validator.py`

**Patterns to Include**:
```python
VAGUE_PATTERNS = [
    # Explicit deferral
    "TBD",
    "To be determined",
    "We'll decide later",
    "Not sure",
    "Maybe",
    "Possibly",

    # Template markers
    "[TODO]",
    "[Not provided]",
    "[Not specified]",

    # From existing templates
    "[Decision 1]",
    "[Alt A, Alt B]",
    "[Why this choice]",
    "[Approach 1]",
    "[Reason]",
    "[Tradeoff 1]",
    "[Benefit]",
    "[Cost]",
    "[Requirement description]",
    "[Term 1]",
    "[Definition]",
    "[Risk description]",
    "[Non-goal 1]",
]
```

**Acceptance Criteria**:
- [ ] All spec patterns included
- [ ] All template placeholders included
- [ ] Case-insensitive matching considered

---

### T11-03-02: Implement Pattern Detection

**Objective**: Detect vague patterns in intake files.

**Files to Modify**:
- [ ] `rice_factor/domain/services/intake_validator.py`

**Implementation**:
- [ ] Add `_check_vague_patterns()` method
- [ ] Iterate through BLOCKING_FILES
- [ ] Search for each pattern in content
- [ ] Create VAGUE_CONTENT error for matches
- [ ] Include matched pattern in error

**Acceptance Criteria**:
- [ ] All patterns detected
- [ ] Multiple patterns per file reported

---

### T11-03-03: Add Line Number Tracking

**Objective**: Include line numbers in error messages.

**Implementation**:
- [ ] Track line number when pattern found
- [ ] Include line_number in IntakeError
- [ ] Show line in formatted output

**Example Output**:
```
  - [vague_content] requirements.md:15: Vague content detected: 'TBD'
```

**Acceptance Criteria**:
- [ ] Line numbers accurate
- [ ] Helps user locate issues

---

### T11-03-04: Create Detailed Error Messages

**Objective**: Provide actionable guidance for each pattern.

**Implementation**:
- [ ] Add pattern-specific remediation hints
- [ ] Explain what to replace pattern with
- [ ] Group similar patterns in output

**Remediation Examples**:
- "TBD" → "Replace with specific decision or requirement"
- "[Term 1]" → "Define actual domain term"
- "[Not specified]" → "Provide specific value"

**Acceptance Criteria**:
- [ ] Each pattern has guidance
- [ ] Users understand what to do

---

### T11-03-05: Write Unit Tests

**Objective**: Test vague pattern detection.

**Files to Create/Modify**:
- [ ] `tests/unit/domain/services/test_intake_validator.py`

**Test Cases**:
- [ ] Test "TBD" detected
- [ ] Test template markers detected
- [ ] Test valid content passes
- [ ] Test case variations (tbd, Tbd)
- [ ] Test multiple patterns in one file
- [ ] Test patterns across multiple files

**Acceptance Criteria**:
- [ ] All patterns have test coverage
- [ ] Edge cases covered

---

## 3. Task Dependencies

```
T11-03-01 (Patterns) ──→ T11-03-02 (Detection) ──→ T11-03-03 (Line #s)
                                                          │
                                                          ↓
                                               T11-03-04 (Messages)
                                                          │
                                                          ↓
                                               T11-03-05 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T11-03-01 | Low | List definition |
| T11-03-02 | Medium | String searching |
| T11-03-03 | Low | Line tracking |
| T11-03-04 | Low | Message strings |
| T11-03-05 | Medium | Many test cases |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
