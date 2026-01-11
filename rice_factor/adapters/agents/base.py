"""Base coordinator implementation.

This module provides the base class for all coordinator implementations.
It handles common functionality like message routing and agent management.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from rice_factor.domain.models.agent import Agent
from rice_factor.domain.models.messages import (
    AgentMessage,
    CoordinationResult,
    MessageType,
)
from rice_factor.domain.ports.coordinator import CoordinationContext, CoordinatorPort

if TYPE_CHECKING:
    from rice_factor.config.run_mode_config import RunModeConfig


class BaseCoordinator(CoordinatorPort):
    """Base class for coordinator implementations.

    Provides common functionality for:
    - Agent lifecycle management
    - Message routing
    - Authority validation

    Subclasses must implement the coordinate() method for their
    specific coordination logic.
    """

    def __init__(self, config: RunModeConfig) -> None:
        """Initialize the coordinator.

        Args:
            config: The run mode configuration.
        """
        self._config = config
        self._agents: dict[str, Agent] = {}
        self._message_queue: list[AgentMessage] = []
        self._responses: dict[str, list[AgentMessage]] = {}

        # Initialize agents from config
        for agent_config in config.agents:
            self._agents[agent_config.agent_id] = Agent(config=agent_config)

    @property
    def config(self) -> RunModeConfig:
        """Get the run mode configuration."""
        return self._config

    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Get the name of this coordination mode."""
        ...

    def get_active_agents(self) -> list[Agent]:
        """Get all currently active agents.

        Returns:
            List of active Agent instances.
        """
        return [a for a in self._agents.values() if a.is_active]

    def get_authority_agent(self) -> Agent:
        """Get the agent with artifact emission authority.

        Returns:
            The Agent that can emit artifacts.

        Raises:
            ValueError: If authority agent is not found.
        """
        authority_id = self._config.authority_agent
        if authority_id not in self._agents:
            raise ValueError(f"Authority agent '{authority_id}' not found")
        return self._agents[authority_id]

    @abstractmethod
    async def coordinate(
        self,
        context: CoordinationContext,
    ) -> CoordinationResult:
        """Run the coordination process for a task.

        Args:
            context: The coordination context with task details.

        Returns:
            CoordinationResult with the outcome.
        """
        ...

    async def send_message(
        self,
        message: AgentMessage,
    ) -> None:
        """Send a message to an agent or broadcast.

        Args:
            message: The message to send.
        """
        self._message_queue.append(message)

        # Initialize response list for this message
        if message.message_id not in self._responses:
            self._responses[message.message_id] = []

    async def collect_responses(
        self,
        message_id: str,
        timeout_ms: int = 30000,  # noqa: ARG002
    ) -> list[AgentMessage]:
        """Collect responses to a message.

        Note: In this base implementation, responses are synchronously
        collected since we're not dealing with actual async LLM calls yet.
        Subclasses can override for real async behavior.

        Args:
            message_id: ID of the message to collect responses for.
            timeout_ms: Maximum time to wait for responses (unused in base).

        Returns:
            List of response messages.
        """
        return self._responses.get(message_id, [])

    def _generate_message_id(self) -> str:
        """Generate a unique message ID.

        Returns:
            Unique message identifier.
        """
        return f"msg-{uuid.uuid4().hex[:12]}"

    def _generate_session_id(self) -> str:
        """Generate a unique session ID.

        Returns:
            Unique session identifier.
        """
        return f"session-{uuid.uuid4().hex[:12]}"

    def _create_task_message(
        self,
        sender_id: str,
        recipient_id: str | None,
        task_content: dict[str, Any],
    ) -> AgentMessage:
        """Create a task assignment message.

        Args:
            sender_id: ID of the sending agent.
            recipient_id: ID of recipient (None for broadcast).
            task_content: The task content.

        Returns:
            AgentMessage for task assignment.
        """
        return AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.TASK_ASSIGNMENT,
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=task_content,
        )

    def _add_response(self, message_id: str, response: AgentMessage) -> None:
        """Add a response to the response collection.

        Args:
            message_id: ID of the original message.
            response: The response message.
        """
        if message_id not in self._responses:
            self._responses[message_id] = []
        self._responses[message_id].append(response)

    def _mark_task_completed(self, agent_id: str) -> None:
        """Mark a task as completed for an agent.

        Args:
            agent_id: ID of the agent that completed the task.
        """
        if agent_id in self._agents:
            self._agents[agent_id] = self._agents[agent_id].with_task_completed()

    def _get_messages_sent(self) -> int:
        """Get the total number of messages sent.

        Returns:
            Count of messages in the queue.
        """
        return len(self._message_queue)
