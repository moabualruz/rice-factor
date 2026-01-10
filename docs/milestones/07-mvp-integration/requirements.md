# Milestone 07: MVP Integration - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.2.0
> **Status**: In Progress
> **Parent**: [Project Requirements](../../project/requirements.md)

---

## 1. Milestone Objective

Integrate all components from Milestones 01-06 into a working end-to-end MVP that proves the core thesis: LLMs can act as compilers generating plan artifacts that drive safe, human-approved code generation.

**Key Integration Goals:**
- Wire real LLM providers (Claude/OpenAI) to CLI plan commands
- Connect executors to CLI commands
- Implement safety enforcement (hard-fail conditions)
- Create comprehensive integration test suite
- Validate all 7 MVP exit criteria

---

## 2. MVP Scope

### 2.1 In Scope
- Single repository
- Single language (Rust OR Go OR JVM)
- One module / bounded context
- Test-driven implementation
- One refactor operation
- CLI only
- Git-backed safety

### 2.2 Explicitly Deferred
- Multi-language repos
- Web UI
- Parallel execution
- Advanced refactor operations
- Performance optimization
- Distributed agents

---

## 3. Requirements

### 3.1 Ubiquitous Requirements

| ID | Requirement |
|----|-------------|
| M07-U-001 | CLI plan commands **shall** use real LLM providers (Claude or OpenAI), not stubs |
| M07-U-002 | Workflow **shall** enforce phase ordering via PhaseService |
| M07-U-003 | Safety violations **shall** cause immediate hard-fail with clear error message |
| M07-U-004 | All operations **shall** emit audit trail entries |
| M07-U-005 | MVP **shall** support single language selection (Rust, Go, or JVM) |
| M07-U-006 | All artifacts **shall** be validated against JSON schemas before use |
| M07-U-007 | LLM temperature **shall** be configured at ≤0.2 for determinism |
| M07-U-008 | Each CLI command **shall** check phase prerequisites before execution |

### 3.2 Event-Driven Requirements

| ID | Requirement |
|----|-------------|
| M07-E-001 | System **shall** hard-fail if tests are modified after TestPlan lock |
| M07-E-002 | System **shall** hard-fail if required artifact is missing |
| M07-E-003 | System **shall** hard-fail if LLM outputs non-JSON response |
| M07-E-004 | System **shall** hard-fail if diff touches files not in ImplementationPlan |
| M07-E-005 | System **shall** hard-fail if schema validation fails |
| M07-E-006 | System **shall** emit ValidationResult after each test run |
| M07-E-007 | System **shall** record approval/rejection in audit trail |

### 3.3 Workflow Orchestration Requirements

| ID | Requirement |
|----|-------------|
| M07-WF-001 | Init flow **shall** block until all intake files (requirements.md, constraints.md, glossary.md) are non-empty |
| M07-WF-002 | Scaffold command **shall** only execute after ProjectPlan is approved |
| M07-WF-003 | Implementation commands **shall** only execute after TestPlan is locked |
| M07-WF-004 | Plan commands **shall** read approved artifacts as context input |
| M07-WF-005 | Apply command **shall** verify diff against approved ImplementationPlan |
| M07-WF-006 | Test command **shall** run after each apply to verify correctness |
| M07-WF-007 | Refactor **shall** only execute after implementation tests pass |
| M07-WF-008 | Resume command **shall** detect current phase and suggest next action |

### 3.4 Safety Enforcement Requirements

| ID | Requirement |
|----|-------------|
| M07-S-001 | TestPlan lock **shall** use hash-based verification stored in `.project/.lock` |
| M07-S-002 | Diff application **shall** verify target files match ImplementationPlan target |
| M07-S-003 | Scaffold executor **shall** only create files specified in ScaffoldPlan |
| M07-S-004 | Refactor executor **shall** verify capabilities before execution |
| M07-S-005 | All executor operations **shall** be auditable and reversible |

---

## 4. MVP Workflow

```
rice-factor init
  ↓
rice-factor plan project → approve
  ↓
rice-factor scaffold
  ↓
rice-factor plan tests → approve → lock
  ↓
rice-factor plan impl <file> → approve
  ↓
rice-factor impl <file> → review diff
  ↓
rice-factor apply
  ↓
rice-factor test
  ↓
(repeat for each file)
  ↓
rice-factor plan refactor <goal>
  ↓
rice-factor refactor dry-run
```

