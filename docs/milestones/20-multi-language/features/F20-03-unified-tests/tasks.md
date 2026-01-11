# F20-03: Unified Test Aggregation - Tasks

## Tasks
### T20-03-01: Create UnifiedTestRunner Service
- [ ] Define TestRunnerConfig model with language, command, args, env, timeout
- [ ] Implement TestRunnerRegistry for per-language configurations
- [ ] Create UnifiedTestRunner that dispatches to language-specific runners

### T20-03-02: Implement Multi-Runner Orchestration
- [ ] Run language-specific test runners in sequence or parallel
- [ ] Handle runner failures gracefully (partial success support)
- [ ] Implement timeout handling per runner

### T20-03-03: Implement Result Aggregation
- [ ] Aggregate test results from multiple runners
- [ ] Normalize output formats (JUnit XML, JSON, TAP)
- [ ] Generate unified summary report

### T20-03-04: Implement Per-Language Test Runner Configuration (GAP-SPEC-004)
- [ ] YAML configuration schema for test runner overrides
- [ ] Language-specific test command customization
- [ ] Support for custom test discovery patterns
- [ ] Environment variable configuration per language

### T20-03-05: Unit Tests
- [ ] Test UnifiedTestRunner with mock runners
- [ ] Test result aggregation logic
- [ ] Test configuration loading and validation

## Estimated Test Count: ~8

## Implementation Notes

### Test Runner Configuration Schema
```yaml
# .project/test-runners.yaml
runners:
  python:
    command: pytest
    args: ["-v", "--tb=short"]
    timeout: 300
  javascript:
    command: npm
    args: ["test"]
    timeout: 120
  java:
    command: mvn
    args: ["test"]
    timeout: 600
```

### References
- GAP-SPEC-004: Test Runner per-language configuration
