# F20-04: Language-Specific Artifact Sections - Tasks

## Tasks
### T20-04-01: Extend ProjectPlan Schema - DONE
### T20-04-02: Add Per-Language Modules - DONE
### T20-04-03: Update Validators - DONE
### T20-04-04: Unit Tests - DONE

## Actual Test Count: 23

## Implementation Notes
- Extended `rice_factor/domain/artifacts/payloads/project_plan.py`:
  - LanguageConfig: Per-language settings (name, version, framework, package_manager, test_runner, build_command, source_dir)
  - LanguageModule: Language-specific modules (name, language, domain, path, entry_point, dependencies)
  - IntegrationConfig: Cross-language integrations (type, provider_language, consumer_language, endpoint, protocol)
  - PolyglotConfig: Container for all polyglot settings (primary_language, language_configs, language_modules, integrations)
  - Added optional `polyglot` field to ProjectPlanPayload
- Updated `schemas/project_plan.schema.json` with matching JSON Schema definitions
- Updated `rice_factor/domain/artifacts/payloads/__init__.py` with exports
- Added tests in `tests/unit/domain/artifacts/payloads/test_payloads.py` (21 new tests)
- Added schema validation tests in `tests/unit/adapters/validators/test_schema_validator.py` (2 new tests)
