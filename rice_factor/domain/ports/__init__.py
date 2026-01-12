"""Port interfaces (hexagonal architecture boundaries)."""

from rice_factor.domain.ports.ast import (
    ASTPort,
    ImportInfo,
    ParameterInfo,
    ParseResult,
    SymbolInfo,
    SymbolKind,
    Visibility,
)
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
from rice_factor.domain.ports.lsp import (
    Location,
    LSPOperation,
    LSPPort,
    LSPResult,
    LSPServerConfig,
    LSPServerStatus,
    MemoryExceedAction,
    TextEdit,
)
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
    # AST parsing port
    "ASTPort",
    "ImportInfo",
    "ParameterInfo",
    "ParseResult",
    "SymbolInfo",
    "SymbolKind",
    "Visibility",
    # Config port
    "ConfigPort",
    # Coordinator port
    "CoordinationContext",
    "CoordinatorPort",
    # Coverage port
    "CoverageDriftResult",
    "CoverageError",
    "CoverageMonitorPort",
    "CoverageResult",
    # Executor port
    "ExecutorPort",
    # LLM port
    "LLMPort",
    # LSP port
    "Location",
    "LSPOperation",
    "LSPPort",
    "LSPResult",
    "LSPServerConfig",
    "LSPServerStatus",
    "MemoryExceedAction",
    "TextEdit",
    # Refactor port
    "RefactorChange",
    "RefactorOperation",
    "RefactorRequest",
    "RefactorResult",
    "RefactorToolPort",
    # Storage port
    "StoragePort",
    "ToolCapability",
    # Validation ports
    "ValidationRunnerPort",
    "ValidatorPort",
]
