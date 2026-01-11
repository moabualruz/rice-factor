# Feature F08-06: CI Configuration Templates - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-06-01 | Create GitHub Actions workflow template | Pending | P0 |
| T08-06-02 | Create template README | Pending | P1 |
| T08-06-03 | Add template generator CLI command | Pending | P1 |
| T08-06-04 | Test template in sample repository | Pending | P0 |
| T08-06-05 | Write documentation | Pending | P1 |

---

## 2. Task Details

### T08-06-01: Create GitHub Actions Workflow Template

**Objective**: Create production-ready GitHub Actions workflow.

**Files to Create**:
- [ ] `rice_factor/templates/ci/github-actions.yml`

**Implementation**:
- [ ] Create workflow file with all CI stages
- [ ] Add proper checkout with full history
- [ ] Add Python setup
- [ ] Add rice-factor installation
- [ ] Run each validation stage separately
- [ ] Add full validation report
- [ ] Upload report as artifact

**Template Content**:
```yaml
name: Rice-Factor CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Rice-Factor
        run: pip install rice-factor

      - name: Stage 1 - Validate Artifacts
        run: rice-factor ci validate-artifacts

      - name: Stage 2 - Verify Approvals
        run: rice-factor ci validate-approvals

      - name: Stage 3 - Enforce Invariants
        run: rice-factor ci validate-invariants

      - name: Stage 4 - Run Tests
        run: rice-factor test

      - name: Stage 5 - Verify Audit Trail
        run: rice-factor ci validate-audit

      - name: Generate Report
        if: always()
        run: rice-factor ci validate --json > ci-report.json

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ci-report
          path: ci-report.json
```

**Acceptance Criteria**:
- [ ] Workflow runs all 5 stages
- [ ] Fails on any stage failure
- [ ] Produces report artifact

---

### T08-06-02: Create Template README

**Objective**: Document how to use the CI template.

**Files to Create**:
- [ ] `rice_factor/templates/ci/README.md`

**Content**:
- [ ] Quick start instructions
- [ ] Configuration options
- [ ] Stage descriptions
- [ ] Troubleshooting common failures
- [ ] Customization guide

**Acceptance Criteria**:
- [ ] Clear and actionable documentation
- [ ] Covers common use cases

---

### T08-06-03: Add Template Generator CLI Command

**Objective**: Add command to generate CI config.

**Implementation**:
- [ ] Add `rice-factor ci init` command
- [ ] Copy template to `.github/workflows/rice-factor.yml`
- [ ] Support `--force` to overwrite
- [ ] Support `--dry-run` to preview

**Acceptance Criteria**:
- [ ] Command creates workflow file
- [ ] Does not overwrite without `--force`

---

### T08-06-04: Test Template in Sample Repository

**Objective**: Verify template works in real CI.

**Implementation**:
- [ ] Create sample repository with artifacts
- [ ] Add GitHub Actions workflow
- [ ] Trigger workflow and verify pass
- [ ] Test failure scenarios
- [ ] Document test results

**Test Scenarios**:
- [ ] Clean repo with approved artifacts passes
- [ ] Repo with draft artifact fails
- [ ] Repo with unplanned change fails
- [ ] Repo with test modification after lock fails

**Acceptance Criteria**:
- [ ] Template works in GitHub Actions
- [ ] Failures produce actionable output

---

### T08-06-05: Write Documentation

**Objective**: Add CI documentation to main docs.

**Files to Create/Update**:
- [ ] Add CI section to project README
- [ ] Create `docs/guides/ci-setup.md`

**Content**:
- [ ] Overview of CI integration
- [ ] Step-by-step setup guide
- [ ] Failure code reference
- [ ] Best practices

**Acceptance Criteria**:
- [ ] Documentation is complete
- [ ] Links to template files

---

## 3. Task Dependencies

```
T08-06-01 (Template) ──→ T08-06-02 (README)
         │
         └──────────────→ T08-06-03 (CLI)
                                  │
                                  ↓
                          T08-06-04 (Test)
                                  │
                                  ↓
                          T08-06-05 (Docs)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T08-06-01 | Medium | YAML workflow |
| T08-06-02 | Low | Documentation |
| T08-06-03 | Low | File copy |
| T08-06-04 | Medium | Real CI testing |
| T08-06-05 | Low | Documentation |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
