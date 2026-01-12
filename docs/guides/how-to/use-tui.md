# Use TUI Mode

This guide explains how to use Rice-Factor's Terminal User Interface (TUI).

## Overview

The TUI provides an interactive interface for:
- Workflow navigation
- Artifact browsing
- Status monitoring
- Quick actions

## Starting the TUI

```bash
# Launch TUI in current directory
rice-factor tui

# Launch for specific project
rice-factor tui --project /path/to/project
```

## Interface Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Rice-Factor                                    Phase: PLANNING  │
├────────────────────────┬────────────────────────────────────────┤
│                        │                                        │
│  Workflow              │  Artifact Details                      │
│  ────────              │  ──────────────────                    │
│  ○ Init                │                                        │
│  ● Plan Project        │  ID: abc123-...                        │
│  ○ Plan Architecture   │  Type: ProjectPlan                     │
│  ○ Scaffold            │  Status: APPROVED                      │
│  ○ Plan Tests          │  Created: 2024-01-15                   │
│  ○ Lock Tests          │                                        │
│  ○ Implement           │  Payload:                              │
│  ○ Test                │  ├─ domains: 2                         │
│                        │  ├─ modules: 3                         │
│                        │  └─ constraints: ...                   │
│                        │                                        │
├────────────────────────┴────────────────────────────────────────┤
│ [Enter] Execute  [a] Approve  [l] Lock  [r] Refresh  [q] Quit  │
└─────────────────────────────────────────────────────────────────┘
```

## Navigation

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑`/`k` | Move up |
| `↓`/`j` | Move down |
| `Enter` | Execute selected action |
| `a` | Approve selected artifact |
| `l` | Lock selected artifact |
| `r` | Refresh display |
| `Tab` | Switch panels |
| `?` | Show help |
| `q` | Quit |

### Mouse Support

- Click to select items
- Scroll to navigate lists
- Double-click to execute

## Workflow Panel

The left panel shows the development workflow:

```
Workflow
────────
✓ Init                 # Completed
● Plan Project         # Current step
○ Plan Architecture    # Not started
○ Scaffold
○ Plan Tests
○ Lock Tests
○ Implement
○ Test
```

**Indicators:**
- `✓` Completed
- `●` Current/Active
- `○` Not started
- `✗` Failed

### Execute Workflow Steps

1. Select a step with arrow keys
2. Press `Enter` to execute
3. Follow prompts for required input

## Artifact Browser

The right panel shows artifact details:

```
Artifact Details
────────────────
ID: abc123-def456-...
Type: ProjectPlan
Status: APPROVED
Created: 2024-01-15 10:30:00
Updated: 2024-01-15 10:35:00

Payload:
├─ domains
│  ├─ name: "core"
│  └─ responsibility: "Business logic"
├─ modules: [...]
└─ constraints: [...]
```

### Browse Artifacts

1. Press `Tab` to switch to artifact panel
2. Use arrows to browse artifacts
3. Press `Enter` to view full details
4. Press `a` to approve (if DRAFT)
5. Press `l` to lock (if TestPlan)

## Status Bar

The bottom bar shows:

```
[Enter] Execute  [a] Approve  [l] Lock  [r] Refresh  [q] Quit
```

And phase information:
```
Phase: PLANNING  │  Artifacts: 3  │  Pending: 1
```

## Quick Actions

### Approve Artifact

1. Select artifact in browser
2. Press `a`
3. Confirm approval

### Lock TestPlan

1. Select TestPlan artifact
2. Press `l`
3. Type "LOCK" to confirm

### Refresh State

Press `r` to refresh:
- Reload artifacts from disk
- Update workflow status
- Check for changes

## Themes

The TUI uses Rice-Factor brand colors:

| Element | Color |
|---------|-------|
| Headers | Primary (#00a020) |
| Active items | Accent (#00c030) |
| Borders | Secondary (#009e20) |
| Background | Dark (#0a1a0a) |

## Configuration

TUI settings in `.rice-factor.yaml`:

```yaml
tui:
  refresh_interval: 5  # Auto-refresh seconds
  show_timestamps: true
  expand_payload: true
  color_scheme: dark   # dark or light
```

## Tips

### 1. Use TUI for Exploration

TUI is great for:
- Understanding project state
- Browsing artifacts
- Quick approvals

### 2. Switch to CLI for Complex Tasks

Use CLI when:
- Running multiple commands
- Scripting workflows
- Debugging issues

### 3. Keep It Open

Run TUI in one terminal while working in another:
- Terminal 1: `rice-factor tui`
- Terminal 2: Edit code, run tests

The TUI shows real-time status.

### 4. Keyboard-First

Learn keyboard shortcuts for speed:
- `j/k` navigation is faster than arrows
- `a` for approve, `l` for lock
- `?` shows all shortcuts

## Troubleshooting

### "Terminal too small"

Resize terminal to at least 80x24 characters.

### "Colors not displaying"

Ensure terminal supports 256 colors:
```bash
echo $TERM  # Should be xterm-256color or similar
```

### "TUI won't start"

Check Textual is installed:
```bash
pip install rice-factor[tui]
# or
pip install textual
```

### "Artifacts not showing"

Ensure you're in a Rice-Factor project:
```bash
ls .project/artifacts/
```

## Accessibility

The TUI supports:
- Keyboard-only navigation
- Screen reader compatibility (basic)
- High-contrast mode (future)

## What's Next?

- [Web Interface](../../reference/cli/commands.md#rice-factor-web) - Browser-based UI
- [CLI Reference](../../reference/cli/commands.md) - All commands
- [Configuration](../../reference/configuration/settings.md) - TUI settings
