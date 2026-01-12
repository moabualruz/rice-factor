# Changelog

All notable changes to Rice-Factor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Web Interface with full dashboard, artifact browser, and diff reviewer
- TUI Mode with workflow navigation and artifact management
- REST API with 45+ endpoints for programmatic access
- WebSocket support for real-time updates
- OAuth2 authentication (GitHub, Google)
- Configuration editor in Web UI

### Changed
- Improved CLI help messages
- Enhanced error reporting

### Fixed
- Various bug fixes

---

## [0.1.0] - 2024-01-15

### Added

#### Core System
- Hexagonal architecture with domain, adapters, and entrypoints layers
- 9 artifact types: ProjectPlan, ArchitecturePlan, ScaffoldPlan, TestPlan, ImplementationPlan, RefactorPlan, ValidationResult, FailureReport, ReconciliationPlan
- Artifact lifecycle: DRAFT -> APPROVED -> LOCKED (TestPlan only)
- Full audit trail with append-only logging
- JSON Schema validation for all artifacts

#### CLI Commands (30 total)
- `init` - Project initialization with questionnaire
- `plan project/architecture/tests/impl/refactor` - Generate plan artifacts
- `scaffold` - Create file structure from ScaffoldPlan
- `impl` - Generate implementation diffs
- `apply` - Apply approved diffs
- `test` - Run test suite
- `approve` - Approve artifacts
- `lock` - Lock TestPlan (immutable)
- `validate` - Run validation pipeline
- `resume` - Resume interrupted workflows
- `reconcile` - Generate ReconciliationPlan for drift
- `refactor check/dry-run/apply` - Refactoring operations
- `override create/list/reconcile` - Override management
- `ci validate/*` - CI/CD pipeline validation
- `audit drift/coverage` - Audit operations
- `artifact age/review/extend/migrate` - Artifact lifecycle
- `capabilities` - Show refactoring capabilities
- `models` - Model management
- `tui` - Launch TUI mode
- `web serve` - Launch Web UI

#### LLM Providers
- Anthropic Claude (claude-3-5-sonnet, claude-3-opus)
- OpenAI (gpt-4-turbo, gpt-4o)
- Ollama (local models)
- vLLM (GPU-accelerated local)
- LocalAI (OpenAI-compatible)
- Azure OpenAI

#### Configuration
- Dynaconf-based configuration system
- Environment variable overrides (RICE_* prefix)
- Per-project (.rice-factor.yaml) and user (~/.rice-factor/config.yaml) configs
- Rate limiting with provider-specific limits
- Storage backends: filesystem, S3, GCS

#### Developer Experience
- TUI mode with Textual framework
- Web dashboard with Vue 3 + TypeScript
- VS Code extension
- Rich CLI output with syntax highlighting

#### Enterprise Features
- CI/CD integration with GitHub Actions, GitLab CI
- Multi-agent coordination (Solo, Orchestrator, Voting, Role-Locked, Hybrid)
- Webhook notifications (Slack, Teams, generic)
- Cost tracking and rate limiting
- Remote storage backends

#### Testing & Quality
- Unit tests with pytest
- Integration tests for CLI commands
- E2E tests for TUI (Textual pilot)
- E2E tests for Web UI (Playwright)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2024-01-15 | Initial release with full MVP and advanced features |

---

## Migration Guides

### From Pre-Release to 0.1.0

No migration required - 0.1.0 is the first stable release.

---

## Roadmap

See [Project Status](../index.md#project-status) for current roadmap and planned features.

---

## Links

- [GitHub Releases](https://github.com/moabualruz/rice-factor/releases)
- [Issue Tracker](https://github.com/moabualruz/rice-factor/issues)
- [Contributing Guide](README.md)
