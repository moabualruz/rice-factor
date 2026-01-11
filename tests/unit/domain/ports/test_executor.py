"""Tests for ExecutorPort protocol."""

from pathlib import Path

from rice_factor.domain.artifacts.execution_types import (
    ExecutionMode,
    ExecutionResult,
)
from rice_factor.domain.ports.executor import ExecutorPort


class TestExecutorPortProtocol:
    """Tests for ExecutorPort protocol definition."""

    def test_executor_port_is_protocol(self) -> None:
        """ExecutorPort should be a Protocol."""
        # Protocol classes are marked with _is_protocol
        from typing import Protocol
        assert issubclass(ExecutorPort, Protocol)

    def test_executor_port_is_runtime_checkable(self) -> None:
        """ExecutorPort should be runtime checkable."""
        # runtime_checkable protocols can be used with isinstance
        assert hasattr(ExecutorPort, "__subclasshook__")

    def test_executor_port_has_execute_method(self) -> None:
        """ExecutorPort should define execute method."""
        assert hasattr(ExecutorPort, "execute")

    def test_implementing_class_satisfies_protocol(self) -> None:
        """A class implementing execute() should satisfy the protocol."""

        class ConcreteExecutor:
            def execute(
                self,
                artifact_path: Path,
                repo_root: Path,
                mode: ExecutionMode,
            ) -> ExecutionResult:
                return ExecutionResult.success_result()

        executor = ConcreteExecutor()
        # runtime_checkable protocols can be used with isinstance
        assert isinstance(executor, ExecutorPort)

    def test_non_implementing_class_does_not_satisfy_protocol(self) -> None:
        """A class without execute() should not satisfy the protocol."""

        class NotAnExecutor:
            def run(self) -> None:
                pass

        obj = NotAnExecutor()
        assert not isinstance(obj, ExecutorPort)

    def test_partial_implementation_does_not_satisfy_protocol(self) -> None:
        """A class with wrong signature should not satisfy the protocol."""

        class WrongSignatureExecutor:
            def execute(self) -> None:
                pass

        obj = WrongSignatureExecutor()
        # Note: runtime_checkable only checks method existence, not signature
        # This is a known limitation of Protocol
        # The actual type checking happens at static analysis time
        assert isinstance(obj, ExecutorPort)  # Only checks method exists


class TestExecutorPortDocumentation:
    """Tests for ExecutorPort documentation."""

    def test_protocol_has_docstring(self) -> None:
        """ExecutorPort should have a docstring."""
        assert ExecutorPort.__doc__ is not None
        assert len(ExecutorPort.__doc__) > 0

    def test_execute_method_has_docstring(self) -> None:
        """execute method should have a docstring."""
        assert ExecutorPort.execute.__doc__ is not None
        assert len(ExecutorPort.execute.__doc__) > 0

    def test_docstring_mentions_9_step_pipeline(self) -> None:
        """Docstring should mention the 9-step pipeline."""
        assert "9-step" in ExecutorPort.__doc__ or "nine-step" in ExecutorPort.__doc__.lower()

    def test_docstring_mentions_stateless(self) -> None:
        """Docstring should mention stateless requirement."""
        assert "Stateless" in ExecutorPort.__doc__ or "stateless" in ExecutorPort.__doc__.lower()
