# F15-05: Model Registry - Tasks

---

## Tasks

### T15-05-01: Create Model Registry YAML Schema
- [x] Files: `rice_factor/domain/services/model_registry.py`
- DEFAULT_MODELS dict with schema for cloud and local models
- ModelCapability enum: CODE, CHAT, REASONING, VISION, FUNCTION_CALLING, JSON_MODE

### T15-05-02: Create ModelRegistry Service
- [x] Files: `rice_factor/domain/services/model_registry.py`
- ModelInfo dataclass with all model metadata
- ModelRegistry class with register/unregister/get methods

### T15-05-03: Implement Model Capability Queries
- [x] Files: `rice_factor/domain/services/model_registry.py`
- get_by_capability, get_by_provider, get_local_models, get_cloud_models
- get_available, get_by_context_length, get_cheapest

### T15-05-04: Implement Auto-Sync with Providers
- [x] Files: `rice_factor/domain/services/model_registry.py`
- sync_with_provider() updates availability based on discovered models
- Automatically adds unknown models to registry

### T15-05-05: Add CLI Command `rice-factor models`
- [x] Files: `rice_factor/entrypoints/cli/commands/models.py`
- Lists all registered LLM models with capabilities, context length, cost
- Filters: --provider, --capability, --local, --cloud, --available, --json

### T15-05-06: Unit Tests for Model Registry
- [x] Files: `tests/unit/domain/services/test_model_registry.py`
- 36 tests covering all functionality

---

## Actual Test Count: 36

