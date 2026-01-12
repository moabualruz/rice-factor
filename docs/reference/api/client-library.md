# TypeScript Client Library

The Rice-Factor frontend includes a TypeScript API client for interacting with the backend. This document covers its usage and available methods.

---

## Installation

The client is part of the Rice-Factor frontend package. For standalone use:

```bash
npm install @rice-factor/api-client
```

Or copy the client files from `rice_factor_web/frontend/src/api/`.

---

## Setup

```typescript
import { createApiClient } from '@rice-factor/api-client';

const api = createApiClient({
  baseUrl: 'http://localhost:8000/api/v1',
  // Optional: custom fetch implementation
  fetch: window.fetch,
});
```

---

## Artifacts API

### List Artifacts

```typescript
const { artifacts, total } = await api.artifacts.list({
  type: 'project_plan',
  status: 'draft',
  limit: 50,
  offset: 0,
});
```

### Get Single Artifact

```typescript
const artifact = await api.artifacts.get('abc123');
console.log(artifact.payload);
```

### Approve Artifact

```typescript
await api.artifacts.approve('abc123', {
  notes: 'Looks good, approved for implementation',
});
```

### Lock Artifact

```typescript
await api.artifacts.lock('abc123');
```

### Get Artifact Stats

```typescript
const stats = await api.artifacts.stats();
console.log(stats.by_type.project_plan); // 5
console.log(stats.by_status.approved);   // 12
```

### Get Artifact Graph

```typescript
const { mermaid } = await api.artifacts.graph();
// Render with Mermaid.js
```

### Get Version History

```typescript
const { versions } = await api.artifacts.versions('abc123');
const oldVersion = await api.artifacts.version('abc123', 1);
```

---

## Diffs API

### List Diffs

```typescript
const { diffs } = await api.diffs.list({
  status: 'pending',
});
```

### Get Diff Details

```typescript
const diff = await api.diffs.get('diff-001');
console.log(diff.original);
console.log(diff.modified);
console.log(diff.unified_diff);
```

### Approve Diff

```typescript
await api.diffs.approve('diff-001', {
  notes: 'Code looks correct',
});
```

### Reject Diff

```typescript
await api.diffs.reject('diff-001', {
  reason: 'Missing error handling',
});
```

### Diff Comments

```typescript
// List comments
const { comments } = await api.diffs.comments('diff-001');

// Add comment
await api.diffs.addComment('diff-001', {
  line: 15,
  content: 'Consider adding a docstring here',
});

// Update comment
await api.diffs.updateComment('diff-001', 'comment-001', {
  content: 'Updated comment text',
});

// Delete comment
await api.diffs.deleteComment('diff-001', 'comment-001');
```

---

## Approvals API

### List Pending Approvals

```typescript
const { pending } = await api.approvals.list();

pending.forEach(item => {
  if (item.type === 'artifact') {
    console.log(`Artifact ${item.artifact_type}: ${item.id}`);
  } else {
    console.log(`Diff for ${item.file_path}: ${item.id}`);
  }
});
```

### Get Approval History

```typescript
const { records } = await api.approvals.history({
  limit: 100,
  action: 'approved',
});
```

### Revoke Approval

```typescript
await api.approvals.revoke('abc123');
```

---

## History API

### Query History

```typescript
const { entries, total } = await api.history.query({
  action: 'artifact.approved',
  from_date: '2024-01-01',
  to_date: '2024-01-31',
  limit: 100,
});
```

### Get Action Types

```typescript
const { actions } = await api.history.actions();
// ['artifact.created', 'artifact.approved', ...]
```

### Export History

```typescript
// Export as CSV
const csvBlob = await api.history.export({
  format: 'csv',
  filters: { from_date: '2024-01-01' },
});

// Download
const url = URL.createObjectURL(csvBlob);
const a = document.createElement('a');
a.href = url;
a.download = 'audit-log.csv';
a.click();
```

### Get Stats

```typescript
const stats = await api.history.stats();
console.log(stats.by_action);
console.log(stats.by_user);
```

---

## Projects API

### Get Current Project

```typescript
const project = await api.projects.current();
console.log(project.name);
console.log(project.initialized);
```

### Get Phase

```typescript
const phase = await api.projects.phase();
console.log(phase.phase);           // 'implementing'
console.log(phase.available_commands);
```

### Get Configuration

```typescript
const config = await api.projects.config();
console.log(config.llm.provider);
```

### List Projects

```typescript
const { projects } = await api.projects.list();
```

### Switch Project

```typescript
await api.projects.switch('/path/to/other-project');
// Note: Requires backend restart
```

