# Raw Specification Documents

This folder contains the **original specification documents** that define the Rice-Factor system. These are the raw design documents created during the initial specification phase.

## Document Index

| File | Purpose |
|------|---------|
| `product-requirements-specification.md` | Core vision, principles, and system components |
| `implementation-ready-specification.md` | Formal artifact schemas and builder design |
| `01-end-to-end-design.md` | Full lifecycle workflow (phases 0-9) |
| `02-Formal-Artifact-Schemas.md` | Detailed JSON schema definitions |
| `03-Artifact-Builder.md` | LLM compiler pass design |
| `04-repository-and-system-layout.md` | Directory structure and ownership rules |
| `05-full-cli-agent-workflow-end-to-end-usage.md` | CLI usage patterns and commands |
| `06-tools-to-integrte-with-or-learn-from.md` | Tool integration recommendations |
| `Phase-01-mvp.md` | MVP scope and exit criteria |
| `Item-01-mvp-example-walkthrough-end-to-end.md` | Concrete MVP walkthrough example |
| `item-02-executor-design-and-pseudocode.md` | Executor interfaces and pseudocode |
| `item-03-ci-cd-pipeline-and-automation-strategy.md` | CI/CD integration strategy |
| `item-04-Multi-Agent-Coordination-Model-and-Run-Modes.md` | Multi-agent topology and run modes |
| `item-05-Failure-Recovery-and-Resilience-Model.md` | Error handling and recovery |
| `REFERENCE-IMPLEMENTATION-SKELETON.md` | Python reference implementation guide |

## Relationship to SDD Documentation

These raw documents have been processed into structured **Spec-Driven Development (SDD)** documentation:

- **Project-level**: `docs/project/requirements.md` and `docs/project/design.md`
- **Milestone-level**: `docs/milestones/*/requirements.md` and `design.md`
- **Feature-level**: `docs/milestones/*/features/*/tasks.md`

The SDD documentation uses **EARS notation** for requirements and provides actionable task breakdowns.

## Usage

- **Reference**: Consult these documents when clarifying original intent
- **Gap Analysis**: Compare against SDD docs to ensure completeness
- **Context**: Provide background for architectural decisions

These documents are **read-only** and should not be modified. Any updates should be made to the SDD documentation in `docs/project/` and `docs/milestones/`.
