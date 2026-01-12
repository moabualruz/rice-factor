import pytest
import os
from pathlib import Path
from rice_factor.entrypoints.tui.app import RiceFactorTUI

# Screenshot directory
SCREENSHOT_DIR = Path("docs/assets/screenshots/tui")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

@pytest.mark.asyncio
async def test_tui_startup_and_init(tmp_path):
    """Test TUI startup and basic workflow navigation."""
    
    # Use a temp dir as project root to simulate clean state
    app = RiceFactorTUI(project_root=tmp_path)
    
    async with app.run_test() as pilot:
        # Check initial state
        assert app.query_one("#workflow-tab").id == "workflow-tab"
        
        # Simulate Enter to run the first command (init)
        await pilot.press("enter")
        await pilot.pause()
        
        # Check if CommandOutputScreen is pushed
        # In a real text runner we'd see if the screen class is in app.screen_stack
        # app.screen is the current screen
        from rice_factor.entrypoints.tui.screens.command_output import CommandOutputScreen
        assert isinstance(app.screen, CommandOutputScreen), "Command Runner screen not opened!"
        
        # Close it
        await pilot.press("enter") # Defaults to close button usually if focused, or we click ID
        # Since we didn't focus specific generic button, let's use ID:
        await pilot.click("#close")
        await pilot.pause()


        # Switch to Artifacts tab
        await pilot.press("a")
        assert app.query_one("TabbedContent").active == "artifacts-tab"
        
        # Test Tree Navigation in Artifacts
        # assuming there's a Tree widget
        if app.query("Tree"):
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter") # Select something
        
        # Switch back to Workflow
        await pilot.press("w")
        assert app.query_one("TabbedContent").active == "workflow-tab"

        # Check Help Dialog
        await pilot.press("question_mark")
        # Textual's notify is transient, difficult to assert content in pilot instantly without custom waiter
        # But we can check if it didn't crash
        
        # Command Palette
        # await pilot.press("ctrl+p") # If implemented
        
        # Refresh
        await pilot.press("r")
        
        # Take a final screenshot for documentation
        # app.save_screenshot(SCREENSHOT_DIR / "tui-e2e-final.svg") # SVG is default for textual screenshot

