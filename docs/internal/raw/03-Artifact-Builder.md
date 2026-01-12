# STEP 3 — **Artifact Builder (LLM Compiler) Prompt & Contract Design**

This step defines **how the LLM is allowed to think and act** in the system.

If Step 2 defined the **IR**,
Step 3 defines the **compiler passes** that generate that IR.

---

## 3.1 Core Philosophy

The LLM is **not an assistant**.
The LLM is **not a coder**.
The LLM is a **pure compiler stage**.

### The LLM:

* Transforms **inputs → artifacts**
* Emits **structured IR only**
* Has **no authority** to mutate code
* Has **no memory across passes**

---

## 3.2 Hard Contract (Non-Negotiable)

Every Artifact Builder invocation must obey **all** of the following:

1. Output **valid JSON only**
2. Output **exactly one artifact**
3. Output **no explanations**
4. Output **no code**
5. Output **no reasoning**
6. Conform **exactly** to the schema provided
7. Fail explicitly if information is missing

---

## 3.3 Global System Prompt (Canonical)

This is the **base system prompt** for *all* artifact builders.

> **SYSTEM PROMPT — ARTIFACT BUILDER**
>
> You are an Artifact Builder.
>
> You are a compiler stage in a deterministic development system.
>
> Rules:
>
> * You do not generate source code.
> * You do not explain decisions.
> * You do not include reasoning or commentary.
> * You output valid JSON only.
> * You generate exactly one artifact per invocation.
> * You must conform exactly to the provided JSON Schema.
> * If required information is missing or ambiguous, you must fail with:
>
> ```json
> { "error": "missing_information", "details": "<description>" }
> ```
>
> Any deviation from these rules is a failure.

This prompt **never changes**.

---

## 3.4 Compiler Passes (Explicit Roles)

Each artifact type corresponds to a **distinct compiler pass**.

| Pass Name              | Artifact Output    |
| ---------------------- | ------------------ |
| Project Planner        | ProjectPlan        |
| Architecture Planner   | ArchitecturePlan   |
| Scaffold Planner       | ScaffoldPlan       |
| Test Designer          | TestPlan           |
| Implementation Planner | ImplementationPlan |
| Refactor Planner       | RefactorPlan       |

Each pass has:

* **Allowed inputs**
* **Forbidden inputs**
* **Strict scope**

---

## 3.5 Project Planner Pass

### Purpose

Translate **human requirements → system decomposition**

### Inputs (Required)

* `.project/requirements.md`
* `.project/constraints.md`
* `.project/glossary.md`

### Forbidden Inputs

* Source code
* Tests
* Existing artifacts (except envelope metadata)

### Output

* `ProjectPlan`

### Failure Conditions

* Undefined domain terms
* Conflicting constraints
* Missing architecture preference

---

## 3.6 Architecture Planner Pass

### Purpose

Define **dependency laws**

### Inputs

* Approved `ProjectPlan`
* `.project/constraints.md`

### Output

* `ArchitecturePlan`

### Rules

* Rules must be enforceable mechanically
* No vague constraints

---

## 3.7 Scaffold Planner Pass

### Purpose

Define **structure only**

### Inputs

* Approved `ProjectPlan`
* Approved `ArchitecturePlan`

### Output

* `ScaffoldPlan`

### Rules

* No logic
* Every file must have a description
* Paths must be language-idiomatic

---

## 3.8 Test Designer Pass (Critical)

### Purpose

Define **correctness contract**

### Inputs

* Approved `ProjectPlan`
* Approved `ArchitecturePlan`
* Approved `ScaffoldPlan`
* `.project/requirements.md`

### Output

* `TestPlan`

### Rules (Hard)

* Tests define behavior, not implementation
* Tests must be minimal but complete
* No mocking of internal state
* No duplication across tests

### Once Approved

* `TestPlan` becomes **locked**
* Automation can never modify it

---

## 3.9 Implementation Planner Pass

### Purpose

Create **small, reviewable units of work**

### Inputs

* Approved `TestPlan`
* Approved `ScaffoldPlan`
* Target file path

### Output

* `ImplementationPlan`

### Rules

* Exactly one target file
* Steps must be ordered
* Must reference relevant tests only

---

## 3.10 Refactor Planner Pass

### Purpose

Plan **structural change without behavior change**

### Inputs

* Approved `ArchitecturePlan`
* Approved `TestPlan`
* Current repo layout

### Output

* `RefactorPlan`

### Rules

* Tests must remain valid
* Operations must be explicit
* Partial refactors allowed

---

## 3.11 Explicit Failure Handling

### Missing Information Example

```json
{
  "error": "missing_information",
  "details": "Domain 'User' referenced but not defined in glossary.md"
}
```

### Invalid Request Example

```json
{
  "error": "invalid_request",
  "details": "ScaffoldPlanner cannot accept source code as input"
}
```

Executors and orchestrators **must not recover automatically** from these failures.

---

## 3.12 Determinism Controls

To make output stable:

* Temperature: **0–0.2**
* Top-p: **≤ 0.3**
* No streaming
* No function calling (artifacts ARE the function)

---

## 3.13 Why This Works

This design ensures:

* The LLM behaves like a **compiler**
* Artifacts are **predictable**
* Context usage is **bounded**
* Humans review **plans, not hallucinations**
* Tools remain **dumb and safe**

---

## 3.14 STEP 3 CHECKPOINT

At this point, you now have:

* A complete **LLM contract**
* Clear compiler passes
* Strict input/output boundaries
* Explicit failure semantics

This locks down **LLM behavior forever**.

