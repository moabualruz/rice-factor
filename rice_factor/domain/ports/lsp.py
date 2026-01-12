"""LSP (Language Server Protocol) client port for language server operations.

This module defines the protocol for LSP client operations that require
semantic analysis beyond what AST parsing can provide (e.g., cross-file
rename, find references).

The LSP layer is used when:
- rename_symbol: Requires semantic understanding for cross-file renames
- move_file: Complex import updates across the project
- find_references: Find all usages of a symbol

Memory management is critical - LSP servers (especially rust-analyzer, gopls)
can consume significant memory. This port supports:
- One-shot mode: Start server, execute operation, kill server
- Memory limits: Configurable per-server with auto-kill on exceed
- Timeout handling: Configurable per-operation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LSPOperation(str, Enum):
    """LSP operations that can be performed."""

    RENAME = "textDocument/rename"
    REFERENCES = "textDocument/references"
    DEFINITION = "textDocument/definition"
    HOVER = "textDocument/hover"
    CODE_ACTION = "textDocument/codeAction"
    COMPLETION = "textDocument/completion"
    DOCUMENT_SYMBOL = "textDocument/documentSymbol"
    WORKSPACE_SYMBOL = "workspace/symbol"


class MemoryExceedAction(str, Enum):
    """Action to take when LSP server exceeds memory limit."""

    KILL = "kill"  # Immediately kill the server
    WARN = "warn"  # Log warning but continue


@dataclass
class TextEdit:
    """A text edit operation from LSP.

    Attributes:
        file_path: Absolute path to the file.
        start_line: Starting line (1-indexed).
        start_column: Starting column (0-indexed).
        end_line: Ending line (1-indexed).
        end_column: Ending column (0-indexed).
        new_text: Text to insert/replace.
    """

    file_path: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    new_text: str


@dataclass
class Location:
    """A location in a source file.

    Attributes:
        file_path: Absolute path to the file.
        start_line: Starting line number (0-indexed for LSP).
        start_column: Starting column number (0-indexed).
        end_line: Optional ending line.
        end_column: Optional ending column.
    """

    file_path: str
    start_line: int
    start_column: int
    end_line: int | None = None
    end_column: int | None = None


@dataclass
class LSPResult:
    """Result of an LSP operation.

    Attributes:
        success: Whether the operation succeeded.
        edits: List of text edits to apply.
        locations: List of locations (for references, definitions).
        errors: List of error messages.
        warnings: List of warning messages.
        server_used: Name of the LSP server used.
        memory_used_mb: Memory used by server at completion.
    """

    success: bool
    edits: list[TextEdit] = field(default_factory=list)
    locations: list[Location] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    server_used: str = ""
    memory_used_mb: float = 0.0


@dataclass
class LSPServerConfig:
    """Configuration for an LSP server.

    Attributes:
        name: Server name for logging/identification.
        command: Command to start the server (e.g., ["gopls", "serve"]).
        languages: List of language identifiers this server handles.
        memory_limit_mb: Maximum memory in MB before action is taken.
        on_memory_exceed: Action when memory limit is exceeded.
        timeout_seconds: Timeout for individual operations.
        initialization_timeout: Timeout for server initialization.
        install_hint: Command or instructions for installing the server.
        initialization_options: Options to send during server initialization.
        workspace_root: Root directory for the workspace.
        extra_args: Additional command line arguments.
        environment: Additional environment variables.
        settings: Server-specific settings (sent during initialization).
    """

    name: str
    command: list[str]
    languages: list[str]
    memory_limit_mb: int = 2048
    on_memory_exceed: MemoryExceedAction = MemoryExceedAction.KILL
    timeout_seconds: int = 60
    initialization_timeout: int = 30
    install_hint: str | None = None
    initialization_options: dict[str, Any] | None = None
    workspace_root: str = ""
    extra_args: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class LSPServerStatus:
    """Status of an LSP server.

    Attributes:
        name: Server name.
        is_running: Whether the server is currently running.
        pid: Process ID if running.
        memory_mb: Current memory usage in MB.
        uptime_seconds: Time since server started.
        last_operation: Last operation performed.
    """

    name: str
    is_running: bool = False
    pid: int | None = None
    memory_mb: float = 0.0
    uptime_seconds: float = 0.0
    last_operation: str | None = None


class LSPPort(ABC):
    """Port for LSP server operations.

    This abstract class defines the interface for LSP client adapters.
    Implementations handle server lifecycle, memory management, and
    LSP protocol communication.

    Key principles:
    1. One-shot mode by default (start → execute → kill)
    2. Memory monitoring with configurable limits
    3. Graceful shutdown with fallback to force kill
    4. Clear error messages when servers unavailable
    """

    @abstractmethod
    def rename(
        self,
        file_path: str,
        line: int,
        column: int,
        new_name: str,
    ) -> LSPResult:
        """Rename a symbol at the given position.

        This performs a semantic rename across all files that reference
        the symbol. Requires the LSP server to have full project context.

        Args:
            file_path: Absolute path to the file containing the symbol.
            line: Line number (1-indexed).
            column: Column number (0-indexed).
            new_name: New name for the symbol.

        Returns:
            LSPResult with text edits for all affected files.
        """
        ...

    @abstractmethod
    def find_references(
        self,
        file_path: str,
        line: int,
        column: int,
        include_declaration: bool = True,
    ) -> LSPResult:
        """Find all references to a symbol.

        Args:
            file_path: Absolute path to the file.
            line: Line number (1-indexed).
            column: Column number (0-indexed).
            include_declaration: Whether to include the declaration.

        Returns:
            LSPResult with locations of all references.
        """
        ...

    @abstractmethod
    def find_definition(
        self,
        file_path: str,
        line: int,
        column: int,
    ) -> LSPResult:
        """Find the definition of a symbol.

        Args:
            file_path: Absolute path to the file.
            line: Line number (1-indexed).
            column: Column number (0-indexed).

        Returns:
            LSPResult with location of the definition.
        """
        ...

    @abstractmethod
    def code_action(
        self,
        file_path: str,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
        action_kind: str | None = None,
    ) -> LSPResult:
        """Request code actions for a range.

        Code actions include refactorings like extract method,
        extract variable, etc.

        Args:
            file_path: Absolute path to the file.
            start_line: Starting line (1-indexed).
            start_column: Starting column (0-indexed).
            end_line: Ending line (1-indexed).
            end_column: Ending column (0-indexed).
            action_kind: Optional filter for action kind.

        Returns:
            LSPResult with available code actions.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LSP server is available.

        Checks if the server binary exists in PATH and can be executed.

        Returns:
            True if the server can be started.
        """
        ...

    @abstractmethod
    def start(self) -> bool:
        """Start the LSP server.

        Spawns the server process, performs initialization handshake,
        and starts memory monitoring.

        Returns:
            True if server started successfully.
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the LSP server.

        Performs graceful shutdown:
        1. Send shutdown request
        2. Send exit notification
        3. Wait for process (with timeout)
        4. Force kill if necessary
        """
        ...

    @abstractmethod
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage of the server process.

        Returns:
            Memory usage in megabytes, 0.0 if not running.
        """
        ...

    @abstractmethod
    def get_status(self) -> LSPServerStatus:
        """Get current status of the LSP server.

        Returns:
            LSPServerStatus with runtime information.
        """
        ...

    @abstractmethod
    def get_config(self) -> LSPServerConfig:
        """Get the configuration for this LSP client.

        Returns:
            LSPServerConfig with all settings.
        """
        ...

    def get_install_instructions(self) -> str:
        """Get installation instructions for the LSP server.

        Returns:
            Human-readable installation instructions.
        """
        config = self.get_config()
        server_name = config.name

        instructions: dict[str, str] = {
            "gopls": "go install golang.org/x/tools/gopls@latest",
            "rust-analyzer": "rustup component add rust-analyzer",
            "rust_analyzer": "rustup component add rust-analyzer",
            "typescript-language-server": "npm install -g typescript-language-server typescript",
            "tsserver": "npm install -g typescript-language-server typescript",
            "pylsp": "pip install python-lsp-server",
        }

        cmd = instructions.get(server_name, f"Install {server_name} for your system")
        return f"To install {server_name}:\n  {cmd}"
