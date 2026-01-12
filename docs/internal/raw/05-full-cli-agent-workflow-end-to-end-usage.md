# STEP 5 — **Full CLI / Agent Workflow (End-to-End Usage)**

This section defines:

* User journeys
* Agent orchestration
* CLI commands
* Review gates
* Failure loops
* Refactoring flows
* Test-driven automation

This is written as if the system already exists and is used daily.

---

## 5.1 Core Interaction Model

The system operates as a **state machine**, not a chat.

Key idea:

> **Users and agents move the project through explicit phases.**
> You cannot skip phases.
> You cannot “just generate code”.

---

## 5.2 CLI Philosophy

The CLI (`dev`) is:

* Declarative
* Phase-aware
* Idempotent
* Safe by default
* Diff-first

### Global CLI Rules

1. No command mutates code without:

   * approved artifact
   * human confirmation
2. No command calls the LLM unless:

   * it produces an artifact
3. All commands are replayable

---

## 5.3 Phase 0 — Project Initialization (Mandatory)

### Command

```bash
dev init
```

### What Happens

1. Creates `.project/`
2. Generates mandatory files:

   * requirements.md
   * constraints.md
   * glossary.md
   * non_goals.md
   * risks.md
3. Opens interactive questionnaire
4. Blocks all other commands until completed

### Example Questions (forced)

* “What problem does this system solve?”
* “What failures are unacceptable?”
* “What architectural style must be enforced?”
* “What languages are allowed?”

**No defaults. No inference.**

---

## 5.4 Phase 1 — Planning

### 5.4.1 Project Planning

```bash
dev plan project
```

* Invokes **Project Planner pass**
* Produces `ProjectPlan`
* Status: `draft`

```bash
dev approve artifacts/planning/project_plan.json
```

* Human approval required
* Status → `approved`

---

### 5.4.2 Architecture Planning

```bash
dev plan architecture
dev approve artifacts/planning/architecture_plan.json
```

Defines **dependency laws** enforced forever.

---

## 5.5 Phase 2 — Scaffolding

### Command

```bash
dev scaffold
```

### Preconditions

* ProjectPlan approved
* ArchitecturePlan approved

### Behavior

* Reads `ScaffoldPlan`
* Creates:

  * empty files
  * TODO doc comments
* No logic
* No tests
* No inference

Result: **compilable but non-functional skeleton**

---

## 5.6 Phase 3 — Test-Driven Development Lock

### 5.6.1 Test Planning

```bash
dev plan tests
```

* Invokes **Test Designer pass**
* Produces `TestPlan`
* Status: `draft`

```bash
dev approve artifacts/tests/test_plan.json
dev lock artifacts/tests/test_plan.json
```

### Lock Effect

* Automation can **never modify tests**
* Any attempt → hard failure

This is the **point of no return**.

---

## 5.7 Phase 4 — Implementation Loop (Per Unit)

This is the **core daily workflow**.

---

### 5.7.1 Plan Implementation

```bash
dev plan impl src/domain/user.rs
```

* Invokes **Implementation Planner**
* Produces:

  * steps
  * referenced tests
* No code yet

Human reviews the plan, not code.

---

### 5.7.2 Generate Implementation Diff

```bash
dev impl src/domain/user.rs
```

### Behavior

1. Loads:

   * target file
   * related interfaces
   * referenced tests only
2. LLM generates **diff**
3. Diff is saved to `audit/diffs/`
4. No code applied yet

---

### 5.7.3 Human Review

```bash
dev review
```

Shows:

* Diff
* Plan steps
* Test expectations

Human chooses:

* approve
* reject
* request re-plan

---

### 5.7.4 Apply & Validate

```bash
dev apply
dev test
```

* Applies diff
* Runs tests
* Runs linters
* Emits `ValidationResult`

---

### 5.7.5 Failure Loop (Automatic)

If tests fail:

```bash
dev diagnose
```

* Produces `ValidationResult`
* LLM plans a **new ImplementationPlan**
* Loop repeats for this unit only

---

## 5.8 Phase 5 — Refactoring Cycle (First-Class)

Refactoring uses the **same rigor** as development.

---

### 5.8.1 Refactor Planning

```bash
dev plan refactor isolate_persistence
```

* Invokes **Refactor Planner**
* Produces `RefactorPlan`
* References ArchitecturePlan + TestPlan

---

### 5.8.2 Capability Check

```bash
dev refactor check
```

* Verifies:

  * language support
  * operation availability
* Fails early if unsupported

---

### 5.8.3 Dry Run

```bash
dev refactor dry-run
```

* Produces diffs only
* No mutation

---

### 5.8.4 Apply Refactor

```bash
dev refactor apply
```

* Human approval required
* Applies operations
* Runs full test suite

---

## 5.9 Phase 6 — Continuous Validation

At any time:

```bash
dev validate
```

Runs:

* schema validation
* architecture rules
* tests
* lint

Produces **ValidationResult artifacts only**.

---

## 5.10 Failure Scenarios (Explicit)

| Scenario                  | System Response |
| ------------------------- | --------------- |
| Missing approval          | Hard fail       |
| Schema invalid            | Hard fail       |
| Test modification attempt | Hard fail       |
| Unsupported refactor      | Hard fail       |
| LLM ambiguity             | Error artifact  |

No silent recovery. Ever.

---

## 5.11 Agent Integration (OpenCode / Claude / Codex)

Agents:

* Only invoke **Artifact Builder passes**
* Never touch executors
* Never write files
* Never bypass CLI

Agents are **brains**, not hands.

---

## 5.12 User Journeys (Examples)

### New Project

```
init → plan → approve → scaffold → tests → lock → impl → test → repeat
```

### Feature Addition

```
plan impl → impl → review → test
```

### Large Refactor

```
plan refactor → check → dry-run → apply → full test
```

---

## 5.13 System Guarantees

By design, the system guarantees:

* No unplanned code
* No broken tests silently
* No LLM hallucinated edits
* No architecture drift
* Full audit trail

---

## 5.14 STEP 5 CHECKPOINT

You now have:

* Full lifecycle definition
* CLI commands
* Agent boundaries
* Refactoring rigor
* Test immutability
* Review enforcement

This is a **complete product specification**, not an MVP sketch.

---

# FINAL STATUS

✅ Step 2 — Artifact Schemas
✅ Step 3 — LLM Compiler Contracts
✅ Step 4 — Repo & System Layout
✅ Step 5 — Full Workflow

You now possess a **coherent, end-to-end system design** that can be built incrementally without re-architecture.
