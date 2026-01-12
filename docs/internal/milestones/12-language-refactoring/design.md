# Milestone 12: Language-Specific Refactoring - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

### 1.1 Architecture Approach

Language-specific refactoring extends the RefactorExecutor with pluggable adapters for each language ecosystem.

```
┌─────────────────────────────────────────────────────────────┐
│                     RefactorPlan                             │
│  { operation: "rename", target: "UserService", ... }        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   RefactorExecutor                           │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              CapabilityRegistry                          ││
│  │  Detects: languages, tools, operations                   ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│          ┌──────────┬────────┼────────┬──────────┐          │
│          ▼          ▼        ▼        ▼          ▼          │
│  ┌───────────┐┌──────────┐┌──────┐┌───────┐┌─────────┐      │
│  │OpenRewrite││  gopls   ││rust- ││jscode-││ Diff/   │      │
│  │ Adapter   ││ Adapter  ││analyz││shift  ││ Patch   │      │
│  └───────────┘└──────────┘└──────┘└───────┘└─────────┘      │
│       │            │          │        │         │          │
└───────┼────────────┼──────────┼────────┼─────────┼──────────┘
        │            │          │        │         │
        ▼            ▼          ▼        ▼         ▼
   ┌─────────┐  ┌─────────┐ ┌──────┐ ┌──────┐ ┌──────────┐
   │ Maven/  │  │  gopls  │ │cargo │ │ npm  │ │   git    │
   │ Gradle  │  │  (LSP)  │ │      │ │      │ │diff/apply│
   └─────────┘  └─────────┘ └──────┘ └──────┘ └──────────┘
```

### 1.2 File Organization

```
rice_factor/
├── domain/
│   ├── ports/
│   │   └── refactor.py                # RefactorToolPort
│   └── services/
│       └── refactor_executor.py       # Updated with tool routing
├── adapters/
│   └── refactoring/
│       ├── capability_registry.py     # Tool detection
│       ├── openrewrite_adapter.py     # JVM refactoring
│       ├── gopls_adapter.py           # Go refactoring
│       ├── rust_analyzer_adapter.py   # Rust refactoring
│       ├── jscodeshift_adapter.py     # JS/TS refactoring
│       └── diff_patch_adapter.py      # Fallback
└── config/
    └── refactoring_config.py          # Tool paths, preferences
```

---

## 2. Domain Models

### 2.1 Refactoring Port

```python
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass


class RefactorOperation(str, Enum):
    """Supported refactoring operations."""

    RENAME = "rename"
    EXTRACT_METHOD = "extract_method"
    EXTRACT_VARIABLE = "extract_variable"
    INLINE = "inline"
    MOVE = "move"
    CHANGE_SIGNATURE = "change_signature"
    ADD_PARAMETER = "add_parameter"
    REMOVE_PARAMETER = "remove_parameter"


@dataclass
class RefactorRequest:
    """Request for a refactoring operation."""

    operation: RefactorOperation
    target: str                    # Symbol/file to refactor
    new_value: str | None = None   # New name, etc.
    parameters: dict | None = None # Operation-specific params


@dataclass
class RefactorChange:
    """A single change resulting from refactoring."""

    file_path: str
    original_content: str
    new_content: str
    description: str


@dataclass
class RefactorResult:
    """Result of a refactoring operation."""

    success: bool
    changes: list[RefactorChange]
    errors: list[str]
    tool_used: str
    dry_run: bool


class RefactorToolPort(ABC):
    """Port for language-specific refactoring tools."""

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """Return list of supported language identifiers."""
        ...

    @abstractmethod
    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return list of supported operations."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the tool is installed and usable."""
        ...

    @abstractmethod
    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute a refactoring operation."""
        ...

    @abstractmethod
    def rollback(self, result: RefactorResult) -> bool:
        """Rollback a previously applied refactoring."""
        ...
```

### 2.2 Capability Registry

```python
@dataclass
class ToolCapability:
    """Capability of a single tool."""

    tool_name: str
    languages: list[str]
    operations: list[RefactorOperation]
    is_available: bool
    version: str | None = None


class CapabilityRegistry:
    """Registry of available refactoring tools."""

    def __init__(self, tools: list[RefactorToolPort]) -> None:
        self.tools = tools
        self._capabilities: dict[str, ToolCapability] = {}
        self._refresh()

    def _refresh(self) -> None:
        """Refresh tool availability."""
        for tool in self.tools:
            cap = ToolCapability(
                tool_name=tool.__class__.__name__,
                languages=tool.get_supported_languages(),
                operations=tool.get_supported_operations(),
                is_available=tool.is_available(),
            )
            for lang in cap.languages:
                if cap.is_available:
                    self._capabilities[lang] = cap

    def get_tool_for_language(
        self,
        language: str,
    ) -> RefactorToolPort | None:
        """Get the best tool for a language."""
        for tool in self.tools:
            if language in tool.get_supported_languages():
                if tool.is_available():
                    return tool
        return None

    def get_all_capabilities(self) -> list[ToolCapability]:
        """Get capabilities of all registered tools."""
        return list(self._capabilities.values())

    def supports_operation(
        self,
        language: str,
        operation: RefactorOperation,
    ) -> bool:
        """Check if an operation is supported for a language."""
        tool = self.get_tool_for_language(language)
        if tool is None:
            return False
        return operation in tool.get_supported_operations()
```

