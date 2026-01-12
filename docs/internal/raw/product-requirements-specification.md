# 1. Product Vision

## 1.1 Purpose

Build a **language-agnostic, LLM-assisted software development system** that:

* Supports **full project lifecycle**:

  * requirements → design → scaffolding → TDD → implementation → refactoring
* Uses **LLMs only for planning and code generation**, never direct mutation
* Uses **artifacts (IR)** as the single source of truth
* Uses **dumb, deterministic tools** for execution
* Enforces **human review gates**
* Minimizes **LLM context usage**
* Scales across **languages, architectures, and teams**

This system must feel closer to a **compiler + CI pipeline** than a chat assistant.

---

# 2. Core Principles (Non-Negotiable)

1. **Artifacts over prompts**
2. **Plans before code**
3. **Tests before implementation**
4. **No LLM writes directly to disk**
5. **All automation is replayable**
6. **Partial failure is acceptable; silent failure is not**
7. **Human approval is mandatory at all irreversible boundaries**

---

# 3. High-Level System Components

## 3.1 Logical Components

| Component              | Responsibility                         |
| ---------------------- | -------------------------------------- |
| Orchestrator           | Drives lifecycle phases                |
| Artifact Builder (LLM) | Compiles intent → IR                   |
| Artifact Store         | Versioned artifact persistence         |
| Executor Engine        | Applies IR via dumb tools              |
| Validation Engine      | Tests, lint, static analysis           |
| Human Review Interface | Approvals, diffs, overrides            |
| Capability Registry    | What operations each language supports |

---

# 4. Mandatory User Intake Phase (Before Anything Runs)

## 4.1 Rationale

No automation begins until **foundational ambiguity is removed**.
The system must *force clarity*, not infer it.

---

## 4.2 Forced Questionnaires (Blocking)

### 4.2.1 Product & Domain Questions

**User must answer all:**

1. What problem does this system solve?
2. Who are the users?
3. What are the core domain concepts?
4. What invariants must *never* be violated?
5. What failures are acceptable vs catastrophic?

---

### 4.2.2 Technical Constraints

1. Target languages (primary + secondary)
2. Runtime environments
3. Persistence model (SQL / NoSQL / Event / None)
4. Performance constraints
5. Security requirements
6. Compliance constraints (if any)

---

### 4.2.3 Development Constraints

1. Architecture preference (Clean / Hexagonal / DDD / Custom)
2. Test philosophy (unit only / unit+integration / property)
3. Automation tolerance (what *must* be human approved)
4. Coding standards
5. Formatting standards

---

## 4.3 Required Initial Files (Created Before Planning)

```text
/.project/
  requirements.md
  constraints.md
  glossary.md
  non_goals.md
  risk_assessment.md
```

These files are **human-written or human-approved**.

---

# 5. Artifact Taxonomy (Core IR)

Artifacts are immutable once approved.

## 5.1 Artifact Types

| Artifact           | Purpose                |
| ------------------ | ---------------------- |
| ProjectPlan        | System decomposition   |
| ArchitecturePlan   | Layering, dependencies |
| ScaffoldPlan       | Files/modules/config   |
| TestPlan           | Test definitions       |
| ImplementationPlan | Per-unit plan          |
| RefactorPlan       | Structural changes     |
| ValidationResult   | Execution feedback     |

---

# 6. Artifact Schemas (Canonical)

## 6.1 ProjectPlan

```yaml
type: ProjectPlan
version: 1
domains:
  - name: User
    responsibility: Identity and lifecycle
modules:
  - name: user-domain
    domain: User
  - name: user-api
    domain: User
dependencies:
  user-api -> user-domain
constraints:
  architecture: clean
  language: rust
```

---

## 6.2 ArchitecturePlan

```yaml
type: ArchitecturePlan
layers:
  - domain
  - application
  - infrastructure
rules:
  - domain_cannot_import_infrastructure
  - application_depends_on_domain
```

---

## 6.3 ScaffoldPlan

