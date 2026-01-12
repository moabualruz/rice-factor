# Installation

This guide covers all installation methods for Rice-Factor.

## Prerequisites

- **Python 3.11+** - Rice-Factor requires Python 3.11 or later
- **pip or uv** - Package installer
- **Git** - For version control operations

### Optional Dependencies

- **ffmpeg** - Required for generating demo GIFs with VHS
- **Node.js** - Required for web interface development

## Installation Methods

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer. This is the recommended installation method.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Rice-Factor
uv pip install rice-factor

# Or install with development dependencies
uv pip install rice-factor[dev]
```

### Using pip

```bash
# Install from PyPI (when available)
pip install rice-factor

# Or install with development dependencies
pip install rice-factor[dev]
```

### From Source

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/[user]/rice-factor.git
cd rice-factor

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install in development mode
pip install -e ".[dev]"
```

## Verification

After installation, verify Rice-Factor is working:

```bash
# Check version
rice-factor --version

# View available commands
rice-factor --help
```

Expected output:
```
Usage: rice-factor [OPTIONS] COMMAND [ARGS]...

  Rice-Factor: LLM-Assisted Development System

Options:
  -v, --version  Show version and exit
  -V, --verbose  Enable verbose output
  -q, --quiet    Suppress non-essential output
  --help         Show this message and exit.

Commands:
  init       Initialize a new rice-factor project
  plan       Generate planning artifacts
  scaffold   Create file structure from ScaffoldPlan
  ...
```

## Configuration

### API Keys

Rice-Factor needs API keys for LLM providers. Set them as environment variables:

```bash
# For Claude (Anthropic)
export ANTHROPIC_API_KEY=sk-ant-...

# For OpenAI
export OPENAI_API_KEY=sk-...

# For local models (Ollama)
export OLLAMA_BASE_URL=http://localhost:11434
```

### Configuration File

Create `.rice-factor.yaml` in your project root:

```yaml
llm:
  provider: claude
  model: claude-3-5-sonnet-20241022
  temperature: 0.0
```

See [Configuration Reference](../../reference/configuration/settings.md) for all options.

## Troubleshooting

### Common Issues

#### "command not found: rice-factor"

The installation directory is not in your PATH. Try:

```bash
# Check if Python scripts are in PATH
python -m rice_factor --help
```

If this works, add the Python scripts directory to your PATH.

#### Import errors

Ensure you're using the correct Python version:

```bash
python --version  # Should be 3.11+
```

#### API key errors

Verify your API keys are set correctly:

```bash
# Check if keys are set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
```

## Next Steps

- [First Project Tutorial](first-project.md) - Create your first Rice-Factor project
- [Core Concepts](concepts.md) - Understand how Rice-Factor works
- [CLI Reference](../../reference/cli/commands.md) - Explore all commands
