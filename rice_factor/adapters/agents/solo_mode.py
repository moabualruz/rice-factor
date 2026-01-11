"""Solo mode coordinator (Mode A).

Solo mode is the simplest coordination mode with a single agent
that has full authority. No delegation, no review, just direct
artifact generation.

Best for:
- Solo developer
- MVP development
- Experimentation
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from rice_factor.adapters.agents.base import BaseCoordinator
from rice_factor.domain.models.messages import (
    AgentMessage,
    CoordinationResult,
    MessageType,
)
from rice_factor.domain.ports.coordinator import CoordinationContext  # noqa: TC001

if TYPE_CHECKING:
    from rice_factor.config.run_mode_config import RunModeConfig


class SoloCoordinator(BaseCoordinator):
    """Coordinator for solo mode (single agent).

    In solo mode:
    - One agent has full authority
    - No parallel reasoning
    - No second opinions
    - Still bound by artifact contracts

    This is the lowest overhead mode with the lowest safety margin.
    """

    def __init__(self, config: RunModeConfig) -> None:
        """Initialize the solo coordinator.

        Args:
            config: The run mode configuration.
        """
        super().__init__(config)

    @property
    def mode_name(self) -> str:
        """Get the mode name."""
        return "solo"

    async def coordinate(
        self,
        context: CoordinationContext,
    ) -> CoordinationResult:
        """Execute coordination in solo mode.

        Solo mode is essentially a pass-through: the single authority
        agent receives the task and produces the result directly.

        Args:
            context: The coordination context with task details.

        Returns:
            CoordinationResult with the outcome.
        """
        start_time = time.time()
        session_id = self._generate_session_id()

        try:
            # Get the authority agent
            authority = self.get_authority_agent()

            # Create task assignment message
            task_message = self._create_task_message(
                sender_id="system",
                recipient_id=authority.agent_id,
                task_content={
                    "task_id": context.task_id,
                    "task_type": context.task_type,
                    "goal": context.goal,
                    "inputs": context.inputs,
                    "constraints": context.constraints,
                },
            )

            # Send the task
            await self.send_message(task_message)

            # In a real implementation, this would invoke the LLM
            # For now, we simulate the agent processing
            result = await self._process_task(authority.agent_id, task_message)

            # Mark task completed
            self._mark_task_completed(authority.agent_id)

            duration_ms = int((time.time() - start_time) * 1000)

            return CoordinationResult(
                session_id=session_id,
                success=result.get("success", True),
                participating_agents=(authority.agent_id,),
                messages_exchanged=self._get_messages_sent(),
                artifact_id=result.get("artifact_id"),
                final_decision=result.get("decision"),
                reasoning=result.get("reasoning"),
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CoordinationResult(
                session_id=session_id,
                success=False,
                participating_agents=tuple(self._agents.keys()),
                messages_exchanged=self._get_messages_sent(),
                errors=(str(e),),
                duration_ms=duration_ms,
            )

    async def _process_task(
        self,
        agent_id: str,
        task_message: AgentMessage,
    ) -> dict[str, Any]:
        """Process a task message (simulated).

        In a real implementation, this would:
        1. Format a prompt from the task message
        2. Call the LLM via the LLM port
        3. Parse the response into structured output
        4. Return the result

        Args:
            agent_id: ID of the processing agent.
            task_message: The task to process.

        Returns:
            Dict with processing results.
        """
        # Create response message
        response = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.TASK_RESULT,
            sender_id=agent_id,
            recipient_id="system",
            content={
                "status": "completed",
                "task_id": task_message.content.get("task_id"),
            },
            correlation_id=task_message.message_id,
        )

        self._add_response(task_message.message_id, response)

        # Return simulated result
        return {
            "success": True,
            "decision": f"Task '{task_message.content.get('goal')}' processed",
            "reasoning": "Solo agent processed task directly",
        }
