# Milestone 11: Enhanced Intake System - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)
> **Source Spec**: [06-tools-to-integrte-with-or-learn-from.md](../../raw/06-tools-to-integrte-with-or-learn-from.md)

---

## 1. Design Overview

The Enhanced Intake System strengthens the project initialization phase by:

1. Adding `decisions.md` as the 6th required intake file
2. Implementing strict validation that blocks planning until intake is complete
3. Detecting and rejecting vague or placeholder answers
4. Validating glossary terms during LLM output processing

This ensures **clarity before intelligence** - the LLM cannot proceed without well-defined inputs.

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Enhanced Intake System                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  InitService │  │IntakeValidator│  │ GlossaryValidator   │  │
│  │  (Extended)  │  │   (New)       │  │      (New)          │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                  │                      │              │
│         ↓                  ↓                      ↓              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Validation Pipeline                       ││
│  │  1. File existence check                                    ││
│  │  2. Template marker detection                               ││
│  │  3. Vague pattern detection                                 ││
│  │  4. Content quality check                                   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  ArtifactBuilder │ ← Blocked until valid
                    └─────────────────┘
```

### 2.2 File Organization

```
rice_factor/
├── domain/
│   └── services/
│       ├── init_service.py         # Extended with decisions.md
│       ├── intake_validator.py     # NEW: Blocking validation
│       └── glossary_validator.py   # NEW: Term validation
│
├── adapters/
│   └── validators/
│       └── intake_adapter.py       # NEW: Adapter for intake validation
│
└── entrypoints/
    └── cli/
        └── commands/
            ├── init.py             # Extended with decisions.md
            └── plan.py             # Extended with intake validation
```

---

## 3. Intake File System

### 3.1 Required Files (6 total)

| File | Purpose | Blocking |
|------|---------|----------|
| `requirements.md` | What must exist | Yes |
| `constraints.md` | What must never change | Yes |
| `glossary.md` | Meaning of terms | Yes |
| `non_goals.md` | Explicit exclusions | No* |
| `risks.md` | Known dangers | No* |
| `decisions.md` | Architecture choices and rationale | No* |

\* These files must exist but can contain minimal content.

### 3.2 decisions.md Template

```python
def _decisions_template(responses: QuestionnaireResponse) -> str:
    """Generate decisions.md content."""
    return """# Decision Log

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
"""
```

---

## 4. Intake Validator

### 4.1 Validation Pipeline

```python
class IntakeValidator:
    """Validates intake files are complete and not vague."""

    REQUIRED_FILES = [
        "requirements.md",
        "constraints.md",
        "glossary.md",
        "non_goals.md",
        "risks.md",
        "decisions.md",
    ]

    BLOCKING_FILES = [
        "requirements.md",
        "constraints.md",
        "glossary.md",
    ]

    VAGUE_PATTERNS = [
        "TBD",
        "To be determined",
        "We'll decide later",
        "Not sure",
        "Maybe",
        "Possibly",
        "[TODO]",
        "[Not provided]",
        "[Not specified]",
        "[Decision 1]",
        "[Alt A, Alt B]",
        "[Requirement description]",
        "[Term 1]",
        "[Definition]",
    ]

    def validate(self, project_dir: Path) -> IntakeValidationResult:
        """
        Validate all intake files.

        Returns:
            IntakeValidationResult with detailed errors
        """
        errors = []

        # Check 1: File existence
        for filename in self.REQUIRED_FILES:
            file_path = project_dir / filename
            if not file_path.exists():
                errors.append(IntakeError(
                    type=IntakeErrorType.FILE_MISSING,
                    file=filename,
                    message=f"Required file missing: {filename}",
                ))

        # Check 2: Empty files (blocking files only)
        for filename in self.BLOCKING_FILES:
            file_path = project_dir / filename
            if file_path.exists():
                content = file_path.read_text().strip()
                if not content:
                    errors.append(IntakeError(
                        type=IntakeErrorType.FILE_EMPTY,
                        file=filename,
                        message=f"Required file is empty: {filename}",
                    ))

        # Check 3: Vague patterns
        for filename in self.BLOCKING_FILES:
            file_path = project_dir / filename
            if file_path.exists():
                content = file_path.read_text()
                for pattern in self.VAGUE_PATTERNS:
                    if pattern in content:
                        errors.append(IntakeError(
                            type=IntakeErrorType.VAGUE_CONTENT,
                            file=filename,
                            message=f"Vague content detected: '{pattern}'",
                            pattern=pattern,
                        ))

        return IntakeValidationResult(
            valid=len(errors) == 0,
            errors=errors,
        )
