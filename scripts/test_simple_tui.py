"""Test TUI with a simpler app."""
import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static


class SimpleTUI(App):
    """Simple TUI app for testing."""

    CSS = """
    Screen {
        background: #0a1a0a;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Hello World")
        yield Footer()


async def main():
    app = SimpleTUI()
    screenshots_dir = Path("docs/assets/screenshots/tui")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "test-simple.svg"))
        print("Captured: test-simple.svg")


if __name__ == "__main__":
    asyncio.run(main())