```yaml
type: ScaffoldPlan
files:
  - path: src/domain/user.rs
    description: User entity and invariants
    visibility: internal
  - path: src/application/create_user.rs
    description: Use case for user creation
configs:
  - path: Cargo.toml
```

---

## 6.4 TestPlan (Immutable During Automation)

```yaml
type: TestPlan
tests:
  - id: user_create_valid
    scope: unit
    target: src/domain/user.rs
    asserts:
      - email_must_be_valid
      - id_generated
```

---

## 6.5 ImplementationPlan

```yaml
type: ImplementationPlan
target: src/domain/user.rs
steps:
  - define User struct
  - validate email format
  - expose constructor
dependencies:
  - tests/user_create_valid
```

---

## 6.6 RefactorPlan

```yaml
type: RefactorPlan
goal: Isolate persistence
operations:
  - type: extract_interface
    source: src/application/user_service.*
    name: UserRepository
  - type: move_file
    from: src/infra/db/*
    to: src/infrastructure/db/
constraints:
  preserve_behavior: true
```

---

# 7. Full Development Lifecycle Workflow

## 7.1 Phase Flow Overview

```text
User Intake
   ↓
ProjectPlan
   ↓
ArchitecturePlan
   ↓
ScaffoldPlan
   ↓
TestPlan (LOCKED)
   ↓
ImplementationPlan (per unit)
   ↓
Code Diff → Human Review
   ↓
Validation Loop
```

---

## 7.2 Implementation Loop (Critical)

For **each unit**:

1. Load only:

   * target file
   * interfaces
   * relevant tests
2. LLM generates **diff**
3. Human approves
4. Apply diff
5. Run tests
6. If fail → ValidationResult → new ImplementationPlan

**LLM never sees the whole repo again.**

---

# 8. Refactoring Cycle (Distinct but Integrated)

## 8.1 Refactor Trigger Conditions

* Architecture violations
* Performance constraints
* Domain evolution
* Duplication thresholds
* Human request

---

## 8.2 Refactoring Workflow

```text
Refactor Intent
   ↓
RefactorPlan
   ↓
Capability Validation
   ↓
Dry Run (Diff)
   ↓
Human Approval
   ↓
Apply
   ↓
Full Test Suite
```

---

## 8.3 Refactor Rules

* No test changes allowed
* Behavior preservation enforced
* Partial refactors allowed
* Unsupported operations must fail explicitly

---

# 9. Executor Requirements (Dumb by Design)

## 9.1 Executor Responsibilities

* Parse artifact
* Validate schema
* Check language capability
* Apply mechanical operations
* Emit diffs

## 9.2 Executor MUST NOT

* Infer intent
* Generate code
* Modify tests
* Reorder operations

---

# 10. Capability Registry

```yaml
language: rust
operations:
  rename_symbol: true
  extract_interface: false
  move_file: true
  enforce_dependency: partial
```

Used **before execution**, never during.

---

# 11. Human Interaction Model

## 11.1 Mandatory Review Gates

| Stage        | Human Required |
| ------------ | -------------- |
| Requirements | Yes            |
| Plans        | Yes            |
| Tests        | Yes            |
| Diffs        | Yes            |
| Refactors    | Yes            |

---

# 12. Non-Functional Requirements

## 12.1 Safety

* All operations reversible
* Git integration mandatory
* Dry-run always available

## 12.2 Performance

* LLM calls minimized
* Cached artifacts reused
* Parallel execution allowed (per unit)

## 12.3 Observability

* Artifact versioning
* Execution logs
* Diff history
* Failure lineage

---

# 13. What This System Explicitly Avoids

* Chat-driven editing
* One-shot generation
* Hidden prompts
* Self-modifying tests
* Implicit architectural decisions

---

# 14. Why This Is the “Full Glory” Design

This system:

* Treats LLMs as **compilers**, not authors
* Treats code as **output**, not conversation
* Treats tests as **law**
* Treats humans as **architects, not editors**

You can safely:

* Extract an MVP
* Scale to teams
* Add languages
* Swap models
* Enforce rigor

Without redesign.

