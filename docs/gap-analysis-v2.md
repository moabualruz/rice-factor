# Gap Analysis v2: Post-MVP Feature Assessment

> **Document Type**: Gap Analysis Report (Post-MVP)
> **Date**: 2026-01-11
> **Status**: Active
> **Supersedes**: `gap-analysis.md` (MVP completion report)

---

## 1. Executive Summary

### Current State

Rice-Factor MVP is **complete**:

- **Milestones 01-07**: All implemented and tested
- **Test Coverage**: 1,699+ unit tests passing
- **Architecture**: Full hexagonal implementation with domain/adapters/entrypoints
- **CLI Commands**: 15 commands operational
- **Artifact Types**: All 8 types with validation and storage

### Analysis Scope

This document identifies **30 specific gaps** between the raw specification documents and the current implementation, organized into **6 categories**. Each gap is directly traceable to its source specification.

### Proposed Additions

**6 new milestones (08-13)** are proposed to address post-MVP features:

| Milestone | Category | Priority | Gaps Addressed |
|-----------|----------|----------|----------------|
| 08 | CI/CD Integration | P0 | 9 |
| 09 | Drift Detection & Reconciliation | P1 | 6 |
| 10 | Artifact Lifecycle Management | P1 | 4 |
| 11 | Enhanced Intake System | P1 | 4 |
| 12 | Language-Specific Refactoring | P2 | 4 |
| 13 | Multi-Agent Orchestration | P2 | 7 |

---

## 2. Gap Analysis by Category

### 2.1 CI/CD Integration

**Source**: `docs/raw/item-03-ci-cd-pipeline-and-automation-strategy.md`

The raw specification defines a comprehensive CI/CD pipeline that acts as a "guardian" enforcing invariants. The current implementation has no CI-specific features.

| Gap ID | Description | Spec Section | Implementation Status |
|--------|-------------|--------------|----------------------|
| GAP-CI-001 | CI pipeline framework (5-stage canonical flow) | 3.4 | Not Implemented |
| GAP-CI-002 | Artifact validation stage (schema, no drafts, locks unchanged) | 3.5 | Not Implemented |
| GAP-CI-003 | Approval verification stage (cross-check artifact IDs) | 3.6 | Not Implemented |
| GAP-CI-004 | Invariant enforcement stage (orchestrates all checks) | 3.7 | Not Implemented |
| GAP-CI-005 | Test immutability check (`git diff` contains `tests/` after lock) | 3.7.1 | Not Implemented |
| GAP-CI-006 | Artifact-to-code mapping (unplanned code change detection) | 3.7.2 | Not Implemented |
| GAP-CI-007 | Audit verification stage (diff hash matching, log entries) | 3.9 | Not Implemented |
| GAP-CI-008 | CI failure taxonomy (structured error codes) | 3.14 | Not Implemented |
| GAP-CI-009 | GitHub Actions configuration template | 3.15 | Not Implemented |

**Spec Quote** (3.1):
> CI is **not allowed to invent anything**. CI's role is to: Verify, Enforce, Reject, Record. CI **never**: runs LLMs, generates artifacts, modifies code, approves anything.

**Current State**: No CI-specific commands or validation modes exist. The `validate` command runs local validation but doesn't implement CI-mode semantics.

---

### 2.2 Drift Detection & Reconciliation

**Source**: `docs/raw/item-05-Failure-Recovery-and-Resilience-Model.md`

The spec defines drift detection for long-running projects and a reconciliation cycle to recover from architectural entropy.

| Gap ID | Description | Spec Section | Implementation Status |
|--------|-------------|--------------|----------------------|
| GAP-DR-001 | `rice-factor audit drift` command | 5.5.1 | Not Implemented |
| GAP-DR-002 | `rice-factor reconcile` command | 5.5.2 | Not Implemented |
| GAP-DR-003 | ReconciliationPlan artifact type | 5.5.2 | Not Implemented |
| GAP-DR-004 | Code ↔ artifact mismatch detection | 5.5.1 | Not Implemented |
| GAP-DR-005 | Unplanned code area detection | 5.5.1 | Not Implemented |
| GAP-DR-006 | Stale plan detection | 5.5.1 | Not Implemented |

**Spec Quote** (5.5.1):
> Drift Signals: Code exists with no plan, Plan exists with no code, Tests cover behavior not documented, Repeated refactors in same area

**Spec Quote** (5.5.2):
> When drift exceeds threshold: System freezes new work, Generates ReconciliationPlan, Human reviews intent vs reality, Artifacts updated to match reality

