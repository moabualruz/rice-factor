# F15-11: Aider CLI Adapter - Tasks

## Tasks
### T15-11-01: Implement AiderAdapter
### T15-11-02: Add Non-Interactive Mode Support
### T15-11-03: Implement Model Selection
### T15-11-04: Add Local Model Routing (Ollama)
### T15-11-05: Implement Git Integration Handling
### T15-11-06: Parse Modified Files from Output
### T15-11-07: Write Unit Tests

## Estimated Test Count: ~8

## Implementation Notes

### CLI Command Pattern
```bash
# Non-interactive with cloud model
aider --yes --message "prompt" --model claude-3-5-sonnet

# With local model
aider --yes --message "prompt" --model ollama/codestral

# Without auto-commits
aider --yes --no-auto-commits --message "prompt"
```

### Key Features
- Works with 100+ LLM models
- Automatic git commits
- Repo map for large codebases
- Voice input support

### Model Options
- Cloud: Claude 3.5 Sonnet, GPT-4o, DeepSeek
- Local: ollama/codestral, ollama/qwen3-coder

### Output Parsing
- "Wrote file.py" lines indicate modified files
- "Added file.py to the chat" for context files

### References
- [Aider](https://github.com/Aider-AI/aider)
- [Documentation](https://aider.chat/docs/)
