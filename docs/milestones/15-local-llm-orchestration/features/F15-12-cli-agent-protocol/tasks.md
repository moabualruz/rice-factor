# F15-12: CLI Agent Protocol & Orchestrator - Tasks

## Tasks
### T15-12-01: Define CLIAgentPort Protocol
### T15-12-02: Create CLITaskResult Dataclass
### T15-12-03: Implement CLI Agent Detector
### T15-12-04: Create Unified Orchestrator
### T15-12-05: Implement Mode Selection Logic
### T15-12-06: Add Fallback Between API and CLI
### T15-12-07: Implement `rice-factor agents` Command
### T15-12-08: Write Unit Tests

## Estimated Test Count: ~10

## Implementation Notes

### CLIAgentPort Protocol
```python
class CLIAgentPort(Protocol):
    @property
    def name(self) -> str: ...
    async def is_available(self) -> bool: ...
    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float = 300.0,
    ) -> CLITaskResult: ...
    def get_capabilities(self) -> list[str]: ...
```

### CLITaskResult
```python
@dataclass
class CLITaskResult:
    success: bool
    output: str
    error: str | None
    files_modified: list[str]
    duration_seconds: float
    agent_name: str
```

### Orchestration Modes
- `API` - Use REST API providers only
- `CLI` - Use CLI agents only
- `AUTO` - Select based on task type

### Task Type Routing
- Simple code generation → API mode
- Complex refactoring → CLI mode
- Multi-file changes → CLI mode
- Testing → CLI mode

### CLI Commands
```bash
rice-factor agents detect      # Detect available CLI agents
rice-factor providers          # List all providers and agents
rice-factor exec --mode cli    # Execute with CLI mode
rice-factor exec --mode auto   # Auto-select mode
```
