# F21-01: VS Code Extension - Tasks

## Tasks
### T21-01-01: Create VS Code Extension Project - DONE
### T21-01-02: Implement Artifact Viewer - DONE
### T21-01-03: Implement Diff Preview - DONE
### T21-01-04: Implement Approval Actions - DONE
### T21-01-05: Tests - DONE

## Estimated Test Count: ~6
## Actual Test Count: 4 (Mocha/VS Code integration tests)

## Implementation Notes
- Created `rice-factor-vscode/` TypeScript project
- Main extension entry: `src/extension.ts`
- Components:
  - `ArtifactTreeProvider`: Tree view of artifacts by type
  - `WorkflowTreeProvider`: Workflow steps with phase detection
  - `DiffPreviewProvider`: VS Code diff editor integration
  - `ApprovalService`: Calls rice-factor CLI for approve/apply
- Commands:
  - `riceFactor.refreshArtifacts`: Refresh artifact list
  - `riceFactor.approveArtifact`: Approve draft artifact
  - `riceFactor.viewDiff`: Show diff in VS Code diff editor
  - `riceFactor.applyDiff`: Apply approved diff
- Activates on `.project` or `artifacts` directory presence
- File watcher refreshes on artifact changes

## Building

```bash
cd rice-factor-vscode
npm install
npm run compile
```

## Packaging

```bash
npx vsce package
```
