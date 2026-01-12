# Contributing to Rice-Factor

Thank you for your interest in contributing! This document provides quick guidelines.

## Quick Links

- [Full Contributing Guide](docs/contributing/README.md)
- [Development Guide](docs/contributing/development.md)
- [Code of Conduct](#code-of-conduct)

## Getting Started

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/rice-factor.git
cd rice-factor

# Create virtual environment
uv venv && source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Ways to Contribute

### Report Bugs

1. Check [existing issues](https://github.com/user/rice-factor/issues)
2. Create new issue with:
   - Rice-Factor version
   - Steps to reproduce
   - Expected vs actual behavior

### Suggest Features

1. Open a [Discussion](https://github.com/user/rice-factor/discussions)
2. Describe use case and benefits
3. Consider implementation approach

### Submit Code

1. Fork the repository
2. Create feature branch: `git checkout -b feat/my-feature`
3. Write tests
4. Run checks: `pre-commit run --all-files`
5. Submit pull request

## Code Style

- Python 3.11+ with type hints
- Follow PEP 8
- Use [Conventional Commits](https://www.conventionalcommits.org/)
- Write Google-style docstrings

## Pull Request Checklist

- [ ] Tests pass (`pytest`)
- [ ] Type checks pass (`mypy rice_factor`)
- [ ] Linting passes (`ruff check rice_factor`)
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventions

## Code of Conduct

Be respectful and inclusive. We welcome contributors of all backgrounds and experience levels.

## License

By contributing, you agree your contributions will be licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

## Questions?

- Open a [Discussion](https://github.com/user/rice-factor/discussions)
- Check [FAQ](docs/guides/troubleshooting/faq.md)
