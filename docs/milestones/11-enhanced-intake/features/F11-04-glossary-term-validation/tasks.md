# Feature F11-04: Glossary Term Validation - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T11-04-01 | Extract terms from glossary.md | Pending | P0 |
| T11-04-02 | Create GlossaryValidator service | Pending | P0 |
| T11-04-03 | Integrate with LLM output processing | Pending | P0 |
| T11-04-04 | Implement undefined term detection | Pending | P0 |
| T11-04-05 | Add hard failure mechanism | Pending | P0 |
| T11-04-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T11-04-01: Extract Terms from glossary.md

**Objective**: Parse glossary.md to extract defined terms.

**Files to Create/Modify**:
- [ ] `rice_factor/domain/services/glossary_parser.py`

**Implementation**:
- [ ] Parse markdown table format
- [ ] Extract term names from first column
- [ ] Handle both "Terms" and "Acronyms" sections
- [ ] Normalize terms (lowercase, strip whitespace)
- [ ] Return set of defined terms

**Glossary Format Expected**:
```markdown
| Term | Definition |
|------|------------|
| Artifact | Structured plan document |
| TestPlan | Test specification |
```

**Acceptance Criteria**:
- [ ] Parses standard markdown tables
- [ ] Handles missing or malformed tables gracefully
- [ ] Returns empty set if no terms found

---

### T11-04-02: Create GlossaryValidator Service

**Objective**: Create service for validating glossary term usage.

**Files to Create**:
- [ ] `rice_factor/domain/services/glossary_validator.py`

**Implementation**:
```python
class GlossaryValidator:
    """Validates that used terms are defined in glossary."""

    def __init__(self, glossary_path: Path) -> None:
        self.defined_terms = self._load_terms(glossary_path)

    def validate_text(self, text: str) -> list[GlossaryError]:
        """Check text for undefined domain terms."""
        ...

    def validate_artifact(self, artifact: ArtifactEnvelope) -> list[GlossaryError]:
        """Check artifact content for undefined terms."""
        ...
```

**Acceptance Criteria**:
- [ ] Loads terms from glossary.md
- [ ] Validates arbitrary text
- [ ] Returns list of undefined term usages

---

### T11-04-03: Integrate with LLM Output Processing

**Objective**: Hook glossary validation into LLM response processing.

**Files to Modify**:
- [ ] `rice_factor/adapters/llm/base_adapter.py` or equivalent

**Implementation**:
- [ ] Add post-processing hook for LLM responses
- [ ] Extract domain terms from generated artifacts
- [ ] Run GlossaryValidator on extracted terms
- [ ] Collect validation errors before artifact creation

**Integration Point**:
```python
def process_llm_response(self, response: str) -> ArtifactEnvelope:
    artifact = self._parse_artifact(response)

    # Validate glossary terms
    glossary_errors = self.glossary_validator.validate_artifact(artifact)
    if glossary_errors:
        raise GlossaryValidationError(glossary_errors)

    return artifact
```

**Acceptance Criteria**:
- [ ] Validation runs on every LLM response
- [ ] Errors collected before artifact persisted
- [ ] Clear integration point for future validators

---

### T11-04-04: Implement Undefined Term Detection

**Objective**: Detect when LLM uses terms not in glossary.

**Files to Modify**:
- [ ] `rice_factor/domain/services/glossary_validator.py`

**Implementation**:
- [ ] Define domain term patterns (capitalized words, quoted terms)
- [ ] Extract potential terms from text
- [ ] Compare against defined terms set
- [ ] Track location (field, line) of undefined terms

**Term Extraction Patterns**:
```python
# Capitalized terms (likely domain concepts)
DOMAIN_TERM_PATTERN = r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b'

# Quoted terms (explicit domain references)
QUOTED_TERM_PATTERN = r'"([^"]+)"'

# Known false positives to ignore
IGNORE_TERMS = {"The", "This", "That", "When", "Where", ...}
```

**Acceptance Criteria**:
- [ ] Detects PascalCase domain terms
- [ ] Detects quoted term references
- [ ] Ignores common words and proper nouns
- [ ] Reports location of each undefined term

---

### T11-04-05: Add Hard Failure Mechanism

**Objective**: Block artifact creation when undefined terms found.

**Files to Create/Modify**:
- [ ] `rice_factor/domain/failures/glossary_errors.py`
- [ ] `rice_factor/adapters/llm/base_adapter.py`

**Error Model**:
```python
@dataclass
class GlossaryValidationError(Exception):
    """Raised when LLM output contains undefined terms."""

    undefined_terms: list[UndefinedTerm]

    def __str__(self) -> str:
        terms = ", ".join(t.term for t in self.undefined_terms)
        return f"Undefined glossary terms: {terms}"

@dataclass
class UndefinedTerm:
    term: str
    location: str  # "ProjectPlan.description" or "line 15"
    suggestion: str | None  # Closest match from glossary
```

**CLI Output**:
```
ERROR: Undefined glossary terms detected

The following terms are used but not defined in .project/glossary.md:

  - "DataIngestion" in ProjectPlan.milestones[0].description
    Suggestion: Did you mean "DataImport"?

  - "ValidationEngine" in ProjectPlan.architecture
    No close match found. Add to glossary.md or use existing term.

Add missing terms to glossary.md before continuing.
```

**Acceptance Criteria**:
- [ ] Blocks artifact creation on error
- [ ] Provides actionable error messages
- [ ] Suggests similar terms when possible

---

### T11-04-06: Write Unit Tests

**Objective**: Comprehensive test coverage for glossary validation.

**Files to Create/Modify**:
- [ ] `tests/unit/domain/services/test_glossary_parser.py`
- [ ] `tests/unit/domain/services/test_glossary_validator.py`

**Test Cases**:
- [ ] Parse valid glossary with terms
- [ ] Parse glossary with acronyms
- [ ] Parse empty glossary
- [ ] Parse malformed glossary
- [ ] Detect single undefined term
- [ ] Detect multiple undefined terms
- [ ] Ignore common words
- [ ] Suggest similar terms
- [ ] Integration with LLM adapter

**Acceptance Criteria**:
- [ ] All parsing edge cases covered
- [ ] All validation scenarios tested
- [ ] Integration tests verify end-to-end flow

---

## 3. Task Dependencies

```
T11-04-01 (Parser) ──→ T11-04-02 (Validator) ──→ T11-04-03 (Integration)
                                                         │
                                                         ↓
                                               T11-04-04 (Detection)
                                                         │
                                                         ↓
                                               T11-04-05 (Hard Fail)
                                                         │
                                                         ↓
                                               T11-04-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T11-04-01 | Low | Markdown parsing |
| T11-04-02 | Medium | Service design |
| T11-04-03 | Medium | Adapter integration |
| T11-04-04 | Medium | Pattern matching |
| T11-04-05 | Low | Error handling |
| T11-04-06 | Medium | Many test cases |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
