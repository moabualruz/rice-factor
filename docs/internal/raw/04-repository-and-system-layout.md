# STEP 4 — **Repository & System Layout (Concrete, Enforceable)**

This step defines **where everything lives**, **who owns what**, and **how the system enforces boundaries**.

If Step 2 defined *what exists* and Step 3 defined *how it’s produced*,
**Step 4 defines how it survives contact with reality** (humans, tools, CI, scale).

---

## 4.1 Core Design Goals of the Layout

The repository layout must:

1. Make **artifacts first-class**
2. Make **automation auditable**
3. Prevent **LLM shortcuts**
4. Support **partial execution**
5. Scale to **multiple languages**
6. Support **future UI without refactor**

---

## 4.2 Top-Level Repository Structure (Canonical)

```text
repo/
├─ .project/                 # Human-owned, immutable by automation
│  ├─ requirements.md
│  ├─ constraints.md
│  ├─ glossary.md
│  ├─ non_goals.md
│  ├─ risks.md
│  └─ decisions.md
│
├─ artifacts/                # System-owned IR (versioned)
│  ├─ _meta/                 # Artifact registry & lineage
│  │  ├─ index.json
│  │  └─ approvals.json
│  │
│  ├─ planning/
│  │  ├─ project_plan.json
│  │  ├─ architecture_plan.json
│  │  └─ scaffold_plan.json
│  │
│  ├─ tests/
│  │  └─ test_plan.json
│  │
│  ├─ implementation/
│  │  ├─ src.domain.user.json
│  │  └─ src.api.user.json
│  │
│  └─ refactor/
│     └─ isolate_persistence.json
│
├─ src/                      # Product source code
├─ tests/                    # Generated + human-written tests
│
├─ tools/                    # Dumb executors & validators
│  ├─ executor/
│  │  ├─ apply_scaffold/
│  │  ├─ apply_refactor/
│  │  ├─ apply_diff/
│  │  └─ capability_check/
│  │
│  ├─ validator/
│  │  ├─ schema_validate/
│  │  ├─ test_runner/
│  │  ├─ lint_runner/
│  │  └─ arch_rules/
│  │
│  └─ registry/
│     └─ capability_registry.yaml
│
├─ audit/                    # Everything automation did
│  ├─ diffs/
│  ├─ executions.log
│  ├─ validation.log
│  └─ failures.log
│
├─ cli/                      # Orchestrator entrypoint
│  └─ dev
│
├─ .gitignore
└─ README.md
```

---

## 4.3 Ownership Rules (CRITICAL)

| Path         | Owner  | Automation Allowed    |
| ------------ | ------ | --------------------- |
| `.project/`  | Human  | ❌ Never               |
| `artifacts/` | System | ⚠️ Only via builder   |
| `src/`       | Mixed  | ✅ Via approved plans  |
| `tests/`     | Mixed  | ❌ After TestPlan lock |
| `tools/`     | Human  | ❌                     |
| `audit/`     | System | ✅ Append-only         |

Automation **must refuse** to operate if these rules are violated.

---

## 4.4 Artifact Registry (`artifacts/_meta/`)

Artifacts must be **discoverable, traceable, and ordered**.

### `index.json`

```json
{
  "artifacts": [
    {
      "id": "uuid",
      "type": "ProjectPlan",
      "path": "planning/project_plan.json",
      "status": "approved"
    }
  ]
}
```

### `approvals.json`

```json
{
  "approvals": [
    {
      "artifact_id": "uuid",
      "approved_by": "human",
      "approved_at": "ISO-8601"
    }
  ]
}
```

Executors **must check approvals.json before acting**.

---

## 4.5 Artifact Naming Conventions

Artifacts must map cleanly to code.

| Artifact Type      | Naming            |
| ------------------ | ----------------- |
| ImplementationPlan | `src.<path>.json` |
| RefactorPlan       | `<goal>.json`     |
| TestPlan           | `test_plan.json`  |

This enables:

* predictable discovery
* per-file planning
* incremental workflows

---

## 4.6 Capability Registry (System Truth)

### `tools/registry/capability_registry.yaml`

```yaml
languages:
  rust:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: partial
  go:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
  jvm:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
```

### Enforcement Rule

Executors **must reject unsupported operations** before execution.

---

## 4.7 Tool Design Rules (Executor Layer)

### Executors MUST:

* Be stateless
* Accept artifacts as input
* Emit diffs, not raw writes
* Log every action
* Fail loudly

### Executors MUST NOT:

* Read `.project/`
* Invoke LLMs
* Guess intent
* Modify artifacts

---

## 4.8 Validation Layer Responsibilities

Validators:

* Schema validation
* Architecture rule enforcement
* Test execution
* Linting / formatting
* Dependency checks

Validation failures generate **ValidationResult artifacts** only.

---

## 4.9 Audit & Traceability Guarantees

Every automated action produces:

1. A diff file (`audit/diffs/`)
2. A log entry (`executions.log`)
3. A validation record (`validation.log`)

Nothing is silent.
Nothing is ephemeral.

---

## 4.10 Multi-Language Support (Future-Proofing)

The layout allows:

```text
src/
├─ rust/
├─ go/
└─ jvm/
```

Artifacts target **paths**, not languages.
Executors resolve language via capability registry.

---

## 4.11 Why This Layout Is Correct

This layout:

* Makes artifacts **more important than code**
* Prevents LLM overreach
* Supports CI/CD natively
* Allows UI layering later
* Makes refactoring safe
* Makes failure debuggable

This is the layout you keep for **years**, not months.

---

## 4.12 STEP 4 CHECKPOINT

You now have:

* A concrete repo layout
* Clear ownership boundaries
* Auditability guarantees
* Executor safety rules
* Language extensibility

Nothing here is accidental.


