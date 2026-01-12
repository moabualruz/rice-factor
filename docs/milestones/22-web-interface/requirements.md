# Milestone 22: Web Interface - Requirements

> **Status**: Complete
> **Priority**: P3 (Team collaboration UI)
> **Dependencies**: M16 (remote storage), M21 (visualization)

---

## 1. Overview

Provide a web-based interface for team collaboration on artifact review and approval workflows.

---

## 2. Core Requirements (Implemented)

### REQ-22-01: Web Dashboard
- [x] Project overview with stats cards
- [x] Artifact status display (by type and status)
- [x] Activity feed with real-time updates
- [x] Phase indicator showing current project phase

### REQ-22-02: Diff Review Interface
- [x] Visual code review with diff viewer
- [x] Basic syntax highlighting (add/remove/context)
- [x] Approve/Reject actions with confirmation
- [x] Split view with line numbers

### REQ-22-03: Team Approval Workflows
- [x] Pending approvals queue with priority sorting
- [x] Approval history tracking
- [x] Revoke approval functionality
- [x] Optional OAuth2 authentication (GitHub/Google)

### REQ-22-04: Artifact History Browser
- [x] Timeline view with event types
- [x] Search and filter by date, event type, artifact type
- [x] Export functionality (JSON, CSV)

---

## 3. Enhanced Requirements (Phase 2)

### REQ-22-05: CLI Commands
- [ ] `rice-factor web serve` - Start web server with uvicorn
- [ ] `rice-factor web serve --port <port>` - Custom port configuration
- [ ] `rice-factor web build` - Build frontend for production

### REQ-22-06: Enhanced Diff Review
- [ ] Monaco Editor integration for professional code viewing
- [ ] Full syntax highlighting by language
- [ ] Inline comments on specific lines
- [ ] Comment threads with replies
- [ ] Unified/Split view toggle

### REQ-22-07: Advanced Approval Workflows
- [ ] Reviewer assignment to specific artifacts/diffs
- [ ] Approval rules engine (e.g., "requires 2 approvals")
- [ ] Role-based permissions (admin, reviewer, viewer)

### REQ-22-08: Notification System
- [ ] Toast notifications for real-time events
- [ ] Notification center with history
- [ ] WebSocket-driven live updates

### REQ-22-09: Project Management
- [ ] Project switcher for multi-project support
- [ ] Project configuration display
- [ ] Quick actions per project

### REQ-22-10: Version Comparison
- [ ] Side-by-side artifact version comparison
- [ ] Payload diff visualization
- [ ] Version history navigation

### REQ-22-11: Visualization Integration
- [ ] Mermaid diagram rendering for artifact graphs
- [ ] Dependency visualization
- [ ] Phase progression charts

---

## 4. Estimated Test Count

| Category | Tests |
|----------|-------|
| Backend API (Phase 1) | 37 |
| Frontend Components (Phase 1) | 3 |
| CLI Commands (Phase 2) | 8 |
| Enhanced Features (Phase 2) | 15 |
| **Total** | **~63** |

---

## 5. Features Summary

| Feature | ID | Status | Tests |
|---------|-----|--------|-------|
| Web Dashboard | F22-01 | Complete | 8 |
| Diff Review Interface | F22-02 | Complete | 7 |
| Team Approval Workflows | F22-03 | Complete | 8 |
| History Browser | F22-04 | Complete | 7 |
| CLI Commands | F22-05 | Pending | 8 |
| Enhanced Diff (Monaco + Comments) | F22-06 | Pending | 10 |
| Toast Notifications | F22-07 | Pending | 5 |
| Project Switcher | F22-08 | Pending | 4 |
| Version Compare | F22-09 | Pending | 5 |
| Mermaid Visualization | F22-10 | Pending | 5 |
