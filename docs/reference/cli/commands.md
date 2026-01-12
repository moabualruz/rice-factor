# CLI Commands Reference

Complete reference for all Rice-Factor CLI commands.

![CLI Help](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-help.svg)

## Global Options

These options are available for all commands:

| Option | Description |
|--------|-------------|
| `--version`, `-v` | Show version and exit |
| `--verbose`, `-V` | Enable verbose output |
| `--quiet`, `-q` | Suppress non-essential output |
| `--help` | Show help message |

## Core Workflow Commands

### rice-factor init

Initialize a new Rice-Factor project.

![CLI Init](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-init.svg)

```bash
rice-factor init [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Path to initialize project in | `.` |
| `--force`, `-f` | Overwrite existing `.project/` directory | `false` |
| `--dry-run`, `-n` | Show what would be created | `false` |
| `--skip-questionnaire`, `-s` | Skip interactive questionnaire | `false` |

**Example:**
```bash
rice-factor init --path ./my-project
```

---

### rice-factor plan

Generate planning artifacts.

![CLI Plan](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-plan.svg)

#### rice-factor plan project

Generate a ProjectPlan artifact.

```bash
rice-factor plan project [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--dry-run`, `-n` | Show without saving | `false` |
| `--stub` | Use stub LLM (no API calls) | `false` |
| `--mode`, `-m` | Multi-agent run mode | `solo` |

---

#### rice-factor plan architecture

Generate an ArchitecturePlan artifact.

```bash
rice-factor plan architecture [OPTIONS]
```

**Options:** Same as `plan project`

**Requires:** Approved ProjectPlan

---

#### rice-factor plan tests

Generate a TestPlan artifact.

```bash
rice-factor plan tests [OPTIONS]
```

**Options:** Same as `plan project`

**Requires:** Scaffolded project

---

#### rice-factor plan impl

Generate an ImplementationPlan for a specific file.

```bash
rice-factor plan impl TARGET [OPTIONS]
```

**Arguments:**
| Argument | Description | Required |
|----------|-------------|----------|
| `TARGET` | Target file to implement | Yes |

**Options:** Same as `plan project`

**Requires:** Locked TestPlan

**Example:**
```bash
rice-factor plan impl src/calculator/operations.py
```

---

#### rice-factor plan refactor

Generate a RefactorPlan artifact.

```bash
rice-factor plan refactor GOAL [OPTIONS]
```

**Arguments:**
| Argument | Description | Required |
|----------|-------------|----------|
| `GOAL` | Goal of the refactoring | Yes |

**Options:** Same as `plan project`

**Example:**
```bash
rice-factor plan refactor "Extract interface from UserService"
```

---

### rice-factor scaffold

Create file structure from ScaffoldPlan.

![CLI Scaffold](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-scaffold.svg)

```bash
rice-factor scaffold [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--dry-run`, `-n` | Show without creating | `false` |
| `--yes`, `-y` | Skip confirmation | `false` |
| `--stub` | Use stub LLM | `false` |

---

### rice-factor impl

Generate implementation diff for a file.

![CLI Impl](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-impl.svg)

```bash
rice-factor impl FILE_PATH [OPTIONS]
```

**Arguments:**
| Argument | Description | Required |
|----------|-------------|----------|
| `FILE_PATH` | Path to file to implement | Yes |

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--dry-run`, `-n` | Show without saving | `false` |
| `--stub` | Use stub LLM | `false` |

---

### rice-factor review

Review pending diffs.

```bash
rice-factor review [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |

**Interactive Actions:**
- `[a]` Approve
- `[r]` Reject
- `[s]` Skip

---

### rice-factor apply

Apply approved diffs.

```bash
rice-factor apply [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--dry-run`, `-n` | Show without applying | `false` |
| `--yes`, `-y` | Skip confirmation | `false` |

---

### rice-factor test

Run test suite.

![CLI Test](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-test.svg)

```bash
rice-factor test [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--verbose`, `-v` | Verbose test output | `false` |

---

### rice-factor approve

Approve an artifact.

![CLI Approve](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-approve.svg)

```bash
rice-factor approve ARTIFACT [OPTIONS]
```

**Arguments:**
| Argument | Description | Required |
|----------|-------------|----------|
| `ARTIFACT` | Artifact ID or path | Yes |

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--yes`, `-y` | Skip confirmation | `false` |

---

### rice-factor lock

Lock an artifact (TestPlan only).

```bash
rice-factor lock ARTIFACT [OPTIONS]
```

**Arguments:**
| Argument | Description | Required |
|----------|-------------|----------|
| `ARTIFACT` | Artifact to lock (`tests` or UUID/path) | Yes |

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |

**Note:** Requires typing "LOCK" to confirm. This is permanent!

---

## Validation Commands

### rice-factor validate

Run validations on artifacts and code.

```bash
rice-factor validate [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--step`, `-s` | Specific step (schema, architecture, tests, lint) | All |
| `--save/--no-save` | Save ValidationResult | `true` |

---

### rice-factor diagnose

Diagnose failures.

```bash
rice-factor diagnose [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |

---

## CI/CD Commands

![CLI CI](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-ci.svg)

### rice-factor ci validate

Run full CI validation pipeline.

```bash
rice-factor ci validate [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--json` | Output results as JSON | `false` |
| `--continue-on-failure` | Run all stages even if earlier stages fail | `false` |

**Stages Executed:**
1. Artifact Validation - Check artifact status and schema
2. Approval Verification - Check all required approvals
3. Invariant Enforcement - Check test locks, architecture rules
4. Audit Verification - Verify audit trail integrity

**Exit Codes:**
- `0` - All stages passed
- `1` - One or more stages failed

---

### rice-factor ci validate-artifacts

Run artifact validation stage only.

```bash
rice-factor ci validate-artifacts [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--json` | Output results as JSON | `false` |

**Validates:**
- No draft artifacts present
- All artifacts pass schema validation
- Locked artifacts not modified
- Artifact hashes match content

---

### rice-factor ci validate-approvals

Run approval verification stage only.

```bash
rice-factor ci validate-approvals [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--json` | Output results as JSON | `false` |

**Validates:**
- All required artifacts are approved
- Approval metadata is complete
- Approvals are not expired

---

### rice-factor ci validate-invariants

Run invariant enforcement stage only.

```bash
rice-factor ci validate-invariants [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--json` | Output results as JSON | `false` |

**Validates:**
- Tests not modified after lock
- No unplanned code changes
- Architecture rules not violated

---

### rice-factor ci validate-audit

Run audit verification stage only.

```bash
rice-factor ci validate-audit [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--json` | Output results as JSON | `false` |

**Validates:**
- Audit trail integrity
- No missing entries
- Hash chain is intact

---

### rice-factor ci init

Initialize CI configuration for the project.

```bash
rice-factor ci init [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root directory | `.` |
| `--force`, `-f` | Overwrite existing workflow file | `false` |
| `--dry-run` | Show what would be created | `false` |

Creates a GitHub Actions workflow file at `.github/workflows/rice-factor.yml`.

---

## Artifact Management

### rice-factor artifact age

Show artifact ages and lifecycle status.

```bash
rice-factor artifact age [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root | `.` |
| `--type`, `-t` | Filter by artifact type | All |
| `--json` | Output as JSON | `false` |

**Exit Codes:**
- `0` - All artifacts healthy
- `1` - Some artifacts require review (>= 3 months old)
- `2` - Artifacts significantly overdue (>= 6 months old)

---

### rice-factor artifact review

Mark an artifact as reviewed.

```bash
rice-factor artifact review ARTIFACT_ID [OPTIONS]
```

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `ARTIFACT_ID` | Artifact ID to mark as reviewed | Yes |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root | `.` |
| `--notes`, `-n` | Optional review notes | None |

**Note:** Cannot review LOCKED artifacts.

---

### rice-factor artifact extend

Extend artifact validity period.

```bash
rice-factor artifact extend ARTIFACT_ID [OPTIONS]
```

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `ARTIFACT_ID` | Artifact ID to extend | Yes |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root | `.` |
| `--reason`, `-r` | Reason for extension (required) | Required |
| `--months`, `-m` | Extension period in months | Type default |

**Note:** Cannot extend LOCKED artifacts.

---

### rice-factor artifact migrate

Migrate artifacts to add lifecycle timestamp fields.

```bash
rice-factor artifact migrate [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root | `.` |
| `--dry-run` | Preview changes without writing | `false` |
| `--verbose`, `-v` | Enable verbose output | `false` |
| `--json` | Output as JSON | `false` |

**Note:** Migration is idempotent - safe to run multiple times.

---

## Drift Detection

![CLI Audit](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-audit.svg)

### rice-factor audit drift

Detect drift between code and artifacts.

```bash
rice-factor audit drift [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root | `.` |
| `--code-dir`, `-d` | Code directory to scan | `src` |
| `--threshold`, `-t` | Drift threshold | `3` |
| `--json` | Output as JSON | `false` |

**Detects:**
- Orphan code: Source files not covered by any implementation plan
- Orphan plans: Plans targeting non-existent files
- Refactor hotspots: Files frequently modified

**Exit Codes:**
- `0` - No drift detected
- `1` - Drift detected but below threshold
- `2` - Reconciliation required (threshold exceeded or critical signals)

---

### rice-factor audit coverage

Check coverage drift for TestPlan artifacts.

```bash
rice-factor audit coverage [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root | `.` |
| `--threshold`, `-t` | Coverage drift threshold percentage | `10.0` |
| `--json` | Output as JSON | `false` |
| `--no-run` | Skip running tests, use existing coverage report | `false` |

**Exit Codes:**
- `0` - All TestPlans within threshold
- `1` - Some TestPlans exceed drift threshold
- `2` - Critical drift detected (> 2x threshold)

---

### rice-factor reconcile

Generate reconciliation plan.

![CLI Reconcile](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-reconcile.svg)

```bash
rice-factor reconcile [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root | `.` |
| `--code-dir`, `-d` | Code directory | `src` |
| `--threshold`, `-t` | Drift threshold | `3` |
| `--no-freeze` | Don't freeze new work | `false` |
| `--dry-run` | Show without saving | `false` |
| `--json` | Output as JSON | `false` |

---

## Refactoring Commands

![CLI Refactor](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-refactor.svg)

### rice-factor refactor check

Check refactoring capability support.

```bash
rice-factor refactor check [OPTIONS]
```

---

### rice-factor capabilities

Show refactoring tool capabilities.

```bash
rice-factor capabilities [OPTIONS]
```

---

## Override and Recovery

### rice-factor override create

Create a manual override for a blocked operation.

```bash
rice-factor override create TARGET [OPTIONS]
```

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `TARGET` | What to override (phase, approval, validation) | Yes |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--reason`, `-r` | Reason for override | Required |
| `--path`, `-p` | Project root | `.` |
| `--yes`, `-y` | Skip confirmation | `false` |

**Valid Targets:**
- `phase` - Bypass phase gating
- `approval` - Bypass approval requirements
- `validation` - Bypass validation checks

**Note:** Requires typing "OVERRIDE" to confirm. All overrides are recorded in the audit trail.

**Example:**
```bash
rice-factor override create phase --reason "Testing in development"
rice-factor override create approval --reason "Emergency hotfix"
```

---

### rice-factor override list

List pending overrides that need reconciliation.

```bash
rice-factor override list [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root | `.` |
| `--all`, `-a` | Show all overrides including reconciled | `false` |

---

### rice-factor override reconcile

Mark an override as reconciled.

```bash
rice-factor override reconcile OVERRIDE_ID [OPTIONS]
```

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `OVERRIDE_ID` | Override ID to reconcile (can be partial) | Yes |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path`, `-p` | Project root | `.` |

---

### rice-factor resume

Resume after failure.

```bash
rice-factor resume [OPTIONS]
```

---

## Migration

### rice-factor migrate status

Show migration status.

```bash
rice-factor migrate status [OPTIONS]
```

---

### rice-factor migrate plan

Generate migration plan.

```bash
rice-factor migrate plan [OPTIONS]
```

---

### rice-factor migrate run

Execute migrations.

```bash
rice-factor migrate run [OPTIONS]
```

---

## Metrics and Usage

### rice-factor metrics show

Display metrics.

```bash
rice-factor metrics show [OPTIONS]
```

---

### rice-factor metrics export

Export metrics.

```bash
rice-factor metrics export [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--format` | Format (prometheus, otlp, json, csv) | `json` |
| `--output`, `-o` | Output file | stdout |

---

### rice-factor usage show

Display usage statistics.

```bash
rice-factor usage show [OPTIONS]
```

---

### rice-factor usage export

Export usage data.

```bash
rice-factor usage export [OPTIONS]
```

---

### rice-factor usage clear

Reset usage tracking.

```bash
rice-factor usage clear [OPTIONS]
```

---

## Model Management

### rice-factor models

List registered LLM models.

```bash
rice-factor models [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--provider`, `-p` | Filter by provider | All |
| `--capability` | Filter by capability | All |
| `--json` | Output as JSON | `false` |

---

## Agent Management

### rice-factor agents detect

Detect available CLI agents.

```bash
rice-factor agents detect [OPTIONS]
```

---

### rice-factor agents list

List configured agents.

```bash
rice-factor agents list [OPTIONS]
```

---

## Batch Operations

### rice-factor batch approve

Approve multiple artifacts.

```bash
rice-factor batch approve PATTERN [OPTIONS]
```

---

### rice-factor batch reject

Reject multiple artifacts.

```bash
rice-factor batch reject PATTERN [OPTIONS]
```

---

## Visualization

### rice-factor viz

Generate dependency graphs.

```bash
rice-factor viz [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--type`, `-t` | Artifact type | All |
| `--format` | Output format (mermaid, dot, svg, png) | `mermaid` |
| `--output`, `-o` | Output file | stdout |
| `--open` | Open in viewer | `false` |

---

## Documentation

### rice-factor docs

Generate documentation from artifacts.

```bash
rice-factor docs [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o` | Output directory | `docs` |
| `--style` | Style (minimal, detailed, api) | `detailed` |
| `--format` | Format (markdown, html, pdf) | `markdown` |

---

## User Interfaces

### rice-factor tui

Launch TUI mode.

![CLI TUI](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/cli/cli-tui.svg)

```bash
rice-factor tui [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--project`, `-p` | Project directory | `.` |

---

### rice-factor web serve

Start web server.

```bash
rice-factor web serve [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--port`, `-p` | Server port | `8000` |
| `--host` | Server host | `127.0.0.1` |
| `--reload`, `-r` | Enable hot reload | `false` |
| `--workers`, `-w` | Worker processes | `1` |

---

### rice-factor web build

Build frontend.

```bash
rice-factor web build [OPTIONS]
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Artifact not found |
| 4 | Validation failure |
