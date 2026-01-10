# Milestone 01: Architecture - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Architectural Approach

### 1.1 Selected Architecture: Hexagonal (Ports & Adapters)

Rice-Factor follows **Hexagonal Architecture** principles:

```
                    ┌─────────────────────────────────────┐
                    │         External Systems            │
                    │  (Claude, OpenAI, Git, Filesystem)  │
                    └───────────────┬─────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  CLI Adapter  │           │  LLM Adapters │           │Executor Adapt.│
│   (Typer)     │           │(Claude,OpenAI)│           │(Scaffold,Diff)│
└───────┬───────┘           └───────┬───────┘           └───────┬───────┘
        │                           │                           │
        │         ┌─────────────────┼─────────────────┐         │
        │         │                 │                 │         │
        ▼         ▼                 ▼                 ▼         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                          PORTS                              │
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
    │  │ LLMPort │  │StorageP.│  │ExecutorP│  │  ValidatorPort  │ │
    │  └─────────┘  └─────────┘  └─────────┘  └─────────────────┘ │
    └─────────────────────────────┬───────────────────────────────┘
                                  │
    ┌─────────────────────────────▼───────────────────────────────┐
    │                        DOMAIN                               │
    │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
    │  │ Artifact Models │  │ Domain Services │  │Business Rules│  │
    │  └─────────────────┘  └─────────────────┘  └─────────────┘  │
    └─────────────────────────────────────────────────────────────┘
```

### 1.2 Rationale

| Consideration | Decision |
|--------------|----------|
| Pluggable LLMs | Ports define interface, adapters implement (Claude, OpenAI, local) |
| Testability | Domain has no external deps, mocks implement ports |
| Separation of concerns | Domain logic independent of CLI/LLM |
| Future UI | Web/GUI is just another adapter |
| Easy swapping | Change LLM provider by swapping adapter config |

---

## 2. Directory Structure Design

### 2.1 Hexagonal Layout

```
rice_factor/                         # Main package (hexagonal structure)
├── __init__.py
│
├── domain/                          # DOMAIN (innermost - NO external deps)
│   ├── __init__.py
│   ├── artifacts/                   # Artifact domain models
│   │   ├── __init__.py
│   │   ├── models.py                # ArtifactEnvelope, all artifact types
│   │   └── enums.py                 # ArtifactType, ArtifactStatus
│   ├── ports/                       # PORT definitions (interfaces)
│   │   ├── __init__.py
│   │   ├── llm.py                   # LLMPort protocol
│   │   ├── storage.py               # StoragePort protocol
│   │   ├── executor.py              # ExecutorPort protocol
│   │   └── validator.py             # ValidatorPort protocol
│   ├── services/                    # Domain services
│   │   ├── __init__.py
│   │   ├── artifact_service.py      # Artifact lifecycle
│   │   └── orchestrator.py          # Phase orchestration
│   └── failures/                    # Failure models
│       ├── __init__.py
│       └── models.py
│
├── adapters/                        # ADAPTERS (implement ports)
│   ├── __init__.py
│   ├── llm/                         # LLM provider adapters
│   │   ├── __init__.py
│   │   ├── claude.py                # ClaudeAdapter (implements LLMPort)
│   │   ├── openai.py                # OpenAIAdapter (implements LLMPort)
│   │   └── local.py                 # LocalAdapter (Ollama/vLLM)
│   ├── storage/                     # Storage adapters
│   │   ├── __init__.py
│   │   └── filesystem.py            # FilesystemStorageAdapter
│   ├── executors/                   # Executor adapters
│   │   ├── __init__.py
│   │   ├── scaffold.py              # ScaffoldExecutor
│   │   ├── diff.py                  # DiffExecutor (git apply)
│   │   └── refactor.py              # RefactorExecutor
│   └── validators/                  # Validator adapters
│       ├── __init__.py
│       ├── schema.py                # JSON Schema validator
│       └── test_runner.py           # Native test runner
│
├── entrypoints/                     # APPLICATION ENTRY POINTS
│   ├── __init__.py
│   └── cli/                         # CLI adapter (Typer)
│       ├── __init__.py
│       ├── main.py                  # `rice-factor` command entry
│       └── commands/                # Subcommands
│           ├── __init__.py
│           ├── init.py              # rice-factor init
│           ├── plan.py              # rice-factor plan <type>
│           ├── scaffold.py          # rice-factor scaffold
│           ├── impl.py              # rice-factor impl <file>
│           ├── refactor.py          # rice-factor refactor <goal>
│           ├── validate.py          # rice-factor validate
│           ├── test.py              # rice-factor test
│           ├── apply.py             # rice-factor apply
│           ├── approve.py           # rice-factor approve <artifact>
│           ├── lock.py              # rice-factor lock <artifact>
│           └── resume.py            # rice-factor resume
│
└── config/                          # Configuration & DI
    ├── __init__.py
    ├── settings.py                  # Environment-based settings
    └── container.py                 # Dependency injection setup

# Supporting directories
schemas/                             # JSON Schema definitions
├── artifact.schema.json
├── project_plan.schema.json
├── scaffold_plan.schema.json
├── test_plan.schema.json
├── implementation_plan.schema.json
├── refactor_plan.schema.json
└── validation_result.schema.json

tests/                               # Test suite
├── __init__.py
├── conftest.py
├── unit/
│   ├── domain/                      # Pure domain tests (no mocks needed)
│   └── adapters/                    # Adapter tests (mock externals)
├── integration/
└── e2e/

docs/                                # SDD documentation
├── project/
├── milestones/
└── raw/                             # Original spec docs

# Runtime directories (in user repos managed by rice-factor)
.project/                            # Human-owned project context
artifacts/                           # Generated artifacts
audit/                               # Audit trail
```

