# 2. Artifact Schemas (Formal, Enforceable)

Artifacts are **the backbone**.
They must be:

* Serializable
* Versioned
* Validated
* Diff-friendly
* Immutable once approved

We’ll define them in **JSON Schema style** (YAML-compatible).

---

## 2.1 Global Artifact Envelope (All Artifacts)

Every artifact shares a common envelope:

```json
{
  "$schema": "https://example.dev/artifact.schema.json",
  "artifact_type": "ProjectPlan",
  "artifact_version": "1.0",
  "id": "uuid",
  "created_by": "llm | human",
  "created_at": "ISO-8601",
  "status": "draft | approved | locked",
  "depends_on": [],
  "payload": {}
}
```

### Rules

* `status=locked` → immutable
* `depends_on` must reference approved artifacts only
* Executors reject `draft`

---

## 2.2 ProjectPlan Schema

```json
{
  "type": "object",
  "required": ["domains", "modules", "constraints"],
  "properties": {
    "domains": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "responsibility"],
        "properties": {
          "name": { "type": "string" },
          "responsibility": { "type": "string" }
        }
      }
    },
    "modules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "domain"],
        "properties": {
          "name": { "type": "string" },
          "domain": { "type": "string" }
        }
      }
    },
    "constraints": {
      "type": "object",
      "properties": {
        "architecture": { "enum": ["clean", "hexagonal", "ddd", "custom"] },
        "languages": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```

---

## 2.3 ScaffoldPlan Schema

```json
{
  "type": "object",
  "required": ["files"],
  "properties": {
    "files": {
      "type": "array",
      "items": {
        "required": ["path", "description", "kind"],
        "properties": {
          "path": { "type": "string" },
          "description": { "type": "string" },
          "kind": {
            "enum": ["source", "test", "config", "doc"]
          }
        }
      }
    }
  }
}
```

---

## 2.4 TestPlan Schema (Immutable)

```json
{
  "type": "object",
  "required": ["tests"],
  "properties": {
    "tests": {
      "type": "array",
      "items": {
        "required": ["id", "target", "assertions"],
        "properties": {
          "id": { "type": "string" },
          "target": { "type": "string" },
          "assertions": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      }
    }
  }
}
```

**Rule:**
If `artifact_type == TestPlan` → executor **must refuse modification**

---

## 2.5 ImplementationPlan Schema

```json
{
  "type": "object",
  "required": ["target", "steps"],
  "properties": {
    "target": { "type": "string" },
    "steps": {
      "type": "array",
      "items": { "type": "string" }
    },
    "related_tests": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

---

## 2.6 RefactorPlan Schema

```json
{
  "type": "object",
  "required": ["goal", "operations"],
  "properties": {
    "goal": { "type": "string" },
    "operations": {
      "type": "array",
      "items": {
        "required": ["type"],
        "properties": {
          "type": {
            "enum": [
              "move_file",
              "rename_symbol",
              "extract_interface",
              "enforce_dependency"
            ]
          },
          "from": { "type": "string" },
          "to": { "type": "string" },
          "symbol": { "type": "string" }
        }
      }
    },
    "constraints": {
      "type": "object",
      "properties": {
        "preserve_behavior": { "type": "boolean" }
      }
    }
  }
}
```

---

# 3. Artifact Builder (LLM Compiler) – Prompt & Contract Design

The **LLM never edits code directly**.
It performs **compiler passes**.

---

## 3.1 Artifact Builder Roles

Each invocation has **one role only**:

| Role              | Output                         |
| ----------------- | ------------------------------ |
| Planner           | ProjectPlan / ArchitecturePlan |
| Scaffolder        | ScaffoldPlan                   |
| Test Designer     | TestPlan                       |
| Implement Planner | ImplementationPlan             |
| Refactor Planner  | RefactorPlan                   |

Never mix roles.

---

## 3.2 Global Artifact Builder Contract (System Prompt)

> You are an Artifact Builder.
> You do not generate source code.
> You do not explain your reasoning.
> You emit **only valid JSON matching the provided schema**.
> If information is missing, you must fail with a `missing_information` error.

---

## 3.3 Example: TestPlan Builder Prompt

**Inputs:**

* Approved ProjectPlan
* Approved ScaffoldPlan
* requirements.md
* constraints.md

**Prompt (conceptual):**

```
Task: Generate a TestPlan.

Rules:
- Tests define correctness.
- Tests must be language-idiomatic.
- Tests must be minimal but complete.
- Tests must not rely on implementation details.
- Do not generate code.
- Output JSON only.

Schema: <TestPlan Schema>
```

---

## 3.4 Guardrails

* JSON Schema validation before acceptance
* Token budget caps per role
* No file system access
* Deterministic temperature (near zero)

---

# 4. Repository & System Layout (Concrete)

This layout supports **full traceability**.

```
repo/
├─ .project/
│  ├─ requirements.md
│  ├─ constraints.md
│  ├─ glossary.md
│  ├─ risks.md
│
├─ artifacts/
│  ├─ project_plan.json
│  ├─ architecture_plan.json
│  ├─ scaffold_plan.json
│  ├─ test_plan.json
│  ├─ impl/
│  │  ├─ user_domain.json
│  │  └─ user_api.json
│  └─ refactor/
│     └─ isolate_persistence.json
│
├─ src/
├─ tests/
├─ tools/
│  ├─ executor/
│  ├─ validator/
│  └─ capability_registry.yaml
│
├─ audit/
│  ├─ diffs/
│  ├─ executions.log
│  └─ failures.log
│
└─ cli/
```

---

## 4.1 Capability Registry

```yaml
language: rust
operations:
  move_file: true
  rename_symbol: true
  extract_interface: false
  enforce_dependency: partial
```

Executors **must consult this first**.

---

# 5. Full CLI / Agent Workflow

This is how a real user interacts.

---

## 5.1 Initialization

```bash
dev init
```

* Creates `.project/`
* Forces questionnaire completion
* Blocks further actions until approved

---

## 5.2 Planning Phase

```bash
dev plan project
dev plan architecture
```

* Generates artifacts
* Human reviews
* Locks artifacts

---

## 5.3 Scaffolding

```bash
dev scaffold
```

* Reads ScaffoldPlan
* Creates empty files with doc comments
* No logic

---

## 5.4 Test Phase (TDD Lock)

```bash
dev plan tests
dev generate tests
dev lock tests
```

Once locked:

* Any attempt to modify tests via automation fails

---

## 5.5 Implementation Loop

```bash
dev plan impl src/domain/user.rs
dev impl src/domain/user.rs
dev test
```

* LLM generates diff
* Human approves
* Executor applies
* Validator runs

---

## 5.6 Refactoring

```bash
dev plan refactor isolate_persistence
dev refactor dry-run
dev refactor apply
dev test --full
```

---

## 5.7 Failure Handling

Failures generate **ValidationResult artifacts**:

```json
{
  "target": "src/domain/user.rs",
  "failure": "email invariant violated",
  "test": "user_create_valid"
}
```

This feeds back into `ImplementationPlan`.

---

# 6. System-Wide Invariants (Hard Rules)

1. No code without a plan
2. No plan without human review
3. No test modification during automation
4. No refactor without full test pass
5. No silent executor behavior

---

# 7. Why This Design Holds Long-Term

* You can swap LLMs freely
* You can add languages incrementally
* You can add UI later
* You can enforce governance
* You can extract MVP safely

Nothing here needs to be thrown away.
