# Milestone 17: Advanced Resilience - Design

> **Status**: Planned
> **Priority**: P1

---

## 1. Package Structure

```
rice_factor/domain/services/
├── state_reconstructor.py       # NEW
├── override_scope_manager.py    # NEW
└── artifact_migrator.py         # NEW

rice_factor/adapters/drift/
├── undocumented_behavior_detector.py  # NEW
└── git_orphan_detector.py       # NEW
```
