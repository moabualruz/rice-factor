# Rice-Factor VS Code Extension

VS Code extension for the Rice-Factor LLM-Assisted Development System.

## Features

- **Artifact Viewer**: Browse artifacts in a tree view in the sidebar
- **Workflow View**: Track workflow progress with phase-aware navigation
- **Diff Preview**: Preview diffs before applying changes
- **Approval Actions**: Approve artifacts and apply diffs directly from VS Code

## Requirements

- VS Code 1.85.0 or higher
- Rice-Factor CLI installed (`pip install rice-factor`)

## Installation

### From VSIX

1. Download the `.vsix` file from releases
2. Install via `code --install-extension rice-factor-vscode-0.1.0.vsix`

### Development

1. Clone the repository
2. Run `npm install` in the `rice-factor-vscode` directory
3. Press F5 to launch a development host

## Commands

| Command | Description |
|---------|-------------|
| `Rice-Factor: Refresh Artifacts` | Refresh the artifact list |
| `Rice-Factor: Approve Artifact` | Approve a draft artifact |
| `Rice-Factor: View Diff` | View diff for an implementation artifact |
| `Rice-Factor: Apply Diff` | Apply an approved diff |

## Keyboard Shortcuts

No default shortcuts are bound. You can bind them via VS Code's keyboard shortcuts settings.

## Views

### Artifacts

Shows all artifacts organized by type:
- PROJECT_PLAN
- TEST_PLAN
- SCAFFOLD_PLAN
- IMPLEMENTATION_PLAN
- etc.

Icons indicate status:
- 📄 Draft
- ✓ Approved
- 🔒 Locked

### Workflow

Shows the current workflow phase:
- ⭕ Pending
- ➡️ Current
- ✅ Complete

## Development

```bash
# Install dependencies
npm install

# Compile
npm run compile

# Watch
npm run watch

# Run tests
npm test

# Lint
npm run lint
```

## License

MIT
