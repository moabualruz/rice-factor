# Environment Variables

All Rice-Factor configuration can be set via environment variables.

## Naming Convention

Environment variables use the `RICE_` prefix with underscore-separated nested keys:

```
RICE_{SECTION}_{KEY}
```

Examples:
- `RICE_LLM_PROVIDER` → `llm.provider`
- `RICE_OUTPUT_VERBOSE` → `output.verbose`
- `RICE_PATHS_ARTIFACTS_DIR` → `paths.artifacts_dir`

## API Keys

These are required for LLM providers:

| Variable | Provider | Example |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Claude | `sk-ant-api03-...` |
| `OPENAI_API_KEY` | OpenAI | `sk-...` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI | `...` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI | `https://...` |

## LLM Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `RICE_LLM_PROVIDER` | LLM provider | `claude` |
| `RICE_LLM_MODEL` | Model identifier | Provider default |
| `RICE_LLM_MAX_TOKENS` | Max response tokens | `4096` |
| `RICE_LLM_TEMPERATURE` | Sampling temperature | `0.0` |
| `RICE_LLM_TOP_P` | Top-p sampling | `0.3` |
| `RICE_LLM_TIMEOUT` | Request timeout (seconds) | `120` |
| `RICE_LLM_MAX_RETRIES` | Retry attempts | `3` |

## Provider-Specific

### OpenAI

| Variable | Description |
|----------|-------------|
| `RICE_OPENAI_MODEL` | OpenAI model override |

### Azure OpenAI

| Variable | Description |
|----------|-------------|
| `RICE_AZURE_OPENAI_ENDPOINT` | Azure endpoint URL |
| `RICE_AZURE_OPENAI_API_VERSION` | API version |

### Ollama

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |

### vLLM

| Variable | Description |
|----------|-------------|
| `RICE_VLLM_API_URL` | vLLM server URL |

## Execution

| Variable | Description | Default |
|----------|-------------|---------|
| `RICE_EXECUTION_DRY_RUN` | Dry run mode | `false` |
| `RICE_EXECUTION_AUTO_APPROVE` | Auto-approve artifacts | `false` |
| `RICE_EXECUTION_MAX_RETRIES` | Operation retries | `3` |
| `RICE_EXECUTION_TIMEOUT_SECONDS` | Operation timeout | `300` |

## Output

| Variable | Description | Default |
|----------|-------------|---------|
| `RICE_OUTPUT_COLOR` | Colored output | `true` |
| `RICE_OUTPUT_VERBOSE` | Verbose logging | `false` |
| `RICE_OUTPUT_LOG_LEVEL` | Log level | `INFO` |

## Paths

| Variable | Description | Default |
|----------|-------------|---------|
| `RICE_PATHS_ARTIFACTS_DIR` | Artifacts directory | `.project/artifacts` |
| `RICE_PATHS_AUDIT_DIR` | Audit directory | `.project/audit` |
| `RICE_PATHS_STAGING_DIR` | Staging directory | `.project/staging` |

## Parsing

| Variable | Description | Default |
|----------|-------------|---------|
| `RICE_PARSING_PROVIDER` | Parser provider | `treesitter` |
| `RICE_PARSING_FALLBACK_ENABLED` | Enable fallback | `false` |

## LSP

| Variable | Description | Default |
|----------|-------------|---------|
| `RICE_LSP_ENABLED` | Enable LSP | `true` |
| `RICE_LSP_ONE_SHOT_MODE` | One-shot mode | `true` |
| `RICE_LSP_DEFAULT_TIMEOUT` | LSP timeout | `60` |

## Storage

| Variable | Description | Default |
|----------|-------------|---------|
| `RICE_STORAGE_DEFAULT_BACKEND` | Default backend | `filesystem` |

### S3

| Variable | Description |
|----------|-------------|
| `RICE_STORAGE_S3_BUCKET` | S3 bucket name |
| `RICE_STORAGE_S3_PREFIX` | Key prefix |
| `RICE_STORAGE_S3_REGION` | AWS region |
| `RICE_STORAGE_S3_ENDPOINT_URL` | Custom endpoint |
| `RICE_STORAGE_S3_ACCESS_KEY_ID` | Access key |
| `RICE_STORAGE_S3_SECRET_ACCESS_KEY` | Secret key |
| `RICE_STORAGE_S3_ENABLED` | Enable S3 |

### GCS

| Variable | Description |
|----------|-------------|
| `RICE_STORAGE_GCS_BUCKET` | GCS bucket name |
| `RICE_STORAGE_GCS_PREFIX` | Object prefix |
| `RICE_STORAGE_GCS_PROJECT` | GCP project |
| `RICE_STORAGE_GCS_CREDENTIALS_PATH` | Credentials file |
| `RICE_STORAGE_GCS_ENABLED` | Enable GCS |

## Rate Limiting

| Variable | Description |
|----------|-------------|
| `RICE_RATE_LIMITS_DEFAULTS_STRATEGY` | Default strategy |
| `RICE_RATE_LIMITS_DEFAULTS_ENABLED` | Enable rate limiting |
| `RICE_RATE_LIMITS_PROVIDERS_CLAUDE_REQUESTS_PER_MINUTE` | Claude RPM |
| `RICE_RATE_LIMITS_PROVIDERS_CLAUDE_TOKENS_PER_MINUTE` | Claude TPM |
| `RICE_RATE_LIMITS_PROVIDERS_OPENAI_REQUESTS_PER_MINUTE` | OpenAI RPM |

## Notifications

| Variable | Description |
|----------|-------------|
| `RICE_NOTIFICATIONS_ENABLED` | Enable notifications |
| `RICE_FACTOR_SLACK_WEBHOOK_URL` | Slack webhook URL |
| `RICE_FACTOR_TEAMS_WEBHOOK_URL` | Teams webhook URL |
| `RICE_FACTOR_WEBHOOK_URL` | Generic webhook URL |

## Usage Examples

### Shell Export

```bash
# ~/.bashrc or ~/.zshrc

# API Keys
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export OPENAI_API_KEY="sk-..."

# LLM Configuration
export RICE_LLM_PROVIDER="claude"
export RICE_LLM_MODEL="claude-3-5-sonnet-20241022"

# Output
export RICE_OUTPUT_VERBOSE="true"
export RICE_OUTPUT_LOG_LEVEL="DEBUG"
```

### dotenv File

```bash
# .env (use with python-dotenv)

ANTHROPIC_API_KEY=sk-ant-api03-...
RICE_LLM_PROVIDER=claude
RICE_OUTPUT_VERBOSE=false
```

### CI Environment

```yaml
# GitHub Actions
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  RICE_LLM_PROVIDER: claude
  RICE_OUTPUT_VERBOSE: true
```

### Docker

```dockerfile
ENV RICE_LLM_PROVIDER=ollama
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV RICE_OUTPUT_COLOR=false
```

## Priority

Environment variables override config file values:

```
CLI args > Env vars > .rice-factor.yaml > ~/.rice-factor/config.yaml > Defaults
```

## Boolean Values

Boolean environment variables accept:
- True: `true`, `1`, `yes`, `on`
- False: `false`, `0`, `no`, `off`

```bash
RICE_OUTPUT_VERBOSE=true    # Enabled
RICE_OUTPUT_VERBOSE=1       # Enabled
RICE_OUTPUT_VERBOSE=false   # Disabled
RICE_OUTPUT_VERBOSE=0       # Disabled
```

## See Also

- [Configuration Settings](settings.md)
- [Config Files](config-files.md)
