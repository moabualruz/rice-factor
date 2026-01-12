"""Unit tests for ModelRegistry."""

from __future__ import annotations

import pytest

from rice_factor.domain.services.model_registry import (
    DEFAULT_MODELS,
    ModelCapability,
    ModelInfo,
    ModelRegistry,
    get_model_registry,
    reset_model_registry,
)


class TestModelCapability:
    """Tests for ModelCapability enum."""

    def test_code_value(self) -> None:
        """ModelCapability.CODE should have 'code' value."""
        assert ModelCapability.CODE.value == "code"

    def test_chat_value(self) -> None:
        """ModelCapability.CHAT should have 'chat' value."""
        assert ModelCapability.CHAT.value == "chat"

    def test_reasoning_value(self) -> None:
        """ModelCapability.REASONING should have 'reasoning' value."""
        assert ModelCapability.REASONING.value == "reasoning"

    def test_vision_value(self) -> None:
        """ModelCapability.VISION should have 'vision' value."""
        assert ModelCapability.VISION.value == "vision"


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_default_values(self) -> None:
        """ModelInfo should have sensible defaults."""
        model = ModelInfo(id="test", provider="test-provider")
        assert model.context_length == 8192
        assert model.capabilities == []
        assert model.cost_per_1k_input == 0.0
        assert model.is_local is False
        assert model.available is True

    def test_custom_values(self) -> None:
        """ModelInfo should accept custom values."""
        model = ModelInfo(
            id="custom",
            provider="ollama",
            context_length=32000,
            capabilities=[ModelCapability.CODE],
            strengths="Fast code completion",
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.002,
            size_gb=12.0,
            is_local=True,
            available=False,
        )
        assert model.id == "custom"
        assert model.context_length == 32000
        assert ModelCapability.CODE in model.capabilities
        assert model.size_gb == 12.0
        assert model.is_local is True
        assert model.available is False


class TestModelRegistryInit:
    """Tests for ModelRegistry initialization."""

    def test_loads_defaults_by_default(self) -> None:
        """ModelRegistry should load default models by default."""
        registry = ModelRegistry()
        assert len(registry.get_all()) > 0

    def test_can_skip_defaults(self) -> None:
        """ModelRegistry should allow skipping defaults."""
        registry = ModelRegistry(load_defaults=False)
        assert len(registry.get_all()) == 0

    def test_default_models_include_claude(self) -> None:
        """Default models should include Claude."""
        registry = ModelRegistry()
        claude_models = registry.get_by_provider("claude")
        assert len(claude_models) > 0

    def test_default_models_include_ollama(self) -> None:
        """Default models should include Ollama models."""
        registry = ModelRegistry()
        ollama_models = registry.get_by_provider("ollama")
        assert len(ollama_models) > 0


class TestModelRegistryRegister:
    """Tests for ModelRegistry.register."""

    def test_register_new_model(self) -> None:
        """register should add a new model to registry."""
        registry = ModelRegistry(load_defaults=False)
        model = ModelInfo(id="new-model", provider="test")

        registry.register(model)

        assert registry.get("new-model") is not None

    def test_register_overwrites_existing(self) -> None:
        """register should overwrite existing model."""
        registry = ModelRegistry(load_defaults=False)
        model1 = ModelInfo(id="model", provider="test", context_length=1000)
        model2 = ModelInfo(id="model", provider="test", context_length=2000)

        registry.register(model1)
        registry.register(model2)

        result = registry.get("model")
        assert result is not None
        assert result.context_length == 2000


class TestModelRegistryUnregister:
    """Tests for ModelRegistry.unregister."""

    def test_unregister_existing_model(self) -> None:
        """unregister should remove existing model."""
        registry = ModelRegistry(load_defaults=False)
        model = ModelInfo(id="model", provider="test")
        registry.register(model)

        result = registry.unregister("model")

        assert result is True
        assert registry.get("model") is None

    def test_unregister_nonexistent_model(self) -> None:
        """unregister should return False for nonexistent model."""
        registry = ModelRegistry(load_defaults=False)

        result = registry.unregister("nonexistent")

        assert result is False


