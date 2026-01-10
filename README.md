# Rice-Factor

**LLM-Assisted Development System** - Treating LLMs as compilers, artifacts as IR.

## Overview

Rice-Factor is a language-agnostic, LLM-assisted software development system that:

- Treats **LLMs as compilers** generating structured plan artifacts (JSON), not raw code
- Uses **artifacts as intermediate representations (IR)** - the single source of truth
- Enforces **human approval gates** at all irreversible boundaries
- Implements **TDD at the system level** - tests are locked before implementation
- Provides **full audit trail** - all actions are replayable and reversible

This system feels closer to a **compiler + CI pipeline** than a chat assistant.

## Installation

```bash
# Install with uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Quick Start

```bash
# Initialize a new project
rice-factor init

# Generate a project plan
rice-factor plan project

# Create file scaffolding
rice-factor scaffold

# Generate and lock tests
rice-factor plan tests
rice-factor lock tests

# Plan and implement a file
rice-factor plan impl src/domain/user.rs
rice-factor impl src/domain/user.rs
rice-factor apply

# Run tests
rice-factor test

# View all commands
rice-factor --help
```

## Core Principles

1. **Artifacts over prompts** - Plans are first-class data structures
2. **Plans before code** - Never write code without a plan artifact
3. **Tests before implementation** - TDD enforced at system level
4. **No LLM writes to disk** - LLM only generates JSON plans
5. **All automation is replayable** - Everything is auditable and reversible
6. **Partial failure is acceptable; silent failure is not**
7. **Human approval is mandatory at all irreversible boundaries**

## Documentation

- [CLAUDE.md](CLAUDE.md) - Development guidelines and architecture
- [docs/raw/](docs/raw/) - Original specification documents
- [docs/milestones/](docs/milestones/) - Implementation milestones

## License

MIT
