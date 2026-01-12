# Configuration Settings

Complete reference for all Rice-Factor configuration options.

## Configuration Hierarchy

Settings are loaded in this order (highest priority first):

1. **CLI Arguments** - `--provider claude`
2. **Environment Variables** - `RICE_LLM_PROVIDER=claude`
3. **Project Config** - `.rice-factor.yaml` in project root
4. **User Config** - `~/.rice-factor/config.yaml`
5. **Defaults** - Built-in default values

## Configuration File

Create `.rice-factor.yaml` in your project root:

```yaml
# .rice-factor.yaml
llm:
  provider: claude
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.0
  top_p: 0.3
  timeout: 120
  max_retries: 3

execution:
  dry_run: false
  auto_approve: false
  max_retries: 3
  timeout_seconds: 300

output:
  color: true
  verbose: false
  log_level: INFO

paths:
  artifacts_dir: .project/artifacts
  audit_dir: .project/audit
  staging_dir: .project/staging
```

## LLM Configuration

### llm.provider

LLM provider to use.

| Value | Description |
|-------|-------------|
| `claude` | Anthropic Claude (default) |
| `openai` | OpenAI GPT models |
| `ollama` | Local Ollama server |
| `vllm` | vLLM server |
| `openai_compat` | OpenAI-compatible APIs |
| `stub` | Mock provider for testing |

### llm.model

Model identifier for the provider.

**Claude models:**
- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`

**OpenAI models:**
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

### llm.max_tokens

Maximum tokens in response. Default: `4096`

### llm.temperature

Sampling temperature. Must be `0.0-0.2` for determinism. Default: `0.0`

### llm.top_p

Top-p sampling. Must be `<= 0.3` for determinism. Default: `0.3`

### llm.timeout

Request timeout in seconds. Default: `120`

### llm.max_retries

Maximum retry attempts. Default: `3`

## Provider-Specific Settings

### OpenAI

```yaml
openai:
  model: gpt-4-turbo
```

### Azure OpenAI

```yaml
azure:
  openai_endpoint: https://your-resource.openai.azure.com
  openai_api_version: 2024-02-15-preview
```

### Ollama

```yaml
ollama:
  base_url: http://localhost:11434  # Default
```

### vLLM

```yaml
vllm:
  api_url: http://localhost:8000
  tensor_parallel_size: 1
```

### OpenAI-Compatible

```yaml
openai_compat:
  base_url: http://localhost:1234/v1
  api_key: lm-studio
```

## Execution Configuration

### execution.dry_run

Run without making changes. Default: `false`

### execution.auto_approve

Auto-approve artifacts (not recommended). Default: `false`

### execution.max_retries

Retry failed operations. Default: `3`

### execution.timeout_seconds

Operation timeout. Default: `300`

## Output Configuration

### output.color

Enable colored output. Default: `true`

### output.verbose

Enable verbose logging. Default: `false`

### output.log_level

Log level. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`. Default: `INFO`

## Path Configuration

### paths.artifacts_dir

Artifacts storage location. Default: `.project/artifacts`

### paths.audit_dir

Audit trail location. Default: `.project/audit`

### paths.staging_dir

Staging area. Default: `.project/staging`

## Parsing Configuration

```yaml
parsing:
  provider: treesitter
  fallback_enabled: false
```

### parsing.provider

AST parser. Options: `treesitter`, `regex`. Default: `treesitter`

### parsing.fallback_enabled

Enable regex fallback. Default: `false`

## LSP Configuration

```yaml
lsp:
  enabled: true
  one_shot_mode: true
  default_timeout: 60
  servers:
    gopls:
      command: gopls
      args: []
    rust_analyzer:
      command: rust-analyzer
    typescript_language_server:
      command: typescript-language-server
      args: [--stdio]
    pylsp:
      command: pylsp
```

### lsp.enabled

Enable LSP integration. Default: `true`

