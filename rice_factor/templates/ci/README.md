# Rice-Factor CI Templates

This directory contains CI configuration templates for integrating rice-factor validation into your CI/CD pipeline.

## Quick Start

### GitHub Actions

1. Copy the template to your repository:
   ```bash
   rice-factor ci init
   ```

   Or manually copy `github-actions.yml` to `.github/workflows/rice-factor.yml`

2. Push to trigger the workflow

3. View results in the Actions tab

## CI Pipeline Stages

The rice-factor CI pipeline runs 5 validation stages:

### Stage 1: Artifact Validation
- Validates all artifact JSON files against schemas
- Ensures no draft artifacts are present
- Checks that locked artifacts haven't been modified

**Failure codes:**
- `DRAFT_ARTIFACT_PRESENT`: Remove or approve draft artifacts
- `LOCKED_ARTIFACT_MODIFIED`: Revert changes to locked artifacts
- `SCHEMA_VALIDATION_FAILED`: Fix artifact schema errors

### Stage 2: Approval Verification
- Verifies all non-draft artifacts have approval records
- Checks approval metadata integrity

**Failure codes:**
- `ARTIFACT_NOT_APPROVED`: Run `rice-factor approve <artifact>`
- `APPROVAL_METADATA_MISSING`: Re-run approval process

### Stage 3: Invariant Enforcement
- Prevents test modifications after TestPlan lock
- Ensures code changes are covered by approved plans

**Failure codes:**
- `TEST_MODIFICATION_AFTER_LOCK`: Revert test changes or unlock TestPlan
- `UNPLANNED_CODE_CHANGE`: Create a plan for the changes

### Stage 4: Test Execution
- Runs the project test suite
- Uses native test runners (pytest, cargo test, etc.)

**Failure codes:**
- `TEST_FAILURE`: Fix failing tests

### Stage 5: Audit Verification
- Verifies audit log integrity
- Checks that referenced diff files exist
- Validates hash chain (if enabled)

**Failure codes:**
- `AUDIT_INTEGRITY_VIOLATION`: Contact security team
- `AUDIT_MISSING_ENTRY`: Ensure operations are logged
- `AUDIT_HASH_CHAIN_BROKEN`: Investigate potential tampering

## Configuration Options

### GitHub Actions

Customize the workflow by editing `.github/workflows/rice-factor.yml`:

```yaml
env:
  PYTHON_VERSION: "3.11"  # Change Python version
```

### CLI Options

Run individual stages:
```bash
rice-factor ci validate-artifacts
rice-factor ci validate-approvals
rice-factor ci validate-invariants
rice-factor ci validate-audit
```

Run full validation:
```bash
rice-factor ci validate
rice-factor ci validate --continue-on-failure  # Run all stages even if some fail
rice-factor ci validate --json                  # JSON output for machine parsing
```

## Troubleshooting

### "Draft artifact found"
Draft artifacts cannot be merged. Either:
1. Approve the artifact: `rice-factor approve <artifact-id>`
2. Delete the draft if not needed

### "Unplanned code change"
All source code changes must be covered by an approved ImplementationPlan or RefactorPlan:
1. Create a plan: `rice-factor plan impl <file>`
2. Approve the plan: `rice-factor approve <plan-id>`

### "Test file modified after TestPlan lock"
Tests are immutable after locking. Either:
1. Revert the test changes
2. Unlock the TestPlan (requires approval workflow)

## Best Practices

1. **Approve artifacts before pushing** - Run `rice-factor ci validate` locally
2. **Keep drafts local** - Don't commit draft artifacts
3. **Lock TestPlan early** - Lock tests after initial approval to prevent drift
4. **Review CI failures** - Each failure code has specific remediation
