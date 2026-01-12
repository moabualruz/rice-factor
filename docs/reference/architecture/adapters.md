# Adapters

Adapters implement domain ports with concrete external integrations.

## Overview

```
rice_factor/adapters/
├── llm/                 # LLM provider adapters
│   ├── claude.py        # Anthropic Claude
│   ├── openai.py        # OpenAI GPT
│   ├── ollama.py        # Ollama (local)
│   └── vllm.py          # vLLM (local)
├── storage/             # Storage adapters
│   ├── filesystem.py    # Local filesystem
│   └── s3.py            # AWS S3
├── executors/           # Execution adapters
│   ├── scaffold.py      # File scaffolding
│   ├── diff.py          # Diff generation/apply
│   └── refactor.py      # Refactoring operations
└── validators/          # Validation adapters
    ├── schema.py        # JSON Schema validation
    ├── test_runner.py   # Test execution
    └── lint.py          # Code linting
```

---

## LLM Adapters

### ClaudeAdapter

Implements `LLMPort` for Anthropic Claude.

```python
# rice_factor/adapters/llm/claude.py
from anthropic import Anthropic
from rice_factor.domain.ports import LLMPort

class ClaudeAdapter(LLMPort):
    """Adapter for Anthropic Claude API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
    ):
        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def generate(
        self,
        prompt: str,
        schema: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate text using Claude.

        Args:
            prompt: Input prompt
            schema: Optional JSON schema for structured output
            max_tokens: Override default max tokens

        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]

        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens or self._max_tokens,
            messages=messages,
        )

        return response.content[0].text

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        """Generate structured output using Claude.

        Uses tool_use for reliable JSON extraction.

        Args:
            prompt: Input prompt
            response_model: Pydantic model for response

        Returns:
            Parsed response
        """
        schema = response_model.model_json_schema()

        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
            tools=[{
                "name": "structured_output",
                "description": "Output structured data",
                "input_schema": schema,
            }],
            tool_choice={"type": "tool", "name": "structured_output"},
        )

        tool_use = next(
            block for block in response.content
            if block.type == "tool_use"
        )

        return response_model.model_validate(tool_use.input)
```

**Configuration:**

```yaml
# .rice-factor.yaml
llm:
  provider: claude
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
```

### OpenAIAdapter

Implements `LLMPort` for OpenAI GPT.

```python
# rice_factor/adapters/llm/openai.py
from openai import OpenAI
from rice_factor.domain.ports import LLMPort

class OpenAIAdapter(LLMPort):
    """Adapter for OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo",
        max_tokens: int = 4096,
    ):
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def generate(
        self,
        prompt: str,
        schema: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate text using GPT."""
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens or self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        """Generate structured output using GPT.

        Uses function calling for reliable JSON extraction.
        """
        schema = response_model.model_json_schema()

        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
            functions=[{
                "name": "structured_output",
                "parameters": schema,
            }],
            function_call={"name": "structured_output"},
        )

        args = response.choices[0].message.function_call.arguments
        return response_model.model_validate_json(args)
```

### OllamaAdapter

Implements `LLMPort` for local Ollama models.

```python
# rice_factor/adapters/llm/ollama.py
import httpx
from rice_factor.domain.ports import LLMPort

class OllamaAdapter(LLMPort):
    """Adapter for Ollama local models."""

    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434",
    ):
        self._model = model
        self._base_url = base_url
        self._client = httpx.Client(base_url=base_url)

    def generate(
        self,
        prompt: str,
        schema: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate text using Ollama."""
        response = self._client.post(
            "/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["response"]

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        """Generate structured output.

        Note: Ollama structured output depends on model support.
        Falls back to prompt engineering if needed.
        """
        schema_prompt = f"""
{prompt}

Respond with valid JSON matching this schema:
{response_model.model_json_schema()}
"""
        response = self.generate(schema_prompt)
        return response_model.model_validate_json(response)
```

### vLLMAdapter

Implements `LLMPort` for vLLM server.

```python
# rice_factor/adapters/llm/vllm.py
import httpx
from rice_factor.domain.ports import LLMPort

class VLLMAdapter(LLMPort):
    """Adapter for vLLM inference server."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:8000",
    ):
        self._model = model
        self._base_url = base_url
        self._client = httpx.Client(base_url=base_url)

    def generate(
        self,
        prompt: str,
        schema: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate text using vLLM."""
        response = self._client.post(
            "/v1/completions",
            json={
                "model": self._model,
                "prompt": prompt,
                "max_tokens": max_tokens or 4096,
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["text"]
```

