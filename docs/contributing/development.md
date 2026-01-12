# Development Guide

Detailed guide for developing Rice-Factor.

## Development Environment

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| uv | Latest | Package management |
| Git | 2.30+ | Version control |
| Pre-commit | 3.0+ | Git hooks |

### Optional Tools

| Tool | Purpose |
|------|---------|
| Docker | Container testing |
| VHS | Demo GIF generation |
| MkDocs | Documentation preview |

### IDE Setup

**VS Code** (recommended):
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "strict",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

**PyCharm**:
1. Set Python interpreter to `.venv/bin/python`
2. Enable type checking (strict)
3. Configure Ruff as external tool

## Project Structure

```
rice-factor/
├── rice_factor/              # Main package
│   ├── domain/               # Core domain (no external deps)
│   │   ├── artifacts/        # Artifact models
│   │   ├── ports/            # Interface definitions
│   │   ├── services/         # Business logic
│   │   └── failures/         # Error models
│   ├── adapters/             # External integrations
│   │   ├── llm/              # LLM providers
│   │   ├── storage/          # Storage backends
│   │   ├── executors/        # Plan executors
│   │   └── validators/       # Validation adapters
│   ├── entrypoints/          # Application entry points
│   │   ├── cli/              # Typer CLI
│   │   ├── tui/              # Textual TUI
│   │   └── web/              # FastAPI web
│   └── config/               # Configuration
│       ├── settings.py       # Dynaconf settings
│       └── container.py      # DI container
├── schemas/                  # JSON Schema definitions
├── tests/                    # Test suites
├── docs/                     # Documentation
└── scripts/                  # Development scripts
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b feat/my-feature
```

### 2. Write Code

Follow the [architecture guidelines](../reference/architecture/overview.md):

```python
# 1. Domain first (if new model)
# rice_factor/domain/artifacts/payloads.py

# 2. Port definition (if new capability)
# rice_factor/domain/ports/my_port.py

# 3. Adapter implementation
# rice_factor/adapters/my_adapter/implementation.py

# 4. Wire in container
# rice_factor/config/container.py

# 5. CLI command (if user-facing)
# rice_factor/entrypoints/cli/commands/my_command.py
```

### 3. Write Tests

```bash
# Create test file
touch tests/domain/test_my_feature.py

# Write tests following pytest conventions
```

### 4. Run Checks

```bash
# All checks
pre-commit run --all-files

# Individual checks
pytest                          # Tests
mypy rice_factor               # Type checking
ruff check rice_factor         # Linting
ruff format --check rice_factor # Formatting
```

### 5. Commit and Push

```bash
git add .
git commit -m "feat(scope): description"
git push origin feat/my-feature
```

### 6. Create Pull Request

Open PR on GitHub with:
- Description of changes
- Link to related issue
- Test instructions

## Testing

### Test Categories

| Category | Location | Speed | External Deps |
|----------|----------|-------|---------------|
| Unit | `tests/domain/` | Fast | None |
| Integration | `tests/adapters/` | Medium | May require |
| E2E | `tests/e2e/` | Slow | Full system |

### Running Tests

```bash
# All tests
pytest

# Specific category
pytest tests/domain/
pytest tests/adapters/
pytest tests/e2e/

# With coverage
pytest --cov=rice_factor --cov-report=html
open htmlcov/index.html

# Parallel execution
pytest -n auto

# Stop on first failure
pytest -x

# Verbose output
pytest -v

# Match pattern
pytest -k "test_approve"
```

### Test Fixtures

Common fixtures in `tests/conftest.py`:

```python
@pytest.fixture
def mock_storage():
    """In-memory storage for testing."""
    return InMemoryStorage()

@pytest.fixture
def mock_llm():
    """Mock LLM that returns predefined responses."""
    return MockLLM()

@pytest.fixture
def temp_project(tmp_path):
    """Temporary project directory."""
    project = tmp_path / "test-project"
    project.mkdir()
    (project / ".project").mkdir()
    return project
```

### Writing Good Tests

