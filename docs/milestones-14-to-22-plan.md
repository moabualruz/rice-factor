# Milestones 14-22 Implementation Plan

> **Created**: 2026-01-11
> **Status**: Pre-Implementation Ready
> **Last Updated**: 2026-01-11

---

## Overview

This plan covers the implementation of Rice-Factor milestones 14-22, including gap analysis verification, documentation updates, and task execution strategy.

---

## 1. Gap Analysis Verification Results

### 1.1 Gaps Fully Mapped (37/40)

All critical gaps have corresponding features in milestone documentation:

| Gap Category | Count | Mapped To |
|--------------|-------|-----------|
| GAP-CAP-001 to GAP-CAP-012 | 12 | M14, M15 |
| GAP-DEF-002, 004, 005, 006 | 4 | M17 |
| GAP-SPEC-001 to GAP-SPEC-006 | 6 | M17, M18, M20 |
| GAP-EXT-001 to GAP-EXT-006 | 5 | M19, M20, M22 |
| GAP-PROD-001 to GAP-PROD-006 | 6 | M15, M16 |
| GAP-DX-001 to GAP-DX-005 | 5 | M21 |

### 1.2 Intentionally Unmapped Gaps (3)

| Gap ID | Reason |
|--------|--------|
| GAP-DEF-001 | Covered by M12 (complete) |
| GAP-DEF-003 | Out of scope (external repo) |
| GAP-EXT-004 | Future consideration |

---

## 2. Implementation Strategy

### Phase 1: P0 Milestones (Foundation)
Execute in order: **M14 → M15 → M16**

### Phase 2: P1 Milestones (Resilience & Performance)
Execute in order: **M17 → M18**

### Phase 3: P2 Milestones (Advanced Features)
Execute in parallel where possible: **M19, M20, M21**

### Phase 4: P3 Milestone (Optional)
Execute last: **M22**

---

## 3. Task Execution Protocol

