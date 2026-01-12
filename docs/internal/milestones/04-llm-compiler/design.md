# Milestone 04: LLM Compiler - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

The LLM Compiler milestone implements the "LLM as compiler" philosophy where the LLM acts as a pure compilation stage that transforms human intent into structured artifacts (IR).

**Key Design Goals:**
- LLM produces structured JSON artifacts, never code
- Deterministic outputs through controlled parameters
- Explicit failure handling with human-in-the-loop
- Provider-agnostic through hexagonal architecture
- Single authority agent model (MVP)

**Core Philosophy:**
- The LLM is NOT an assistant
- The LLM is NOT a coder
- The LLM is a **pure compiler stage**

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLI Layer (from M03)                            │
│  plan project | plan tests | plan impl | plan refactor                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────┐
│                         Domain Services                                  │
│                                │                                         │
│  ┌─────────────────────────────┴─────────────────────────────────────┐  │
│  │                      ArtifactBuilder                              │  │
│  │  • Orchestrates compilation                                       │  │
│  │  • Manages context building                                       │  │
│  │  • Validates output                                               │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                       │
│  ┌───────────────┐  ┌────────────┴────────────┐  ┌──────────────────┐  │
│  │ContextBuilder │  │   CompilerPassRegistry   │  │ OutputValidator  │  │
│  │ (gather input)│  │  (6 passes registered)   │  │ (JSON + schema)  │  │
│  └───────────────┘  └────────────┬────────────┘  └──────────────────┘  │
│                                  │                                       │
│  ┌───────────────────────────────┴───────────────────────────────────┐  │
│  │                       CompilerPass (Base)                         │  │
│  │  ProjectPlanner | ArchPlanner | ScaffoldPlanner | TestDesigner    │  │
│  │  ImplementationPlanner | RefactorPlanner                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                  │                                       │
│  ┌───────────────────────────────┴───────────────────────────────────┐  │
│  │                       Prompts Module                              │  │
│  │  BASE_SYSTEM_PROMPT + pass-specific prompts + schema injection    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                  │                                       │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼───────────────────────────────────────┐
│                          Domain Ports                                    │
│                                  │                                       │
│  ┌───────────────────────────────┴───────────────────────────────────┐  │
│  │                         LLMPort                                   │  │
│  │  Protocol:                                                        │  │
│  │    generate(pass_type, context, schema) -> CompilerResult         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼───────────────────────────────────────┐
│                            Adapters                                      │
│                                  │                                       │
│  ┌──────────────────┐  ┌────────┴────────┐  ┌───────────────────────┐  │
│  │  ClaudeAdapter   │  │  OpenAIAdapter  │  │    StubLLMAdapter     │  │
│  │  (anthropic SDK) │  │  (openai SDK)   │  │    (testing/dev)      │  │
│  └──────────────────┘  └─────────────────┘  └───────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Hexagonal File Organization

```
rice_factor/
├── domain/
│   ├── ports/
│   │   └── llm.py                    # LLMPort protocol (NEW)
│   │
│   ├── artifacts/
│   │   ├── compiler_types.py         # CompilerPassType, CompilerContext, CompilerResult (NEW)
│   │   └── payloads/
│   │       └── failure_report.py     # FailureReportPayload (NEW)
│   │
│   ├── prompts/                      # NEW MODULE
│   │   ├── __init__.py               # PromptManager
│   │   ├── base.py                   # BASE_SYSTEM_PROMPT
│   │   ├── project_planner.py        # Project planner prompt
│   │   ├── architecture_planner.py   # Architecture planner prompt
│   │   ├── scaffold_planner.py       # Scaffold planner prompt
│   │   ├── test_designer.py          # Test designer prompt
│   │   ├── implementation_planner.py # Implementation planner prompt
│   │   ├── refactor_planner.py       # Refactor planner prompt
│   │   └── schema_injector.py        # Schema injection utility
│   │
│   ├── services/
│   │   ├── context_builder.py        # Build context for passes (NEW)
│   │   ├── artifact_builder.py       # Main compilation orchestrator (NEW)
│   │   ├── compiler_pass.py          # Base CompilerPass class (NEW)
│   │   ├── json_extractor.py         # Extract JSON from LLM response (NEW)
│   │   ├── output_validator.py       # Validate LLM output (NEW)
│   │   ├── code_detector.py          # Detect code in output (NEW)
│   │   ├── failure_parser.py         # Parse LLM failure responses (NEW)
│   │   ├── failure_service.py        # Create FailureReport artifacts (NEW)
│   │   └── passes/                   # NEW SUBMODULE
│   │       ├── __init__.py           # PassRegistry
│   │       ├── project_planner.py    # ProjectPlannerPass
│   │       ├── architecture_planner.py
│   │       ├── scaffold_planner.py
│   │       ├── test_designer.py
│   │       ├── implementation_planner.py
│   │       └── refactor_planner.py
│   │
│   └── failures/
│       └── llm_errors.py             # LLM-specific error types (NEW)
│
├── adapters/
│   └── llm/
│       ├── __init__.py               # Export adapters
│       ├── stub.py                   # Existing stub adapter (UPDATE)
│       ├── claude.py                 # Claude adapter (NEW)
│       ├── claude_client.py          # Claude API client (NEW)
│       ├── openai_adapter.py         # OpenAI adapter (NEW)
│       └── openai_client.py          # OpenAI API client (NEW)
│
├── config/
│   ├── settings.py                   # Add LLM config (UPDATE)
│   └── container.py                  # Wire LLM adapters (UPDATE)
│
└── schemas/
    └── failure_report.schema.json    # FailureReport JSON schema (NEW)
```

