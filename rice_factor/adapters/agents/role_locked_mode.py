"""Role-locked mode coordinator (Mode D).

Role-locked mode has specialized agents with fixed roles where each role
has a specific function in a structured workflow. Handoffs between roles
are explicit, and critic review is mandatory before artifact approval.

Best for:
- Enterprise/regulated environments
- Quality-critical work
- Compliance requirements
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from rice_factor.adapters.agents.base import BaseCoordinator
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


# Role workflow order - defines the sequence of handoffs
ROLE_WORKFLOW_ORDER: tuple[AgentRole, ...] = (
    AgentRole.PLANNER,
    AgentRole.DOMAIN_SPECIALIST,
    AgentRole.REFACTOR_ANALYST,
    AgentRole.TEST_STRATEGIST,
    AgentRole.PRIMARY,
    AgentRole.CRITIC,
)


class RoleLockedCoordinator(BaseCoordinator):
    """Coordinator for role-locked mode (fixed role workflow).

    In role-locked mode:
    - Each agent has a fixed, specialized role
    - Work flows through roles in a defined order
    - Handoffs between roles are explicit
    - Critic review is mandatory before completion
    - Only the primary agent can emit artifacts

    Workflow:
    1. Planner decomposes the task
    2. Domain specialists provide expertise
    3. Refactor analyst evaluates safety
    4. Test strategist evaluates test impact
    5. Primary synthesizes and drafts artifact
    6. Critic reviews (mandatory, can block)
    7. Primary finalizes if critic approves
    """

    def __init__(self, config: RunModeConfig) -> None:
        """Initialize the role-locked coordinator.

        Args:
            config: The run mode configuration.
        """
        super().__init__(config)
        self._workflow_state: dict[str, Any] = {}
        self._handoff_log: list[dict[str, str]] = []

    @property
    def mode_name(self) -> str:
        """Get the mode name."""
        return "role_locked"

    async def coordinate(
        self,
        context: CoordinationContext,
    ) -> CoordinationResult:
        """Execute coordination in role-locked mode.

        The coordination follows a strict role-based workflow:
        1. Each available role is invoked in order
        2. Output from each role is passed to the next
        3. Critic must approve before completion
        4. Primary emits final artifact

        Args:
            context: The coordination context with task details.

        Returns:
            CoordinationResult with the outcome.
        """
        start_time = time.time()
        session_id = self._generate_session_id()
        self._workflow_state = {}
        self._handoff_log = []

        try:
            # Get authority agent (must be primary)
            authority = self.get_authority_agent()

            # Step 1: Execute role-based workflow
            workflow_result = await self._execute_workflow(context)

            # Step 2: Mandatory critic review
            critic_result = await self._mandatory_critic_review(
                workflow_result, context
            )

            if not critic_result.get("approved", False):
                # Critic blocked the result
                duration_ms = int((time.time() - start_time) * 1000)
                return CoordinationResult(
                    session_id=session_id,
                    success=False,
                    participating_agents=tuple(self._agents.keys()),
                    messages_exchanged=self._get_messages_sent(),
                    final_decision=None,
                    reasoning=f"Critic blocked: {critic_result.get('reason', 'No reason provided')}",
                    errors=("Critic review failed",),
                    duration_ms=duration_ms,
                )

            # Step 3: Primary finalizes artifact
            final_result = await self._finalize_artifact(
                authority, workflow_result, critic_result, context
            )

            self._mark_task_completed(authority.agent_id)
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
                reasoning=self._compile_workflow_reasoning(),
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

    async def _execute_workflow(
        self,
        context: CoordinationContext,
    ) -> dict[str, Any]:
        """Execute the role-based workflow.

        Args:
            context: The coordination context.

        Returns:
            Accumulated workflow result from all roles.
        """
        workflow_output: dict[str, Any] = {
            "task_id": context.task_id,
            "goal": context.goal,
            "role_outputs": {},
        }

        # Execute each role in order (if available)
        for role in ROLE_WORKFLOW_ORDER:
            # Skip critic here - it's handled separately
            if role == AgentRole.CRITIC:
                continue

            agents_with_role = self._get_agents_by_role(role)
            if not agents_with_role:
                continue

            for agent in agents_with_role:
                role_output = await self._execute_role_task(
                    agent, role, workflow_output, context
                )
                workflow_output["role_outputs"][agent.agent_id] = role_output

                # Log handoff
                self._handoff_log.append({
                    "from": "system" if role == ROLE_WORKFLOW_ORDER[0] else "previous",
                    "to": agent.agent_id,
                    "role": role.value,
                })

                self._mark_task_completed(agent.agent_id)

        return workflow_output

    async def _execute_role_task(
        self,
        agent: Agent,
        role: AgentRole,
        current_state: dict[str, Any],
        context: CoordinationContext,
    ) -> dict[str, Any]:
        """Execute a task appropriate for the agent's role.

        Args:
            agent: The agent to execute the task.
            role: The agent's role.
            current_state: Current workflow state.
            context: The coordination context.

        Returns:
            Role-specific output.
        """
        # Create role-specific task
        task_content = self._create_role_task(role, current_state, context)

        task_msg = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.TASK_ASSIGNMENT,
            sender_id="system",
            recipient_id=agent.agent_id,
            content=task_content,
            correlation_id=context.task_id,
        )

        await self.send_message(task_msg)

        # Simulate role-specific processing
        return await self._process_role_task(agent, role, task_msg, context)

    def _create_role_task(
        self,
        role: AgentRole,
        current_state: dict[str, Any],
        context: CoordinationContext,
    ) -> dict[str, Any]:
        """Create a task appropriate for the role.

        Args:
            role: The agent's role.
            current_state: Current workflow state.
            context: The coordination context.

        Returns:
            Task content dict.
        """
        base_task = {
            "task_id": context.task_id,
            "goal": context.goal,
            "inputs": context.inputs,
            "constraints": context.constraints,
            "previous_outputs": current_state.get("role_outputs", {}),
        }

        if role == AgentRole.PLANNER:
            base_task["instruction"] = "Decompose this task into subtasks with dependencies"
            base_task["expected_output"] = "Task decomposition with execution order"

        elif role == AgentRole.DOMAIN_SPECIALIST:
            base_task["instruction"] = "Provide domain expertise relevant to this task"
            base_task["expected_output"] = "Domain-specific recommendations and constraints"

        elif role == AgentRole.REFACTOR_ANALYST:
            base_task["instruction"] = "Analyze safety and ripple effects of proposed changes"
            base_task["expected_output"] = "Safety assessment with risk factors"

        elif role == AgentRole.TEST_STRATEGIST:
            base_task["instruction"] = "Evaluate test coverage and identify testing gaps"
            base_task["expected_output"] = "Test strategy with coverage assessment"

        elif role == AgentRole.PRIMARY:
            base_task["instruction"] = "Synthesize all inputs and draft the final artifact"
            base_task["expected_output"] = "Draft artifact ready for review"

        else:
            base_task["instruction"] = f"Provide input as {role.value}"
            base_task["expected_output"] = "Role-specific contribution"

        return base_task

    async def _process_role_task(
        self,
        agent: Agent,
        role: AgentRole,
        task_msg: AgentMessage,
        context: CoordinationContext,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Process a role-specific task (simulated).

        Args:
            agent: The agent processing the task.
            role: The agent's role.
            task_msg: The task message.
            context: The coordination context.

        Returns:
            Role output dict.
        """
        # Simulate role-specific output
        output: dict[str, Any] = {
            "agent_id": agent.agent_id,
            "role": role.value,
            "status": "completed",
        }

        if role == AgentRole.PLANNER:
            output["subtasks"] = [
                {"id": "subtask-1", "description": "First step"},
                {"id": "subtask-2", "description": "Second step"},
            ]
            output["dependencies"] = {"subtask-2": ["subtask-1"]}

        elif role == AgentRole.DOMAIN_SPECIALIST:
            output["recommendations"] = ["Use established patterns", "Consider edge cases"]
            output["constraints"] = ["Must maintain backward compatibility"]

        elif role == AgentRole.REFACTOR_ANALYST:
            output["safety_assessment"] = "Low risk"
            output["ripple_effects"] = []
            output["risk_factors"] = []

        elif role == AgentRole.TEST_STRATEGIST:
            output["coverage_assessment"] = "Adequate coverage"
            output["testing_gaps"] = []
            output["recommended_tests"] = ["unit", "integration"]

        elif role == AgentRole.PRIMARY:
            output["artifact_draft"] = {
                "type": "draft",
                "content": "Synthesized artifact content",
            }

        # Create response message
        response = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.TASK_RESULT,
            sender_id=agent.agent_id,
            recipient_id="system",
            content=output,
            correlation_id=task_msg.message_id,
        )
        self._add_response(task_msg.message_id, response)

        return output

    async def _mandatory_critic_review(
        self,
        workflow_result: dict[str, Any],
        context: CoordinationContext,
    ) -> dict[str, Any]:
        """Execute mandatory critic review.

        In role-locked mode, critic review is always required.
        The critic can block the workflow if issues are found.

        Args:
            workflow_result: Result from the workflow execution.
            context: The coordination context.

        Returns:
            Critic review result with approval status.
        """
        critics = self._get_agents_by_role(AgentRole.CRITIC)

        if not critics:
            # No critic configured - this is a configuration error in role-locked mode
            # For safety, we block without explicit critic
            return {
                "approved": False,
                "reason": "No critic agent configured (required for role-locked mode)",
                "suggestions": ["Add a critic agent to the configuration"],
            }

        critic = critics[0]

        # Create review request
        review_msg = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.ARTIFACT_CRITIQUE,
            sender_id="system",
            recipient_id=critic.agent_id,
            content={
                "task_id": context.task_id,
                "goal": context.goal,
                "workflow_result": workflow_result,
                "role_outputs": workflow_result.get("role_outputs", {}),
                "instruction": "Review all role outputs and approve or block",
            },
            priority=MessagePriority.CRITICAL,
            correlation_id=context.task_id,
        )

        await self.send_message(review_msg)

        # Simulate critic review
        review_result = await self._process_critic_review(critic, review_msg)
        self._mark_task_completed(critic.agent_id)

        # Log handoff to critic
        self._handoff_log.append({
            "from": "workflow",
            "to": critic.agent_id,
            "role": "critic",
        })

        return review_result

    async def _process_critic_review(
        self,
        critic: Agent,
        review_msg: AgentMessage,
    ) -> dict[str, Any]:
        """Process critic review (simulated).

        Args:
            critic: The critic agent.
            review_msg: The review request message.

        Returns:
            Review result with approval status.
        """
        # In simulation, critic approves by default
        # In real implementation, this would invoke the LLM
        result = {
            "approved": True,
            "agent_id": critic.agent_id,
            "critique": "All role outputs are satisfactory",
            "suggestions": [],
            "blocking_issues": [],
        }

        # Create response message
        response = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.ARTIFACT_CRITIQUE,
            sender_id=critic.agent_id,
            recipient_id="system",
            content=result,
            correlation_id=review_msg.message_id,
        )
        self._add_response(review_msg.message_id, response)

        return result

    async def _finalize_artifact(
        self,
        authority: Agent,
        workflow_result: dict[str, Any],
        critic_result: dict[str, Any],
        context: CoordinationContext,
    ) -> dict[str, Any]:
        """Finalize the artifact after critic approval.

        Args:
            authority: The authority agent (primary).
            workflow_result: Accumulated workflow output.
            critic_result: Critic review result.
            context: The coordination context.

        Returns:
            Final result dict.
        """
        # Create finalization message
        finalize_msg = AgentMessage(
            message_id=self._generate_message_id(),
            message_type=MessageType.SYNTHESIS,
            sender_id="system",
            recipient_id=authority.agent_id,
            content={
                "task_id": context.task_id,
                "workflow_result": workflow_result,
                "critic_approval": critic_result,
                "instruction": "Finalize artifact based on critic-approved workflow",
            },
            correlation_id=context.task_id,
        )

        await self.send_message(finalize_msg)

        # Log final handoff
        self._handoff_log.append({
            "from": "critic",
            "to": authority.agent_id,
            "role": "primary",
        })

        return {
            "success": True,
            "decision": f"Artifact finalized for '{context.goal}'",
            "artifact_draft": workflow_result.get("role_outputs", {})
                .get(authority.agent_id, {})
                .get("artifact_draft"),
        }

    def _get_agents_by_role(self, role: AgentRole) -> list[Agent]:
        """Get all agents with a specific role.

        Args:
            role: The role to filter by.

        Returns:
            List of agents with that role.
        """
        return [
            agent for agent in self.get_active_agents()
            if agent.role == role
        ]

    def _compile_workflow_reasoning(self) -> str:
        """Compile reasoning from the workflow execution.

        Returns:
            Combined reasoning string.
        """
        parts = ["Role-Locked Workflow Execution:"]

        # Add handoff log
        parts.append("\nHandoff Log:")
        for handoff in self._handoff_log:
            parts.append(
                f"  {handoff['from']} -> {handoff['to']} ({handoff['role']})"
            )

        # Add role outputs summary
        if self._workflow_state:
            parts.append("\nRole Outputs:")
            role_outputs = self._workflow_state.get("role_outputs", {})
            for agent_id, output in role_outputs.items():
                role = output.get("role", "unknown")
                status = output.get("status", "unknown")
                parts.append(f"  [{role}] {agent_id}: {status}")

        return "\n".join(parts)

    def get_workflow_order(self) -> tuple[AgentRole, ...]:
        """Get the workflow role order.

        Returns:
            Tuple of roles in workflow order.
        """
        return ROLE_WORKFLOW_ORDER

    def get_handoff_log(self) -> list[dict[str, str]]:
        """Get the handoff log from the last coordination.

        Returns:
            List of handoff records.
        """
        return self._handoff_log.copy()