### 2.2 Hexagonal Layer Dependencies

```
entrypoints/cli/ ───────────┐
                            ▼
    adapters/* ─────────────┤ (implement ports)
                            │
        ┌───────────────────┘
        ▼
    domain/ports/ ──────────┤ (interface definitions)
                            ▼
    domain/* ───────────────┘ (NO external dependencies)
```

**Hexagonal Rules**:
- `entrypoints/` imports from `domain/` and `adapters/`
- `adapters/` imports from `domain/` (implements ports)
- `domain/` has NO external imports (pure Python, stdlib only)
- `domain/ports/` defines interfaces that adapters implement
- External libraries ONLY in `adapters/` (anthropic, openai, etc.)

---

## 3. Technology Stack Details

### 3.1 Dependencies (pyproject.toml)

```toml
[project]
name = "rice-factor"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "typer>=0.9.0",           # CLI framework
    "pydantic>=2.5.0",        # Data validation
    "jsonschema>=4.20.0",     # JSON Schema validation
    "rich>=13.0.0",           # Terminal formatting
    "pyyaml>=6.0",            # YAML parsing
]

[project.optional-dependencies]
llm = [
    "anthropic>=0.18.0",      # Claude API
    "openai>=1.10.0",         # OpenAI API
]

dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",
]

[project.scripts]
rice-factor = "rice_factor.entrypoints.cli.main:app"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.ruff]
target-version = "py311"
line-length = 100
```

### 3.2 CLI Framework: Typer

```python
# rice_factor/entrypoints/cli/main.py
import typer
from rice_factor.entrypoints.cli.commands import init, plan, scaffold, impl, refactor, validate

app = typer.Typer(
    name="rice-factor",
    help="Rice-Factor: LLM-assisted development system",
    no_args_is_help=True,
)

app.add_typer(init.app, name="init")
app.add_typer(plan.app, name="plan")
app.add_typer(scaffold.app, name="scaffold")
# ... etc

if __name__ == "__main__":
    app()
```

---

## 4. Module Responsibilities

### 4.1 Domain Layer (Innermost - No External Dependencies)

| Module | Responsibility |
|--------|----------------|
| `domain/artifacts/` | Pydantic models for all artifact types |
| `domain/ports/` | Port definitions (LLMPort, ExecutorPort, etc.) |
| `domain/services/` | Domain services (orchestrator, artifact lifecycle) |
| `domain/failures/` | Failure report models |

### 4.2 Adapters Layer (Implements Ports)

| Module | Responsibility |
|--------|----------------|
| `adapters/llm/` | LLM provider adapters (Claude, OpenAI, local) |
| `adapters/executors/` | Executor adapters (scaffold, diff, refactor) |
| `adapters/validators/` | Validator adapters (schema, test runner) |
| `adapters/storage/` | Storage adapters (filesystem) |

### 4.3 Entrypoints Layer (Application Entry)

| Module | Responsibility |
|--------|----------------|
| `entrypoints/cli/` | CLI adapter (Typer commands) |
| `entrypoints/cli/commands/` | Individual CLI subcommands |

### 4.4 Config Layer

| Module | Responsibility |
|--------|----------------|
| `config/settings.py` | Environment-based configuration |
| `config/container.py` | Dependency injection / adapter wiring |

---

## 5. Configuration Management

### 5.1 Design Principles: 12-Factor App Methodology

