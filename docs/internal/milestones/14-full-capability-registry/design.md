# Milestone 14: Full Capability Registry - Design

> **Status**: Planned
> **Priority**: P0

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Refactoring Subsystem                        │
├─────────────────────────────────────────────────────────────────┤
│  RefactoringPort (Protocol)                                      │
│    ├── Operations: move_file, rename_symbol,                     │
│    │               extract_interface, enforce_dependency         │
│    └── Returns: RefactoringResult with diff/changes              │
├─────────────────────────────────────────────────────────────────┤
│  Language Adapters                                               │
│    ├── rope_adapter.py         # Python (NEW)                    │
│    ├── openrewrite_adapter.py  # Java/Kotlin/Groovy (ENHANCED)   │
│    ├── roslyn_adapter.py       # C# (NEW)                        │
│    ├── ruby_parser_adapter.py  # Ruby (NEW)                      │
│    ├── rector_adapter.py       # PHP (NEW)                       │
│    ├── jscodeshift_adapter.py  # JS/TS (ENHANCED)                │
│    ├── gopls_adapter.py        # Go (ENHANCED)                   │
│    ├── rust_analyzer_adapter.py # Rust (ENHANCED)                │
│    └── diff_patch_adapter.py   # Fallback (EXISTING)             │
├─────────────────────────────────────────────────────────────────┤
│  CapabilityDetector                                              │
│    ├── Probes for installed tools                                │
│    ├── Updates registry dynamically                              │
│    └── Provides capability queries                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Package Structure

```
rice_factor/adapters/refactoring/
├── __init__.py
├── base.py                      # RefactoringPort protocol
├── rope_adapter.py              # NEW: Python via Rope
├── roslyn_adapter.py            # NEW: C# via Roslyn
├── ruby_parser_adapter.py       # NEW: Ruby via Parser gem
├── rector_adapter.py            # NEW: PHP via Rector
├── openrewrite_adapter.py       # ENHANCE: Full operations
├── jscodeshift_adapter.py       # ENHANCE: extract_interface
├── gopls_adapter.py             # ENHANCE: extract_interface
├── rust_analyzer_adapter.py     # ENHANCE: extract_interface
├── diff_patch_adapter.py        # EXISTING: Fallback
└── capability_detector.py       # NEW: Auto-detect tools

rice_factor/config/
└── capability_registry.yaml     # UPDATED: Full capabilities

rice_factor/domain/services/
└── refactoring_router.py        # Routes to correct adapter
```

---

## 3. Adapter Interface

```python
from typing import Protocol, Literal
from dataclasses import dataclass

class RefactoringPort(Protocol):
    """Protocol for language-specific refactoring adapters."""

    def move_file(
        self,
        source: Path,
        destination: Path
    ) -> RefactoringResult:
        """Move file and update all references."""
        ...

    def rename_symbol(
        self,
        file: Path,
        old_name: str,
        new_name: str,
        scope: Literal["local", "project"] = "project"
    ) -> RefactoringResult:
        """Rename symbol across codebase."""
        ...

    def extract_interface(
        self,
        file: Path,
        class_name: str,
        interface_name: str,
        methods: list[str] | None = None
    ) -> RefactoringResult:
        """Extract interface/protocol from concrete class."""
        ...

    def enforce_dependency(
        self,
        rule: DependencyRule,
        fix: bool = False
    ) -> RefactoringResult:
        """Check/fix architectural dependency violations."""
        ...

@dataclass
class RefactoringResult:
    success: bool
    changes: list[FileChange]
    errors: list[str]
    warnings: list[str]

@dataclass
class FileChange:
    path: Path
    diff: str
    action: Literal["modify", "create", "delete", "move"]
```

---

## 4. Adapter Implementations

### 4.1 Rope Adapter (Python)

```python
# rice_factor/adapters/refactoring/rope_adapter.py
import rope.base.project
import rope.refactor.rename
import rope.refactor.extract
import rope.refactor.move

class RopeAdapter(RefactoringPort):
    def __init__(self, project_root: Path):
        self.project = rope.base.project.Project(str(project_root))

    def extract_interface(self, file, class_name, interface_name, methods):
        # Use Rope's extract method + generate Protocol
        resource = self.project.get_resource(str(file))
        # Generate Protocol/ABC from class methods
        ...

    def enforce_dependency(self, rule, fix):
        # Analyze imports, find violations, optionally fix
        ...
```

### 4.2 Roslyn Adapter (C#)

```python
# rice_factor/adapters/refactoring/roslyn_adapter.py
import subprocess

class RoslynAdapter(RefactoringPort):
    def extract_interface(self, file, class_name, interface_name, methods):
        # Use dotnet CLI with custom Roslyn analyzer
        # Or invoke Roslynator CLI
        result = subprocess.run([
            "dotnet", "roslynator", "refactor",
            "--extract-interface", class_name,
            "--interface-name", interface_name,
            "--methods", ",".join(methods or []),
            str(file)
        ], capture_output=True)
        ...
```

