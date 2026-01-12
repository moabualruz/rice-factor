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

## Branding
The TUI uses Rice-Factor brand colors from `.branding/`:
- **Primary**: `#00a020` (bright green)
- **Secondary**: `#009e20` (darker green)
- **Accent**: `#00c030` (lighter green)
- **Background Dark**: `#0a1a0a` (dark green-black)
- **Background Light**: `#102010` (lighter green-black)

### Recommended Font
For the best visual experience, use the **Terminus (Nerd Font)** included in `.branding/Terminus/`:
- `TerminessNerdFontMono-Regular.ttf` - Regular weight
- `TerminessNerdFontMono-Bold.ttf` - Bold weight

Configure your terminal emulator to use this font for the TUI.
