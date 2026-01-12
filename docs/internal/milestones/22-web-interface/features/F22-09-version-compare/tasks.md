# F22-09: Version Compare View - Tasks

## Overview
Add side-by-side version comparison for artifact payloads.

## Tasks

### T22-09-01: Add version history API endpoint
- [x] Add `GET /api/v1/artifacts/{id}/versions` to list versions
- [x] Return version number, timestamp, and metadata
- [x] Support single version (extensible for Git-backed storage)

### T22-09-02: Add version payload API endpoint
- [x] Add `GET /api/v1/artifacts/{id}/versions/{version}` for payload
- [x] Return payload for specified version

### T22-09-03: Create VersionCompare component
- [x] Create `VersionCompare.vue` component
- [x] Use Monaco diff editor for JSON
- [x] Add version selector dropdowns
- [x] Show metadata changes (status, timestamps)

### T22-09-04: Integrate with ArtifactDetailView
- [x] Add "Compare Versions" button
- [x] Open modal with version compare view
- [x] Handle single-version artifacts gracefully

### T22-09-05: Write tests
- [ ] Backend: Version history API test
- [ ] Backend: Version payload API test
- [ ] Frontend: VersionCompare component test

## Estimated Test Count: ~5

## Status: MOSTLY COMPLETE (tests pending)
