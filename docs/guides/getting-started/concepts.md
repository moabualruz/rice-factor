# Core Concepts

This guide explains the fundamental concepts behind Rice-Factor.

## Philosophy

Rice-Factor treats LLMs fundamentally differently than typical AI coding assistants:

| Traditional Approach | Rice-Factor Approach |
|---------------------|---------------------|
| LLM writes code directly | LLM generates structured plans |
| Chat-based interaction | Artifact-based workflow |
| Human reviews code | Human approves plans |
| Tests are optional | Tests are locked law |
| Unpredictable outputs | Deterministic, validated |

## Key Concepts

### 1. Artifacts as Intermediate Representation

In compiler design, code goes through intermediate representations (IR) before becoming machine code. Rice-Factor applies this concept to software development:

```
Requirements → [LLM Compiler] → Artifacts (IR) → [Executor] → Code
```

**Artifacts are:**
- Structured JSON documents
- Schema-validated
- Immutable once approved
- The single source of truth

### 2. LLMs as Compilers

Rice-Factor treats LLMs as **compilers**, not assistants:

- **Input**: Project context (requirements, constraints, existing code)
- **Output**: Structured JSON artifacts
- **Behavior**: Deterministic (temperature 0.0, strict sampling)

The LLM never:
- Writes directly to disk
- Executes commands
- Makes decisions without approval

### 3. Artifact Lifecycle

Every artifact follows a strict state machine:

```
┌──────────┐     approve     ┌──────────┐     lock      ┌──────────┐
│  DRAFT   │ ─────────────→  │ APPROVED │ ────────────→ │  LOCKED  │
└──────────┘                 └──────────┘               └──────────┘
     │                            │                          │
     │ (editable)                 │ (executable)             │ (immutable)
     │                            │                          │
     └────────────────────────────┴──────────────────────────┘
```

- **DRAFT**: Can be modified, not executable
- **APPROVED**: Ready for execution, no longer editable
- **LOCKED**: Permanently immutable (TestPlan only)

### 4. Tests as Immutable Law

In Rice-Factor, the TestPlan is special:

1. Generated before implementation
2. Approved by human
3. **Locked permanently**

Once locked, tests cannot be modified by automation. This enforces TDD at the system level - if tests fail, implementation must change, not tests.

### 5. Human Approval Gates

Rice-Factor requires human approval at irreversible boundaries:

| Operation | Requires Approval |
|-----------|------------------|
| DRAFT → APPROVED | Yes |
| APPROVED → LOCKED | Yes (explicit "LOCK" confirmation) |
| Apply diff to code | Yes |
| Override validation | Yes (with audit trail) |

This ensures humans remain architects, not just reviewers.

## Artifact Types

Rice-Factor manages 9 artifact types:

### Planning Artifacts

| Artifact | Purpose | When Created |
|----------|---------|--------------|
| **ProjectPlan** | Defines domains, modules, constraints | After `init` |
| **ArchitecturePlan** | Dependency laws, layer rules | After ProjectPlan |
| **ScaffoldPlan** | Files to create | After ArchitecturePlan |
| **TestPlan** | Test definitions | Before implementation |
| **ImplementationPlan** | Steps to implement a file | Per file |
| **RefactorPlan** | Structural changes | When refactoring |

### Result Artifacts

| Artifact | Purpose |
|----------|---------|
| **ValidationResult** | Test/lint/arch validation outcomes |
| **FailureReport** | Blocking failures needing attention |
| **ReconciliationPlan** | Steps to resolve drift |

## Hexagonal Architecture

Rice-Factor uses hexagonal architecture (ports & adapters):

```
┌─────────────────────────────────────────────┐
│              ENTRYPOINTS                    │
│         CLI  │  TUI  │  Web                 │
└─────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────┐
│                ADAPTERS                      │
│  LLM        │  Storage    │   Executors     │
│  (Claude,   │  (File,     │   (Scaffold,    │
│   OpenAI)   │   S3, GCS)  │    Diff)        │
└─────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────┐
│            DOMAIN (Pure Python)             │
│    Ports  │  Artifacts  │  Services         │
│         No external dependencies            │
└─────────────────────────────────────────────┘
```

**Key rule**: The domain layer has ZERO external dependencies. All integrations go through adapters implementing ports (protocols).

## Seven Principles

These are non-negotiable:

1. **Artifacts over prompts** - Plans are first-class data structures
2. **Plans before code** - Never write code without a plan artifact
3. **Tests before implementation** - TDD enforced at system level
4. **No LLM writes to disk** - LLM only generates JSON plans
5. **All automation is replayable** - Everything is auditable and reversible
6. **Partial failure is acceptable; silent failure is not**
7. **Human approval is mandatory at all irreversible boundaries**

## Development Phases

A Rice-Factor project progresses through phases:

```
INIT → PLANNING → SCAFFOLDED → TEST_LOCKED → IMPLEMENTING → COMPLETE
```

Each phase has:
- Prerequisites (artifacts that must exist)
- Gating (what operations are allowed)
- Exit criteria (when to move to next phase)

## Audit Trail

Every operation is logged:

```
.project/
├── artifacts/      # All artifacts (immutable after approval)
├── audit/          # Audit trail
│   ├── diffs/      # Generated diffs
│   ├── logs/       # Operation logs
│   └── overrides/  # Override records
└── staging/        # Work in progress
```

The audit trail enables:
- Full replay of any session
- Rollback to any point
- Debugging of failures
- Compliance tracking

## What's Next?

- [Basic Workflow Tutorial](../tutorials/basic-workflow.md) - Hands-on practice
- [Artifact Lifecycle](../tutorials/artifact-lifecycle.md) - Deep dive into states
- [Architecture Reference](../../reference/architecture/overview.md) - Technical details
