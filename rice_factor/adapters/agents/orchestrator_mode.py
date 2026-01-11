"""Orchestrator mode coordinator (Mode B).

Orchestrator mode has one authoritative orchestrator agent that
delegates to multiple helper agents, synthesizes their results,
and produces the final output.

Best for:
- Non-trivial projects
- Refactoring
- Architecture-sensitive work
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from rice_factor.adapters.agents.base import BaseCoordinator
from rice_factor.config.run_mode_config import CoordinationRule
from rice_factor.domain.models.agent import Agent, AgentRole
from rice_factor.domain.models.messages import (
    AgentMessage,
    CoordinationResult,
    MessagePriority,
    MessageType,
)
from rice_factor.domain.ports.coordinator import CoordinationContext  # noqa: TC001

if TYPE_CHECKING:
    from rice_factor.config.run_mode_config import RunModeConfig


class OrchestratorCoordinator(BaseCoordinator):
    """Coordinator for orchestrator mode (delegation pattern).

    In orchestrator mode:
    - One orchestrator has authority to emit artifacts
    - Multiple helper agents provide input
    - Orchestrator synthesizes results
    - Critic review can be mandatory

    Workflow:
    1. Orchestrator receives task
    2. Orchestrator delegates subtasks to helpers
    3. Helpers return proposals/analysis
    4. Critic reviews (if mandatory)
    5. Orchestrator synthesizes final result
    6. Orchestrator emits artifact
    """

    def __init__(self, config: RunModeConfig) -> None:
        """Initialize the orchestrator coordinator.

        Args:
            config: The run mode configuration.
        """
        super().__init__(config)
        self._round_count = 0

    @property
    def mode_name(self) -> str:
        """Get the mode name."""
        return "orchestrator"

    async def coordinate(
        self,
        context: CoordinationContext,
    ) -> CoordinationResult:
        """Execute coordination in orchestrator mode.

        The orchestrator:
        1. Analyzes the task
        2. Delegates to appropriate helpers
        3. Collects responses
        4. Has critic review if required
        5. Synthesizes final result

        Args:
            context: The coordination context with task details.

        Returns:
            CoordinationResult with the outcome.
        """
        start_time = time.time()
        session_id = self._generate_session_id()
        self._round_count = 0

        try:
            # Get orchestrator (authority agent)
            orchestrator = self.get_authority_agent()

            # Step 1: Create initial task for orchestrator
            initial_task = self._create_task_message(
                sender_id="system",
                recipient_id=orchestrator.agent_id,
                task_content={
                    "task_id": context.task_id,
                    "task_type": context.task_type,
                    "goal": context.goal,
                    "inputs": context.inputs,
                    "constraints": context.constraints,
                    "phase": "delegation_planning",
                },
            )
            await self.send_message(initial_task)
            self._round_count += 1

            # Step 2: Plan delegation
            delegation_plan = await self._plan_delegation(orchestrator, context)

            # Step 3: Delegate to helpers
            helper_responses = await self._delegate_to_helpers(
                orchestrator, delegation_plan, context
            )

            # Step 4: Critic review (if required)
            critic_feedback = None
            if self._requires_critic_review():
                critic_feedback = await self._get_critic_review(
                    orchestrator, helper_responses, context
                )

            # Step 5: Synthesize final result
            final_result = await self._synthesize_result(
                orchestrator, helper_responses, critic_feedback, context
            )

            # Mark orchestrator task completed
            self._mark_task_completed(orchestrator.agent_id)

            duration_ms = int((time.time() - start_time) * 1000)

            return CoordinationResult(
                session_id=session_id,
                success=final_result.get("success", True),
                participating_agents=tuple(
                    a.agent_id for a in self.get_active_agents()
                ),
                messages_exchanged=self._get_messages_sent(),
                artifact_id=final_result.get("artifact_id"),
                final_decision=final_result.get("decision"),
                reasoning=final_result.get("reasoning"),
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

    async def _plan_delegation(
        self,
        orchestrator: Agent,  # noqa: ARG002
        context: CoordinationContext,
    ) -> dict[str, Any]:
        """Plan how to delegate the task.

        The orchestrator analyzes the task and determines:
        - Which helper agents to involve
        - What subtasks to assign each
        - In what order

        Args:
            orchestrator: The orchestrator agent.
            context: The coordination context.

        Returns:
            Delegation plan with subtasks and assignments.
        """
        # Get available helpers
        helpers = self._get_helper_agents()

        # Create delegation plan based on task type and available helpers
        plan: dict[str, Any] = {
            "subtasks": [],
            "assignments": {},
        }

        for helper in helpers:
            subtask = self._create_subtask_for_helper(helper, context)
            if subtask:
                plan["subtasks"].append(subtask)
                plan["assignments"][helper.agent_id] = subtask

        return plan

    async def _delegate_to_helpers(
        self,
        orchestrator: Agent,
        delegation_plan: dict[str, object],
        context: CoordinationContext,
    ) -> list[AgentMessage]:
        """Delegate subtasks to helper agents.

        Args:
            orchestrator: The orchestrator agent.
            delegation_plan: The delegation plan.
            context: The coordination context.

        Returns:
            List of response messages from helpers.
        """
        responses: list[AgentMessage] = []

        assignments = delegation_plan.get("assignments", {})
        if not isinstance(assignments, dict):
            assignments = {}
        for agent_id, subtask in assignments.items():
            # Create delegation message
            delegation_msg = AgentMessage(
                message_id=self._generate_message_id(),
                message_type=MessageType.TASK_DELEGATION,
                sender_id=orchestrator.agent_id,
                recipient_id=agent_id,
                content={
                    "subtask": subtask,
                    "context": {
                        "task_id": context.task_id,
                        "goal": context.goal,
                    },
                },
                correlation_id=context.task_id,
            )

            await self.send_message(delegation_msg)
            self._round_count += 1

            # Simulate helper processing
            response = await self._process_helper_task(agent_id, delegation_msg)
            responses.append(response)
            self._mark_task_completed(agent_id)

        return responses

    async def _get_critic_review(
        self,
        orchestrator: Agent,
        helper_responses: list[AgentMessage],
        context: CoordinationContext,
    ) -> AgentMessage | None:
        """Get critic review of the collected responses.

        Args:
            orchestrator: The orchestrator agent.
            helper_responses: Responses from helper agents.
            context: The coordination context.

        Returns:
            Critic's review message, or None if no critic available.
        """
        critics = self._config.get_agents_by_role(AgentRole.CRITIC)
        if not critics:
            return None

        critic = critics[0]

        # Create review request
        review_request = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.ARTIFACT_CRITIQUE,
            sender_id=orchestrator.agent_id,
            recipient_id=critic.agent_id,
            content={
                "task_id": context.task_id,
                "responses": [
                    {"agent_id": r.sender_id, "content": r.content}
                    for r in helper_responses
                ],
                "request": "Review the collected proposals and identify issues",
            },
            priority=MessagePriority.HIGH,
        )

        await self.send_message(review_request)
        self._round_count += 1

        # Simulate critic review
        critique = await self._process_critic_review(critic.agent_id, review_request)
        self._mark_task_completed(critic.agent_id)

        return critique

    async def _synthesize_result(
        self,
        orchestrator: Agent,
        helper_responses: list[AgentMessage],
        critic_feedback: AgentMessage | None,
        context: CoordinationContext,
    ) -> dict[str, Any]:
        """Synthesize the final result from all inputs.

        The orchestrator combines:
        - Helper responses
        - Critic feedback (if any)
        - Original context

        To produce the final artifact.

        Args:
            orchestrator: The orchestrator agent.
            helper_responses: Responses from helpers.
            critic_feedback: Optional critic feedback.
            context: The coordination context.

        Returns:
            Final result dictionary.
        """
        # Create synthesis message
        synthesis_msg = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.SYNTHESIS,
            sender_id="system",
            recipient_id=orchestrator.agent_id,
            content={
                "task_id": context.task_id,
                "helper_responses": [
                    {"agent_id": r.sender_id, "content": r.content}
                    for r in helper_responses
                ],
                "critic_feedback": critic_feedback.content if critic_feedback else None,
                "request": "Synthesize final result",
            },
        )

        await self.send_message(synthesis_msg)
        self._round_count += 1

        # Combine reasoning from all sources
        reasoning_parts = []
        for response in helper_responses:
            agent_id = response.sender_id
            content = response.content.get("analysis", response.content.get("proposal", ""))
            if content:
                reasoning_parts.append(f"[{agent_id}]: {content}")

        if critic_feedback:
            critic_content = critic_feedback.content.get("critique", "")
            if critic_content:
                reasoning_parts.append(f"[critic]: {critic_content}")

        return {
            "success": True,
            "decision": f"Orchestrator synthesized result for '{context.goal}'",
            "reasoning": "\n".join(reasoning_parts) if reasoning_parts else "Synthesis complete",
        }

    def _get_helper_agents(self) -> list[Agent]:
        """Get all non-orchestrator agents that can help.

        Returns:
            List of helper agents.
        """
        authority_id = self._config.authority_agent
        return [
            agent for agent in self.get_active_agents()
            if agent.agent_id != authority_id
        ]

    def _create_subtask_for_helper(
        self,
        helper: Agent,
        context: CoordinationContext,
    ) -> dict[str, str] | None:
        """Create a subtask appropriate for a helper's role.

        Args:
            helper: The helper agent.
            context: The coordination context.

        Returns:
            Subtask dict, or None if no appropriate task.
        """
        role = helper.role

        if role == AgentRole.PLANNER:
            return {
                "type": "decompose",
                "instruction": f"Decompose the goal '{context.goal}' into subtasks",
            }
        elif role == AgentRole.CRITIC:
            # Critic will be called separately for review
            return None
        elif role == AgentRole.DOMAIN_SPECIALIST:
            scope = helper.config.scope or "general"
            return {
                "type": "analyze",
                "instruction": f"Analyze '{context.goal}' from {scope} perspective",
            }
        elif role == AgentRole.REFACTOR_ANALYST:
            return {
                "type": "safety_analysis",
                "instruction": f"Evaluate safety and ripple effects of '{context.goal}'",
            }
        elif role == AgentRole.TEST_STRATEGIST:
            return {
                "type": "test_evaluation",
                "instruction": f"Evaluate test implications of '{context.goal}'",
            }
        else:
            return {
                "type": "general",
                "instruction": f"Provide input on '{context.goal}'",
            }

    def _requires_critic_review(self) -> bool:
        """Check if critic review is mandatory.

        Returns:
            True if critic must review before completion.
        """
        return (
            self._config.has_rule(CoordinationRule.MANDATORY_CRITIC_REVIEW)
            or self._config.has_rule(CoordinationRule.CRITICS_MUST_REVIEW_BEFORE_APPROVAL)
        )

    async def _process_helper_task(
        self,
        agent_id: str,
        task_message: AgentMessage,
    ) -> AgentMessage:
        """Process a helper's subtask (simulated).

        Args:
            agent_id: ID of the helper agent.
            task_message: The task message.

        Returns:
            Response message from the helper.
        """
        subtask = task_message.content.get("subtask", {})
        task_type = subtask.get("type", "general")

        response = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.TASK_RESULT,
            sender_id=agent_id,
            recipient_id=task_message.sender_id,
            content={
                "status": "completed",
                "task_type": task_type,
                "proposal": f"Proposal from {agent_id} for {task_type}",
                "analysis": f"Analysis from {agent_id}",
            },
            correlation_id=task_message.message_id,
        )

        self._add_response(task_message.message_id, response)
        return response

    async def _process_critic_review(
        self,
        agent_id: str,
        review_request: AgentMessage,
    ) -> AgentMessage:
        """Process a critic's review (simulated).

        Args:
            agent_id: ID of the critic agent.
            review_request: The review request message.

        Returns:
            Critique response message.
        """
        response = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.ARTIFACT_CRITIQUE,
            sender_id=agent_id,
            recipient_id=review_request.sender_id,
            content={
                "status": "reviewed",
                "critique": "No critical issues found",
                "suggestions": [],
                "approved": True,
            },
            correlation_id=review_request.message_id,
        )

        self._add_response(review_request.message_id, response)
        return response
