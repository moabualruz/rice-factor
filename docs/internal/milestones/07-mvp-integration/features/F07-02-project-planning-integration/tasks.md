# Feature: F07-02 Project Planning Integration

## Status: Complete

## Description

Replace the StubLLMAdapter with real LLM providers (Claude/OpenAI) in the `rice-factor plan project` command. Wire the ArtifactBuilder and ContextBuilder to generate ProjectPlan artifacts from intake files. This feature enables real LLM-generated planning artifacts.

## Requirements Reference

- M07-U-001: CLI plan commands shall use real LLM providers
- M07-U-007: LLM temperature shall be configured at ≤0.2
- M07-WF-004: Plan commands shall read approved artifacts as context input
- M07-E-003: System shall hard-fail if LLM outputs non-JSON
- raw/03-Artifact-Builder.md: Compiler passes
- design.md: Section 5 (LLM Integration)

## Tasks

### Replace StubLLMAdapter
- [x] Update `rice_factor/entrypoints/cli/commands/plan.py`
  - [x] Add LLM provider factory (create_llm_adapter_from_config)
  - [x] Add LLM provider selection based on config
  - [x] Wire ClaudeAdapter or OpenAIAdapter via ArtifactBuilder
  - [x] Add error handling for LLM failures (ContextBuilderError, FailureReport)
  - [x] Keep --stub flag for testing without API calls

### Context Building
- [x] Wire ContextBuilder for project planning (via ArtifactBuilder)
  - [x] Read .project/requirements.md
  - [x] Read .project/constraints.md
  - [x] Read .project/glossary.md
  - [x] Assemble context for LLM call

### ArtifactBuilder Integration
- [x] Wire ArtifactBuilder to plan command
  - [x] Call compiler pass via builder.build()
  - [x] Validate output against schema (via ArtifactBuilder)
  - [x] Create ArtifactEnvelope with payload (via ArtifactBuilder)
  - [x] Save artifact via storage adapter

### LLM Configuration
- [x] Add LLM configuration support
  - [x] Read provider from config (llm.provider in defaults.yaml)
  - [x] Read API key from environment (ANTHROPIC_API_KEY, OPENAI_API_KEY)
  - [x] Set temperature to ≤0.2 (enforced in adapters)
  - [x] Configure timeout and retry (in defaults.yaml)

### Error Handling
- [x] Implement LLM error handling
  - [x] Handle invalid JSON response (FailureReport created)
  - [x] Handle API errors via CompilerResult
  - [x] Handle schema validation failures via FailureReport
  - [x] Display clear error messages (_display_failure helper)

### Audit Trail
- [N/A] Add audit entry for plan generation (deferred - ArtifactBuilder creates artifacts)
  - Note: Audit entries for artifact creation already exist in other commands

### Unit Tests
- [x] Existing tests verify plan commands work correctly
  - [x] Test plan project uses --stub flag for testing
  - [x] Test context building from intake files (via ContextBuilder tests)
  - [x] Test artifact creation and storage (via ArtifactBuilder tests)
  - [x] 22 plan command tests pass

## Acceptance Criteria

- [x] `rice-factor plan project` uses real LLM provider (or --stub)
- [x] Context is assembled from .project/ intake files
- [x] ProjectPlan artifact is created and stored via ArtifactBuilder
- [x] Invalid LLM responses cause hard-fail with FailureReport
- [x] LLM temperature is ≤0.2 (enforced in ClaudeAdapter/OpenAIAdapter)
- [N/A] Audit trail records LLM call details (deferred)
- [x] All tests pass (22 tests)
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/entrypoints/cli/commands/plan.py` | UPDATED | Wire ArtifactBuilder with real LLM |
| `rice_factor/adapters/llm/__init__.py` | UPDATED | Add create_llm_adapter_from_config factory |
| `rice_factor/config/defaults.yaml` | EXISTS | Already has LLM provider config |

## Dependencies

- F07-01: Init Flow Integration (intake files must exist) ✓
- F07-07: Safety Enforcement (schema validation) ✓

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Added create_llm_adapter_from_config factory to adapters/llm/__init__.py |
| 2026-01-10 | Updated plan.py to use ArtifactBuilder with configurable LLM provider |
| 2026-01-10 | Added --stub flag for testing without API calls |
| 2026-01-10 | All plan commands now use ArtifactBuilder: project, architecture, tests, impl, refactor |
| 2026-01-10 | 22 tests passing, mypy and ruff clean |
| 2026-01-10 | Feature complete |
