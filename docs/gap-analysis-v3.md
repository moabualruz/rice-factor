# Gap Analysis v3: Future Milestones Assessment (Revised)

> **Document Type**: Gap Analysis Report (Future Milestones)
> **Date**: 2026-01-11
> **Status**: Active
> **Revision**: v3.1 - Added Capability Registry & Local LLM gaps
> **Supersedes**: `gap-analysis-v2.md` (Post-MVP completion report)
> **Prior Test Count**: 2,408 tests passing (Milestones 01-13)

---

## 1. Executive Summary

### Current State

Rice-Factor is **feature-complete** for all original specifications across 13 milestones:

- **Milestones 01-07**: MVP complete
- **Milestones 08-13**: Post-MVP complete
- **Test Coverage**: 2,408 unit tests passing
- **Architecture**: Full hexagonal implementation with domain/adapters/entrypoints
- **CLI Commands**: 20+ commands operational
- **Artifact Types**: All 9 types with validation and storage

### Analysis Scope

This document identifies **40+ gaps** representing:
1. **Critical capability gaps** (NEW) - Refactoring tools and LLM providers
2. **Deferred tasks** from existing milestones
3. **Spec features** not fully productionized
4. **Natural extensions** mentioned in Phase-01 spec
5. **Production hardening** requirements
6. **Developer experience** improvements

### Proposed Milestones (Revised)

This analysis proposes **9 new milestones (14-22)** with **2 NEW high-priority milestones**:

| Milestone | Name | Priority | Features | Gaps Addressed |
|-----------|------|----------|----------|----------------|
| **14** | **Full Capability Registry** | **P0** | 7 | GAP-CAP-001 to GAP-CAP-005 |
| **15** | **Local LLM Orchestration** | **P0** | 6 | GAP-CAP-006 to GAP-CAP-008 |
| 16 | Production Hardening | P0 | 6 | GAP-PROD-001 to GAP-PROD-006 |
| 17 | Advanced Resilience | P1 | 5 | GAP-DEF-002/004/005, GAP-SPEC-001/006 |
| 18 | Performance & Parallelism | P1 | 4 | GAP-SPEC-002/003 |
| 19 | Advanced Refactoring | P2 | 4 | GAP-EXT-003/006 |
| 20 | Multi-Language Support | P2 | 4 | GAP-EXT-001 |
| 21 | Developer Experience | P2 | 5 | GAP-DX-001 to GAP-DX-005 |
| 22 | Web Interface | P3 | 4 | GAP-EXT-002 |

---

## 2. Research Findings (2025 State-of-Art)

### 2.1 Language-Specific Refactoring Tools

