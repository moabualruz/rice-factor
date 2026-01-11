# Milestone 14: Full Capability Registry - Requirements

> **Status**: Planned
> **Priority**: P0 (Foundation for all refactoring)
> **Dependencies**: None

---

## 1. Overview

Make ALL languages fully capable with `extract_interface` and `enforce_dependency` operations by integrating production-grade refactoring tools.

### Current State

The capability registry (`rice_factor/config/capability_registry.yaml`) shows:
- **extract_interface**: FALSE for ALL 8 languages
- **enforce_dependency**: FALSE/PARTIAL for all languages
- **Python**: No dedicated adapter (DiffPatch fallback)
- **Ruby, PHP**: Not in registry at all

### Target State

- All 10 languages (Python, Java, Kotlin, C#, JS, TS, Go, Rust, Ruby, PHP) fully capable
- All 4 operations (move_file, rename_symbol, extract_interface, enforce_dependency) supported
- Auto-detection of available tools at runtime

---

## 2. Requirements

### REQ-14-01: Python Refactoring Adapter (Rope)

**Description**: Integrate Rope library for Python refactoring operations.

**Acceptance Criteria**:
- [ ] `rope_adapter.py` implements RefactoringPort protocol
- [ ] Supports: move_file, rename_symbol, extract_interface, enforce_dependency
- [ ] Extract interface creates Protocol/ABC from concrete class
- [ ] Enforce dependency analyzes and fixes import violations
- [ ] Falls back to DiffPatch when Rope unavailable

**Tool**: [Rope](https://github.com/python-rope/rope)

---

### REQ-14-02: Enhanced Java/Kotlin Adapter (OpenRewrite)

**Description**: Extend OpenRewrite adapter to support all operations.

**Acceptance Criteria**:
- [ ] `openrewrite_adapter.py` enhanced with extract_interface recipe
- [ ] Supports enforce_dependency via ArchUnit-style recipes
- [ ] Works for Java, Kotlin, and Groovy
- [ ] Uses OpenRewrite CLI or Gradle/Maven plugin

**Tool**: [OpenRewrite](https://docs.openrewrite.org/)

---

### REQ-14-03: C# Roslyn Adapter

**Description**: Integrate Roslyn SDK for C# refactoring operations.

**Acceptance Criteria**:
- [ ] `roslyn_adapter.py` implements RefactoringPort protocol
- [ ] Uses dotnet CLI with Roslyn analyzers
- [ ] Supports all 4 operations
- [ ] Works with .NET 6+ projects

**Tool**: [Roslyn/Roslynator](https://github.com/dotnet/roslynator)

---

### REQ-14-04: Ruby Refactoring Adapter

**Description**: Integrate Parser gem and Rubocop-AST for Ruby refactoring.

**Acceptance Criteria**:
- [ ] `ruby_parser_adapter.py` implements RefactoringPort protocol
- [ ] Uses Parser gem for AST manipulation
- [ ] TreeRewriter for code modifications
- [ ] Supports Prism parser for Ruby 3.4+
- [ ] Adds Ruby to capability registry

**Tool**: [Parser gem](https://github.com/whitequark/parser)

---

### REQ-14-05: PHP Refactoring Adapter

**Description**: Integrate Rector and PHP-Parser for PHP refactoring.

**Acceptance Criteria**:
- [ ] `rector_adapter.py` implements RefactoringPort protocol
- [ ] Uses Rector CLI for automated refactoring
- [ ] nikic/PHP-Parser for custom transformations
- [ ] Supports PHP 7.4 through 8.4
- [ ] Adds PHP to capability registry

**Tool**: [Rector](https://github.com/rectorphp/rector)

---

### REQ-14-06: Enhanced JavaScript/TypeScript Adapter

**Description**: Extend jscodeshift adapter for extract_interface and enforce_dependency.

**Acceptance Criteria**:
- [ ] `jscodeshift_adapter.py` enhanced with interface extraction
- [ ] Supports TypeScript interface generation from class
- [ ] Dependency enforcement via import analysis
- [ ] Works with ESM and CommonJS modules

**Tool**: jscodeshift (existing)

---

### REQ-14-07: Capability Auto-Detection

**Description**: Automatically detect available refactoring tools at runtime.

**Acceptance Criteria**:
- [ ] `capability_detector.py` probes for installed tools
- [ ] Checks: rope, rector, dotnet (roslyn), ruby parser, node (jscodeshift)
- [ ] Updates capability registry dynamically
- [ ] Graceful degradation when tools unavailable
- [ ] CLI command: `rice-factor capabilities` shows available operations

---

## 3. Non-Functional Requirements

### NFR-14-01: Performance
- Tool invocation should complete within 30 seconds for typical operations
- Large file refactoring should stream progress updates

### NFR-14-02: Error Handling
- Clear error messages when tools unavailable
- Fallback to DiffPatch with user notification
- No silent failures

### NFR-14-03: Testing
- Unit tests for each adapter
- Integration tests with sample projects per language
- Minimum 90% code coverage for new adapters

---

## 4. Exit Criteria

- [ ] All 10 languages have full refactoring support
- [ ] extract_interface works for all languages
- [ ] enforce_dependency works for all languages
- [ ] Capability auto-detection finds available tools
- [ ] Fallback to DiffPatch when tools unavailable
- [ ] All tests passing
- [ ] Documentation updated

---

## 5. Estimated Test Count

~50 tests (unit + integration per adapter)
