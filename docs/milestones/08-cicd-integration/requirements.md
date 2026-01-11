# Milestone 08: CI/CD Integration - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.0.0
> **Status**: Planned
> **Priority**: P0 (Essential for team adoption)
> **Parent**: [Project Requirements](../../project/requirements.md)
> **Source Spec**: [item-03-ci-cd-pipeline-and-automation-strategy.md](../../raw/item-03-ci-cd-pipeline-and-automation-strategy.md)

---

## 1. Milestone Objective

Implement CI/CD integration that enforces Rice-Factor's invariants in automated pipelines, including:

- CI pipeline framework with 5 canonical stages
- Artifact validation before code is trusted
- Approval verification for all plans
- Invariant enforcement (test immutability, artifact-to-code mapping)
- Audit verification for traceability
- GitHub Actions configuration templates

**Core Principle** (from spec 3.1):
> CI is **not allowed to invent anything**. CI's role is to: Verify, Enforce, Reject, Record. CI **never**: runs LLMs, generates artifacts, modifies code, approves anything. CI is the **guardian**, not a participant.

---

## 2. Scope

### 2.1 In Scope

- CI pipeline framework with 5 stages (checkout → artifact validation → approval verification → invariant enforcement → audit verification)
- `rice-factor ci validate` command with subcommands for each stage
- Test immutability check (prevent test modifications after TestPlan lock)
- Artifact-to-code mapping check (detect unplanned code changes)
- CI failure taxonomy with structured error codes
- GitHub Actions workflow template
- CI mode for existing validation commands

### 2.2 Out of Scope

- GitLab CI, CircleCI, Jenkins templates (post-MVP, can be added later)
- Parallel execution of CI stages (sequential is sufficient for MVP)
- CI-triggered LLM operations (explicitly forbidden by spec)
- Auto-fixing of any violations (CI reports only)
- Web UI for CI results (CLI output only)

---

## 3. Requirements

### 3.1 CI Philosophy Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M08-U-001 | CI shall never run LLMs or generate artifacts | P0 |
| M08-U-002 | CI shall never modify code or approve anything | P0 |
| M08-U-003 | CI shall only verify, enforce, reject, and record | P0 |
| M08-U-004 | CI shall treat all agent output as untrusted until approved | P0 |

### 3.2 Pipeline Stage Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M08-S-001 | While CI is running, the system shall execute stages in order: checkout → artifact validation → approval verification → invariant enforcement → test execution → audit verification | P0 |
| M08-S-002 | While any stage fails, CI shall halt and report the failure with a structured error code | P0 |
| M08-S-003 | While CI completes successfully, the system shall produce a validation report | P1 |

### 3.3 Artifact Validation Stage Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M08-E-001 | As soon as artifact validation runs, the system shall validate JSON Schema for all artifacts | P0 |
| M08-E-002 | As soon as a draft artifact is detected, CI shall fail with `draft_artifact_present` | P0 |
| M08-E-003 | As soon as a locked artifact has changed, CI shall fail with `locked_artifact_modified` | P0 |

### 3.4 Approval Verification Stage Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M08-E-004 | As soon as approval verification runs, the system shall load `artifacts/_meta/approvals.json` | P0 |
| M08-E-005 | As soon as an unapproved artifact is detected, CI shall fail with `artifact_not_approved` | P0 |
| M08-E-006 | As soon as approval cross-check completes, the system shall verify all artifact IDs match | P0 |

### 3.5 Invariant Enforcement Stage Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M08-I-001 | If TestPlan is locked AND git diff contains changes to `tests/`, then CI shall fail with `test_modification_after_lock` | P0 |
| M08-I-002 | If code changes exist that are not covered by ImplementationPlan or RefactorPlan targets, then CI shall fail with `unplanned_code_change` | P0 |
| M08-I-003 | If architecture rules are defined AND violations exist, then CI shall fail with `architecture_violation` | P1 |

### 3.6 Audit Verification Stage Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M08-E-007 | As soon as audit verification runs, the system shall verify every applied diff exists in `audit/diffs/` | P0 |
| M08-E-008 | As soon as an orphaned code change is detected (no audit entry), CI shall fail with `orphaned_code_change` | P0 |
| M08-E-009 | As soon as diff hash mismatch is detected, CI shall fail with `audit_integrity_violation` | P1 |

