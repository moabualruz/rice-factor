"""Built-in project templates.

Provides pre-configured templates for common project setups.
"""

from __future__ import annotations

from rice_factor.adapters.templates.template_registry import (
    DirectoryTemplate,
    FileTemplate,
    ProjectTemplate,
    TemplateConfig,
)


def create_python_clean_template() -> ProjectTemplate:
    """Create a Python clean architecture template.

    Returns:
        Python clean architecture project template.
    """
    config = TemplateConfig(
        name="python-clean",
        description="Python project with clean architecture",
        language="python",
        architecture="clean",
        tags=["python", "clean", "tdd", "pydantic"],
    )

    directories = [
        DirectoryTemplate("src", "Application source code"),
        DirectoryTemplate("src/domain", "Domain models and business logic"),
        DirectoryTemplate("src/application", "Application services"),
        DirectoryTemplate("src/infrastructure", "Infrastructure adapters"),
        DirectoryTemplate("tests", "Test directory"),
        DirectoryTemplate("tests/unit", "Unit tests"),
        DirectoryTemplate("tests/integration", "Integration tests"),
    ]

    files = [
        FileTemplate(
            "pyproject.toml",
            '''[project]
name = "{{ project_name }}"
version = "0.1.0"
description = "{{ description }}"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "mypy>=1.0",
    "ruff>=0.3",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.mypy]
strict = true

[tool.ruff]
line-length = 88
target-version = "py311"
''',
            "Project configuration",
        ),
        FileTemplate(
            "src/__init__.py",
            '"""{{ project_name }} package."""\n',
            "Package init",
        ),
        FileTemplate(
            "src/domain/__init__.py",
            '"""Domain layer - business logic and models."""\n',
            "Domain layer init",
        ),
        FileTemplate(
            "src/application/__init__.py",
            '"""Application layer - services and use cases."""\n',
            "Application layer init",
        ),
        FileTemplate(
            "src/infrastructure/__init__.py",
            '"""Infrastructure layer - external adapters."""\n',
            "Infrastructure layer init",
        ),
        FileTemplate(
            "tests/__init__.py",
            '"""Tests package."""\n',
            "Tests init",
        ),
        FileTemplate(
            ".gitignore",
            """# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
.env

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/
*.swp

# Build
dist/
build/
*.egg-info/
""",
            "Git ignore patterns",
        ),
    ]

    project_context = {
        "architecture": "clean",
        "languages": ["python"],
        "test_runner": "pytest",
    }

    return ProjectTemplate(
        config=config,
        directories=directories,
        files=files,
        project_context=project_context,
        dev_dependencies=["pytest", "pytest-cov", "mypy", "ruff"],
    )


def create_go_hexagonal_template() -> ProjectTemplate:
    """Create a Go hexagonal architecture template.

    Returns:
        Go hexagonal architecture project template.
    """
    config = TemplateConfig(
        name="go-hexagonal",
        description="Go project with hexagonal architecture",
        language="go",
        architecture="hexagonal",
        tags=["go", "hexagonal", "ports-adapters"],
    )

    directories = [
        DirectoryTemplate("cmd", "Application entry points"),
        DirectoryTemplate("internal/domain", "Domain models and ports"),
        DirectoryTemplate("internal/adapters/primary", "Primary adapters (handlers)"),
        DirectoryTemplate("internal/adapters/secondary", "Secondary adapters (repos)"),
        DirectoryTemplate("pkg", "Shared packages"),
    ]

    files = [
        FileTemplate(
            "go.mod",
            """module {{ module_path }}

go 1.21
""",
            "Go module definition",
        ),
        FileTemplate(
            "cmd/main.go",
            """package main

import "fmt"

func main() {
	fmt.Println("{{ project_name }}")
}
""",
            "Application entry point",
        ),
        FileTemplate(
            "internal/domain/ports.go",
            """package domain

// Repository defines the data access port.
type Repository interface {
	// Add repository methods here
}

// Service defines the application service port.
type Service interface {
	// Add service methods here
}
""",
            "Port definitions",
        ),
        FileTemplate(
            "Makefile",
            """.PHONY: build test run

build:
	go build -o bin/{{ project_name }} ./cmd

test:
	go test -v ./...

run:
	go run ./cmd
""",
            "Build automation",
        ),
        FileTemplate(
            ".gitignore",
            """# Go
bin/
vendor/
*.exe
*.test
*.out

# IDE
.idea/
.vscode/
""",
            "Git ignore patterns",
        ),
    ]

    project_context = {
        "architecture": "hexagonal",
        "languages": ["go"],
        "test_runner": "go test",
    }

    return ProjectTemplate(
        config=config,
        directories=directories,
        files=files,
        project_context=project_context,
    )