class TestModelRegistryGet:
    """Tests for ModelRegistry.get."""

    def test_get_existing_model(self) -> None:
        """get should return existing model."""
        registry = ModelRegistry(load_defaults=False)
        model = ModelInfo(id="model", provider="test")
        registry.register(model)

        result = registry.get("model")

        assert result is not None
        assert result.id == "model"

    def test_get_nonexistent_model(self) -> None:
        """get should return None for nonexistent model."""
        registry = ModelRegistry(load_defaults=False)

        result = registry.get("nonexistent")

        assert result is None


class TestModelRegistryQueryMethods:
    """Tests for ModelRegistry query methods."""

    @pytest.fixture
    def registry_with_models(self) -> ModelRegistry:
        """Create registry with test models."""
        registry = ModelRegistry(load_defaults=False)
        registry.register(
            ModelInfo(
                id="cloud-1",
                provider="claude",
                capabilities=[ModelCapability.CODE, ModelCapability.CHAT],
                is_local=False,
                available=True,
                context_length=100000,
            )
        )
        registry.register(
            ModelInfo(
                id="cloud-2",
                provider="openai",
                capabilities=[ModelCapability.CODE],
                is_local=False,
                available=False,
                context_length=50000,
            )
        )
        registry.register(
            ModelInfo(
                id="local-1",
                provider="ollama",
                capabilities=[ModelCapability.CODE],
                is_local=True,
                available=True,
                context_length=32000,
            )
        )
        return registry

    def test_get_all(self, registry_with_models: ModelRegistry) -> None:
        """get_all should return all models."""
        models = registry_with_models.get_all()
        assert len(models) == 3

    def test_get_by_provider(self, registry_with_models: ModelRegistry) -> None:
        """get_by_provider should filter by provider."""
        claude_models = registry_with_models.get_by_provider("claude")
        assert len(claude_models) == 1
        assert claude_models[0].id == "cloud-1"

    def test_get_by_capability(self, registry_with_models: ModelRegistry) -> None:
        """get_by_capability should filter by capability."""
        code_models = registry_with_models.get_by_capability(ModelCapability.CODE)
        assert len(code_models) == 3

        chat_models = registry_with_models.get_by_capability(ModelCapability.CHAT)
        assert len(chat_models) == 1

    def test_get_local_models(self, registry_with_models: ModelRegistry) -> None:
        """get_local_models should return only local models."""
        local_models = registry_with_models.get_local_models()
        assert len(local_models) == 1
        assert local_models[0].is_local is True

    def test_get_cloud_models(self, registry_with_models: ModelRegistry) -> None:
        """get_cloud_models should return only cloud models."""
        cloud_models = registry_with_models.get_cloud_models()
        assert len(cloud_models) == 2
        assert all(not m.is_local for m in cloud_models)

    def test_get_available(self, registry_with_models: ModelRegistry) -> None:
        """get_available should return only available models."""
        available = registry_with_models.get_available()
        assert len(available) == 2
        assert all(m.available for m in available)

    def test_get_by_context_length(self, registry_with_models: ModelRegistry) -> None:
        """get_by_context_length should filter by minimum context."""
        large_context = registry_with_models.get_by_context_length(50000)
        assert len(large_context) == 2


class TestModelRegistryGetCheapest:
    """Tests for ModelRegistry.get_cheapest."""

    def test_get_cheapest_returns_free_model(self) -> None:
        """get_cheapest should prefer free models."""
        registry = ModelRegistry(load_defaults=False)
        registry.register(
            ModelInfo(
                id="expensive",
                provider="claude",
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.05,
            )
        )
        registry.register(
            ModelInfo(
                id="free",
                provider="ollama",
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
            )
        )

        cheapest = registry.get_cheapest()

        assert cheapest is not None
        assert cheapest.id == "free"

    def test_get_cheapest_with_capability_filter(self) -> None:
        """get_cheapest should filter by capability."""
        registry = ModelRegistry(load_defaults=False)
        registry.register(
            ModelInfo(
                id="code-model",
                provider="ollama",
                capabilities=[ModelCapability.CODE],
                cost_per_1k_input=0.0,
            )
        )
        registry.register(
            ModelInfo(
                id="chat-model",
                provider="claude",
                capabilities=[ModelCapability.CHAT],
                cost_per_1k_input=0.01,
            )
        )

        cheapest = registry.get_cheapest(ModelCapability.CHAT)

        assert cheapest is not None
        assert cheapest.id == "chat-model"

    def test_get_cheapest_returns_none_when_empty(self) -> None:
        """get_cheapest should return None when no models match."""
        registry = ModelRegistry(load_defaults=False)

        cheapest = registry.get_cheapest()

        assert cheapest is None


