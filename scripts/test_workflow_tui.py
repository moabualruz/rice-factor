"""Test TUI with workflow screen."""
import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

from rice_factor.entrypoints.tui.screens.workflow import WorkflowScreen


class WorkflowTUI(App):
    """Workflow TUI app for testing."""

    CSS = """
    Screen {
        background: #0a1a0a;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield WorkflowScreen(project_root=Path("."))
        yield Footer()


async def main():
    app = WorkflowTUI()
    screenshots_dir = Path("docs/assets/screenshots/tui")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "test-workflow.svg"))
        print("Captured: test-workflow.svg")


if __name__ == "__main__":
    asyncio.run(main())
