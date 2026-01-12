# Rice-Factor Project Design Document

> **Document Type**: Project-Level Architecture & Design Specification
> **Version**: 1.0.0
> **Status**: Draft

---

## 1. Design Philosophy

### 1.1 Mental Model

> **LLM = Planner & Compiler**
> **Artifacts = Contracts (IR)**
> **Tools = Dumb Executors**
> **Tests = Immovable Truth**

The system operates as a **compiler pipeline** rather than a chat assistant:
- LLMs perform **compiler passes** that generate structured IR (artifacts)
- Executors **mechanically apply** artifacts without interpretation
- Tests define **correctness** and are never modified by automation
- Humans **architect and approve**, they don't edit code directly

### 1.2 Architectural Paradigm

| Approach | Fits Rice-Factor? | Rationale |
|----------|-------------------|-----------|
| **Hexagonal (Ports & Adapters)** | ✅ **Selected** | Perfect for pluggable LLM/executor adapters |
| **Clean Architecture** | ✅ Compatible | Similar goals, more prescriptive layers |
| **Domain-Driven Design (DDD)** | ✅ Strategic | Bounded contexts align with artifact domains |
| **Event-Driven** | ⚠️ Partial | Useful for failure recovery, not core architecture |
| **Microservices** | ❌ Not for MVP | Over-engineering for single-user CLI tool |
| **Monolith** | ✅ For MVP | Single deployable unit, simpler development |

**Decision**: Hexagonal Architecture (Ports & Adapters) with DDD strategic patterns, monolithic deployment for MVP.

### 1.3 Development Methodology

**Artifact-driven development** with:
- **TDD** for implementation (tests locked before code)
- **Artifact-first** workflow (plans before execution)
- **Human-in-the-loop** approval gates

---

## 2. High-Level Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Human Interface                           │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │   CLI   │  │ Review UI   │  │ Approval UI │                  │
│  └────┬────┘  └──────┬──────┘  └──────┬──────┘                  │
└───────┼──────────────┼────────────────┼─────────────────────────┘
        │              │                │
┌───────┴──────────────┴────────────────┴─────────────────────────┐
│                      Orchestrator Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Phase Manager│  │ Run Mode Cfg │  │ Coordination Protocol │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                    Artifact Builder (LLM)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │  Planner   │  │ Scaffolder │  │ Test Des.  │  │ Impl Plan │  │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                      Artifact Store                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │  Registry  │  │  Approvals │  │  Validator │  │   Loader  │  │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                      Executor Engine                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │  Scaffold  │  │    Diff    │  │  Refactor  │  │ Cap Check │  │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                    Validation Engine                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │Test Runner │  │ Lint/Format│  │ Arch Rules │  │ Invariants│  │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility | Automation Allowed |
|-----------|----------------|-------------------|
| **Orchestrator** | Drives lifecycle phases, coordinates agents | ✅ |
| **Artifact Builder** | Compiles intent → IR via LLM | ✅ (via builder only) |
| **Artifact Store** | Versioned artifact persistence | ✅ (append-only) |
| **Executor Engine** | Applies IR via dumb tools | ✅ (with approval) |
| **Validation Engine** | Tests, lint, static analysis | ✅ |
| **Human Interface** | Approvals, diffs, overrides | ❌ (human-driven) |
| **Capability Registry** | What operations each language supports | ❌ (human-maintained) |

---

## 3. Repository Layout

### 3.1 Hexagonal Architecture Structure

The codebase follows **Hexagonal Architecture (Ports & Adapters)** with clear separation between domain logic and external concerns.

