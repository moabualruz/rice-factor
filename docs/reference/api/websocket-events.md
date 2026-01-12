# WebSocket Events Reference

The Rice-Factor Web UI uses WebSocket connections for real-time updates. This document describes all available events.

**WebSocket URL:** `ws://localhost:8000/ws`

---

## Connection

### Connecting

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to Rice-Factor');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

### Message Format

All WebSocket messages follow this format:

```json
{
  "type": "event.name",
  "payload": { ... },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## Artifact Events

### artifact.created

Fired when a new artifact is created.

```json
{
  "type": "artifact.created",
  "payload": {
    "id": "abc123",
    "artifact_type": "project_plan",
    "status": "draft",
    "created_by": "llm_compiler"
  }
}
```

### artifact.updated

Fired when an artifact is modified.

```json
{
  "type": "artifact.updated",
  "payload": {
    "id": "abc123",
    "changes": ["payload"],
    "version": 2
  }
}
```

### artifact.approved

Fired when an artifact is approved.

```json
{
  "type": "artifact.approved",
  "payload": {
    "id": "abc123",
    "approved_by": "user",
    "notes": "Looks good"
  }
}
```

### artifact.rejected

Fired when an artifact approval is revoked.

```json
{
  "type": "artifact.rejected",
  "payload": {
    "id": "abc123",
    "rejected_by": "user",
    "reason": "Needs revision"
  }
}
```

### artifact.locked

Fired when an artifact is locked (TestPlan only).

```json
{
  "type": "artifact.locked",
  "payload": {
    "id": "abc123",
    "locked_by": "user"
  }
}
```

---

## Diff Events

### diff.created

Fired when a new diff is generated.

```json
{
  "type": "diff.created",
  "payload": {
    "id": "diff-001",
    "artifact_id": "impl-abc123",
    "file_path": "src/main.py",
    "lines_added": 15,
    "lines_removed": 3
  }
}
```

### diff.approved

Fired when a diff is approved.

```json
{
  "type": "diff.approved",
  "payload": {
    "id": "diff-001",
    "approved_by": "user"
  }
}
```

### diff.rejected

Fired when a diff is rejected.

```json
{
  "type": "diff.rejected",
  "payload": {
    "id": "diff-001",
    "rejected_by": "user",
    "reason": "Missing error handling"
  }
}
```

### diff.applied

Fired when an approved diff is applied to the filesystem.

```json
{
  "type": "diff.applied",
  "payload": {
    "id": "diff-001",
    "file_path": "src/main.py"
  }
}
```

---

## Command Events

### command.started

Fired when a CLI command begins execution.

```json
{
  "type": "command.started",
  "payload": {
    "command_id": "cmd-001",
    "command": "plan project",
    "started_at": "2024-01-15T10:30:00Z"
  }
}
```

### command.output

Fired for streaming command output (stdout/stderr).

```json
{
  "type": "command.output",
  "payload": {
    "command_id": "cmd-001",
    "stream": "stdout",
    "content": "Generating ProjectPlan..."
  }
}
```

### command.completed

Fired when a command finishes execution.

```json
{
  "type": "command.completed",
  "payload": {
    "command_id": "cmd-001",
    "exit_code": 0,
    "duration_ms": 1523
  }
}
```

### command.failed

Fired when a command fails.

```json
{
  "type": "command.failed",
  "payload": {
    "command_id": "cmd-001",
    "exit_code": 1,
    "error": "LLM provider error: rate limited"
  }
}
```

---

## Test Events

### test.started

Fired when test suite execution begins.

```json
{
  "type": "test.started",
  "payload": {
    "test_run_id": "run-001",
    "total_tests": 42
  }
}
```

### test.passed

Fired when a test passes.

```json
{
  "type": "test.passed",
  "payload": {
    "test_run_id": "run-001",
    "test_name": "test_user_creation",
    "duration_ms": 125
  }
}
```

### test.failed

Fired when a test fails.

```json
{
  "type": "test.failed",
  "payload": {
    "test_run_id": "run-001",
    "test_name": "test_user_deletion",
    "error": "AssertionError: Expected 204, got 404",
    "duration_ms": 89
  }
}
```

### test.completed

Fired when test suite finishes.

```json
{
  "type": "test.completed",
  "payload": {
    "test_run_id": "run-001",
    "passed": 40,
    "failed": 2,
    "skipped": 0,
    "duration_ms": 5230
  }
}
```

---

## Phase Events

### phase.changed

Fired when the project phase changes.

```json
{
  "type": "phase.changed",
  "payload": {
    "previous_phase": "planning",
    "current_phase": "scaffolded",
    "available_commands": ["plan tests", "lock tests"]
  }
}
```

---

## System Events

### system.error

Fired on system-level errors.

```json
{
  "type": "system.error",
  "payload": {
    "error": "Database connection lost",
    "severity": "critical"
  }
}
```

### system.notification

Fired for general notifications.

```json
{
  "type": "system.notification",
  "payload": {
    "message": "Artifact cache cleared",
    "severity": "info"
  }
}
```

---

## Client-Side Implementation

### Vue 3 Composable Example

```typescript
// composables/useWebSocket.ts
import { ref, onMounted, onUnmounted } from 'vue';

export function useWebSocket() {
  const connected = ref(false);
  const lastEvent = ref(null);
  let ws: WebSocket | null = null;

  const connect = () => {
    ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      connected.value = true;
    };

    ws.onmessage = (event) => {
      lastEvent.value = JSON.parse(event.data);
    };

    ws.onclose = () => {
      connected.value = false;
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };
  };

  onMounted(connect);
  onUnmounted(() => ws?.close());

  return { connected, lastEvent };
}
```

### Event Handler Pattern

```typescript
// stores/events.ts
import { defineStore } from 'pinia';

export const useEventStore = defineStore('events', {
  state: () => ({
    artifacts: [],
    diffs: [],
  }),

  actions: {
    handleEvent(event: { type: string; payload: any }) {
      switch (event.type) {
        case 'artifact.created':
          this.artifacts.push(event.payload);
          break;
        case 'artifact.approved':
          const artifact = this.artifacts.find(a => a.id === event.payload.id);
          if (artifact) artifact.status = 'approved';
          break;
        // ... handle other events
      }
    }
  }
});
```

---

## Subscribing to Specific Events

You can subscribe to specific event types by sending a subscription message:

```json
{
  "action": "subscribe",
  "events": ["artifact.*", "diff.approved"]
}
```

To unsubscribe:

```json
{
  "action": "unsubscribe",
  "events": ["artifact.*"]
}
```

---

## Heartbeat

The server sends periodic heartbeat messages:

```json
{
  "type": "heartbeat",
  "payload": {
    "server_time": "2024-01-15T10:30:00Z"
  }
}
```

Clients should respond with:

```json
{
  "action": "pong"
}
```

If no pong is received within 30 seconds, the connection may be closed.