---

## 3. LLM Protocol Design

### 3.1 LLMPort Protocol

```python
from typing import Protocol
from rice_factor.domain.artifacts.compiler_types import (
    CompilerPassType, CompilerContext, CompilerResult
)

class LLMPort(Protocol):
    """Abstract interface for LLM providers."""

    def generate(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict
    ) -> CompilerResult:
        """
        Generate an artifact for the given compiler pass.

        Args:
            pass_type: Which compiler pass to execute
            context: Input context (files, artifacts)
            schema: JSON Schema for output validation

        Returns:
            CompilerResult with artifact payload or error

        Raises:
            LLMAPIError: Provider API failure
            LLMTimeoutError: Request timeout
            LLMRateLimitError: Rate limiting
        """
        ...
```

### 3.2 Compiler Types

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any

class CompilerPassType(Enum):
    PROJECT = "project"
    ARCHITECTURE = "architecture"
    SCAFFOLD = "scaffold"
    TEST = "test"
    IMPLEMENTATION = "implementation"
    REFACTOR = "refactor"

@dataclass
class CompilerContext:
    """Input context for a compiler pass."""
    pass_type: CompilerPassType
    project_files: dict[str, str]    # path -> content
    artifacts: dict[str, Any]        # artifact_id -> payload
    target_file: str | None = None   # For implementation pass

@dataclass
class CompilerResult:
    """Result from a compiler pass."""
    success: bool
    payload: dict | None = None      # Artifact payload if success
    error_type: str | None = None    # "missing_information", "invalid_request"
    error_details: str | None = None
    raw_response: str | None = None  # For debugging
```

---

## 4. Compiler Pass Design

### 4.1 Base CompilerPass

```python
from abc import ABC, abstractmethod

class CompilerPass(ABC):
    """Base class for compiler passes."""

    @property
    @abstractmethod
    def pass_type(self) -> CompilerPassType:
        """Return the pass type."""
        ...

    @property
    @abstractmethod
    def required_inputs(self) -> list[str]:
        """Return list of required input keys."""
        ...

    @property
    @abstractmethod
    def forbidden_inputs(self) -> list[str]:
        """Return list of forbidden input types."""
        ...

    @property
    @abstractmethod
    def output_artifact_type(self) -> ArtifactType:
        """Return the output artifact type."""
        ...

    def compile(self, context: CompilerContext, llm: LLMPort) -> CompilerResult:
        """Template method for compilation."""
        self.validate_context(context)
        prompt = self.build_prompt(context)
        schema = self.get_output_schema()
        result = llm.generate(self.pass_type, context, schema)
        if result.success:
            self.validate_output(result.payload)
        return result
```

### 4.2 Pass Input/Output Specification

| Pass | Required Inputs | Forbidden Inputs | Output |
|------|-----------------|------------------|--------|
| Project Planner | requirements.md, constraints.md, glossary.md | source code, tests | ProjectPlan |
| Architecture Planner | ProjectPlan (approved), constraints.md | - | ArchitecturePlan |
| Scaffold Planner | ProjectPlan (approved), ArchitecturePlan (approved) | - | ScaffoldPlan |
| Test Designer | ProjectPlan, ArchitecturePlan, ScaffoldPlan (all approved), requirements.md | - | TestPlan |
| Implementation Planner | TestPlan (approved), ScaffoldPlan (approved), target file | All other source files | ImplementationPlan |
| Refactor Planner | ArchitecturePlan (approved), TestPlan (locked), repo layout | - | RefactorPlan |

---

## 5. System Prompt Design

### 5.1 Global System Prompt (Canonical)

```
SYSTEM PROMPT — ARTIFACT BUILDER

You are an Artifact Builder.

You are a compiler stage in a deterministic development system.

Rules:
* You do not generate source code.
* You do not explain decisions.
* You do not include reasoning or commentary.
* You output valid JSON only.
* You generate exactly one artifact per invocation.
* You must conform exactly to the provided JSON Schema.
* If required information is missing or ambiguous, you must fail with:

{ "error": "missing_information", "details": "<description>" }

Any deviation from these rules is a failure.
```

### 5.2 Pass-Specific Prompt Structure

Each pass prompt includes:
1. **Purpose**: What this pass accomplishes
2. **Inputs**: What data is provided
3. **Rules**: Pass-specific constraints
4. **Output Schema**: JSON Schema reference
5. **Failure Conditions**: When to emit error

---

## 6. Validation Pipeline

### 6.1 Output Validation Flow

```
LLM Response
     │
     ▼