```

### 4.2 Validation Result Model

```python
from enum import Enum
from dataclasses import dataclass

class IntakeErrorType(str, Enum):
    FILE_MISSING = "file_missing"
    FILE_EMPTY = "file_empty"
    VAGUE_CONTENT = "vague_content"
    UNDEFINED_TERM = "undefined_term"

@dataclass
class IntakeError:
    type: IntakeErrorType
    file: str
    message: str
    pattern: str | None = None
    line_number: int | None = None

@dataclass
class IntakeValidationResult:
    valid: bool
    errors: list[IntakeError]

    def format_errors(self) -> str:
        """Format errors for CLI display."""
        if self.valid:
            return "All intake files are valid."

        lines = ["Intake validation failed:", ""]
        for error in self.errors:
            lines.append(f"  - [{error.type.value}] {error.file}: {error.message}")
        return "\n".join(lines)
```

---

## 5. Glossary Term Validation

### 5.1 Glossary Parser

```python
class GlossaryParser:
    """Parse glossary.md to extract defined terms."""

    def parse(self, glossary_path: Path) -> set[str]:
        """
        Extract defined terms from glossary.md.

        Supports formats:
        - Markdown headers: ## TermName
        - Table format: | TermName | Definition |

        Returns:
            Set of defined term names (case-insensitive matching)
        """
        content = glossary_path.read_text()
        terms = set()

        # Extract from headers (## Term)
        for match in re.finditer(r'^##\s+(\w+)', content, re.MULTILINE):
            terms.add(match.group(1).lower())

        # Extract from tables (| Term | Definition |)
        for match in re.finditer(r'^\|\s*(\w+)\s*\|', content, re.MULTILINE):
            term = match.group(1).lower()
            if term not in ('term', 'acronym', '---'):
                terms.add(term)

        return terms
