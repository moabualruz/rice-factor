"""Memory management for LSP servers.

Monitors memory usage of LSP server processes and takes
action when configured limits are exceeded.
"""

import logging
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemoryStatus:
    """Current memory status of a process.

    Attributes:
        pid: Process ID.
        memory_mb: Current memory usage in megabytes.
        limit_mb: Configured memory limit.
        exceeded: Whether the limit has been exceeded.
    """

    pid: int
    memory_mb: float
    limit_mb: float
    exceeded: bool


class MemoryManager:
    """Monitors and manages memory usage of LSP server processes.

    Uses psutil to monitor process memory and can trigger
    callbacks when limits are exceeded.

    Attributes:
        limit_mb: Memory limit in megabytes.
        check_interval: How often to check memory (seconds).
        on_exceed: Callback when limit exceeded.
    """

    def __init__(
        self,
        limit_mb: float = 2048,
        check_interval: float = 5.0,
        on_exceed: Callable[[MemoryStatus], None] | None = None,
    ) -> None:
        """Initialize memory manager.

        Args:
            limit_mb: Memory limit in megabytes.
            check_interval: How often to check memory in seconds.
            on_exceed: Optional callback when limit is exceeded.
        """
        self.limit_mb = limit_mb
        self.check_interval = check_interval
        self.on_exceed = on_exceed

        self._process: subprocess.Popen[bytes] | None = None
        self._running = False
        self._monitor_thread: threading.Thread | None = None
        self._psutil_available: bool | None = None
        self._peak_memory_mb: float = 0.0

    def _check_psutil(self) -> bool:
        """Check if psutil is available.

        Returns:
            True if psutil can be imported.
        """
        if self._psutil_available is not None:
            return self._psutil_available

        try:
            import psutil  # noqa: F401

            self._psutil_available = True
        except ImportError:
            logger.warning(
                "psutil not installed - memory monitoring disabled. "
                "Install with: pip install psutil"
            )
            self._psutil_available = False

        return self._psutil_available

    def start_monitoring(self, process: subprocess.Popen[bytes]) -> bool:
        """Start monitoring a process for memory usage.

        Args:
            process: The subprocess to monitor.

        Returns:
            True if monitoring started successfully.
        """
        if not self._check_psutil():
            return False

        if self._running:
            self.stop_monitoring()

        self._process = process
        self._running = True
        self._peak_memory_mb = 0.0

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name=f"lsp-memory-monitor-{process.pid}",
        )
        self._monitor_thread.start()

        logger.debug(
            f"Started memory monitoring for PID {process.pid}, limit={self.limit_mb}MB"
        )
        return True

    def stop_monitoring(self) -> None:
        """Stop monitoring the current process."""
        self._running = False

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)

        self._process = None
        self._monitor_thread = None

    def _monitor_loop(self) -> None:
        """Main monitoring loop (runs in background thread)."""
        import psutil

        while self._running and self._process:
            try:
                # Check if process is still running
                if self._process.poll() is not None:
                    logger.debug("Monitored process has exited")
                    break

                # Get memory info
                try:
                    proc = psutil.Process(self._process.pid)
                    memory_info = proc.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                except psutil.NoSuchProcess:
                    logger.debug("Process no longer exists")
                    break
                except psutil.AccessDenied:
                    logger.warning("Cannot access process memory info")
                    break

                # Track peak memory
                if memory_mb > self._peak_memory_mb:
                    self._peak_memory_mb = memory_mb

                # Check against limit
                status = MemoryStatus(
                    pid=self._process.pid,
                    memory_mb=memory_mb,
                    limit_mb=self.limit_mb,
                    exceeded=memory_mb > self.limit_mb,
                )

                if status.exceeded:
                    logger.warning(
                        f"LSP server PID {status.pid} exceeded memory limit: "
                        f"{status.memory_mb:.0f}MB > {status.limit_mb:.0f}MB"
                    )
                    if self.on_exceed:
                        self.on_exceed(status)
                    break

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in memory monitoring: {e}")
                break

        self._running = False

    def get_current_memory_mb(self) -> float:
        """Get current memory usage of monitored process.

        Returns:
            Current memory in MB, or 0 if not monitoring.
        """
        if not self._check_psutil() or not self._process:
            return 0.0

        try:
            import psutil

            proc = psutil.Process(self._process.pid)
            return float(proc.memory_info().rss / (1024 * 1024))
        except Exception:
            return 0.0

    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage recorded during monitoring.

        Returns:
            Peak memory in MB.
        """
        return self._peak_memory_mb

    def is_running(self) -> bool:
        """Check if monitoring is active.

        Returns:
            True if currently monitoring a process.
        """
        return self._running

    def kill_process(self) -> bool:
        """Kill the monitored process.

        Returns:
            True if process was killed successfully.
        """
        if not self._process:
            return False

        try:
            self._process.kill()
            self._process.wait(timeout=5)
            logger.info(f"Killed LSP server process PID {self._process.pid}")
            return True
        except Exception as e:
            logger.error(f"Failed to kill process: {e}")
            return False
        finally:
            self.stop_monitoring()

    def terminate_gracefully(self, timeout: float = 5.0) -> bool:
        """Attempt graceful termination before force kill.

        Args:
            timeout: Seconds to wait for graceful shutdown.

        Returns:
            True if process terminated successfully.
        """
        if not self._process:
            return False

        try:
            # Try terminate first (SIGTERM)
            self._process.terminate()

            try:
                self._process.wait(timeout=timeout)
                logger.info(f"LSP server PID {self._process.pid} terminated gracefully")
                return True
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown failed
                logger.warning(
                    f"Graceful shutdown timed out, force killing PID {self._process.pid}"
                )
                return self.kill_process()

        except Exception as e:
            logger.error(f"Error during graceful termination: {e}")
            return self.kill_process()
        finally:
            self.stop_monitoring()