```python
class TestArtifactApproval:
    """Tests for artifact approval functionality."""

    def test_approve_draft_succeeds(self, mock_storage):
        """Approving a DRAFT artifact should succeed."""
        # Arrange
        service = ArtifactService(storage=mock_storage)
        artifact = service.create(...)

        # Act
        result = service.approve(artifact.id)

        # Assert
        assert result.status == ArtifactStatus.APPROVED

    def test_approve_already_approved_fails(self, mock_storage):
        """Approving an APPROVED artifact should fail."""
        service = ArtifactService(storage=mock_storage)
        artifact = service.create(...)
        service.approve(artifact.id)

        with pytest.raises(ArtifactStatusError):
            service.approve(artifact.id)
```

## Debugging

### CLI Debugging

```bash
# Verbose output
rice-factor --verbose plan project

# Debug logging
RICE_LOG_LEVEL=DEBUG rice-factor plan project

# Python debugger
python -m pdb -m rice_factor.entrypoints.cli.main plan project
```

### Test Debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Set breakpoint in code
import pdb; pdb.set_trace()

# VS Code: Use "Python: Debug Tests" configuration
```

### Common Issues

**Import errors:**
```bash
# Ensure package is installed in editable mode
pip install -e ".[dev]"
```

**Type errors:**
```bash
# Check specific file
mypy rice_factor/domain/services/artifact_service.py

# Reveal inferred types
mypy --show-error-codes --pretty rice_factor/
```

**Test isolation:**
```bash
# Run tests in random order to find dependencies
pytest --randomly-seed=12345
```

## Documentation

### Preview Locally

```bash
# Install MkDocs
pip install mkdocs-material

# Serve with auto-reload
mkdocs serve

# Open http://localhost:8000
```

### Update Documentation

```bash
# Edit markdown files in docs/

# Check for broken links
mkdocs build --strict

# Preview changes
mkdocs serve
```

### Docstring Format

```python
def function_name(param1: str, param2: int = 10) -> Result:
    """Short one-line description.

    Longer description with more details about the function,
    its behavior, and any important notes.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.
            Can span multiple lines if needed.

    Returns:
        Description of return value.
        Can include structure details.

    Raises:
        ValueError: When param1 is invalid.
        RuntimeError: When operation fails.

    Example:
        Basic usage::

            result = function_name("value", 42)
            print(result)

    Note:
        Additional notes or warnings.

    See Also:
        - :func:`related_function`
        - :class:`RelatedClass`
    """
```

## Release Process

### Version Bumping

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md

# Commit and tag
git add .
git commit -m "chore: release v0.2.0"
git tag v0.2.0
git push origin main --tags
```

### Changelog Format

```markdown
## [0.2.0] - 2024-01-20

### Added
- New feature X (#123)
- Support for Y

### Changed
- Improved Z performance

### Fixed
- Bug in artifact approval (#456)

### Deprecated
- Old API endpoint (use new one)

### Removed
- Legacy support for X
```

## Performance

### Profiling

```bash
# Profile CLI command
python -m cProfile -o profile.prof -m rice_factor.entrypoints.cli.main plan project

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.prof
```

### Benchmarking

```python
# tests/benchmarks/test_performance.py
import pytest

@pytest.mark.benchmark
def test_artifact_creation_speed(benchmark, mock_storage):
    service = ArtifactService(storage=mock_storage)

    result = benchmark(
        service.create,
        artifact_type=ArtifactType.PROJECT_PLAN,
        payload=sample_payload,
    )

    assert result is not None
```

```bash
# Run benchmarks
pytest tests/benchmarks/ --benchmark-only
```

## Troubleshooting

### Common Development Issues

**"Module not found" errors:**
```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

**Pre-commit hooks failing:**
```bash
# Update hooks
pre-commit autoupdate

# Run specific hook
pre-commit run ruff --all-files
```

**Tests hanging:**
```bash
# Run with timeout
pytest --timeout=30

# Check for blocking I/O
pytest -v --tb=short
```

**Mypy cache issues:**
```bash
# Clear cache
rm -rf .mypy_cache/
mypy rice_factor
```

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
