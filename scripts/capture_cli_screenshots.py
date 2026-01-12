"""Capture CLI screenshots as SVG using Rich console."""

import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def capture_command_output(command: list[str], title: str) -> str:
    """Run a command and capture its output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent,
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


def create_cli_screenshot(
    output: str,
    title: str,
    filename: str,
    screenshots_dir: Path,
) -> None:
    """Create an SVG screenshot of CLI output."""
    console = Console(record=True, width=100, force_terminal=True)

    # Create styled output
    text = Text(output)
    panel = Panel(
        text,
        title=f"[bold green]$ {title}[/bold green]",
        border_style="green",
        padding=(1, 2),
    )

    console.print(panel)

    # Export as SVG
    svg_path = screenshots_dir / filename
    console.save_svg(str(svg_path), title=title)
    print(f"Captured: {filename}")


def main():
    screenshots_dir = Path("docs/assets/screenshots/cli")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Commands to capture
    commands = [
        (["rice-factor", "--help"], "rice-factor --help", "cli-help.svg"),
        (["rice-factor", "init", "--help"], "rice-factor init --help", "cli-init.svg"),
        (["rice-factor", "plan", "--help"], "rice-factor plan --help", "cli-plan.svg"),
        (["rice-factor", "scaffold", "--help"], "rice-factor scaffold --help", "cli-scaffold.svg"),
        (["rice-factor", "impl", "--help"], "rice-factor impl --help", "cli-impl.svg"),
        (["rice-factor", "test", "--help"], "rice-factor test --help", "cli-test.svg"),
        (["rice-factor", "approve", "--help"], "rice-factor approve --help", "cli-approve.svg"),
        (["rice-factor", "ci", "--help"], "rice-factor ci --help", "cli-ci.svg"),
        (["rice-factor", "audit", "--help"], "rice-factor audit --help", "cli-audit.svg"),
        (["rice-factor", "refactor", "--help"], "rice-factor refactor --help", "cli-refactor.svg"),
        (["rice-factor", "reconcile", "--help"], "rice-factor reconcile --help", "cli-reconcile.svg"),
        (["rice-factor", "tui", "--help"], "rice-factor tui --help", "cli-tui.svg"),
    ]

    for cmd, title, filename in commands:
        # Use the venv's rice-factor
        venv_cmd = [str(Path(".venv/Scripts/rice-factor"))] + cmd[1:]
        output = capture_command_output(venv_cmd, title)
        create_cli_screenshot(output, title, filename, screenshots_dir)

    print(f"\nCaptured {len(commands)} CLI screenshots to {screenshots_dir}")


if __name__ == "__main__":
    main()
