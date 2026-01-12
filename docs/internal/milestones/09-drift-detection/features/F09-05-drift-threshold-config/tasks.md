# Feature F09-05: Drift Threshold Configuration - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-05-01 | Create DriftConfig model | **Complete** | P0 |
| T09-05-02 | Add YAML configuration support | **Complete** | P0 |
| T09-05-03 | Integrate with DriftDetector | **Complete** | P0 |
| T09-05-04 | Add CLI override options | **Complete** | P1 |
| T09-05-05 | Document configuration | Deferred | P1 |
| T09-05-06 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T09-05-01: Create DriftConfig Model

**Objective**: Define configuration model for drift detection.

**Files**:
- [x] `rice_factor/domain/drift/models.py` (DriftConfig dataclass)

**Implementation**:
- [x] DriftConfig dataclass with all fields
- [x] drift_threshold, refactor_threshold, refactor_window_days
- [x] code_patterns, ignore_patterns, source_dirs
- [x] should_ignore() method for pattern matching
- [x] matches_code_pattern() method for code file detection

**Acceptance Criteria**:
- [x] All settings have sensible defaults
- [x] Dataclass is serializable
- [x] Type hints for all fields

---

### T09-05-02: Add YAML Configuration Support

**Objective**: Load drift config from project YAML file.

**Files Modified**:
- [x] `rice_factor/domain/drift/models.py` (added from_file classmethod)

**Configuration File Location**: `.project/config.yaml`

**Format**:
```yaml
drift:
  drift_threshold: 5
  refactor_threshold: 4
  refactor_window_days: 60
  code_patterns:
    - "*.py"
    - "*.ts"
  ignore_patterns:
    - "*_test.py"
    - "migrations/*"
```

**Implementation**:
- [x] from_file() classmethod that loads from YAML
- [x] Supports 'drift' section or root-level config
- [x] Gracefully handles missing/invalid files

**Acceptance Criteria**:
- [x] Missing file returns defaults
- [x] Partial config merged with defaults
- [x] Invalid YAML handled gracefully

---

### T09-05-03: Integrate with DriftDetector

**Objective**: Wire configuration into drift detection.

**Files**:
- [x] `rice_factor/adapters/drift/detector.py` (DriftDetectorAdapter)

**Implementation**:
- [x] DriftDetectorAdapter accepts DriftConfig in constructor
- [x] Uses config.code_patterns for file scanning
- [x] Uses config.ignore_patterns for filtering
- [x] Uses config.source_dirs in full_analysis()
- [x] Uses config.drift_threshold for report threshold
- [x] Uses config.refactor_threshold and refactor_window_days

**Acceptance Criteria**:
- [x] Detector uses config values
- [x] Config can be passed to adapter
- [x] Defaults used when config not provided

---

### T09-05-04: Add CLI Override Options

**Objective**: Allow CLI flags to override config.

**Files**:
- [x] `rice_factor/entrypoints/cli/commands/audit.py`
- [x] `rice_factor/entrypoints/cli/commands/reconcile.py`

**Implementation**:
- [x] `--threshold` option to override drift_threshold
- [x] `--code-dir` option to override source_dirs
- [x] CLI arguments take precedence over defaults
- [x] Help text documents all options

**Acceptance Criteria**:
- [x] CLI overrides take precedence
- [x] None means use config value
- [x] Help text explains behavior

---

### T09-05-05: Document Configuration

**Objective**: Document all configuration options.

**Files to Create/Modify**:
- [ ] Add section to project README
- [ ] Create sample `.project/config.yaml`

**Documentation Content**:
- [ ] All config keys explained
- [ ] Default values listed
- [ ] Example configurations
- [ ] CLI override examples

**Acceptance Criteria**:
- [ ] All options documented
- [ ] Examples are runnable

---

### T09-05-06: Write Unit Tests

**Objective**: Test configuration loading and merging.

**Files**:
- [x] `tests/unit/domain/drift/test_models.py` (8 new tests added)

**Test Cases**:
- [x] test_from_file_missing_file - defaults returned
- [x] test_from_file_valid_yaml - all values loaded
- [x] test_from_file_partial_config - merged with defaults
- [x] test_from_file_invalid_yaml - graceful fallback
- [x] test_from_file_empty_file - defaults returned
- [x] test_from_file_root_level_config - no 'drift' section
- [x] test_from_file_with_string_path - accepts string paths

**Acceptance Criteria**:
- [x] All loading scenarios tested (24 tests total in file)
- [x] Override behavior verified

---

## 3. Task Dependencies

```
T09-05-01 (Model) ──→ T09-05-02 (YAML) ──→ T09-05-03 (Integration)
                                                  │
                                    ┌─────────────┼─────────────┐
                                    ↓             ↓             ↓
                           T09-05-04 (CLI) T09-05-05 (Docs) T09-05-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T09-05-01 | Low | Dataclass |
| T09-05-02 | Low | YAML loading |
| T09-05-03 | Medium | Wiring |
| T09-05-04 | Low | CLI options |
| T09-05-05 | Low | Documentation |
| T09-05-06 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.0.1 | 2026-01-11 | Implementation | Core tasks complete - 24 tests passing, T09-05-05 (docs) deferred |