Rice-Factor follows the **12-Factor App** configuration principles (https://12factor.net):

1. **Strict separation of config from code** - Config varies between deploys, code does not
2. **Store secrets in environment variables** - Language/OS-agnostic, won't be checked into repo
3. **No hardcoded values** - All behavior should be configurable at runtime

### 5.2 Layered Configuration Priority

Configuration values are resolved in this order (highest priority first):

```
1. CLI arguments          (--llm-provider=claude)
2. Environment variables  (RICE_LLM_PROVIDER=claude)
3. Project config file    (.rice-factor.yaml)
4. User config file       (~/.rice-factor/config.yaml)
5. Default values         (fallback only, in code)
```

### 5.3 Configuration Library: Dynaconf

**Decision**: Use **Dynaconf** for configuration management with hot reload support.

**Rationale**:
- Runtime config changes without restart (user requirement)
- 12-Factor compliance out of the box
- Multi-format support (YAML, TOML, JSON, env vars)
- HashiCorp Vault integration for secrets (future)
- Fits hexagonal architecture (can be swapped via adapter)

### 5.4 Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `RICE_LLM_PROVIDER` | LLM provider (claude/openai/local) | claude |
| `RICE_LLM_MODEL` | Model identifier | claude-3-5-sonnet |
| `RICE_API_KEY` | API key for LLM provider | (required) |
| `RICE_LOG_LEVEL` | Logging level | INFO |
| `RICE_DRY_RUN` | Global dry-run mode | false |
| `RICE_AUTO_APPROVE` | Skip approval prompts | false |

### 5.5 Configuration Files

```
# User-level defaults (not in repo)
~/.rice-factor/
└── config.yaml

# Project-level overrides
.rice-factor.yaml

# Secrets (gitignored)
.env

# Default configuration (in repo)
rice_factor/config/defaults.yaml

# Language capabilities
tools/registry/capability_registry.yaml
```

### 5.6 Configuration Schema

```yaml
# ~/.rice-factor/config.yaml or .rice-factor.yaml
llm:
  provider: claude           # claude | openai | local
  model: claude-3-5-sonnet   # Model identifier
  api_key: ${RICE_API_KEY}   # Environment variable reference
  timeout: 60                # Request timeout in seconds
  max_retries: 3             # Retry count on failure

execution:
  dry_run: false             # Preview mode
  auto_approve: false        # Skip approval prompts
  max_context_tokens: 100000 # LLM context limit

output:
  color: true                # Colored terminal output
  verbose: false             # Verbose logging
  log_level: INFO            # DEBUG | INFO | WARNING | ERROR

paths:
  artifacts_dir: ./artifacts
  audit_dir: ./audit
  project_dir: ./.project
```

### 5.7 Hot Reload Implementation

```python
# rice_factor/config/settings.py
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="RICE",
    settings_files=[
        "rice_factor/config/defaults.yaml",  # Package defaults
        "~/.rice-factor/config.yaml",        # User defaults
        ".rice-factor.yaml",                  # Project overrides
    ],
    load_dotenv=True,
    environments=False,  # No dev/prod split for CLI tool
)

def get_setting(key: str, default=None):
    """Get a configuration value with optional default."""
    return settings.get(key, default)

def reload_config():
    """Reload configuration from files (for hot reload)."""
    settings.reload()
```

### 5.8 Configuration Port (Hexagonal)

```python
# rice_factor/domain/ports/config.py
from typing import Protocol, Any

class ConfigPort(Protocol):
    """Port for configuration access."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        ...

    def reload(self) -> None:
        """Reload configuration from sources."""
        ...

# rice_factor/adapters/config/dynaconf_adapter.py
from rice_factor.domain.ports.config import ConfigPort
from dynaconf import Dynaconf

class DynaconfAdapter:
    """Adapter implementing ConfigPort using Dynaconf."""

    def __init__(self, settings: Dynaconf):
        self._settings = settings

    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    def reload(self):
        self._settings.reload()
```

---

## 6. Error Handling Strategy

### 6.1 Exception Hierarchy

```python
class RiceFactorError(Exception):
    """Base exception for all Rice-Factor errors."""

class ArtifactError(RiceFactorError):
    """Artifact-related errors."""

class ValidationError(ArtifactError):
    """Schema validation failed."""

class ApprovalError(ArtifactError):
    """Approval missing or invalid."""

class ExecutionError(RiceFactorError):
    """Executor-related errors."""

class LLMError(RiceFactorError):
    """LLM provider errors."""
```

### 6.2 Error Response Pattern

```python
@dataclass
class Result(Generic[T]):
    success: bool
    value: T | None
    error: RiceFactorError | None
```

---

## 7. Testing Strategy

### 7.1 Test Layers

| Layer | Focus | Tools |
|-------|-------|-------|
| Unit | Domain logic, pure functions | pytest |
| Integration | Service interactions, LLM mocks | pytest, pytest-mock |
| E2E | Full CLI workflows | pytest, temp directories |

### 7.2 Test Coverage Targets

| Module | Target |
|--------|--------|
| `domain/` | 95% |
| `adapters/` | 80% |
| `entrypoints/cli/` | 70% |
| `config/` | 90% |

---

## 8. Development Workflow

### 8.1 Setup

```bash
# Clone and install
git clone <repo>
cd rice-factor
pip install -e ".[dev,llm]"

# Verify
rice-factor --help
pytest
mypy rice_factor
ruff check .
```

### 8.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        entry: ruff check --fix
        language: system
        types: [python]
      - id: mypy
        name: mypy
        entry: mypy
        language: system
        types: [python]
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone design |
| 1.1.0 | 2026-01-10 | User Decision | Updated to Hexagonal Architecture, `rice-factor` CLI command |
| 1.2.0 | 2026-01-10 | User Decision | Added 12-Factor App configuration management with Dynaconf |
