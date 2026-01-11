# Rice-Factor

A language-agnostic, LLM-assisted software development system that treats LLMs as compilers generating plan artifacts, not direct code generators.

---

## Core Philosophy

- **LLMs as compilers** - Generate structured plans (JSON), not raw code
- **Artifacts as IR** - Plans are first-class intermediate representations
- **Tests as immutable law** - TestPlan is locked and never modified by automation
- **Humans as architects** - Approval required at all irreversible boundaries

---

## Seven Principles (Non-Negotiable)

1. **Artifacts over prompts** - Plans are first-class data structures
2. **Plans before code** - Never write code without a plan artifact
3. **Tests before implementation** - TDD enforced at system level
4. **No LLM writes to disk** - LLM only generates JSON plans
5. **All automation is replayable** - Everything is auditable and reversible
6. **Partial failure is acceptable; silent failure is not**
7. **Human approval is mandatory at all irreversible boundaries**

---

## Documentation

### Original Specification Documents (in `docs/raw/`)

| File | Purpose |
|------|---------|
| `docs/raw/product-requirements-specification.md` | Core vision and system components |
| `docs/raw/implementation-ready-specification.md` | Formal artifact schemas and builder design |
| `docs/raw/REFERENCE-IMPLEMENTATION-SKELETON.md` | Python reference implementation guide |
| `docs/raw/01-end-to-end-design.md` | Full lifecycle workflow (phases 0-9) |
| `docs/raw/02-Formal-Artifact-Schemas.md` | Detailed JSON schema definitions |
| `docs/raw/03-Artifact-Builder.md` | LLM compiler pass design |
| `docs/raw/04-repository-and-system-layout.md` | Directory structure and ownership |
| `docs/raw/05-full-cli-agent-workflow-end-to-end-usage.md` | CLI usage patterns |
| `docs/raw/Phase-01-mvp.md` | MVP scope and exit criteria |
| `docs/raw/Item-01-mvp-example-walkthrough-end-to-end.md` | Concrete walkthrough |
| `docs/raw/item-02-executor-design-and-pseudocode.md` | Executor interfaces |
| `docs/raw/item-03-ci-cd-pipeline-and-automation-strategy.md` | CI/CD integration |
| `docs/raw/item-04-Multi-Agent-Coordination-Model-and-Run-Modes.md` | Agent topology |
| `docs/raw/item-05-Failure-Recovery-and-Resilience-Model.md` | Error handling |
| `docs/raw/06-tools-to-integrte-with-or-learn-from.md` | Tool integration |

### Milestone Documentation

| Path | Purpose |
|------|---------|
| `docs/milestones/*/requirements.md` | Milestone requirements |
| `docs/milestones/*/design.md` | Milestone design |
| `docs/milestones/*/features/*/tasks.md` | Feature task breakdown |

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.11+ | Best LLM ecosystem, rapid development, Pydantic v2 |
| **Architecture** | Hexagonal (Ports & Adapters) | Pluggable LLM/executor adapters, easy testing |
| **CLI Framework** | Typer | Type hints, auto-completion, minimal boilerplate |
| **CLI Command** | `rice-factor` | Project-named command |
| **Validation** | Pydantic v2 + jsonschema | Type-safe models + schema validation |
| **LLM Providers** | Pluggable (Claude, OpenAI, local) | Abstract port with swappable adapters |
| **Diff** | git diff/apply | Standard, safe, rollback-friendly |
| **Tests** | Native runners | cargo test, go test, mvn test |

---

## Project Structure (Hexagonal Architecture)

```
rice_factor/                           # Main package
├── domain/                            # DOMAIN (innermost - NO external deps)
│   ├── artifacts/                     # Artifact models (Pydantic)
│   ├── ports/                         # Port definitions (interfaces)
│   │   ├── llm.py                     # LLMPort protocol
│   │   ├── storage.py                 # StoragePort protocol
│   │   ├── executor.py                # ExecutorPort protocol
│   │   └── validator.py               # ValidatorPort protocol
│   ├── services/                      # Domain services
│   └── failures/                      # Failure models
│
├── adapters/                          # ADAPTERS (implement ports)
│   ├── llm/                           # LLM adapters (Claude, OpenAI, local)
│   ├── storage/                       # Storage adapters (filesystem)
│   ├── executors/                     # Executor adapters
│   └── validators/                    # Validator adapters
│
├── entrypoints/                       # APPLICATION ENTRY POINTS
│   └── cli/                           # CLI adapter (Typer)
│       ├── main.py                    # `rice-factor` command
│       └── commands/                  # Subcommands
│
└── config/                            # Configuration & DI
    ├── settings.py                    # Environment config
    └── container.py                   # Adapter wiring

# Supporting directories
schemas/                               # JSON Schema definitions
tests/                                 # Test suites
docs/                                  # Documentation

# Runtime directories (in user repos)
.project/                              # Human-owned context
artifacts/                             # System-owned IR
audit/                                 # Audit trail
```

---

## CLI Commands (MVP)

