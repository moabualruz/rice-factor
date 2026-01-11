# Milestones 08-11 Implementation Plan

> **Purpose**: Persistent, resumable plan for implementing post-MVP milestones
> **Created**: 2026-01-11
> **Status**: In Progress

---

## Executive Summary

| Milestone | Name | Features | Tasks | Priority | Status |
|-----------|------|----------|-------|----------|--------|
| M11 | Enhanced Intake | 4 | 21 | P1 | Pending |
| M08 | CI/CD Integration | 6 | 36 | P0 | Pending |
| M09 | Drift Detection | 5 | 31 | P1 | Pending |
| M10 | Artifact Lifecycle | 4 | 24 | P1 | Pending |
| **Total** | | **19** | **112** | | |

---

## Phase 1: Gap Remediation

Before implementation, update milestone docs with gaps found in raw specs.

### M08 Gaps (CI/CD Integration)

| Gap | Location to Add | Status |
|-----|-----------------|--------|
| Agent workflow rule: "Agents run locally, never interact with CI" | requirements.md Section 3.1.1 | **Complete** |
| Artifact-to-code mapping algorithm pseudocode | design.md before Section 5.3 | **Complete** |
| PR vs Main branch mode differences | Already in docs | Complete |

### M09 Gaps (Drift Detection)

| Gap | Location to Add | Status |
|-----|-----------------|--------|
| DriftSeverity levels (LOW, MEDIUM, HIGH, CRITICAL) | design.md Section 2.1 (already exists) | **Complete** |
| Blocking command list (which commands blocked during reconciliation) | design.md Section 4.2 | **Complete** |
| RefactorHotspot detection algorithm (time window, count) | design.md Section 4.3 | **Complete** |
| Undocumented behavior detection algorithm | design.md Section 2.2 (already exists) | **Complete** |

### M10 Gaps (Artifact Lifecycle)

| Gap | Location to Add | Status |
|-----|-----------------|--------|
| Default age thresholds (ProjectPlan: 3mo, ArchitecturePlan: 6mo, TestPlan: 3mo) | design.md Section 6 (already exists) | **Complete** |
| Coverage drift measurement algorithm | design.md Section 5.1.1 | **Complete** |
| Artifact extension mechanism (`rice-factor artifact extend`) | requirements.md Section 3.1.1 + design.md CLI | **Complete** |

### M11 Gaps (Enhanced Intake)

| Gap | Location to Add | Status |
|-----|-----------------|--------|
| Glossary validation timing: during planning AND artifact generation | design.md Section 6 | **Complete** |
| Pattern matching algorithm (case sensitivity, regex vs exact) | design.md Section 5 (already exists) | **Complete** |

---

## Phase 2: Implementation Order

```
┌────────────────────────────────────────────────────────────┐
│  M11 (Enhanced Intake)  │  No dependencies, quick win     │
│  Est: 3-4 days          │  4 features, 21 tasks           │
└──────────────┬─────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────┐
│  M08 (CI/CD Integration) │  P0 priority, team adoption    │
│  Est: 7-10 days          │  6 features, 36 tasks          │
└──────────────┬─────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────┐
│  M09 (Drift Detection)   │  Uses M08 concepts             │
│  Est: 6-8 days           │  5 features, 31 tasks          │
└──────────────┬─────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────┐
│  M10 (Artifact Lifecycle)│  Uses M09 drift signals        │
│  Est: 5-6 days           │  4 features, 24 tasks          │
└────────────────────────────────────────────────────────────┘
```

---

## Phase 3: Feature-by-Feature Execution

### Milestone 11: Enhanced Intake

| Order | Feature | Tasks File | Status |
|-------|---------|------------|--------|
| 1 | F11-01: Decisions.md Template | `docs/milestones/11-enhanced-intake/features/F11-01-decisions-template/tasks.md` | **Complete** |
| 2 | F11-02: Blocking Questionnaire | `docs/milestones/11-enhanced-intake/features/F11-02-blocking-questionnaire/tasks.md` | **Complete** |
| 3 | F11-03: Vague Answer Rejection | `docs/milestones/11-enhanced-intake/features/F11-03-vague-answer-rejection/tasks.md` | **Complete** |
| 4 | F11-04: Glossary Term Validation | `docs/milestones/11-enhanced-intake/features/F11-04-glossary-term-validation/tasks.md` | **Complete** |

### Milestone 08: CI/CD Integration

| Order | Feature | Tasks File | Status |
|-------|---------|------------|--------|
| 1 | F08-01: CI Pipeline Framework | `docs/milestones/08-cicd-integration/features/F08-01-ci-pipeline-framework/tasks.md` | **Complete** |
| 2 | F08-02: Artifact Validation Stage | `docs/milestones/08-cicd-integration/features/F08-02-artifact-validation-stage/tasks.md` | Pending |
| 3 | F08-03: Approval Verification Stage | `docs/milestones/08-cicd-integration/features/F08-03-approval-verification-stage/tasks.md` | Pending |
| 4 | F08-04: Invariant Enforcement Stage | `docs/milestones/08-cicd-integration/features/F08-04-invariant-enforcement-stage/tasks.md` | Pending |
| 5 | F08-05: Audit Verification Stage | `docs/milestones/08-cicd-integration/features/F08-05-audit-verification-stage/tasks.md` | Pending |
| 6 | F08-06: CI Configuration Templates | `docs/milestones/08-cicd-integration/features/F08-06-ci-configuration-templates/tasks.md` | Pending |

