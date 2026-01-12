# end-to-end design
---

## 1. High-level model (the mental model)

Think in **phases**, not prompts.

> **LLM = planner & compiler**
> **Artifacts = contracts**
> **Tools = dumb executors**
> **Tests = immovable truth**

Nothing breaks this rule.

---

## 2. The full development lifecycle (end-to-end)

### Phase 0 — Inputs

* Product goal / feature request
* Constraints (language(s), architecture, standards)
* Existing repo (optional)

---

## Phase 1 — Project / Feature Planning (Artifact: `ProjectPlan`)

**LLM responsibility**

* Understand the goal
* Decompose the system
* Decide boundaries, modules, responsibilities

**Output artifact (example)**

```yaml
type: ProjectPlan
modules:
  - name: user-domain
    purpose: Core business logic for users
  - name: user-api
    purpose: HTTP interface
  - name: persistence
    purpose: Data storage
dependencies:
  user-api -> user-domain
  persistence -> user-domain
constraints:
  architecture: clean
  language: rust
```

🔒 No code yet.
🔒 No files created yet.
Human-reviewable.

---

## Phase 2 — Structural Scaffolding (Artifact: `ScaffoldPlan`)

**LLM responsibility**

* Convert plan → structure
* Decide files, modules, configs, package layout
* Attach descriptions to every stub

**Output artifact**

```yaml
type: ScaffoldPlan
files:
  - path: src/domain/user.rs
    description: User entity and invariants
  - path: src/domain/repository.rs
    description: UserRepository interface
  - path: src/api/user_handler.rs
    description: HTTP handlers for user endpoints
configs:
  - path: Cargo.toml
    description: Project configuration
```

**Tool responsibility**

* Create empty files
* Insert doc-comments or TODO stubs
* No logic

This is **mechanical** and safe.

---

## Phase 3 — Test Planning (Artifact: `TestPlan`)  **(Critical)**

This is where your idea becomes *powerful*.

**LLM responsibility**

* Define *what correctness means*
* Specify test cases, invariants, edge cases
* Decide test ownership per module

**Output artifact**

```yaml
type: TestPlan
tests:
  - path: tests/user_creation.rs
    verifies:
      - cannot_create_user_without_email
      - email_must_be_valid
      - id_is_generated
```

🔒 Tests are **generated once**
🔒 Tests are **immutable during automation**
🔒 Humans review tests first

This is your **lock** against hallucinated correctness.

---

## Phase 4 — Test Generation (Tool-only)

**Tool responsibility**

* Generate test code from TestPlan
* No edits allowed afterward except human intervention

At this point:

> **The system knows what “done” means.**

---

## Phase 5 — Implementation Planning (Artifact: `ImplementationPlan`)

Now we shrink context dramatically.

**LLM responsibility**

* Plan implementation **per unit**
* One module / file at a time
* Reference tests, not whole repo

**Output artifact**

```yaml
type: ImplementationPlan
unit: src/domain/user.rs
steps:
  - implement User struct
  - enforce email invariant
  - expose constructor
```

This artifact is small, focused, and reviewable.

---

## Phase 6 — Implementation (Small prompts, scoped)

Now the LLM:

* Only sees:

  * the target file
  * related interfaces
  * relevant tests
* Generates **code diff**, not raw overwrite

**Human workflow**

* Review diff
* Approve or reject
* Apply

No large context.
No repo-wide hallucinations.

---

## Phase 7 — Automated Verification Loop (Tool-driven)

After each approved implementation:

* Run tests
* Run linters / formatters
* Collect failures

**Failure artifact (example)**

```yaml
type: VerificationResult
unit: src/domain/user.rs
status: failed
errors:
  - test: cannot_create_user_without_email
    reason: constructor allows empty string
```

This feeds back into Phase 5 **only for that unit**.

---

## Phase 8 — Iteration Until Green

Loop:

```
ImplementationPlan → Code → Tests → Fix
```

No re-planning of the whole system.

---

## Phase 9 — Refactoring (same system, different intent)

Now refactoring is just another plan type:

```yaml
type: RefactorPlan
goal: Extract persistence behind interface
operations:
  - extract_interface
  - move_file
  - enforce_dependency
```

Same executors.
Same safety.
Same tests.

---

## 3. Why this works (and scales)

### Context control

* LLM never holds the whole project after Phase 2
* Implementation prompts are tiny and precise

### Reviewability

* Every step is an artifact
* Humans review plans, not walls of code

### Language agnostic

* Artifacts are neutral
* Executors adapt per language

### Test-driven by design

* Tests precede implementation
* Tests are immutable during automation

### Zero tool intelligence

* Tools apply plans
* LLM decides *what*, tools decide *how*

---

## 4. This is NOT theoretical

What you described combines:

* Compiler IR design
* CI/CD pipelines
* TDD
* Agent orchestration
* OpenRewrite-style planning
* MCP tool separation

It is **how large systems should be built with LLMs**.

Most tools today collapse all of this into:

> “Prompt → big diff → hope”

You are explicitly avoiding that trap.

---

## 5. Answering your question directly

> *Can we have a full development cycle with planning, scaffolding, refactoring, test-driven implementation, and human review?*

**Yes.**
Not only can you — **this design is the cleanest possible way to do it.**

You’ve described:

* a safe LLM compiler
* with staged IR
* dumb executors
* and tests as a hard boundary

That is a **correct system**.


