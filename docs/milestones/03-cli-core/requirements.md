# Milestone 03: CLI Core - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.2.0
> **Status**: Pending

---

## 1. Milestone Objective

Implement the complete CLI interface for Rice-Factor, including all commands for initialization, planning, implementation, and validation workflows.

---

## 2. Scope

### 2.1 In Scope
- CLI framework setup (Typer)
- All `rice-factor` subcommands
- Interactive questionnaire for `rice-factor init`
- Human approval workflows
- Progress reporting and output formatting

### 2.2 Out of Scope
- LLM integration (Milestone 04)
- Executor logic (Milestone 05)
- Validation logic (Milestone 06)

---

## 3. Ubiquitous Requirements

| ID | Requirement |
|----|-------------|
| M03-U-001 | The CLI **shall** be invoked via the `rice-factor` command |
| M03-U-002 | All commands **shall** support `--help` for documentation |
| M03-U-003 | All commands **shall** support `--dry-run` where applicable |
| M03-U-004 | All destructive commands **shall** require confirmation |
| M03-U-005 | The CLI **shall** provide colored, formatted output via Rich |

---

## 4. Commands

| Command | Purpose | Priority |
|---------|---------|----------|
| `rice-factor init` | Initialize project | P0 |
| `rice-factor plan project` | Generate ProjectPlan | P0 |
| `rice-factor plan architecture` | Generate ArchitecturePlan | P1 |
| `rice-factor scaffold` | Create file structure | P0 |
| `rice-factor plan tests` | Generate TestPlan | P0 |
| `rice-factor lock tests` | Lock TestPlan | P0 |
| `rice-factor plan impl <file>` | Generate ImplementationPlan | P0 |
| `rice-factor impl <file>` | Generate implementation diff | P0 |
| `rice-factor review` | Show pending diff for approval | P0 |
| `rice-factor apply` | Apply approved diff | P0 |
| `rice-factor test` | Run test suite | P0 |
| `rice-factor diagnose` | Analyze test/validation failures | P0 |
| `rice-factor approve <artifact>` | Approve artifact | P0 |
| `rice-factor plan refactor <goal>` | Generate RefactorPlan | P1 |
| `rice-factor refactor check` | Verify refactor capability support | P1 |
| `rice-factor refactor dry-run` | Preview refactor | P1 |
| `rice-factor refactor apply` | Apply refactor | P1 |
| `rice-factor validate` | Run all validations | P1 |
| `rice-factor override --reason` | Override blocked operations with audit | P1 |
| `rice-factor resume` | Resume after failure | P1 |

---

## 5. Features

| Feature ID | Feature Name | Priority |
|------------|--------------|----------|
| F03-01 | CLI Framework Setup | P0 |
| F03-02 | Init Command | P0 |
| F03-03 | Plan Commands | P0 |
| F03-04 | Scaffold Command | P0 |
| F03-05 | Implementation Commands | P0 |
| F03-06 | Approval Commands | P0 |
| F03-07 | Refactor Commands | P1 |
| F03-08 | Validation Commands | P1 |
| F03-09 | Override & Recovery Commands | P1 |

---

## 6. Success Criteria

- [ ] `rice-factor --help` shows all available commands
- [ ] `rice-factor init` creates `.project/` structure
- [ ] All commands integrate with artifact system
- [ ] Output is clear and actionable
- [ ] Error messages are helpful

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone requirements |
| 1.1.0 | 2026-01-10 | User Decision | Updated CLI command from `dev` to `rice-factor` |
| 1.2.0 | 2026-01-10 | Gap Analysis | Added missing commands (review, diagnose, override, refactor check) and F03-09 feature |
