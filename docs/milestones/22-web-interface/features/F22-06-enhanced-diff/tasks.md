# F22-06: Enhanced Diff Review - Tasks

## Overview
Integrate Monaco Editor for professional diff viewing and add inline comment support.

## Tasks

### T22-06-01: Create Monaco Editor component
- [x] Create `MonacoDiffEditor.vue` component
- [x] Configure Monaco for diff mode
- [x] Add language detection from file extension
- [x] Support split/unified view toggle

### T22-06-02: Create comment backend API
- [x] Create comment endpoints in diffs.py
- [x] Implement CRUD endpoints (create, list, update, delete)
- [x] In-memory storage (can be extended to file-based)

### T22-06-03: Create comment storage
- [x] In-memory store for comments
- [x] Future: Can be extended to file-based persistence

### T22-06-04: Create inline comment components
- [x] Create `InlineComment.vue` for single comments
- [x] Create `useInlineComments.ts` composable
- [x] Add comment markers in diff viewer
- [x] Style with brand colors

### T22-06-05: Integrate with DiffDetailView
- [x] Add MonacoDiffViewer component option
- [x] Add view mode toggle (Side-by-Side / Unified)
- [x] Handle comment creation on line click
- [x] Pass diff ID and enable comments prop

### T22-06-06: Write tests
- [ ] Backend: Comment API tests (5 tests)
- [ ] Frontend: Monaco component tests (3 tests)
- [ ] Frontend: Comment component tests (2 tests)

## Estimated Test Count: ~10

## Status: MOSTLY COMPLETE (tests pending)
