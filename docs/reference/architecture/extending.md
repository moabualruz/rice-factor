# Extending Rice-Factor

This guide explains how to add new adapters and extend Rice-Factor's functionality.

## Adding a New LLM Provider

### Step 1: Implement LLMPort

Create a new adapter that implements the `LLMPort` protocol.

```python
# rice_factor/adapters/llm/my_provider.py
from rice_factor.domain.ports import LLMPort
from typing import TypeVar

T = TypeVar("T")

class MyProviderAdapter(LLMPort):
    """Adapter for MyProvider LLM API."""

    def __init__(
        self,
        api_key: str,
        model: str = "default-model",
        base_url: str = "https://api.myprovider.com",
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        # Initialize client

    def generate(
        self,
        prompt: str,
        schema: dict | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Generate text from prompt.

        Args:
            prompt: Input prompt
            schema: Optional JSON schema for structured output
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        # Implement API call
        response = self._client.generate(
            model=self._model,
            prompt=prompt,
            max_tokens=max_tokens,
        )
        return response.text

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        """Generate structured output.

        Args:
            prompt: Input prompt
            response_model: Pydantic model for response

        Returns:
            Parsed response as model instance
        """
        schema = response_model.model_json_schema()

        # Use provider's structured output feature if available
        # Otherwise, use prompt engineering
        schema_prompt = f"""
{prompt}

Respond with valid JSON matching this schema:
```json
{json.dumps(schema, indent=2)}
```
"""
        response = self.generate(schema_prompt)

        # Parse and validate
        try:
            data = json.loads(response)
            return response_model.model_validate(data)
        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON response: {e}")
```

### Step 2: Register in Container

Add the adapter to the dependency injection container.

```python
# rice_factor/config/container.py

from rice_factor.adapters.llm.my_provider import MyProviderAdapter

class Container:
    def get_llm(self) -> LLMPort:
        provider = self.settings.llm.provider

        adapters = {
            "claude": lambda: ClaudeAdapter(...),
            "openai": lambda: OpenAIAdapter(...),
            "ollama": lambda: OllamaAdapter(...),
            "myprovider": lambda: MyProviderAdapter(  # Add new provider
                api_key=self.settings.llm.api_key,
                model=self.settings.llm.model,
                base_url=self.settings.llm.base_url,
            ),
        }

        return adapters[provider]()
```

### Step 3: Add Configuration

Update the settings schema.

```python
# rice_factor/config/settings.py

class LLMSettings(BaseSettings):
    provider: Literal["claude", "openai", "ollama", "myprovider"] = "claude"
    api_key: str = ""
    model: str = ""
    base_url: str = ""
```

### Step 4: Add Tests

Write tests for the adapter.

```python
# tests/adapters/llm/test_my_provider.py
import pytest
from rice_factor.adapters.llm.my_provider import MyProviderAdapter

class TestMyProviderAdapter:
    def test_generate_returns_text(self, mock_api):
        adapter = MyProviderAdapter(api_key="test-key")
        result = adapter.generate("Test prompt")
        assert isinstance(result, str)

    def test_generate_structured_returns_model(self, mock_api):
        adapter = MyProviderAdapter(api_key="test-key")
        result = adapter.generate_structured(
            "Generate a plan",
            ProjectPlanPayload,
        )
        assert isinstance(result, ProjectPlanPayload)

@pytest.mark.integration
class TestMyProviderIntegration:
    def test_real_api_call(self):
        adapter = MyProviderAdapter(
            api_key=os.environ["MYPROVIDER_API_KEY"]
        )
        result = adapter.generate("Hello, world!")
        assert len(result) > 0
```

---

## Adding a New Storage Backend

### Step 1: Implement StoragePort

```python
# rice_factor/adapters/storage/redis_storage.py
import redis
import json
from rice_factor.domain.ports import StoragePort
from rice_factor.domain.artifacts import ArtifactEnvelope

class RedisStorageAdapter(StoragePort):
    """Adapter for Redis storage."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        prefix: str = "rice-factor:",
    ):
        self._client = redis.Redis(host=host, port=port)
        self._prefix = prefix

    def save(self, artifact: ArtifactEnvelope) -> None:
        """Save artifact to Redis."""
        key = f"{self._prefix}{artifact.artifact_type}:{artifact.id}"
        self._client.set(key, artifact.model_dump_json())

    def load(self, artifact_id: str) -> ArtifactEnvelope:
        """Load artifact from Redis."""
        # Search across all types
        for key in self._client.scan_iter(f"{self._prefix}*:{artifact_id}"):
            data = self._client.get(key)
            if data:
                return ArtifactEnvelope.model_validate_json(data)

        raise ArtifactNotFoundError(f"Artifact {artifact_id} not found")

    def delete(self, artifact_id: str) -> None:
        """Delete artifact from Redis."""
        for key in self._client.scan_iter(f"{self._prefix}*:{artifact_id}"):
            self._client.delete(key)
            return

        raise ArtifactNotFoundError(f"Artifact {artifact_id} not found")

    def list_by_type(self, artifact_type: str) -> list[ArtifactEnvelope]:
        """List artifacts by type."""
        artifacts = []
        pattern = f"{self._prefix}{artifact_type}:*"

        for key in self._client.scan_iter(pattern):
            data = self._client.get(key)
            if data:
                artifacts.append(ArtifactEnvelope.model_validate_json(data))

        return artifacts

    def list_all(self) -> list[ArtifactEnvelope]:
        """List all artifacts."""
        artifacts = []
        for key in self._client.scan_iter(f"{self._prefix}*"):
            data = self._client.get(key)
            if data:
                artifacts.append(ArtifactEnvelope.model_validate_json(data))
        return artifacts
```