### 4.3 Ruby Parser Adapter

```python
# rice_factor/adapters/refactoring/ruby_parser_adapter.py
import subprocess

class RubyParserAdapter(RefactoringPort):
    def extract_interface(self, file, class_name, interface_name, methods):
        # Ruby doesn't have interfaces, but we can:
        # 1. Generate a module with method signatures as comments
        # 2. Generate RBS type definitions
        # Use a Ruby script that leverages Parser gem
        script = self._generate_extract_script(file, class_name, interface_name)
        result = subprocess.run(["ruby", "-e", script], capture_output=True)
        ...
```

### 4.4 Rector Adapter (PHP)

```python
# rice_factor/adapters/refactoring/rector_adapter.py
import subprocess

class RectorAdapter(RefactoringPort):
    def extract_interface(self, file, class_name, interface_name, methods):
        # Use Rector CLI with custom rule
        # Or generate rector.php config dynamically
        result = subprocess.run([
            "vendor/bin/rector", "process",
            "--config", self._generate_config(file, class_name, interface_name),
            str(file)
        ], capture_output=True)
        ...
```

---

## 5. Capability Registry Update

```yaml
# rice_factor/config/capability_registry.yaml (UPDATED)
languages:
  python:
    adapter: rope
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true

  java:
    adapter: openrewrite
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true

  kotlin:
    adapter: openrewrite
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true

  csharp:
    adapter: roslyn
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true

  javascript:
    adapter: jscodeshift
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true

  typescript:
    adapter: jscodeshift
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true

  go:
    adapter: gopls
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true

  rust:
    adapter: rust_analyzer
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true

  ruby:
    adapter: ruby_parser
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true  # Generates module/RBS
      enforce_dependency: true

  php:
    adapter: rector
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: true
      enforce_dependency: true
```

---

## 6. Capability Detector

```python
# rice_factor/adapters/refactoring/capability_detector.py
import shutil
import subprocess

class CapabilityDetector:
    """Detects available refactoring tools at runtime."""

    def detect_all(self) -> dict[str, bool]:
        """Probe for all supported tools."""
        return {
            "rope": self._check_python_package("rope"),
            "openrewrite": self._check_command("openrewrite"),
            "roslyn": self._check_command("dotnet"),
            "ruby_parser": self._check_ruby_gem("parser"),
            "rector": self._check_php_package("rector/rector"),
            "jscodeshift": self._check_npm_package("jscodeshift"),
            "gopls": self._check_command("gopls"),
            "rust_analyzer": self._check_command("rust-analyzer"),
        }

    def _check_python_package(self, package: str) -> bool:
        try:
            __import__(package)
            return True
        except ImportError:
            return False

    def _check_command(self, cmd: str) -> bool:
        return shutil.which(cmd) is not None

    def _check_ruby_gem(self, gem: str) -> bool:
        result = subprocess.run(
            ["gem", "list", "-i", gem],
            capture_output=True
        )
        return result.returncode == 0

    def _check_php_package(self, package: str) -> bool:
        result = subprocess.run(
            ["composer", "show", package],
            capture_output=True
        )
        return result.returncode == 0

    def _check_npm_package(self, package: str) -> bool:
        result = subprocess.run(
            ["npm", "list", "-g", package],
            capture_output=True
        )
        return result.returncode == 0
```

---

## 7. CLI Integration

```bash
# Show available capabilities
rice-factor capabilities

# Output:
# Language    | move_file | rename | extract_if | enforce_dep | Adapter
# ------------|-----------|--------|------------|-------------|----------
# python      | ✓         | ✓      | ✓          | ✓           | rope
# java        | ✓         | ✓      | ✓          | ✓           | openrewrite
# kotlin      | ✓         | ✓      | ✓          | ✓           | openrewrite
# csharp      | ✓         | ✓      | ✓          | ✓           | roslyn
# javascript  | ✓         | ✓      | ✓          | ✓           | jscodeshift
# typescript  | ✓         | ✓      | ✓          | ✓           | jscodeshift
# go          | ✓         | ✓      | ✓          | ✓           | gopls
# rust        | ✓         | ✓      | ✓          | ✓           | rust-analyzer
# ruby        | ✓         | ✓      | ✓          | ✓           | parser
# php         | ✓         | ✓      | ✓          | ✓           | rector
```

---

## 8. Dependencies

### Python Packages
- `rope` - Python refactoring library

### External Tools
- OpenRewrite CLI or Gradle/Maven plugin
- .NET SDK with Roslynator
- Ruby with Parser gem
- PHP with Rector
- Node.js with jscodeshift
- gopls (Go language server)
- rust-analyzer

---

## 9. Testing Strategy

1. **Unit Tests**: Mock tool invocations, test adapter logic
2. **Integration Tests**: Sample projects per language
3. **Fallback Tests**: Verify DiffPatch fallback when tools unavailable
4. **Detection Tests**: Test capability detection across environments
