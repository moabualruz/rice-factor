# Feature F09-05: Drift Threshold Configuration - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-05-01 | Create DriftConfig model | Pending | P0 |
| T09-05-02 | Add YAML configuration support | Pending | P0 |
| T09-05-03 | Integrate with DriftDetector | Pending | P0 |
| T09-05-04 | Add CLI override options | Pending | P1 |
| T09-05-05 | Document configuration | Pending | P1 |
| T09-05-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T09-05-01: Create DriftConfig Model

**Objective**: Define configuration model for drift detection.

**Files to Create**:
- [ ] `rice_factor/config/drift_config.py`

**Implementation**:
```python
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DriftConfig:
    """Configuration for drift detection."""

    # Main threshold
    drift_threshold: int = 3

    # Code scanning
    code_patterns: list[str] = field(default_factory=lambda: [
        "*.py", "*.ts", "*.js", "*.go", "*.rs", "*.java",
    ])
    ignore_patterns: list[str] = field(default_factory=lambda: [
        "*_test.py", "test_*.py", "__pycache__/*",
    ])

    # Refactor hotspot settings
    refactor_threshold: int = 3
    refactor_window_days: int = 30
```

**Acceptance Criteria**:
- [ ] All settings have sensible defaults
- [ ] Dataclass is serializable
- [ ] Type hints for all fields

---

### T09-05-02: Add YAML Configuration Support

**Objective**: Load drift config from project YAML file.

**Files to Modify**:
- [ ] `rice_factor/config/drift_config.py`

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
```python
@classmethod
def from_file(cls, path: Path) -> "DriftConfig":
    """Load config from YAML file."""
    if not path.exists():
        return cls()

    import yaml
    with open(path) as f:
        data = yaml.safe_load(f)

    drift_data = data.get("drift", {})
    return cls(**drift_data)
```

**Acceptance Criteria**:
- [ ] Missing file returns defaults
- [ ] Partial config merged with defaults
- [ ] Invalid YAML handled gracefully

---

### T09-05-03: Integrate with DriftDetector

**Objective**: Wire configuration into drift detection.

**Files to Modify**:
- [ ] `rice_factor/domain/services/drift_detector.py`
- [ ] `rice_factor/config/container.py`

**Implementation**:
```python
class DriftDetector:
    def __init__(
        self,
        artifact_store: StoragePort,
        audit_reader: AuditReaderPort,
        config: DriftConfig,
    ) -> None:
        self.artifact_store = artifact_store
        self.audit_reader = audit_reader
        self.config = config

    def _scan_code_files(self, code_dir: Path) -> list[Path]:
        patterns = self.config.code_patterns
        ignore = self.config.ignore_patterns
        ...
```

**Acceptance Criteria**:
- [ ] Detector uses config values
- [ ] Container injects config
- [ ] Config loaded at startup

---

### T09-05-04: Add CLI Override Options

**Objective**: Allow CLI flags to override config.

**Files to Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/audit.py`

**Implementation**:
```python
@app.command("drift")
def audit_drift(
    threshold: int = typer.Option(
        None,
        "--threshold", "-t",
        help="Override drift threshold from config",
    ),
    refactor_threshold: int = typer.Option(
        None,
        "--refactor-threshold",
        help="Override refactor hotspot threshold",
    ),
) -> None:
    config = load_drift_config()

    # Apply CLI overrides
    if threshold is not None:
        config.drift_threshold = threshold
    if refactor_threshold is not None:
        config.refactor_threshold = refactor_threshold
```

**Acceptance Criteria**:
- [ ] CLI overrides take precedence
- [ ] None means use config value
- [ ] Help text explains behavior

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

**Files to Create**:
- [ ] `tests/unit/config/test_drift_config.py`

**Test Cases**:
- [ ] Default config values
- [ ] Load from valid YAML
- [ ] Load from missing file
- [ ] Partial config merging
- [ ] Invalid YAML handling
- [ ] CLI override application

**Acceptance Criteria**:
- [ ] All loading scenarios tested
- [ ] Override behavior verified

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
