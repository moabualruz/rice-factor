"""LSP client for language server operations.

Provides a one-shot LSP client that starts a language server,
executes operations, and shuts down. Includes memory management
and timeout handling.
"""

import contextlib
import json
import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from rice_factor.adapters.lsp.memory_manager import MemoryManager, MemoryStatus
from rice_factor.domain.ports.lsp import (
    Location,
    LSPPort,
    LSPResult,
    LSPServerConfig,
    MemoryExceedAction,
    TextEdit,
)

logger = logging.getLogger(__name__)


class LSPClient(LSPPort):
    """One-shot LSP client with memory management.

    Starts a language server process, executes the requested
    operation, and shuts down. Memory usage is monitored and
    the server is killed if limits are exceeded.

    Attributes:
        config: Server configuration.
        project_root: Root directory of the project.
    """

    def __init__(
        self,
        config: LSPServerConfig,
        project_root: Path,
    ) -> None:
        """Initialize the LSP client.

        Args:
            config: Server configuration including command, limits, etc.
            project_root: Root directory of the project being analyzed.
        """
        self.config = config
        self.project_root = project_root

        self._process: subprocess.Popen[bytes] | None = None
        self._memory_manager: MemoryManager | None = None
        self._request_id = 0
        self._responses: dict[int, Any] = {}
        self._response_lock = threading.Lock()
        self._reader_thread: threading.Thread | None = None
        self._running = False
        self._memory_exceeded = False

    def start(self) -> bool:
        """Start the LSP server process.

        Returns:
            True if server started successfully.
        """
        if self._process is not None:
            logger.warning("LSP server already running")
            return True

        try:
            # Start the server process
            self._process = subprocess.Popen(
                self.config.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root),
            )

            self._running = True
            self._memory_exceeded = False

            # Start memory monitoring
            self._memory_manager = MemoryManager(
                limit_mb=self.config.memory_limit_mb,
                check_interval=5.0,
                on_exceed=self._on_memory_exceed,
            )
            self._memory_manager.start_monitoring(self._process)

            # Start response reader thread
            self._reader_thread = threading.Thread(
                target=self._read_responses,
                daemon=True,
                name=f"lsp-reader-{self.config.name}",
            )
            self._reader_thread.start()

            # Initialize the server
            if not self._initialize():
                self.stop()
                return False

            logger.info(f"LSP server '{self.config.name}' started (PID {self._process.pid})")
            return True

        except FileNotFoundError:
            logger.error(
                f"LSP server command not found: {self.config.command[0]}. "
                f"Install with: {self.config.install_hint or 'see documentation'}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to start LSP server: {e}")
            self.stop()
            return False

    def stop(self) -> None:
        """Stop the LSP server process."""
        self._running = False

        if self._process:
            try:
                # Send shutdown request
                self._send_request("shutdown", {})

                # Send exit notification
                self._send_notification("exit", {})

                # Wait briefly for graceful shutdown
                with contextlib.suppress(subprocess.TimeoutExpired):
                    self._process.wait(timeout=3.0)

            except Exception:
                pass  # Best effort shutdown

            # Force kill if still running
            if self._memory_manager:
                self._memory_manager.terminate_gracefully()
                self._memory_manager = None

            self._process = None

        # Wait for reader thread
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1.0)

        self._reader_thread = None
        self._responses.clear()

        logger.info(f"LSP server '{self.config.name}' stopped")

    def _on_memory_exceed(self, status: MemoryStatus) -> None:
        """Handle memory limit exceeded event.

        Args:
            status: Current memory status.
        """
        self._memory_exceeded = True

        if self.config.on_memory_exceed == MemoryExceedAction.KILL:
            logger.warning(
                f"Killing LSP server '{self.config.name}' due to memory limit "
                f"({status.memory_mb:.0f}MB > {status.limit_mb:.0f}MB)"
            )
            if self._memory_manager:
                self._memory_manager.kill_process()
        else:
            logger.warning(
                f"LSP server '{self.config.name}' exceeded memory limit "
                f"({status.memory_mb:.0f}MB > {status.limit_mb:.0f}MB) - continuing"
            )

    def _initialize(self) -> bool:
        """Send LSP initialize request.

        Returns:
            True if initialization succeeded.
        """
        params = {
            "processId": None,
            "rootUri": self.project_root.as_uri(),
            "rootPath": str(self.project_root),
            "capabilities": {
                "textDocument": {
                    "rename": {"prepareSupport": True},
                    "references": {},
                    "definition": {},
                    "hover": {},
                },
                "workspace": {
                    "applyEdit": True,
                    "workspaceEdit": {"documentChanges": True},
                },
            },
            "initializationOptions": self.config.initialization_options or {},
        }

        result = self._send_request(
            "initialize",
            params,
            timeout=self.config.initialization_timeout,
        )

        if result is None:
            logger.error("LSP initialization failed - no response")
            return False

        # Send initialized notification
        self._send_notification("initialized", {})

        logger.debug(f"LSP server initialized: {result.get('serverInfo', {})}")
        return True

    def _send_request(
        self,
        method: str,
        params: dict[str, Any],
        timeout: float | None = None,
    ) -> Any | None:
        """Send an LSP request and wait for response.

        Args:
            method: LSP method name.
            params: Request parameters.
            timeout: Optional timeout in seconds.

        Returns:
            Response result or None on error/timeout.
        """
        if not self._process or not self._process.stdin:
            return None

        self._request_id += 1
        request_id = self._request_id

        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        try:
            content = json.dumps(message)
            header = f"Content-Length: {len(content)}\r\n\r\n"
            self._process.stdin.write((header + content).encode("utf-8"))
            self._process.stdin.flush()

            logger.debug(f"LSP request [{request_id}]: {method}")

        except Exception as e:
            logger.error(f"Failed to send LSP request: {e}")
            return None

        # Wait for response
        timeout = timeout or self.config.timeout_seconds
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._memory_exceeded:
                logger.error("LSP request aborted - memory limit exceeded")
                return None

            with self._response_lock:
                if request_id in self._responses:
                    response = self._responses.pop(request_id)
                    if "error" in response:
                        logger.error(f"LSP error: {response['error']}")
                        return None
                    return response.get("result")

            time.sleep(0.05)

        logger.warning(f"LSP request [{request_id}] timed out after {timeout}s")
        return None

    def _send_notification(self, method: str, params: dict[str, Any]) -> None:
        """Send an LSP notification (no response expected).

        Args:
            method: LSP method name.
            params: Notification parameters.
        """
        if not self._process or not self._process.stdin:
            return

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        try:
            content = json.dumps(message)
            header = f"Content-Length: {len(content)}\r\n\r\n"
            self._process.stdin.write((header + content).encode("utf-8"))
            self._process.stdin.flush()
        except Exception as e:
            logger.debug(f"Failed to send notification: {e}")

    def _read_responses(self) -> None:
        """Background thread to read LSP responses."""
        if not self._process or not self._process.stdout:
            return

        buffer = b""

        while self._running and self._process.poll() is None:
            try:
                # Read available data
                data = self._process.stdout.read(4096)
                if not data:
                    break
                buffer += data

                # Parse messages from buffer
                while True:
                    # Look for Content-Length header
                    header_end = buffer.find(b"\r\n\r\n")
                    if header_end == -1:
                        break

                    header = buffer[:header_end].decode("utf-8")
                    content_length = None

                    for line in header.split("\r\n"):
                        if line.lower().startswith("content-length:"):
                            content_length = int(line.split(":")[1].strip())
                            break

                    if content_length is None:
                        logger.warning("Missing Content-Length header")
                        buffer = buffer[header_end + 4 :]
                        continue

                    content_start = header_end + 4
                    content_end = content_start + content_length

                    if len(buffer) < content_end:
                        break  # Need more data

                    content = buffer[content_start:content_end]
                    buffer = buffer[content_end:]

                    try:
                        message = json.loads(content.decode("utf-8"))

                        if "id" in message:
                            with self._response_lock:
                                self._responses[message["id"]] = message

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse LSP message: {e}")

            except Exception as e:
                if self._running:
                    logger.debug(f"Error reading LSP response: {e}")
                break

    def rename(
        self,
        file_path: str,
        line: int,
        column: int,
        new_name: str,
    ) -> LSPResult:
        """Rename a symbol across the project.

        Args:
            file_path: Path to the file containing the symbol.
            line: Line number (0-indexed).
            column: Column number (0-indexed).
            new_name: New name for the symbol.

        Returns:
            LSPResult with text edits.
        """
        if not self._process:
            return LSPResult(
                success=False,
                edits=[],
                locations=[],
                errors=[f"LSP server '{self.config.name}' not running"],
                memory_used_mb=0,
            )

        # Open the file in the server
        file_uri = Path(file_path).as_uri()
        self._open_document(file_path)

        # Send rename request
        params = {
            "textDocument": {"uri": file_uri},
            "position": {"line": line, "character": column},
            "newName": new_name,
        }

        result = self._send_request("textDocument/rename", params)

        memory_used = (
            self._memory_manager.get_current_memory_mb()
            if self._memory_manager
            else 0.0
        )

        if result is None:
            return LSPResult(
                success=False,
                edits=[],
                locations=[],
                errors=["Rename request failed or timed out"],
                memory_used_mb=memory_used,
            )

        # Parse workspace edit
        edits = self._parse_workspace_edit(result)

        return LSPResult(
            success=True,
            edits=edits,
            locations=[],
            errors=[],
            memory_used_mb=memory_used,
        )

    def find_references(
        self,
        file_path: str,
        line: int,
        column: int,
        include_declaration: bool = True,
    ) -> LSPResult:
        """Find all references to a symbol.

        Args:
            file_path: Path to the file containing the symbol.
            line: Line number (0-indexed).
            column: Column number (0-indexed).
            include_declaration: Whether to include the declaration.

        Returns:
            LSPResult with locations.
        """
        if not self._process:
            return LSPResult(
                success=False,
                edits=[],
                locations=[],
                errors=[f"LSP server '{self.config.name}' not running"],
                memory_used_mb=0,
            )

        # Open the file in the server
        file_uri = Path(file_path).as_uri()
        self._open_document(file_path)

        # Send references request
        params = {
            "textDocument": {"uri": file_uri},
            "position": {"line": line, "character": column},
            "context": {"includeDeclaration": include_declaration},
        }

        result = self._send_request("textDocument/references", params)

        memory_used = (
            self._memory_manager.get_current_memory_mb()
            if self._memory_manager
            else 0.0
        )

        if result is None:
            return LSPResult(
                success=False,
                edits=[],
                locations=[],
                errors=["Find references request failed or timed out"],
                memory_used_mb=memory_used,
            )

        # Parse locations
        locations = self._parse_locations(result)

        return LSPResult(
            success=True,
            edits=[],
            locations=locations,
            errors=[],
            memory_used_mb=memory_used,
        )

    def _open_document(self, file_path: str) -> None:
        """Notify server that a document is open.

        Args:
            file_path: Path to the file.
        """
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            file_uri = Path(file_path).as_uri()

            # Detect language from extension
            ext = Path(file_path).suffix.lower()
            language_id = {
                ".py": "python",
                ".go": "go",
                ".rs": "rust",
                ".java": "java",
                ".kt": "kotlin",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".js": "javascript",
                ".jsx": "javascript",
                ".rb": "ruby",
                ".cs": "csharp",
                ".php": "php",
            }.get(ext, "plaintext")

            self._send_notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": file_uri,
                        "languageId": language_id,
                        "version": 1,
                        "text": content,
                    }
                },
            )
        except Exception as e:
            logger.warning(f"Failed to open document in LSP: {e}")

    def _parse_workspace_edit(self, result: dict[str, Any]) -> list[TextEdit]:
        """Parse a WorkspaceEdit into TextEdit list.

        Args:
            result: LSP WorkspaceEdit response.

        Returns:
            List of TextEdit objects.
        """
        edits: list[TextEdit] = []

        if not result:
            return edits

        # Handle documentChanges format
        if "documentChanges" in result:
            for doc_change in result["documentChanges"]:
                if "textDocument" in doc_change and "edits" in doc_change:
                    uri = doc_change["textDocument"]["uri"]
                    file_path = self._uri_to_path(uri)

                    for edit in doc_change["edits"]:
                        edits.append(self._parse_text_edit(file_path, edit))

        # Handle changes format (older LSP)
        elif "changes" in result:
            for uri, doc_edits in result["changes"].items():
                file_path = self._uri_to_path(uri)

                for edit in doc_edits:
                    edits.append(self._parse_text_edit(file_path, edit))

        return edits

    def _parse_text_edit(self, file_path: str, edit: dict[str, Any]) -> TextEdit:
        """Parse a single TextEdit.

        Args:
            file_path: File path for the edit.
            edit: LSP TextEdit object.

        Returns:
            TextEdit object.
        """
        range_obj = edit.get("range", {})
        start = range_obj.get("start", {})
        end = range_obj.get("end", {})

        return TextEdit(
            file_path=file_path,
            start_line=start.get("line", 0),
            start_column=start.get("character", 0),
            end_line=end.get("line", 0),
            end_column=end.get("character", 0),
            new_text=edit.get("newText", ""),
        )

    def _parse_locations(self, result: list[dict[str, Any]] | None) -> list[Location]:
        """Parse location results.

        Args:
            result: List of LSP Location objects.

        Returns:
            List of Location objects.
        """
        if not result:
            return []

        locations: list[Location] = []

        for loc in result:
            uri = loc.get("uri", "")
            range_obj = loc.get("range", {})
            start = range_obj.get("start", {})
            end = range_obj.get("end", {})

            locations.append(
                Location(
                    file_path=self._uri_to_path(uri),
                    start_line=start.get("line", 0),
                    start_column=start.get("character", 0),
                    end_line=end.get("line", 0),
                    end_column=end.get("character", 0),
                )
            )

        return locations

    def _uri_to_path(self, uri: str) -> str:
        """Convert file URI to path.

        Args:
            uri: File URI (file://...).

        Returns:
            File path string.
        """
        if uri.startswith("file://"):
            # Handle Windows paths (file:///C:/...)
            path = uri[7:]
            if path.startswith("/") and len(path) > 2 and path[2] == ":":
                path = path[1:]
            return path
        return uri

    def get_memory_usage_mb(self) -> float:
        """Get current memory usage of the LSP server.

        Returns:
            Memory usage in megabytes.
        """
        if self._memory_manager:
            return self._memory_manager.get_current_memory_mb()
        return 0.0

    def is_available(self) -> bool:
        """Check if the LSP server command is available.

        Returns:
            True if the server command exists.
        """
        import shutil

        return shutil.which(self.config.command[0]) is not None

    def get_supported_operations(self) -> list[str]:
        """Return list of supported LSP operations.

        Returns:
            List of operation names.
        """
        return ["rename", "find_references"]