---

## 5. MVP Exit Criteria

| Criterion | Description | Verification |
|-----------|-------------|--------------|
| EC-001 | New repo can be initialized via `rice-factor init` | F07-08 E2E test |
| EC-002 | Module can be scaffolded from approved plans | F07-08 E2E test |
| EC-003 | Tests are generated and locked before implementation | F07-08 E2E test |
| EC-004 | One file is implemented via plan → diff → test cycle | F07-08 E2E test |
| EC-005 | One refactor can be dry-run successfully | F07-08 E2E test |
| EC-006 | No step requires manual cleanup | F07-08 E2E test |
| EC-007 | Full audit trail exists | F07-08 audit test |

---

## 6. MVP Artifacts Required

| Artifact | MVP Status |
|----------|------------|
| ProjectPlan | ✅ Required |
| ArchitecturePlan | ❌ Deferred |
| ScaffoldPlan | ✅ Required |
| TestPlan | ✅ Required |
| ImplementationPlan | ✅ Required |
| RefactorPlan | ⚠️ Minimal |
| ValidationResult | ⚠️ Inline only |

---

## 7. MVP CLI Commands

```bash
rice-factor init
rice-factor plan project
rice-factor scaffold
rice-factor plan tests
rice-factor lock tests
rice-factor plan impl <file>
rice-factor impl <file>
rice-factor apply
rice-factor test
rice-factor plan refactor <goal>
rice-factor refactor dry-run
```

---

## 8. MVP Executors

| Executor | Purpose |
|----------|---------|
| scaffold_executor | Create empty files |
| diff_executor | Apply approved diffs |
| refactor_executor | Move/rename only |

---

## 9. Features

| Feature ID | Name | Priority | Description |
|------------|------|----------|-------------|
| F07-01 | Init Flow Integration | P0 | Wire init command with intake validation and blocking |
| F07-02 | Project Planning Integration | P0 | Replace stub LLM with real providers in plan commands |
| F07-03 | Scaffolding Integration | P0 | Wire ScaffoldExecutor to scaffold CLI command |
| F07-04 | Test Lock Integration | P0 | Implement hash-based TestPlan lock verification |
| F07-05 | Implementation Loop | P0 | Wire plan→impl→apply→test cycle |
| F07-06 | Refactoring Integration | P1 | Wire RefactorExecutor with capability checking |
| F07-07 | Safety Enforcement | P0 | Implement hard-fail conditions for safety violations |
| F07-08 | Integration Tests | P0 | Create end-to-end test suite for all exit criteria |

---

## 10. MVP Proofs

If the MVP works, we have proven:
1. LLMs can act as compilers
2. Artifacts are a viable IR
3. Human-in-the-loop scales
4. Tests can be immutable
5. Refactoring is safe
6. Context usage is controllable

---

## 11. Success Criteria

- [ ] Complete happy-path walkthrough succeeds (EC-001 through EC-007)
- [ ] All safety invariants are enforced (M07-S-001 through M07-S-005)
- [ ] Audit trail is complete for all operations
- [ ] No manual intervention required at any step
- [ ] Architecture can scale to full system

---

## 12. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Milestone 01 | Internal | Architecture, CLI skeleton |
| Milestone 02 | Internal | Artifact system, storage, approvals |
| Milestone 03 | Internal | CLI commands, phase service |
| Milestone 04 | Internal | LLM compiler, artifact builder |
| Milestone 05 | Internal | Executors (scaffold, diff, refactor) |
| Milestone 06 | Internal | Validation engine, test runner |

---

## 13. Implementation Order

1. **F07-07**: Safety Enforcement (foundation for all operations)
2. **F07-01**: Init Flow Integration (entry point)
3. **F07-02**: Project Planning Integration (LLM wiring)
4. **F07-03**: Scaffolding Integration (executor wiring)
5. **F07-04**: Test Lock Integration (TDD enforcement)
6. **F07-05**: Implementation Loop (core workflow)
7. **F07-06**: Refactoring Integration (optional workflow)
8. **F07-08**: Integration Tests (validation)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone requirements |
| 1.1.0 | 2026-01-10 | User Decision | Updated CLI command from `dev` to `rice-factor` |
| 1.2.0 | 2026-01-10 | SDD Process | Added detailed requirements (M07-*), features table, dependencies |