### Initialize Project

```typescript
await api.projects.init({
  project_name: 'my-new-project',
  force: false,
});
```

---

## Configuration API

### Get Configuration

```typescript
const config = await api.configuration.get();
console.log(config.merged);       // Effective config
console.log(config.files.project); // Raw YAML
```

### Update Configuration

```typescript
await api.configuration.update({
  scope: 'project',  // or 'user'
  content: `
llm:
  provider: openai
  model: gpt-4-turbo
`,
});
```

---

## Commands API

### Execute Command

```typescript
const result = await api.commands.execute({
  command: 'plan',
  args: ['project', '--dry-run'],
});

console.log(result.exit_code);
console.log(result.stdout);
console.log(result.stderr);
console.log(result.duration_ms);
```

---

## Authentication API

### Get Status

```typescript
const status = await api.auth.status();
if (status.authenticated) {
  console.log(`Logged in as ${status.user.name}`);
}
```

### Get Providers

```typescript
const { providers } = await api.auth.providers();
// ['github', 'google']
```

### Login

```typescript
// Redirect to OAuth provider
window.location.href = api.auth.loginUrl('github');
```

### Logout

```typescript
await api.auth.logout();
```

---

## Error Handling

The client throws typed errors:

```typescript
import { ApiError, NotFoundError, UnauthorizedError } from '@rice-factor/api-client';

try {
  const artifact = await api.artifacts.get('nonexistent');
} catch (error) {
  if (error instanceof NotFoundError) {
    console.log('Artifact not found');
  } else if (error instanceof UnauthorizedError) {
    // Redirect to login
    window.location.href = '/login';
  } else if (error instanceof ApiError) {
    console.error(`API error: ${error.message} (${error.statusCode})`);
  }
}
```

---

## TypeScript Types

The client exports TypeScript types for all API responses:

```typescript
import type {
  Artifact,
  ArtifactType,
  ArtifactStatus,
  Diff,
  DiffStatus,
  HistoryEntry,
  ProjectInfo,
  PhaseInfo,
  User,
} from '@rice-factor/api-client';

const artifact: Artifact = await api.artifacts.get('abc123');
```

### Type Definitions

```typescript
type ArtifactType =
  | 'project_plan'
  | 'architecture_plan'
  | 'scaffold_plan'
  | 'test_plan'
  | 'implementation_plan'
  | 'refactor_plan'
  | 'validation_result'
  | 'failure_report'
  | 'reconciliation_plan';

type ArtifactStatus = 'draft' | 'approved' | 'locked';

interface Artifact {
  id: string;
  type: ArtifactType;
  status: ArtifactStatus;
  version: number;
  created_at: string;
  created_by: 'system' | 'human' | 'llm_compiler';
  payload: Record<string, unknown>;
}

type DiffStatus = 'pending' | 'approved' | 'rejected' | 'applied';

interface Diff {
  id: string;
  artifact_id: string;
  file_path: string;
  status: DiffStatus;
  original: string;
  modified: string;
  unified_diff: string;
}

interface HistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user: string;
  artifact_id?: string;
  details: Record<string, unknown>;
}
```

---

## WebSocket Client

The client also includes a WebSocket wrapper:

```typescript
import { createWebSocketClient } from '@rice-factor/api-client';

const ws = createWebSocketClient({
  url: 'ws://localhost:8000/ws',
  reconnect: true,
  reconnectInterval: 3000,
});

// Subscribe to events
ws.on('artifact.created', (payload) => {
  console.log('New artifact:', payload.id);
});

ws.on('artifact.approved', (payload) => {
  console.log('Artifact approved:', payload.id);
});

// Connect
ws.connect();

// Disconnect when done
ws.disconnect();
```

---

## Usage with Pinia Store

```typescript
// stores/artifacts.ts
import { defineStore } from 'pinia';
import { createApiClient } from '@rice-factor/api-client';

const api = createApiClient({ baseUrl: '/api/v1' });

export const useArtifactStore = defineStore('artifacts', {
  state: () => ({
    artifacts: [] as Artifact[],
    loading: false,
    error: null as string | null,
  }),

  actions: {
    async fetchArtifacts(filters = {}) {
      this.loading = true;
      this.error = null;
      try {
        const { artifacts } = await api.artifacts.list(filters);
        this.artifacts = artifacts;
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },

    async approveArtifact(id: string, notes?: string) {
      await api.artifacts.approve(id, { notes });
      const artifact = this.artifacts.find(a => a.id === id);
      if (artifact) artifact.status = 'approved';
    },
  },
});
```
