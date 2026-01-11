# Milestone 21: Developer Experience - Design

> **Status**: Planned
> **Priority**: P2

---

## 1. Package Structure

```
vscode-rice-factor/              # VS Code extension
├── src/extension.ts
├── src/artifactViewer.ts
└── src/diffPreview.ts

rice_factor/entrypoints/tui/     # Interactive TUI
├── main.py
├── workflow_view.py
└── artifact_browser.py

rice_factor/adapters/templates/  # Project templates
├── python_clean.yaml
├── rust_hexagonal.yaml
└── go_ddd.yaml

rice_factor/adapters/viz/        # Visualization
├── graph_generator.py
└── mermaid_adapter.py
```