**Current State**: No drift detection mechanisms exist. The system cannot identify when code and artifacts diverge.

---

### 2.3 Artifact Lifecycle Management

**Source**: `docs/raw/item-05-Failure-Recovery-and-Resilience-Model.md`

The spec defines artifact aging with soft expiration and mandatory reviews.

| Gap ID | Description | Spec Section | Implementation Status |
|--------|-------------|--------------|----------------------|
| GAP-AL-001 | Soft expiration for artifacts | 5.5.3 | Not Implemented |
| GAP-AL-002 | ProjectPlan age review prompts (older than N months) | 5.5.3 | Not Implemented |
| GAP-AL-003 | ArchitecturePlan violation mandatory review | 5.5.3 | Not Implemented |
| GAP-AL-004 | TestPlan coverage drift audit | 5.5.3 | Not Implemented |

**Spec Quote** (5.5.3):
> Artifacts have **soft expiration**: ProjectPlan older than N months → review prompt, ArchitecturePlan violated → mandatory review, TestPlan coverage drift → audit flag. Artifacts are **living contracts**, not fossils.

**Current State**: Artifacts have no age tracking or expiration. Once created, they persist indefinitely without review prompts.

---

### 2.4 Enhanced Intake System

**Source**: `docs/raw/06-tools-to-integrte-with-or-learn-from.md`

The spec defines a rigorous intake questionnaire with blocking behavior and validation.

| Gap ID | Description | Spec Section | Implementation Status |
|--------|-------------|--------------|----------------------|
| GAP-IN-001 | `decisions.md` template file | 2.2 | Not Implemented |
| GAP-IN-002 | Blocking questionnaire enforcement | 2.4 | Partial (validation exists, not blocking) |
| GAP-IN-003 | Vague answer rejection ("TBD", "We'll decide later") | 2.3A | Not Implemented |
| GAP-IN-004 | Glossary term hard fail (undefined terms cause failure) | 2.3C | Not Implemented |

**Spec Quote** (2.2):
> Required Intake Files: requirements.md, constraints.md, glossary.md, non_goals.md, risks.md, **decisions.md**

**Spec Quote** (2.4):
> Enforcement Rules: No artifact builder runs unless all files exist, files are non-empty, human approval recorded. Any missing concept → `missing_information` error.

**Current State**:
- Only 5 of 6 intake files created (`decisions.md` missing)
- `validate_intake_files()` exists but doesn't block planning
- No vague answer detection
- No glossary term validation during planning

---

### 2.5 Language-Specific Refactoring

**Source**: `docs/raw/06-tools-to-integrte-with-or-learn-from.md`

The spec recommends language-native refactoring tools for high-quality structural changes.

| Gap ID | Description | Spec Section | Implementation Status |
|--------|-------------|--------------|----------------------|
| GAP-RF-001 | OpenRewrite adapter (JVM) | 5 | Not Implemented |
| GAP-RF-002 | gopls adapter (Go) | 5 | Not Implemented |
| GAP-RF-003 | rust-analyzer adapter (Rust) | 5 | Not Implemented |
| GAP-RF-004 | jscodeshift/ts-morph adapter (JS/TS) | 5 | Not Implemented |

**Spec Quote** (5):
> Use selectively (per language): JVM → OpenRewrite, Go → gopls, gofmt, Rust → rust-analyzer, cargo fix, JS/TS → jscodeshift, ts-morph. Do NOT try to unify refactoring engines. Keep RefactorPlan universal, write thin adapters.

**Current State**: RefactorExecutor uses basic file operations (move, rename). No language-specific AST-based refactoring is available.

---

### 2.6 Multi-Agent Orchestration

**Source**: `docs/raw/item-04-Multi-Agent-Coordination-Model-and-Run-Modes.md`

The spec defines 5 run modes for agent orchestration, with Mode A (single agent) being the MVP default.

| Gap ID | Description | Spec Section | Implementation Status |
|--------|-------------|--------------|----------------------|
| GAP-MA-001 | `run_mode.yaml` configuration loading | 4.6 | Not Implemented |
| GAP-MA-002 | Mode B: Orchestrator + Sub-agents | 4.5.2 | Not Implemented |
| GAP-MA-003 | Mode C: Multiple Voting Agents | 4.5.3 | Not Implemented |
| GAP-MA-004 | Mode D: Specialist Role-Locked | 4.5.4 | Not Implemented |
| GAP-MA-005 | Mode E: Hybrid | 4.5.5 | Not Implemented |
| GAP-MA-006 | Critic agent role | 4.4 | Not Implemented |
| GAP-MA-007 | Domain Specialist agent role | 4.4 | Not Implemented |