### 3.7 CI Failure Taxonomy Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M08-U-005 | CI shall use structured failure codes from the canonical taxonomy | P0 |
| M08-U-006 | Each CI failure shall be actionable with clear remediation guidance | P1 |

**Canonical Failure Taxonomy** (from spec 3.14):

| Failure Code | Meaning | Remediation |
|--------------|---------|-------------|
| `draft_artifact_present` | Planning incomplete | Approve or remove draft artifacts |
| `artifact_not_approved` | Human gate skipped | Run `rice-factor approve <artifact>` |
| `locked_artifact_modified` | Immutability violated | Revert changes to locked artifact |
| `test_modification_after_lock` | TDD violated | Unlock TestPlan, update, re-lock |
| `unplanned_code_change` | Rogue edit | Create plan for changed files |
| `architecture_violation` | Structural drift | Fix imports or update ArchitecturePlan |
| `orphaned_code_change` | Missing audit trail | Apply changes via rice-factor workflow |
| `audit_integrity_violation` | Tampered audit log | Investigate and restore audit integrity |
| `test_failure` | Behavioral regression | Fix implementation or update tests |

### 3.8 CLI Command Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| M08-U-007 | The system shall provide `rice-factor ci validate` as the main CI command | P0 |
| M08-U-008 | The system shall provide `rice-factor ci validate artifacts` for Stage 1 | P0 |
| M08-U-009 | The system shall provide `rice-factor ci validate approvals` for Stage 2 | P0 |
| M08-U-010 | The system shall provide `rice-factor ci validate invariants` for Stage 3 | P0 |
| M08-U-011 | The system shall provide `rice-factor ci validate audit` for Stage 4 | P0 |
| M08-U-012 | All CI commands shall exit with non-zero code on failure | P0 |
| M08-U-013 | All CI commands shall produce machine-readable JSON output with `--json` flag | P1 |

---

## 4. Features in This Milestone

| Feature ID | Feature Name | Priority | Status | Gaps Addressed |
|------------|--------------|----------|--------|----------------|
| F08-01 | CI Pipeline Framework | P0 | Pending | GAP-CI-001 |
| F08-02 | Artifact Validation Stage | P0 | Pending | GAP-CI-002, GAP-CI-008 |
| F08-03 | Approval Verification Stage | P0 | Pending | GAP-CI-003 |
| F08-04 | Invariant Enforcement Stage | P0 | Pending | GAP-CI-004, GAP-CI-005, GAP-CI-006 |
| F08-05 | Audit Verification Stage | P0 | Pending | GAP-CI-007 |
| F08-06 | CI Configuration Templates | P1 | Pending | GAP-CI-009 |

---

## 5. Success Criteria

- [ ] `rice-factor ci validate` runs all stages in order
- [ ] Draft artifacts cause CI failure with `draft_artifact_present`
- [ ] Unapproved artifacts cause CI failure with `artifact_not_approved`
- [ ] Test modifications after lock cause CI failure with `test_modification_after_lock`
- [ ] Unplanned code changes cause CI failure with `unplanned_code_change`
- [ ] Missing audit entries cause CI failure with `orphaned_code_change`
- [ ] GitHub Actions template validates a sample repository
- [ ] All failure codes are documented and actionable
- [ ] CI commands exit with appropriate codes (0 = success, non-zero = failure)
- [ ] `--json` flag produces machine-readable output

---

## 6. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Milestone 02 | Internal | Artifact system for validation |
| Milestone 05 | Internal | Executor audit logging |
| Milestone 06 | Internal | Test runner for test execution stage |
| Git | External | For diff detection and hash verification |
| GitHub Actions | External | For workflow templates |

---

## 7. CI Modes

### 7.1 Pull Request Mode (Default)

- Strict enforcement of all invariants
- No artifacts generated
- No plans created
- Read-only verification
- Blocks merge on any failure

### 7.2 Main Branch Mode

Same as PR mode, plus optional:
- Full refactor validation
- Full test suite execution
- Extended audit verification

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial milestone requirements |
