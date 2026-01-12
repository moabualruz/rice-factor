# Milestone 05: Executor Engine - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.2.0
> **Status**: Pending

---

## 1. Milestone Objective

Implement the dumb, deterministic executor engine that applies approved artifacts to the codebase. Executors are mechanical tools with no intelligence.

---

## 2. Scope

### 2.1 In Scope
- Executor base interface (ExecutorPort protocol)
- Scaffold Executor (create files from ScaffoldPlan)
- Diff Executor (apply patches from approved diffs)
- Refactor Executor (move_file, rename_symbol operations)
- Capability Registry (language operation support)
- Audit logging (execution trail)

### 2.2 Out of Scope
- Artifact generation (Milestone 04 - LLM Compiler)
- Test Runner (Milestone 06 - Validation Engine)
- Architecture Validator (post-MVP)
- Lint Runner (Milestone 06 - Validation Engine)

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
| M05-U-009 | Executors **shall** accept artifacts as input |
| M05-U-010 | Executors **shall** fail loudly on any error |

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

### 4.1 ExecutionResult Schema

All executors **shall** return results conforming to this schema:

```json
{
  "status": "success | failure",
  "diffs": ["audit/diffs/<id>.diff"],
  "errors": ["string"],
  "logs": ["string"]
}
```

### 4.2 Capability Registry Schema

The capability registry **shall** conform to this YAML schema:

```yaml
languages:
  <language>:
    operations:
      move_file: true | false
      rename_symbol: true | false
      extract_interface: true | false
      enforce_dependency: true | false | partial
```

**Default Capability Registry:**

```yaml
languages:
  python:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: false
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
      enforce_dependency: false
  javascript:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: false
  typescript:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: false
```

---

## 5. State-Driven Requirements

| ID | Requirement |
|----|-------------|
| M05-S-001 | **While** in DRY_RUN mode, executors **shall** generate diff without applying |
| M05-S-002 | **While** tests are locked, executors **shall** reject any test file modifications |
| M05-S-003 | **While** artifact is DRAFT, executors **shall** reject execution |

---

## 6. Unwanted Behavior Requirements

| ID | Requirement |
|----|-------------|
| M05-I-001 | **If** artifact is draft, **then** executor **shall** reject it |
| M05-I-002 | **If** artifact is not approved, **then** executor **shall** reject it |
| M05-I-003 | **If** operation is unsupported for language, **then** executor **shall** fail explicitly |
| M05-I-004 | **If** diff touches unauthorized files, **then** executor **shall** reject the diff |
| M05-I-005 | **If** path escapes repository root, **then** executor **shall** reject operation |

---

## 7. Domain-Specific Requirements

### 7.1 Scaffold Executor Requirements

| ID | Requirement |
|----|-------------|
| M05-SC-001 | Scaffold Executor **shall** accept ScaffoldPlan artifacts only |
| M05-SC-002 | Scaffold Executor **shall** create empty files with TODO comments |
| M05-SC-003 | Scaffold Executor **shall** skip files that already exist |
| M05-SC-004 | Scaffold Executor **shall** create parent directories as needed |
| M05-SC-005 | **If** file already exists, **then** Scaffold Executor **shall** skip with warning |

### 7.2 Diff Executor Requirements

| ID | Requirement |
|----|-------------|
| M05-DI-001 | Diff Executor **shall** accept approved diff files only |
| M05-DI-002 | Diff Executor **shall** use git apply to apply patches |
| M05-DI-003 | Diff Executor **shall** verify diff touches only declared files |
| M05-DI-004 | Diff Executor **shall not** generate diffs (only apply them) |
| M05-DI-005 | **If** patch fails to apply, **then** Diff Executor **shall** fail with details |

### 7.3 Refactor Executor Requirements

| ID | Requirement |
|----|-------------|
| M05-RF-001 | Refactor Executor **shall** accept RefactorPlan artifacts only |
| M05-RF-002 | Refactor Executor **shall** support move_file operation |
| M05-RF-003 | Refactor Executor **shall** support rename_symbol operation (simple textual) |
| M05-RF-004 | Refactor Executor **shall** check capability registry before execution |
| M05-RF-005 | Refactor Executor **shall** generate diff from operations |
| M05-RF-006 | **If** source file missing, **then** Refactor Executor **shall** fail |
| M05-RF-007 | **If** destination exists, **then** Refactor Executor **shall** fail |

### 7.4 Capability Registry Requirements

| ID | Requirement |
|----|-------------|
| M05-CR-001 | Capability Registry **shall** load from bundled default configuration |
| M05-CR-002 | Capability Registry **shall** allow override from project `tools/registry/capability_registry.yaml` |
| M05-CR-003 | Capability Registry **shall** provide `check_capability(operation, language)` function |
| M05-CR-004 | **If** capability check fails, **then** system **shall** fail before execution |

### 7.5 Audit Logging Requirements

| ID | Requirement |
|----|-------------|
| M05-AU-001 | Audit Logger **shall** write JSON log entries to `audit/executions.log` |
| M05-AU-002 | Audit Logger **shall** record timestamp, executor name, artifact path, status |
| M05-AU-003 | Audit Logger **shall** record diff location for successful executions |
| M05-AU-004 | Audit Logger **shall** be append-only |
| M05-AU-005 | **If** no audit log written, **then** execution **shall** be considered invalid |

---

## 8. Features

| Feature ID | Feature Name | Priority |
|------------|--------------|----------|
| F05-01 | Executor Base Interface | P0 |
| F05-02 | Scaffold Executor | P0 |
| F05-03 | Diff Executor | P0 |
| F05-04 | Refactor Executor | P1 |
| F05-05 | Capability Registry | P0 |
| F05-06 | Audit Logging | P0 |

---

## 9. Success Criteria

- [ ] ExecutorPort protocol defined with DRY_RUN and APPLY modes
- [ ] Scaffolding creates correct file structure with TODO comments
- [ ] Diffs apply cleanly via git apply
- [ ] Refactors work for move_file and rename_symbol operations
- [ ] Unsupported operations fail explicitly with capability check
- [ ] All actions are audited in JSON format
- [ ] Capability registry loads from bundled + project override
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

---

## 10. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Milestone 02 - Artifact System | Required | Artifact storage, validation, approval system |
| Milestone 04 - LLM Compiler | Required | Generates artifacts that executors consume |
| Git | External | Used by Diff Executor for git apply |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone requirements |
| 1.1.0 | 2026-01-10 | SDD Process | Added version bump |
| 1.2.0 | 2026-01-10 | SDD Process | Added ExecutionResult schema, Capability Registry schema, domain-specific requirements, dependencies |