### Step 2: Register and Configure

```python
# rice_factor/config/container.py

class Container:
    def get_storage(self) -> StoragePort:
        backend = self.settings.storage.backend

        if backend == "filesystem":
            return FilesystemStorageAdapter(self.settings.project_path)
        elif backend == "s3":
            return S3StorageAdapter(
                bucket=self.settings.storage.s3_bucket,
                prefix=self.settings.storage.s3_prefix,
            )
        elif backend == "redis":
            return RedisStorageAdapter(
                host=self.settings.storage.redis_host,
                port=self.settings.storage.redis_port,
            )
```

---

## Adding a New Executor

### Step 1: Implement ExecutorPort

```python
# rice_factor/adapters/executors/docker_executor.py
import docker
from rice_factor.domain.ports import ExecutorPort

class DockerExecutor(ExecutorPort):
    """Executor that runs tests in Docker containers."""

    def __init__(self, image: str = "python:3.11"):
        self._client = docker.from_env()
        self._image = image

    def execute(self, artifact: ArtifactEnvelope) -> ExecutionResult:
        """Execute tests in Docker container."""
        container = self._client.containers.run(
            self._image,
            command="pytest -v",
            volumes={
                str(self._project_root): {
                    "bind": "/app",
                    "mode": "ro"
                }
            },
            working_dir="/app",
            detach=True,
        )

        result = container.wait()
        logs = container.logs().decode()
        container.remove()

        return ExecutionResult(
            success=result["StatusCode"] == 0,
            output=logs,
            errors=[] if result["StatusCode"] == 0 else [logs],
        )

    def dry_run(self, artifact: ArtifactEnvelope) -> DryRunResult:
        """Preview Docker execution."""
        return DryRunResult(
            would_run=[
                f"docker run {self._image} pytest -v"
            ],
        )
```

---

## Adding a New Validator

### Step 1: Implement ValidatorPort

```python
# rice_factor/adapters/validators/mypy_validator.py
import subprocess
from pathlib import Path
from rice_factor.domain.ports import ValidatorPort

class MypyValidator(ValidatorPort):
    """Validator using mypy for type checking."""

    def __init__(self, project_root: Path):
        self._project_root = Path(project_root)

    def validate(self, paths: list[str] | None = None) -> ValidationResult:
        """Run mypy type checking."""
        cmd = ["mypy", "--strict"]

        if paths:
            cmd.extend(paths)
        else:
            cmd.append(".")

        result = subprocess.run(
            cmd,
            cwd=self._project_root,
            capture_output=True,
            text=True,
        )

        errors = []
        if result.returncode != 0:
            # Parse mypy output
            for line in result.stdout.splitlines():
                if ": error:" in line:
                    errors.append(line)

        return ValidationResult(
            valid=result.returncode == 0,
            output=result.stdout,
            errors=errors,
        )
```

---

## Adding a New Refactoring Adapter

### Step 1: Implement RefactoringAdapter

```python
# rice_factor/adapters/refactoring/rust_analyzer.py
import subprocess
import json
from pathlib import Path

class RustAnalyzerAdapter:
    """Refactoring adapter using rust-analyzer."""

    def __init__(self, project_root: Path):
        self._project_root = Path(project_root)

    def rename_symbol(
        self,
        symbol: str,
        new_name: str,
        file_path: str | None = None,
    ) -> RefactoringResult:
        """Rename a symbol using rust-analyzer."""
        # Use rust-analyzer LSP protocol
        result = subprocess.run(
            [
                "rust-analyzer",
                "rename",
                symbol,
                new_name,
            ],
            cwd=self._project_root,
            capture_output=True,
            text=True,
        )

        return RefactoringResult(
            success=result.returncode == 0,
            changes=self._parse_changes(result.stdout),
            errors=[result.stderr] if result.returncode != 0 else [],
        )

    def extract_function(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        function_name: str,
    ) -> RefactoringResult:
        """Extract code to a new function."""
        # Use rust-analyzer's extract function command
        pass

    def move_item(
        self,
        from_path: str,
        to_path: str,
        item_name: str,
    ) -> RefactoringResult:
        """Move item between modules."""
        pass
```

### Step 2: Register Language Support

