# PART 1 — EXISTING TOOLS TO INTEGRATE WITH / LEARN FROM

The guiding principle:

> **Reuse tools where the problem is already *solved deterministically***
> **Study tools where the problem is solved *conceptually***
> **Never reuse tools that hide intelligence or mix concerns**

---

## 1. Artifact Validation & Schemas

### Use outright

* **JSON Schema (Draft 2020-12)**
* **Ajv** (Node) or **jsonschema** (Python)

**Why**

* Battle-tested
* Deterministic
* CI-friendly
* No opinion leakage

You already designed schemas correctly — do not invent your own validator.

---

## 2. Diff Generation & Application

### Use outright

* **git diff / git apply**
* **libgit2** (if embedding)
* **unidiff** (Python) for parsing

**Why**

* Git already *is* the safest patch engine
* Humans understand diffs
* Rollback is trivial

> Do NOT invent a patch format.

Your system should **generate unified diffs only**.

---

## 3. Test Execution & Locking

### Use outright

* Native test runners:

  * `cargo test`
  * `go test`
  * `mvn test` / `gradle test`
* File permission locking (filesystem-level)
* Git hooks (optional)

**Why**

* Tests must be **language-native**
* Anything else breaks developer trust

### Learn from

* **Bazel** (tests as immutable inputs)
* **Nix** (immutability model)

---

## 4. Scaffolding (File/Project Creation)

### Use outright

* Plain filesystem operations
* Templates only for headers / comments

### Learn from

* **Cookiecutter**
* **Yeoman**
* **Rails generators**

But:

* **No logic**
* **No opinions**
* **No branching**

Your ScaffoldPlan already replaces generators.

---

## 5. Refactoring (Executor side)

### Use selectively (per language)

| Language | Use                          | Learn from   |
| -------- | ---------------------------- | ------------ |
| JVM      | **OpenRewrite**              | ArchUnit     |
| Go       | **gopls**, gofmt             | staticcheck  |
| Rust     | **rust-analyzer**, cargo fix | Clippy       |
| JS/TS    | **jscodeshift**, ts-morph    | ESLint rules |

**Important**
Do NOT try to unify refactoring engines.

Instead:

* Keep your **RefactorPlan** universal
* Write **thin adapters**
* Fail loudly if unsupported

---

## 6. Architecture Rule Enforcement

### Use outright

* **ArchUnit** (JVM)
* **depguard** (Go)
* **Rust module visibility + clippy**

### Learn from

* **NDepend**
* **Structure101**

But:

* Enforcement only
* No auto-fixing at MVP+

---

## 7. LLM-Orchestrated Planning

### Learn from (do not copy)

* **OpenRewrite recipes** (structure, not syntax)
* **Terraform plan/apply**
* **Bazel analysis vs execution phases**
* **LLVM IR passes**

These reinforce:

> *Planning is separate from execution*

---

## 8. CLI & Orchestration

### Use outright

* **Click** (Python) or **Cobra** (Go)
* **Rich** / **Textual** (optional UX)

### Learn from

* **Git**
* **Terraform**
* **kubectl**

Especially:

* dry-run semantics
* explicit apply
* immutable plans

---

## 9. Audit & Lineage

### Use outright

* Append-only logs
* Git history
* JSON event logs

### Learn from

* **Airflow DAGs**
* **MLFlow**
* **DVC**

Artifacts are your “models”.

---

## 10. What NOT to Integrate

Avoid these categories entirely:

* IDE AI plugins (Copilot, Refact, Cursor)
* Chat-based refactoring tools
* Tools that mutate code directly
* Tools that hide prompts or logic

They violate your core architecture.

---

# PART 2 — USER QUESTIONNAIRE & REQUIRED FILES (MANDATORY INTAKE)

This is the **missing keystone**.
The system must *force clarity* before intelligence is applied.

---

## 2.1 Principles of the Questionnaire

1. **Blocking** — cannot proceed without answers
2. **Explicit** — no defaults inferred
3. **Written to files** — not ephemeral
4. **Human-authored** — LLM may assist, not decide
5. **Reviewed once, referenced forever**

---

## 2.2 Required Intake Files (Authoritative)

Created by `dev init` and locked before planning:

```text
.project/
├─ requirements.md        # What must exist
├─ constraints.md         # What must never change
├─ glossary.md            # Meaning of terms
├─ non_goals.md           # Explicit exclusions
├─ risks.md               # Known dangers
└─ decisions.md           # Future-proofing
```

---

## 2.3 Detailed Questionnaire (Forced)

### A. Problem Definition → `requirements.md`

Mandatory questions:

1. What user problem does this system solve?
2. Who is the primary user?
3. What workflows must be supported?
4. What data is critical?
5. What correctness means for this system?
6. What failure modes are acceptable?
7. What failure modes are catastrophic?

**Rejection criteria**

* Vague answers
* “TBD”
* “We’ll decide later”

---

### B. Technical Constraints → `constraints.md`

Mandatory questions:

1. Target language(s)
2. Runtime environment(s)
3. Deployment target(s)
4. Performance constraints (latency, throughput)
5. Security requirements
6. Compliance constraints
7. Dependency restrictions
8. Architecture preference

**This file is LAW.**

---

### C. Domain Language → `glossary.md`

Mandatory:

* Every domain term
* Every acronym
* Every invariant concept

Example:

```md
## User
An authenticated account with a unique email.

## Active User
A user who has confirmed email and not been disabled.
```

If a term appears later without being here → **hard fail**.

---

### D. Explicit Non-Goals → `non_goals.md`

This prevents scope creep.

Mandatory:

1. Features explicitly excluded
2. Technologies explicitly excluded
3. Performance targets explicitly not pursued

This file is referenced by the LLM to **avoid hallucinating features**.

---

### E. Risk Register → `risks.md`

Mandatory:

1. Technical risks
2. Product risks
3. Scaling risks
4. Security risks

This informs **TestPlan** and **RefactorPlan**.

---

### F. Decision Log → `decisions.md`

Records:

* Architecture choices
* Rejected alternatives
* Tradeoffs

This prevents “why did we do this?” loops.

---

## 2.4 Enforcement Rules

* No artifact builder runs unless:

  * all files exist
  * files are non-empty
  * human approval recorded
* Any missing concept → `missing_information` error
* LLM cannot add or modify these files

---

## 2.5 Why This Matters

This intake system:

* Eliminates ambiguous prompts
* Prevents LLM overreach
* Makes planning deterministic
* Preserves human intent
* Scales to teams
* Creates institutional memory

Most AI tools skip this — that’s why they fail at scale.

---

## FINAL SUMMARY

### You should:

* **Reuse**: Git, JSON Schema, native test runners, OpenRewrite (JVM), gopls, rust-analyzer
* **Learn from**: Terraform, Bazel, LLVM, OpenRewrite, Nix
* **Avoid**: AI tools that mutate code directly

### You now have:

* A complete tool integration map
* A mandatory, enforceable user questionnaire
* A clean intake boundary between humans and LLMs
* A system that can grow without collapsing