def create_rust_ddd_template() -> ProjectTemplate:
    """Create a Rust DDD architecture template.

    Returns:
        Rust DDD architecture project template.
    """
    config = TemplateConfig(
        name="rust-ddd",
        description="Rust project with DDD architecture",
        language="rust",
        architecture="ddd",
        tags=["rust", "ddd", "domain-driven"],
    )

    directories = [
        DirectoryTemplate("src/domain", "Domain layer"),
        DirectoryTemplate("src/application", "Application services"),
        DirectoryTemplate("src/infrastructure", "Infrastructure layer"),
        DirectoryTemplate("tests", "Integration tests"),
    ]

    files = [
        FileTemplate(
            "Cargo.toml",
            '''[package]
name = "{{ project_name }}"
version = "0.1.0"
edition = "2021"

[dependencies]

[dev-dependencies]
''',
            "Cargo manifest",
        ),
        FileTemplate(
            "src/main.rs",
            '''mod domain;
mod application;
mod infrastructure;

fn main() {
    println!("{{ project_name }}");
}
''',
            "Application entry point",
        ),
        FileTemplate(
            "src/domain/mod.rs",
            """//! Domain layer - entities, value objects, aggregates.

pub mod entities;
pub mod value_objects;
""",
            "Domain module",
        ),
        FileTemplate(
            "src/domain/entities.rs",
            "//! Domain entities.\n",
            "Entities module",
        ),
        FileTemplate(
            "src/domain/value_objects.rs",
            "//! Value objects.\n",
            "Value objects module",
        ),
        FileTemplate(
            "src/application/mod.rs",
            "//! Application services layer.\n",
            "Application module",
        ),
        FileTemplate(
            "src/infrastructure/mod.rs",
            "//! Infrastructure layer - repositories, external services.\n",
            "Infrastructure module",
        ),
        FileTemplate(
            ".gitignore",
            """# Rust
/target/
Cargo.lock

# IDE
.idea/
.vscode/
""",
            "Git ignore patterns",
        ),
    ]

    project_context = {
        "architecture": "ddd",
        "languages": ["rust"],
        "test_runner": "cargo test",
    }

    return ProjectTemplate(
        config=config,
        directories=directories,
        files=files,
        project_context=project_context,
    )


def create_typescript_react_template() -> ProjectTemplate:
    """Create a TypeScript React template.

    Returns:
        TypeScript React project template.
    """
    config = TemplateConfig(
        name="typescript-react",
        description="TypeScript React application",
        language="typescript",
        architecture="custom",
        tags=["typescript", "react", "frontend", "spa"],
    )

    directories = [
        DirectoryTemplate("src", "Source code"),
        DirectoryTemplate("src/components", "React components"),
        DirectoryTemplate("src/hooks", "Custom hooks"),
        DirectoryTemplate("src/services", "API services"),
        DirectoryTemplate("src/types", "TypeScript types"),
        DirectoryTemplate("public", "Static assets"),
    ]

    files = [
        FileTemplate(
            "package.json",
            """{
  "name": "{{ project_name }}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "test": "vitest",
    "lint": "eslint src"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0"
  }
}
""",
            "Package manifest",
        ),
        FileTemplate(
            "tsconfig.json",
            """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
""",
            "TypeScript configuration",
        ),
        FileTemplate(
            "src/main.tsx",
            """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""",
            "Application entry point",
        ),
        FileTemplate(
            "src/App.tsx",
            """function App() {
  return (
    <div>
      <h1>{{ project_name }}</h1>
    </div>
  );
}

export default App;
""",
            "Main App component",
        ),
        FileTemplate(
            "index.html",
            """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ project_name }}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",
            "HTML entry point",
        ),
        FileTemplate(
            ".gitignore",
            """# Dependencies
node_modules/

# Build
dist/

# IDE
.idea/
.vscode/
*.swp

# Environment
.env
.env.local
""",
            "Git ignore patterns",
        ),
    ]

    project_context = {
        "architecture": "custom",
        "languages": ["typescript"],
        "test_runner": "vitest",
    }

    return ProjectTemplate(
        config=config,
        directories=directories,
        files=files,
        project_context=project_context,
        dependencies=["react", "react-dom"],
        dev_dependencies=["typescript", "vite", "vitest"],
    )


def create_java_spring_template() -> ProjectTemplate:
    """Create a Java Spring Boot template.

    Returns:
        Java Spring Boot project template.
    """
    config = TemplateConfig(
        name="java-spring",
        description="Java Spring Boot application",
        language="java",
        architecture="hexagonal",
        tags=["java", "spring", "spring-boot", "hexagonal"],
    )

    directories = [
        DirectoryTemplate("src/main/java", "Java source code"),
        DirectoryTemplate("src/main/resources", "Application resources"),
        DirectoryTemplate("src/test/java", "Test source code"),
    ]

    files = [
        FileTemplate(
            "pom.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>{{ group_id }}</groupId>
    <artifactId>{{ project_name }}</artifactId>
    <version>0.1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>

    <properties>
        <java.version>21</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
""",
            "Maven POM",
        ),
        FileTemplate(
            "src/main/resources/application.properties",
            """# Application properties
spring.application.name={{ project_name }}
server.port=8080
""",
            "Application properties",
        ),
        FileTemplate(
            ".gitignore",
            """# Java
*.class
*.jar
*.war

# Maven
target/

# IDE
.idea/
*.iml
.vscode/

# OS
.DS_Store
""",
            "Git ignore patterns",
        ),
    ]

    project_context = {
        "architecture": "hexagonal",
        "languages": ["java"],
        "test_runner": "mvn test",
    }

    return ProjectTemplate(
        config=config,
        directories=directories,
        files=files,
        project_context=project_context,
    )


# Built-in templates registry
BUILTIN_TEMPLATES: dict[str, ProjectTemplate] = {
    "python-clean": create_python_clean_template(),
    "go-hexagonal": create_go_hexagonal_template(),
    "rust-ddd": create_rust_ddd_template(),
    "typescript-react": create_typescript_react_template(),
    "java-spring": create_java_spring_template(),
}
