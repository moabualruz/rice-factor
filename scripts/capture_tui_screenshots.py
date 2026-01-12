"""Capture TUI screenshots using Textual's built-in screenshot feature."""

import asyncio
from pathlib import Path

from textual.pilot import Pilot


async def capture_screenshots():
    """Capture screenshots of all TUI screens."""
    from rice_factor.entrypoints.tui.app import RiceFactorTUI

    # Create a test project directory
    test_project = Path("tests/fixtures/demo-project")
    test_project.mkdir(parents=True, exist_ok=True)

    # Create .project structure
    project_dir = test_project / ".project"
    project_dir.mkdir(exist_ok=True)
    (project_dir / "requirements.md").write_text("# Requirements\n\nDemo project.")
    (project_dir / "constraints.md").write_text("# Constraints\n\nNone.")
    (project_dir / "glossary.md").write_text("# Glossary\n\n- **Term**: Definition")
    (project_dir / ".phase").write_text("PLANNING")

    # Create artifacts
    artifacts_dir = test_project / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    import json
    sample_artifact = {
        "id": "project-plan-001",
        "artifact_type": "ProjectPlan",
        "version": "1.0.0",
        "status": "approved",
        "created_at": "2024-01-15T10:30:00Z",
        "payload": {"name": "Demo Project", "goals": ["Build CLI", "Add TUI"]}
    }
    (artifacts_dir / "project-plan-001.json").write_text(json.dumps(sample_artifact, indent=2))

    screenshots_dir = Path("docs/assets/screenshots/tui")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    app = RiceFactorTUI(project_root=test_project)

    async with app.run_test(size=(120, 40)) as pilot:
        # Wait for app to load
        await pilot.pause()

        # Screenshot workflow tab (default)
        app.save_screenshot(str(screenshots_dir / "tui-workflow.svg"))
        print("Captured: tui-workflow.svg")

        # Switch to artifacts tab
        await pilot.press("a")
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-artifacts.svg"))
        print("Captured: tui-artifacts.svg")

        # Switch to diffs tab
        await pilot.press("d")
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-diffs.svg"))
        print("Captured: tui-diffs.svg")

        # Switch to config tab
        await pilot.press("c")
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-config.svg"))
        print("Captured: tui-config.svg")

        # Switch to history tab
        await pilot.press("h")
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-history.svg"))
        print("Captured: tui-history.svg")

        # Switch to graph tab
        await pilot.press("g")
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-graph.svg"))
        print("Captured: tui-graph.svg")

        # Show help
        await pilot.press("?")
        await pilot.pause()
        app.save_screenshot(str(screenshots_dir / "tui-help.svg"))
        print("Captured: tui-help.svg")


if __name__ == "__main__":
    asyncio.run(capture_screenshots())
