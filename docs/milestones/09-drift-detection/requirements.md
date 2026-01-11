# Milestone 09: Drift Detection & Reconciliation - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.1.0
> **Status**: Complete
> **Tests**: 103 passing (drift detection, reconciliation, CLI)
> **Parent**: [Project Requirements](../../project/requirements.md)
> **Source**: [item-05-Failure-Recovery-and-Resilience-Model.md](../../raw/item-05-Failure-Recovery-and-Resilience-Model.md)

---

## 1. Milestone Objective

Implement drift detection and reconciliation capabilities to identify when code and artifacts diverge over time in long-running projects. This milestone addresses sections 5.5.1-5.5.2 of the specification.

### 1.1 Problem Statement

Long-running projects suffer from **entropy collapse** where:
- Code diverges from documented intent
- Artifacts no longer reflect reality
- Unplanned code areas accumulate
- Repeated refactors pile up in same areas
- Architecture erodes over time

### 1.2 Solution Overview

Provide commands and services to:
1. Detect drift between code and artifacts
2. Generate reconciliation plans
3. Freeze new work until drift is resolved
4. Update artifacts to match reality

---

## 2. Scope

### 2.1 In Scope

- Drift detection service
- ReconciliationPlan artifact type
- `rice-factor audit drift` command
- `rice-factor reconcile` command
- Drift threshold configuration
- Drift signal reporting

### 2.2 Out of Scope

- Automatic drift resolution
- Cross-repository drift detection
- Historical drift analysis
- Drift prediction/prevention

---

## 3. Requirements

### 3.1 User Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| M09-U-001 | User can detect code/artifact mismatches | P0 | 5.5.1 |
| M09-U-002 | User can identify unplanned code areas | P0 | 5.5.1 |
| M09-U-003 | User can find stale/orphaned plans | P0 | 5.5.1 |
| M09-U-004 | User can generate reconciliation plan | P0 | 5.5.2 |
| M09-U-005 | User can configure drift thresholds | P1 | - |
| M09-U-006 | User receives actionable drift signals | P0 | 5.5.1 |

### 3.2 System Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| M09-S-001 | System detects code with no plan | P0 | 5.5.1 |
| M09-S-002 | System detects plan with no code | P0 | 5.5.1 |
| M09-S-003 | System detects tests covering undocumented behavior | P1 | 5.5.1 |
| M09-S-004 | System detects repeated refactors in same area | P1 | 5.5.1 |
| M09-S-005 | System freezes new work when drift exceeds threshold | P0 | 5.5.2 |
| M09-S-006 | System generates ReconciliationPlan artifact | P0 | 5.5.2 |

### 3.3 Exit Criteria Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| M09-E-001 | `rice-factor audit drift` produces structured report | P0 | 5.5.1 |
| M09-E-002 | ReconciliationPlan captures drift resolution steps | P0 | 5.5.2 |
| M09-E-003 | Drift signals are specific and actionable | P0 | 5.5.1 |
| M09-E-004 | Threshold configuration is documented | P1 | - |

### 3.4 Drift Signals (From Specification)

The system MUST detect these drift signals:

| Signal | Description | Detection Method |
|--------|-------------|------------------|
| Orphan Code | Code exists with no plan | Compare file paths to artifact coverage |
| Orphan Plan | Plan exists with no code | Check if plan targets still exist |
| Undocumented Tests | Tests cover behavior not in specs | Analyze test coverage vs requirements |
| Refactor Hotspots | Repeated refactors in same area | Track refactor frequency by path |

---

## 4. Features in This Milestone

| Feature ID | Feature Name | Priority | Status |
|------------|--------------|----------|--------|
| F09-01 | Drift Detection Service | P0 | Pending |
| F09-02 | ReconciliationPlan Artifact | P0 | Pending |
| F09-03 | `audit drift` Command | P0 | Pending |
| F09-04 | `reconcile` Command | P0 | Pending |
| F09-05 | Drift Threshold Config | P1 | Pending |

---

## 5. Success Criteria

- [ ] `rice-factor audit drift` detects all 4 drift signal types
- [ ] ReconciliationPlan artifact is valid against schema
- [ ] Drift report includes file paths, artifact IDs, and severity
- [ ] `rice-factor reconcile` generates actionable plan
- [ ] Threshold configuration controls when reconciliation is required
- [ ] All drift detection has unit test coverage

---

## 6. Dependencies

### 6.1 Internal Dependencies

| Dependency | Milestone | Reason |
|------------|-----------|--------|
| Artifact System | 02 | Artifact storage and retrieval |
| Audit Trail | 02 | Track changes over time |
| CLI Core | 03 | Command infrastructure |

### 6.2 External Dependencies

None.

---

## 7. Acceptance Criteria

### 7.1 Drift Detection

```bash
$ rice-factor audit drift

Drift Analysis Report
=====================

Orphan Code (code with no plan):
  - src/utils/legacy_helper.py (no coverage in any ImplementationPlan)
  - src/api/deprecated_endpoint.py (no coverage in any ImplementationPlan)

Orphan Plans (plans with no code):
  - artifacts/impl-plan-user-service.json (targets non-existent src/services/user.py)

Undocumented Behavior:
  - tests/test_edge_cases.py covers behavior not in requirements.md

Refactor Hotspots:
  - src/core/parser.py (refactored 5 times in last 30 days)

Summary: 4 drift signals detected (threshold: 3)
Status: RECONCILIATION REQUIRED
```

### 7.2 Reconciliation

```bash
$ rice-factor reconcile

Generating ReconciliationPlan...

The following actions are recommended:

1. UPDATE requirements.md to document edge case behavior
2. ARCHIVE impl-plan-user-service.json (targets removed code)
3. CREATE ImplementationPlan for src/utils/legacy_helper.py
4. REVIEW src/core/parser.py for architectural issues

ReconciliationPlan saved to: artifacts/reconciliation-plan-2026-01-11.json

Human review required. Run 'rice-factor approve reconciliation' after review.
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial requirements |
