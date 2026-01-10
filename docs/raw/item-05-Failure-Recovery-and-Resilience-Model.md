# ITEM 5 — **Failure, Recovery & Resilience Model**

## 5.1 Core Principle (Non-Negotiable)

> **Failure is not an exception — it is a first-class state.**

Your system must:

* expect partial failure
* record it
* stop safely
* resume deterministically

There is **no concept of “retry until it works”**.

---

## 5.2 Failure Taxonomy (Exhaustive)

All failures fall into **exactly one** category.

### 5.2.1 Human-Input Failures

* unclear requirements
* contradictory constraints
* missing glossary terms
* wrong architectural intent

**Detected by**: Artifact Builder
**Recovered by**: Human clarification
**Never auto-recovered**

---

### 5.2.2 Planning Failures (LLM-side)

* missing steps
* invalid artifact
* ambiguity
* incomplete test coverage
* refactor ripple not captured

**Detected by**:

* schema validation
* critic agents
* test failures

**Recovered by**:

* re-planning (same phase)
* never by execution

---

### 5.2.3 Execution Failures

* patch application fails
* file already exists
* rename collision
* unsupported refactor op
* filesystem constraints

**Detected by**: Executors
**Recovered by**:

* plan correction
* executor retry only after plan change

---

### 5.2.4 Verification Failures

* test failures
* architecture violations
* lint failures
* invariant violations

**Detected by**: Validators / CI
**Recovered by**:

* new ImplementationPlan
* never by patching tests

---

### 5.2.5 Drift / Entropy Failures (Long-Running)

* code diverges from intent
* architecture erodes
* refactors pile up
* artifacts no longer reflect reality

**Detected by**:

* periodic audits
* invariant checks
* refactor pressure

**Recovered by**:

* reconciliation cycle (defined below)

---

## 5.3 Failure Objects (First-Class Artifacts)

Failures are **not logs**.
They are **structured artifacts**.

### Failure Artifact Schema

```json
{
  "type": "FailureReport",
  "id": "uuid",
  "phase": "planning | execution | verification | refactor",
  "artifact_id": "uuid",
  "category": "planning | execution | verification | drift",
  "summary": "string",
  "details": ["string"],
  "detected_at": "ISO-8601",
  "blocking": true
}
```

These artifacts:

* block progression
* are reviewable
* are auditable
* are replayable

---

## 5.4 Recovery Playbooks (Explicit, Enforced)

Each failure category has **one allowed recovery path**.

---

### 5.4.1 Recovery: Planning Failure

**Trigger**

* Invalid artifact
* Critic flags ambiguity
* Missing info error

**Playbook**

1. System halts
2. FailureReport created
3. Human edits `.project/` files
4. Artifact Builder re-runs same pass
5. Old artifact archived
6. New artifact reviewed

**Forbidden**

* Skipping pass
* Manual artifact edits

---

### 5.4.2 Recovery: Execution Failure

**Trigger**

* Patch fails
* File collision
* Tool failure

**Playbook**

1. Executor stops immediately
2. Partial changes rolled back
3. FailureReport created
4. Human reviews failure
5. New plan required
6. Execution restarts from plan

**Key rule**

> **Executors never “try harder”**

---

### 5.4.3 Recovery: Verification Failure (Tests)

**Trigger**

* Tests fail
* Architecture rule fails

**Playbook**

1. ValidationResult emitted
2. FailureReport created
3. New ImplementationPlan generated
4. Only target unit re-entered
5. Tests remain locked

This enforces **true TDD**.

---

### 5.4.4 Recovery: Refactor Failure

**Trigger**

* Broken tests
* Unsupported op
* Architecture violation

**Playbook**

1. Refactor aborted
2. Diff discarded
3. FailureReport created
4. RefactorPlan revised or split
5. Dry-run repeated

No partial refactors ever persist.

---

## 5.5 Long-Running Project Resilience

This is the part most systems ignore — and fail.

---

## 5.5.1 Artifact Drift Detection

Periodic command:

```bash
dev audit drift
```

Checks:

* code ↔ artifact mismatch
* unplanned code areas
* architecture violations
* stale plans

### Drift Signals

* Code exists with no plan
* Plan exists with no code
* Tests cover behavior not documented
* Repeated refactors in same area

---

## 5.5.2 Reconciliation Cycle (Critical)

When drift exceeds threshold:

```bash
dev reconcile
```

### What happens

1. System freezes new work
2. Generates **ReconciliationPlan**
3. Human reviews intent vs reality
4. Artifacts updated to match reality
5. Architecture rules reaffirmed
6. Work resumes

This prevents entropy collapse.

---

## 5.5.3 Aging Artifacts

Artifacts have **soft expiration**.

Example:

* ProjectPlan older than N months → review prompt
* ArchitecturePlan violated → mandatory review
* TestPlan coverage drift → audit flag

Artifacts are **living contracts**, not fossils.

---

## 5.6 Partial Work & Safe Interruptions

The system assumes:

* people stop mid-flow
* machines crash
* context is lost

### Guarantees

* No executor leaves repo half-modified
* No artifact changes without approval
* No orphaned diffs

### Resume Command

```bash
dev resume
```

Reconstructs state from:

* artifacts
* audit logs
* git history

---

## 5.7 Human Override (Controlled, Logged)

Sometimes humans must break glass.

### Command

```bash
dev override --reason "…"
```

Rules:

* Reason required
* Scope limited
* CI flags override forever
* Forces reconciliation later

Overrides are **visible scars**, not hidden hacks.

---

## 5.8 Disaster Scenarios (Explicitly Covered)

| Scenario          | Outcome            |
| ----------------- | ------------------ |
| LLM hallucination | Caught at schema   |
| Bad refactor      | Tests block        |
| Rogue human edit  | CI blocks          |
| Lost context      | Artifacts restore  |
| Team turnover     | Artifacts explain  |
| Tool upgrade      | Executors isolated |

---

## 5.9 Why This Works Long-Term

This failure model ensures:

* No silent corruption
* No “we don’t know why this is here”
* No accidental regressions
* No reliance on agent memory
* No brittle automation

It turns the system into a **self-correcting loop**.

---

## 5.10 ITEM 5 CHECKPOINT

You now have:

* Explicit failure taxonomy
* Structured failure artifacts
* Deterministic recovery playbooks
* Drift detection & reconciliation
* Long-term resilience model
* Human override safety

This completes the **full system design**.

