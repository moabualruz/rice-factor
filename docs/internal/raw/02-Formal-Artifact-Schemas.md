# STEP 2 — **Formal Artifact Schemas (Fully Specified, Enforceable)**

This step defines the **canonical IR** of the entire system.
Everything else (prompts, executors, UI, workflows) depends on this.

**Goal of Step 2:**
You should be able to:

* Validate every artifact with a schema validator
* Reject malformed or ambiguous plans automatically
* Version artifacts safely
* Diff and audit artifacts
* Use them across languages and tools

---

## 2.1 Core Design Decisions (Before Schemas)

These are **intentional constraints**:

1. **All artifacts are declarative**
2. **No artifact contains source code**
3. **No artifact contains reasoning or prose**
4. **Artifacts describe *what*, never *how***
5. **Executors are allowed to fail**
6. **Unsupported operations are explicit**

---

## 2.2 Universal Artifact Envelope (MANDATORY)

Every artifact in the system MUST conform to this envelope.

### `artifact.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.dev/schemas/artifact.schema.json",
  "type": "object",
  "required": [
    "artifact_type",
    "artifact_version",
    "id",
    "status",
    "created_at",
    "created_by",
    "payload"
  ],
  "properties": {
    "artifact_type": {
      "type": "string",
      "enum": [
        "ProjectPlan",
        "ArchitecturePlan",
        "ScaffoldPlan",
        "TestPlan",
        "ImplementationPlan",
        "RefactorPlan",
        "ValidationResult"
      ]
    },
    "artifact_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "status": {
      "type": "string",
      "enum": ["draft", "approved", "locked"]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "created_by": {
      "type": "string",
      "enum": ["human", "llm"]
    },
    "depends_on": {
      "type": "array",
      "items": { "type": "string", "format": "uuid" }
    },
    "payload": {
      "type": "object"
    }
  },
  "additionalProperties": false
}
```

### Hard Rules

* `locked` artifacts are immutable
* Executors **must reject** `draft`
* `depends_on` must reference **approved or locked** artifacts only

---

## 2.3 ProjectPlan Schema

### Purpose

Defines **what the system is**, not how it’s built.

### `project_plan.schema.json`

```json
{
  "$id": "https://example.dev/schemas/project_plan.schema.json",
  "type": "object",
  "required": ["domains", "modules", "constraints"],
  "properties": {
    "domains": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "responsibility"],
        "properties": {
          "name": { "type": "string" },
          "responsibility": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "modules": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "domain"],
        "properties": {
          "name": { "type": "string" },
          "domain": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "constraints": {
      "type": "object",
      "required": ["architecture", "languages"],
      "properties": {
        "architecture": {
          "enum": ["clean", "hexagonal", "ddd", "custom"]
        },
        "languages": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string" }
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

---

## 2.4 ArchitecturePlan Schema

### Purpose

Defines **dependency laws** that must never be violated.

```json
{
  "$id": "https://example.dev/schemas/architecture_plan.schema.json",
  "type": "object",
  "required": ["layers", "rules"],
  "properties": {
    "layers": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" }
    },
    "rules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["rule"],
        "properties": {
          "rule": {
            "enum": [
              "domain_cannot_import_infrastructure",
              "application_depends_on_domain",
              "infrastructure_depends_on_application"
            ]
          }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

---

## 2.5 ScaffoldPlan Schema

### Purpose

Creates **structure only** — no logic.

```json
{
  "$id": "https://example.dev/schemas/scaffold_plan.schema.json",
  "type": "object",
  "required": ["files"],
  "properties": {
    "files": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["path", "description", "kind"],
        "properties": {
          "path": { "type": "string" },
          "description": { "type": "string" },
          "kind": {
            "enum": ["source", "test", "config", "doc"]
          }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

---

## 2.6 TestPlan Schema (IMMUTABLE)

### Purpose

Defines **correctness**.
Tests are **law**, not suggestions.

```json
{
  "$id": "https://example.dev/schemas/test_plan.schema.json",
  "type": "object",
  "required": ["tests"],
  "properties": {
    "tests": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "target", "assertions"],
        "properties": {
          "id": { "type": "string" },
          "target": { "type": "string" },
          "assertions": {
            "type": "array",
            "minItems": 1,
            "items": { "type": "string" }
          }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

### Enforcement Rule

* If `artifact_type == TestPlan` and `status == locked`
  → **automation cannot modify tests**

---

## 2.7 ImplementationPlan Schema

### Purpose

Keeps implementation **small, scoped, and reviewable**.

```json
{
  "$id": "https://example.dev/schemas/implementation_plan.schema.json",
  "type": "object",
  "required": ["target", "steps", "related_tests"],
  "properties": {
    "target": { "type": "string" },
    "steps": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" }
    },
    "related_tests": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "additionalProperties": false
}
```

---

## 2.8 RefactorPlan Schema

### Purpose

Structural change **without behavioral change**.

```json
{
  "$id": "https://example.dev/schemas/refactor_plan.schema.json",
  "type": "object",
  "required": ["goal", "operations"],
  "properties": {
    "goal": { "type": "string" },
    "operations": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
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
        },
        "additionalProperties": false
      }
    },
    "constraints": {
      "type": "object",
      "properties": {
        "preserve_behavior": { "type": "boolean" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

---

## 2.9 ValidationResult Schema

```json
{
  "$id": "https://example.dev/schemas/validation_result.schema.json",
  "type": "object",
  "required": ["target", "status"],
  "properties": {
    "target": { "type": "string" },
    "status": {
      "enum": ["passed", "failed"]
    },
    "errors": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "additionalProperties": false
}
```

---

## 2.10 Summary of Step 2 (Checkpoint)

At this point you now have:

* A **formal IR**
* Fully enforceable schemas
* Clear immutability rules
* Clear executor boundaries
* A system that can be validated mechanically

Nothing in later steps will contradict this.
