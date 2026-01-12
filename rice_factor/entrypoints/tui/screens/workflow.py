"""Workflow view screen for TUI.

This module provides the workflow navigation screen showing the current
project phase and available commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, Static

if TYPE_CHECKING:
    from rice_factor.domain.services.phase_service import PhaseService


# Phase workflow steps
WORKFLOW_STEPS = [
    ("init", "Initialize Project", "Create .project/ directory"),
    ("plan project", "Plan Project", "Generate ProjectPlan artifact"),
    ("scaffold", "Scaffold", "Create project structure"),
    ("plan tests", "Plan Tests", "Generate TestPlan artifact"),
    ("lock", "Lock Tests", "Lock TestPlan (immutable)"),
    ("plan impl", "Plan Implementation", "Generate ImplementationPlan"),
    ("impl", "Implement", "Generate code changes"),
    ("apply", "Apply Changes", "Apply approved diffs"),
    ("test", "Run Tests", "Execute test suite"),
]


class WorkflowStep(Static):
    """A single step in the workflow.

    Attributes:
        step_name: Name of the command/step.
        description: Short description of the step.
        is_current: Whether this is the current step.
        is_complete: Whether this step has been completed.
    """

    # Rice-Factor brand colors
    DEFAULT_CSS = """
    WorkflowStep {
        height: auto;
        padding: 1;
        margin: 0 1;
        border: solid #009e20;
        background: #0a1a0a;
    }

    WorkflowStep.current {
        border: double #00a020;
        background: #102010;
    }

    WorkflowStep.complete {
        border: solid #00c030;
    }

    WorkflowStep.unavailable {
        opacity: 0.5;
    }

    WorkflowStep .step-name {
        text-style: bold;
        color: #00a020;
    }

    WorkflowStep .step-description {
        color: #808080;
    }
    """

    def __init__(
        self,
        step_name: str,
        title: str,
        description: str,
        is_current: bool = False,
        is_complete: bool = False,
        is_available: bool = True,
    ) -> None:
        """Initialize a workflow step.

        Args:
            step_name: Name of the command/step.
            title: Display title.
            description: Short description.
            is_current: Whether this is the current step.
            is_complete: Whether this step is complete.
            is_available: Whether this step is currently available.
        """
        super().__init__()
        self._step_name = step_name
        self._title = title
        self._description = description
        self._is_current = is_current
        self._is_complete = is_complete
        self._is_available = is_available

    def compose(self) -> ComposeResult:
        """Compose the step display.

        Yields:
            UI components.
        """
        status = ""
        if self._is_complete:
            status = " [OK]"
        elif self._is_current:
            status = " [>>]"

        yield Label(f"{self._title}{status}", classes="step-name")
        yield Label(self._description, classes="step-description")

    def on_mount(self) -> None:
        """Handle mount event."""
        if self._is_current:
            self.add_class("current")
        if self._is_complete:
            self.add_class("complete")
        if not self._is_available:
            self.add_class("unavailable")


class WorkflowScreen(Container):
    """Workflow navigation screen.

    Shows the current project phase and workflow progress.

    Attributes:
        project_root: Root directory of the project.
        phase_service: Service for phase detection.
    """

    # Rice-Factor brand colors
    DEFAULT_CSS = """
    WorkflowScreen {
        width: 100%;
        height: 100%;
        background: #0a1a0a;
    }

    #workflow-header {
        height: auto;
        padding: 1;
        text-align: center;
        background: #009e20;
        color: white;
    }

    #workflow-steps {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }

    #phase-info {
        height: auto;
        padding: 1;
        margin: 1;
        border: solid #00a020;
        color: #00c030;
    }
    """

    def __init__(
        self,
        project_root: Path | None = None,
        phase_service: PhaseService | None = None,
    ) -> None:
        """Initialize the workflow screen.

        Args:
            project_root: Root directory of the project.
            phase_service: Service for phase detection.
        """
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._phase_service = phase_service

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    @property
    def phase_service(self) -> PhaseService | None:
        """Get the phase service."""
        return self._phase_service

    def compose(self) -> ComposeResult:
        """Compose the workflow view.

        Yields:
            UI components.
        """
        yield Static("Rice-Factor Workflow", id="workflow-header")

        # Phase information
        phase_text = self._get_phase_text()
        yield Static(phase_text, id="phase-info")

        # Workflow steps
        
        current_step = self._get_current_step()
        steps = []
        for i, (cmd, title, desc) in enumerate(WORKFLOW_STEPS):
            is_current = cmd == current_step
            is_complete = self._is_step_complete(i)
            is_available = self._is_step_available(cmd)

            steps.append(WorkflowStep(
                step_name=cmd,
                title=title,
                description=desc,
                is_current=is_current,
                is_complete=is_complete,
                is_available=is_available,
            ))
        
        yield Vertical(*steps, id="workflow-steps")

    def _get_phase_text(self) -> str:
        """Get the current phase display text.

        Returns:
            Phase description text.
        """
        if self._phase_service is None:
            return "Phase: Unknown (no phase service)"

        phase = self._phase_service.get_current_phase()
        phase_descriptions = {
            "uninit": "Not initialized - run 'rice-factor init'",
            "init": "Initialized - ready to plan project",
            "planning": "Planning - ProjectPlan approved",
            "scaffolded": "Scaffolded - structure created",
            "test_locked": "Tests Locked - ready for implementation",
            "implementing": "Implementing - active development",
        }
        desc = phase_descriptions.get(phase.value, phase.value)
        return f"Current Phase: {desc}"

    def _get_current_step(self) -> str:
        """Get the current workflow step based on phase.

        Returns:
            Current step command name.
        """
        if self._phase_service is None:
            return "init"

        phase = self._phase_service.get_current_phase()
        phase_to_step = {
            "uninit": "init",
            "init": "plan project",
            "planning": "scaffold",
            "scaffolded": "plan tests",
            "test_locked": "plan impl",
            "implementing": "impl",
        }
        return phase_to_step.get(phase.value, "init")

    def _is_step_complete(self, step_index: int) -> bool:
        """Check if a step is complete based on phase.

        Args:
            step_index: Index of the step in WORKFLOW_STEPS.

        Returns:
            True if the step is complete.
        """
        if self._phase_service is None:
            return False

        phase = self._phase_service.get_current_phase()
        phase_index = {
            "uninit": -1,
            "init": 0,
            "planning": 1,
            "scaffolded": 3,
            "test_locked": 4,
            "implementing": 5,
        }.get(phase.value, -1)

        return step_index <= phase_index

    def _is_step_available(self, step_cmd: str) -> bool:
        """Check if a step is currently available.

        Args:
            step_cmd: Command name.

        Returns:
            True if the step can be executed.
        """
        if self._phase_service is None:
            return step_cmd == "init"

        return self._phase_service.can_execute(step_cmd)

    async def action_execute_step(self) -> None:
        """Execute the current workflow step."""
        current_step = self._get_current_step()
        await self._exec_command_for_step(current_step)

    async def _exec_command_for_step(self, step_cmd: str) -> None:
        """Execute the equivalent CLI command for a step."""
        from rice_factor.entrypoints.tui.screens.command_output import CommandOutputScreen
        
        # specific handling for init to show questionnaire could be kept,
        # but for parity running the CLI (which handles it) is cleaner via the output screen
        # IF the CLI is interactive, our text log won't handle inputs well yet.
        # For this implementation, we assume non-interactive or "default" args where possible
        # or we implement a real terminal widget.
        # Given constraints, we will run commands with flags to avoid interaction or assume the log is just tailored.
        
        # Map step name to CLI args
        # "init", "plan project", "scaffold", "plan tests", "lock", "plan impl", "impl", "apply", "test"
        
        cmd_map = {
            "init": ["init", "--skip-questionnaire"], # Non-interactive for basic TUI flow
            "plan project": ["plan", "--mode", "planning"],
            "scaffold": ["scaffold"],
            "plan tests": ["plan", "--mode", "tests"],
            "lock": ["lock"],
            "plan impl": ["plan", "--mode", "implementation"],
            "impl": ["impl"],
            "apply": ["apply"],
            "test": ["test"],
        }
        
        args = cmd_map.get(step_cmd)
        if args:
            self.app.push_screen(CommandOutputScreen(title=f"Running {step_cmd.title()}...", command_args=args))
        else:
             self.notify(f"Unknown command mapping for '{step_cmd}'", severity="error")

    async def _exec_init(self) -> None:
        """Deprecated: Use _exec_command_for_step."""
        pass

    async def refresh_view(self) -> None:
        """Refresh the workflow view."""
        await self.remove_children()
        await self.mount_all(list(self.compose()))
