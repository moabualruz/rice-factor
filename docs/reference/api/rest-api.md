# REST API Reference

The Rice-Factor Web UI is powered by a FastAPI backend that exposes a comprehensive REST API. This reference documents all available endpoints.

**Base URL:** `http://localhost:8000/api/v1`

---

## Authentication

### GET /auth/status

Get current authentication status.

**Response:**
```json
{
  "authenticated": true,
  "user": {
    "id": "user-123",
    "name": "John Doe",
    "email": "john@example.com",
    "provider": "github"
  }
}
```

### GET /auth/providers

List available OAuth providers.

**Response:**
```json
{
  "providers": ["github", "google"]
}
```

### GET /auth/github/login

Initiate GitHub OAuth flow. Redirects to GitHub.

### GET /auth/github/callback

GitHub OAuth callback endpoint.

### GET /auth/google/login

Initiate Google OAuth flow. Redirects to Google.

### GET /auth/google/callback

Google OAuth callback endpoint.

### POST /auth/logout

Clear the current session.

---

## Projects

### GET /projects/current

Get information about the current project.

**Response:**
```json
{
  "name": "my-project",
  "root": "/path/to/project",
  "initialized": true,
  "phase": "implementing"
}
```

### GET /projects/phase

Get the current project phase and available commands.

**Response:**
```json
{
  "phase": "implementing",
  "description": "Active development phase",
  "available_commands": ["plan impl", "impl", "apply", "test"]
}
```

### GET /projects/config

Get project configuration from `.project/`.

**Response:**
```json
{
  "llm": {
    "provider": "claude",
    "model": "claude-3-5-sonnet-20241022"
  },
  "paths": {
    "artifacts_dir": ".project/artifacts"
  }
}
```

### GET /projects

List sibling projects (other Rice-Factor projects in parent directory).

### POST /projects/switch

Switch to a different project.

**Request:**
```json
{
  "project_path": "/path/to/other-project"
}
```

### POST /projects/init

Initialize a new Rice-Factor project via API.

**Request:**
```json
{
  "project_name": "my-new-project",
  "force": false
}
```

---

## Artifacts

### GET /artifacts

List all artifacts with optional filtering.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by artifact type (e.g., `project_plan`, `test_plan`) |
| `status` | string | Filter by status (`draft`, `approved`, `locked`) |
| `limit` | int | Maximum number of results (default: 50) |
| `offset` | int | Pagination offset |