For each milestone:
1. Read `requirements.md` and `design.md`
2. For each feature (F##-##):
   - Read `tasks.md`
   - Execute tasks (T##-##-##) sequentially
   - Update task status in `tasks.md` as: `[ ]` → `[x]`
   - Run tests after each task
3. Mark feature complete in requirements.md
4. Update CLAUDE.md milestone status

### Task Status Legend
```
[ ] - Pending
[~] - In Progress
[x] - Complete
[!] - Blocked
```

---

## 4. Milestone Summary

| # | Name | Features | Tasks | Tests | Priority | Status |
|---|------|----------|-------|-------|----------|--------|
| 14 | Full Capability Registry | 7 | 48 | 172 | P0 | **Complete** |
| 15 | LLM Orchestration | 13 | 80 | 323 | P0 | **Complete** |
| 16 | Production Hardening | 6 | ~25 | ~35 | P0 | Planned |
| 17 | Advanced Resilience | 5 | ~25 | ~30 | P1 | Planned |
| 18 | Performance & Parallelism | 4 | ~15 | ~25 | P1 | Planned |
| 19 | Advanced Refactoring | 4 | ~15 | ~25 | P2 | Planned |
| 20 | Multi-Language Support | 4 | ~15 | ~22 | P2 | Planned |
| 21 | Developer Experience | 5 | ~25 | ~30 | P2 | Planned |
| 22 | Web Interface | 4 | ~20 | ~30 | P3 | Planned |
| **TOTAL** | | **51** | **~235** | **~322** | | |

---

## 5. Current Progress

### Status: In Progress

### Active Milestone: M16 - Production Hardening

### Completed Features
- **F14-01: Python Rope Adapter** (7/7 tasks complete)
  - Created `rice_factor/adapters/refactoring/rope_adapter.py`
  - Created `rice_factor/adapters/refactoring/capability_detector.py`
  - Added `rope>=1.11.0` as optional dependency
  - Implemented: move_file, rename_symbol, extract_interface, enforce_dependency
  - 59 tests (47 passed, 12 skipped when rope not installed)
  - Test baseline: 2479 -> 2526 tests

- **F14-02: Enhanced Java/Kotlin Adapter (OpenRewrite)** (5/5 tasks complete)
  - Enhanced `rice_factor/adapters/refactoring/openrewrite_adapter.py`
  - Added `JvmDependencyRule` and `JvmDependencyViolation` dataclasses
  - Implemented: extract_interface (Java + Kotlin), enforce_dependency (ArchUnit-style)
  - Added extract_interface_via_recipe for OpenRewrite recipe-based extraction
  - 20 new tests (37 total for OpenRewrite adapter)
  - Test baseline: 2526 -> 2546 tests

- **F14-03: C# Roslyn Adapter** (7/7 tasks complete)
  - Created `rice_factor/adapters/refactoring/roslyn_adapter.py`
  - Added `CSharpDependencyRule` and `CSharpDependencyViolation` dataclasses
  - Implemented: rename (text-based fallback), move (namespace change), extract_interface, enforce_dependency
  - Uses dotnet CLI for availability detection
  - 23 new tests for Roslyn adapter
  - Test baseline: 2546 -> 2569 tests

- **F14-04: Ruby Parser Adapter** (8/8 tasks complete)
  - Created `rice_factor/adapters/refactoring/ruby_parser_adapter.py`
  - Added `RubyDependencyRule` and `RubyDependencyViolation` dataclasses
  - Implemented: rename, move (module/require updates), extract_interface (Ruby module + RBS), enforce_dependency
  - Generates both Ruby module stubs and RBS (Ruby Signature) type files
  - 33 new tests for Ruby adapter
  - Test baseline: 2569 -> 2602 tests

- **F14-05: PHP Rector Adapter** (8/8 tasks complete)
  - Created `rice_factor/adapters/refactoring/rector_adapter.py`
  - Added `PhpDependencyRule` and `PhpDependencyViolation` dataclasses
  - Implemented: rename, move (namespace with escaped backslashes), extract_interface, enforce_dependency
  - Handles PHP namespace escaping in regex replacements
  - 25 new tests for Rector adapter
  - Test baseline: 2602 -> 2627 tests

- **F14-06: Enhanced JavaScript/TypeScript Adapter** (5/5 tasks complete)
  - Enhanced `rice_factor/adapters/refactoring/jscodeshift_adapter.py`
  - Added `JsDependencyRule` and `JsDependencyViolation` dataclasses
  - Implemented: extract_interface (TypeScript interfaces + JSDoc typedefs), enforce_dependency
  - Supports ES modules, CommonJS require, and dynamic imports
  - Cross-platform path handling (Windows backslash normalization)
  - 16 new tests (40 total for jscodeshift adapter)
  - Test baseline: 2627 -> 2643 tests

- **F14-07: Capability Auto-Detection** (8/8 tasks complete)
  - CapabilityDetector already existed with detection for 8 tools
  - Updated jscodeshift operations to include `extract_interface` and `enforce_dependency`
  - Created `rice_factor/entrypoints/cli/commands/capabilities.py`
  - Added `rice-factor capabilities` CLI command with --refresh, --tools, --languages, --json options
  - 8 new tests for CLI command
  - Test baseline: 2643 -> 2651 tests

### M14 Complete!

**Milestone 14: Full Capability Registry** is now complete with all 7 features implemented:
- F14-01: Python Rope Adapter (59 tests)
- F14-02: Enhanced Java/Kotlin OpenRewrite (37 tests)
- F14-03: C# Roslyn Adapter (23 tests)
- F14-04: Ruby Parser Adapter (33 tests)
- F14-05: PHP Rector Adapter (25 tests)
- F14-06: Enhanced JavaScript/TypeScript (40 tests)
- F14-07: Capability Auto-Detection (33 tests)

**Total M14 tests**: 172 new tests
**Test baseline**: 2479 -> 2651 tests

### M15 In Progress

**Milestone 15: Local LLM Orchestration** - P0 priority

#### Completed Features (M15)
- **F15-01: Ollama Adapter** (7/7 tasks complete)
  - Created `rice_factor/adapters/llm/ollama_adapter.py`
  - OllamaClient with httpx/requests fallback
  - Async streaming support via generate_async()
  - list_models(), is_available() health checks
  - Temperature capped at 0.2 for determinism
  - 28 new tests
  - Test baseline: 2651 -> 2679 tests

- **F15-02: vLLM Adapter** (7/7 tasks complete)
  - Created `rice_factor/adapters/llm/vllm_adapter.py`
  - VLLMClient using OpenAI-compatible API (/v1/completions, /v1/chat/completions)
  - Async streaming support via generate_async()
  - Chat completions API for batch processing
  - 33 new tests
  - Test baseline: 2679 -> 2712 tests

- **F15-03: OpenAI-Compatible Adapter** (6/6 tasks complete)
  - Created `rice_factor/adapters/llm/openai_compat_adapter.py`
  - Generic adapter for any OpenAI-compatible server (LocalAI, LM Studio, TGI)
  - KNOWN_PROVIDERS configuration for localai, lmstudio, tgi, generic
  - Provider aliases in create_llm_adapter_from_config
  - 37 new tests
  - Test baseline: 2712 -> 2749 tests

- **F15-04: Provider Fallback Chain** (7/7 tasks complete)
  - Created `rice_factor/adapters/llm/provider_selector.py`
  - ProviderSelector with SelectionStrategy enum (PRIORITY, ROUND_ROBIN, COST_BASED)
  - ProviderConfig dataclass with cost tracking
  - Automatic fallback on provider failure with max_retries
  - Async support via generate_async()
  - 35 new tests
  - Test baseline: 2749 -> 2784 tests

- **F15-05: Model Registry** (6/6 tasks complete)
  - Created `rice_factor/domain/services/model_registry.py`
  - ModelRegistry with DEFAULT_MODELS for cloud and local models
  - ModelCapability enum (CODE, CHAT, REASONING, VISION, FUNCTION_CALLING, JSON_MODE)
  - Query methods: get_by_capability, get_cheapest, sync_with_provider
  - 36 new tests
  - Test baseline: 2784 -> 2820 tests

- **F15-06: Cost & Latency Tracking** (7/7 tasks complete)
  - Created `rice_factor/adapters/llm/usage_tracker.py`
  - UsageTracker with UsageRecord and ProviderStats dataclasses
  - Token counting, cost calculation, latency metrics
  - Prometheus export (llm_cost_usd, llm_tokens_total, llm_latency_ms)
  - 23 new tests
  - Test baseline: 2820 -> 2843 tests

- **F15-07: Claude Code CLI Adapter** (6/6 tasks complete)
  - Created `rice_factor/adapters/llm/cli/claude_code_adapter.py`
  - ClaudeCodeAdapter with JSON output parsing
  - Async execution with timeout handling
  - Availability detection via shutil.which()
  - 17 new tests
  - Test baseline: 2843 -> 2860 tests

- **F15-08: OpenAI Codex CLI Adapter** (6/6 tasks complete)
  - Created `rice_factor/adapters/llm/cli/codex_adapter.py`
  - CodexAdapter with approval mode configuration (suggest, auto-edit, full-auto)
  - Non-interactive execution mode (--output-format json)
  - 10 new tests
  - Test baseline: 2860 -> 2870 tests

- **F15-09: Google Gemini CLI Adapter** (6/6 tasks complete)
  - Created `rice_factor/adapters/llm/cli/gemini_cli_adapter.py`
  - GeminiCLIAdapter with model selection
  - ReAct loop support and sandbox mode configuration
  - 10 new tests
  - Test baseline: 2870 -> 2880 tests

- **F15-10: Qwen Code CLI Adapter** (6/6 tasks complete)
  - Created `rice_factor/adapters/llm/cli/qwen_code_adapter.py`
  - QwenCodeAdapter with local model routing
  - OAuth authentication and plan mode integration
  - 10 new tests
  - Test baseline: 2880 -> 2890 tests

- **F15-11: Aider CLI Adapter** (7/7 tasks complete)
  - Created `rice_factor/adapters/llm/cli/aider_adapter.py`
  - AiderAdapter with git integration handling
  - Modified file parsing from output ("Wrote file.py" patterns)
  - Auto-commits toggle (--no-auto-commits flag)
  - 13 new tests
  - Test baseline: 2890 -> 2903 tests

- **F15-12: CLI Agent Protocol & Orchestrator** (7/8 tasks complete)
  - Created `rice_factor/adapters/llm/cli/base.py` (CLIAgentPort, CLITaskResult, DetectedAgent)
  - Created `rice_factor/adapters/llm/cli/detector.py` (CLIAgentDetector)
  - Created `rice_factor/adapters/llm/orchestrator.py` (UnifiedOrchestrator)
  - OrchestrationMode enum (API, CLI, AUTO)
  - Mode selection logic and fallback between API/CLI
  - T15-12-07 (rice-factor agents command) deferred to CLI phase
  - 45 new tests (15 orchestrator + 30 detector/base)
  - Test baseline: 2903 -> 2918 tests

- **F15-13: OpenCode CLI Adapter** (7/7 tasks complete)
  - Created `rice_factor/adapters/llm/cli/opencode_adapter.py`
  - OpenCodeAdapter with model selection (provider/model format)
  - Server attach mode (`--attach`) for faster execution
  - Session management (`--session`, `--continue`)
  - JSON output parsing
  - 26 new tests
  - Test baseline: 2918 -> 2944 tests

### M15 Complete!

**Milestone 15: Local LLM Orchestration** is now complete with all 13 features implemented:
- F15-01: Ollama Adapter (28 tests)
- F15-02: vLLM Adapter (33 tests)
- F15-03: OpenAI-Compatible Adapter (37 tests)
- F15-04: Provider Fallback Chain (35 tests)
- F15-05: Model Registry (36 tests)
- F15-06: Cost & Latency Tracking (23 tests)
- F15-07: Claude Code CLI Adapter (17 tests)
- F15-08: Codex CLI Adapter (10 tests)
- F15-09: Gemini CLI Adapter (10 tests)
- F15-10: Qwen Code CLI Adapter (10 tests)
- F15-11: Aider CLI Adapter (13 tests)
- F15-12: CLI Agent Protocol & Orchestrator (45 tests)
- F15-13: OpenCode CLI Adapter (26 tests)

**Total M15 tests**: 323 new tests
**Test baseline**: 2651 -> 2944 tests

### Next Action
Continue with M16: Production Hardening

To continue implementation:
1. Read `docs/milestones/16-production-hardening/requirements.md`
2. Read `docs/milestones/16-production-hardening/design.md`
3. Execute F16-01 through F16-06

---

## 6. Milestone-by-Milestone Execution Guide

### M14: Full Capability Registry (P0)

**Documentation Path**: `docs/milestones/14-full-capability-registry/`
**New Files to Create**:
```
rice_factor/adapters/refactoring/
├── rope_adapter.py           # F14-01
├── roslyn_adapter.py         # F14-03
├── ruby_parser_adapter.py    # F14-04
├── rector_adapter.py         # F14-05
└── capability_detector.py    # F14-07
```
**Files to Modify**:
- `rice_factor/adapters/refactoring/openrewrite_adapter.py` (F14-02)
- `rice_factor/adapters/refactoring/jscodeshift_adapter.py` (F14-06)
- `rice_factor/config/capability_registry.yaml`

**Features (7)**:
1. F14-01-python-rope: 7 tasks
2. F14-02-java-openrewrite: Enhanced operations
3. F14-03-csharp-roslyn: 6 tasks
4. F14-04-ruby-parser: 6 tasks
5. F14-05-php-rector: 6 tasks
6. F14-06-js-enhanced: 5 tasks
7. F14-07-capability-detection: 5 tasks

---

### M15: LLM Orchestration (P0)

**Documentation Path**: `docs/milestones/15-local-llm-orchestration/`
**New Files to Create**:
```
rice_factor/adapters/llm/
├── ollama_adapter.py         # F15-01
├── vllm_adapter.py           # F15-02
├── openai_compat_adapter.py  # F15-03
├── provider_selector.py      # F15-04
├── usage_tracker.py          # F15-06
├── orchestrator.py           # F15-12
└── cli/
    ├── __init__.py
    ├── base.py               # F15-12
    ├── claude_code_adapter.py   # F15-07
    ├── codex_adapter.py         # F15-08
    ├── gemini_cli_adapter.py    # F15-09
    ├── qwen_code_adapter.py     # F15-10
    ├── aider_adapter.py         # F15-11
    └── detector.py              # F15-12

rice_factor/config/
├── llm_providers.yaml        # F15-04
└── model_registry.yaml       # F15-05

rice_factor/domain/ports/
└── cli_agent.py              # F15-12
```

**Features (12)**:
1. F15-01-ollama-adapter: 7 tasks
2. F15-02-vllm-adapter: 6 tasks
3. F15-03-openai-compat: 5 tasks
4. F15-04-fallback-chain: 6 tasks
5. F15-05-model-registry: 5 tasks
6. F15-06-cost-tracking: 5 tasks
7. F15-07-claude-code-cli: 6 tasks
8. F15-08-codex-cli: 6 tasks
9. F15-09-gemini-cli: 6 tasks
10. F15-10-qwen-code-cli: 6 tasks
11. F15-11-aider-cli: 7 tasks
12. F15-12-cli-agent-protocol: 8 tasks

---

### M16: Production Hardening (P0)

**Documentation Path**: `docs/milestones/16-production-hardening/`

**Features (6)**:
1. F16-01-rate-limiting: 4 tasks
2. F16-02-cost-tracking: 5 tasks
3. F16-03-schema-versioning: 5 tasks
4. F16-04-remote-storage: 6 tasks
5. F16-05-webhooks: 5 tasks
6. F16-06-metrics: 5 tasks

---

### M17: Advanced Resilience (P1)

**Documentation Path**: `docs/milestones/17-advanced-resilience/`

**Features (5)**:
1. F17-01-state-reconstruction: 5 tasks
2. F17-02-override-tracking: 4 tasks
3. F17-03-undocumented-behavior: 5 tasks
4. F17-04-orphan-detection: 4 tasks
5. F17-05-artifact-migration: 5 tasks

---

### M18: Performance & Parallelism (P1)

**Documentation Path**: `docs/milestones/18-performance-parallelism/`

**Features (4)**:
1. F18-01-parallel-execution: 4 tasks
2. F18-02-artifact-caching: 4 tasks
3. F18-03-incremental-validation: 4 tasks
4. F18-04-batch-operations: 4 tasks

---

### M19: Advanced Refactoring (P2)

**Documentation Path**: `docs/milestones/19-advanced-refactoring/`

**Features (4)**:
1. F19-01-extract-interface: 4 tasks
2. F19-02-enforce-dependency: 4 tasks
3. F19-03-cross-file-refactoring: 4 tasks
4. F19-04-safety-analysis: 4 tasks

---

### M20: Multi-Language Support (P2)

**Documentation Path**: `docs/milestones/20-multi-language/`

**Features (4)**:
1. F20-01-language-detection: 4 tasks
2. F20-02-cross-language-deps: 4 tasks
3. F20-03-unified-tests: 4 tasks
4. F20-04-language-sections: 4 tasks

---

### M21: Developer Experience (P2)

**Documentation Path**: `docs/milestones/21-developer-experience/`

**Features (5)**:
1. F21-01-vscode-extension: 5 tasks
2. F21-02-interactive-tui: 5 tasks
3. F21-03-project-templates: 4 tasks
4. F21-04-visualization: 4 tasks
5. F21-05-doc-generation: 4 tasks

---

### M22: Web Interface (P3)

**Documentation Path**: `docs/milestones/22-web-interface/`

**Features (4)**:
1. F22-01-web-dashboard: 5 tasks
2. F22-02-diff-review: 5 tasks
3. F22-03-team-approvals: 5 tasks
4. F22-04-history-browser: 5 tasks

---

## 7. Session Resume Instructions

To resume this work in a future session:

1. Read this file (`docs/milestones-14-to-22-plan.md`) for current status
2. Check the "Current Progress" section above
3. Check CLAUDE.md for milestone status
4. Find the current task in the relevant `tasks.md` file
5. Continue from the last `[ ]` (pending) task

---

## 8. Pre-Implementation Checklist

- [x] Create persistent plan file: `docs/milestones-14-to-22-plan.md`
- [x] Update M20 requirements with GAP-SPEC-004
- [x] Update M18 requirements with GAP-SPEC-005
- [x] Verify all tasks.md files have proper format
  - Note: 49/51 files use summary format (task headers only)
  - 2 files (F18-04, F20-03) have detailed checkboxes for gap items
  - Checkboxes will be added per-feature at implementation time
- [x] Run existing tests to confirm baseline: **2,479 tests passing** (verified 2026-01-11)

---

## 9. Existing Infrastructure

**Existing (from Milestones 01-13)**:
- ✅ LLM adapters: Claude, OpenAI (2 providers)
- ✅ Refactoring adapters: jscodeshift, OpenRewrite, gopls, rust-analyzer, DiffPatch
- ✅ Multi-agent coordination: 5 modes implemented
- ✅ CI/CD pipeline: Complete
- ✅ Test coverage: 2,479 tests (baseline)

**What M14-22 Will Add**:
- 4 new LLM API adapters (Ollama, vLLM, LM Studio, LocalAI)
- 5 CLI agent adapters (Claude Code, Codex, Gemini, Qwen, Aider)
- 4 new refactoring adapters (Rope, Roslyn, Ruby, PHP)
- Production features (rate limiting, webhooks, metrics)
- DX improvements (VS Code, TUI, templates)
- Web interface (dashboard, review, approvals)