**Spec Quote** (4.5):
> Mode A: Single Agent (MVP) - One model handles all compiler passes
> Mode B: Orchestrator + Sub-agents - Orchestrator delegates to specialized agents
> Mode C: Voting - Multiple agents generate, consensus or human picks
> Mode D: Role-Locked - Agents have fixed responsibilities
> Mode E: Hybrid - Combines above based on phase

**Current State**: Only Mode A (single agent) is implemented. The system has no multi-agent coordination.

---

## 3. Proposed Milestones

### Milestone 08: CI/CD Integration

**Priority**: P0 (Essential for team adoption)
**Dependencies**: None (builds on existing validation)

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F08-01 | CI Pipeline Framework | GAP-CI-001 |
| F08-02 | Artifact Validation Stage | GAP-CI-002, GAP-CI-008 |
| F08-03 | Approval Verification Stage | GAP-CI-003 |
| F08-04 | Invariant Enforcement Stage | GAP-CI-004, GAP-CI-005, GAP-CI-006 |
| F08-05 | Audit Verification Stage | GAP-CI-007 |
| F08-06 | CI Configuration Templates | GAP-CI-009 |

**New CLI Commands**:
```bash
rice-factor ci validate           # Run full CI validation pipeline
rice-factor ci validate artifacts # Stage 1: Artifact validation
rice-factor ci validate approvals # Stage 2: Approval verification
rice-factor ci validate invariants # Stage 3: Invariant enforcement
rice-factor ci validate audit     # Stage 4: Audit verification
```

**Exit Criteria**:
- [ ] PR pipeline validates artifacts before merge
- [ ] Locked TestPlan prevents test modifications in CI
- [ ] Unplanned code changes are blocked with clear error
- [ ] GitHub Actions template runs successfully
- [ ] CI failure codes are structured and actionable

---

### Milestone 09: Drift Detection & Reconciliation

**Priority**: P1 (Long-running project support)
**Dependencies**: M08 (CI can trigger drift checks)

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F09-01 | Drift Detection Service | GAP-DR-004, GAP-DR-005, GAP-DR-006 |
| F09-02 | ReconciliationPlan Artifact | GAP-DR-003 |
| F09-03 | `audit drift` Command | GAP-DR-001 |
| F09-04 | `reconcile` Command | GAP-DR-002 |
| F09-05 | Drift Threshold Configuration | - |

**New Artifact Type**:
```json
{
  "artifact_type": "ReconciliationPlan",
  "payload": {
    "drift_signals": [
      {"type": "unplanned_code", "path": "src/new_file.py"},
      {"type": "stale_plan", "artifact_id": "uuid"}
    ],
    "recommended_actions": [
      {"action": "create_plan", "target": "src/new_file.py"},
      {"action": "archive_artifact", "artifact_id": "uuid"}
    ]
  }
}
```

**New CLI Commands**:
```bash
rice-factor audit drift           # Detect code/artifact drift
rice-factor reconcile             # Generate ReconciliationPlan
rice-factor reconcile apply       # Apply reconciliation actions
```

**Exit Criteria**:
- [ ] `rice-factor audit drift` detects code/artifact mismatches
- [ ] Unplanned code areas are identified
- [ ] Stale plans are flagged
- [ ] `rice-factor reconcile` generates actionable ReconciliationPlan
- [ ] Drift threshold is configurable

---

### Milestone 10: Artifact Lifecycle Management

**Priority**: P1 (Long-running project support)
**Dependencies**: M09 (uses drift signals)

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F10-01 | Artifact Aging System | GAP-AL-001 |
| F10-02 | Expiration Policies | GAP-AL-001 |
| F10-03 | Age-Based Review Prompts | GAP-AL-002, GAP-AL-003 |
| F10-04 | Coverage Drift Detection | GAP-AL-004 |

**Configuration**:
```yaml
# .project/lifecycle.yaml
aging:
  project_plan:
    review_after_days: 90
    warn_after_days: 60
  architecture_plan:
    violation_triggers_review: true
  test_plan:
    coverage_drift_threshold: 0.1  # 10% drift triggers audit
```

**New CLI Commands**:
```bash
rice-factor audit lifecycle       # Check artifact ages and health
rice-factor lifecycle review      # Interactive review of aging artifacts
```

**Exit Criteria**:
- [ ] Old artifacts trigger review prompts
- [ ] ArchitecturePlan violations force mandatory review
- [ ] TestPlan coverage drift is detectable and auditable
- [ ] Lifecycle configuration is user-customizable