```
rice_factor/                           # Main package (hexagonal structure)
├── domain/                            # Core business logic (NO external deps)
│   ├── __init__.py
│   ├── artifacts/                     # Artifact domain models
│   │   ├── __init__.py
│   │   ├── models.py                  # Pydantic models for artifacts
│   │   └── enums.py                   # ArtifactType, ArtifactStatus
│   ├── ports/                         # Interface definitions (abstractions)
│   │   ├── __init__.py
│   │   ├── llm.py                     # LLMPort protocol
│   │   ├── storage.py                 # StoragePort protocol
│   │   ├── executor.py                # ExecutorPort protocol
│   │   └── validator.py               # ValidatorPort protocol
│   └── services/                      # Domain services
│       ├── __init__.py
│       ├── artifact_service.py        # Artifact lifecycle management
│       └── orchestrator.py            # Phase orchestration
│
├── adapters/                          # External implementations
│   ├── __init__.py
│   ├── llm/                           # LLM provider adapters
│   │   ├── __init__.py
│   │   ├── claude.py                  # Anthropic Claude adapter
│   │   ├── openai.py                  # OpenAI adapter
│   │   └── local.py                   # Ollama/vLLM adapter
│   ├── storage/                       # Artifact storage adapters
│   │   ├── __init__.py
│   │   └── filesystem.py              # JSON file storage
│   ├── executors/                     # Executor adapters
│   │   ├── __init__.py
│   │   ├── scaffold.py                # ScaffoldExecutor
│   │   ├── diff.py                    # DiffExecutor (git apply)
│   │   └── refactor.py                # RefactorExecutor
│   └── validators/                    # Validator adapters
│       ├── __init__.py
│       ├── schema.py                  # JSON Schema validator
│       └── test_runner.py             # Native test runner adapter
│
├── entrypoints/                       # Application entry points
│   ├── __init__.py
│   └── cli/                           # CLI adapter (Typer)
│       ├── __init__.py
│       ├── main.py                    # `rice-factor` command
│       └── commands/                  # Subcommands
│           ├── __init__.py
│           ├── init.py                # rice-factor init
│           ├── plan.py                # rice-factor plan
│           ├── scaffold.py            # rice-factor scaffold
│           ├── impl.py                # rice-factor impl
│           ├── test.py                # rice-factor test
│           └── refactor.py            # rice-factor refactor
│
└── config/                            # Configuration
    ├── __init__.py
    └── settings.py                    # Environment-based settings

# Project-managed directories (in target repositories)
.project/                              # Human-owned (NEVER automated)
├── requirements.md                    # Problem statement
├── constraints.md                     # Technical constraints
├── glossary.md                        # Domain terminology
├── non_goals.md                       # Explicit exclusions
├── risks.md                           # Risk assessment
└── decisions.md                       # Architecture decision log

artifacts/                             # System-owned IR (versioned)
├── _meta/
│   ├── index.json                     # Artifact registry
│   └── approvals.json                 # Human approvals
├── planning/
│   ├── project_plan.json
│   ├── architecture_plan.json
│   └── scaffold_plan.json
├── tests/
│   └── test_plan.json                 # LOCKED after approval
├── implementation/
│   └── <path>.json                    # Per-file implementation plans
└── refactor/
    └── <goal>.json                    # Refactoring plans

audit/                                 # Immutable audit trail
├── diffs/                             # Every diff applied
├── executions.log                     # Every executor invocation
├── validation.log                     # Every test/lint result
└── failures.log                       # Every failure (no silent failures)

schemas/                               # JSON Schema definitions
├── artifact.schema.json
├── project_plan.schema.json
└── ...
```

### 3.2 Hexagonal Layers Explained

