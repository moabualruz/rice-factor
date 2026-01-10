# Milestone 07: MVP Integration - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.1.0
> **Status**: Pending

---

## 1. Milestone Objective

Integrate all components into a working MVP that proves the core thesis: LLMs can act as compilers generating plan artifacts that drive safe, human-approved code generation.

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

## 3. MVP Workflow

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

## 4. MVP Exit Criteria

| Criterion | Description |
|-----------|-------------|
| EC-001 | New repo can be initialized via `rice-factor init` |
| EC-002 | Module can be scaffolded from approved plans |
| EC-003 | Tests are generated and locked before implementation |
| EC-004 | One file is implemented via plan → diff → test cycle |
| EC-005 | One refactor can be dry-run successfully |
| EC-006 | No step requires manual cleanup |
| EC-007 | Full audit trail exists |

---

## 5. MVP Artifacts Required

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

## 6. MVP CLI Commands

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

## 7. MVP Executors

| Executor | Purpose |
|----------|---------|
| scaffold_executor | Create empty files |
| diff_executor | Apply approved diffs |
| refactor_executor | Move/rename only |

---

## 8. MVP Proofs

If the MVP works, we have proven:
1. LLMs can act as compilers
2. Artifacts are a viable IR
3. Human-in-the-loop scales
4. Tests can be immutable
5. Refactoring is safe
6. Context usage is controllable

---

## 9. Success Criteria

- [ ] Complete happy-path walkthrough succeeds
- [ ] All safety invariants are enforced
- [ ] Audit trail is complete
- [ ] No manual intervention required
- [ ] Architecture can scale to full system

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone requirements |
| 1.1.0 | 2026-01-10 | User Decision | Updated CLI command from `dev` to `rice-factor` |