class TestModelRegistrySetAvailability:
    """Tests for ModelRegistry.set_availability."""

    def test_set_availability_updates_model(self) -> None:
        """set_availability should update model status."""
        registry = ModelRegistry(load_defaults=False)
        registry.register(ModelInfo(id="model", provider="test", available=True))

        result = registry.set_availability("model", False)

        assert result is True
        model = registry.get("model")
        assert model is not None
        assert model.available is False

    def test_set_availability_returns_false_for_unknown(self) -> None:
        """set_availability should return False for unknown model."""
        registry = ModelRegistry(load_defaults=False)

        result = registry.set_availability("unknown", True)

        assert result is False


class TestModelRegistrySyncWithProvider:
    """Tests for ModelRegistry.sync_with_provider."""

    def test_sync_marks_missing_models_unavailable(self) -> None:
        """sync_with_provider should mark missing models unavailable."""
        registry = ModelRegistry(load_defaults=False)
        registry.register(
            ModelInfo(id="model-1", provider="ollama", available=True)
        )
        registry.register(
            ModelInfo(id="model-2", provider="ollama", available=True)
        )

        registry.sync_with_provider("ollama", ["model-1"])

        assert registry.get("model-1").available is True  # type: ignore[union-attr]
        assert registry.get("model-2").available is False  # type: ignore[union-attr]

    def test_sync_adds_new_models(self) -> None:
        """sync_with_provider should add discovered models not in registry."""
        registry = ModelRegistry(load_defaults=False)

        registry.sync_with_provider("ollama", ["new-model"])

        model = registry.get("new-model")
        assert model is not None
        assert model.provider == "ollama"
        assert model.available is True


class TestModelRegistryToDict:
    """Tests for ModelRegistry.to_dict."""

    def test_to_dict_returns_all_models(self) -> None:
        """to_dict should return all models as dict."""
        registry = ModelRegistry(load_defaults=False)
        registry.register(
            ModelInfo(
                id="model",
                provider="test",
                context_length=8192,
                capabilities=[ModelCapability.CODE],
            )
        )

        result = registry.to_dict()

        assert "model" in result
        assert result["model"]["provider"] == "test"
        assert result["model"]["capabilities"] == ["code"]


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_get_model_registry_returns_same_instance(self) -> None:
        """get_model_registry should return same instance."""
        reset_model_registry()

        registry1 = get_model_registry()
        registry2 = get_model_registry()

        assert registry1 is registry2

    def test_reset_model_registry_clears_instance(self) -> None:
        """reset_model_registry should clear global instance."""
        registry1 = get_model_registry()

        reset_model_registry()

        registry2 = get_model_registry()
        assert registry1 is not registry2


class TestDefaultModels:
    """Tests for DEFAULT_MODELS configuration."""

    def test_default_models_has_entries(self) -> None:
        """DEFAULT_MODELS should have model definitions."""
        assert len(DEFAULT_MODELS) > 0

    def test_default_models_have_provider(self) -> None:
        """All default models should have provider."""
        for model_id, config in DEFAULT_MODELS.items():
            assert "provider" in config, f"{model_id} missing provider"

    def test_default_models_have_context_length(self) -> None:
        """All default models should have context_length."""
        for model_id, config in DEFAULT_MODELS.items():
            assert "context_length" in config, f"{model_id} missing context_length"
