from textual.app import ComposeResult
from textual.widgets import Log, Button, Label, Static
from textual.screen import ModalScreen
from textual.containers import Grid, Vertical

class CommandOutputScreen(ModalScreen[None]):
    """Screen to display output of a running command."""

    CSS = """
    CommandOutputScreen {
        background: rgba(0,0,0,0.7);
        align: center middle;
    }

    #dialog {
        background: #0a1a0a;
        border: solid #00a020;
        width: 90%;
        height: 80%;
        padding: 1;
    }
    
    #title {
        text-align: center;
        background: #009e20;
        color: white;
        padding: 1;
    }

    Log {
        border: solid #009e20;
        height: 1fr;
        background: #000000;
        color: #00ff00;
    }

    #close {
        width: 100%;
        margin-top: 1;
    }
    """

    def __init__(self, title: str, command_args: list[str]) -> None:
        super().__init__()
        self._title = title
        self._command_args = command_args

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self._title, id="title")
            yield Log(id="output-log")
            yield Button("Close", id="close", variant="primary")

    def on_mount(self) -> None:
        log = self.query_one(Log)
        log.write_line(f"Running: {' '.join(self._command_args)}...")
        self.run_command()

    def run_command(self) -> None:
        """Run the command in background and pipe output to log."""
        # In a real app we'd use asyncio.create_subprocess_exec
        # verifying proper event loop handling.
        import asyncio
        import sys
        
        async def _run():
            log = self.query_one(Log)
            try:
                # We need to find the rice-factor executable or identical python module call
                # Using sys.executable to run the module is safer for portability
                cmd = [sys.executable, "-m", "rice_factor.entrypoints.cli.main"] + self._command_args
                
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                if proc.stdout:
                    while True:
                        line = await proc.stdout.readline()
                        if not line:
                            break
                        log.write(line.decode().replace('\r', ''))
                
                await proc.wait()
                
                if proc.returncode == 0:
                    log.write_line("\n[SUCCESS] Command completed.")
                else:
                    log.write_line(f"\n[ERROR] Command failed with code {proc.returncode}")
                    if proc.stderr:
                        err = await proc.stderr.read()
                        log.write(err.decode())
                        
            except Exception as e:
                log.write_line(f"[EXCEPTION] {e}")

        asyncio.create_task(_run())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()