---

## 3. OpenRewrite Adapter

### 3.1 Implementation

```python
import subprocess
import tempfile
from pathlib import Path


class OpenRewriteAdapter(RefactorToolPort):
    """Adapter for OpenRewrite (JVM refactoring)."""

    LANGUAGES = ["java", "kotlin", "groovy"]

    OPERATIONS = [
        RefactorOperation.RENAME,
        RefactorOperation.EXTRACT_METHOD,
        RefactorOperation.INLINE,
        RefactorOperation.MOVE,
        RefactorOperation.CHANGE_SIGNATURE,
    ]

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def get_supported_languages(self) -> list[str]:
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if Maven/Gradle with OpenRewrite is available."""
        # Check for pom.xml with OpenRewrite plugin
        pom = self.project_root / "pom.xml"
        if pom.exists():
            content = pom.read_text()
            return "openrewrite" in content.lower()

        # Check for build.gradle with OpenRewrite
        gradle = self.project_root / "build.gradle"
        if gradle.exists():
            content = gradle.read_text()
            return "openrewrite" in content.lower()

        return False

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring via OpenRewrite recipes."""
        recipe = self._get_recipe(request)

        cmd = self._build_command(recipe, dry_run)

        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[result.stderr],
                tool_used="OpenRewrite",
                dry_run=dry_run,
            )

        changes = self._parse_changes(result.stdout)

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="OpenRewrite",
            dry_run=dry_run,
        )

    def _get_recipe(self, request: RefactorRequest) -> str:
        """Map operation to OpenRewrite recipe."""
        recipes = {
            RefactorOperation.RENAME: "org.openrewrite.java.ChangeType",
            RefactorOperation.MOVE: "org.openrewrite.java.ChangePackage",
        }
        return recipes.get(request.operation, "")

    def _build_command(self, recipe: str, dry_run: bool) -> list[str]:
        """Build Maven/Gradle command for recipe execution."""
        # Maven example
        cmd = [
            "mvn",
            "rewrite:run",
            f"-Drewrite.activeRecipes={recipe}",
        ]
        if dry_run:
            cmd.append("-Drewrite.dryRun=true")
        return cmd

    def rollback(self, result: RefactorResult) -> bool:
        """Rollback using git."""
        subprocess.run(["git", "checkout", "."], cwd=self.project_root)
        return True
```

---

## 4. gopls Adapter

### 4.1 Implementation

```python
import json
import subprocess


class GoplsAdapter(RefactorToolPort):
    """Adapter for gopls (Go Language Server)."""

    LANGUAGES = ["go"]

    OPERATIONS = [
        RefactorOperation.RENAME,
        RefactorOperation.EXTRACT_METHOD,
        RefactorOperation.INLINE,
    ]

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def get_supported_languages(self) -> list[str]:
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if gopls is installed."""
        result = subprocess.run(
            ["gopls", "version"],
            capture_output=True,
        )
        return result.returncode == 0

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring via gopls."""
        if request.operation == RefactorOperation.RENAME:
            return self._rename(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_METHOD:
            return self._extract(request, dry_run)

        return RefactorResult(
            success=False,
            changes=[],
            errors=["Operation not supported"],
            tool_used="gopls",
            dry_run=dry_run,
        )

    def _rename(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Perform rename refactoring."""
        # gopls uses LSP protocol
        # Use gorename for simpler CLI interface
        cmd = [
            "gorename",
            "-from", request.target,
            "-to", request.new_value,
        ]

        if dry_run:
            cmd.append("-d")  # dry-run flag

        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[result.stderr],
                tool_used="gopls/gorename",
                dry_run=dry_run,
            )

        changes = self._parse_diff(result.stdout)

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="gopls/gorename",
            dry_run=dry_run,
        )

    def rollback(self, result: RefactorResult) -> bool:
        subprocess.run(["git", "checkout", "."], cwd=self.project_root)
        return True
```

---

## 5. rust-analyzer Adapter

### 5.1 Implementation

