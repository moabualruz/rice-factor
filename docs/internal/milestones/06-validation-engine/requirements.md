# Milestone 06: Validation Engine - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.2.0
> **Status**: Pending

---

## 1. Milestone Objective

Implement the validation engine that verifies correctness through tests, linting, architecture rules, and invariant checks. Generate ValidationResult artifacts that feed back into the planning loop.

**Key Design Goals:**
- Native tool integration (no custom runners)
- Emit-only model (produce ValidationResult, no side effects)
- Fail-fast on any validation failure
- No auto-fixing (report, never repair)
- Auditable validation history

---

## 2. Scope

### 2.1 In Scope
- Test runner integration (cargo test, go test, mvn test, npm test, pytest)
- Lint runner integration (ruff, clippy, golint, eslint)
- Architecture rule enforcement (import layer checks)
- Invariant checking (domain constraints, lock verification)
- ValidationResult artifact generation
- Validation audit logging
- CLI integration (`rice-factor test` command)

### 2.2 Out of Scope
- Test generation (covered by LLM compiler in M04)
- Diff application (covered by M05 Executor Engine)
- Custom test runners (use native tools only)
- Auto-fix functionality (validators report, never repair)
- Complex AST analysis (basic import checks only)

---

## 3. Ubiquitous Requirements

| ID | Requirement |
|----|-------------|
| M06-U-001 | The validation engine **shall** use native test runners |
| M06-U-002 | The validation engine **shall** emit ValidationResult artifacts |
| M06-U-003 | The validation engine **shall** never auto-fix issues |
| M06-U-004 | The validation engine **shall** provide actionable error messages |
| M06-U-005 | The validation engine **shall** log all validation actions to audit trail |
| M06-U-006 | The validation engine **shall** be deterministic and reproducible |
| M06-U-007 | The validation engine **shall** fail fast on first validation failure |
| M06-U-008 | The validation engine **shall** support language-specific validators |

---

## 4. Event-Driven Requirements

| ID | Requirement |
|----|-------------|
| M06-E-001 | **As soon as** tests fail, the system **shall** emit ValidationResult with failure details |
| M06-E-002 | **As soon as** architecture rules are violated, the system **shall** block further execution |
| M06-E-003 | **As soon as** validation passes, the system **shall** allow proceeding to next phase |
| M06-E-004 | **As soon as** lint errors are found, the system **shall** emit ValidationResult with lint details |
| M06-E-005 | **As soon as** invariants are violated, the system **shall** emit ValidationResult with violation details |

---

## 5. Domain-Specific Requirements

### 5.1 Test Runner Requirements

| ID | Requirement |
|----|-------------|
| M06-TR-001 | The test runner **shall** detect language from project configuration |
| M06-TR-002 | The test runner **shall** use exit code to determine pass/fail |
| M06-TR-003 | The test runner **shall** capture stdout/stderr for error messages |
| M06-TR-004 | The test runner **shall** support timeout configuration |
| M06-TR-005 | The test runner **shall** support the following test commands: |

| Language | Test Command | Notes |
|----------|--------------|-------|
| Python | `pytest` | Or `python -m pytest` |
| Rust | `cargo test` | Default runner |
| Go | `go test ./...` | Recursive test |
| JavaScript | `npm test` | Via package.json |
| TypeScript | `npm test` | Via package.json |
| Java | `mvn test` | Maven runner |

### 5.2 Lint Runner Requirements

| ID | Requirement |
|----|-------------|
| M06-LR-001 | The lint runner **shall** detect language from project configuration |
| M06-LR-002 | The lint runner **shall** parse linter output for error locations |
| M06-LR-003 | The lint runner **shall** report all lint errors, not just first |
| M06-LR-004 | The lint runner **shall** support the following linters: |

| Language | Lint Command | Notes |
|----------|--------------|-------|
| Python | `ruff check` | Fast Python linter |
| Rust | `cargo clippy` | Rust linter |
| Go | `golint` | Go linter |
| JavaScript | `eslint` | JavaScript linter |
| TypeScript | `eslint` | TypeScript linter |

### 5.3 Architecture Validator Requirements

