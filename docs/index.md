# Rice-Factor Documentation

<p align="center">
    <img src="../.branding/logo.svg" alt="Rice-Factor" width="300">
</p>

<p align="center">
  <strong>LLM-Assisted Development System</strong><br>
  Treating LLMs as compilers, artifacts as IR
</p>

---

## What is Rice-Factor?

Rice-Factor is a language-agnostic, LLM-assisted software development system that treats LLMs as **compilers generating structured plan artifacts**, not direct code generators.

**Key Principles:**

- **Artifacts over prompts** - Plans are first-class data structures
- **Plans before code** - Never write code without a plan artifact
- **Tests before implementation** - TDD enforced at system level
- **Human approval required** - At all irreversible boundaries

## Quick Start

```bash
# Install
pip install rice-factor

# Initialize project
rice-factor init

# Generate and approve plans
rice-factor plan project
rice-factor approve <id>

# Scaffold, test, implement
rice-factor scaffold
rice-factor plan tests
rice-factor lock tests
rice-factor impl <file>
rice-factor test
```

## Documentation Sections

<div class="grid cards" markdown>

-   :material-rocket-launch: **Getting Started**

    ---

    Installation, first project, core concepts

    [:octicons-arrow-right-24: Get started](guides/getting-started/installation.md)

-   :material-book-open-variant: **Tutorials**

    ---

    Step-by-step guides for common workflows

    [:octicons-arrow-right-24: Learn](guides/tutorials/basic-workflow.md)

-   :material-tools: **How-To Guides**

    ---

    Task-oriented guides for specific needs

    [:octicons-arrow-right-24: How-to](guides/how-to/configure-llm-providers.md)

-   :material-file-document: **Reference**

    ---

    CLI commands, configuration, schemas

    [:octicons-arrow-right-24: Reference](reference/cli/commands.md)

</div>

## The Rice-Factor Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      RICE-FACTOR WORKFLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. INIT           rice-factor init                             │
│     │              Create .project/ with requirements           │
│     ▼                                                           │
│  2. PLAN           rice-factor plan project                     │
│     │              LLM generates ProjectPlan artifact           │
│     ▼                                                           │
│  3. APPROVE        rice-factor approve <id>                     │
│     │              Human reviews and approves                   │
│     ▼                                                           │
│  4. SCAFFOLD       rice-factor scaffold                         │
│     │              Create empty file structure                  │
│     ▼                                                           │
│  5. TEST PLAN      rice-factor plan tests                       │
│     │              Generate TestPlan from requirements          │
│     ▼                                                           │
│  6. LOCK           rice-factor lock tests                       │
│     │              Tests become IMMUTABLE                       │
│     ▼                                                           │
│  7. IMPLEMENT      rice-factor impl <file>                      │
│     │              Generate code to satisfy tests               │
│     ▼                                                           │
│  8. TEST           rice-factor test                             │
│                    Verify implementation passes                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Why Rice-Factor?

| Traditional LLM | Rice-Factor |
|-----------------|-------------|
| LLM writes code directly | LLM generates structured plans |
| Code reviewed after writing | Plans reviewed before execution |
| Tests are optional | Tests are locked, immutable |
| No audit trail | Full audit trail |
| Non-deterministic | Reproducible workflows |

## Supported LLM Providers

- **Anthropic Claude** - Claude 3.5 Sonnet, Claude 3 Opus
- **OpenAI** - GPT-4 Turbo, GPT-4o
- **Ollama** - Llama 2, Mistral, CodeLlama (local)
- **vLLM** - Any supported model (local, GPU-accelerated)

## Architecture

Rice-Factor uses **Hexagonal Architecture** (Ports & Adapters):

```
┌─────────────────────────────────────────────┐
│              Entrypoints                    │
│         (CLI, TUI, Web, API)                │
├─────────────────────────────────────────────┤
│              Adapters                       │
│    (LLM, Storage, Executor, Validator)      │
├─────────────────────────────────────────────┤
│               Domain                        │
│    (Ports, Services, Artifacts, Models)     │
└─────────────────────────────────────────────┘
```

## Getting Help

- [FAQ](guides/troubleshooting/faq.md) - Frequently asked questions
- [Common Errors](guides/troubleshooting/common-errors.md) - Error solutions
- [GitHub Issues](https://github.com/user/rice-factor/issues) - Report bugs

## License

Rice-Factor is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
