"""Port interfaces (hexagonal architecture boundaries)."""

from rice_factor.domain.ports.config import ConfigPort
from rice_factor.domain.ports.coordinator import (
    CoordinationContext,
    CoordinatorPort,
)
from rice_factor.domain.ports.coverage import (
    CoverageDriftResult,
    CoverageError,
    CoverageMonitorPort,
    CoverageResult,
)
from rice_factor.domain.ports.executor import ExecutorPort
from rice_factor.domain.ports.llm import LLMPort
from rice_factor.domain.ports.refactor import (
    RefactorChange,
    RefactorOperation,
    RefactorRequest,
    RefactorResult,
    RefactorToolPort,
    ToolCapability,
)
from rice_factor.domain.ports.storage import StoragePort
from rice_factor.domain.ports.validation_runner import ValidationRunnerPort
from rice_factor.domain.ports.validator import ValidatorPort

__all__ = [
    "ConfigPort",
    "CoordinationContext",
    "CoordinatorPort",
    "CoverageDriftResult",
    "CoverageError",
    "CoverageMonitorPort",
    "CoverageResult",
    "ExecutorPort",
    "LLMPort",
    "RefactorChange",
    "RefactorOperation",
    "RefactorRequest",
    "RefactorResult",
    "RefactorToolPort",
    "StoragePort",
    "ToolCapability",
    "ValidationRunnerPort",
    "ValidatorPort",
]
