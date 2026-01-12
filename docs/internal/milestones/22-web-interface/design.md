# Milestone 22: Web Interface - Design

> **Status**: In Progress (Phase 2)
> **Priority**: P3

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │Dashboard │  │DiffReview│  │ Approvals│  │  History Browser │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
│       │             │             │                  │           │
│  ┌────┴─────────────┴─────────────┴──────────────────┴────────┐ │
│  │                  Toast Notifications                        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────┼─────────────┼─────────────┼─────────────────┼───────────┘
        └─────────────┴─────────────┴─────────────────┘
                              │ REST + WebSocket
┌─────────────────────────────┼───────────────────────────────────┐
│                        Backend (FastAPI)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Routes  │  │   Auth   │  │WebSocket │  │   Domain Services│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                     CLI Entry Point                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  rice-factor web serve | build                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Package Structure

```
rice_factor_web/                    # Separate package
├── __init__.py
├── py.typed
│
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app factory
│   ├── config.py                   # WebSettings (Dynaconf)
│   ├── deps.py                     # Dependency injection
│   │
│   ├── api/v1/
│   │   ├── __init__.py
│   │   ├── artifacts.py            # Artifact CRUD + approve/lock
│   │   ├── diffs.py                # Diff review + approve/reject
│   │   ├── approvals.py            # Approval workflows
│   │   ├── history.py              # Audit history + export
│   │   ├── auth.py                 # OAuth2 routes
│   │   ├── projects.py             # Project info + phase
│   │   └── comments.py             # NEW: Inline comments API
│   │
│   ├── schemas/
│   │   ├── artifact.py
│   │   ├── diff.py
│   │   ├── approval.py
│   │   ├── history.py
│   │   ├── auth.py
│   │   └── comment.py              # NEW: Comment schemas
│   │
│   ├── auth/
│   │   ├── oauth.py                # GitHub/Google OAuth
│   │   ├── session.py              # Secure cookie sessions
│   │   └── middleware.py           # Auth middleware
│   │
│   ├── websocket/
│   │   ├── manager.py              # Connection manager
│   │   └── events.py               # Event types
│   │
│   └── services/
│       ├── adapter.py              # Domain service adapter
│       └── comments.py             # NEW: Comments service
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   │
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── router/index.ts
│       │
│       ├── api/
│       │   ├── client.ts
│       │   ├── types.ts
│       │   ├── artifacts.ts
│       │   ├── diffs.ts
│       │   ├── approvals.ts
│       │   ├── history.ts
│       │   ├── auth.ts
│       │   ├── projects.ts
│       │   └── comments.ts         # NEW
│       │
│       ├── components/
│       │   ├── AppHeader.vue
│       │   ├── AppSidebar.vue
│       │   ├── StatsCard.vue
│       │   ├── PhaseIndicator.vue
│       │   ├── ActivityFeed.vue
│       │   ├── DiffViewer.vue
│       │   ├── MonacoDiffEditor.vue    # NEW: Monaco integration
│       │   ├── InlineComment.vue       # NEW: Comment component
│       │   ├── CommentThread.vue       # NEW: Comment thread
│       │   ├── ToastNotification.vue   # NEW: Toast component
│       │   ├── ToastContainer.vue      # NEW: Toast container
│       │   ├── ProjectSwitcher.vue     # NEW: Project switcher
│       │   ├── VersionCompare.vue      # NEW: Version comparison
│       │   └── MermaidDiagram.vue      # NEW: Mermaid rendering
│       │
│       ├── views/
│       │   ├── DashboardView.vue
│       │   ├── ArtifactsView.vue
│       │   ├── ArtifactDetailView.vue
│       │   ├── DiffsView.vue
│       │   ├── DiffDetailView.vue
│       │   ├── ApprovalsView.vue
│       │   ├── HistoryView.vue
│       │   └── LoginView.vue
│       │
│       ├── composables/
│       │   ├── useWebSocket.ts
│       │   ├── useArtifacts.ts
│       │   ├── useDiffs.ts
│       │   ├── useToast.ts             # NEW: Toast composable
│       │   └── useComments.ts          # NEW: Comments composable
│       │
│       ├── stores/
│       │   ├── auth.ts
│       │   ├── project.ts
│       │   ├── notifications.ts        # NEW: Notification store
│       │   └── comments.ts             # NEW: Comments store
│       │
│       └── assets/
│           └── main.css
│
├── tests/
│   ├── conftest.py
│   ├── backend/                    # pytest tests
│   └── frontend/                   # Vitest tests
│
└── docker/
    ├── Dockerfile
    ├── docker-compose.yml
    └── .env.example
```

---

## 3. CLI Commands

```bash
# Start web server
rice-factor web serve                 # Default port 8000
rice-factor web serve --port 8080     # Custom port
rice-factor web serve --host 0.0.0.0  # Bind to all interfaces
rice-factor web serve --reload        # Enable hot reload (dev)

# Build frontend
rice-factor web build                 # Build for production
rice-factor web build --outdir dist   # Custom output directory
```