| Language | Tool | Capabilities | Integration Pattern |
|----------|------|--------------|---------------------|
| **Python** | [Rope](https://github.com/python-rope/rope) | rename, extract, move, inline, change_signature | Python library, CLI |
| **Python** | Jedi + refactor library | rename, extract_variable, extract_function | Python library |
| **Java/Kotlin/Groovy** | [OpenRewrite](https://docs.openrewrite.org/) | ALL operations (700+ recipes) | CLI, Gradle/Maven |
| **C#** | [Roslyn/Roslynator](https://github.com/dotnet/roslynator) | ALL operations via Roslyn API | .NET SDK, CLI |
| **JavaScript/TypeScript** | jscodeshift (existing) | rename, extract, inline | CLI |
| **Go** | gopls (existing) | rename, extract | LSP |
| **Rust** | rust-analyzer (existing) | rename, extract | LSP |
| **Ruby** | [Parser gem + Rubocop-AST](https://github.com/whitequark/parser) | Full AST manipulation | Ruby library |
| **Ruby** | Prism (Ruby 3.4+) | Modern parser with rewriter | Ruby built-in |
| **PHP** | [nikic/PHP-Parser](https://github.com/nikic/PHP-Parser) | Full AST manipulation | PHP library |
| **PHP** | [Rector](https://github.com/rectorphp/rector) | Automated refactoring (5.3-8.5) | CLI |

### 2.2 Local LLM Providers (Production-Ready)

| Provider | Type | API | Best For | GPU Support |
|----------|------|-----|----------|-------------|
| **[Ollama](https://github.com/ollama/ollama)** | Simple CLI | REST + OpenAI-compat | Development, simple deployment | Optional |
| **[vLLM](https://docs.vllm.ai/)** | Production server | OpenAI-compat | High-throughput production (2-24x faster) | Required |
| **[LM Studio](https://lmstudio.ai/)** | Desktop app | OpenAI-compat | Local development | Optional |
| **[LocalAI](https://localai.io/)** | All-in-one | OpenAI-compat | Drop-in OpenAI replacement | Optional |

### 2.3 Best Local Code Models (2025)

| Model | Size | Strength | Provider |
|-------|------|----------|----------|
| **Codestral-22B** | 22B | Fastest, excellent code | Mistral |
| **Qwen3-Coder** | 7B-72B | Multi-language, reasoning | Alibaba |
| **DeepSeek-Coder-V3** | 7B-33B | Best code completion | DeepSeek |
| **StarCoder2** | 3B-15B | Open weights, multi-lang | BigCode |
| **CodeLlama** | 7B-70B | Meta's code model | Meta |

---

## 3. Gap Categories

### 3.0 Category 0: Critical Capability Gaps (NEW)

**These gaps were discovered during implementation review and are critical blockers.**

| Gap ID | Description | Current State | Impact |
|--------|-------------|---------------|--------|
| GAP-CAP-001 | Python has no dedicated refactoring adapter | DiffPatch fallback | Reduced Python refactoring quality |
| GAP-CAP-002 | extract_interface FALSE for ALL languages | Tools exist but not integrated | Cannot extract interfaces |
| GAP-CAP-003 | enforce_dependency FALSE/PARTIAL for all | Tools exist but not integrated | Cannot enforce architecture |
| GAP-CAP-004 | No Ruby language support | Not in registry | Cannot refactor Ruby code |
| GAP-CAP-005 | No PHP language support | Not in registry | Cannot refactor PHP code |
| GAP-CAP-006 | No local LLM provider support | Only Claude/OpenAI | Requires internet, no privacy |
| GAP-CAP-007 | No provider fallback/routing | Single provider per session | Single point of failure |
| GAP-CAP-008 | No model capability registry | Hardcoded model selection | Cannot optimize model selection |

**Current Capability Registry State** (`rice_factor/config/capability_registry.yaml`):

| Language | move_file | rename_symbol | extract_interface | enforce_dependency | **Gap** |
|----------|-----------|---------------|-------------------|-------------------|---------|
| python | ✅ | ✅ | ❌ | ❌ | No dedicated adapter (DiffPatch fallback) |
| rust | ✅ | ✅ | ❌ | partial | rust-analyzer limited |
| go | ✅ | ✅ | ❌ | ❌ | gopls limited |
| javascript | ✅ | ✅ | ❌ | ❌ | jscodeshift partial |
| typescript | ✅ | ✅ | ❌ | ❌ | jscodeshift partial |
| java | ✅ | ✅ | ❌ | partial | OpenRewrite CAN do all |
| csharp | ✅ | ✅ | ❌ | ❌ | Roslyn CAN do all |
| kotlin | ✅ | ✅ | ❌ | ❌ | OpenRewrite CAN do all |

**Key Finding**: The tools exist but aren't fully integrated!

---

### 3.1 Category 1: Deferred Tasks from Existing Milestones

These tasks were explicitly deferred during the implementation of Milestones 08-13.

| Gap ID | Source | Description | Original Milestone | Reason Deferred |
|--------|--------|-------------|-------------------|-----------------|
| GAP-DEF-001 | M08 | Architecture rule check in CI | M08 → M12 | Language-specific rules handled in M12 |
| GAP-DEF-002 | M08 | Orphaned code detection via git commit analysis | M08 | Requires git history traversal |
| GAP-DEF-003 | M08 | Test template in external sample repository | M08 | External repo dependency |
| GAP-DEF-004 | M09 | Undocumented behavior detection (static analysis) | M09 | Requires parsing test assertions |
| GAP-DEF-005 | M10 | Artifact migration script for legacy artifacts | M10 | No legacy artifacts yet |
| GAP-DEF-006 | M10 | Full CLI integration with lifecycle in plan/impl | M10 | Scope control |

**Source Reference**: `docs/gap-analysis-v2.md` Section 6 (Deferred Tasks)

---

### 3.2 Category 2: Spec Features Not Fully Productionized

These features are mentioned in the raw specifications but have partial or basic implementations.

| Gap ID | Spec Section | Description | Current State |
|--------|--------------|-------------|---------------|
| GAP-SPEC-001 | item-05 5.6 | Safe interruption & resume with full state reconstruction | Basic `dev resume` exists, doesn't reconstruct from artifacts/audit/git |
| GAP-SPEC-002 | PRS 12.2 | Parallel execution per unit | Not implemented - sequential only |
| GAP-SPEC-003 | PRS 12.2 | Cached artifacts reuse for performance | Not implemented |
| GAP-SPEC-004 | item-02 2.8 | Test Runner per-language configuration | Basic - hardcoded commands |
| GAP-SPEC-005 | PRS 3.1 | Orchestrator component (drives lifecycle phases) | CLI-driven only, no automated orchestration |
| GAP-SPEC-006 | item-05 5.7 | Human override scope limiting & CI flagging forever | Basic override exists, no scope limits or permanent CI flags |

**Spec Quote** (item-05 5.6):
> Reconstructs state from: artifacts, audit logs, git history

**Spec Quote** (PRS 12.2):
> Performance: LLM calls minimized, Cached artifacts reused, Parallel execution allowed (per unit)

**Spec Quote** (item-05 5.7):
> Rules: Reason required, Scope limited, CI flags override forever, Forces reconciliation later

---

### 3.3 Category 3: Natural Extensions (Post-MVP Spec Mentions)

Features explicitly listed as "Not Supported Yet" in Phase-01 MVP spec.

| Gap ID | Description | Spec Reference | Spec Quote |
|--------|-------------|----------------|------------|
| GAP-EXT-001 | Multi-language repository support | Phase-01 Section 1 | "Multi-language repos - Not Supported (Yet)" |
| GAP-EXT-002 | UI/Web interface for review workflows | Phase-01 Section 1 | "UI - Not Supported (Yet)" |
| GAP-EXT-003 | Advanced refactor operations (extract_interface, enforce_dependency) | item-02 2.7 | "MVP: move_file, rename_symbol (simple)" |
| GAP-EXT-004 | Distributed agent execution | item-04 | Mentioned but not detailed |
| GAP-EXT-005 | Performance optimization tooling | Phase-01 Section 1 | "Performance optimization - Not Supported (Yet)" |
| GAP-EXT-006 | AST-level refactoring beyond tool adapters | item-02 | "No AST work yet" (MVP scope) |

**Spec Quote** (Phase-01 Section 1):
> Not Supported (Yet): Multi-language repos, UI, Parallel execution, Advanced refactor ops, Performance optimization, Distributed agents

---

### 3.4 Category 4: Production Hardening

Features not specified but essential for production deployment.

| Gap ID | Description | Rationale |
|--------|-------------|-----------|
| GAP-PROD-001 | LLM provider fallback chain | Claude → OpenAI → local for reliability |
| GAP-PROD-002 | Rate limiting and cost tracking | Production LLM usage monitoring |
| GAP-PROD-003 | Artifact versioning & migration | Schema evolution across versions |
| GAP-PROD-004 | Remote artifact storage (S3, GCS) | Team collaboration and CI integration |
| GAP-PROD-005 | Webhook integrations (Slack, Teams) | Notification on approvals/failures |
| GAP-PROD-006 | Metrics and telemetry export | Observability (Prometheus, OpenTelemetry) |

**Rationale**: These features bridge the gap between a working system and a production-ready system that teams can rely on.

---

### 3.5 Category 5: Developer Experience

Features to improve usability and adoption.

| Gap ID | Description | Rationale |
|--------|-------------|-----------|
| GAP-DX-001 | IDE plugins (VS Code, JetBrains) | Inline artifact review, diff preview |
| GAP-DX-002 | Interactive TUI for workflow | Rich terminal experience beyond CLI |
| GAP-DX-003 | Project templates/presets | Quick start for common stacks (Python, Rust, Go, JVM) |
| GAP-DX-004 | Documentation site generation | Generate docs from artifacts automatically |
| GAP-DX-005 | Artifact visualization (dependency graphs) | Visual understanding of plans |

**Rationale**: Developer experience improvements drive adoption and reduce friction in daily workflows.

---

## 4. Proposed Milestones (14-22)

### 4.1 Milestone 14: Full Capability Registry (NEW)

**Priority**: P0 (Foundation for all refactoring)
**Dependencies**: None
**Estimated Features**: 7

| Feature | Description | Tool Integration | Gaps Addressed |
|---------|-------------|------------------|----------------|
| F14-01 | Python Refactoring Adapter | Rope library | GAP-CAP-001 |
| F14-02 | Enhanced Java/Kotlin Adapter | Full OpenRewrite | GAP-CAP-002, GAP-CAP-003 |
| F14-03 | C# Roslyn Adapter | Roslyn SDK | GAP-CAP-002, GAP-CAP-003 |
| F14-04 | Ruby Refactoring Adapter | Parser gem | GAP-CAP-004 |
| F14-05 | PHP Refactoring Adapter | Rector + PHP-Parser | GAP-CAP-005 |
| F14-06 | Enhanced JS/TS Adapter | Extended jscodeshift | GAP-CAP-002 |
| F14-07 | Capability Auto-Detection | Runtime check | All |

**Target Capability Matrix (After M14)**:

| Language | move_file | rename_symbol | extract_interface | enforce_dependency | Tool |
|----------|-----------|---------------|-------------------|-------------------|------|
| python | ✅ | ✅ | ✅ | ✅ | Rope |
| java | ✅ | ✅ | ✅ | ✅ | OpenRewrite |
| kotlin | ✅ | ✅ | ✅ | ✅ | OpenRewrite |
| csharp | ✅ | ✅ | ✅ | ✅ | Roslyn |
| javascript | ✅ | ✅ | ✅ | ✅ | jscodeshift+ |
| typescript | ✅ | ✅ | ✅ | ✅ | jscodeshift+ |
| go | ✅ | ✅ | ✅ | ✅ | gopls+ |
| rust | ✅ | ✅ | ✅ | ✅ | rust-analyzer+ |
| ruby | ✅ | ✅ | ✅ | ✅ | Parser gem |
| php | ✅ | ✅ | ✅ | ✅ | Rector |

**New Components**:
```
rice_factor/adapters/refactoring/
├── rope_adapter.py              # NEW: Python via Rope
├── roslyn_adapter.py            # NEW: C# via Roslyn
├── ruby_parser_adapter.py       # NEW: Ruby via Parser gem
├── rector_adapter.py            # NEW: PHP via Rector
├── openrewrite_adapter.py       # ENHANCE: Full operations
├── jscodeshift_adapter.py       # ENHANCE: extract_interface
├── gopls_adapter.py             # ENHANCE: extract_interface
├── rust_analyzer_adapter.py     # ENHANCE: extract_interface
└── capability_detector.py       # NEW: Auto-detect available tools
```

**Exit Criteria**:
- [ ] All 10 languages have full refactoring support
- [ ] extract_interface works for all languages
- [ ] enforce_dependency works for all languages
- [ ] Capability auto-detection finds available tools
- [ ] Fallback to DiffPatch when tools unavailable

---

### 4.2 Milestone 15: Local LLM Orchestration (NEW)

**Priority**: P0 (Cost reduction, privacy, offline mode)
**Dependencies**: None
**Estimated Features**: 6

| Feature | Description | Integration | Gaps Addressed |
|---------|-------------|-------------|----------------|
| F15-01 | Ollama Adapter | REST API localhost:11434 | GAP-CAP-006 |
| F15-02 | vLLM Adapter | OpenAI-compat API | GAP-CAP-006 |
| F15-03 | OpenAI-Compatible Adapter | Generic adapter | GAP-CAP-006 |
| F15-04 | Provider Fallback Chain | Config-driven failover | GAP-CAP-007 |
| F15-05 | Model Registry | YAML model capabilities | GAP-CAP-008 |
| F15-06 | Cost & Latency Tracking | Usage metrics | GAP-PROD-002 |

**Architecture**:
```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Orchestration Layer                     │
├─────────────────────────────────────────────────────────────────┤
│  LLMPort (Protocol)                                              │
│    ├── CloudProviders                                            │
│    │   ├── ClaudeAdapter (existing)                              │
│    │   └── OpenAIAdapter (existing)                              │
│    └── LocalProviders (NEW)                                      │
│        ├── OllamaAdapter      # REST API localhost:11434         │
│        ├── VLLMAdapter        # OpenAI-compat API                │
│        ├── LMStudioAdapter    # OpenAI-compat API                │
│        └── LocalAIAdapter     # OpenAI-compat API                │
├─────────────────────────────────────────────────────────────────┤
│  ProviderSelector                                                │
│    ├── Fallback Chain: Claude → OpenAI → Ollama → vLLM          │
│    ├── Cost-based routing                                        │
│    └── Capability-based routing (code vs chat)                   │
└─────────────────────────────────────────────────────────────────┘
```

**Configuration Design**:
```yaml
# rice_factor/config/llm_providers.yaml
providers:
  cloud:
    claude:
      enabled: true
      api_key_env: ANTHROPIC_API_KEY
      models: [claude-sonnet-4-20250514, claude-opus-4-20250514]
      priority: 1
    openai:
      enabled: true
      api_key_env: OPENAI_API_KEY
      models: [gpt-4o, gpt-4-turbo]
      priority: 2

  local:
    ollama:
      enabled: true
      base_url: http://localhost:11434
      models: [codestral, qwen3-coder, deepseek-coder-v3]
      priority: 3
    vllm:
      enabled: false
      base_url: http://localhost:8000
      models: [codestral-22b]
      priority: 4

fallback:
  strategy: priority  # priority | round_robin | cost_based
  max_retries: 3
  timeout_seconds: 30
```

**New Components**:
```
rice_factor/adapters/llm/
├── ollama_adapter.py            # NEW: Ollama integration
├── vllm_adapter.py              # NEW: vLLM integration
├── openai_compat_adapter.py     # NEW: Generic OpenAI-compat
├── local_ai_adapter.py          # NEW: LocalAI integration
└── provider_selector.py         # NEW: Fallback/routing logic

rice_factor/config/
├── llm_providers.yaml           # NEW: Provider configuration
└── model_registry.yaml          # NEW: Model capabilities
```

**Exit Criteria**:
- [ ] Ollama models work for artifact generation
- [ ] vLLM production deployment supported
- [ ] Automatic fallback when provider unavailable
- [ ] Cost tracking per provider
- [ ] Model capability registry guides model selection
- [ ] Offline mode with local models only

---

### 4.3 Milestone 16: Production Hardening

**Priority**: P0 (Essential for production use)
**Dependencies**: M15 (uses LLM orchestration layer)
**Estimated Features**: 6

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F16-01 | Rate Limiting | GAP-PROD-002 |
| F16-02 | Cost Tracking | GAP-PROD-002 |
| F16-03 | Artifact Schema Versioning | GAP-PROD-003 |
| F16-04 | Remote Storage Adapters | GAP-PROD-004 |
| F16-05 | Notification Webhooks | GAP-PROD-005 |
| F16-06 | Metrics Export | GAP-PROD-006 |

**New Components**:
```
rice_factor/domain/services/rate_limiter.py
rice_factor/domain/services/cost_tracker.py
rice_factor/adapters/storage/s3_adapter.py
rice_factor/adapters/storage/gcs_adapter.py
rice_factor/adapters/notifications/webhook_adapter.py
rice_factor/adapters/metrics/prometheus_adapter.py
rice_factor/adapters/metrics/opentelemetry_adapter.py
```

**Exit Criteria**:
- [ ] Rate limits enforced with configurable thresholds
- [ ] Cost per operation tracked and exportable
- [ ] Artifacts can be stored/retrieved from S3/GCS
- [ ] Webhooks fire on artifact approval/rejection
- [ ] Metrics exportable to Prometheus/OpenTelemetry

---

### 4.4 Milestone 17: Advanced Resilience

**Priority**: P1 (Long-running project support)
**Dependencies**: M16 (metrics help with resilience monitoring)
**Estimated Features**: 5

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F17-01 | Full State Reconstruction Resume | GAP-SPEC-001 |
| F17-02 | Override Scope Limiting & Tracking | GAP-SPEC-006 |
| F17-03 | Undocumented Behavior Detection | GAP-DEF-004 |
| F17-04 | Git Commit-Level Orphan Detection | GAP-DEF-002 |
| F17-05 | Artifact Migration Scripts | GAP-DEF-005 |

**Exit Criteria**:
- [ ] `rice-factor resume` fully reconstructs state from artifacts + audit + git
- [ ] Override commands have configurable scope limits
- [ ] CI permanently flags files modified by override
- [ ] Tests covering undocumented behavior are detected
- [ ] Migration scripts upgrade artifacts between schema versions

---

### 4.5 Milestone 18: Performance & Parallelism

**Priority**: P1 (Scale and speed)
**Dependencies**: M16 (metrics track performance)
**Estimated Features**: 4

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F18-01 | Parallel Unit Execution | GAP-SPEC-002 |
| F18-02 | Artifact Caching Layer | GAP-SPEC-003 |
| F18-03 | Incremental Validation | Performance |
| F18-04 | Batch Operations | Multiple artifacts |

**Exit Criteria**:
- [ ] Multiple implementation plans can execute in parallel
- [ ] Artifact loading uses a caching layer (memory/Redis)
- [ ] Validation skips unchanged files (incremental)
- [ ] Batch approval/rejection of multiple artifacts

---

### 4.6 Milestone 19: Advanced Refactoring

**Priority**: P2 (Semantic code transformations)
**Dependencies**: M14 (full capability registry)
**Estimated Features**: 4

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F19-01 | Extract Interface Operation | GAP-EXT-003 |
| F19-02 | Enforce Dependency Operation | GAP-EXT-003 |
| F19-03 | Cross-File Refactoring | GAP-EXT-006 |
| F19-04 | Refactoring Safety Analysis | Pre-execution checks |

**Exit Criteria**:
- [ ] `extract_interface` creates interface from concrete class
- [ ] `enforce_dependency` removes architecture violations
- [ ] Refactoring can span multiple files atomically
- [ ] Safety analysis predicts refactoring impact before execution

---

### 4.7 Milestone 20: Multi-Language Support

**Priority**: P2 (Polyglot repositories)
**Dependencies**: M14 (full capability), M19 (advanced refactoring)
**Estimated Features**: 4

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F20-01 | Multi-Language Project Detection | GAP-EXT-001 |
| F20-02 | Cross-Language Dependency Tracking | GAP-EXT-001 |
| F20-03 | Unified Test Aggregation | Multi-runner |
| F20-04 | Language-Specific Artifact Sections | Schema extension |

**Exit Criteria**:
- [ ] `rice-factor init` detects multiple languages in repo
- [ ] ProjectPlan tracks per-language modules
- [ ] Cross-language API dependencies are tracked
- [ ] `rice-factor test` runs all language-specific test runners

---

### 4.8 Milestone 21: Developer Experience

**Priority**: P2 (Usability improvements)
**Dependencies**: None
**Estimated Features**: 5

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F21-01 | VS Code Extension | GAP-DX-001 |
| F21-02 | Interactive TUI Mode | GAP-DX-002 |
| F21-03 | Project Templates | GAP-DX-003 |
| F21-04 | Artifact Visualization | GAP-DX-005 |
| F21-05 | Documentation Generation | GAP-DX-004 |

**Exit Criteria**:
- [ ] VS Code extension shows artifacts inline
- [ ] TUI mode provides interactive workflow navigation
- [ ] `rice-factor init --template python-clean` bootstraps project
- [ ] `rice-factor viz` generates dependency graphs
- [ ] `rice-factor docs` generates documentation from artifacts

---

### 4.9 Milestone 22: Web Interface

**Priority**: P3 (Team collaboration UI)
**Dependencies**: M16 (remote storage), M21 (visualization)
**Estimated Features**: 4

| Feature | Description | Gaps Addressed |
|---------|-------------|----------------|
| F22-01 | Web Dashboard | GAP-EXT-002 |
| F22-02 | Diff Review Interface | GAP-EXT-002 |
| F22-03 | Team Approval Workflows | Collaboration |
| F22-04 | Artifact History Browser | Visibility |

**Exit Criteria**:
- [ ] Web dashboard shows project status and artifacts
- [ ] Diff review interface with approve/reject actions
- [ ] Team members can be assigned to approvals
- [ ] Full artifact history with filtering and search

---

## 5. Implementation Roadmap

### Phase 1: Foundation (P0)

```
Milestone 14: Full Capability Registry
├── Enables all refactoring operations
├── Adds Ruby and PHP support
└── Foundation for M19 (Advanced Refactoring)

Milestone 15: Local LLM Orchestration
├── Cost reduction (no cloud API required)
├── Privacy (local execution)
└── Offline mode support

Milestone 16: Production Hardening
├── Essential for team/production use
├── Uses M15 orchestration layer
└── Enables reliable deployment
```

### Phase 2: Scale & Reliability (P1)

```
Milestone 17: Advanced Resilience
├── Builds on M16 metrics
├── Critical for long-running projects
└── Improves recovery capabilities

Milestone 18: Performance & Parallelism
├── Builds on M16 metrics
├── Improves execution speed
└── Enables larger projects
```

### Phase 3: Advanced Features (P2)

```
Milestone 19: Advanced Refactoring
├── Builds on M14 capability registry
└── Semantic code transformations

Milestone 20: Multi-Language Support
├── Builds on M14, M19
└── Polyglot repository support

Milestone 21: Developer Experience
├── Standalone improvements
└── Drives adoption
```

### Phase 4: Team Collaboration (P3)

```
Milestone 22: Web Interface
├── Builds on M16, M21
└── Full web-based workflow
```

---

## 6. Specification Reference Matrix

### Gap to Milestone Mapping (Revised)

| Gap ID | Category | Milestone | Feature |
|--------|----------|-----------|---------|
| GAP-CAP-001 | Capability | M14 | F14-01 |
| GAP-CAP-002 | Capability | M14 | F14-02, F14-03, F14-06 |
| GAP-CAP-003 | Capability | M14 | F14-02, F14-03 |
| GAP-CAP-004 | Capability | M14 | F14-04 |
| GAP-CAP-005 | Capability | M14 | F14-05 |
| GAP-CAP-006 | Capability | M15 | F15-01, F15-02, F15-03 |
| GAP-CAP-007 | Capability | M15 | F15-04 |
| GAP-CAP-008 | Capability | M15 | F15-05 |
| GAP-DEF-001 | Deferred | - | Covered by M12 |
| GAP-DEF-002 | Deferred | M17 | F17-04 |
| GAP-DEF-003 | Deferred | - | External repo (out of scope) |
| GAP-DEF-004 | Deferred | M17 | F17-03 |
| GAP-DEF-005 | Deferred | M17 | F17-05 |
| GAP-DEF-006 | Deferred | M17 | F17-01 |
| GAP-SPEC-001 | Spec | M17 | F17-01 |
| GAP-SPEC-002 | Spec | M18 | F18-01 |
| GAP-SPEC-003 | Spec | M18 | F18-02 |
| GAP-SPEC-004 | Spec | M20 | F20-03 |
| GAP-SPEC-005 | Spec | M18 | F18-04 |
| GAP-SPEC-006 | Spec | M17 | F17-02 |
| GAP-EXT-001 | Extension | M20 | F20-01, F20-02 |
| GAP-EXT-002 | Extension | M22 | F22-01 to F22-04 |
| GAP-EXT-003 | Extension | M19 | F19-01, F19-02 |
| GAP-EXT-004 | Extension | - | Future consideration |
| GAP-EXT-005 | Extension | M18 | F18-01 to F18-04 |
| GAP-EXT-006 | Extension | M19 | F19-03 |
| GAP-PROD-001 | Production | M15 | F15-04 (fallback) |
| GAP-PROD-002 | Production | M15, M16 | F15-06, F16-01, F16-02 |
| GAP-PROD-003 | Production | M16 | F16-03 |
| GAP-PROD-004 | Production | M16 | F16-04 |
| GAP-PROD-005 | Production | M16 | F16-05 |
| GAP-PROD-006 | Production | M16 | F16-06 |
| GAP-DX-001 | DX | M21 | F21-01 |
| GAP-DX-002 | DX | M21 | F21-02 |
| GAP-DX-003 | DX | M21 | F21-03 |
| GAP-DX-004 | DX | M21 | F21-05 |
| GAP-DX-005 | DX | M21 | F21-04 |

---

## 7. Research Sources

### Refactoring Tools
- [Rope (Python)](https://github.com/python-rope/rope)
- [OpenRewrite (Java/Kotlin)](https://docs.openrewrite.org/)
- [Roslyn/Roslynator (C#)](https://github.com/dotnet/roslynator)
- [Roslyn SDK Tutorial](https://learn.microsoft.com/en-us/dotnet/csharp/roslyn-sdk/)
- [Parser gem (Ruby)](https://github.com/whitequark/parser)
- [nikic/PHP-Parser](https://github.com/nikic/PHP-Parser)
- [Rector (PHP)](https://github.com/rectorphp/rector)

### Local LLM Providers
- [Ollama](https://github.com/ollama/ollama)
- [Ollama Python Library](https://github.com/ollama/ollama-python)
- [vLLM Documentation](https://docs.vllm.ai/en/stable/serving/openai_compatible_server/)
- [vLLM Production Guide](https://introl.com/blog/vllm-production-deployment-inference-serving-architecture)
- [LM Studio](https://lmstudio.ai/)
- [LocalAI](https://localai.io/)

### Integration Guides
- [LangChain Ollama Integration](https://docs.langchain.com/oss/python/integrations/chat/ollama)
- [LlamaIndex Ollama](https://developers.llamaindex.ai/python/examples/llm/ollama/)

---

## 8. Conclusion

Rice-Factor has achieved **full specification compliance** for Milestones 01-13. This revised gap analysis identifies **40+ opportunities** for future development organized into **9 new milestones (14-22)**.

### Key Statistics

| Metric | Value |
|--------|-------|
| Identified Gaps | 40+ |
| Proposed Milestones | 9 (14-22) |
| Total New Features | 45 |
| P0 Features | 19 |
| P1 Features | 9 |
| P2 Features | 13 |
| P3 Features | 4 |

### Key Changes from v3.0

1. **Added Milestone 14: Full Capability Registry** - Addresses critical gap where no language has full refactoring support
2. **Added Milestone 15: Local LLM Orchestration** - Enables offline mode, cost savings, and privacy
3. **Renumbered existing milestones** (14-20 → 16-22) to maintain sequential ordering
4. **Added Category 0: Critical Capability Gaps** - 8 new gaps identified
5. **Added research findings** on 2025 state-of-art tools

### Next Steps

1. Review and approve revised milestone structure
2. Delete old milestone directories (14-20)
3. Create new milestone documentation for 14-22
4. Begin implementation with Milestone 14 (Full Capability Registry)