---

## Storage Adapters

### FilesystemStorageAdapter

Implements `StoragePort` for local filesystem.

```python
# rice_factor/adapters/storage/filesystem.py
import json
from pathlib import Path
from rice_factor.domain.ports import StoragePort
from rice_factor.domain.artifacts import ArtifactEnvelope

class FilesystemStorageAdapter(StoragePort):
    """Adapter for local filesystem storage."""

    def __init__(self, base_path: Path):
        self._base_path = Path(base_path)
        self._artifacts_path = self._base_path / ".project" / "artifacts"

    def save(self, artifact: ArtifactEnvelope) -> None:
        """Save artifact to filesystem."""
        type_dir = self._get_type_dir(artifact.artifact_type)
        type_dir.mkdir(parents=True, exist_ok=True)

        file_path = type_dir / f"{artifact.id}.json"
        file_path.write_text(
            artifact.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def load(self, artifact_id: str) -> ArtifactEnvelope:
        """Load artifact from filesystem."""
        for type_dir in self._artifacts_path.iterdir():
            if type_dir.is_dir():
                file_path = type_dir / f"{artifact_id}.json"
                if file_path.exists():
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    return ArtifactEnvelope.model_validate(data)

        raise ArtifactNotFoundError(f"Artifact {artifact_id} not found")

    def delete(self, artifact_id: str) -> None:
        """Delete artifact from filesystem."""
        for type_dir in self._artifacts_path.iterdir():
            if type_dir.is_dir():
                file_path = type_dir / f"{artifact_id}.json"
                if file_path.exists():
                    file_path.unlink()
                    return

        raise ArtifactNotFoundError(f"Artifact {artifact_id} not found")

    def list_by_type(self, artifact_type: str) -> list[ArtifactEnvelope]:
        """List artifacts by type."""
        type_dir = self._get_type_dir(artifact_type)
        if not type_dir.exists():
            return []

        artifacts = []
        for file_path in type_dir.glob("*.json"):
            data = json.loads(file_path.read_text(encoding="utf-8"))
            artifacts.append(ArtifactEnvelope.model_validate(data))

        return artifacts

    def list_all(self) -> list[ArtifactEnvelope]:
        """List all artifacts."""
        artifacts = []
        for type_dir in self._artifacts_path.iterdir():
            if type_dir.is_dir():
                for file_path in type_dir.glob("*.json"):
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    artifacts.append(ArtifactEnvelope.model_validate(data))
        return artifacts

    def _get_type_dir(self, artifact_type: str) -> Path:
        """Get directory for artifact type."""
        type_map = {
            "ProjectPlan": "project_plans",
            "ArchitecturePlan": "architecture_plans",
            "ScaffoldPlan": "scaffold_plans",
            "TestPlan": "test_plans",
            "ImplementationPlan": "implementation_plans",
            "RefactorPlan": "refactor_plans",
            "ValidationResult": "validation_results",
            "FailureReport": "failure_reports",
            "ReconciliationPlan": "reconciliation_plans",
        }
        return self._artifacts_path / type_map.get(artifact_type, "other")
```

### S3StorageAdapter

Implements `StoragePort` for AWS S3.

```python
# rice_factor/adapters/storage/s3.py
import json
import boto3
from rice_factor.domain.ports import StoragePort

class S3StorageAdapter(StoragePort):
    """Adapter for AWS S3 storage."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "artifacts/",
        region: str = "us-east-1",
    ):
        self._bucket = bucket
        self._prefix = prefix
        self._client = boto3.client("s3", region_name=region)

    def save(self, artifact: ArtifactEnvelope) -> None:
        """Save artifact to S3."""
        key = f"{self._prefix}{artifact.artifact_type}/{artifact.id}.json"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=artifact.model_dump_json(indent=2),
            ContentType="application/json",
        )

    def load(self, artifact_id: str) -> ArtifactEnvelope:
        """Load artifact from S3."""
        # Search across type prefixes
        paginator = self._client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self._bucket, Prefix=self._prefix):
            for obj in page.get("Contents", []):
                if artifact_id in obj["Key"]:
                    response = self._client.get_object(
                        Bucket=self._bucket,
                        Key=obj["Key"],
                    )
                    data = json.loads(response["Body"].read())
                    return ArtifactEnvelope.model_validate(data)

        raise ArtifactNotFoundError(f"Artifact {artifact_id} not found")
```

---

## Executor Adapters

### ScaffoldExecutor

Implements `ExecutorPort` for file scaffolding.

