# Milestone 20: Multi-Language Support - Requirements

> **Status**: Complete
> **Priority**: P2 (Polyglot repositories)
> **Dependencies**: M14 (full capability), M19 (advanced refactoring)

---

## 1. Overview

Enable support for polyglot repositories with multiple languages.

---

## 2. Requirements

### REQ-20-01: Multi-Language Project Detection
- [x] Detect multiple languages in repo
- [x] Language distribution analysis

### REQ-20-02: Cross-Language Dependency Tracking
- [x] Track API dependencies between languages
- [x] Integration point mapping

### REQ-20-03: Unified Test Aggregation
- [x] Run all language-specific test runners
- [x] Aggregate results
- [x] Per-language test runner configuration (GAP-SPEC-004)
- [x] Language-specific test command overrides

### REQ-20-04: Language-Specific Artifact Sections
- [x] Extended ProjectPlan schema
- [x] Per-language modules

---

## 3. Estimated Test Count: ~22
## 4. Actual Test Count: 124

| Feature | Tests |
|---------|-------|
| F20-01: Language Detection | 36 |
| F20-02: Cross-Language Deps | 28 |
| F20-03: Unified Test Runner | 37 |
| F20-04: Language Sections | 23 |
| **Total** | **124** |
