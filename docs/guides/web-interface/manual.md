# Web Interface Manual

This manual provides a detailed reference for all views and features in the Rice-Factor Web Interface.

**Last Updated:** January 2026

---

## Starting the Web Interface

Launch the web server from your project directory:

```bash
rice-factor web serve
```

By default, the server runs at `http://localhost:8000`. Open this URL in your browser.

### Command Options

| Option | Description |
|--------|-------------|
| `--host` | Bind address (default: `127.0.0.1`) |
| `--port` | Port number (default: `8000`) |
| `--reload` | Enable hot reload for development |

```bash
# Example: bind to all interfaces on port 3000
rice-factor web serve --host 0.0.0.0 --port 3000
```

---

## Dashboard

The **Dashboard** is your landing page, providing an immediate snapshot of project health.

![Dashboard Screenshot](../../assets/screenshots/web-dashboard.png)

### Statistics Cards

The top row displays four key metrics:

| Card | Description |
|------|-------------|
| **Total Artifacts** | Count of all artifacts in the project |
| **Pending Approvals** | Items waiting for review |
| **Pending Diffs** | Code changes awaiting approval |
| **Approved Today** | Items approved in the current day |

### Artifacts by Type

A breakdown showing counts for each artifact type:
- ProjectPlan
- ArchitecturePlan
- ScaffoldPlan
- TestPlan
- ImplementationPlan
- RefactorPlan
- ValidationResult
- FailureReport
- ReconciliationPlan

### Artifacts by Status

Visual indicator of artifact states:

| Status | Color | Meaning |
|--------|-------|---------|
| **Draft** | Yellow | Awaiting approval |
| **Approved** | Green | Ready for use |
| **Locked** | Red | Immutable (TestPlan) |

### Phase Indicator

The top-right corner shows the current project phase:
- **Uninitialized** - Project not yet set up
- **Planning** - Ready to create project plan
- **Scaffolded** - File structure created
- **Implementing** - Active development

### Activity Feed

A real-time list of recent actions:
- Plan generation events
- Artifact approvals
- Test execution results
- File modifications
- Command executions

---

## Artifacts View

Navigate to **Artifacts** in the sidebar to browse all project artifacts.

### List View

The artifacts list provides:
- **Filter by Type** - Dropdown to select specific artifact types
- **Filter by Status** - Show only Draft, Approved, or Locked items
- **Sort Controls** - Order by creation date (newest/oldest)
- **Search** - Filter by artifact ID or content

Each artifact row displays:
- Status badge (colored indicator)
- Artifact type
- Truncated ID
- Creation timestamp
- Creator (system, human, or llm_compiler)

### Detail View

Click any artifact to open its detail view:

**Header Section:**
- Full artifact ID
- Type badge
- Status badge
- Version number
- Created/Updated timestamps

**Content Section:**
- Monaco editor with JSON syntax highlighting
- Read-only view of artifact payload
- Expand/collapse nested objects

**Actions:**

| Button | Availability | Effect |
|--------|--------------|--------|
| **Approve** | Draft artifacts only | Moves to APPROVED status |
| **Lock** | TestPlan only (when APPROVED) | Moves to LOCKED status (immutable) |
| **Compare** | When versions exist | Opens version comparison view |

### Version History

If an artifact has multiple versions:
1. Click **Compare** to open version selector
2. Select two versions to compare
3. View side-by-side diff of changes

---

## Diffs View

The **Diffs** view is optimized for code review.

### List View

Pending diffs are listed with:
- Target file path
- Lines added/removed counts
- Associated artifact ID
- Creation timestamp

### Detail View (Diff Reviewer)

The diff reviewer provides a professional code review interface:

**Split View:**
- Left panel: Original code
- Right panel: Modified code
- Synchronized scrolling
- Line numbers with diff markers

**Diff Indicators:**
- Green background: Added lines
- Red background: Removed lines
- Yellow highlight: Modified lines

**Syntax Highlighting:**
- Python, JavaScript, TypeScript, Go, Rust
- JSON, YAML, Markdown
- And more (via Monaco editor)

### Inline Comments

Add comments directly on specific lines:

1. Click the line number gutter
2. Type your comment in the popup
3. Click **Add Comment**

Comments are saved and visible to all reviewers.

### Actions

| Button | Effect |
|--------|--------|
| **Approve** | Mark diff as correct, ready to apply |
| **Reject** | Mark as incorrect, requires regeneration |
| **Apply** | Apply the diff to the filesystem (requires approval) |

---

## Approvals View

The **Approvals** view shows all items pending review in one place.

### Pending Items

Two sections:

**Artifacts Pending Approval:**
- List of DRAFT artifacts
- Quick approve buttons
- Links to detail views

**Diffs Pending Review:**
- List of pending diffs
- File path and change summary
- Links to diff reviewer

### Bulk Actions

For efficiency:
- Select multiple items
- Approve all selected
- Reject all selected (with reason)

---

## History View

The **History** view provides a complete audit trail.

### Event Log

Every action is recorded:
- Artifact creation/approval/lock
- Diff generation/approval/rejection
- Command execution
- Configuration changes
- Authentication events