```python
# rice_factor/adapters/executors/scaffold.py
from pathlib import Path
from rice_factor.domain.ports import ExecutorPort

class ScaffoldExecutor(ExecutorPort):
    """Executor for ScaffoldPlan artifacts."""

    def __init__(self, project_root: Path):
        self._project_root = Path(project_root)

    def execute(self, artifact: ArtifactEnvelope) -> ExecutionResult:
        """Execute scaffold plan - create empty files."""
        if artifact.artifact_type != ArtifactType.SCAFFOLD_PLAN:
            raise ValueError("Expected ScaffoldPlan artifact")

        created_files = []
        errors = []

        for file_entry in artifact.payload["files"]:
            file_path = self._project_root / file_entry["path"]

            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)

                if not file_path.exists():
                    # Create with TODO comment
                    content = self._generate_stub(file_entry)
                    file_path.write_text(content, encoding="utf-8")
                    created_files.append(str(file_path))

            except Exception as e:
                errors.append(f"Failed to create {file_path}: {e}")

        return ExecutionResult(
            success=len(errors) == 0,
            created_files=created_files,
            errors=errors,
        )

    def dry_run(self, artifact: ArtifactEnvelope) -> DryRunResult:
        """Preview scaffold execution."""
        would_create = []
        would_skip = []

        for file_entry in artifact.payload["files"]:
            file_path = self._project_root / file_entry["path"]
            if file_path.exists():
                would_skip.append(str(file_path))
            else:
                would_create.append(str(file_path))

        return DryRunResult(
            would_create=would_create,
            would_skip=would_skip,
        )

    def _generate_stub(self, file_entry: dict) -> str:
        """Generate stub content for file."""
        kind = file_entry.get("kind", "SOURCE")
        description = file_entry.get("description", "")

        if file_entry["path"].endswith(".py"):
            return f'"""TODO: {description}"""\n'
        elif file_entry["path"].endswith((".ts", ".js")):
            return f"// TODO: {description}\n"
        else:
            return f"# TODO: {description}\n"
```

### DiffExecutor

Implements `ExecutorPort` for diff application.

```python
# rice_factor/adapters/executors/diff.py
import subprocess
from pathlib import Path
from rice_factor.domain.ports import ExecutorPort

class DiffExecutor(ExecutorPort):
    """Executor for applying diffs."""

    def __init__(self, project_root: Path, audit_path: Path):
        self._project_root = Path(project_root)
        self._audit_path = Path(audit_path)

    def execute(self, artifact: ArtifactEnvelope) -> ExecutionResult:
        """Apply diff from ImplementationPlan."""
        diff_file = self._audit_path / "diffs" / f"{artifact.id}.diff"

        if not diff_file.exists():
            return ExecutionResult(
                success=False,
                errors=["Diff file not found"],
            )

        result = subprocess.run(
            ["git", "apply", "--check", str(diff_file)],
            cwd=self._project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return ExecutionResult(
                success=False,
                errors=[f"Diff check failed: {result.stderr}"],
            )

        # Apply the diff
        result = subprocess.run(
            ["git", "apply", str(diff_file)],
            cwd=self._project_root,
            capture_output=True,
            text=True,
        )

        return ExecutionResult(
            success=result.returncode == 0,
            errors=[result.stderr] if result.returncode != 0 else [],
        )

    def dry_run(self, artifact: ArtifactEnvelope) -> DryRunResult:
        """Preview diff application."""
        diff_file = self._audit_path / "diffs" / f"{artifact.id}.diff"

        if not diff_file.exists():
            return DryRunResult(errors=["Diff file not found"])

        diff_content = diff_file.read_text(encoding="utf-8")
        return DryRunResult(
            diff_preview=diff_content,
            affected_files=self._extract_files_from_diff(diff_content),
        )

    def rollback(self, execution_id: str) -> None:
        """Rollback diff application."""
        diff_file = self._audit_path / "diffs" / f"{execution_id}.diff"

        result = subprocess.run(
            ["git", "apply", "--reverse", str(diff_file)],
            cwd=self._project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RollbackError(f"Rollback failed: {result.stderr}")
```

### RefactorExecutor

Implements `ExecutorPort` for refactoring operations.