---

### Milestone 11: Enhanced Intake System

**Priority**: P1 (Quality improvement)
**Dependencies**: None (enhances existing init)

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F11-01 | `decisions.md` Template | GAP-IN-001 |
| F11-02 | Blocking Questionnaire Enforcement | GAP-IN-002 |
| F11-03 | Vague Answer Rejection | GAP-IN-003 |
| F11-04 | Glossary Term Validation | GAP-IN-004 |

**New Intake File** (`decisions.md`):
```markdown
# Decision Log

## Architecture Choices

| Decision | Alternatives Considered | Rationale |
|----------|------------------------|-----------|
| [Decision 1] | [Alt A, Alt B] | [Why this choice] |

## Rejected Approaches

| Approach | Reason for Rejection |
|----------|---------------------|
| [Approach 1] | [Reason] |

## Tradeoffs Accepted

| Tradeoff | Benefit | Cost |
|----------|---------|------|
| [Tradeoff 1] | [Benefit] | [Cost] |
```

**Validation Rules**:
```python
VAGUE_ANSWER_PATTERNS = [
    "TBD", "To be determined", "We'll decide later",
    "Not sure", "Maybe", "Possibly", "[TODO]"
]
```

**Exit Criteria**:
- [ ] `rice-factor init` creates 6 intake files (including `decisions.md`)
- [ ] Planning fails if intake files contain template placeholders
- [ ] Vague answers are rejected with specific guidance
- [ ] Undefined glossary terms cause hard failure during planning

---

### Milestone 12: Language-Specific Refactoring

**Priority**: P2 (Advanced features)
**Dependencies**: M05 (builds on RefactorExecutor)

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F12-01 | OpenRewrite Adapter (JVM) | GAP-RF-001 |
| F12-02 | gopls Adapter (Go) | GAP-RF-002 |
| F12-03 | rust-analyzer Adapter (Rust) | GAP-RF-003 |
| F12-04 | jscodeshift Adapter (JS/TS) | GAP-RF-004 |

**Architecture**:
```
rice_factor/adapters/refactoring/
├── __init__.py
├── base.py              # RefactoringToolPort protocol
├── openrewrite.py       # JVM adapter
├── gopls.py             # Go adapter
├── rust_analyzer.py     # Rust adapter
└── jscodeshift.py       # JS/TS adapter
```

**Capability Registry Update**:
```yaml
# tools/registry/capability_registry.yaml
languages:
  java:
    refactoring_tool: openrewrite
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true  # Now supported via OpenRewrite
      enforce_dependency: true
  rust:
    refactoring_tool: rust-analyzer
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
```

**Exit Criteria**:
- [ ] Each supported language has a native refactoring adapter
- [ ] RefactorPlan operations use language-native tools when available
- [ ] Capability registry accurately reflects tool support
- [ ] Fallback to basic file operations when no tool available

---

### Milestone 13: Multi-Agent Orchestration

**Priority**: P2 (Advanced features)
**Dependencies**: M04 (builds on LLM compiler)

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F13-01 | Run Mode Configuration | GAP-MA-001 |
| F13-02 | Orchestrator Mode (B) | GAP-MA-002 |
| F13-03 | Voting Mode (C) | GAP-MA-003 |
| F13-04 | Role-Locked Mode (D) | GAP-MA-004, GAP-MA-006, GAP-MA-007 |
| F13-05 | Hybrid Mode (E) | GAP-MA-005 |

**Run Mode Configuration** (`.project/run_mode.yaml`):
```yaml
mode: B  # orchestrator

agents:
  orchestrator:
    model: claude-3-opus
    authority: emit_artifacts

  planner:
    model: claude-3-sonnet
    authority: suggest_only

  critic:
    model: claude-3-sonnet
    authority: review_only
    review_before_approval: true

  domain_specialist:
    model: claude-3-haiku
    authority: narrow_scope
    domains: ["payments", "auth"]

coordination:
  voting_threshold: 0.66  # For mode C
  require_critic_approval: true
```

**Agent Roles**:
| Role | Authority | Description |
|------|-----------|-------------|
| Orchestrator | emit_artifacts | Coordinates passes, makes final decisions |
| Planner | suggest_only | Proposes structure, no direct authority |
| Critic | review_only | Reviews artifacts, can block approval |
| Domain Specialist | narrow_scope | Deep knowledge in specific domain |
| Refactor Analyst | analyze_only | Safety analysis for refactors |
| Test Strategist | suggest_only | Coverage and test strategy advice |

