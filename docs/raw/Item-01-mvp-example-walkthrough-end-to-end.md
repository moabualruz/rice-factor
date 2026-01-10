# ITEM 1 — **Concrete Example Project (MVP Walkthrough, End-to-End)**

This section **walks the entire MVP system using a real project**, exactly as it would run.
No abstractions, no “imagine that…”.

We will use:

* **Language**: Rust (the strictest case → validates the design)
* **Scope**: One domain, one module, one refactor
* **Architecture**: Clean
* **Goal**: Create a minimal User domain with TDD

Everything here is **mechanically executable**.

---

## 1.1 Project Goal (Human Intent)

> “Build a minimal user domain where users can be created with an email.
> Email must be valid.
> IDs are generated automatically.”

No persistence, no HTTP, no UI.

---

## 1.2 Phase 0 — Initialization (Blocking)

### Command

```bash
dev init
```

### Generated files

```
.project/
├─ requirements.md
├─ constraints.md
├─ glossary.md
├─ non_goals.md
└─ risks.md
```

---

### requirements.md (example)

```md
The system manages users.

Users have:
- a unique identifier
- an email address

Users can be created only with a valid email.

Correctness means:
- invalid emails are rejected
- valid emails create users
- IDs are always present

Catastrophic failures:
- creating users with invalid emails
```

---

### constraints.md

```md
Language: Rust
Architecture: Clean
Tests: Unit tests required
No persistence
No networking
```

---

### glossary.md

```md
User:
A domain entity representing a system user.

Email:
A string containing exactly one '@' and a domain.
```

---

### non_goals.md

```md
No database
No authentication
No HTTP API
```

---

### risks.md

```md
Email validation logic may be incomplete.
```

🔒 **System refuses to continue until all files exist and are non-empty**

---

## 1.3 Phase 1 — Project Planning

### Command

```bash
dev plan project
```

### LLM Output → ProjectPlan artifact

```json
{
  "artifact_type": "ProjectPlan",
  "artifact_version": "1.0",
  "id": "uuid-1",
  "status": "draft",
  "created_by": "llm",
  "created_at": "...",
  "payload": {
    "domains": [
      { "name": "User", "responsibility": "User lifecycle and validation" }
    ],
    "modules": [
      { "name": "user-domain", "domain": "User" }
    ],
    "constraints": {
      "architecture": "clean",
      "languages": ["rust"]
    }
  }
}
```

### Human action

```bash
dev approve artifacts/project_plan.json
```

Status → `approved`

---

## 1.4 Phase 2 — Scaffolding

### Command

```bash
dev scaffold
```

### ScaffoldPlan (already approved)

```json
{
  "files": [
    {
      "path": "src/domain/user.rs",
      "description": "User entity and invariants",
      "kind": "source"
    },
    {
      "path": "tests/user_creation.rs",
      "description": "User creation tests",
      "kind": "test"
    }
  ]
}
```

### Executor result

```rust
// src/domain/user.rs
// User entity and invariants
// TODO: Implement
```

```rust
// tests/user_creation.rs
// User creation tests
// TODO: Implement
```

No logic. No assumptions.

---

## 1.5 Phase 3 — Test Planning (TDD Lock)

### Command

```bash
dev plan tests
```

### TestPlan output

```json
{
  "artifact_type": "TestPlan",
  "artifact_version": "1.0",
  "id": "uuid-2",
  "status": "draft",
  "payload": {
    "tests": [
      {
        "id": "create_user_valid_email",
        "target": "src/domain/user.rs",
        "assertions": [
          "email must contain @",
          "user id is present"
        ]
      },
      {
        "id": "create_user_invalid_email",
        "target": "src/domain/user.rs",
        "assertions": [
          "creation fails for invalid email"
        ]
      }
    ]
  }
}
```

### Human action

```bash
dev approve artifacts/test_plan.json
dev lock artifacts/test_plan.json
```

🔒 **Automation can never modify tests after this**

---

## 1.6 Phase 4 — Implementation (Single File)

### Step 1: Plan implementation

```bash
dev plan impl src/domain/user.rs
```

### ImplementationPlan

```json
{
  "artifact_type": "ImplementationPlan",
  "artifact_version": "1.0",
  "id": "uuid-3",
  "payload": {
    "target": "src/domain/user.rs",
    "steps": [
      "Define User struct",
      "Add constructor with email validation",
      "Generate id"
    ],
    "related_tests": [
      "create_user_valid_email",
      "create_user_invalid_email"
    ]
  }
}
```

Human approves.

---

### Step 2: Generate diff

```bash
dev impl src/domain/user.rs
```

LLM sees:

* user.rs
* test_plan assertions
* nothing else

### Generated diff

```diff
+ pub struct User {
+   pub id: String,
+   pub email: String,
+ }
+
+ impl User {
+   pub fn new(email: &str) -> Result<Self, String> {
+     if !email.contains("@") {
+       return Err("invalid email".into());
+     }
+     Ok(User {
+       id: uuid::Uuid::new_v4().to_string(),
+       email: email.to_string()
+     })
+   }
+ }
```

Saved to `audit/diffs/`.

---

### Step 3: Apply & test

```bash
dev apply
dev test
```

Tests pass → done.

---

## 1.7 Phase 5 — Refactor (Minimal Example)

Goal: Rename `new` → `create`

### Command

```bash
dev plan refactor rename_constructor
```

### RefactorPlan

```json
{
  "goal": "Rename constructor",
  "operations": [
    {
      "type": "rename_symbol",
      "symbol": "User::new",
      "to": "User::create"
    }
  ]
}
```

### Dry run

```bash
dev refactor dry-run
```

Produces diff only.

---

## 1.8 What This Example Proves

This single walkthrough proves:

* Intake files prevent ambiguity
* LLM generates **plans**, not code
* Tests define truth
* Context stays small
* Refactors are explicit and safe
* Nothing is magic

This is already stronger than Refact / Copilot / Cursor.
