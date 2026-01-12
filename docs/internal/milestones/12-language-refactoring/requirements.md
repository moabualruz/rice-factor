# Milestone 12: Language-Specific Refactoring - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.1.0
> **Status**: Complete
> **Parent**: [Project Requirements](../../project/requirements.md)
> **Source**: [06-tools-to-integrte-with-or-learn-from.md](../../raw/06-tools-to-integrte-with-or-learn-from.md)

---

## 1. Milestone Objective

Implement language-native refactoring adapters that leverage existing ecosystem tools rather than text-based diff/patch operations. This enables semantic refactoring with proper AST-level understanding.

### 1.1 Problem Statement

Current refactoring uses text-based diff/patch which:
- Lacks semantic understanding of code
- Cannot perform complex refactorings (rename across files)
- May produce invalid code
- Doesn't leverage language-specific tooling

### 1.2 Solution Overview

Integrate with mature refactoring tools for each language:
- **JVM (Java/Kotlin)**: OpenRewrite
- **Go**: gopls (Go Language Server)
- **Rust**: rust-analyzer
- **JavaScript/TypeScript**: jscodeshift

From the spec:
> "RefactorExecutor delegates to language-native tools where possible."

---

## 2. Scope

### 2.1 In Scope

- OpenRewrite adapter for JVM languages
- gopls adapter for Go
- rust-analyzer adapter for Rust
- jscodeshift adapter for JavaScript/TypeScript
- Capability registry for language support
- Fallback to diff/patch when no native tool available

### 2.2 Out of Scope

- Custom refactoring rule authoring
- IDE integration
- Real-time refactoring suggestions
- Multi-language refactoring in single operation

---

## 3. Requirements

### 3.1 User Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| M12-U-001 | User can refactor JVM code using OpenRewrite | P0 | 5 |
| M12-U-002 | User can refactor Go code using gopls | P1 | 5 |
| M12-U-003 | User can refactor Rust code using rust-analyzer | P1 | 5 |
| M12-U-004 | User can refactor JS/TS using jscodeshift | P1 | 5 |
| M12-U-005 | User sees which tools are available | P1 | - |

### 3.2 System Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| M12-S-001 | System detects available refactoring tools | P0 | - |
| M12-S-002 | System selects appropriate tool per language | P0 | - |
| M12-S-003 | System falls back to diff/patch when no tool | P0 | - |
| M12-S-004 | RefactorPlan operations map to tool commands | P0 | - |
| M12-S-005 | Tool execution is transactional (rollback) | P1 | - |

### 3.3 Supported Refactoring Operations

| Operation | OpenRewrite | gopls | rust-analyzer | jscodeshift |
|-----------|-------------|-------|---------------|-------------|
| Rename | ✓ | ✓ | ✓ | ✓ |
| Extract Method | ✓ | ✓ | ✓ | ✓ |
| Inline | ✓ | ✓ | ✓ | ✓ |
| Move | ✓ | ✓ | ✓ | ✓ |
| Change Signature | ✓ | ✓ | ✓ | Partial |
| Add Parameter | ✓ | ✓ | ✓ | ✓ |
| Remove Parameter | ✓ | ✓ | ✓ | ✓ |

---

## 4. Features in This Milestone

| Feature ID | Feature Name | Priority | Status |
|------------|--------------|----------|--------|
| F12-01 | OpenRewrite Adapter | P0 | Complete |
| F12-02 | gopls Adapter | P1 | Complete |
| F12-03 | rust-analyzer Adapter | P1 | Complete |
| F12-04 | jscodeshift Adapter | P1 | Complete |

---

## 5. Success Criteria

- [x] OpenRewrite can rename classes across JVM codebase
- [x] gopls can perform Go refactorings via LSP
- [x] rust-analyzer can rename Rust symbols
- [x] jscodeshift can transform JS/TS code
- [x] Capability registry accurately reflects tool availability
- [x] Fallback to diff/patch works for unsupported languages

---

## 6. Dependencies

### 6.1 Internal Dependencies

| Dependency | Milestone | Reason |
|------------|-----------|--------|
| Executor Engine | 05 | RefactorExecutor base |
| Artifact System | 02 | RefactorPlan handling |

### 6.2 External Dependencies

| Tool | Version | Installation |
|------|---------|--------------|
| OpenRewrite CLI | 8.x+ | Maven/Gradle plugin |
| gopls | latest | Go toolchain |
| rust-analyzer | latest | cargo install |
| jscodeshift | 0.15+ | npm install |

---

## 7. Acceptance Criteria

### 7.1 Tool Detection

```bash
$ rice-factor refactor --capabilities

Refactoring Capabilities
========================

Language    Tool            Status    Operations
--------    ----            ------    ----------
Java        OpenRewrite     ✓         rename, extract, move, inline
Kotlin      OpenRewrite     ✓         rename, extract, move, inline
Go          gopls           ✓         rename, extract, inline
Rust        rust-analyzer   ✗         (not installed)
JavaScript  jscodeshift     ✓         rename, extract, transform
TypeScript  jscodeshift     ✓         rename, extract, transform
Python      (diff/patch)    ✓         basic text operations
```

### 7.2 Native Refactoring

```bash
$ rice-factor refactor dry-run

RefactorPlan: Rename UserService to AccountService
Tool: OpenRewrite

Analyzing project...

Changes to apply:
  1. Rename class: src/main/java/com/example/UserService.java
     - Class name: UserService → AccountService
     - File: UserService.java → AccountService.java

  2. Update references:
     - src/main/java/com/example/UserController.java (3 references)
     - src/main/java/com/example/UserRepository.java (2 references)
     - src/test/java/com/example/UserServiceTest.java (5 references)

Total: 4 files, 10 references

Run 'rice-factor refactor apply' to execute.
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial requirements |
| 1.1.0 | 2026-01-11 | Implementation | Milestone completed |