```python
# rice_factor/adapters/refactoring/__init__.py

LANGUAGE_ADAPTERS = {
    "python": PythonRefactoringAdapter,
    "javascript": JSCodeshiftAdapter,
    "typescript": JSCodeshiftAdapter,
    "go": GoplsAdapter,
    "rust": RustAnalyzerAdapter,
    "java": OpenRewriteAdapter,
}

def get_refactoring_adapter(language: str, project_root: Path):
    """Get refactoring adapter for language."""
    adapter_class = LANGUAGE_ADAPTERS.get(language)
    if not adapter_class:
        raise ValueError(f"No refactoring adapter for {language}")
    return adapter_class(project_root)
```

---

## Adding a New CLI Command

### Step 1: Create Command Module

```python
# rice_factor/entrypoints/cli/commands/mycommand.py
import typer
from rice_factor.config.container import Container

app = typer.Typer(help="My custom command")

@app.command()
def run(
    option: str = typer.Option(
        "default",
        "--option", "-o",
        help="Command option"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Verbose output"
    ),
):
    """Run my custom command."""
    container = Container()

    # Use services
    artifact_service = container.get_artifact_service()

    # Do something
    if verbose:
        typer.echo("Running with verbose output...")

    typer.echo(f"Command completed with option: {option}")
```

### Step 2: Register Command

```python
# rice_factor/entrypoints/cli/main.py
from rice_factor.entrypoints.cli.commands import mycommand

app = typer.Typer(
    name="rice-factor",
    help="LLM-assisted development system",
)

# Register command
app.add_typer(mycommand.app, name="mycommand")
```

---

## Adding a New Artifact Type

### Step 1: Define Payload Model

```python
# rice_factor/domain/artifacts/payloads.py

class MyArtifactPayload(BaseModel):
    """Payload for MyArtifact type."""

    name: str = Field(..., description="Artifact name")
    items: list[str] = Field(min_length=1, description="List of items")
    metadata: dict = Field(default_factory=dict)
```

### Step 2: Add to ArtifactType Enum

```python
# rice_factor/domain/artifacts/enums.py

class ArtifactType(str, Enum):
    # ... existing types
    MY_ARTIFACT = "MyArtifact"
```

### Step 3: Create JSON Schema

```json
// schemas/my_artifact.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "artifact_type": {
      "const": "MyArtifact"
    },
    "payload": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "items": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1
        },
        "metadata": { "type": "object" }
      },
      "required": ["name", "items"]
    }
  },
  "required": ["artifact_type", "payload"]
}
```

### Step 4: Add Storage Mapping

```python
# rice_factor/adapters/storage/filesystem.py

TYPE_DIRECTORIES = {
    # ... existing mappings
    "MyArtifact": "my_artifacts",
}
```

---

## Best Practices

### 1. Follow Port Contracts

Always implement the full protocol interface:

```python
class MyAdapter(SomePort):
    # Implement ALL methods from the port
    def method_one(self, arg: str) -> Result:
        ...

    def method_two(self, arg: int) -> Result:
        ...
```

### 2. Handle Errors Gracefully

Use domain exceptions:

```python
from rice_factor.domain.exceptions import (
    ArtifactNotFoundError,
    ArtifactValidationError,
)

def load(self, artifact_id: str) -> ArtifactEnvelope:
    try:
        # Load logic
        pass
    except KeyError:
        raise ArtifactNotFoundError(f"Artifact {artifact_id} not found")
```

### 3. Add Configuration Options

Make adapters configurable:

```python
class MyAdapter:
    def __init__(
        self,
        option_a: str = "default_a",
        option_b: int = 100,
        # Allow overrides
    ):
        self._option_a = option_a
        self._option_b = option_b
```

### 4. Write Comprehensive Tests

Test both unit and integration:

```python
# Unit tests (mocked)
class TestMyAdapterUnit:
    def test_method_returns_expected(self, mock_dependency):
        adapter = MyAdapter()
        result = adapter.method()
        assert result == expected

# Integration tests (real services)
@pytest.mark.integration
class TestMyAdapterIntegration:
    def test_real_service_call(self):
        adapter = MyAdapter(api_key=os.environ["API_KEY"])
        result = adapter.method()
        assert result is not None
```

### 5. Document Your Extension

Add docstrings and update docs:

```python
class MyAdapter(SomePort):
    """Adapter for MyService integration.

    This adapter connects Rice-Factor to MyService for XYZ functionality.

    Configuration:
        Set MYSERVICE_API_KEY environment variable or configure in
        .rice-factor.yaml under myservice.api_key.

    Example:
        ```python
        adapter = MyAdapter(api_key="...")
        result = adapter.do_something()
        ```

    See Also:
        - MyService docs: https://myservice.com/docs
        - Rice-Factor adapters: docs/reference/architecture/adapters.md
    """
```

---

## See Also

- [Architecture Overview](overview.md) - Hexagonal architecture
- [Domain Layer](domain.md) - Port definitions
- [Adapters](adapters.md) - Existing adapters
- [CLI Reference](../cli/commands.md) - CLI structure
