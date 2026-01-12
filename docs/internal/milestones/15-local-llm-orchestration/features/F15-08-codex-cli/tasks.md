# F15-08: OpenAI Codex CLI Adapter - Tasks

## Tasks
### T15-08-01: Implement CodexAdapter ✅
### T15-08-02: Add Non-Interactive Execution Mode ✅
### T15-08-03: Implement Approval Mode Configuration ✅
### T15-08-04: Add JSON Output Parsing ✅
### T15-08-05: Implement Model Selection ✅
### T15-08-06: Write Unit Tests ✅

## Estimated Test Count: ~7 (Actual: 10)

## Implementation Notes

### CLI Command Pattern
```bash
# Non-interactive execution
codex exec --approval-mode suggest --output-format json "prompt"
```

### Approval Modes
- `suggest` - Suggest changes, require confirmation
- `auto-edit` - Auto-apply safe edits
- `full-auto` - Fully autonomous execution

### Key Features
- `exec` subcommand for scripted/CI-style runs
- Model selection via `--model` flag
- Structured JSON output
- Session resume capability

### References
- [OpenAI Codex CLI](https://github.com/openai/codex)
- [CLI Reference](https://developers.openai.com/codex/cli/reference/)
