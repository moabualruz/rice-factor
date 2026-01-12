# PHASE-1 MVP — **Architecturally Complete, Operationally Minimal**

## MVP Objective (Very Explicit)

The MVP must prove that:

1. An LLM can be constrained to **compile plans instead of writing code**
2. Artifacts can **drive code creation safely**
3. **Tests are immutable law**
4. A **human-in-the-loop** workflow prevents damage
5. The system works **end-to-end** for:

   * one language
   * one module
   * one refactor

Nothing else is required.

---

# 1. What the MVP WILL Support

### Supported

* Single repository
* Single language (pick **one**: Rust *or* Go *or* JVM)
* One module / bounded context
* Test-driven implementation
* One refactor operation
* CLI only
* Git-backed safety

### Not Supported (Yet)

* Multi-language repos
* UI
* Parallel execution
* Advanced refactor ops
* Performance optimization
* Distributed agents

These are **explicitly deferred**, not ignored.

---

# 2. MVP Scope by System Layer

## 2.1 Artifacts (Reduced Set)

Only **5 artifact types** are required for MVP:

| Artifact           | MVP Status     |
| ------------------ | -------------- |
| ProjectPlan        | ✅ Required     |
| ScaffoldPlan       | ✅ Required     |
| TestPlan           | ✅ Required     |
| ImplementationPlan | ✅ Required     |
| RefactorPlan       | ⚠️ Minimal     |
| ArchitecturePlan   | ❌ Deferred     |
| ValidationResult   | ⚠️ Inline only |

We keep schemas **unchanged** — just don’t generate some yet.

---

## 2.2 LLM Compiler Passes (MVP)

Only these passes are implemented:

| Pass                   | Status     |
| ---------------------- | ---------- |
| Project Planner        | ✅          |
| Scaffold Planner       | ✅          |
| Test Designer          | ✅          |
| Implementation Planner | ✅          |
| Refactor Planner       | ⚠️ Minimal |

No others.

---

# 3. MVP Repository Layout (Minimal but Compatible)

```text
repo/
├─ .project/
│  ├─ requirements.md
│  ├─ constraints.md
│  └─ glossary.md
│
├─ artifacts/
│  ├─ project_plan.json
│  ├─ scaffold_plan.json
│  ├─ test_plan.json
│  ├─ implementation/
│  │  └─ <file>.json
│  └─ refactor/
│     └─ <goal>.json
│
├─ src/
├─ tests/
│
├─ audit/
│  └─ diffs/
│
└─ dev
```

**Everything here exists in the full system already.**

---

# 4. MVP CLI Commands (Exact Set)

The MVP CLI supports **only these commands**:

```bash
dev init
dev plan project
dev scaffold
dev plan tests
dev lock tests
dev plan impl <file>
dev impl <file>
dev apply
dev test
dev plan refactor <goal>
dev refactor dry-run
```

Nothing else.

---

# 5. MVP User Journey (Happy Path)

### Step 1 — Initialize

```bash
dev init
```

User fills:

* requirements.md
* constraints.md
* glossary.md

---

### Step 2 — Plan Project

```bash
dev plan project
```

→ produces `ProjectPlan`
→ human reviews & approves

---

### Step 3 — Scaffold

```bash
dev scaffold
```

→ creates empty files with doc comments

---

### Step 4 — Test-Driven Lock

```bash
dev plan tests
dev lock tests
```

From this moment on:

> **Automation may never modify tests**

This proves the TDD core of the system.

---

### Step 5 — Implement One File

```bash
dev plan impl src/domain/user.rs
dev impl src/domain/user.rs
dev apply
dev test
```

This proves:

* small-context generation
* diff-first workflow
* human gate
* automated verification

---

### Step 6 — Refactor Once

```bash
dev plan refactor rename_user_service
dev refactor dry-run
```

Even a trivial refactor is enough to prove the loop.

---

# 6. MVP Executor Implementation (Minimal)

You only need **3 executors**:

| Executor          | Purpose              |
| ----------------- | -------------------- |
| scaffold_executor | create empty files   |
| diff_executor     | apply approved diffs |
| refactor_executor | move / rename only   |

No AST work yet.

---

# 7. MVP Safety Guarantees (Must-Have)

The MVP must **hard fail** if:

* Tests are modified after lock
* An artifact is missing
* Schema validation fails
* LLM outputs non-JSON
* A diff touches files not in plan

These failures are features, not bugs.

---

# 8. MVP LLM Constraints (Critical)

* Temperature ≤ 0.2
* No streaming
* One artifact per call
* Max context:

  * Project planner: large
  * Everything else: **tiny**

This proves your **context-efficiency thesis**.

---

# 9. What the MVP Explicitly Proves

If the MVP works, you have proven:

1. LLMs can act as **compilers**
2. Artifacts are a viable IR
3. Human-in-the-loop scales
4. Tests can be immutable
5. Refactoring is safe
6. Context usage is controllable

This is already **more advanced than existing tools**.

---

# 10. What You Can Safely Defer After MVP

After MVP success, you can layer on:

* ArchitecturePlan
* Capability registry
* Multi-language execution
* AST-level refactors
* UI
* Parallelism
* CI integration

None of these require rework.

---

# 11. MVP Exit Criteria (Objective)

You are done with Phase-1 MVP when:

* A new repo can be created
* A module can be scaffolded
* Tests are generated and locked
* One file is implemented via plan → diff → test
* One refactor can be dry-run
* No step requires manual cleanup

If all pass → **architecture validated**.
