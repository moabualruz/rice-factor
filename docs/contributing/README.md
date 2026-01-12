# Contributing to Rice-Factor

Thank you for your interest in contributing to Rice-Factor! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Ways to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/user/rice-factor/issues) first
2. Use the bug report template
3. Include:
   - Rice-Factor version (`rice-factor --version`)
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs or error messages

### Suggesting Features

1. Check existing issues and discussions
2. Use the feature request template
3. Describe the use case and benefits
4. Consider implementation complexity

### Contributing Code

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/rice-factor.git
cd rice-factor

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rice_factor --cov-report=html

# Run specific test file
pytest tests/domain/test_artifacts.py

# Run tests matching pattern
pytest -k "test_approve"
```

### Code Quality

```bash
# Type checking
mypy rice_factor

# Linting
ruff check rice_factor

# Formatting
ruff format rice_factor

# All checks (pre-commit)
pre-commit run --all-files
```

## Code Style

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all functions
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names

```python
# Good
def approve_artifact(artifact_id: str) -> ArtifactEnvelope:
    """Approve an artifact by ID.

    Args:
        artifact_id: The unique identifier of the artifact.

    Returns:
        The approved artifact.

    Raises:
        ArtifactNotFoundError: If artifact doesn't exist.
        ArtifactStatusError: If artifact is not in DRAFT status.
    """
    ...

# Avoid
def approve(id):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of the function.

    Longer description if needed, explaining behavior,
    edge cases, or important notes.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is empty.
        TypeError: When param2 is not an integer.

    Example:
        >>> function_name("hello", 42)
        True
    """
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(cli): add --verbose flag to plan command

fix(storage): handle Unicode filenames correctly

docs(readme): update installation instructions

refactor(adapters): extract common LLM logic to base class
```

## Architecture Guidelines

### Hexagonal Architecture

Rice-Factor uses hexagonal (ports & adapters) architecture:

```
domain/     → Core logic, NO external dependencies
adapters/   → Implement domain ports
entrypoints/→ CLI, TUI, Web interfaces
config/     → Configuration and DI
```

**Rules:**
1. Domain layer has NO imports from adapters or entrypoints
2. Domain uses only stdlib + Pydantic
3. Adapters implement protocols from domain/ports/
4. Entrypoints wire everything together

### Adding New Features

1. **Define the domain model** (if needed)
   ```python
   # rice_factor/domain/artifacts/payloads.py
   class NewPayload(BaseModel):
       ...
   ```

2. **Define the port** (if new capability)
   ```python
   # rice_factor/domain/ports/new_port.py
   class NewPort(Protocol):
       def do_something(self, arg: str) -> Result:
           ...
   ```

3. **Implement the adapter**
   ```python
   # rice_factor/adapters/new/implementation.py
   class NewAdapter(NewPort):
       def do_something(self, arg: str) -> Result:
           ...
   ```

4. **Wire in container**
   ```python
   # rice_factor/config/container.py
   def get_new_adapter(self) -> NewPort:
       return NewAdapter(...)
   ```

5. **Add CLI command** (if user-facing)
   ```python
   # rice_factor/entrypoints/cli/commands/new.py
   @app.command()
   def new_command():
       ...
   ```

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally (`pytest`)
- [ ] Type checks pass (`mypy rice_factor`)
- [ ] Linting passes (`ruff check rice_factor`)
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG updated (for significant changes)

### PR Description

Include:
- What the PR does
- Why the change is needed
- How to test it
- Screenshots (for UI changes)

### Review Process

1. Automated checks run (CI)
2. Maintainer reviews code
3. Address feedback
4. Squash and merge when approved

## Testing Guidelines

### Test Structure

```
tests/
├── domain/           # Unit tests (no external deps)
├── adapters/         # Integration tests
├── e2e/              # End-to-end tests
├── conftest.py       # Shared fixtures
└── mocks/            # Mock implementations
```

### Writing Tests

```python
# tests/domain/test_artifact_service.py
import pytest
from rice_factor.domain.services import ArtifactService

class TestArtifactService:
    """Tests for ArtifactService."""

    def test_create_returns_draft_artifact(self, mock_storage):
        """Creating an artifact should return DRAFT status."""
        service = ArtifactService(storage=mock_storage)

        artifact = service.create(
            artifact_type=ArtifactType.PROJECT_PLAN,
            payload={"domains": [{"name": "core"}]},
        )

        assert artifact.status == ArtifactStatus.DRAFT

    def test_approve_transitions_to_approved(self, mock_storage):
        """Approving should transition DRAFT to APPROVED."""
        ...

    @pytest.mark.parametrize("invalid_status", [
        ArtifactStatus.APPROVED,
        ArtifactStatus.LOCKED,
    ])
    def test_approve_rejects_non_draft(self, invalid_status, mock_storage):
        """Approving non-DRAFT artifacts should raise error."""
        ...
```

### Test Markers

```python
@pytest.mark.unit       # Fast, no external deps
@pytest.mark.integration # Requires external service
@pytest.mark.e2e        # Full workflow test
@pytest.mark.slow       # Long-running test
```

## Documentation

### Where to Document

| Type | Location |
|------|----------|
| User guides | `docs/guides/` |
| Reference | `docs/reference/` |
| API docs | Docstrings (auto-generated) |
| Internal | `docs/internal/` |

### Building Docs

```bash
# Install MkDocs
pip install mkdocs-material

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/user/rice-factor/discussions)
- **Bugs**: Open an [Issue](https://github.com/user/rice-factor/issues)
- **Chat**: Join our Discord (link TBD)

## License

By contributing, you agree that your contributions will be licensed under the same [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) license as the project.
