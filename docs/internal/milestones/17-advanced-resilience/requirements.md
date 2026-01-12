# Milestone 17: Advanced Resilience - Requirements

> **Status**: Planned
> **Priority**: P1 (Long-running project support)
> **Dependencies**: M16 (metrics)

---

## 1. Overview

Enable long-running project support with full state reconstruction, override tracking, and artifact migration.

---

## 2. Requirements

### REQ-17-01: Full State Reconstruction Resume
- [ ] Reconstruct state from artifacts + audit + git
- [ ] `rice-factor resume` command enhancement

### REQ-17-02: Override Scope Limiting & Tracking
- [ ] Configurable override scope limits
- [ ] CI permanently flags overridden files

### REQ-17-03: Undocumented Behavior Detection
- [ ] Static analysis of tests for undocumented behavior
- [ ] Detection and reporting

### REQ-17-04: Git Commit-Level Orphan Detection
- [ ] Analyze git history for orphaned code
- [ ] Detection and cleanup recommendations

### REQ-17-05: Artifact Migration Scripts
- [ ] Upgrade artifacts between schema versions
- [ ] Automated and manual migration paths

---

## 3. Estimated Test Count: ~30
