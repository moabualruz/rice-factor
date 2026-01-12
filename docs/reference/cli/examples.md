# CLI Examples

Real-world examples of Rice-Factor CLI usage.

## Project Initialization

### Basic Init
```bash
rice-factor init
```

### Init with Custom Path
```bash
rice-factor init --path ./new-project
```

### Non-Interactive Init
```bash
rice-factor init --skip-questionnaire
```

### Preview Init (Dry Run)
```bash
rice-factor init --dry-run
```

## Planning Workflow

### Generate All Plans
```bash
# Generate project plan
rice-factor plan project

# Approve and continue
rice-factor approve <project-plan-id>

# Generate architecture
rice-factor plan architecture
rice-factor approve <arch-plan-id>
```

### Quick Test with Stub
```bash
# Test workflow without API calls
rice-factor plan project --stub
rice-factor approve <id>
rice-factor scaffold --stub
```

### Multi-Agent Mode
```bash
# Use voting mode for critical plans
rice-factor plan project --mode voting
```

## Implementation Workflow

### Full Implementation Cycle
```bash
# 1. Plan the implementation
rice-factor plan impl src/models/user.py

# 2. Generate the code
rice-factor impl src/models/user.py

# 3. Review the diff
rice-factor review

# 4. Apply changes
rice-factor apply

# 5. Run tests
rice-factor test
```

### Implement Multiple Files
```bash
# Plan all implementations first
rice-factor plan impl src/models/user.py
rice-factor plan impl src/models/order.py
rice-factor plan impl src/services/auth.py

# Then implement and apply each
for file in src/models/user.py src/models/order.py src/services/auth.py; do
  rice-factor impl "$file"
  rice-factor review
  rice-factor apply
done

rice-factor test
```

### Skip Confirmation
```bash
rice-factor apply --yes
```

## Test Management

### Lock Tests
```bash
# Generate and approve
rice-factor plan tests
rice-factor approve <test-plan-id>

# Lock (permanent!)
rice-factor lock tests
```

### Run Verbose Tests
```bash
rice-factor test --verbose
```

## Validation

### Full Validation
```bash
rice-factor validate
```

### Specific Validation Step
```bash
rice-factor validate --step schema
rice-factor validate --step architecture
rice-factor validate --step tests
rice-factor validate --step lint
```

### Validation Without Saving
```bash
rice-factor validate --no-save
```

## CI/CD Integration

### Full CI Pipeline
```bash
rice-factor ci validate
```

### Specific Stage
```bash
rice-factor ci validate --stage artifact_validation
```

### JSON Output for CI
```bash
rice-factor ci validate --json > ci-results.json
```

### Continue on Failure
```bash
rice-factor ci validate --continue
```

## Drift Detection

### Check for Drift
```bash
rice-factor audit drift
```

### Custom Threshold
```bash
rice-factor audit drift --threshold 2
```

### Different Code Directory
```bash
rice-factor audit drift --code-dir lib
```

### JSON Report
```bash
rice-factor audit drift --json > drift-report.json
```

## Reconciliation

### Generate Reconciliation Plan
```bash
rice-factor reconcile
```

### Preview Without Saving
```bash
rice-factor reconcile --dry-run
```

### Allow New Work During Reconciliation
```bash
rice-factor reconcile --no-freeze
```

## Artifact Management

### List All Artifacts
```bash
rice-factor artifact list
```

### Filter by Type
```bash
rice-factor artifact list --type ProjectPlan
rice-factor artifact list --type TestPlan
```

### Check Artifact Ages
```bash
rice-factor artifact age
```

### JSON Output
```bash
rice-factor artifact age --json
```

## Override Operations

### Override Phase Gate
```bash
rice-factor override phase --reason "Emergency production fix"
```

### Override Validation
```bash
rice-factor override validation --reason "Known false positive" --yes
```

## Migration

### Check Migration Status
```bash
rice-factor migrate status
```

### Preview Migrations
```bash
rice-factor migrate plan
```