```python
# rice_factor/adapters/executors/refactor.py
from rice_factor.domain.ports import ExecutorPort
from rice_factor.adapters.refactoring import (
    OpenRewriteAdapter,
    TreeSitterAdapter,
)

class RefactorExecutor(ExecutorPort):
    """Executor for RefactorPlan artifacts."""

    def __init__(
        self,
        project_root: Path,
        language_adapters: dict[str, RefactoringAdapter],
    ):
        self._project_root = project_root
        self._adapters = language_adapters

    def execute(self, artifact: ArtifactEnvelope) -> ExecutionResult:
        """Execute refactoring operations."""
        results = []
        errors = []

        for operation in artifact.payload["operations"]:
            op_type = operation["type"]

            try:
                if op_type == "MOVE_FILE":
                    self._move_file(
                        operation["from_path"],
                        operation["to_path"],
                    )
                elif op_type == "RENAME_SYMBOL":
                    self._rename_symbol(
                        operation["symbol"],
                        operation["new_name"],
                    )
                elif op_type == "EXTRACT_INTERFACE":
                    self._extract_interface(
                        operation["symbol"],
                        operation["interface_name"],
                    )
                results.append(f"Completed: {op_type}")

            except Exception as e:
                errors.append(f"Failed {op_type}: {e}")

        return ExecutionResult(
            success=len(errors) == 0,
            results=results,
            errors=errors,
        )

    def _rename_symbol(self, symbol: str, new_name: str) -> None:
        """Rename symbol across codebase."""
        # Use appropriate language adapter
        for adapter in self._adapters.values():
            adapter.rename_symbol(symbol, new_name)
```

---

## Validator Adapters

### SchemaValidator

Implements `ValidatorPort` for JSON Schema validation.

```python
# rice_factor/adapters/validators/schema.py
import jsonschema
from pathlib import Path
from rice_factor.domain.ports import ValidatorPort

class SchemaValidator(ValidatorPort):
    """Validator for JSON Schema compliance."""

    def __init__(self, schemas_path: Path):
        self._schemas_path = Path(schemas_path)
        self._schemas: dict[str, dict] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all schemas from disk."""
        for schema_file in self._schemas_path.glob("*.schema.json"):
            schema = json.loads(schema_file.read_text())
            self._schemas[schema_file.stem] = schema

    def validate_schema(self, artifact: ArtifactEnvelope) -> ValidationResult:
        """Validate artifact against JSON schema."""
        schema_name = f"{artifact.artifact_type.lower()}.schema"
        schema = self._schemas.get(schema_name)

        if not schema:
            return ValidationResult(
                valid=False,
                errors=[f"No schema found for {artifact.artifact_type}"],
            )

        try:
            jsonschema.validate(
                artifact.model_dump(),
                schema,
            )
            return ValidationResult(valid=True)

        except jsonschema.ValidationError as e:
            return ValidationResult(
                valid=False,
                errors=[e.message],
            )
```

### TestRunner

Implements `ValidatorPort` for test execution.

```python
# rice_factor/adapters/validators/test_runner.py
import subprocess
from pathlib import Path
from rice_factor.domain.ports import ValidatorPort

class TestRunner(ValidatorPort):
    """Validator that runs test suites."""

    def __init__(self, project_root: Path):
        self._project_root = Path(project_root)

    def run_tests(self, test_path: str | None = None) -> ValidationResult:
        """Run tests and return results."""
        cmd = ["pytest", "-v", "--tb=short"]
        if test_path:
            cmd.append(test_path)

        result = subprocess.run(
            cmd,
            cwd=self._project_root,
            capture_output=True,
            text=True,
        )

        return ValidationResult(
            valid=result.returncode == 0,
            output=result.stdout,
            errors=[result.stderr] if result.returncode != 0 else [],
        )
```

---

## Adapter Selection

The container selects adapters based on configuration:

```python
# rice_factor/config/container.py

class Container:
    def get_llm(self) -> LLMPort:
        provider = self.settings.llm.provider

        adapters = {
            "claude": lambda: ClaudeAdapter(
                api_key=self.settings.llm.api_key,
                model=self.settings.llm.model,
            ),
            "openai": lambda: OpenAIAdapter(
                api_key=self.settings.llm.api_key,
                model=self.settings.llm.model,
            ),
            "ollama": lambda: OllamaAdapter(
                model=self.settings.llm.model,
                base_url=self.settings.llm.base_url,
            ),
            "vllm": lambda: VLLMAdapter(
                model=self.settings.llm.model,
                base_url=self.settings.llm.base_url,
            ),
        }

        if provider not in adapters:
            raise ValueError(f"Unknown LLM provider: {provider}")

        return adapters[provider]()
```

---

## See Also

- [Architecture Overview](overview.md) - Hexagonal architecture
- [Domain Layer](domain.md) - Port definitions
- [Extending Rice-Factor](extending.md) - Adding adapters
- [Configuration](../configuration/settings.md) - Adapter configuration
