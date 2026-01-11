"""Coordinator port for multi-agent orchestration.

This module defines the abstract protocol for agent coordinators.
All run modes implement this protocol.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rice_factor.config.run_mode_config import RunModeConfig
    from rice_factor.domain.models.agent import Agent
    from rice_factor.domain.models.messages import AgentMessage, CoordinationResult


@dataclass
class CoordinationContext:
    """Context for a coordination session.

    This contains all the information needed for agents to coordinate
    on a task.

    Attributes:
        task_id: Unique identifier for the task being coordinated.
        task_type: Type of task (e.g., "plan_project", "refactor").
        goal: The high-level goal to achieve.
        inputs: Input data for the task.
        constraints: Any constraints on the solution.
        phase: Current workflow phase (for hybrid mode).
        metadata: Additional context.
    """

    task_id: str
    task_type: str
    goal: str
    inputs: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    phase: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CoordinatorPort(ABC):
    """Abstract base class for agent coordinators.

    All run mode implementations must implement this protocol.
    The coordinator manages the interaction between agents and
    ensures that authority rules are enforced.
    """

    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Get the name of this coordination mode.

        Returns:
            Human-readable mode name.
        """
        ...

    @property
    @abstractmethod
    def config(self) -> "RunModeConfig":
        """Get the run mode configuration.

        Returns:
            The configuration for this coordinator.
        """
        ...

    @abstractmethod
    def get_active_agents(self) -> list["Agent"]:
        """Get all currently active agents.

        Returns:
            List of active Agent instances.
        """
        ...

    @abstractmethod
    def get_authority_agent(self) -> "Agent":
        """Get the agent with artifact emission authority.

        Returns:
            The Agent that can emit artifacts.
        """
        ...

    @abstractmethod
    async def coordinate(
        self,
        context: CoordinationContext,
    ) -> "CoordinationResult":
        """Run the coordination process for a task.

        This is the main entry point for multi-agent coordination.
        The coordinator will:
        1. Distribute the task to appropriate agents
        2. Collect responses/proposals
        3. Handle any voting or review
        4. Synthesize the final result
        5. Ensure only the authority agent emits artifacts

        Args:
            context: The coordination context with task details.

        Returns:
            CoordinationResult with the outcome.
        """
        ...

    @abstractmethod
    async def send_message(
        self,
        message: "AgentMessage",
    ) -> None:
        """Send a message to an agent or broadcast.

        Args:
            message: The message to send.
        """
        ...

    @abstractmethod
    async def collect_responses(
        self,
        message_id: str,
        timeout_ms: int = 30000,
    ) -> list["AgentMessage"]:
        """Collect responses to a message.

        Args:
            message_id: ID of the message to collect responses for.
            timeout_ms: Maximum time to wait for responses.

        Returns:
            List of response messages.
        """
        ...

    def validate_authority(self, agent_id: str) -> bool:
        """Check if an agent has authority to emit artifacts.

        Args:
            agent_id: ID of the agent to check.

        Returns:
            True if the agent has authority.
        """
        return agent_id == self.config.authority_agent
