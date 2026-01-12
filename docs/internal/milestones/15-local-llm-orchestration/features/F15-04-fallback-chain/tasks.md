# F15-04: Provider Fallback Chain - Tasks

---

## Tasks

### T15-04-01: Create ProviderSelector Class
- [x] Files: `rice_factor/adapters/llm/provider_selector.py`
- Created ProviderSelector with ProviderConfig, SelectionResult, AllProvidersFailedError

### T15-04-02: Implement Priority-Based Selection
- [x] Files: `rice_factor/adapters/llm/provider_selector.py`
- PRIORITY strategy selects highest priority provider first

### T15-04-03: Implement Round-Robin Selection
- [x] Files: `rice_factor/adapters/llm/provider_selector.py`
- ROUND_ROBIN strategy rotates through providers

### T15-04-04: Implement Cost-Based Selection
- [x] Files: `rice_factor/adapters/llm/provider_selector.py`
- COST_BASED strategy selects cheapest provider

### T15-04-05: Implement Automatic Retry Logic
- [x] Files: `rice_factor/adapters/llm/provider_selector.py`
- Fallback on failure with configurable max_retries
- Both sync and async generate methods

### T15-04-06: Add Fallback Configuration Schema
- [x] Files: `rice_factor/adapters/llm/provider_selector.py`
- create_provider_selector_from_config() reads llm.fallback config
- Note: YAML config file optional - uses settings-based configuration

### T15-04-07: Unit Tests for Provider Selector
- [x] Files: `tests/unit/adapters/llm/test_provider_selector.py`
- 35 tests covering all strategies, fallback, enable/disable, config

---

## Actual Test Count: 35

