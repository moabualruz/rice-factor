# Rice-Factor CLI Demo
# VHS Tape Script - https://github.com/charmbracelet/vhs
#
# To generate the demo GIF, install VHS and run:
#   vhs demo.tape
#
# This will create demo.gif in the current directory.
# Move it to docs/assets/demos/ for use in README.md

# Output settings
Output demo.gif
Output demo.mp4
Output demo.webm

# Terminal settings
Set FontSize 14
Set Width 1200
Set Height 700
Set Theme "Catppuccin Mocha"
Set FontFamily "JetBrains Mono"
Set Padding 20
Set Framerate 30

# Window chrome
Set WindowBar Colorful
Set WindowBarSize 40

# Initial pause
Sleep 1s

# Title card
Type "# Rice-Factor: LLM-Assisted Development System"
Enter
Sleep 2s
Ctrl+L

# Show version
Type "rice-factor --version"
Enter
Sleep 1.5s

# Show help
Type "rice-factor --help"
Enter
Sleep 3s

# Clear and start workflow
Ctrl+L
Type "# Initialize a new project"
Enter
Sleep 500ms

Type "rice-factor init"
Enter
Sleep 2s

# Show project structure
Type "tree .project -L 2"
Enter
Sleep 2s

# Generate project plan
Ctrl+L
Type "# Generate project plan from requirements"
Enter
Sleep 500ms

Type "rice-factor plan project"
Enter
Sleep 3s

# List artifacts
Type "rice-factor artifact list"
Enter
Sleep 2s

# Approve plan
Ctrl+L
Type "# Approve the project plan"
Enter
Sleep 500ms

Type "rice-factor approve proj-demo-123"
Enter
Sleep 1.5s

# Generate scaffold
Type "# Create file scaffolding"
Enter
Sleep 500ms

Type "rice-factor scaffold"
Enter
Sleep 2s

# Generate tests
Ctrl+L
Type "# Generate test plan (TDD)"
Enter
Sleep 500ms

Type "rice-factor plan tests"
Enter
Sleep 2.5s

# Approve tests
Type "rice-factor approve test-demo-456"
Enter
Sleep 1s

# Lock tests
Type "# Lock tests (immutable)"
Enter
Sleep 500ms

Type "rice-factor lock tests"
Enter
Sleep 500ms
Type "LOCK"
Enter
Sleep 2s

# Generate implementation
Ctrl+L
Type "# Plan and implement code"
Enter
Sleep 500ms

Type "rice-factor plan impl src/converter.py"
Enter
Sleep 2s

Type "rice-factor impl src/converter.py"
Enter
Sleep 2.5s

# Review diff
Type "rice-factor review"
Enter
Sleep 2s

# Apply changes
Type "rice-factor apply"
Enter
Sleep 1.5s

# Run tests
Ctrl+L
Type "# Run tests"
Enter
Sleep 500ms

Type "rice-factor test"
Enter
Sleep 2.5s

# Final summary
Ctrl+L
Type "# Workflow complete!"
Enter
Type "# Artifacts approved, tests locked, code implemented"
Enter
Sleep 500ms

Type "rice-factor status"
Enter
Sleep 3s

# End
Sleep 2s
