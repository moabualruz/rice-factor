# F22-08: Project Switcher - Tasks

## Overview
Add ability to switch between multiple project roots in the web interface.

## Tasks

### T22-08-01: Add project list API endpoint
- [x] Add `GET /api/v1/projects` to list known projects
- [x] Use project store for current project info
- [x] Return project info (name, root, initialized status)

### T22-08-02: Add project switch API endpoint
- [x] Add `POST /api/v1/projects/switch` to change current project
- [x] Validate project root exists
- [x] Update project store

### T22-08-03: Create ProjectSwitcher component
- [x] Create `ProjectSwitcher.vue` dropdown component
- [x] Display current project with indicator
- [x] Handle switch action

### T22-08-04: Integrate with AppHeader
- [x] Add ProjectSwitcher to header
- [x] Refresh data on project switch

### T22-08-05: Write tests
- [ ] Backend: Project list API test
- [ ] Backend: Project switch API test
- [ ] Frontend: ProjectSwitcher component test

## Estimated Test Count: ~4

## Status: MOSTLY COMPLETE (tests pending)
