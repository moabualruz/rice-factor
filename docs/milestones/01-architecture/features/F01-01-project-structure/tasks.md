# Feature: F01-01 Project Folder Structure

## Status: Pending

## Description
Create the hexagonal architecture folder structure for rice-factor.

## Tasks
- [ ] Create `rice_factor/` package root
- [ ] Create `rice_factor/domain/` with subdirectories (artifacts, ports, services, failures)
- [ ] Create `rice_factor/adapters/` with subdirectories (llm, storage, executors, validators)
- [ ] Create `rice_factor/entrypoints/cli/` with commands directory
- [ ] Create `rice_factor/config/` directory
- [ ] Create `schemas/` directory for JSON schemas
- [ ] Create `tests/` directory structure (unit, integration, e2e)
- [ ] Add `__init__.py` files to all packages

## Acceptance Criteria
- Directory structure matches `docs/milestones/01-architecture/design.md` Section 2.1
- All `__init__.py` files present
- No circular import issues

## Progress Log
| Date | Update |
|------|--------|
| 2026-01-10 | Created task file |
