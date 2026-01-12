# Milestone 21: Developer Experience - Requirements

> **Status**: Complete
> **Priority**: P2 (Usability improvements)
> **Dependencies**: None

---

## 1. Overview

Improve developer usability with IDE integration, TUI mode, templates, and visualization.

---

## 2. Requirements

### REQ-21-01: VS Code Extension
- [ ] Artifact viewer in IDE (deferred - external project)
- [ ] Diff preview (deferred - external project)
- [ ] Inline approval actions (deferred - external project)

### REQ-21-02: Interactive TUI Mode
- [ ] Rich terminal UI (deferred - requires Rich/Textual dependency)
- [ ] Workflow navigation (deferred)
- [ ] Artifact browser (deferred)

### REQ-21-03: Project Templates
- [x] Quick start presets
- [x] `rice-factor init --template` support (adapters complete)

### REQ-21-04: Artifact Visualization
- [x] Dependency graphs
- [x] `rice-factor viz` command (adapters complete)

### REQ-21-05: Documentation Generation
- [x] Generate docs from artifacts
- [x] `rice-factor docs` command (adapters complete)

---

## 3. Estimated Test Count: ~30
## 4. Actual Test Count: 115

| Feature | Tests |
|---------|-------|
| F21-03: Project Templates | 33 |
| F21-04: Visualization | 45 |
| F21-05: Doc Generation | 37 |
| **Total** | **115** |

Note: F21-01 (VS Code Extension) and F21-02 (Interactive TUI) are deferred as they require external projects or additional dependencies beyond the core Python package.
