# Changelog

All notable changes to Rice-Factor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation restructure following Diátaxis framework
- MkDocs Material configuration for documentation site
- VHS tape scripts for CLI demo generation
- Brand color integration across TUI components

## [0.1.0] - 2024-XX-XX

### Added

#### Core Features (Milestones 01-07)
- Hexagonal architecture with domain/adapters/entrypoints structure
- CLI foundation with Typer (`rice-factor` command)
- Configuration management with Dynaconf
- Artifact system with 9 artifact types:
  - ProjectPlan
  - ArchitecturePlan
  - ScaffoldPlan
  - TestPlan
  - ImplementationPlan
  - RefactorPlan
  - ValidationResult
  - FailureReport
  - ReconciliationPlan
- Artifact lifecycle management (DRAFT → APPROVED → LOCKED)
- JSON Schema validation for all artifacts
- Filesystem storage adapter
- LLM provider adapters:
  - Anthropic Claude
  - OpenAI GPT
  - Ollama (local)
  - vLLM (local)
- Scaffold executor for file generation
- Diff executor for code changes
- Refactoring executors with multi-language support
- Test runner integration
- Approval system with human-in-the-loop

#### Post-MVP Features (Milestones 08-13)
- CI/CD integration with artifact validation
- Drift detection and reconciliation
- Artifact lifecycle aging and expiration
- Enhanced intake with decisions.md
- Language-specific refactoring adapters:
  - Python (rope, jedi)
  - JavaScript/TypeScript (jscodeshift)
  - Go (gopls)
  - Rust (rust-analyzer)
  - Java (OpenRewrite)
  - C# (Roslyn)
  - Ruby
  - PHP
- Multi-agent run modes (A-E)

#### Advanced Features (Milestones 14-22)
- Full capability registry for refactoring
- AST parsing with Tree-sitter (9 languages)
- LSP client integration with memory management
- Local LLM orchestration with provider fallback
- Production hardening:
  - Rate limiting
  - Cost tracking
  - Remote storage (S3)
  - Webhooks
  - Metrics
- Advanced resilience features:
  - State reconstruction
  - Override tracking
  - Orphan detection
  - Migration support
- Performance optimizations:
  - Parallel execution
  - Artifact caching
  - Incremental validation
- Cross-file refactoring support
- Multi-language/polyglot repository support
- Developer experience:
  - VS Code extension
  - TUI mode (Textual)
  - Project templates
  - Visualization
- Web interface:
  - Dashboard
  - Diff review UI
  - Team approvals
  - History browser

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

---

## Release Types

- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

## Versioning Notes

Rice-Factor follows [Semantic Versioning](https://semver.org/):

- **0.x.x**: Initial development, API may change
- **1.0.0**: First stable release
- **Post 1.0**: Strict backward compatibility

## Links

- [GitHub Releases](https://github.com/user/rice-factor/releases)
- [PyPI](https://pypi.org/project/rice-factor/)
- [Documentation](https://rice-factor.dev)

[Unreleased]: https://github.com/user/rice-factor/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/user/rice-factor/releases/tag/v0.1.0