```python
class RustAnalyzerAdapter(RefactorToolPort):
    """Adapter for rust-analyzer."""

    LANGUAGES = ["rust"]

    OPERATIONS = [
        RefactorOperation.RENAME,
        RefactorOperation.EXTRACT_METHOD,
        RefactorOperation.INLINE,
    ]

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def get_supported_languages(self) -> list[str]:
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if rust-analyzer is installed."""
        result = subprocess.run(
            ["rust-analyzer", "--version"],
            capture_output=True,
        )
        return result.returncode == 0

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring via rust-analyzer LSP."""
        # rust-analyzer works via LSP
        # Use ra_ap_rust_analyzer crate for CLI if available

        # For rename, we can use LSP textDocument/rename
        if request.operation == RefactorOperation.RENAME:
            return self._lsp_rename(request, dry_run)

        return RefactorResult(
            success=False,
            changes=[],
            errors=["Operation requires LSP client"],
            tool_used="rust-analyzer",
            dry_run=dry_run,
        )

    def _lsp_rename(
        self,
        request: RefactorRequest,
        dry_run: bool,
    ) -> RefactorResult:
        """Perform rename via LSP protocol."""
        # Implementation would use LSP client
        # This is a simplified placeholder
        ...

    def rollback(self, result: RefactorResult) -> bool:
        subprocess.run(["git", "checkout", "."], cwd=self.project_root)
        return True
```

---

## 6. jscodeshift Adapter

### 6.1 Implementation

```python
class JscodeshiftAdapter(RefactorToolPort):
    """Adapter for jscodeshift (JavaScript/TypeScript)."""

    LANGUAGES = ["javascript", "typescript", "jsx", "tsx"]

    OPERATIONS = [
        RefactorOperation.RENAME,
        RefactorOperation.EXTRACT_METHOD,
        RefactorOperation.MOVE,
    ]

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.transforms_dir = Path(__file__).parent / "transforms"

    def get_supported_languages(self) -> list[str]:
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if jscodeshift is installed."""
        result = subprocess.run(
            ["npx", "jscodeshift", "--version"],
            capture_output=True,
        )
        return result.returncode == 0

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute transform via jscodeshift."""
        transform = self._get_transform(request)

        cmd = [
            "npx", "jscodeshift",
            "-t", str(transform),
            "--parser", "tsx",
        ]

        if dry_run:
            cmd.append("--dry")

        # Add target files
        cmd.extend(self._get_target_files(request))

        # Add transform options
        for key, value in (request.parameters or {}).items():
            cmd.extend([f"--{key}", str(value)])

        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[result.stderr],
                tool_used="jscodeshift",
                dry_run=dry_run,
            )

        changes = self._parse_output(result.stdout)

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="jscodeshift",
            dry_run=dry_run,
        )

    def _get_transform(self, request: RefactorRequest) -> Path:
        """Get transform file for operation."""
        transforms = {
            RefactorOperation.RENAME: "rename-symbol.js",
            RefactorOperation.EXTRACT_METHOD: "extract-method.js",
        }
        return self.transforms_dir / transforms.get(
            request.operation, "noop.js"
        )

    def rollback(self, result: RefactorResult) -> bool:
        subprocess.run(["git", "checkout", "."], cwd=self.project_root)
        return True
```

---

## 7. RefactorExecutor Integration

### 7.1 Updated Executor

```python
class RefactorExecutor:
    """Executor that routes to language-specific tools."""

    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        diff_patch_adapter: DiffPatchAdapter,
    ) -> None:
        self.registry = capability_registry
        self.fallback = diff_patch_adapter

    def execute(
        self,
        plan: RefactorPlan,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring plan using appropriate tool."""
        language = self._detect_language(plan)
        tool = self.registry.get_tool_for_language(language)

        if tool is None:
            # Fallback to diff/patch
            return self.fallback.execute(plan, dry_run)

        request = self._plan_to_request(plan)
        return tool.execute(request, dry_run)

    def _detect_language(self, plan: RefactorPlan) -> str:
        """Detect language from plan target files."""
        target = plan.payload.get("target_file", "")
        extension = Path(target).suffix

        extensions = {
            ".java": "java",
            ".kt": "kotlin",
            ".go": "go",
            ".rs": "rust",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".py": "python",
        }

        return extensions.get(extension, "unknown")

    def _plan_to_request(self, plan: RefactorPlan) -> RefactorRequest:
        """Convert RefactorPlan to RefactorRequest."""
        return RefactorRequest(
            operation=RefactorOperation(plan.payload["operation"]),
            target=plan.payload["target"],
            new_value=plan.payload.get("new_value"),
            parameters=plan.payload.get("parameters"),
        )
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial design |
