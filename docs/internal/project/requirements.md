# Rice-Factor Project Requirements

> **Document Type**: Project-Level Requirements Specification
> **Version**: 2.0.0
> **Status**: Draft

---

## 1. Executive Summary

Rice-Factor is a **language-agnostic, LLM-assisted software development system** that treats LLMs as compilers generating structured plan artifacts rather than direct code generators. The system enforces a full project lifecycle from requirements through implementation, with human approval gates at every critical boundary.

---

## 2. Problem Statement

### 2.1 Current State

Most AI-assisted development tools suffer from:
- **Chat-driven editing**: Unstructured, unpredictable outputs
- **One-shot generation**: Large context, hallucination-prone
- **Hidden prompts**: No traceability or auditability
- **Self-modifying tests**: Corrupted correctness guarantees
- **Implicit decisions**: Architecture drift and entropy

### 2.2 Desired State

A system that:
- Treats LLMs as **compilers**, not authors
- Treats code as **output**, not conversation
- Treats tests as **immutable law**
- Treats humans as **architects and approvers**, not editors

---

## 3. Core Principles (Non-Negotiable)

These principles are **hard constraints** that the system shall never violate:

1. **Artifacts over prompts** - Use structured artifacts as the single source of truth for all automation
2. **Plans before code** - Require an approved plan artifact before any code is generated
3. **Tests before implementation** - Generate and lock test plans before implementation begins
4. **No LLM writes to disk** - LLMs only generate JSON artifacts, never modify files directly
5. **All automation is replayable** - Log all automated actions such that they can be replayed deterministically
6. **Partial failure is acceptable; silent failure is not** - Fail loudly and record all failures as first-class artifacts
7. **Human approval at irreversible boundaries** - Require explicit human approval before any irreversible operation

---

## 4. System Requirements

### 4.1 Lifecycle Support

The system shall:
- Support full project lifecycle: requirements → design → scaffolding → TDD → implementation → refactoring
- Be language-agnostic for product code generation
- Use artifacts (IR) as the single source of truth
- Use dumb, deterministic tools for execution
- Enforce human review gates at all critical phases
- Minimize LLM context usage through scoped planning
- Scale across languages, architectures, and teams

### 4.2 Artifact Behavior

All artifacts shall:
- Be serializable to JSON
- Be versioned
- Be validated against JSON Schema before acceptance
- Be immutable once approved
- Be diff-friendly for human review

### 4.3 Executor Behavior

Executors shall:
- Be stateless
- Be deterministic
- Fail fast on any precondition violation
- Emit diffs rather than direct file writes
- Log every action to the audit trail

---

## 5. State-Based Behavior

### 5.1 TestPlan Lock

- While the TestPlan is locked, reject any attempt to modify test files via automation
- While the TestPlan is locked, reject any artifact that would alter test definitions
- While the TestPlan is locked, require explicit unlock command with human confirmation before test modification

### 5.2 Artifact Status

- While an artifact has status "draft", executors shall reject the artifact
- While an artifact has status "locked", reject any modification attempt
- While an artifact has status "approved", allow executor access

### 5.3 Project Initialization

- While `.project/` directory does not exist, block all commands except `rice-factor init`
- While mandatory intake files are incomplete, block all planning commands

---

## 6. Event-Based Behavior

### 6.1 LLM Output

- As soon as the LLM generates output, validate it against the expected JSON Schema
- As soon as JSON Schema validation fails, reject the artifact and emit a failure report
- As soon as the LLM returns a `missing_information` error, halt and request human clarification

### 6.2 Execution

- As soon as a diff is approved by a human, apply the diff via git
- As soon as a diff application fails, roll back and emit a failure report
- As soon as tests fail after implementation, emit a ValidationResult and trigger re-planning

### 6.3 Approval

- As soon as an artifact is approved, update `artifacts/_meta/approvals.json`
- As soon as a TestPlan is locked, set its status to "locked" and record the lock timestamp

---

## 7. Error Handling

### 7.1 Invalid LLM Behavior

- If the LLM generates non-JSON output, reject the response and emit a failure report
- If the LLM generates code instead of a plan artifact, reject the response
- If the LLM attempts to modify an artifact with status "locked", reject the request

### 7.2 Executor Violations

- If an executor attempts to write to `.project/` directory, hard fail
- If a diff touches files not declared in the ImplementationPlan, reject the diff
- If a refactor operation is unsupported for the target language, fail explicitly

### 7.3 Approval Violations

- If an artifact is not found in approvals.json, executors shall reject it
- If a human attempts to skip a mandatory approval gate, refuse to proceed

---

## 8. Implementation Loop

- While implementing a file, as soon as tests fail, generate a new ImplementationPlan for that file only
- While the TestPlan is locked, as soon as a verification failure occurs, never suggest test modifications
- While a RefactorPlan is active, as soon as tests fail after dry-run, abort the refactor
- While a RefactorPlan is approved, as soon as capability check fails, reject the operation

---

## 9. Non-Functional Requirements

### 9.1 Safety

- All operations shall be reversible via git
- Git integration shall be mandatory for all code changes
- Dry-run mode shall be available for all destructive operations

### 9.2 Performance

- LLM calls shall be minimized through scoped context
- Cached artifacts shall be reused when unchanged
- Parallel execution shall be supported per independent unit

### 9.3 Observability

- The system shall provide artifact versioning
- The system shall maintain execution logs
- The system shall preserve diff history
- The system shall track failure lineage

### 9.4 Extensibility

- The system shall allow LLM providers to be swapped without code changes
- The system shall allow languages to be added incrementally via capability registry
- The system shall allow UI to be layered without architectural changes

---

## 10. Explicit Non-Goals

The system shall NOT:
- Act as a chat-driven code editor
- Generate code without a plan artifact
- Hide prompts or LLM interactions from the audit trail
- Modify tests after TestPlan lock via automation
- Make implicit architectural decisions
- Self-correct or retry without human awareness

---

## 11. Success Criteria

The project is successful when:

1. A new repository can be initialized via `rice-factor init`
2. A module can be scaffolded from approved plans
3. Tests are generated and locked before implementation
4. One file is implemented via plan → diff → test cycle
5. One refactor can be executed via dry-run → apply
6. No step requires manual cleanup or intervention
7. All actions are fully auditable and replayable

---

## 12. Glossary

| Term | Definition |
|------|------------|
| **Artifact** | A structured JSON document that serves as intermediate representation (IR) for the development system |
| **Executor** | A stateless, deterministic tool that applies artifacts to the codebase |
| **Plan** | An artifact that describes what should be built, not how |
| **TestPlan Lock** | The state where test definitions become immutable to automation |
| **Capability Registry** | A configuration file that defines what operations each language supports |
| **Approval Gate** | A mandatory human review point before irreversible operations |
