# Feature: F01-04 Development Environment

## Status: Pending

## Description
Configure development tooling for code quality and testing.

## Tasks
- [ ] Create `.pre-commit-config.yaml` with ruff and mypy hooks
- [ ] Create `tests/conftest.py` with pytest fixtures
- [ ] Create sample unit test in `tests/unit/`
- [ ] Verify `pytest` runs successfully
- [ ] Verify `mypy rice_factor` passes
- [ ] Verify `ruff check .` passes
- [ ] Create `.gitignore` with Python and IDE patterns
- [ ] Create `.python-version` file (3.11+)

## Acceptance Criteria
- `pytest` discovers and runs tests
- `mypy rice_factor` reports no errors
- `ruff check .` reports no violations
- Pre-commit hooks run on git commit

## Progress Log
| Date | Update |
|------|--------|
| 2026-01-10 | Created task file |
