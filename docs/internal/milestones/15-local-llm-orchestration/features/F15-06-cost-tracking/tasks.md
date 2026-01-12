# F15-06: Cost & Latency Tracking - Tasks

---

## Tasks

### T15-06-01: Create UsageTracker Class
- [x] Files: `rice_factor/adapters/llm/usage_tracker.py`
- UsageTracker with UsageRecord and ProviderStats dataclasses

### T15-06-02: Implement Token Counting
- [x] Files: `rice_factor/adapters/llm/usage_tracker.py`
- count_tokens() with simple heuristic (~4 chars per token)
- record_with_tokens() for provider-reported token counts

### T15-06-03: Implement Cost Calculation
- [x] Files: `rice_factor/adapters/llm/usage_tracker.py`
- Automatic cost calculation based on token counts and rates
- total_cost(), by_provider(), by_model() methods

### T15-06-04: Implement Latency Metrics
- [x] Files: `rice_factor/adapters/llm/usage_tracker.py`
- ProviderStats with avg/min/max latency tracking

### T15-06-05: Implement Prometheus Export
- [x] Files: `rice_factor/adapters/llm/usage_tracker.py`
- export_prometheus() for llm_cost_usd, llm_tokens_total, llm_requests_total, llm_latency_ms
- export_json() for JSON-serializable metrics

### T15-06-06: Add CLI Command `rice-factor usage`
- [x] Files: `rice_factor/entrypoints/cli/commands/usage.py`
- `usage show`: Display usage statistics by provider/model
- `usage export`: Export as JSON or Prometheus format
- `usage clear`: Reset usage tracking

### T15-06-07: Unit Tests for Usage Tracker
- [x] Files: `tests/unit/adapters/llm/test_usage_tracker.py`
- 23 tests covering all functionality

---

## Actual Test Count: 23

