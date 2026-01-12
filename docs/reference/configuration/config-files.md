# Configuration Files

Rice-Factor uses several configuration files for different purposes.

## Configuration File Locations

| File | Location | Purpose |
|------|----------|---------|
| `.rice-factor.yaml` | Project root | Project-specific settings |
| `~/.rice-factor/config.yaml` | User home | User-wide defaults |
| `.project/run_mode.yaml` | Project `.project/` | Multi-agent configuration |

## Project Configuration

### .rice-factor.yaml

Main project configuration file. Place in your project root.

```yaml
# .rice-factor.yaml

# LLM Provider Configuration
llm:
  provider: claude
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.0
  top_p: 0.3
  timeout: 120
  max_retries: 3

# Execution Settings
execution:
  dry_run: false
  auto_approve: false
  max_retries: 3
  timeout_seconds: 300

# Output Settings
output:
  color: true
  verbose: false
  log_level: INFO

# Path Settings
paths:
  artifacts_dir: .project/artifacts
  audit_dir: .project/audit
  staging_dir: .project/staging

# Parsing Settings
parsing:
  provider: treesitter
  fallback_enabled: false

# LSP Settings
lsp:
  enabled: true
  one_shot_mode: true
  default_timeout: 60
```

## User Configuration

### ~/.rice-factor/config.yaml

User-wide defaults. Applied to all projects unless overridden.

```yaml
# ~/.rice-factor/config.yaml

llm:
  provider: claude
  model: claude-3-5-sonnet-20241022

output:
  color: true
  verbose: false

# Default rate limits
rate_limits:
  providers:
    claude:
      requests_per_minute: 60
      tokens_per_minute: 100000
```

## Run Mode Configuration

### .project/run_mode.yaml

Multi-agent coordination settings.

```yaml
# .project/run_mode.yaml

mode: solo  # solo, orchestrator, voting, role_locked, hybrid

# For orchestrator/voting modes
authority_agent: primary

agents:
  - name: primary
    provider: claude
    model: claude-3-5-sonnet-20241022

  - name: critic
    provider: openai
    model: gpt-4-turbo

rules:
  - ONLY_PRIMARY_EMITS_ARTIFACTS
  - CRITICS_MUST_REVIEW_BEFORE_APPROVAL
  - NO_FREE_FORM_CHAT

voting_threshold: 0.6
max_rounds: 3

# Phase-specific modes (for hybrid)
phase_modes:
  planning: orchestrator
  implementation: solo
  review: voting
```

## Supplementary Configuration Files

### rate_limits.yaml

Rate limiting configuration.

```yaml
# rice_factor/config/rate_limits.yaml (or custom location)

defaults:
  strategy: block  # block, reject, degrade
  enabled: true

providers:
  claude:
    requests_per_minute: 60
    tokens_per_minute: 100000
    tokens_per_day: 10000000
    concurrent_requests: 5
    enabled: true

  openai:
    requests_per_minute: 60
    tokens_per_minute: 150000
    concurrent_requests: 10
    enabled: true

  ollama:
    requests_per_minute: 120
    concurrent_requests: 4
    enabled: true

tiers:
  free:
    requests_per_minute: 20
    tokens_per_minute: 40000
  standard:
    requests_per_minute: 60
    tokens_per_minute: 100000
  professional:
    requests_per_minute: 120
    tokens_per_minute: 200000
```

### storage.yaml

Storage backend configuration.

```yaml
# Storage configuration

default_backend: filesystem

filesystem:
  artifacts_dir: .project/artifacts
  enabled: true

s3:
  bucket: my-artifacts-bucket
  prefix: artifacts
  region: us-east-1
  endpoint_url: ""  # For S3-compatible services
  enabled: false

gcs:
  bucket: my-gcs-bucket
  prefix: artifacts
  project: my-gcp-project
  credentials_path: ""
  enabled: false

backend_priority:
  - filesystem
  - s3
  - gcs

fallback:
  enabled: true
  write_through: false
  read_first_available: true

cache:
  enabled: false
  ttl_seconds: 300
  max_size_mb: 100
  cache_dir: .project/.cache
```

### notifications.yaml

Webhook and notification settings.

```yaml
# Notification configuration

notifications:
  enabled: true
  default_timeout: 30
  retry_count: 3
  retry_delay: 1.0
  verify_ssl: true

webhooks:
  slack:
    enabled: false
    webhook_url: ${RICE_FACTOR_SLACK_WEBHOOK_URL}
    events:
      - artifact.created
      - artifact.approved
      - artifact.locked
      - build.failed
      - test.failed
      - error

  teams:
    enabled: false
    webhook_url: ${RICE_FACTOR_TEAMS_WEBHOOK_URL}
    use_adaptive_cards: true
    events:
      - artifact.*
      - build.*

  generic:
    enabled: false
    webhook_url: ${RICE_FACTOR_WEBHOOK_URL}
    headers:
      Authorization: Bearer ${WEBHOOK_TOKEN}
    events:
      - "*"

routing:
  critical:
    - build.failed
    - test.failed
    - error
    - cost.threshold
  standard:
    - artifact.created
    - artifact.approved
    - build.completed
  verbose:
    - rate.limit
    - artifact.rejected
```

### capability_registry.yaml

Language-specific refactoring capabilities.

```yaml
# Capability registry

languages:
  python:
    parser: treesitter
    lsp_server: pylsp
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true
    tools:
      - rope

  rust:
    parser: treesitter
    lsp_server: rust-analyzer
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: partial

  go:
    parser: treesitter
    lsp_server: gopls
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true

  typescript:
    parser: treesitter
    lsp_server: typescript-language-server
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true
    tools:
      - jscodeshift

  java:
    parser: treesitter
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true
    tools:
      - openrewrite
```

## Project Context Files

### .project/ Directory

Created by `rice-factor init`:

```
.project/
├── requirements.md      # Project requirements
├── constraints.md       # Technical constraints
├── glossary.md          # Domain terminology
├── non_goals.md         # Explicit non-goals
├── risks.md             # Known risks
├── decisions.md         # Architecture decisions (optional)
├── run_mode.yaml        # Multi-agent config (optional)
├── artifacts/           # Generated artifacts
├── audit/               # Audit trail
└── staging/             # Work in progress
```

## File Format

All configuration files use YAML format:

```yaml
# Comments start with #

# Simple values
key: value
number: 42
boolean: true

# Nested values
parent:
  child: value
  nested:
    deep: value

# Lists
items:
  - item1
  - item2
  - item3

# Environment variable substitution
api_key: ${ANTHROPIC_API_KEY}
url: ${BASE_URL:-http://localhost:8000}  # With default
```

## Hot Reload

Rice-Factor supports hot reload for configuration:

```python
# Programmatic reload
from rice_factor.config import reload_config
reload_config()
```

Some settings require restart to take effect (noted in documentation).

## Validation

Configuration is validated on load:

```bash
# Validate configuration
rice-factor validate --step config

# Common validation errors:
# - Invalid YAML syntax
# - Unknown configuration keys
# - Invalid value types
# - Missing required fields
```

## See Also

- [Configuration Settings](settings.md) - All options
- [Environment Variables](environment-variables.md) - Env var reference
