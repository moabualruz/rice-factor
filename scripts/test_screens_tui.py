"""Test each TUI screen individually."""
import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

screenshots_dir = Path("docs/assets/screenshots/tui")
screenshots_dir.mkdir(parents=True, exist_ok=True)


async def test_workflow():
    from rice_factor.entrypoints.tui.screens.workflow import WorkflowScreen

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield WorkflowScreen(project_root=Path("."))
            yield Footer()

    app = TestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-workflow.svg"))
        print("Captured: tui-workflow.svg")


async def test_browser():
    from rice_factor.entrypoints.tui.screens.browser import ArtifactBrowserScreen

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield ArtifactBrowserScreen(project_root=Path("."))
            yield Footer()

    app = TestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-artifacts.svg"))
        print("Captured: tui-artifacts.svg")


async def test_diff_viewer():
    from rice_factor.entrypoints.tui.screens.diff_viewer import DiffViewerScreen

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield DiffViewerScreen(project_root=Path("."))
            yield Footer()

    app = TestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-diffs.svg"))
        print("Captured: tui-diffs.svg")


async def test_config():
    from rice_factor.entrypoints.tui.screens.config_editor import ConfigEditorScreen

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield ConfigEditorScreen(project_root=Path("."))
            yield Footer()

    app = TestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-config.svg"))
        print("Captured: tui-config.svg")


async def test_history():
    from rice_factor.entrypoints.tui.screens.history import HistoryScreen

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield HistoryScreen(project_root=Path("."))
            yield Footer()

    app = TestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-history.svg"))
        print("Captured: tui-history.svg")


async def test_graph():
    from rice_factor.entrypoints.tui.screens.graph import GraphScreen

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield GraphScreen(project_root=Path("."))
            yield Footer()

    app = TestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-graph.svg"))
        print("Captured: tui-graph.svg")


async def main():
    print("Testing workflow...")
    await test_workflow()

    print("Testing browser...")
    await test_browser()

    print("Testing diff viewer...")
    await test_diff_viewer()

    print("Testing config...")
    await test_config()

    print("Testing history...")
    await test_history()

    print("Testing graph...")
    await test_graph()

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