### Run Migrations
```bash
rice-factor migrate run
```

### Migration Without Backup
```bash
rice-factor migrate run --no-backup
```

## Usage Tracking

### View Usage
```bash
rice-factor usage show
```

### Filter by Provider
```bash
rice-factor usage show --provider claude
```

### Export Usage
```bash
rice-factor usage export --format csv --output usage.csv
rice-factor usage export --format prometheus
```

### Reset Usage
```bash
rice-factor usage clear --confirm
```

## Metrics

### View Metrics
```bash
rice-factor metrics show
```

### Export Metrics
```bash
rice-factor metrics export --format prometheus > metrics.prom
rice-factor metrics export --format json --output metrics.json
```

## Model Information

### List Available Models
```bash
rice-factor models list
```

### Filter by Provider
```bash
rice-factor models list --provider claude
rice-factor models list --provider openai
rice-factor models list --provider ollama
```

### Filter by Capability
```bash
rice-factor models list --capability code
```

## Agent Management

### Detect Available Agents
```bash
rice-factor agents detect
```

### Force Re-Detection
```bash
rice-factor agents detect --refresh
```

### List Configured Agents
```bash
rice-factor agents list
```

## Batch Operations

### Approve Multiple Artifacts
```bash
rice-factor batch approve "project-plan-*"
```

### Reject with Reason
```bash
rice-factor batch reject "draft-*" --reason "Superseded by new plans"
```

## Visualization

### Generate Mermaid Diagram
```bash
rice-factor viz --format mermaid
```

### Generate SVG
```bash
rice-factor viz --format svg --output deps.svg
```

### Open in Viewer
```bash
rice-factor viz --format png --open
```

### Specific Artifact Type
```bash
rice-factor viz --type ProjectPlan
```

## Documentation Generation

### Generate Markdown Docs
```bash
rice-factor docs
```

### Custom Output Directory
```bash
rice-factor docs --output api-docs
```

### Different Styles
```bash
rice-factor docs --style minimal
rice-factor docs --style detailed
rice-factor docs --style api
```

### HTML Format
```bash
rice-factor docs --format html
```

## User Interfaces

### Launch TUI
```bash
rice-factor tui
```

### TUI for Different Project
```bash
rice-factor tui --project /path/to/project
```

### Start Web Server
```bash
rice-factor web serve
```

### Web Server with Options
```bash
rice-factor web serve --port 8080 --host 0.0.0.0
```

### Development Mode
```bash
rice-factor web serve --reload
```

### Production Mode
```bash
rice-factor web serve --workers 4
```

## Scripting Examples

### Full Automation Script
```bash
#!/bin/bash
set -e

# Initialize and plan
rice-factor init --skip-questionnaire
rice-factor plan project --stub
PROJ_ID=$(rice-factor artifact list --type ProjectPlan --json | jq -r '.[0].id')
rice-factor approve "$PROJ_ID" --yes

# Scaffold
rice-factor scaffold --yes --stub

# Generate and lock tests
rice-factor plan tests --stub
TEST_ID=$(rice-factor artifact list --type TestPlan --json | jq -r '.[0].id')
rice-factor approve "$TEST_ID" --yes
echo "LOCK" | rice-factor lock tests

echo "Setup complete!"
```

### CI Validation Script
```bash
#!/bin/bash

# Run all CI validations
rice-factor ci validate --json | tee ci-results.json

# Check exit code
if [ $? -ne 0 ]; then
  echo "CI validation failed!"
  jq '.stages[] | select(.status == "failed")' ci-results.json
  exit 1
fi

echo "CI validation passed!"
```

### Drift Check Script
```bash
#!/bin/bash

# Check for drift
DRIFT=$(rice-factor audit drift --json)
THRESHOLD=$(echo "$DRIFT" | jq '.max_severity')

if [ "$THRESHOLD" -ge 3 ]; then
  echo "Critical drift detected!"
  echo "$DRIFT" | jq '.signals[] | select(.severity >= 3)'
  exit 1
fi

echo "Drift check passed."
```
