# Milestone 11: Enhanced Intake System - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.1.0
> **Status**: Complete
> **Priority**: P1 (Quality improvement)
> **Tests**: 41 passing (intake + glossary validators)
> **Parent**: [Project Requirements](../../project/requirements.md)
> **Source Spec**: [06-tools-to-integrte-with-or-learn-from.md](../../raw/06-tools-to-integrte-with-or-learn-from.md)

---

## 1. Milestone Objective

Enhance the project intake system to enforce rigorous input quality, including:

- Add `decisions.md` as the 6th required intake file
- Implement blocking questionnaire enforcement
- Reject vague or placeholder answers
- Validate glossary terms during planning
- Force clarity before intelligence is applied

**Core Principle** (from spec 2.1):
> The system must *force clarity* before intelligence is applied. Questionnaire principles: Blocking (cannot proceed without answers), Explicit (no defaults inferred), Written to files (not ephemeral), Human-authored (LLM may assist, not decide).

---

## 2. Scope

### 2.1 In Scope

- `decisions.md` template file creation
- Blocking enforcement for all 6 intake files
- Vague answer pattern detection and rejection
- Glossary term validation during LLM planning passes
- Enhanced intake validation in `rice-factor init`
- Rejection criteria for incomplete inputs

### 2.2 Out of Scope

- LLM-assisted questionnaire completion (humans must author)
- Automatic glossary term extraction
- Natural language understanding of requirements
- Interactive questionnaire wizard (CLI prompts are sufficient)

---

## 3. Requirements

### 3.1 Intake File Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M11-U-001 | The system shall create 6 intake files during `rice-factor init` | P0 |
| M11-U-002 | All 6 intake files shall be created in `.project/` directory | P0 |
| M11-U-003 | The 6 required files shall be: requirements.md, constraints.md, glossary.md, non_goals.md, risks.md, decisions.md | P0 |

### 3.2 Decisions.md Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M11-S-001 | While `rice-factor init` runs, the system shall create `decisions.md` with template content | P0 |
| M11-U-004 | `decisions.md` shall contain sections for: Architecture Choices, Rejected Approaches, Tradeoffs Accepted | P0 |
| M11-U-005 | `decisions.md` shall record why decisions were made, not just what | P1 |

### 3.3 Blocking Questionnaire Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M11-I-001 | If any required intake file is empty or contains only template markers, then artifact builder shall not run | P0 |
| M11-I-002 | If any required intake file is missing, then artifact builder shall not run | P0 |
| M11-E-001 | As soon as intake validation fails, the system shall display specific files that need attention | P0 |
| M11-U-006 | Planning commands shall validate intake files before invoking LLM | P0 |

### 3.4 Vague Answer Rejection Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M11-I-003 | If intake file contains "TBD" or "To be determined", then validation shall fail | P0 |
| M11-I-004 | If intake file contains "We'll decide later" or similar deferral phrases, then validation shall fail | P0 |
| M11-I-005 | If intake file contains placeholder markers like "[TODO]" or "[Not provided]", then validation shall fail | P0 |
| M11-U-007 | The system shall provide a list of detected vague patterns when validation fails | P1 |

**Vague Answer Patterns** (from spec 2.3A):
- "TBD"
- "To be determined"
- "We'll decide later"
- "Not sure"
- "Maybe"
- "Possibly"
- "[TODO]"
- "[Not provided]"
- "[Not specified]"

### 3.5 Glossary Term Validation Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M11-E-002 | As soon as LLM output references a term not in glossary.md, the system shall fail with `undefined_glossary_term` | P0 |
| M11-U-008 | Glossary validation shall extract all capitalized domain terms from LLM output | P1 |
| M11-U-009 | Glossary validation shall compare against terms defined in glossary.md | P0 |
| M11-I-006 | If a term appears in artifacts without glossary definition, then hard fail | P0 |

**Spec Quote** (2.3C):
> If a term appears later without being here → **hard fail**.

---

## 4. Features in This Milestone

| Feature ID | Feature Name | Priority | Status | Gaps Addressed |
|------------|--------------|----------|--------|----------------|
| F11-01 | Decisions.md Template | P0 | Pending | GAP-IN-001 |
| F11-02 | Blocking Questionnaire Enforcement | P0 | Pending | GAP-IN-002 |
| F11-03 | Vague Answer Rejection | P0 | Pending | GAP-IN-003 |
| F11-04 | Glossary Term Validation | P0 | Pending | GAP-IN-004 |

---

## 5. Success Criteria

- [ ] `rice-factor init` creates 6 intake files (including decisions.md)
- [ ] `rice-factor plan project` fails if any intake file is empty
- [ ] `rice-factor plan project` fails if intake files contain "TBD"
- [ ] `rice-factor plan project` fails if intake files contain "[Not provided]"
- [ ] Error messages specify which files need attention
- [ ] LLM output with undefined terms fails validation
- [ ] Glossary terms are checked against glossary.md
- [ ] All vague patterns are documented and rejected

---

## 6. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Milestone 03 | Internal | CLI commands for init and plan |
| Milestone 04 | Internal | LLM compiler for term extraction |
| Existing InitService | Internal | Extends current initialization |

---

## 7. Intake File Templates

### 7.1 decisions.md Template

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

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial milestone requirements |