**Response:**
```json
{
  "artifacts": [
    {
      "id": "abc123",
      "type": "project_plan",
      "status": "approved",
      "version": 1,
      "created_at": "2024-01-15T10:30:00Z",
      "created_by": "llm_compiler"
    }
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

### GET /artifacts/{id}

Get a single artifact by ID.

**Response:**
```json
{
  "id": "abc123",
  "type": "project_plan",
  "status": "approved",
  "version": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "created_by": "llm_compiler",
  "payload": {
    "domains": [...],
    "modules": [...],
    "constraints": [...]
  }
}
```

### POST /artifacts/{id}/approve

Approve a draft artifact.

**Request:**
```json
{
  "notes": "Looks good, approved for implementation"
}
```

**Response:**
```json
{
  "id": "abc123",
  "status": "approved",
  "approved_at": "2024-01-15T11:00:00Z",
  "approved_by": "user"
}
```

### POST /artifacts/{id}/lock

Lock an approved artifact (TestPlan only).

**Response:**
```json
{
  "id": "abc123",
  "status": "locked",
  "locked_at": "2024-01-15T11:05:00Z"
}
```

### GET /artifacts/stats

Get artifact statistics for the dashboard.

**Response:**
```json
{
  "total": 15,
  "by_type": {
    "project_plan": 1,
    "test_plan": 2,
    "implementation_plan": 8,
    "refactor_plan": 4
  },
  "by_status": {
    "draft": 5,
    "approved": 8,
    "locked": 2
  }
}
```

### GET /artifacts/graph/mermaid

Get the full artifact dependency graph as Mermaid diagram.

**Response:**
```json
{
  "mermaid": "graph TD\n  A[ProjectPlan] --> B[TestPlan]\n  B --> C[ImplPlan-1]"
}
```

### GET /artifacts/{id}/graph/mermaid

Get dependencies for a single artifact.

### GET /artifacts/{id}/versions

Get version history for an artifact.

**Response:**
```json
{
  "versions": [
    {"version": 1, "created_at": "2024-01-15T10:00:00Z"},
    {"version": 2, "created_at": "2024-01-15T12:00:00Z"}
  ]
}
```

### GET /artifacts/{id}/versions/{version}

Get a specific version of an artifact.

---

## Diffs

### GET /diffs

List all diffs with optional filtering.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (`pending`, `approved`, `rejected`) |
| `file` | string | Filter by target file path |

**Response:**
```json
{
  "diffs": [
    {
      "id": "diff-001",
      "artifact_id": "impl-abc123",
      "file_path": "src/main.py",
      "status": "pending",
      "created_at": "2024-01-15T14:00:00Z"
    }
  ]
}
```

### GET /diffs/{id}

Get a single diff with computed modified version.

**Response:**
```json
{
  "id": "diff-001",
  "artifact_id": "impl-abc123",
  "file_path": "src/main.py",
  "status": "pending",
  "original": "def hello():\n    pass",
  "modified": "def hello():\n    print('Hello, World!')",
  "unified_diff": "--- a/src/main.py\n+++ b/src/main.py\n@@ -1,2 +1,2 @@\n def hello():\n-    pass\n+    print('Hello, World!')"
}
```

### POST /diffs/{id}/approve

Approve a diff for application.

**Request:**
```json
{
  "notes": "Code looks correct"
}
```

### POST /diffs/{id}/reject

Reject a diff with reason.

**Request:**
```json
{
  "reason": "Missing error handling"
}
```

### GET /diffs/{id}/comments

List inline comments on a diff.

**Response:**
```json
{
  "comments": [
    {
      "id": "comment-001",
      "line": 15,
      "content": "Consider adding a docstring here",
      "author": "reviewer",
      "created_at": "2024-01-15T15:00:00Z"
    }
  ]
}
```

### POST /diffs/{id}/comments

Add an inline comment.

**Request:**
```json
{
  "line": 15,
  "content": "Consider adding a docstring here"
}
```

### PUT /diffs/{id}/comments/{comment_id}

Update an existing comment.

### DELETE /diffs/{id}/comments/{comment_id}

Delete a comment.

---

## Approvals

### GET /approvals

List all pending approvals (artifacts and diffs).

**Response:**
```json
{
  "pending": [
    {
      "id": "abc123",
      "type": "artifact",
      "artifact_type": "implementation_plan",
      "created_at": "2024-01-15T14:00:00Z"
    },
    {
      "id": "diff-001",
      "type": "diff",
      "file_path": "src/main.py",
      "created_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

### GET /approvals/history

Get approval history with pagination.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Maximum results |
| `offset` | int | Pagination offset |
| `action` | string | Filter by action (`approved`, `rejected`, `locked`) |

### POST /approvals/{id}/revoke

Revoke an approval (move from `approved` back to `draft`).

---

## History

### GET /history

Get audit log with filtering.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Filter by action type |
| `user` | string | Filter by user |
| `artifact_id` | string | Filter by artifact |
| `from_date` | string | Start date (ISO format) |
| `to_date` | string | End date (ISO format) |
| `limit` | int | Maximum results |
| `offset` | int | Pagination offset |

**Response:**
```json
{
  "entries": [
    {
      "id": "entry-001",
      "timestamp": "2024-01-15T10:30:00Z",
      "action": "artifact.created",
      "user": "system",
      "artifact_id": "abc123",
      "details": {"type": "project_plan"}
    }
  ],
  "total": 150
}
```

### GET /history/actions

Get distinct action types for filtering.

**Response:**
```json
{
  "actions": [
    "artifact.created",
    "artifact.approved",
    "artifact.locked",
    "diff.created",
    "diff.approved",
    "diff.rejected",
    "command.executed"
  ]
}
```

### POST /history/export

Export audit log as CSV or JSON.

**Request:**
```json
{
  "format": "csv",
  "filters": {
    "from_date": "2024-01-01",
    "to_date": "2024-01-31"
  }
}
```

**Response:** File download

### GET /history/stats

Get statistics by action type and user.

**Response:**
```json
{
  "by_action": {
    "artifact.created": 25,
    "artifact.approved": 20,
    "diff.approved": 15
  },
  "by_user": {
    "system": 40,
    "user": 20
  }
}
```

---

## Configuration

### GET /configuration

Get merged configuration with raw file contents.

**Response:**
```json
{
  "merged": {
    "llm": {"provider": "claude", "model": "..."},
    "execution": {"dry_run": false}
  },
  "files": {
    "project": "llm:\n  provider: claude\n...",
    "user": "output:\n  color: true\n..."
  }
}
```

### POST /configuration

Update project or user configuration.

**Request:**
```json
{
  "scope": "project",
  "content": "llm:\n  provider: openai\n  model: gpt-4-turbo"
}
```

---

## Commands

### POST /commands/execute

Execute a Rice-Factor CLI command from the Web UI.

**Request:**
```json
{
  "command": "plan",
  "args": ["project", "--dry-run"]
}
```

**Response:**
```json
{
  "exit_code": 0,
  "stdout": "Generated ProjectPlan artifact...",
  "stderr": "",
  "duration_ms": 1523
}
```

---

## Health

### GET /health

Simple health probe.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Artifact not found",
  "status_code": 404
}
```

Common status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict (e.g., artifact already approved) |
| 500 | Internal server error |
