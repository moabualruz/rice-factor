# F15-13: OpenCode CLI Adapter - Tasks

## Tasks
### T15-13-01: Implement OpenCodeAdapter ✅
### T15-13-02: Add Non-Interactive Run Mode ✅
### T15-13-03: Implement JSON Output Parsing ✅
### T15-13-04: Add Server Attach Mode (--attach) ✅
### T15-13-05: Implement Session Management ✅
### T15-13-06: Add Model Selection ✅
### T15-13-07: Write Unit Tests ✅

## Estimated Test Count: ~10 (Actual: 26)

## Implementation Notes

### Overview
OpenCode is an open-source AI coding agent built in Go that runs in the terminal. With 50k+ GitHub stars and 650k+ monthly users, it's a truly open alternative to Claude Code that supports nearly all AI providers.

### CLI Command Patterns
```bash
# Non-interactive mode with direct prompt
opencode run "Explain the use of context in Go"

# With JSON output format
opencode run --format json "prompt"

# With specific model
opencode run --model anthropic/claude-4-sonnet "prompt"

# Attach to running server (faster, no cold boot)
opencode serve  # Start server first
opencode run --attach http://localhost:4096 "prompt"

# Resume session
opencode run --session <session-id> "prompt"
opencode run --continue "prompt"  # Resume last session

# With file attachments
opencode run --file src/main.py "Review this code"
```

### Key Flags
| Flag | Short | Description |
|------|-------|-------------|
| `--format` | | Output format: `default` or `json` |
| `--attach` | | Connect to running server URL |
| `--session` | `-s` | Resume specific session ID |
| `--continue` | `-c` | Resume last session |
| `--model` | `-m` | Specify model as `provider/model` |
| `--file` | `-f` | Attach file(s) to message |
| `--title` | | Custom session title |
| `--share` | | Share the session |

### Supported Providers
OpenCode supports multiple AI providers:
- **Anthropic**: Claude 4 Sonnet, Claude 3.5/3.7 Sonnet, Claude 3 Haiku/Opus
- **OpenAI**: GPT-4.1, GPT-4.5, GPT-4o, O1/O3/O4 series
- **Google**: Gemini 2.5, 2.5 Flash, 2.0 Flash
- **GitHub Copilot**: Various models
- **AWS Bedrock**: Claude 3.7 Sonnet
- **Groq**: Llama, QWEN, Deepseek
- **Azure OpenAI**: GPT-4.x, O-series
- **VertexAI**: Gemini models
- **Local**: Self-hosted models via LOCAL_ENDPOINT

### Built-in Agents
- **build**: Default agent with full access for development
- **plan**: Read-only agent for analysis and exploration
- **general**: Subagent for complex multi-step tasks (@general)

### Installation Detection
```bash
# Check availability
which opencode

# Check version
opencode --version
```

### Configuration
OpenCode searches for config in:
1. `$HOME/.opencode.json`
2. `$XDG_CONFIG_HOME/opencode/.opencode.json`
3. `./.opencode.json` (local project)

### Server Mode (Performance Optimization)
For repeated calls, use server mode to avoid cold boot:
```bash
# Start server (Terminal 1)
opencode serve --port 4096

# Attach client calls (Terminal 2+)
opencode run --attach http://localhost:4096 "prompt"
```

### Output Parsing
JSON format provides structured output for programmatic parsing:
```json
{
  "type": "message",
  "content": "...",
  "files_modified": [...],
  "session_id": "..."
}
```

### References
- [OpenCode Website](https://opencode.ai/)
- [OpenCode Documentation](https://opencode.ai/docs/)
- [OpenCode CLI Reference](https://opencode.ai/docs/cli/)
- [GitHub Repository](https://github.com/sst/opencode)
- [Agents Documentation](https://opencode.ai/docs/agents/)