### Filtering

| Filter | Options |
|--------|---------|
| **Action Type** | Select from dropdown |
| **User** | Filter by actor |
| **Date Range** | From/to date pickers |
| **Artifact ID** | Search specific artifact |

### Export

Download the audit log:

1. Apply desired filters
2. Click **Export** dropdown
3. Select format:
   - **JSON** - Machine-readable
   - **CSV** - Spreadsheet-compatible

---

## Configuration View

The **Configuration** view provides a YAML editor for project settings.

### Configuration Files

Two tabs:
- **Project Config** (`.rice-factor.yaml`)
- **User Config** (`~/.rice-factor/config.yaml`)

### Editor Features

- YAML syntax highlighting
- Real-time validation
- Error indicators for invalid syntax
- Auto-completion for known keys

### Editable Settings

```yaml
llm:
  provider: claude          # claude, openai, ollama, vllm
  model: claude-3-5-sonnet-20241022
  temperature: 0.0
  max_tokens: 4096

execution:
  dry_run: false
  auto_approve: false

output:
  color: true
  verbose: false
  log_level: INFO

paths:
  artifacts_dir: .project/artifacts
  audit_dir: .project/audit
```

### Saving Changes

1. Edit the YAML content
2. Click **Save**
3. Changes take effect immediately (some may require restart)

---

## Commands View

The **Commands** view allows executing Rice-Factor CLI commands from the browser.

### Command Selector

Dropdown with available commands:
- `plan project`
- `plan architecture`
- `plan tests`
- `plan impl <file>`
- `scaffold`
- `impl <file>`
- `test`
- `validate`
- And more...

### Arguments Input

Text field for command arguments:
```
# Examples
--dry-run
--verbose
src/main.py
```

### Execution

1. Select command from dropdown
2. Enter arguments (if needed)
3. Click **Run**
4. Watch real-time output

### Output Display

Terminal-like output area showing:
- Command being executed
- Stdout (standard output)
- Stderr (error output)
- Exit code
- Execution duration

### Command History

Previous commands are saved:
- Click to re-run
- Edit and execute variations

---

## Login View

The **Login** view handles authentication.

### Authentication Options

| Method | Description |
|--------|-------------|
| **Anonymous** | No login required (local development) |
| **GitHub OAuth** | Sign in with GitHub account |
| **Google OAuth** | Sign in with Google account |

### OAuth Flow

1. Click provider button (GitHub/Google)
2. Redirect to provider login page
3. Authorize Rice-Factor application
4. Redirect back to dashboard

### Session Management

- Sessions persist across browser restarts
- Click **Logout** in header to end session
- Automatic timeout after inactivity (configurable)

---

## Init View

The **Init** view appears for uninitialized projects.

### Project Initialization

If the project directory lacks a `.project/` folder:

1. Welcome screen appears automatically
2. Click **Initialize Project**
3. Answer the questionnaire (optional)
4. `.project/` directory is created
5. Redirect to Dashboard

### Questionnaire

Interactive questions about your project:
- Project name and description
- Target language(s)
- Testing framework
- Architecture preferences
- Team size and workflow

Answers populate `.project/requirements.md`.

---

## Navigation

### Sidebar

The left sidebar provides navigation:

| Icon | Page | Shortcut |
|------|------|----------|
| Dashboard icon | Dashboard | `D` |
| Box icon | Artifacts | `A` |
| Code icon | Diff Review | `R` |
| Check icon | Approvals | `P` |
| Clock icon | History | `H` |
| Settings icon | Configuration | `C` |
| Terminal icon | Commands | `X` |

### Header

The header shows:
- Rice-Factor logo (click to go home)
- Project name
- Phase indicator
- User info / Login button

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `?` | Show help modal |
| `D` | Go to Dashboard |
| `A` | Go to Artifacts |
| `R` | Go to Diff Review |
| `/` | Focus search |
| `Esc` | Close modal/cancel |

---

## Real-Time Updates

The Web UI uses WebSocket connections for live updates:

- **Artifact changes** - New artifacts appear automatically
- **Status updates** - Approvals reflect immediately
- **Command output** - Streams in real-time
- **Activity feed** - Updates without refresh

### Connection Status

The footer shows connection status:
- Green dot: Connected
- Yellow dot: Reconnecting
- Red dot: Disconnected

---

## Troubleshooting

### Common Issues

**"Cannot connect to server"**
- Ensure `rice-factor web serve` is running
- Check the port is not in use
- Verify firewall settings

**"Not initialized"**
- Run `rice-factor init` from CLI, or
- Use the Init view in the browser

**"Authentication required"**
- Configure OAuth providers, or
- Enable anonymous mode in settings

### Browser Compatibility

Tested browsers:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Performance Tips

- Close unused tabs (WebSocket connections)
- Use filters to limit displayed items
- Export large history sets instead of scrolling

---

## See Also

- [Web Interface Overview](overview.md) - Getting started
- [Web Interface Workflows](workflows.md) - Common tasks
- [REST API Reference](../../reference/api/rest-api.md) - API documentation
- [WebSocket Events](../../reference/api/websocket-events.md) - Real-time events
