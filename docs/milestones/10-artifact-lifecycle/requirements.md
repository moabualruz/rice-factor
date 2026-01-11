# Milestone 10: Artifact Lifecycle Management - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.0.0
> **Status**: Planned
> **Parent**: [Project Requirements](../../project/requirements.md)
> **Source**: [item-05-Failure-Recovery-and-Resilience-Model.md](../../raw/item-05-Failure-Recovery-and-Resilience-Model.md)

---

## 1. Milestone Objective

Implement artifact lifecycle management to ensure artifacts remain living contracts rather than fossils. This milestone addresses section 5.5.3 of the specification: "Aging Artifacts."

### 1.1 Problem Statement

In long-running projects, artifacts become stale:
- ProjectPlan becomes outdated as scope evolves
- ArchitecturePlan is violated by accumulated changes
- TestPlan coverage drifts from actual behavior
- Old artifacts become misleading rather than helpful

### 1.2 Solution Overview

Treat artifacts as **living contracts** with:
1. Soft expiration dates
2. Age-based review prompts
3. Violation-triggered mandatory reviews
4. Coverage drift detection

From the spec:
> "Artifacts are **living contracts**, not fossils."

---

## 2. Scope

### 2.1 In Scope

- Artifact age tracking
- Expiration policy configuration
- Age-based review prompts
- ArchitecturePlan violation detection
- TestPlan coverage drift detection
- Review workflow integration

### 2.2 Out of Scope

- Automatic artifact updates
- AI-generated artifact refresh
- Cross-project artifact sharing
- Artifact versioning/branching

---

## 3. Requirements

### 3.1 User Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| M10-U-001 | User receives prompts for old artifacts | P0 | 5.5.3 |
| M10-U-002 | User can configure expiration policies | P1 | - |
| M10-U-003 | User is notified of ArchitecturePlan violations | P0 | 5.5.3 |
| M10-U-004 | User can see TestPlan coverage drift | P1 | 5.5.3 |
| M10-U-005 | User can extend artifact validity | P1 | - |

### 3.2 System Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| M10-S-001 | System tracks artifact creation/update dates | P0 | 5.5.3 |
| M10-S-002 | System calculates artifact age | P0 | 5.5.3 |
| M10-S-003 | System applies expiration policies | P0 | 5.5.3 |
| M10-S-004 | System detects architecture violations | P0 | 5.5.3 |
| M10-S-005 | System measures test coverage drift | P1 | 5.5.3 |
| M10-S-006 | System triggers mandatory review for violations | P0 | 5.5.3 |

### 3.3 Specification Requirements (From 5.5.3)

| Artifact Type | Trigger | Action |
|---------------|---------|--------|
| ProjectPlan | Older than N months | Review prompt |
| ArchitecturePlan | Violated by code | Mandatory review |
| TestPlan | Coverage drift | Audit flag |

---

## 4. Features in This Milestone

| Feature ID | Feature Name | Priority | Status |
|------------|--------------|----------|--------|
| F10-01 | Artifact Aging System | P0 | Pending |
| F10-02 | Expiration Policies | P1 | Pending |
| F10-03 | Age-Based Review Prompts | P0 | Pending |
| F10-04 | Coverage Drift Detection | P1 | Pending |

---

## 5. Success Criteria

- [ ] All artifacts track creation and modification timestamps
- [ ] Expiration policies are configurable per artifact type
- [ ] Old ProjectPlan triggers review prompt
- [ ] ArchitecturePlan violation forces mandatory review
- [ ] TestPlan coverage drift is measurable and auditable
- [ ] Review prompts integrate with existing approval workflow

---

## 6. Dependencies

### 6.1 Internal Dependencies

| Dependency | Milestone | Reason |
|------------|-----------|--------|
| Artifact System | 02 | Artifact metadata |
| Approval System | 02 | Review workflow |
| Validation Engine | 06 | Architecture checks |
| Drift Detection | 09 | Drift infrastructure |

### 6.2 External Dependencies

None.

---

## 7. Acceptance Criteria

### 7.1 Artifact Aging

```bash
$ rice-factor artifact age

Artifact Age Report
===================

ProjectPlan (project-plan-001):
  Created: 2025-09-15
  Age: 4 months
  Policy: Review after 3 months
  Status: REVIEW REQUIRED

ArchitecturePlan (arch-plan-001):
  Created: 2025-11-01
  Age: 2 months
  Policy: Review after 6 months
  Status: OK
  Violations: 2 detected (mandatory review)

TestPlan (test-plan-001):
  Created: 2025-10-01
  Age: 3 months
  Policy: Review after 3 months
  Coverage Drift: 15% (was 95%, now 80%)
  Status: AUDIT FLAG
```

### 7.2 Policy Configuration

```yaml
# .project/config.yaml
lifecycle:
  policies:
    ProjectPlan:
      review_after_months: 3
      warning_at_months: 2
    ArchitecturePlan:
      review_after_months: 6
      mandatory_on_violation: true
    TestPlan:
      review_after_months: 3
      coverage_drift_threshold: 10  # percent
```

### 7.3 Violation Review

```bash
$ rice-factor validate architecture

Architecture Validation
=======================

Checking ArchitecturePlan constraints...

VIOLATIONS DETECTED:

1. Layer Violation:
   - src/adapters/llm/claude.py imports from src/entrypoints/cli
   - Rule: adapters/ cannot import from entrypoints/

2. Dependency Violation:
   - src/domain/services/planner.py imports anthropic
   - Rule: domain/ has no external dependencies

ArchitecturePlan Status: MANDATORY REVIEW REQUIRED

The ArchitecturePlan must be reviewed and either:
  a) Update the plan to allow these patterns
  b) Fix the code to comply with the plan

Run 'rice-factor approve architecture --reviewed' after review.
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial requirements |
