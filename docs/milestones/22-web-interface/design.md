# Milestone 22: Web Interface - Design

> **Status**: Planned
> **Priority**: P3

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │Dashboard │  │DiffReview│  │ Approvals│  │  History Browser │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
└───────┼─────────────┼─────────────┼─────────────────┼───────────┘
        └─────────────┴─────────────┴─────────────────┘
                              │ REST + WebSocket
┌─────────────────────────────┼───────────────────────────────────┐
│                        Backend (FastAPI)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Routes  │  │   Auth   │  │WebSocket │  │   Domain Services│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Package Structure

```
rice_factor_web/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── routes/
│   │   ├── artifacts.py
│   │   ├── approvals.py
│   │   ├── projects.py
│   │   └── websocket.py
│   └── auth/
│       ├── __init__.py
│       └── jwt.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DiffReview.tsx
│   │   │   ├── ApprovalFlow.tsx
│   │   │   └── HistoryBrowser.tsx
│   │   └── hooks/
│   │       └── useWebSocket.ts
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yaml
```

---

## 3. CLI Commands

```bash
rice-factor web serve                 # Start web server
rice-factor web serve --port 8080     # Custom port
rice-factor web build                 # Build frontend
```
