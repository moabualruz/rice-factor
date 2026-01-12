# Feature: F01-06 Configuration System

## Status: Pending

## Description
Implement 12-Factor App compliant configuration using Dynaconf.

## Tasks
- [ ] Create `rice_factor/config/settings.py` with Dynaconf setup
- [ ] Create `rice_factor/config/defaults.yaml` with default values
- [ ] Create `rice_factor/domain/ports/config.py` with ConfigPort protocol
- [ ] Create `rice_factor/adapters/config/dynaconf_adapter.py`
- [ ] Implement layered config priority:
  - [ ] CLI arguments (highest)
  - [ ] Environment variables (RICE_* prefix)
  - [ ] Project config (.rice-factor.yaml)
  - [ ] User config (~/.rice-factor/config.yaml)
  - [ ] Defaults (lowest)
- [ ] Add config reload capability for hot reload
- [ ] Write unit tests for configuration loading

## Acceptance Criteria
- Configuration loads from all sources in correct priority
- Environment variables override file config
- `settings.reload()` updates values without restart
- All settings have documented defaults

## Progress Log
| Date | Update |
|------|--------|
| 2026-01-10 | Created task file |
