# Milestone 01: Architecture - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.2.0
> **Status**: In Progress
> **Parent**: [Project Requirements](../../project/requirements.md)

---

## 1. Milestone Objective

Establish the foundational architecture for Rice-Factor, including:
- Project folder structure
- Technology stack selection
- Architectural patterns
- Development environment setup

---

## 2. Scope

### 2.1 In Scope
- Repository structure definition
- Core module organization
- Dependency management setup
- Development tooling configuration
- Basic CLI skeleton

### 2.2 Out of Scope
- Artifact system implementation (Milestone 02)
- LLM integration (Milestone 04)
- Executor implementation (Milestone 05)

---

## 3. Requirements

### 3.1 Architecture

- The project structure shall follow Hexagonal Architecture (Ports & Adapters) principles
- The project structure shall separate concerns into distinct layers (domain, adapters, entrypoints, config)
- The project shall use Python 3.11+ as the implementation language
- The project shall use pyproject.toml for dependency management
- The project shall define type hints for all public interfaces
- The project shall use Dynaconf for 12-Factor App compliant configuration management

### 3.2 Initialization

- While the project is not initialized, the system shall provide a `rice-factor init` command to bootstrap the structure
- While dependencies are not installed, the system shall fail gracefully with installation instructions
- As soon as `rice-factor init` is run, the system shall create the `.project/` directory structure
- As soon as the project is cloned, the system shall be installable via `pip install -e .`

---

## 4. Features in This Milestone

| Feature ID | Feature Name | Priority | Status |
|------------|--------------|----------|--------|
| F01-01 | Project Folder Structure | P0 (Critical) | Done |
| F01-02 | Python Package Setup | P0 (Critical) | Done |
| F01-03 | CLI Skeleton | P0 (Critical) | Done |
| F01-04 | Development Environment | P1 (High) | In Progress |
| F01-05 | Documentation Structure | P1 (High) | In Progress |
| F01-06 | Configuration System | P1 (High) | Done |

---

## 5. Success Criteria

- [x] Repository structure matches hexagonal layout
- [x] `pip install -e .` succeeds
- [x] `rice-factor --help` displays available commands
- [ ] All Python files pass type checking (mypy)
- [ ] Project passes linting (ruff)
- [ ] README documents setup process
- [x] Configuration loads from layered sources (env, files, defaults)

---

## 6. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Python 3.11+ | External | Runtime requirement |
| Typer | Library | CLI framework |
| Pydantic v2 | Library | Data validation |
| Rich | Library | Terminal formatting |
| Dynaconf | Library | 12-Factor configuration with hot reload |
| pytest | Library | Testing framework |
| mypy | Tool | Type checking |
| ruff | Tool | Linting and formatting |
