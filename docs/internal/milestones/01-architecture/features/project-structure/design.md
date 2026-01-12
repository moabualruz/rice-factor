# Feature F01-01: Project Folder Structure - Design

> **Document Type**: Feature Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent Milestone**: [01-Architecture Design](../../design.md)

---

## 1. Design Approach

### 1.1 Selected Pattern: Clean Architecture

The folder structure implements Clean Architecture with clear layer boundaries:

1. **Domain Layer** (`core/domain/`) - Business entities and rules
2. **Application Layer** (`core/application/`) - Use cases and orchestration
3. **Infrastructure Layer** (`core/infrastructure/`) - External adapters
4. **Interface Layer** (`cli/`) - User interface

### 1.2 Dependency Direction

```
cli/ → core/application/ → core/domain/
                  ↓
          core/infrastructure/ (implements domain protocols)
```

---

## 2. Directory Structure

```
rice-factor/
├── cli/
│   ├── __init__.py
│   ├── main.py
│   └── commands/
│       └── __init__.py
│
├── core/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── artifacts/
│   │   │   └── __init__.py
│   │   ├── failures/
│   │   │   └── __init__.py
│   │   └── protocols/
│   │       └── __init__.py
│   ├── application/
│   │   ├── __init__.py
│   │   └── services/
│   │       └── __init__.py
│   └── infrastructure/
│       ├── __init__.py
│       ├── llm/
│       │   └── __init__.py
│       ├── executors/
│       │   └── __init__.py
│       ├── validators/
│       │   └── __init__.py
│       ├── storage/
│       │   └── __init__.py
│       └── audit/
│           └── __init__.py
│
├── schemas/
│   └── .gitkeep
│
├── tools/
│   └── registry/
│       └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   └── __init__.py
│   ├── integration/
│   │   └── __init__.py
│   └── e2e/
│       └── __init__.py
│
├── docs/
│   ├── project/
│   └── milestones/
│
├── pyproject.toml
├── README.md
├── CLAUDE.md
└── .gitignore
```

---

## 3. File Contents

### 3.1 Root `__init__.py` Pattern

```python
"""Rice-Factor: LLM-assisted development system."""
```

### 3.2 Subpackage `__init__.py` Pattern

```python
"""<Package description>."""
from <package>.<module> import <exports>  # When applicable
```

### 3.3 `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp

# Environment
.env
.env.local

# Testing
.coverage
htmlcov/
.pytest_cache/

# Type checking
.mypy_cache/

# Rice-Factor runtime
.project/
artifacts/
audit/
```

---

## 4. Implementation Notes

- Use `pathlib.Path` for all path operations
- Ensure cross-platform compatibility (Windows, macOS, Linux)
- Create `.gitkeep` files in empty directories that need to be tracked

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial feature design |