```bash
rice-factor init                    # Create .project/, run questionnaire
rice-factor plan project            # Generate ProjectPlan
rice-factor scaffold                # Create empty files from ScaffoldPlan
rice-factor plan tests              # Generate TestPlan
rice-factor lock tests              # Lock tests (immutable)
rice-factor plan impl <file>        # Generate ImplementationPlan
rice-factor impl <file>             # Generate diff for file
rice-factor apply                   # Apply approved diff
rice-factor test                    # Run test suite
rice-factor approve <artifact>      # Approve artifact
rice-factor plan refactor <goal>    # Generate RefactorPlan
rice-factor refactor dry-run        # Preview refactor
```

---

## Milestones

### MVP Complete (01-07)

| # | Milestone | Status | Description |
|---|-----------|--------|-------------|
| 01 | Architecture | Complete | Hexagonal structure, tooling setup |
| 02 | Artifact System | Complete | Models, schemas, validation, storage |
| 03 | CLI Core | Complete | All `rice-factor` commands |
| 04 | LLM Compiler | Complete | Artifact builder, provider adapters |
| 05 | Executor Engine | Complete | Scaffold, diff, refactor executors |
| 06 | Validation Engine | Complete | Test runner, lint, arch rules |
| 07 | MVP Integration | Complete | End-to-end workflow |

### Post-MVP Complete (08-13)

| # | Milestone | Status | Priority | Description |
|---|-----------|--------|----------|-------------|
| 08 | CI/CD Integration | Complete | P0 | CI pipeline, artifact validation, invariant enforcement |
| 09 | Drift Detection | Complete | P1 | Drift detection, reconciliation, ReconciliationPlan |
| 10 | Artifact Lifecycle | Complete | P1 | Aging system, expiration policies, review prompts |
| 11 | Enhanced Intake | Complete | P1 | decisions.md, blocking questionnaire, glossary validation |
| 12 | Language Refactoring | Complete | P2 | OpenRewrite, gopls, rust-analyzer, jscodeshift adapters |
| 13 | Multi-Agent | Complete | P2 | Run modes B-E, agent roles, orchestration |

### Future Milestones (14-22)

| # | Milestone | Status | Priority | Description |
|---|-----------|--------|----------|-------------|
| 14 | Full Capability Registry | Planned | P0 | Python/Ruby/PHP adapters, full extract_interface & enforce_dependency |
| 15 | Local LLM Orchestration | Planned | P0 | Ollama, vLLM, LocalAI adapters, provider fallback, model registry |
| 16 | Production Hardening | Planned | P0 | Rate limiting, cost tracking, remote storage, webhooks, metrics |
| 17 | Advanced Resilience | Planned | P1 | State reconstruction, override tracking, orphan detection, migration |
| 18 | Performance & Parallelism | Planned | P1 | Parallel execution, artifact caching, incremental validation |
| 19 | Advanced Refactoring | Planned | P2 | extract_interface, enforce_dependency, cross-file refactoring |
| 20 | Multi-Language Support | Planned | P2 | Polyglot repos, cross-language deps, unified test aggregation |
| 21 | Developer Experience | Planned | P2 | VS Code extension, TUI mode, project templates, visualization |
| 22 | Web Interface | Planned | P3 | Web dashboard, diff review UI, team approvals, history browser |

> See `docs/gap-analysis-v3.md` for detailed gap analysis and feature breakdown.

---

## Ownership Rules

| Path | Owner | Automation |
|------|-------|------------|
| `.project/` | Human | NEVER |
| `artifacts/` | System | Only via builder |
| `src/` | Mixed | Via approved plans |
| `tests/` | Mixed | LOCKED after TestPlan |
| `audit/` | System | Append-only |
| `rice_factor/` | Human | Development code |
| `docs/` | Human | Documentation |

---

## Hexagonal Architecture Rules

| Layer | Dependencies | External Libraries |
|-------|--------------|-------------------|
| `domain/` | None (stdlib only) | NO |
| `adapters/` | `domain/` | YES (anthropic, openai, etc.) |
| `entrypoints/` | `domain/`, `adapters/` | YES (typer, rich) |
| `config/` | All layers | YES |

**Key Rule**: Domain has NO external dependencies. All external integrations go through adapters.

---

## Configuration Management

Rice-Factor follows **12-Factor App** methodology for configuration:

- **No hardcoded values** - All behavior configurable at runtime
- **Layered priority**: CLI args → Env vars → Project config → User config → Defaults
- **Hot reload** - Config changes without restart (Dynaconf)

---

## Development Workflow

### When Implementing Features

1. **Read the original spec first**: Check `docs/raw/` for authoritative requirements
2. **Check milestone docs**: `docs/milestones/<milestone>/` for task breakdown
3. **Cross-reference**: Verify implementation matches original spec intent
4. **Track progress**: Update `docs/gap-analysis-v2.md` when completing items

### Before Moving to Next Milestone

1. Verify all tasks in current milestone are complete
2. Run `docs/gap-analysis-v2.md` cross-check
3. Ensure all tests pass
4. Update milestone status in this file

### Gap Analysis Documents

| Document | Purpose |
|----------|---------|
| `docs/gap-analysis-v1-mvp.md` | MVP completion report (Milestones 01-07) |
| `docs/gap-analysis-v2.md` | Post-MVP gap analysis (Milestones 08-13) |
| `docs/gap-analysis-v3.md` | Future milestones assessment (Milestones 14-22) - includes capability registry & local LLM research |
