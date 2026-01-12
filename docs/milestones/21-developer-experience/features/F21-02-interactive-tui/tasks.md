# F21-02: Interactive TUI Mode - Tasks

## Tasks
### T21-02-01: Create TUI Framework - DONE
### T21-02-02: Implement Workflow View - DONE
### T21-02-03: Implement Artifact Browser - DONE
### T21-02-04: Tests - DONE

## Actual Test Count: 26

## Implementation Notes
- Created `rice_factor/entrypoints/tui/` package with Textual-based TUI
- Main app: `RiceFactorTUI` with tabbed interface (Workflow, Artifacts)
- Screens:
  - `WorkflowScreen`: Shows workflow steps with phase-aware navigation
  - `ArtifactBrowserScreen`: Lists artifacts with detail panel
- Widgets:
  - `ArtifactTree`: Tree view for artifact hierarchy
  - `StatusBar`: Bottom status bar with phase info
- CLI entry: `rice-factor tui` command
- Keyboard bindings: q (quit), w (workflow), a (artifacts), r (refresh), ? (help)
- Integrates with PhaseService and ArtifactService when project is initialized
