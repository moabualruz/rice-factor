# Internal Documentation

This section contains internal project documentation, including original specifications, milestone tracking, and gap analysis reports.

!!! note "For Contributors"
    This documentation is primarily for contributors and maintainers. For user documentation, see the [Getting Started](../guides/getting-started/installation.md) guide.

## Contents

### Original Specifications (`raw/`)

The foundational specification documents:

| Document | Description |
|----------|-------------|
| [Product Requirements](raw/product-requirements-specification.md) | Core vision and system components |
| [Implementation Spec](raw/implementation-ready-specification.md) | Formal artifact schemas and builder design |
| [Reference Implementation](raw/REFERENCE-IMPLEMENTATION-SKELETON.md) | Python reference implementation guide |
| [End-to-End Design](raw/01-end-to-end-design.md) | Full lifecycle workflow (phases 0-9) |
| [Formal Artifact Schemas](raw/02-Formal-Artifact-Schemas.md) | Detailed JSON schema definitions |
| [Artifact Builder](raw/03-Artifact-Builder.md) | LLM compiler pass design |
| [Repository Layout](raw/04-repository-and-system-layout.md) | Directory structure and ownership |
| [CLI Agent Workflow](raw/05-full-cli-agent-workflow-end-to-end-usage.md) | CLI usage patterns |
| [MVP Phase](raw/Phase-01-mvp.md) | MVP scope and exit criteria |
| [MVP Walkthrough](raw/Item-01-mvp-example-walkthrough-end-to-end.md) | Concrete walkthrough |
| [Executor Design](raw/item-02-executor-design-and-pseudocode.md) | Executor interfaces |
| [CI/CD Strategy](raw/item-03-ci-cd-pipeline-and-automation-strategy.md) | CI/CD integration |
| [Multi-Agent Model](raw/item-04-Multi-Agent-Coordination-Model-and-Run-Modes.md) | Agent topology |
| [Failure Recovery](raw/item-05-Failure-Recovery-and-Resilience-Model.md) | Error handling |
| [Tool Integration](raw/06-tools-to-integrte-with-or-learn-from.md) | External tool integration |

### Milestones (`milestones/`)

Detailed milestone documentation:

- **Milestone 01-07**: MVP (Architecture, Artifacts, CLI, LLM, Executor, Validation, Integration)
- **Milestone 08-13**: Post-MVP (CI/CD, Drift, Lifecycle, Intake, Refactoring, Multi-Agent)
- **Milestone 14-22**: Advanced (Registry, AST/LSP, Local LLM, Hardening, Resilience, Performance, Refactoring, Multi-Language, DX, Web)

Each milestone contains:
- `requirements.md` - Feature requirements
- `design.md` - Technical design
- `features/*/tasks.md` - Task breakdown

### Gap Analysis (`gap-analysis/`)

| Document | Coverage |
|----------|----------|
| [Gap Analysis v1](gap-analysis/gap-analysis-v1-mvp.md) | MVP completion (Milestones 01-07) |
| [Gap Analysis v2](gap-analysis/gap-analysis-v2.md) | Post-MVP gaps (Milestones 08-13) |
| [Gap Analysis v3](gap-analysis/gap-analysis-v3.md) | Future assessment (Milestones 14-22) |

### Project Documentation (`project/`)

Project-level documentation and planning materials.

## Quick Reference

### Milestone Status

| Range | Status | Description |
|-------|--------|-------------|
| 01-07 | Complete | MVP features |
| 08-13 | Complete | Post-MVP features |
| 14-22 | Complete | Advanced features |

### Key Design Decisions

1. **Hexagonal Architecture** - Clean separation, testability
2. **Artifacts as IR** - Plans are intermediate representations
3. **TDD Enforcement** - Tests locked before implementation
4. **Human Approval** - Required at all irreversible boundaries

### Architecture Layers

```
┌─────────────────────────────────────────┐
│            Entrypoints                  │
│       (CLI, TUI, Web, API)              │
├─────────────────────────────────────────┤
│             Adapters                    │
│   (LLM, Storage, Executor, Validator)   │
├─────────────────────────────────────────┤
│              Domain                     │
│   (Ports, Services, Artifacts, Models)  │
└─────────────────────────────────────────┘
```

## Navigation

- [Back to Documentation Home](../index.md)
- [User Guides](../guides/getting-started/installation.md)
- [Reference](../reference/cli/commands.md)
- [Contributing](../contributing/README.md)