┌─────────────────┐
│ JSON Extractor  │──▶ Extract JSON from response
└────────┬────────┘    Handle markdown fences
         │             Reject multiple objects
         ▼
┌─────────────────┐
│ Failure Parser  │──▶ Check for error response
└────────┬────────┘    {"error": "...", "details": "..."}
         │
         ▼
┌─────────────────┐
│ Schema Validator│──▶ Validate against JSON Schema
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Code Detector   │──▶ Check for code snippets
└────────┬────────┘    Reject if found
         │
         ▼
┌─────────────────┐
│Output Validator │──▶ Final validation checks
└────────┬────────┘
         │
         ▼
    CompilerResult
```

### 6.2 Rejection Criteria

| Condition | Error Type | Action |
|-----------|------------|--------|
| Non-JSON response | InvalidJSONError | Reject immediately |
| Multiple JSON objects | MultipleArtifactsError | Reject |
| Schema mismatch | SchemaViolationError | Reject |
| Code detected | CodeInOutputError | Reject |
| Explanatory text | ExplanatoryTextError | Reject |
| Missing info (LLM) | LLMMissingInformationError | Halt for human |
| Invalid request (LLM) | LLMInvalidRequestError | Reject |

---

## 7. Error Handling Strategy

### 7.1 Error Taxonomy

```
LLMError (base)
├── LLMAPIError           # Provider API failure
├── LLMTimeoutError       # Request timeout
├── LLMRateLimitError     # Rate limiting
├── LLMOutputError (base)
│   ├── InvalidJSONError
│   ├── SchemaViolationError
│   ├── CodeInOutputError
│   ├── MultipleArtifactsError
│   └── ExplanatoryTextError
├── LLMMissingInformationError  # Explicit LLM failure
└── LLMInvalidRequestError      # Explicit LLM failure
```

### 7.2 FailureReport Artifact

When blocking failures occur, create a FailureReport artifact:

```json
{
  "phase": "planning",
  "artifact_id": "uuid-of-failed-artifact",
  "category": "missing_information",
  "summary": "Domain 'User' referenced but not defined in glossary.md",
  "details": {...},
  "blocking": true,
  "recovery_action": "human_input_required"
}
```

---

## 8. Provider Adapter Design

### 8.1 Claude Adapter

```python
class ClaudeAdapter(LLMPort):
    """Anthropic Claude API adapter."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.0,
        top_p: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 120
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.timeout = timeout

    def generate(self, pass_type, context, schema) -> CompilerResult:
        # Build messages
        # Call API with determinism parameters
        # Extract and validate response
        ...
```

### 8.2 Provider Configuration

```python
# config/settings.py
LLM_PROVIDER = "claude"  # or "openai", "stub"
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
OPENAI_API_KEY = env("OPENAI_API_KEY")
LLM_MODEL = env("LLM_MODEL", default="claude-3-5-sonnet-20241022")
LLM_TEMPERATURE = env.float("LLM_TEMPERATURE", default=0.0)
LLM_TOP_P = env.float("LLM_TOP_P", default=0.3)
LLM_TIMEOUT = env.int("LLM_TIMEOUT", default=120)
```

---

## 9. Testing Strategy

### 9.1 Unit Tests (Mocked LLM)

- Mock LLM responses for each pass type
- Test valid artifact generation
- Test all rejection scenarios
- Test error handling paths

### 9.2 Contract Tests

- Verify prompt structure matches spec
- Verify schema injection works
- Verify determinism parameters enforced

### 9.3 Integration Tests

- Test full compilation flow with stub adapter
- Test provider selection via configuration

---

## 10. CLI Integration

### 10.1 Command Flow

```
rice-factor plan project
     │
     ▼
PhaseService.can_execute("plan_project")
     │
     ▼
ArtifactBuilder.build(CompilerPassType.PROJECT)
     │
     ├── ContextBuilder.build_context()
     ├── PromptManager.get_system_prompt()
     ├── LLMPort.generate()
     ├── OutputValidator.validate()
     └── ArtifactService.save()
     │
     ▼
Display result to user
```

### 10.2 Existing CLI Commands to Update

- `rice-factor plan project` - Wire to ProjectPlannerPass
- `rice-factor plan architecture` - Wire to ArchitecturePlannerPass
- `rice-factor plan tests` - Wire to TestDesignerPass
- `rice-factor plan impl <file>` - Wire to ImplementationPlannerPass
- `rice-factor plan refactor <goal>` - Wire to RefactorPlannerPass

---

## 11. Implementation Order

1. **F04-01**: LLMPort protocol and types (foundation)
2. **F04-07**: Error handling and FailureReport (needed by all)
3. **F04-05**: System prompts (needed by passes)
4. **F04-06**: Output validation (needed by passes)
5. **F04-04**: Compiler pass framework (core logic)
6. **F04-02**: Claude adapter (primary provider)
7. **F04-03**: OpenAI adapter (secondary provider)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial design document |