### Milestone 09: Drift Detection

| Order | Feature | Tasks File | Status |
|-------|---------|------------|--------|
| 1 | F09-01: Drift Detection Service | `docs/milestones/09-drift-detection/features/F09-01-drift-detection-service/tasks.md` | Pending |
| 2 | F09-02: ReconciliationPlan Artifact | `docs/milestones/09-drift-detection/features/F09-02-reconciliation-plan-artifact/tasks.md` | Pending |
| 3 | F09-03: Audit Drift Command | `docs/milestones/09-drift-detection/features/F09-03-audit-drift-command/tasks.md` | Pending |
| 4 | F09-04: Reconcile Command | `docs/milestones/09-drift-detection/features/F09-04-reconcile-command/tasks.md` | Pending |
| 5 | F09-05: Drift Threshold Config | `docs/milestones/09-drift-detection/features/F09-05-drift-threshold-config/tasks.md` | Pending |

### Milestone 10: Artifact Lifecycle

| Order | Feature | Tasks File | Status |
|-------|---------|------------|--------|
| 1 | F10-01: Artifact Aging System | `docs/milestones/10-artifact-lifecycle/features/F10-01-artifact-aging-system/tasks.md` | Pending |
| 2 | F10-02: Expiration Policies | `docs/milestones/10-artifact-lifecycle/features/F10-02-expiration-policies/tasks.md` | Pending |
| 3 | F10-03: Age-Based Review Prompts | `docs/milestones/10-artifact-lifecycle/features/F10-03-age-based-review-prompts/tasks.md` | Pending |
| 4 | F10-04: Coverage Drift Detection | `docs/milestones/10-artifact-lifecycle/features/F10-04-coverage-drift-detection/tasks.md` | Pending |

---

## Phase 4: Progress Tracking

### How to Track Progress

1. **Task Level**: Update checkboxes in each `tasks.md` file
   ```markdown
   - [x] Completed sub-task
   - [ ] Pending sub-task
   ```

2. **Feature Level**: Update Status column in this file
   - `Pending` → `In Progress` → `Complete`

3. **Milestone Level**: Update CLAUDE.md milestone table when complete

4. **Gap Analysis**: Update `docs/gap-analysis-v2.md` when gaps are closed

### Current Progress

| Phase | Item | Status |
|-------|------|--------|
| Gap Remediation | M08 docs | **Complete** |
| Gap Remediation | M09 docs | **Complete** |
| Gap Remediation | M10 docs | **Complete** |
| Gap Remediation | M11 docs | **Complete** |
| Implementation | M11 | **Complete** |
| Implementation | M08 | In Progress (1/6 features) |
| Implementation | M09 | Pending |
| Implementation | M10 | Pending |

---

## Key Files Reference

### New Domain Files to Create
```
rice_factor/domain/
├── ci/
│   ├── __init__.py
│   └── models.py              # CIFailure, CIResult, CIStageResult
├── models/
│   ├── drift.py               # DriftSignal, DriftReport
│   └── lifecycle.py           # LifecyclePolicy, PolicyResult
├── ports/
│   ├── ci_validator.py        # CIValidatorPort
│   ├── drift.py               # DriftDetectorPort
│   └── coverage_monitor.py    # CoverageMonitorPort
└── services/
    ├── intake_validator.py    # IntakeValidator
    ├── glossary_validator.py  # GlossaryValidator
    ├── drift_detector.py      # DriftDetector
    ├── reconciliation_service.py
    └── lifecycle_service.py   # LifecycleService
```

### New Adapter Files to Create
```
rice_factor/adapters/
├── ci/
│   ├── __init__.py
│   ├── artifact_validator.py
│   ├── approval_verifier.py
│   ├── invariant_enforcer.py
│   └── audit_verifier.py
├── drift/
│   └── file_scanner_adapter.py
└── lifecycle/
    └── coverage_adapter.py
```

### New CLI Commands to Create
```
rice_factor/entrypoints/cli/commands/
├── ci.py                      # rice-factor ci validate
└── (extend) audit.py          # rice-factor audit drift
```

### Schemas to Create
```
schemas/
└── reconciliation_plan.schema.json
```

---

## Resuming Work

To resume this plan in a future session:

1. Read this file to understand current progress
2. Check the "Current Progress" table above
3. Find the next pending item
4. Read the corresponding tasks.md file
5. Continue from the first unchecked task

---

## Document History

| Date | Changes |
|------|---------|
| 2026-01-11 | Initial plan created |
| 2026-01-11 | Gap remediation complete for M08, M09, M10, M11 |
| 2026-01-11 | F11-01 (decisions.md template) complete - 28 tests passing |
| 2026-01-11 | F11-02 (blocking questionnaire) complete - 17 tests passing |
| 2026-01-11 | F11-03 (vague answer rejection) complete - 22 tests passing |
| 2026-01-11 | F11-04 (glossary term validation) complete - 19 tests passing |
| 2026-01-11 | **M11 (Enhanced Intake) COMPLETE** - 4 features, 86 tests total |
| 2026-01-11 | F08-01 (CI pipeline framework) complete - 41 tests passing |