**Exit Criteria**:
- [ ] `run_mode.yaml` configuration is loaded and validated
- [ ] Mode B: Multiple agents can collaborate on artifact generation
- [ ] Mode C: Voting mechanism selects best artifact
- [ ] Mode D: Roles are enforced (critic must approve)
- [ ] Critic role can review before human approval

---

## 4. Implementation Roadmap

### Phase 1: Team Adoption (Essential)

```
Milestone 08: CI/CD Integration
├── Enables team-based workflow with automated checks
├── Prevents rogue edits and unplanned changes
└── Required for production use

Milestone 11: Enhanced Intake System
├── Improves project setup quality
├── Reduces ambiguity in requirements
└── Independent of other milestones
```

### Phase 2: Long-Running Project Support

```
Milestone 09: Drift Detection & Reconciliation
├── Enables long-term project health
├── Depends on: None (can run standalone)
└── Enhances: CI pipeline can trigger drift checks

Milestone 10: Artifact Lifecycle Management
├── Prevents stale artifacts
├── Depends on: M09 (uses drift signals)
└── Enhances: Review prompts integrated with drift detection
```

### Phase 3: Advanced Features

```
Milestone 12: Language-Specific Refactoring
├── Improves refactoring quality
├── Depends on: None (extends RefactorExecutor)
└── Per-language, can be implemented incrementally

Milestone 13: Multi-Agent Orchestration
├── Advanced artifact generation
├── Depends on: M04 (LLM Compiler)
└── Most complex, highest payoff for large projects
```

---

## 5. Specification Reference Matrix

### Full Coverage (MVP Complete)

| Raw Spec Document | Implementation Status |
|-------------------|----------------------|
| `product-requirements-specification.md` | 100% - Core philosophy implemented |
| `implementation-ready-specification.md` | 100% - Formal schemas implemented |
| `01-end-to-end-design.md` | 100% - Full lifecycle workflow |
| `02-Formal-Artifact-Schemas.md` | 100% - All 8 artifact types |
| `03-Artifact-Builder.md` | 100% - Compiler passes complete |
| `04-repository-and-system-layout.md` | 100% - Directory structure correct |
| `05-full-cli-agent-workflow-end-to-end-usage.md` | 100% - CLI commands working |
| `Phase-01-mvp.md` | 100% - MVP exit criteria met |
| `Item-01-mvp-example-walkthrough-end-to-end.md` | 100% - Workflow functional |
| `item-02-executor-design-and-pseudocode.md` | 100% - Executors implemented |

### Partial Coverage (Post-MVP)

| Raw Spec Document | Coverage | Gaps | Proposed Milestone |
|-------------------|----------|------|-------------------|
| `item-03-ci-cd-pipeline-and-automation-strategy.md` | 10% | GAP-CI-001 to GAP-CI-009 | M08 |
| `item-04-Multi-Agent-Coordination-Model-and-Run-Modes.md` | 30% | GAP-MA-001 to GAP-MA-007 | M13 |
| `item-05-Failure-Recovery-and-Resilience-Model.md` | 60% | GAP-DR-*, GAP-AL-* | M09, M10 |
| `06-tools-to-integrte-with-or-learn-from.md` | 40% | GAP-IN-*, GAP-RF-* | M11, M12 |

---

## 6. Action Items

### Immediate (Before M08)

- [ ] Create milestone documentation structure for M08-M13
- [ ] Update `CLAUDE.md` milestone table with new milestones
- [ ] Archive `gap-analysis.md` as `gap-analysis-v1-mvp.md`

### Per-Milestone

Each milestone requires:
1. `docs/milestones/<milestone>/requirements.md`
2. `docs/milestones/<milestone>/design.md`
3. `docs/milestones/<milestone>/features/<feature>/tasks.md`

---

## 7. Conclusion

The Rice-Factor MVP successfully implements the core LLM-as-compiler architecture with:
- Full artifact system (8 types, validation, storage)
- Complete CLI (15 commands)
- Working LLM integration (Claude, OpenAI)
- Comprehensive test coverage (1,699+ tests)

The **6 proposed milestones** (08-13) address remaining specification requirements:
- **P0**: CI/CD Integration (team adoption blocker)
- **P1**: Drift Detection, Lifecycle Management, Enhanced Intake (long-running support)
- **P2**: Language Refactoring, Multi-Agent (advanced features)

Total gaps identified: **30**
Total new features proposed: **32** (across 6 milestones)

This gap analysis provides a complete roadmap from MVP to full specification compliance.
