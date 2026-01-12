# ITEM 3 — **CI/CD Integration & Automation Strategy**

## 3.1 CI Philosophy (Core Principle)

CI is **not allowed to invent anything**.

CI’s role is to:

* **Verify**
* **Enforce**
* **Reject**
* **Record**

CI **never**:

* runs LLMs
* generates artifacts
* modifies code
* approves anything

CI is the **guardian**, not a participant.

---

## 3.2 CI Responsibilities (Explicit)

CI must enforce **five invariants**:

1. All code changes are backed by approved artifacts
2. Locked artifacts (especially TestPlan) are never violated
3. Architecture rules are never broken
4. Tests always pass
5. All automation is auditable

If **any invariant fails**, CI fails.

---

## 3.3 What CI Sees as Inputs

CI consumes:

* Repository state
* Artifacts (JSON)
* Approval metadata
* Audit logs

CI **does not** consume:

* Prompts
* LLM outputs
* Planning context
* Human chat history

---

## 3.4 CI Pipeline Stages (Canonical)

### High-Level Flow

```text
Checkout
  ↓
Artifact Validation
  ↓
Approval Verification
  ↓
Invariant Enforcement
  ↓
Test Execution
  ↓
Audit Verification
```

---

## 3.5 Stage 1 — Artifact Validation

### Purpose

Ensure **plans are valid before code is trusted**.

### Actions

* Validate JSON Schema for all artifacts
* Ensure no `draft` artifacts exist
* Ensure `locked` artifacts unchanged

### Pseudocode

```pseudo
for artifact in artifacts:
  validate_schema(artifact)
  if artifact.status == "draft":
    fail("draft_artifact_present")
```

---

## 3.6 Stage 2 — Approval Verification

### Purpose

Ensure **humans approved every plan**.

### Actions

* Load `artifacts/_meta/approvals.json`
* Cross-check artifact IDs
* Reject unapproved plans

### Pseudocode

```pseudo
for artifact in artifacts:
  if artifact.id not in approvals:
    fail("artifact_not_approved")
```

---

## 3.7 Stage 3 — Invariant Enforcement

This is where your system **outperforms traditional CI**.

### 3.7.1 Test Immutability Check

If `TestPlan` is locked:

```pseudo
if git_diff_contains("tests/"):
  fail("test_modification_after_lock")
```

No exceptions.

---

### 3.7.2 Artifact-to-Code Mapping Check

Ensure code changes are **covered by plans**.

```pseudo
changed_files = git_diff_files()

allowed_files = union(
  ImplementationPlan.targets,
  RefactorPlan.affected_files
)

if any(changed_files not in allowed_files):
  fail("unplanned_code_change")
```

This single rule eliminates:

* rogue edits
* accidental refactors
* LLM hallucinations

---

### 3.7.3 Architecture Rules (If Present)

```pseudo
run_architecture_validator()
if violations:
  fail("architecture_violation")
```

No auto-fix.

---

## 3.8 Stage 4 — Test Execution

CI runs **only native tools**.

Examples:

```bash
cargo test --locked
go test ./...
mvn test
```

Failures:

* produce ValidationResult
* block merge

CI never retries or “fixes”.

---

## 3.9 Stage 5 — Audit Verification

CI ensures **everything is traceable**.

### Checks

* Every diff applied exists in `audit/diffs/`
* Every executor action has a log entry
* No orphaned code changes

### Pseudocode

```pseudo
for commit in PR:
  ensure audit log exists
  ensure diff hash matches
```

---

## 3.10 CI Modes

### 3.10.1 Pull Request Mode (Default)

* Strict enforcement
* No artifacts generated
* No plans created
* Read-only verification

### 3.10.2 Main Branch Mode

* Same as PR
* Plus optional:

  * full refactor validation
  * full test suite

---

## 3.11 Human Workflow with CI

### Human edits code manually?

CI response:
❌ Fail — unplanned change

### Human wants to change tests?

Required flow:

1. Unlock TestPlan
2. Update TestPlan
3. Re-approve
4. Regenerate tests
5. Re-lock

CI enforces this ritual.

---

## 3.12 Agent Workflow with CI

Agents:

* Run **only locally**
* Generate artifacts
* Never push code directly
* Never interact with CI

CI treats agent output as **untrusted until approved**.

---

## 3.13 Refactoring in CI

Refactors must:

* Have a RefactorPlan
* Be dry-run validated locally
* Pass full test suite in CI

CI does not care *why* — only *that* it’s planned and valid.

---

## 3.14 CI Failure Taxonomy (Explicit)

| Failure                        | Meaning               |
| ------------------------------ | --------------------- |
| `draft_artifact_present`       | Planning incomplete   |
| `artifact_not_approved`        | Human gate skipped    |
| `test_modification_after_lock` | TDD violated          |
| `unplanned_code_change`        | Rogue edit            |
| `architecture_violation`       | Structural drift      |
| `test_failure`                 | Behavioral regression |

Each failure is **actionable**, not vague.

---

## 3.15 CI Configuration Example (GitHub Actions)

```yaml
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - run: dev validate artifacts
      - run: dev validate approvals
      - run: dev validate invariants
      - run: dev test
```

Simple, strict, predictable.

---

## 3.16 Why This CI Model Is Correct

This CI model:

* Enforces intent, not just syntax
* Prevents architectural erosion
* Scales to teams
* Works asynchronously
* Doesn’t depend on LLM availability
* Makes refactors safe
* Makes audits trivial

Most CI pipelines only check *what happened*.
This one checks **why it was allowed to happen**.
