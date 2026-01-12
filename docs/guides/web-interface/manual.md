# Web Interface Manual

This manual provides a detailed reference for all views and features in the Rice-Factor Web Interface.

## Dashboard

The **Dashboard** is your landing page. It provides an immediate snapshot of the project's health.

### Statistics Cards
- **Artifacts**: Total number of artifacts and how many are in specific states (Draft, Approved, Locked).
- **Pending Approvals**: Number of items waiting for your attention.
- **Phase**: The current development phase (e.g., `PLANNING`, `IMPLEMENTING`).

### Activity Feed
A real-time list of actions performed in the project, such as:
- Plan generation
- User approvals
- Test execution results
- File modifications

## Artifacts View

Navigate to **Artifacts** to browse the project's intermediate representations.

### List View
- Filter by type (`ProjectPlan`, `TestPlan`, etc.)
- Filter by status (`DRAFT`, `APPROVED`, etc.)
- Sort by creation date

### Detail View
Clicking an artifact opens the detail view:
- **Metadata**: Created at, Author, ID.
- **Content**: A read-only Monaco editor showing the JSON content.
- **Actions**:
    - **Approve**: Move artifact from `DRAFT` to `APPROVED`.
    - **Lock**: (TestPlan only) Move to `LOCKED` state.

## Diffs View

The **Diffs** view is optimized for code review.

### Review Interface
- **Split View**: See original vs. modified code side-by-side.
- **Language Aware**: Syntax highlighting for Python, JSON, Markdown, etc.
- **Inline Comments**: (Coming Soon) Add comments directly on lines of code.

### Actions
- **Approve**: Signals that the implementation is correct.
- **Reject**: Signals that the LLM needs to retry.
- **Apply**: Applies the approved diff to the filesystem.

## History View

The **History** view provides a complete audit trail. It logs every CLI command and API call.

- **Replay**: (Coming Soon) Re-run a sequence of events.
- **Export**: Download the audit log as JSON or CSV.
