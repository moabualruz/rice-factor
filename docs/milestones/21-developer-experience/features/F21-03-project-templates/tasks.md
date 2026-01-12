# F21-03: Project Templates - Tasks

## Tasks
### T21-03-01: Create Template System - DONE
### T21-03-02: Create Python Template - DONE
### T21-03-03: Create Go Template - DONE
### T21-03-04: Create Rust Template - DONE
### T21-03-05: Tests - DONE

## Actual Test Count: 33

## Implementation Notes
- Created `rice_factor/adapters/templates/` package
- Models: TemplateConfig, FileTemplate, DirectoryTemplate, ProjectTemplate
- TemplateRegistry with register, unregister, get, list, search, apply operations
- 5 built-in templates:
  - python-clean: Python clean architecture with pytest, mypy, ruff
  - go-hexagonal: Go hexagonal architecture with ports/adapters
  - rust-ddd: Rust DDD with domain/application/infrastructure layers
  - typescript-react: TypeScript React SPA with Vite
  - java-spring: Java Spring Boot with Maven
- Variable substitution in templates ({{ project_name }}, etc.)
- Template validation (name, language, architecture, duplicate files)
