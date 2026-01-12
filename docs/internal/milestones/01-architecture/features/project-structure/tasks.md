# Feature F01-01: Project Folder Structure - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Draft
> **Parent Feature**: [requirements.md](./requirements.md) | [design.md](./design.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T01-01-01 | Research software paradigms | Pending | P0 |
| T01-01-02 | Design folder structure | Pending | P0 |
| T01-01-03 | Get user feedback on structure | Pending | P0 |
| T01-01-04 | Create directory structure | Pending | P0 |
| T01-01-05 | Create configuration files | Pending | P0 |
| T01-01-06 | Verify structure | Pending | P1 |

---

## 2. Task Details

### T01-01-01: Research Software Paradigms

**Objective**: Research and document architectural patterns suitable for Rice-Factor.

**Research Areas**:
- [ ] Clean Architecture
  - Dependency rule (dependencies point inward)
  - Layer separation
  - Interface adapters pattern
- [ ] Hexagonal Architecture (Ports & Adapters)
  - Primary ports (driving)
  - Secondary ports (driven)
  - Adapter implementations
- [ ] Domain-Driven Design (DDD)
  - Strategic patterns (Bounded Contexts)
  - Tactical patterns (Entities, Value Objects, Aggregates)
- [ ] Event-Driven Architecture
  - Event sourcing applicability
  - Message-based communication
- [ ] Monolith vs Microservices
  - Trade-offs for CLI tools
  - Modular monolith approach

**Deliverables**:
- [ ] Research notes in `docs/research/architecture-patterns.md`
- [ ] Recommendation summary

**Acceptance Criteria**:
- [ ] All patterns researched and documented
- [ ] Pros/cons for each pattern listed
- [ ] Clear recommendation with rationale

---

### T01-01-02: Design Folder Structure

**Objective**: Create the canonical folder structure design.

**Subtasks**:
- [ ] Define top-level directories
  - `cli/` - CLI interface
  - `core/` - Business logic
  - `schemas/` - JSON Schemas
  - `tools/` - External tool configs
  - `tests/` - Test suites
  - `docs/` - Documentation
- [ ] Define `core/` internal structure
  - `domain/` - Entities, protocols
  - `application/` - Services, orchestration
  - `infrastructure/` - Adapters
- [ ] Define layer dependencies
- [ ] Document ownership rules

**Deliverables**:
- [ ] Updated design.md with full structure
- [ ] ASCII diagram of layers

**Acceptance Criteria**:
- [ ] Structure follows Clean Architecture
- [ ] All modules have clear responsibilities
- [ ] Dependency direction is correct

---

### T01-01-03: Get User Feedback on Structure

**Objective**: Validate structure with user before implementation.

**Feedback Loop**:
1. Present proposed structure
2. Explain rationale for key decisions
3. Collect feedback on:
   - Directory naming
   - Layer organization
   - Module placement
4. Iterate based on feedback

**Deliverables**:
- [ ] User approval recorded

**Acceptance Criteria**:
- [ ] User has approved the structure
- [ ] Any requested changes incorporated

---

### T01-01-04: Create Directory Structure

**Objective**: Physically create all directories and placeholder files.

**Subtasks**:
- [ ] Create `cli/` directory structure
  ```
  cli/
  ├── __init__.py
  ├── main.py
  └── commands/
      └── __init__.py
  ```
- [ ] Create `core/` directory structure
  ```
  core/
  ├── __init__.py
  ├── domain/
  │   ├── __init__.py
  │   ├── artifacts/
  │   ├── failures/
  │   └── protocols/
  ├── application/
  │   ├── __init__.py
  │   └── services/
  └── infrastructure/
      ├── __init__.py
      ├── llm/
      ├── executors/
      ├── validators/
      ├── storage/
      └── audit/
  ```
- [ ] Create `schemas/` directory
- [ ] Create `tools/registry/` directory
- [ ] Create `tests/` directory structure
- [ ] Create `docs/` directory structure (already exists)

**Deliverables**:
- [ ] All directories created
- [ ] All `__init__.py` files created
- [ ] `.gitkeep` files in empty directories

**Acceptance Criteria**:
- [ ] `tree` command shows expected structure
- [ ] All Python packages are importable

---

### T01-01-05: Create Configuration Files

**Objective**: Create root-level configuration files.

**Files to Create**:
- [ ] `pyproject.toml` - Python project configuration
  - Project metadata
  - Dependencies
  - Scripts entry point
  - Tool configurations (mypy, ruff, pytest)
- [ ] `.gitignore` - Git ignore patterns
  - Python artifacts
  - Virtual environments
  - IDE files
  - Rice-Factor runtime directories
- [ ] `README.md` - Project documentation (update existing)
- [ ] `CLAUDE.md` - AI context file (update existing)

**Deliverables**:
- [ ] All configuration files created/updated
- [ ] `pip install -e .` works

**Acceptance Criteria**:
- [ ] Project is installable
- [ ] `dev --help` runs (with placeholder)
- [ ] Type checking passes
- [ ] Linting passes

---

### T01-01-06: Verify Structure

**Objective**: Verify the structure meets all requirements.

**Verification Steps**:
- [ ] Run `pip install -e ".[dev]"`
- [ ] Run `mypy cli core` - should pass
- [ ] Run `ruff check .` - should pass
- [ ] Run `pytest` - should discover tests
- [ ] Run `dev --help` - should show help
- [ ] Verify all imports work:
  ```python
  from cli import main
  from core.domain import artifacts
  from core.application import services
  from core.infrastructure import llm
  ```

**Deliverables**:
- [ ] Verification checklist completed
- [ ] All checks pass

**Acceptance Criteria**:
- [ ] All verification steps pass
- [ ] No import errors
- [ ] No type errors
- [ ] No lint errors

---

## 3. Task Dependencies

```
T01-01-01 (Research)
    ↓
T01-01-02 (Design)
    ↓
T01-01-03 (Feedback)
    ↓
T01-01-04 (Create Dirs)
    ↓
T01-01-05 (Config Files)
    ↓
T01-01-06 (Verify)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T01-01-01 | Low | Research already done in design phase |
| T01-01-02 | Low | Structure already designed |
| T01-01-03 | Low | Quick approval loop |
| T01-01-04 | Low | Mechanical directory creation |
| T01-01-05 | Medium | Configuration requires attention |
| T01-01-06 | Low | Automated verification |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial task breakdown |
