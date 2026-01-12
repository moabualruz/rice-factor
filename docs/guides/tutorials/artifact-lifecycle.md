# Artifact Lifecycle Tutorial

This tutorial provides a deep understanding of how artifacts flow through states in Rice-Factor.

## Understanding Artifact States

Every artifact in Rice-Factor has a status that controls what operations are allowed:

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│  DRAFT   │ ────approve────→   │ APPROVED │ ─────lock─────→    │  LOCKED  │
│          │                    │          │                    │          │
│ Editable │                    │Executable│                    │Immutable │
│ Not exec │                    │ Not edit │                    │ Not edit │
└──────────┘                    └──────────┘                    └──────────┘
```

### DRAFT State

**What it means**: The artifact is a work in progress.

**Allowed operations**:
- View/read the artifact
- Delete the artifact
- Regenerate (creates new artifact)

**Not allowed**:
- Execute (scaffold, implement, etc.)
- Lock

**How to exit**: `rice-factor approve <artifact-id>`

### APPROVED State

**What it means**: Human has reviewed and approved the plan.

**Allowed operations**:
- View/read
- Execute (the main purpose!)
- Lock (TestPlan only)

**Not allowed**:
- Modify
- Delete (without explicit override)

**How to exit**:
- `rice-factor lock <artifact-id>` (TestPlan only)
- Otherwise, APPROVED is the final state

### LOCKED State

**What it means**: Permanently immutable. Automation cannot modify.

**Applies to**: TestPlan only

**Allowed operations**:
- View/read
- Execute

**Not allowed**:
- Modify (ever)
- Delete (ever)
- Unlock (no such operation exists)

**Purpose**: Enforces TDD - tests are the source of truth.

## Hands-On: Tracking State Changes

### Create a Test Artifact

```bash
# Initialize project
rice-factor init

# Edit requirements (minimal example)
echo "# Simple Calculator" > .project/requirements.md

# Generate a plan
rice-factor plan project
```

### Check Initial State

```bash
# List artifacts
rice-factor artifact list

# Output shows:
# ID: abc123-...
# Type: ProjectPlan
# Status: DRAFT
# Created: 2024-01-15T10:30:00Z
```

The artifact starts in DRAFT.

### Transition to APPROVED

```bash
# Approve the artifact
rice-factor approve abc123

# Check status again
rice-factor artifact list

# Status is now: APPROVED
```

### Observe Execution Gate

```bash
# Try to scaffold without approval
# (Would fail if artifact was still DRAFT)
rice-factor scaffold
```

Only APPROVED or LOCKED artifacts can be executed.

### Lock a TestPlan

```bash
# Generate and approve test plan
rice-factor plan tests
rice-factor approve <test-plan-id>

# Lock it (requires confirmation)
rice-factor lock tests
# Type "LOCK" to confirm

# Status is now: LOCKED
```

## State Transitions in Detail

### DRAFT → APPROVED

**Trigger**: `rice-factor approve <artifact>`

**What happens**:
1. Artifact status changes to APPROVED
2. `updated_at` timestamp updated
3. Approval record created in audit trail
4. Artifact becomes executable

**Audit entry example**:
```json
{
  "action": "approve",
  "artifact_id": "abc123-...",
  "approved_by": "cli",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### APPROVED → LOCKED

**Trigger**: `rice-factor lock <artifact>` or `rice-factor lock tests`

**What happens**:
1. Status changes to LOCKED
2. Artifact becomes permanently immutable
3. Lock record created in audit trail
4. Human must type "LOCK" to confirm

**Why explicit confirmation?**
Locking is irreversible. Once locked, a TestPlan can never be changed. This ensures humans understand the implications.

## Artifact Dependencies

Artifacts can depend on each other:

```
ProjectPlan
    ↓
ArchitecturePlan
    ↓
ScaffoldPlan
    ↓
TestPlan (locked)
    ↓
ImplementationPlan → ValidationResult
```

### Dependency Rules

1. **ProjectPlan** must be APPROVED before generating ArchitecturePlan
2. **ScaffoldPlan** requires approved ProjectPlan
3. **TestPlan** must be LOCKED before generating ImplementationPlan
4. **ImplementationPlan** references the locked TestPlan

### Checking Dependencies

```bash
# View an artifact's dependencies
cat .project/artifacts/implementation_plans/*.json | jq '.depends_on'
```

## Lifecycle Metadata

Each artifact tracks lifecycle information:

```json
{
  "id": "abc123-...",
  "artifact_type": "TestPlan",
  "status": "locked",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "created_by": "llm",
  "last_reviewed_at": "2024-01-15T10:34:00Z",
  "review_notes": "Approved after checking test coverage",
  "depends_on": ["project-plan-id"]
}
```

### Age Tracking

Rice-Factor tracks how old artifacts are:

```bash
# Check artifact ages
rice-factor artifact age

# Output:
# TestPlan abc123: 5 days old (healthy)
# ProjectPlan def456: 45 days old (REVIEW NEEDED)
```

Artifacts may need review after extended periods.

## Practical Patterns

### Pattern 1: Regenerate Instead of Edit

Since APPROVED artifacts can't be edited, regenerate if changes needed:

```bash
# Bad: trying to edit approved artifact
# (Not allowed)

# Good: generate a new plan
rice-factor plan project  # Creates new DRAFT
rice-factor approve <new-id>
```

### Pattern 2: Override for Emergencies

If you must bypass a gate (rare!):

```bash
rice-factor override phase --reason "Critical hotfix for production"
```

Overrides are:
- Logged in audit trail
- Require explicit reason
- Should be rare

### Pattern 3: Review Before Lock

Always review TestPlan thoroughly before locking:

```bash
# View the test plan
cat .project/artifacts/test_plans/*.json | jq '.payload.tests'

# Check test coverage looks complete
# Then approve and lock
rice-factor approve <id>
rice-factor lock tests
```

## Common Questions

### Can I unlock a TestPlan?
No. Locking is permanent by design. If tests need to change, it indicates a requirements change that should go through the full planning cycle.

### What if I approved the wrong artifact?
Generate a new one and approve that instead. The old artifact remains but won't be used.

### How do I know what state an artifact is in?
```bash
rice-factor artifact list
# or
cat .project/artifacts/*/*.json | jq '{id, status}'
```

### Can DRAFT artifacts be executed?
No. Execution requires APPROVED or LOCKED status.

## Summary

| State | Editable | Executable | Lockable |
|-------|----------|------------|----------|
| DRAFT | Yes | No | No |
| APPROVED | No | Yes | Yes (TestPlan) |
| LOCKED | No | Yes | N/A |

## What's Next?

- [TDD Workflow](tdd-workflow.md) - How locked tests enforce TDD
- [Artifact Reference](../../reference/artifacts/overview.md) - All artifact types
- [Common Errors](../troubleshooting/common-errors.md) - State-related errors