### lsp.one_shot_mode

Start/stop LSP per operation. Default: `true`

### lsp.default_timeout

LSP operation timeout. Default: `60`

## Rate Limiting

```yaml
rate_limits:
  defaults:
    strategy: block
    enabled: true

  providers:
    claude:
      requests_per_minute: 60
      tokens_per_minute: 100000
      tokens_per_day: 10000000
      concurrent_requests: 5
    openai:
      requests_per_minute: 60
      tokens_per_minute: 150000
      concurrent_requests: 10
```

### Rate Limit Strategies

| Strategy | Behavior |
|----------|----------|
| `block` | Wait until limit resets (default) |
| `reject` | Fail immediately |
| `degrade` | Use fallback provider |

## Storage Configuration

```yaml
storage:
  default_backend: filesystem

  filesystem:
    artifacts_dir: .project/artifacts
    enabled: true

  s3:
    bucket: ""
    prefix: artifacts
    region: ""
    enabled: false

  gcs:
    bucket: ""
    prefix: artifacts
    project: ""
    enabled: false

  fallback:
    enabled: true
    write_through: false
    read_first_available: true

  cache:
    enabled: false
    ttl_seconds: 300
    max_size_mb: 100
```

## Notifications

```yaml
notifications:
  enabled: true
  default_timeout: 30
  retry_count: 3

webhooks:
  slack:
    enabled: false
    webhook_url: ${RICE_FACTOR_SLACK_WEBHOOK_URL}
    events:
      - artifact.*
      - build.*
      - error

  teams:
    enabled: false
    webhook_url: ${RICE_FACTOR_TEAMS_WEBHOOK_URL}

  generic:
    enabled: false
    webhook_url: ${RICE_FACTOR_WEBHOOK_URL}
```

## Capability Registry

```yaml
capabilities:
  languages:
    python:
      operations:
        move_file: true
        rename_symbol: true
        extract_interface: true
        enforce_dependency: true
    rust:
      operations:
        move_file: true
        rename_symbol: true
        extract_interface: false
        enforce_dependency: partial
```

## Run Modes (Multi-Agent)

```yaml
run_mode:
  mode: solo

  # For orchestrator mode
  authority_agent: primary
  agents:
    - name: primary
      provider: claude
    - name: critic
      provider: openai

  rules:
    - ONLY_PRIMARY_EMITS_ARTIFACTS
    - CRITICS_MUST_REVIEW_BEFORE_APPROVAL

  voting_threshold: 0.6
  max_rounds: 3
```

### Run Mode Options

| Mode | Description |
|------|-------------|
| `solo` | Single agent (default) |
| `orchestrator` | Primary delegates to sub-agents |
| `voting` | Multiple agents vote |
| `role_locked` | Fixed specialist roles |
| `hybrid` | Combination |

## TUI Configuration

```yaml
tui:
  refresh_interval: 5
  show_timestamps: true
  expand_payload: true
  color_scheme: dark
```

## Web Configuration

```yaml
web:
  host: 127.0.0.1
  port: 8000
  workers: 1
  reload: false
```

## Complete Example

```yaml
# .rice-factor.yaml - Complete configuration

llm:
  provider: claude
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.0
  top_p: 0.3
  timeout: 120
  max_retries: 3

execution:
  dry_run: false
  auto_approve: false

output:
  color: true
  verbose: false
  log_level: INFO

paths:
  artifacts_dir: .project/artifacts
  audit_dir: .project/audit

parsing:
  provider: treesitter

lsp:
  enabled: true
  one_shot_mode: true

rate_limits:
  providers:
    claude:
      requests_per_minute: 60
      tokens_per_minute: 100000

storage:
  default_backend: filesystem

notifications:
  enabled: false

run_mode:
  mode: solo
```

## See Also

- [Environment Variables](environment-variables.md)
- [Config Files](config-files.md)
- [CLI Reference](../cli/commands.md)
