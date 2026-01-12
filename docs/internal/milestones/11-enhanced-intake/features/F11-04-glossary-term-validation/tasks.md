# Feature F11-04: Glossary Term Validation - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T11-04-01 | Extract terms from glossary.md | **Complete** | P0 |
| T11-04-02 | Create GlossaryValidator service | **Complete** | P0 |
| T11-04-03 | Integrate with LLM output processing | **Complete** | P0 |
| T11-04-04 | Implement undefined term detection | **Complete** | P0 |
| T11-04-05 | Add hard failure mechanism | **Complete** | P0 |
| T11-04-06 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T11-04-01: Extract Terms from glossary.md

**Objective**: Parse glossary.md to extract defined terms.

**Files to Create/Modify**:
- [x] `rice_factor/domain/services/glossary_validator.py` (GlossaryParser class)

**Implementation**:
- [x] Parse markdown table format
- [x] Extract term names from first column
- [x] Handle both "Terms" and "Acronyms" sections
- [x] Normalize terms (lowercase, strip whitespace)
- [x] Return set of defined terms

**Glossary Format Expected**:
```markdown
| Term | Definition |
|------|------------|
| Artifact | Structured plan document |
| TestPlan | Test specification |
```

**Acceptance Criteria**:
- [x] Parses standard markdown tables
- [x] Handles missing or malformed tables gracefully
- [x] Returns empty set if no terms found

---

### T11-04-02: Create GlossaryValidator Service

**Objective**: Create service for validating glossary term usage.

**Files to Create**:
- [x] `rice_factor/domain/services/glossary_validator.py`

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
- [x] Loads terms from glossary.md
- [x] Validates arbitrary text
- [x] Returns list of undefined term usages

---

### T11-04-03: Integrate with LLM Output Processing

**Objective**: Hook glossary validation into LLM response processing.

**Files to Modify**:
- [x] `rice_factor/domain/services/glossary_validator.py` - validate_artifact() method

**Implementation**:
- [x] Add post-processing hook for LLM responses (validate_artifact method)
- [x] Extract domain terms from generated artifacts (recursive dict traversal)
- [x] Run GlossaryValidator on extracted terms
- [x] Collect validation errors before artifact creation

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
- [x] Validation runs on every LLM response (validate_artifact ready for integration)
- [x] Errors collected before artifact persisted
- [x] Clear integration point for future validators

---

### T11-04-04: Implement Undefined Term Detection

**Objective**: Detect when LLM uses terms not in glossary.

**Files to Modify**:
- [x] `rice_factor/domain/services/glossary_validator.py`

**Implementation**:
- [x] Define domain term patterns (capitalized words, quoted terms)
- [x] Extract potential terms from text
- [x] Compare against defined terms set
- [x] Track location (field, line) of undefined terms

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
- [x] Detects PascalCase domain terms
- [x] Detects quoted term references
- [x] Ignores common words and proper nouns
- [x] Reports location of each undefined term

---

### T11-04-05: Add Hard Failure Mechanism

**Objective**: Block artifact creation when undefined terms found.

**Files to Create/Modify**:
- [x] `rice_factor/domain/services/glossary_validator.py` - UndefinedTerm, GlossaryValidationResult

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
- [x] Blocks artifact creation on error (via GlossaryValidationResult.valid)
- [x] Provides actionable error messages (format_errors method)
- [x] Suggests similar terms when possible (_find_suggestion with difflib)

---

### T11-04-06: Write Unit Tests

**Objective**: Comprehensive test coverage for glossary validation.

**Files to Create/Modify**:
- [x] `tests/unit/domain/services/test_glossary_validator.py` (19 tests)

**Test Cases**:
- [x] Parse valid glossary with terms
- [x] Parse glossary with acronyms
- [x] Parse empty glossary
- [x] Parse malformed glossary (handles gracefully)
- [x] Detect single undefined term
- [x] Detect multiple undefined terms
- [x] Ignore common words
- [x] Suggest similar terms
- [x] Artifact validation (nested dicts)

**Acceptance Criteria**:
- [x] All parsing edge cases covered
- [x] All validation scenarios tested
- [x] 19 tests passing

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
