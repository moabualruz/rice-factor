# Feature F13-01: Run Mode Configuration - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T13-01-01 | Create agent domain models | Pending | P0 |
| T13-01-02 | Define RunMode enum | Pending | P0 |
| T13-01-03 | Create RunModeConfig model | Pending | P0 |
| T13-01-04 | Implement YAML loader | Pending | P0 |
| T13-01-05 | Add CLI mode override | Pending | P1 |
| T13-01-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T13-01-01: Create Agent Domain Models

**Objective**: Define core models for agents.

**Files to Create**:
- [ ] `rice_factor/domain/models/agent.py`

**Implementation**:
```python
class AgentRole(str, Enum):
    BUILDER = "builder"
    CRITIC = "critic"
    DOMAIN_SPECIALIST = "domain_specialist"
    ORCHESTRATOR = "orchestrator"
    VOTER = "voter"

class AgentCapability(str, Enum):
    PLAN = "plan"
    SCAFFOLD = "scaffold"
    IMPLEMENT = "implement"
    REVIEW = "review"
    VALIDATE = "validate"

@dataclass
class AgentConfig:
    name: str
    role: AgentRole
    model: str
    capabilities: list[AgentCapability]
```

**Acceptance Criteria**:
- [ ] All roles defined
- [ ] All capabilities defined
- [ ] AgentConfig is complete

---

### T13-01-02: Define RunMode Enum

**Objective**: Define available run modes.

**Files to Create**:
- [ ] `rice_factor/config/run_mode_config.py`

**Implementation**:
```python
class RunMode(str, Enum):
    SOLO = "solo"
    ORCHESTRATOR = "orchestrator"
    VOTING = "voting"
    ROLE_LOCKED = "role_locked"
    HYBRID = "hybrid"
```

**Acceptance Criteria**:
- [ ] All 5 modes defined
- [ ] String-based for YAML

---

### T13-01-03: Create RunModeConfig Model

**Objective**: Configuration model for all modes.

**Files to Modify**:
- [ ] `rice_factor/config/run_mode_config.py`

**Implementation**:
```python
@dataclass
class RunModeConfig:
    mode: RunMode = RunMode.SOLO

    # Orchestrator settings
    orchestrator_model: str | None = None
    max_delegation_depth: int = 2
    sub_agents: list[AgentConfig] = field(default_factory=list)

    # Voting settings
    voting_agents: int = 3
    voting_threshold: float = 0.5

    # Role-locked settings
    roles: dict[str, AgentConfig] = field(default_factory=dict)
    critic_required: bool = True

    # Hybrid settings
    phase_modes: dict[str, RunMode] = field(default_factory=dict)
```

**Acceptance Criteria**:
- [ ] All mode settings included
- [ ] Sensible defaults
- [ ] Dataclass pattern

---

### T13-01-04: Implement YAML Loader

**Objective**: Load run_mode.yaml configuration.

**Files to Modify**:
- [ ] `rice_factor/config/run_mode_config.py`

**File Location**: `.project/run_mode.yaml`

**Implementation**:
```python
@classmethod
def from_file(cls, path: Path) -> "RunModeConfig":
    if not path.exists():
        return cls()  # Default solo mode

    with open(path) as f:
        data = yaml.safe_load(f)

    mode = RunMode(data.get("mode", "solo"))
    config = cls(mode=mode)

    # Parse mode-specific settings
    if mode == RunMode.ORCHESTRATOR:
        config.orchestrator_model = data.get("orchestrator", {}).get("model")
        config.sub_agents = [
            cls._parse_agent(a) for a in data.get("sub_agents", [])
        ]
    # ... other modes

    return config
```

**Acceptance Criteria**:
- [ ] Missing file returns default
- [ ] All modes parsed correctly
- [ ] Invalid YAML handled

---

### T13-01-05: Add CLI Mode Override

**Objective**: Allow CLI to override configured mode.

**Files to Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/plan.py`
- [ ] Other relevant commands

**Implementation**:
```python
@app.command()
def plan(
    artifact_type: str,
    mode: str = typer.Option(
        None,
        "--mode",
        help="Override run mode",
    ),
) -> None:
    config = RunModeConfig.from_file(Path(".project/run_mode.yaml"))

    if mode:
        config.mode = RunMode(mode)

    coordinator = get_coordinator(config)
    ...
```

**Acceptance Criteria**:
- [ ] --mode flag works
- [ ] Overrides file config
- [ ] Invalid mode rejected

---

### T13-01-06: Write Unit Tests

**Objective**: Test configuration loading.

**Files to Create**:
- [ ] `tests/unit/config/test_run_mode_config.py`

**Test Cases**:
- [ ] Default config (solo mode)
- [ ] Load orchestrator config
- [ ] Load voting config
- [ ] Load role-locked config
- [ ] Load hybrid config
- [ ] Missing file handling
- [ ] Invalid YAML handling
- [ ] CLI override

**Acceptance Criteria**:
- [ ] All modes tested
- [ ] Edge cases covered

---

## 3. Task Dependencies

```
T13-01-01 (Models) ──→ T13-01-02 (Enum) ──→ T13-01-03 (Config)
                                                  │
                                                  ↓
                                          T13-01-04 (Loader)
                                                  │
                                                  ↓
                                          T13-01-05 (CLI)
                                                  │
                                                  ↓
                                          T13-01-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T13-01-01 | Low | Enums + dataclass |
| T13-01-02 | Low | Simple enum |
| T13-01-03 | Medium | Many fields |
| T13-01-04 | Medium | YAML parsing |
| T13-01-05 | Low | CLI option |
| T13-01-06 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
