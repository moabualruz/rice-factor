# Drift Detection and Reconciliation Configuration

This guide covers how to configure drift detection and reconciliation in Rice-Factor.

## Overview

Rice-Factor includes a drift detection system that identifies when code and artifacts diverge. When drift exceeds a configurable threshold, a reconciliation plan is generated to bring them back into alignment.

## Configuration File

Create `.project/drift.yaml` in your project root:

```yaml
# Drift Detection Configuration
drift:
  # Drift threshold - number of signals before reconciliation is required
  # Default: 3
  threshold: 3

  # Source directories to scan for code
  # Default: ["src"]
  source_dirs:
    - src
    - lib

  # Patterns to exclude from scanning
  # Default: ["__pycache__", ".git", "node_modules"]
  exclude_patterns:
    - "__pycache__"
    - ".git"
    - "node_modules"
    - ".venv"

  # Enable/disable specific signal types
  signals:
    unplanned_code: true      # Code without corresponding plan
    orphaned_plan: true       # Plans without corresponding code
    stale_plan: true          # Plans older than threshold
    repeated_refactor: true   # Multiple refactors in same area
    undocumented_behavior: true  # Tests for undocumented features
```

## CLI Options

Drift detection and reconciliation can be configured via CLI options:

### `rice-factor audit drift`

Detect drift between code and artifacts.

```bash
# Basic usage
rice-factor audit drift

# With custom code directory
rice-factor audit drift --code-dir src/main

# JSON output
rice-factor audit drift --json

# Full analysis (detailed)
rice-factor audit drift --full
```

### `rice-factor reconcile`

Generate a reconciliation plan.

```bash
# Basic usage
rice-factor reconcile

# Custom threshold
rice-factor reconcile --threshold 5

# Dry run (don't save)
rice-factor reconcile --dry-run

# Don't freeze new work
rice-factor reconcile --no-freeze

# JSON output
rice-factor reconcile --json
```

## Drift Signals

Rice-Factor detects the following drift signals:

| Signal Type | Description |
|-------------|-------------|
| `unplanned_code` | Code files that have no corresponding ImplementationPlan or ScaffoldPlan |
| `orphaned_plan` | Plans that reference code that doesn't exist |
| `stale_plan` | Plans that haven't been updated past their review date |
| `repeated_refactor` | Multiple refactors targeting the same code area |
| `undocumented_behavior` | Tests that cover behavior not in requirements |

## Reconciliation Actions

When reconciliation is needed, the following actions may be recommended:

| Action | Description |
|--------|-------------|
| `create_artifact` | Create a new plan for unplanned code |
| `update_artifact` | Update an existing plan to match reality |
| `archive_artifact` | Archive an orphaned or obsolete plan |
| `update_requirements` | Update requirements to match behavior |
| `review_code` | Human review of code needed |
| `delete_code` | Consider removing code |

## Thresholds

The drift threshold controls when reconciliation is triggered:

- **Low threshold (1-2)**: Strict - reconcile on any drift
- **Default (3)**: Balanced - allows minor drift
- **High (5+)**: Permissive - only reconcile on significant drift

## Work Freeze

When drift exceeds the threshold, new work can be frozen:

```yaml
reconciliation:
  freeze_on_drift: true  # Default
```

While frozen:
- `rice-factor plan impl` is blocked
- `rice-factor scaffold` is blocked
- `rice-factor reconcile apply` must be used first

## Example Workflow

1. **Detect drift**:
   ```bash
   rice-factor audit drift
   ```

2. **Generate reconciliation plan**:
   ```bash
   rice-factor reconcile
   ```

3. **Review the plan**:
   The plan is saved as a DRAFT artifact.

4. **Approve the plan**:
   ```bash
   rice-factor approve <artifact-id>
   ```

5. **Resume work**:
   After approval, new work is unblocked.

## Artifact Lifecycle Integration

Drift detection integrates with the artifact lifecycle system:

- Stale artifacts (past review date) trigger drift signals
- Coverage drift in TestPlan triggers reconciliation
- ArchitecturePlan violations are flagged

See also: [Artifact Lifecycle](./artifact-lifecycle.md)
