"""Model registry for LLM model metadata and capabilities.

This module provides the ModelRegistry service that maintains information
about available LLM models across different providers, including their
capabilities, context lengths, and cost information.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class ModelCapability(Enum):
    """Capabilities that a model may support."""

    CODE = "code"  # Code generation and completion
    CHAT = "chat"  # Conversational chat
    REASONING = "reasoning"  # Complex reasoning tasks
    VISION = "vision"  # Image understanding
    FUNCTION_CALLING = "function_calling"  # Tool/function calling
    JSON_MODE = "json_mode"  # Structured JSON output


@dataclass
class ModelInfo:
    """Information about a single LLM model.

    Attributes:
        id: Unique model identifier (e.g., "claude-sonnet-4-20250514").
        provider: Provider name (e.g., "claude", "ollama").
        context_length: Maximum context length in tokens.
        capabilities: List of supported capabilities.
        strengths: Human-readable description of model strengths.
        cost_per_1k_input: Cost in USD per 1000 input tokens (0 for local).
        cost_per_1k_output: Cost in USD per 1000 output tokens (0 for local).
        size_gb: Model size in GB (for local models).
        is_local: Whether this is a local model.
        available: Whether this model is currently available.
    """

    id: str
    provider: str
    context_length: int = 8192
    capabilities: list[ModelCapability] = field(default_factory=list)
    strengths: str = ""
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    size_gb: float | None = None
    is_local: bool = False
    available: bool = True


# Default model configurations
DEFAULT_MODELS: dict[str, dict[str, Any]] = {
    # Cloud Models
    "claude-sonnet-4-20250514": {
        "provider": "claude",
        "context_length": 200000,
        "capabilities": [
            ModelCapability.CODE,
            ModelCapability.CHAT,
            ModelCapability.REASONING,
            ModelCapability.VISION,
            ModelCapability.JSON_MODE,
        ],
        "strengths": "Best for complex code generation and reasoning",
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
    },
    "claude-opus-4-20250514": {
        "provider": "claude",
        "context_length": 200000,
        "capabilities": [
            ModelCapability.CODE,
            ModelCapability.CHAT,
            ModelCapability.REASONING,
            ModelCapability.VISION,
            ModelCapability.JSON_MODE,
        ],
        "strengths": "Most capable model for complex tasks",
        "cost_per_1k_input": 0.015,
        "cost_per_1k_output": 0.075,
    },
    "gpt-4o": {
        "provider": "openai",
        "context_length": 128000,
        "capabilities": [
            ModelCapability.CODE,
            ModelCapability.CHAT,
            ModelCapability.REASONING,
            ModelCapability.VISION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.JSON_MODE,
        ],
        "strengths": "Fast, multimodal, excellent tool use",
        "cost_per_1k_input": 0.005,
        "cost_per_1k_output": 0.015,
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "context_length": 128000,
        "capabilities": [
            ModelCapability.CODE,
            ModelCapability.CHAT,
            ModelCapability.REASONING,
            ModelCapability.VISION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.JSON_MODE,
        ],
        "strengths": "High accuracy, large context",
        "cost_per_1k_input": 0.01,
        "cost_per_1k_output": 0.03,
    },
    # Local Models
    "codestral": {
        "provider": "ollama",
        "context_length": 32000,
        "capabilities": [ModelCapability.CODE],
        "strengths": "Fast code completion, Mistral quality",
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
        "size_gb": 12.0,
        "is_local": True,
    },
    "qwen2.5-coder": {
        "provider": "ollama",
        "context_length": 32768,
        "capabilities": [ModelCapability.CODE, ModelCapability.REASONING],
        "strengths": "Multi-language support, reasoning chains",
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
        "size_gb": 7.0,
        "is_local": True,
    },
    "deepseek-coder-v2": {
        "provider": "ollama",
        "context_length": 128000,
        "capabilities": [ModelCapability.CODE],
        "strengths": "Best open-source code completion accuracy",
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
        "size_gb": 16.0,
        "is_local": True,
    },
    "llama3.2": {
        "provider": "ollama",
        "context_length": 8192,
        "capabilities": [ModelCapability.CHAT, ModelCapability.REASONING],
        "strengths": "General purpose, efficient",
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
        "size_gb": 4.0,
        "is_local": True,
    },
}


class ModelRegistry:
    """Registry service for LLM model metadata.

    The registry maintains information about available models,
    their capabilities, and allows querying by various criteria.

    Example:
        >>> registry = ModelRegistry()
        >>> registry.register(ModelInfo(id="custom-model", provider="ollama"))
        >>> models = registry.get_by_capability(ModelCapability.CODE)
        >>> model = registry.get("claude-sonnet-4-20250514")
    """

    def __init__(self, load_defaults: bool = True) -> None:
        """Initialize the model registry.

        Args:
            load_defaults: Whether to load default model configurations.
        """
        self._models: dict[str, ModelInfo] = {}

        if load_defaults:
            self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default model configurations."""
        for model_id, config in DEFAULT_MODELS.items():
            self.register(
                ModelInfo(
                    id=model_id,
                    provider=config["provider"],
                    context_length=config.get("context_length", 8192),
                    capabilities=config.get("capabilities", []),
                    strengths=config.get("strengths", ""),
                    cost_per_1k_input=config.get("cost_per_1k_input", 0.0),
                    cost_per_1k_output=config.get("cost_per_1k_output", 0.0),
                    size_gb=config.get("size_gb"),
                    is_local=config.get("is_local", False),
                )
            )

    def register(self, model: ModelInfo) -> None:
        """Register a model in the registry.

        Args:
            model: ModelInfo to register.
        """
        self._models[model.id] = model

    def unregister(self, model_id: str) -> bool:
        """Remove a model from the registry.

        Args:
            model_id: ID of the model to remove.

        Returns:
            True if model was found and removed.
        """
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False

    def get(self, model_id: str) -> ModelInfo | None:
        """Get a model by ID.

        Args:
            model_id: Unique model identifier.

        Returns:
            ModelInfo if found, None otherwise.
        """
        return self._models.get(model_id)

    def get_all(self) -> list[ModelInfo]:
        """Get all registered models.

        Returns:
            List of all ModelInfo objects.
        """
        return list(self._models.values())

    def get_by_provider(self, provider: str) -> list[ModelInfo]:
        """Get all models for a specific provider.

        Args:
            provider: Provider name (e.g., "claude", "ollama").

        Returns:
            List of models for the provider.
        """
        return [m for m in self._models.values() if m.provider == provider]

    def get_by_capability(self, capability: ModelCapability) -> list[ModelInfo]:
        """Get all models with a specific capability.

        Args:
            capability: The required capability.

        Returns:
            List of models with the capability.
        """
        return [m for m in self._models.values() if capability in m.capabilities]

    def get_local_models(self) -> list[ModelInfo]:
        """Get all local models.

        Returns:
            List of local models.
        """
        return [m for m in self._models.values() if m.is_local]

    def get_cloud_models(self) -> list[ModelInfo]:
        """Get all cloud-hosted models.

        Returns:
            List of cloud models.
        """
        return [m for m in self._models.values() if not m.is_local]

    def get_available(self) -> list[ModelInfo]:
        """Get all available models.

        Returns:
            List of models marked as available.
        """
        return [m for m in self._models.values() if m.available]

    def get_by_context_length(self, min_length: int) -> list[ModelInfo]:
        """Get models with at least the specified context length.

        Args:
            min_length: Minimum context length in tokens.

        Returns:
            List of models meeting the requirement.
        """
        return [m for m in self._models.values() if m.context_length >= min_length]

    def get_cheapest(
        self, capability: ModelCapability | None = None
    ) -> ModelInfo | None:
        """Get the cheapest model, optionally filtered by capability.

        Args:
            capability: Optional capability filter.

        Returns:
            Cheapest model, or None if no models available.
        """
        candidates = self.get_all()
        if capability:
            candidates = [m for m in candidates if capability in m.capabilities]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda m: m.cost_per_1k_input + m.cost_per_1k_output,
        )

    def set_availability(self, model_id: str, available: bool) -> bool:
        """Update the availability status of a model.

        Args:
            model_id: Model identifier.
            available: New availability status.

        Returns:
            True if model was found and updated.
        """
        model = self._models.get(model_id)
        if model:
            model.available = available
            return True
        return False

    def sync_with_provider(
        self,
        provider: str,
        discovered_models: list[str],
    ) -> None:
        """Sync registry with discovered models from a provider.

        Updates availability based on what models the provider reports.

        Args:
            provider: Provider name.
            discovered_models: List of model IDs discovered from provider.
        """
        for model in self.get_by_provider(provider):
            model.available = model.id in discovered_models

        # Add any new models not in registry as available
        for model_id in discovered_models:
            if model_id not in self._models:
                # Register as generic model with unknown capabilities
                self.register(
                    ModelInfo(
                        id=model_id,
                        provider=provider,
                        is_local=provider in ("ollama", "vllm", "openai_compat"),
                        available=True,
                    )
                )

    def load_from_yaml(self, path: Path) -> int:
        """Load model configurations from a YAML file.

        Args:
            path: Path to YAML configuration file.

        Returns:
            Number of models loaded.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If YAML is invalid.
        """
        try:
            import yaml
        except ImportError as e:
            raise ImportError("PyYAML required. Install with: pip install pyyaml") from e

        if not path.exists():
            raise FileNotFoundError(f"Model registry file not found: {path}")

        with path.open() as f:
            data = yaml.safe_load(f)

        if not data or "models" not in data:
            raise ValueError("Invalid model registry YAML: missing 'models' key")

        count = 0
        for model_id, config in data["models"].items():
            # Parse capabilities from strings
            capabilities = []
            for cap_str in config.get("capabilities", []):
                with contextlib.suppress(ValueError):
                    capabilities.append(ModelCapability(cap_str))

            self.register(
                ModelInfo(
                    id=model_id,
                    provider=config.get("provider", "unknown"),
                    context_length=config.get("context_length", 8192),
                    capabilities=capabilities,
                    strengths=config.get("strengths", ""),
                    cost_per_1k_input=config.get("cost_per_1k_input", 0.0),
                    cost_per_1k_output=config.get("cost_per_1k_output", 0.0),
                    size_gb=config.get("size_gb"),
                    is_local=config.get("is_local", False),
                )
            )
            count += 1

        return count

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Export registry as a dictionary.

        Returns:
            Dictionary representation of all models.
        """
        result: dict[str, dict[str, Any]] = {}
        for model_id, model in self._models.items():
            result[model_id] = {
                "provider": model.provider,
                "context_length": model.context_length,
                "capabilities": [c.value for c in model.capabilities],
                "strengths": model.strengths,
                "cost_per_1k_input": model.cost_per_1k_input,
                "cost_per_1k_output": model.cost_per_1k_output,
                "is_local": model.is_local,
                "available": model.available,
            }
            if model.size_gb:
                result[model_id]["size_gb"] = model.size_gb
        return result


# Global registry instance
_registry: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    """Get the global model registry instance.

    Returns:
        The global ModelRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def reset_model_registry() -> None:
    """Reset the global model registry (useful for testing)."""
    global _registry
    _registry = None
