# F22-07: Toast Notification System - Tasks

## Overview
Add toast notifications for real-time feedback on actions and WebSocket events.

## Tasks

### T22-07-01: Create notification store
- [x] Create `stores/notifications.ts` with Pinia
- [x] Define Toast interface (id, type, title, message, duration)
- [x] Implement add/remove toast methods
- [x] Auto-dismiss after duration

### T22-07-02: Create toast composable
- [x] Create `composables/useToast.ts`
- [x] Add success(), error(), warning(), info() methods
- [x] Generate unique IDs
- [x] Return toast API for components

### T22-07-03: Create toast components
- [x] Create `ToastNotification.vue` for single toast
- [x] Create `ToastContainer.vue` for positioning
- [x] Add slide-in/slide-out animations
- [x] Style with brand colors per type

### T22-07-04: Integrate with WebSocket events
- [x] Subscribe to artifact events (created, approved, locked)
- [x] Subscribe to diff events (approved, rejected)
- [x] Subscribe to error events
- [x] Show appropriate toast for each event

### T22-07-05: Add to App.vue
- [x] Mount ToastContainer at app level
- [x] Integrate WebSocket subscriptions

### T22-07-06: Write tests
- [ ] Test notification store
- [ ] Test toast composable
- [ ] Test toast component rendering

## Estimated Test Count: ~5

## Status: MOSTLY COMPLETE (tests pending)
