"""Unit tests for LLM port protocol."""

from typing import Protocol, get_type_hints

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.ports.llm import LLMPort


class TestLLMPort:
    """Tests for LLMPort protocol definition."""

    def test_llm_port_is_protocol(self) -> None:
        """LLMPort should be a Protocol class."""
        assert issubclass(LLMPort, Protocol)

    def test_llm_port_has_generate_method(self) -> None:
        """LLMPort should define a generate method."""
        assert hasattr(LLMPort, "generate")

    def test_generate_method_signature(self) -> None:
        """Generate method should have correct parameter types."""
        hints = get_type_hints(LLMPort.generate)

        # Check parameter types
        assert hints.get("pass_type") == CompilerPassType
        assert hints.get("context") == CompilerContext
        assert hints.get("schema") == dict[str, object]

        # Check return type
        assert hints.get("return") == CompilerResult

    def test_protocol_cannot_be_instantiated_directly(self) -> None:
        """Protocol classes cannot be instantiated directly."""
        # This is just documenting behavior - Protocol classes
        # raise TypeError when instantiated without implementation
        with pytest.raises(TypeError):
            LLMPort()  # type: ignore

    def test_class_implementing_protocol(self) -> None:
        """A class implementing the protocol should be valid."""

        class MockLLMAdapter:
            """Mock implementation of LLMPort."""

            def generate(
                self,
                pass_type: CompilerPassType,
                context: CompilerContext,
                schema: dict,
            ) -> CompilerResult:
                return CompilerResult(success=True, payload={"test": "data"})

        # Should be able to instantiate implementing class
        adapter = MockLLMAdapter()
        assert adapter is not None

        # Should be able to call generate
        context = CompilerContext(pass_type=CompilerPassType.PROJECT)
        result = adapter.generate(CompilerPassType.PROJECT, context, {})
        assert result.success is True
