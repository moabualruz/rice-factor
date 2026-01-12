# Integrate CI/CD

This guide explains how to integrate Rice-Factor with CI/CD pipelines.

## Overview

Rice-Factor provides CI/CD commands that:
- Validate all artifacts
- Verify approvals
- Enforce invariants
- Check audit trail integrity

## Quick Start

Add to your pipeline:

```yaml
# GitHub Actions
- name: Validate Rice-Factor
  run: rice-factor ci validate
```

## GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/rice-factor.yml
name: Rice-Factor Validation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Rice-Factor
        run: pip install rice-factor

      - name: Validate Artifacts
        run: rice-factor ci validate

      - name: Run Tests
        run: rice-factor test
```

### Full Pipeline

```yaml
name: Rice-Factor CI

on:
  push:
    branches: [main, develop]
  pull_request:

env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

jobs:
  validate:
    name: Validate Artifacts
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install rice-factor
          pip install -e ".[dev]"

      - name: Artifact Validation
        run: rice-factor ci validate --stage artifact_validation

      - name: Approval Verification
        run: rice-factor ci validate --stage approval_verification

      - name: Invariant Enforcement
        run: rice-factor ci validate --stage invariant_enforcement

      - name: Audit Verification
        run: rice-factor ci validate --stage audit_verification

  test:
    name: Run Tests
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run Rice-Factor Tests
        run: rice-factor test --verbose

      - name: Upload Validation Results
        uses: actions/upload-artifact@v4
        with:
          name: validation-results
          path: .project/artifacts/validation_results/

  drift:
    name: Drift Detection
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Rice-Factor
        run: pip install rice-factor

      - name: Check for Drift
        run: rice-factor audit drift --threshold 3 --json > drift-report.json

      - name: Upload Drift Report
        uses: actions/upload-artifact@v4
        with:
          name: drift-report
          path: drift-report.json
```

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

validate:
  stage: validate
  image: python:3.11
  script:
    - pip install rice-factor
    - rice-factor ci validate
  artifacts:
    paths:
      - .project/artifacts/
    expire_in: 1 week

test:
  stage: test
  image: python:3.11
  needs: [validate]
  script:
    - pip install -e ".[dev]"
    - rice-factor test --verbose
  artifacts:
    reports:
      junit: test-results.xml

drift-check:
  stage: validate
  image: python:3.11
  script:
    - pip install rice-factor
    - rice-factor audit drift --json > drift-report.json
  artifacts:
    paths:
      - drift-report.json
  only:
    - merge_requests
```

## CI Validation Stages

### Stage 1: Artifact Validation

Validates all artifacts against schemas:

```bash
rice-factor ci validate --stage artifact_validation
```

**Checks:**
- JSON schema compliance
- Required fields present
- Data types correct
- Constraints satisfied

### Stage 2: Approval Verification

Verifies artifacts are properly approved:

```bash
rice-factor ci validate --stage approval_verification
```

**Checks:**
- Executable artifacts are APPROVED or LOCKED
- TestPlan is LOCKED before implementation
- Approval records exist in audit trail

### Stage 3: Invariant Enforcement

Enforces system invariants:

```bash
rice-factor ci validate --stage invariant_enforcement
```

**Checks:**
- No code without plan
- No implementation before test lock
- Architecture rules not violated
- No orphan artifacts

### Stage 4: Audit Verification

Checks audit trail integrity:

```bash
rice-factor ci validate --stage audit_verification
```

**Checks:**
- Audit log completeness
- Override records have reasons
- No gaps in audit trail

## Drift Detection in CI

Detect when code drifts from artifacts:

```yaml
- name: Drift Check
  run: |
    rice-factor audit drift --threshold 3
    if [ $? -ne 0 ]; then
      echo "Drift detected! Run 'rice-factor reconcile' locally."
      exit 1
    fi
```

Threshold levels:
- `1`: Informational (log only)
- `2`: Warning (continue)
- `3`: Error (fail pipeline)

## PR Validation

Add checks for pull requests:

```yaml
# Check PR doesn't introduce unapproved changes
- name: Validate PR Changes
  run: |
    # Get changed files
    CHANGED=$(git diff --name-only origin/main)

    # Check if artifact files changed
    if echo "$CHANGED" | grep -q ".project/artifacts/"; then
      # Verify new artifacts are valid
      rice-factor ci validate
    fi
```

## Blocking Conditions

Configure what blocks merges:

```yaml
# rice-factor CI config
ci:
  block_on:
    - unapproved_artifacts
    - unlocked_tests
    - schema_violations
    - drift_threshold_exceeded

  warn_on:
    - stale_artifacts
    - missing_reviews
```

## JSON Output

Get machine-readable output for integrations:

```bash
# Full report as JSON
rice-factor ci validate --json > ci-report.json

# Use with jq
rice-factor ci validate --json | jq '.stages[] | select(.status == "failed")'
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | Validation failures |
| 2 | Configuration error |
| 3 | Artifact not found |

## Integration Examples

### Slack Notification on Failure

```yaml
- name: Notify Slack on Failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    channel-id: 'dev-alerts'
    slack-message: |
      :x: Rice-Factor CI failed on ${{ github.ref }}
      Commit: ${{ github.sha }}
      Run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

### Store Artifacts for Review

```yaml
- name: Upload Artifacts for Review
  uses: actions/upload-artifact@v4
  with:
    name: rice-factor-artifacts
    path: |
      .project/artifacts/
      .project/audit/
```

### Required Status Checks

In GitHub repository settings:
1. Settings → Branches → Branch protection rules
2. Require status checks: `validate`, `test`
3. Require branches to be up to date

## Troubleshooting

### "Artifact validation failed"

```bash
# Get detailed errors
rice-factor ci validate --json | jq '.stages[0].errors'
```

### "Tests not locked"

Tests must be locked before implementation:

```bash
rice-factor lock tests
git add .project/artifacts/test_plans/
git commit -m "Lock TestPlan"
```

### "Approval missing"

```bash
# Find unapproved artifacts
rice-factor artifact list | grep DRAFT
```

## What's Next?

- [CI Reference](../../reference/cli/commands.md#rice-factor-ci) - Full CI command docs
- [Drift Detection](../../reference/artifacts/lifecycle.md) - Understanding drift
- [Troubleshooting](../troubleshooting/common-errors.md) - CI errors
