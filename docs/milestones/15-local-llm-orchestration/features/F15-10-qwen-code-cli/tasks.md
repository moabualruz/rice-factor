# F15-10: Qwen Code CLI Adapter - Tasks

## Tasks
### T15-10-01: Implement QwenCodeAdapter ✅
### T15-10-02: Add OAuth Authentication Support ✅
### T15-10-03: Implement Plan Mode Integration ✅
### T15-10-04: Add Local Model Routing (Ollama) ✅
### T15-10-05: Implement Output Parsing ✅
### T15-10-06: Write Unit Tests ✅

## Estimated Test Count: ~7 (Actual: 10)

## Implementation Notes

### CLI Command Pattern
```bash
# Basic execution
qwen-code "prompt"

# With specific model
qwen-code --model qwen3-coder "prompt"
```

### Key Features
- OAuth authentication with 2000 free requests/day
- Plan mode for complex tasks
- SubAgents for parallel work
- Local model support via Ollama

### Model Support
- Qwen3-Coder-480B-A35B (flagship)
- Qwen3-Coder-32B (fast, local)
- OpenAI-compatible API support

### References
- [Qwen Code CLI](https://github.com/QwenLM/qwen-code)
- [Qwen3-Coder Models](https://github.com/QwenLM/Qwen3-Coder)
