# Milestone 05: Executor Engine - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.1.0
> **Status**: Pending

---

## 1. Milestone Objective

Implement the dumb, deterministic executor engine that applies approved artifacts to the codebase. Executors are mechanical tools with no intelligence.

---

## 2. Scope

### 2.1 In Scope
- Executor base interface
- Scaffold Executor (create files)
- Diff Executor (apply patches)
- Refactor Executor (move/rename)
- Capability Registry
- Audit logging

### 2.2 Out of Scope
- Artifact generation (Milestone 04)
- Validation logic (Milestone 06)

---

## 3. Ubiquitous Requirements

| ID | Requirement |
|----|-------------|
| M05-U-001 | Executors **shall** be stateless |
| M05-U-002 | Executors **shall** be deterministic |
| M05-U-003 | Executors **shall** fail fast on precondition violations |
| M05-U-004 | Executors **shall** emit diffs rather than direct writes |
| M05-U-005 | Executors **shall** log every action to the audit trail |
| M05-U-006 | Executors **shall not** infer intent |
| M05-U-007 | Executors **shall not** call LLMs |
| M05-U-008 | Executors **shall not** modify artifacts |

---

## 4. Executor Pipeline

Every executor **shall** follow this exact sequence:
1. Load artifact
2. Validate schema
3. Verify approval & lock status
4. Capability check (per language)
5. Precondition checks
6. Generate diff
7. (If APPLY) Apply diff
8. Emit audit logs
9. Return result

---

## 5. State-Driven Requirements

| ID | Requirement |
|----|-------------|
| M05-S-001 | **While** in DRY_RUN mode, executors **shall** generate diff without applying |
| M05-S-002 | **While** tests are locked, executors **shall** reject any test file modifications |

---

## 6. Unwanted Behavior Requirements

| ID | Requirement |
|----|-------------|
| M05-I-001 | **If** artifact is draft, **then** executor **shall** reject it |
| M05-I-002 | **If** artifact is not approved, **then** executor **shall** reject it |
| M05-I-003 | **If** operation is unsupported for language, **then** executor **shall** fail explicitly |
| M05-I-004 | **If** diff touches unauthorized files, **then** executor **shall** reject the diff |

---

## 7. Features

| Feature ID | Feature Name | Priority |
|------------|--------------|----------|
| F05-01 | Executor Base Interface | P0 |
| F05-02 | Scaffold Executor | P0 |
| F05-03 | Diff Executor | P0 |
| F05-04 | Refactor Executor | P1 |
| F05-05 | Capability Registry | P0 |
| F05-06 | Audit Logging | P0 |

---

## 8. Success Criteria

- [ ] Scaffolding creates correct file structure
- [ ] Diffs apply cleanly via git
- [ ] Refactors work for supported operations
- [ ] Unsupported operations fail explicitly
- [ ] All actions are audited

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone requirements |