| Layer | Purpose | Dependencies |
|-------|---------|--------------|
| **domain/** | Core business logic, artifact models, ports | None (pure Python) |
| **adapters/** | Implementations of ports | domain/, external libraries |
| **entrypoints/** | Application entry points (CLI, API) | domain/, adapters/ |
| **config/** | Configuration and DI setup | All layers |

### 3.3 Ownership Rules

| Path | Owner | Automation |
|------|-------|------------|
| `.project/` | Human | ❌ NEVER |
| `artifacts/` | System | ⚠️ Only via artifact builder |
| `src/` | Mixed | ✅ Via approved plans |
| `tests/` | Mixed | ❌ After TestPlan lock |
| `audit/` | System | ✅ Append-only |
| `rice_factor/` | Human | ❌ Development code |

---

## 4. Technology Stack

### 4.1 Core Technologies

| Layer | Technology | Alternative Considered | Decision Rationale |
|-------|------------|----------------------|-------------------|
| **Language** | Python 3.11+ | Go, Rust | Best for orchestration, JSON Schema, rapid CLI development |
| **CLI Framework** | [Typer](https://typer.tiangolo.com/) | Click, argparse | Type hints, auto-completion, minimal boilerplate |
| **Schema Validation** | [Pydantic v2](https://docs.pydantic.dev/) + jsonschema | jsonschema alone | Pydantic for Python models, jsonschema for runtime validation |
| **LLM Interface** | Abstract (pluggable) | N/A | Support Claude, OpenAI, local models |
| **Diff Engine** | git diff / git apply | libgit2, unidiff | Standard, human-readable, safe rollback |
| **Test Runner** | Native (cargo, go, mvn) | Unified | Language-native for developer trust |

### 4.2 LLM Provider Strategy (Pluggable Adapters)

All LLM providers are implemented as adapters that conform to the `LLMPort` protocol:

```python
# domain/ports/llm.py - Port definition (interface)
from typing import Protocol

class LLMPort(Protocol):
    """Port for LLM interactions - all adapters must implement this."""

    def generate_artifact(
        self,
        system_prompt: str,
        user_input: str,
        schema: dict
    ) -> dict:
        """Generate a structured artifact conforming to the schema."""
        ...
```

```python
# adapters/llm/claude.py - Adapter implementation
from domain.ports.llm import LLMPort

class ClaudeAdapter:
    """Anthropic Claude adapter implementing LLMPort."""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_artifact(self, system_prompt: str, user_input: str, schema: dict) -> dict:
        # Implementation using Claude structured outputs
        ...
```

**Supported adapters:**
- `ClaudeAdapter` - Anthropic Claude (structured outputs)
- `OpenAIAdapter` - OpenAI GPT-4 (function calling)
- `LocalAdapter` - Ollama, vLLM (local models)

### 4.3 Structured Output Strategy

Use [Claude Structured Outputs](https://docs.anthropic.com/claude/docs/structured-outputs) with JSON Schema for guaranteed schema compliance:
- Define schemas in Pydantic
- Export to JSON Schema
- Validate outputs automatically
- Zero parsing errors with structured output mode

---

## 5. Artifact System Design

### 5.1 Universal Artifact Envelope

Every artifact conforms to this structure:

```json
{
  "$schema": "https://example.dev/schemas/artifact.schema.json",
  "artifact_type": "ProjectPlan | ArchitecturePlan | ScaffoldPlan | TestPlan | ImplementationPlan | RefactorPlan | ValidationResult",
  "artifact_version": "1.0",
  "id": "uuid",
  "status": "draft | approved | locked",
  "created_by": "llm | human",
  "created_at": "ISO-8601",
  "depends_on": ["uuid"],
  "payload": {}
}
```

### 5.2 Artifact Types

| Type | Purpose | Status Transitions |
|------|---------|-------------------|
| **ProjectPlan** | System decomposition | draft → approved |
| **ArchitecturePlan** | Dependency rules | draft → approved |
| **ScaffoldPlan** | File structure | draft → approved |
| **TestPlan** | Correctness contract | draft → approved → **locked** |
| **ImplementationPlan** | Per-file steps | draft → approved |
| **RefactorPlan** | Structural changes | draft → approved |
| **ValidationResult** | Execution feedback | (generated only) |

### 5.3 Immutability Rules

- `status=locked` → artifact is immutable forever
- `status=approved` → artifact cannot be edited, only superseded
- `depends_on` must reference approved/locked artifacts only
- Executors reject `draft` artifacts

---

## 6. LLM Compiler Design

### 6.1 Core Contract (Non-Negotiable)

Every LLM invocation must:
1. Output **valid JSON only**
2. Output **exactly one artifact**
3. Output **no explanations**
4. Output **no code**
5. Conform **exactly** to the provided schema
6. Fail explicitly if information is missing

### 6.2 Compiler Passes

| Pass | Input | Output | Context Size |
|------|-------|--------|--------------|
| Project Planner | requirements.md, constraints.md, glossary.md | ProjectPlan | Large |
| Architecture Planner | ProjectPlan, constraints.md | ArchitecturePlan | Medium |
| Scaffold Planner | ProjectPlan, ArchitecturePlan | ScaffoldPlan | Medium |
| Test Designer | ProjectPlan, ScaffoldPlan, requirements.md | TestPlan | Medium |
| Implementation Planner | TestPlan, target file, interfaces | ImplementationPlan | **Tiny** |
| Refactor Planner | ArchitecturePlan, TestPlan, repo layout | RefactorPlan | Medium |

### 6.3 Determinism Controls

- Temperature: **0.0–0.2**
- Top-p: **≤ 0.3**
- No streaming
- One artifact per call
- Structured output mode enabled

---

## 7. Executor Design

### 7.1 Executor Port Interface

Executors follow the Hexagonal pattern with a port (interface) and adapters (implementations):

```python
# domain/ports/executor.py - Port definition
from typing import Protocol, Literal
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ExecutionResult:
    status: Literal["success", "failure"]
    diffs: list[Path]
    errors: list[str]
    logs: list[str]

class ExecutorPort(Protocol):
    """Port for executing artifacts - all executor adapters implement this."""

    def execute(
        self,
        artifact_path: Path,
        repo_root: Path,
        mode: Literal["DRY_RUN", "APPLY"]
    ) -> ExecutionResult:
        ...
```

```python
# adapters/executors/scaffold.py - Adapter implementation
from domain.ports.executor import ExecutorPort, ExecutionResult

class ScaffoldExecutor:
    """Adapter that creates file scaffolding from ScaffoldPlan artifacts."""

    def execute(self, artifact_path, repo_root, mode) -> ExecutionResult:
        # Implementation: create directories and empty files
        ...
```

### 7.2 Executor Pipeline

Every executor follows this exact sequence:

```
1. Load artifact
2. Validate schema
3. Verify approval & lock status
4. Capability check (per language)
5. Precondition checks
6. Generate diff
7. (If APPLY) Apply diff
8. Emit audit logs
9. Return result
```

### 7.3 MVP Executors

| Executor | Purpose | Operations |
|----------|---------|------------|
| **ScaffoldExecutor** | Create empty files | mkdir, touch, add comments |
| **DiffExecutor** | Apply approved diffs | git apply |
| **RefactorExecutor** | Mechanical refactors | move_file, rename_symbol |
| **TestRunner** | Verify correctness | cargo test, go test, etc. |

---

## 8. Multi-Agent Coordination

### 8.1 Core Principle

> **Only one agent is ever allowed to produce authoritative artifacts at a time.**

### 8.2 Run Modes

| Mode | Agents | Best For |
|------|--------|----------|
| **Single Agent** | 1 (Primary) | MVP, solo developer |
| **Orchestrator + Specialists** | 1 Primary + N helpers | Non-trivial projects |
| **Voting** | N identical → 1 selected | Ideation diversity |
| **Role-Locked** | Domain experts + Primary | Regulated domains |
| **Hybrid** | Mix of above | Production systems |

### 8.3 Agent Roles

- **Primary**: Only agent that emits artifacts
- **Planner**: Suggests structure
- **Critic**: Reviews, identifies issues
- **Specialist**: Domain-specific analysis
- **Test Strategist**: Evaluates test coverage

---

## 9. Failure & Recovery Model

### 9.1 Failure Categories

| Category | Detected By | Recovered By |
|----------|-------------|--------------|
| Human-Input | Artifact Builder | Human clarification |
| Planning | Schema validation, critics | Re-planning (same phase) |
| Execution | Executors | Plan correction |
| Verification | Validators, CI | New ImplementationPlan |
| Drift | Periodic audits | Reconciliation cycle |

### 9.2 Failure Artifacts

Failures are first-class artifacts:

```json
{
  "type": "FailureReport",
  "id": "uuid",
  "phase": "planning | execution | verification | refactor",
  "category": "planning | execution | verification | drift",
  "summary": "string",
  "details": ["string"],
  "detected_at": "ISO-8601",
  "blocking": true
}
```

### 9.3 Recovery Playbooks

- **Planning Failure**: Halt → Human edits .project/ → Re-run pass
- **Execution Failure**: Rollback → FailureReport → New plan required
- **Verification Failure**: ValidationResult → New ImplementationPlan (same unit)
- **Refactor Failure**: Abort → Discard diff → Revise RefactorPlan

---

## 10. CI/CD Integration

### 10.1 CI Responsibilities

CI **verifies, enforces, rejects, records** — never invents.

### 10.2 CI Pipeline Stages

```
Checkout
  ↓
Artifact Validation (schema + approval)
  ↓
Invariant Enforcement (test lock, planned changes)
  ↓
Test Execution
  ↓
Audit Verification
```

### 10.3 CI Failure Taxonomy

| Failure | Meaning |
|---------|---------|
| `draft_artifact_present` | Planning incomplete |
| `artifact_not_approved` | Human gate skipped |
| `test_modification_after_lock` | TDD violated |
| `unplanned_code_change` | Rogue edit |
| `architecture_violation` | Structural drift |
| `test_failure` | Behavioral regression |

---

## 11. Technology Alternatives Considered

### 11.1 CLI Frameworks

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **argparse** | Built-in, no deps | Verbose, manual | ❌ |
| **Click** | Mature, flexible | More boilerplate | ❌ |
| **Typer** | Type hints, auto-complete | Dependency on Click | ✅ Selected |

### 11.2 Validation Libraries

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **jsonschema** | Pure JSON Schema validation | No Python type safety | ✅ For runtime |
| **Pydantic v2** | Type-safe, fast (Rust core) | Doesn't validate JSON Schema directly | ✅ For models |

### 11.3 Refactoring Tools

| Language | Tool | Notes |
|----------|------|-------|
| **JVM** | OpenRewrite | Production-grade, LST-based |
| **Rust** | rust-analyzer SSR | Structured Search Replace |
| **Go** | gopls | Limited refactoring |
| **JS/TS** | jscodeshift, ts-morph | AST manipulation |

---

## 12. Security Considerations

- No secrets in artifacts
- No LLM access to filesystem
- All diffs reviewed before apply
- Audit trail for compliance
- Git-backed rollback capability

---

## 13. Future Considerations

Post-MVP features (no architecture changes needed):
- ArchitecturePlan enforcement
- Advanced refactor operations (extract_interface)
- Multi-language support
- Parallel execution
- Web UI
- Team collaboration

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial design specification |
| 1.1.0 | 2026-01-10 | User Decision | Updated to Hexagonal Architecture, `rice-factor` CLI command, pluggable LLM adapters |
