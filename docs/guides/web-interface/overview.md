# Web Interface Overview

Rice-Factor includes a modern, responsive web interface for managing your development workflow. While the CLI is powerful, the Web UI provides a superior experience for reviewing artifacts, visualizing diffs, and auditing project history.

## Launching the Interface

To start the web server, run the following command in your project directory:

```bash
rice-factor web serve
```

By default, the interface will be available at **http://127.0.0.1:8000**.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--port`, `-p` | Port to bind to | `8000` |
| `--host`, `-h` | Host to bind to | `127.0.0.1` |
| `--reload`, `-r` | Enable hot reload (for contributors) | `False` |

## Key Features

- **Dashboard**: High-level overview of project status, active phase, and recent activity.
- **Artifact Explorer**: visual JSON editor and approval interface for all project artifacts.
- **Diff Reviewer**: Monaco-based diff editor for reviewing implementation plans and code changes.
- **Audit Logs**: Searchable history of every action taken in the project.
- **Real-time Updates**: WebSocket integration for live status updates.

## Navigation

The interface is divided into several main sections:

1.  **Dashboard**: The command center with project status overview.
2.  **Artifacts**: Manage Plans, Specs, and Reports.
3.  **Diffs**: Review and apply code changes.
4.  **Approvals**: Pending items requiring human intervention.
5.  **History**: Complete audit trail of all actions.
6.  **Configuration**: Edit project settings.
7.  **Commands**: Execute CLI commands from the browser.

![Web Interface Dashboard](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/web/web-dashboard.png)

### Quick Access to Key Views

| View | Screenshot |
|------|------------|
| **Artifacts** | ![Artifacts](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/web/web-artifacts.png) |
| **Diffs** | ![Diffs](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/web/web-diffs.png) |
| **History** | ![History](https://raw.githubusercontent.com/moabualruz/rice-factor/main/docs/assets/screenshots/web/web-history.png) |

For detailed documentation of each view, see the [Web Interface Manual](manual.md).
