"""Project templates for quick start setup."""

from rice_factor.adapters.templates.template_registry import (
    ProjectTemplate,
    TemplateConfig,
    TemplateRegistry,
)
from rice_factor.adapters.templates.templates import (
    BUILTIN_TEMPLATES,
    create_python_clean_template,
    create_go_hexagonal_template,
    create_rust_ddd_template,
    create_typescript_react_template,
    create_java_spring_template,
)

__all__ = [
    "BUILTIN_TEMPLATES",
    "ProjectTemplate",
    "TemplateConfig",
    "TemplateRegistry",
    "create_go_hexagonal_template",
    "create_java_spring_template",
    "create_python_clean_template",
    "create_rust_ddd_template",
    "create_typescript_react_template",
]
