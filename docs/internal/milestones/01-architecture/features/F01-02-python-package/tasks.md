# Feature: F01-02 Python Package Setup

## Status: Pending

## Description
Configure Python packaging with pyproject.toml for the rice-factor CLI tool.

## Tasks
- [ ] Create `pyproject.toml` with project metadata
- [ ] Define core dependencies (typer, pydantic, rich, dynaconf, pyyaml, jsonschema)
- [ ] Define optional dependencies for LLM providers (anthropic, openai)
- [ ] Define dev dependencies (pytest, pytest-cov, mypy, ruff)
- [ ] Configure entry point: `rice-factor = "rice_factor.entrypoints.cli.main:app"`
- [ ] Configure mypy settings (strict mode, Python 3.11)
- [ ] Configure ruff settings (line length 100, py311 target)
- [ ] Verify `pip install -e .` works

## Acceptance Criteria
- `pip install -e .` succeeds without errors
- `rice-factor --help` runs after installation
- All dependencies are pinned with minimum versions

## Progress Log
| Date | Update |
|------|--------|
| 2026-01-10 | Created task file |