| ID | Requirement |
|----|-------------|
| M06-AV-001 | The architecture validator **shall** be optional (can be disabled) |
| M06-AV-002 | The architecture validator **shall** check hexagonal layer imports |
| M06-AV-003 | The architecture validator **shall** detect domain → adapter imports |
| M06-AV-004 | The architecture validator **shall** never auto-fix violations |
| M06-AV-005 | The architecture validator **shall** report exact import location |

**Hexagonal Layer Rules:**
- `domain/` **shall not** import from `adapters/`
- `domain/` **shall not** import from `entrypoints/`
- `domain/` **shall only** use stdlib
- `adapters/` **may** import from `domain/`
- `entrypoints/` **may** import from `domain/` and `adapters/`

### 5.4 Invariant Checker Requirements

| ID | Requirement |
|----|-------------|
| M06-IC-001 | The invariant checker **shall** verify TestPlan lock status |
| M06-IC-002 | The invariant checker **shall** verify artifact status transitions |
| M06-IC-003 | The invariant checker **shall** verify approval chain integrity |
| M06-IC-004 | The invariant checker **shall** verify artifact dependencies exist |

**Domain Invariants:**
- Locked TestPlan **shall not** be modified
- Artifact status **shall** only transition: draft → approved → locked
- Approved artifacts **shall** have valid approval records
- Artifact dependencies **shall** reference existing artifacts

### 5.5 ValidationResult Requirements

| ID | Requirement |
|----|-------------|
| M06-VR-001 | ValidationResult **shall** conform to schema in `raw/02-Formal-Artifact-Schemas.md` |
| M06-VR-002 | ValidationResult **shall** include target identifier |
| M06-VR-003 | ValidationResult **shall** include status (passed/failed) |
| M06-VR-004 | ValidationResult **shall** include error array for failures |
| M06-VR-005 | ValidationResult **shall** be saved to `artifacts/validation/` |

**ValidationResult Schema:**
```json
{
  "target": "string (required)",
  "status": "passed | failed (required)",
  "errors": ["string"] (optional)
}
```

---

## 6. Features

| Feature ID | Feature Name | Priority | Description |
|------------|--------------|----------|-------------|
| F06-01 | Test Runner Adapter | P0 | Language-agnostic test execution |
| F06-02 | Lint Runner Adapter | P1 | Language-agnostic lint execution |
| F06-03 | Architecture Validator | P1 | Hexagonal layer import checking (optional) |
| F06-04 | Invariant Checker | P1 | Domain constraint verification |
| F06-05 | ValidationResult Generator | P0 | Foundation - defines types and generation |

---

## 7. Success Criteria

- [ ] Tests run via native runners for all supported languages
- [ ] Lint checks run via native linters for all supported languages
- [ ] Failures produce clear ValidationResult with actionable errors
- [ ] Architecture violations are detected (if enabled)
- [ ] Invariants are verified before validation proceeds
- [ ] Validation feeds back to planning loop
- [ ] All validation actions logged to audit trail
- [ ] Unit tests for all validators
- [ ] mypy passes
- [ ] ruff passes

---

## 8. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Milestone 02 | Required | ValidationResult artifact type defined |
| Milestone 03 | Required | CLI `rice-factor test` command |
| Milestone 05 | Required | Capability Registry for language detection |

---

## 9. Implementation Order

1. **F06-05**: ValidationResult Generator (P0 - foundation)
   - Defines ValidatorPort protocol
   - Defines ValidationResult types
   - Defines validation error hierarchy

2. **F06-01**: Test Runner Adapter (P0 - core functionality)
   - Implements test execution
   - Integrates with capability registry

3. **F06-02**: Lint Runner Adapter (P1 - extends pattern)
   - Implements lint execution
   - Follows test runner pattern

4. **F06-04**: Invariant Checker (P1 - domain constraints)
   - Verifies domain rules
   - Independent of external tools

5. **F06-03**: Architecture Validator (P1 - optional)
   - Import analysis
   - Can defer if time-constrained

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone requirements |
| 1.1.0 | 2026-01-10 | SDD Process | Added features section |
| 1.2.0 | 2026-01-10 | SDD Process | Expanded requirements, added domain-specific sections |