```

### 5.2 Term Validator

```python
class GlossaryValidator:
    """Validate that artifact terms are defined in glossary."""

    def __init__(self, glossary_path: Path):
        self.parser = GlossaryParser()
        self.defined_terms = self.parser.parse(glossary_path)

    def validate_artifact(self, artifact: dict) -> list[IntakeError]:
        """
        Check that all domain terms in artifact are defined.

        Extracts capitalized terms from artifact payload and
        verifies they exist in glossary.
        """
        errors = []
        terms_used = self._extract_terms(artifact)

        for term in terms_used:
            if term.lower() not in self.defined_terms:
                errors.append(IntakeError(
                    type=IntakeErrorType.UNDEFINED_TERM,
                    file="glossary.md",
                    message=f"Undefined term: '{term}' - add to glossary.md",
                    pattern=term,
                ))

        return errors

    def _extract_terms(self, artifact: dict) -> set[str]:
        """Extract capitalized domain terms from artifact."""
        text = json.dumps(artifact)
        # Find CamelCase and UPPERCASE terms
        terms = set()
        for match in re.finditer(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', text):
            terms.add(match.group(1))
        for match in re.finditer(r'\b([A-Z]{2,})\b', text):
            terms.add(match.group(1))
        return terms
```

---

## 6. Validation Timing

### 6.1 When Validation Occurs

From spec 2.4.1, validation runs at two distinct phases:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Validation Timing                             │
│                                                                  │
│  PLANNING PHASE (Pre-LLM)              EXECUTION PHASE           │
│  ┌─────────────────────────┐           ┌──────────────────────┐  │
│  │ 1. File existence       │           │ 1. Glossary terms    │  │
│  │ 2. Empty file check     │           │    in LLM output     │  │
│  │ 3. Vague pattern scan   │           │ 2. Term consistency  │  │
│  │ 4. Template marker check│           │    across artifacts  │  │
│  └──────────┬──────────────┘           └──────────┬───────────┘  │
│             │                                      │              │
│             │ BLOCKS                               │ WARNS        │
│             │ LLM invocation                       │ or BLOCKS    │
│             ↓                                      ↓              │
│       ┌─────────────────────────────────────────────────────────┐│
│       │              ArtifactBuilder.build()                     ││
│       └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Planning Phase Validation** (BLOCKS LLM call):
- Runs BEFORE any LLM invocation
- Validates intake files are complete and non-vague
- If validation fails, LLM is never called (saves cost + time)
- Errors are actionable: "Add definition to glossary.md"

**Execution Phase Validation** (BLOCKS artifact creation):
- Runs AFTER LLM generates artifact
- Validates terms used in artifact exist in glossary
- Ensures LLM didn't hallucinate undefined domain terms
- Can be configured to warn or block

### 6.2 Configuration

```yaml
# .project/config.yaml
intake:
  validation:
    # Planning phase
    require_all_files: true
    reject_vague_patterns: true
    reject_template_markers: true

    # Execution phase
    glossary_validation: strict  # strict | warn | off
    undefined_term_action: block  # block | warn
```

---

## 7. Integration with Artifact Builder

### 7.1 Pre-Build Validation

```python
class ArtifactBuilder:
    """Extended to validate intake before building."""

    def __init__(
        self,
        llm: LLMPort,
        intake_validator: IntakeValidator,
        glossary_validator: GlossaryValidator,
        ...
    ):
        self.intake_validator = intake_validator
        self.glossary_validator = glossary_validator
        ...

    def build(self, pass_type: CompilerPassType, context: dict) -> ArtifactEnvelope:
        """Build artifact with intake validation."""

        # Step 1: Validate intake files BEFORE invoking LLM (Planning Phase)
        project_dir = context.get("project_dir")
        if project_dir:
            intake_result = self.intake_validator.validate(project_dir)
            if not intake_result.valid:
                raise IntakeValidationError(intake_result)

        # Step 2: Invoke LLM (only if planning validation passed)
        result = self.llm.generate(pass_type, context, schema)

        # Step 3: Validate glossary terms in output (Execution Phase)
        if result.success:
            term_errors = self.glossary_validator.validate_artifact(result.payload)
            if term_errors:
                raise GlossaryValidationError(term_errors)

        return self._create_envelope(result)
```

### 7.2 Error Types

```python
class IntakeValidationError(RiceFactorError):
    """Raised when intake validation fails."""

    def __init__(self, result: IntakeValidationResult):
        self.result = result
        super().__init__(result.format_errors())

class GlossaryValidationError(RiceFactorError):
    """Raised when glossary validation fails."""

    def __init__(self, errors: list[IntakeError]):
        self.errors = errors
        message = "Undefined glossary terms found:\n"
        message += "\n".join(f"  - {e.pattern}" for e in errors)
        super().__init__(message)
```

---

## 8. CLI Integration

### 8.1 Enhanced Init Command

```python
@init_app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing"),
):
    """Initialize project with all 6 intake files."""
    service = InitService()

    # Now creates 6 files including decisions.md
    files = service.initialize(force=force)

    console.print(f"Created {len(files)} intake files:")
    for f in files:
        console.print(f"  - {f.name}")

    console.print("\n[yellow]Please complete all intake files before planning.[/]")
```

### 8.2 Enhanced Plan Commands

```python
@plan_app.command("project")
def plan_project():
    """Generate ProjectPlan (with intake validation)."""
    validator = IntakeValidator()
    project_dir = Path.cwd() / ".project"

    # Validate intake before planning
    result = validator.validate(project_dir)
    if not result.valid:
        console.print("[red]Intake validation failed:[/]")
        console.print(result.format_errors())
        raise typer.Exit(1)

    # Proceed with planning
    ...
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

- Test IntakeValidator with various file states
- Test vague pattern detection
- Test GlossaryParser with different formats
- Test term extraction from artifacts

### 9.2 Integration Tests

- Test `rice-factor init` creates 6 files
- Test `rice-factor plan project` fails with empty files
- Test `rice-factor plan project` fails with vague content
- Test planning succeeds with complete intake

### 9.3 Test Fixtures

```python
@pytest.fixture
def incomplete_intake(tmp_path):
    """Create .project/ with incomplete intake."""
    project_dir = tmp_path / ".project"
    project_dir.mkdir()
    (project_dir / "requirements.md").write_text("# Requirements\n\nTBD")
    (project_dir / "constraints.md").write_text("")
    return project_dir
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial milestone design |
