# Configure LLM Providers

This guide explains how to configure different LLM providers in Rice-Factor.

## Supported Providers

| Provider | Type | Best For |
|----------|------|----------|
| **Claude** | Cloud | High-quality plan generation |
| **OpenAI** | Cloud | GPT-4 Turbo, Azure OpenAI |
| **Ollama** | Local | Privacy, offline development |
| **vLLM** | Local | GPU-accelerated inference |
| **OpenAI-Compatible** | Local/Cloud | LocalAI, LM Studio, TGI |

## Quick Setup

### Claude (Default)

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-api03-...

# Configure in .rice-factor.yaml
llm:
  provider: claude
  model: claude-3-5-sonnet-20241022
```

### OpenAI

```bash
# Set API key
export OPENAI_API_KEY=sk-...

# Configure
llm:
  provider: openai
  model: gpt-4-turbo
```

### Ollama (Local)

```bash
# Start Ollama server
ollama serve

# Pull a model
ollama pull llama2

# Configure
llm:
  provider: ollama
  model: llama2
```

## Detailed Configuration

### Claude Configuration

```yaml
# .rice-factor.yaml
llm:
  provider: claude
  model: claude-3-5-sonnet-20241022  # or claude-3-opus-20240229
  max_tokens: 4096
  temperature: 0.0      # Must be 0.0-0.2 for determinism
  top_p: 0.3            # Must be <= 0.3
  timeout: 120          # Request timeout in seconds
  max_retries: 3
```

**Environment variables:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### OpenAI Configuration

```yaml
llm:
  provider: openai
  model: gpt-4-turbo    # or gpt-4, gpt-3.5-turbo
  max_tokens: 4096
  temperature: 0.0
  timeout: 120

# Optional: Azure OpenAI
azure:
  openai_endpoint: https://your-resource.openai.azure.com
  openai_api_version: 2024-02-15-preview
```

**Environment variables:**
```bash
export OPENAI_API_KEY=sk-...
# For Azure:
export AZURE_OPENAI_API_KEY=...
export AZURE_OPENAI_ENDPOINT=https://...
```

### Ollama Configuration

```yaml
llm:
  provider: ollama
  model: llama2         # or codellama, mistral, etc.
  max_tokens: 4096
  temperature: 0.0

# Optional: Custom server
ollama:
  base_url: http://localhost:11434  # Default
```

**Environment variables:**
```bash
export OLLAMA_BASE_URL=http://localhost:11434
```

### vLLM Configuration

```yaml
llm:
  provider: vllm
  model: meta-llama/Llama-2-7b-chat-hf
  max_tokens: 4096

vllm:
  api_url: http://localhost:8000
  tensor_parallel_size: 1
```

### OpenAI-Compatible Configuration

For LocalAI, LM Studio, or other OpenAI-compatible servers:

```yaml
llm:
  provider: openai_compat
  model: local-model-name

openai_compat:
  base_url: http://localhost:1234/v1
  api_key: lm-studio  # Some servers require a dummy key
```

## Provider Selection

### Automatic Fallback

Configure multiple providers with fallback:

```yaml
llm:
  provider: claude      # Primary
  fallback:
    - openai            # First fallback
    - ollama            # Second fallback
```

### Per-Operation Provider

Different providers for different operations:

```yaml
llm:
  provider: claude      # Default

# Override for specific operations (future feature)
overrides:
  test_generation:
    provider: openai
    model: gpt-4-turbo
```

## Rate Limiting

Configure rate limits to avoid API throttling:

```yaml
# rate_limits.yaml or in .rice-factor.yaml
rate_limits:
  claude:
    requests_per_minute: 60
    tokens_per_minute: 100000
    concurrent_requests: 5
  openai:
    requests_per_minute: 60
    tokens_per_minute: 150000
```

## Cost Tracking

Track LLM costs:

```bash
# View usage
rice-factor usage show

# Output:
# Provider: claude
# Requests: 42
# Input tokens: 125,000
# Output tokens: 45,000
# Estimated cost: $3.45
```

Export usage data:

```bash
rice-factor usage export --format csv --output usage.csv
```

## Testing Without API Calls

Use the stub provider for testing:

```bash
# Single command
rice-factor plan project --stub

# Or configure globally
llm:
  provider: stub
```

The stub provider returns minimal valid artifacts without making API calls.

## Model Selection Guide

### For Plan Generation

| Quality | Claude | OpenAI | Local |
|---------|--------|--------|-------|
| Best | claude-3-opus | gpt-4-turbo | - |
| Good | claude-3-5-sonnet | gpt-4 | llama2-70b |
| Fast | claude-3-haiku | gpt-3.5-turbo | llama2-7b |

### For Test Generation

Larger models generally produce better tests. Recommended:
- claude-3-5-sonnet-20241022
- gpt-4-turbo

### For Implementation

Consistency matters most. Use the same model throughout a project.

## Troubleshooting

### "API key not found"

```bash
# Check key is set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Ensure no extra whitespace
export ANTHROPIC_API_KEY=$(echo $ANTHROPIC_API_KEY | tr -d ' ')
```

### "Rate limit exceeded"

```yaml
# Lower rate limits
rate_limits:
  claude:
    requests_per_minute: 30
    concurrent_requests: 2
```

### "Model not found" (Ollama)

```bash
# List available models
ollama list

# Pull the model
ollama pull llama2
```

### "Connection refused" (Local)

```bash
# Check server is running
curl http://localhost:11434/api/version  # Ollama
curl http://localhost:8000/health        # vLLM
```

## Best Practices

1. **Use deterministic settings**
   - temperature: 0.0
   - top_p: 0.3 or lower

2. **Match model to task**
   - Complex planning: larger models
   - Simple scaffolding: faster models

3. **Monitor costs**
   - Check `rice-factor usage show` regularly
   - Set up budget alerts

4. **Test with stub first**
   - Validate workflow with `--stub`
   - Then switch to real provider

## What's Next?

- [Configuration Reference](../../reference/configuration/settings.md) - All config options
- [Environment Variables](../../reference/configuration/environment-variables.md) - Full list
- [Troubleshooting](../troubleshooting/common-errors.md) - Provider errors
