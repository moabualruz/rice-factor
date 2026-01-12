# Frequently Asked Questions

Common questions about Rice-Factor.

## General

### What is Rice-Factor?

Rice-Factor is an LLM-assisted software development system that treats LLMs as compilers generating structured plan artifacts, not direct code generators. It enforces TDD at the system level and requires human approval at irreversible boundaries.

### Why "Rice-Factor"?

The name represents the idea of adding quality and structure to the development process - like adding a "factor" that improves the outcome.

### How is this different from GitHub Copilot or ChatGPT?

| Feature | Copilot/ChatGPT | Rice-Factor |
|---------|----------------|-------------|
| Output | Raw code | JSON artifacts |
| Review | After code written | Before execution |
| Tests | Optional | Required, locked |
| Audit | None | Full trail |
| Determinism | Variable | Enforced |

### What languages does Rice-Factor support?

Rice-Factor is language-agnostic. The artifact system works with any language. Currently supported for refactoring:
- Python
- JavaScript/TypeScript
- Go
- Rust
- Java
- C#
- Ruby
- PHP

## Workflow

### Do I have to use all the commands?

No. The minimal workflow is:
```bash
rice-factor init
rice-factor plan project
rice-factor approve <id>
rice-factor scaffold
```

But for full TDD benefits, use the complete workflow including test locking.

### Can I skip test locking?

Technically yes, but it defeats the purpose. Test locking ensures TDD is enforced - tests become the source of truth that implementation must satisfy.

### What happens if I edit code manually?

You can! Rice-Factor doesn't prevent manual edits. However:
- Manual edits won't have artifacts
- Drift detection may flag them
- Consider using `rice-factor audit drift` to check

### Can I use Rice-Factor on existing projects?

Yes. Run `rice-factor init` in your project root. You can incrementally adopt Rice-Factor for new features while maintaining existing code.

## Artifacts

### Where are artifacts stored?

In `.project/artifacts/` organized by type:
```
.project/artifacts/
├── project_plans/
├── test_plans/
├── implementation_plans/
└── ...
```

### Can I edit artifacts directly?

You can edit DRAFT artifacts, but:
- APPROVED artifacts are immutable
- LOCKED artifacts are permanently immutable
- Prefer regenerating over editing

### What if I approved the wrong artifact?

Generate a new one. The old artifact remains but won't be used if you approve and use the new one.

### How do I delete an artifact?

```bash
rice-factor artifact delete <id>
```

Note: Can't delete LOCKED artifacts.

## Tests

### Why can't I change locked tests?

Locked tests enforce TDD at the system level. If tests could be changed, developers might modify tests to match buggy implementation instead of fixing the implementation.

### What if a locked test is genuinely wrong?

This is rare if you review carefully before locking. Options:
1. Complete current cycle with workaround
2. Document the issue
3. Start fresh cycle with corrected requirements
4. Use override (last resort, audited)

### Can I add more tests after locking?

Not to the locked TestPlan. You would:
1. Complete current implementation
2. Create new requirements for additional features
3. Generate new TestPlan
4. Lock and implement new tests

## LLM/Providers

### Which LLM should I use?

| Use Case | Recommendation |
|----------|---------------|
| Best quality | Claude 3.5 Sonnet or GPT-4 Turbo |
| Fast iteration | Claude 3 Haiku or GPT-3.5 |
| Privacy/Offline | Ollama with Llama 2 |

### How much does it cost?

Costs vary by provider and usage. Typical project setup:
- Project planning: ~$0.10-0.50
- Test generation: ~$0.20-1.00
- Per-file implementation: ~$0.05-0.20

Use `rice-factor usage show` to track costs.

### Can I use Rice-Factor offline?

Yes, with local LLM providers:
- Ollama (easiest)
- vLLM (GPU-accelerated)
- LocalAI

### What about rate limits?

Rice-Factor has built-in rate limiting. Configure in `.rice-factor.yaml`:
```yaml
rate_limits:
  claude:
    requests_per_minute: 60
```

## CI/CD

### Does Rice-Factor work with GitHub Actions?

Yes! See [CI/CD Integration](../how-to/integrate-ci-cd.md).

### What does CI validate?

- Artifact schema compliance
- Approval status
- System invariants
- Audit trail integrity

### Can CI modify artifacts?

No. CI only validates - it never generates or modifies artifacts. This follows the principle that humans must approve all changes.

## Troubleshooting

### "Command not found"

Ensure Rice-Factor is installed and in PATH:
```bash
pip install rice-factor
python -m rice_factor --version
```

### "API key not set"

Set your API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### "Tests failed"

This means your implementation doesn't match the locked tests. Fix the implementation, not the tests!

### Where can I get help?

- [Common Errors](common-errors.md)
- [GitHub Issues](https://github.com/moabualruz/rice-factor/issues)
- [Documentation](../../index.md)

## Philosophy

### Why require human approval?

Automation should augment human judgment, not replace it. Requiring approval ensures:
- Humans understand what's being built
- Mistakes are caught before execution
- There's accountability for decisions

### Why immutable artifacts?

Immutability provides:
- Audit trail integrity
- Reproducibility
- Prevention of accidental modification
- Single source of truth

### Why TDD at the system level?

Traditional TDD relies on discipline. Rice-Factor makes it structural:
- Tests are locked before implementation
- Implementation MUST satisfy tests
- No "fix the test to pass" shortcuts

### Is this over-engineered for small projects?

Rice-Factor shines on:
- Projects with multiple contributors
- Long-lived codebases
- Regulated environments
- Complex domain logic

For quick scripts, simpler tools may suffice.

## Contributing

### How can I contribute?

See [CONTRIBUTING.md](../../../CONTRIBUTING.md) for guidelines.

### Can I add a new LLM provider?

Yes! Implement the `LLMPort` protocol. See existing adapters in `rice_factor/adapters/llm/`.

### Can I add support for a new language?

Yes! Add a new adapter implementing `RefactorToolPort`. See `rice_factor/adapters/refactoring/`.