### CLI Implementation

```python
# rice_factor/entrypoints/cli/commands/web.py
import typer
from pathlib import Path

app = typer.Typer(help="Web interface commands")

@app.command()
def serve(
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server host"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable hot reload"),
):
    """Start the web server."""
    import uvicorn
    from rice_factor_web.backend.main import create_app

    app = create_app()
    uvicorn.run(
        "rice_factor_web.backend.main:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )

@app.command()
def build(
    outdir: Path = typer.Option(Path("dist"), "--outdir", "-o", help="Output directory"),
):
    """Build frontend for production."""
    import subprocess
    frontend_dir = Path(__file__).parent.parent.parent.parent.parent / "rice_factor_web" / "frontend"
    subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
```

---

## 4. Enhanced Features Design

### 4.1 Toast Notification System

```typescript
// stores/notifications.ts
interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number  // ms, 0 = persistent
  action?: { label: string; handler: () => void }
}

// Triggered by WebSocket events
subscribe('artifact_approved', (event) => {
  toast.success('Artifact Approved', `${event.payload.artifact_type} approved`)
})
```

### 4.2 Monaco Editor Integration

```vue
<!-- components/MonacoDiffEditor.vue -->
<script setup lang="ts">
import * as monaco from 'monaco-editor'

const props = defineProps<{
  original: string
  modified: string
  language: string
}>()

// Create diff editor with inline comments support
const diffEditor = monaco.editor.createDiffEditor(container, {
  renderSideBySide: true,
  enableSplitViewResizing: true,
})
</script>
```

### 4.3 Inline Comments API

```python
# Backend: POST /api/v1/comments
class CommentCreate(BaseModel):
    diff_id: UUID
    line_number: int
    content: str
    parent_id: UUID | None = None  # For replies

class Comment(BaseModel):
    id: UUID
    diff_id: UUID
    line_number: int
    content: str
    author: str
    created_at: datetime
    replies: list["Comment"] = []
```

### 4.4 Project Switcher

```vue
<!-- components/ProjectSwitcher.vue -->
<script setup lang="ts">
// Supports multiple project roots
const projects = ref<ProjectInfo[]>([])
const currentProject = ref<ProjectInfo | null>(null)

async function switchProject(projectRoot: string) {
  await api.post('/projects/switch', { root: projectRoot })
  await projectStore.refresh()
}
</script>
```

### 4.5 Version Compare

```vue
<!-- components/VersionCompare.vue -->
<script setup lang="ts">
// Side-by-side JSON diff for artifact payloads
const leftVersion = ref<ArtifactDetail | null>(null)
const rightVersion = ref<ArtifactDetail | null>(null)

// Uses Monaco diff for JSON comparison
</script>
```

### 4.6 Mermaid Visualization

```vue
<!-- components/MermaidDiagram.vue -->
<script setup lang="ts">
import mermaid from 'mermaid'

const props = defineProps<{
  diagram: string  // Mermaid syntax from GraphGenerator
}>()

onMounted(() => {
  mermaid.initialize({ theme: 'dark' })
  mermaid.render('diagram', props.diagram)
})
</script>
```

---

## 5. Brand Colors (from `.branding/`)

```css
:root {
  --rf-primary: #00a020;      /* Headers, buttons, active states */
  --rf-secondary: #009e20;    /* Borders, inactive elements */
  --rf-accent: #00c030;       /* Highlights, success states */
  --rf-bg-dark: #0a1a0a;      /* Main backgrounds */
  --rf-bg-light: #102010;     /* Card backgrounds */
}
```

---

## 6. Test Distribution

| Category | Count | Framework |
|----------|-------|-----------|
| Artifacts API | 5 | pytest |
| Diffs API | 5 | pytest |
| Approvals API | 5 | pytest |
| History API | 6 | pytest |
| Auth API | 5 | pytest |
| Projects API | 3 | pytest |
| WebSocket | 7 | pytest |
| Comments API | 5 | pytest |
| CLI Commands | 8 | pytest |
| Toast Component | 3 | Vitest |
| Monaco Editor | 3 | Vitest |
| Project Switcher | 2 | Vitest |
| Version Compare | 2 | Vitest |
| Mermaid | 2 | Vitest |
| **Total** | **~61** | |

---

## 7. Dependencies

### Backend (Python)
```toml
# Already in pyproject.toml [project.optional-dependencies.web]
web = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "authlib>=1.3.0",
    "itsdangerous>=2.1.0",
    "python-multipart>=0.0.7",
    "httpx>=0.27.0",
]
```

### Frontend (npm)
```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "pinia": "^2.2.0",
    "@vueuse/core": "^11.0.0",
    "monaco-editor": "^0.50.0",
    "mermaid": "^11.0.0"
  }
}
```
