"""Voting mode coordinator (Mode C).

Voting mode uses multiple agents to generate candidate proposals,
then selects the best one through a voting process.

Best for:
- Exploring different approaches
- Reducing bias from single perspective
- Complex decisions with multiple valid solutions
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from rice_factor.adapters.agents.base import BaseCoordinator
from rice_factor.domain.models.agent import Agent, AgentRole
from rice_factor.domain.models.messages import (
    AgentMessage,
    CoordinationResult,
    MessageType,
    Vote,
    VoteResult,
)
from rice_factor.domain.ports.coordinator import CoordinationContext  # noqa: TC001

if TYPE_CHECKING:
    from rice_factor.config.run_mode_config import RunModeConfig


class VotingCoordinator(BaseCoordinator):
    """Coordinator for voting mode (consensus through voting).

    In voting mode:
    - N identical or similar agents generate proposals
    - Proposals are collected and compared
    - Agents vote on the best proposal
    - Winner is selected based on threshold

    Selection strategies:
    - Majority vote
    - Weighted by confidence
    - Threshold-based consensus
    """

    def __init__(self, config: RunModeConfig) -> None:
        """Initialize the voting coordinator.

        Args:
            config: The run mode configuration.
        """
        super().__init__(config)
        self._proposals: dict[str, dict[str, Any]] = {}
        self._votes: list[Vote] = []

    @property
    def mode_name(self) -> str:
        """Get the mode name."""
        return "voting"

    async def coordinate(
        self,
        context: CoordinationContext,
    ) -> CoordinationResult:
        """Execute coordination in voting mode.

        The voting process:
        1. All voting agents generate proposals
        2. Proposals are collected
        3. Agents vote on proposals
        4. Winner is determined by threshold
        5. Authority agent finalizes result

        Args:
            context: The coordination context with task details.

        Returns:
            CoordinationResult with the outcome.
        """
        start_time = time.time()
        session_id = self._generate_session_id()
        self._proposals = {}
        self._votes = []

        try:
            # Get voting agents
            voting_agents = self._get_voting_agents()
            if not voting_agents:
                raise ValueError("No voting agents available")

            # Step 1: Collect proposals from all agents
            proposals = await self._collect_proposals(voting_agents, context)

            # Step 2: Conduct voting
            vote_result = await self._conduct_voting(voting_agents, proposals, context)

            # Step 3: Determine winner
            if vote_result.consensus_reached and vote_result.winner:
                winning_proposal = proposals.get(vote_result.winner)
                final_decision = winning_proposal.get("summary", vote_result.winner) if winning_proposal else vote_result.winner
                reasoning = self._compile_reasoning(vote_result, proposals)
                success = True
            else:
                final_decision = None
                reasoning = "No consensus reached"
                success = False

            duration_ms = int((time.time() - start_time) * 1000)

            return CoordinationResult(
                session_id=session_id,
                success=success,
                participating_agents=tuple(a.agent_id for a in voting_agents),
                messages_exchanged=self._get_messages_sent(),
                votes=vote_result,
                final_decision=final_decision,
                reasoning=reasoning,
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

    async def _collect_proposals(
        self,
        voting_agents: list[Agent],
        context: CoordinationContext,
    ) -> dict[str, dict[str, Any]]:
        """Collect proposals from all voting agents.

        Args:
            voting_agents: Agents that will generate proposals.
            context: The coordination context.

        Returns:
            Dict mapping proposal IDs to proposal content.
        """
        proposals: dict[str, dict[str, Any]] = {}

        for agent in voting_agents:
            # Create proposal request
            request_msg = AgentMessage(
                message_id=self._generate_message_id(),
                message_type=MessageType.TASK_ASSIGNMENT,
                sender_id="system",
                recipient_id=agent.agent_id,
                content={
                    "task_id": context.task_id,
                    "task_type": context.task_type,
                    "goal": context.goal,
                    "inputs": context.inputs,
                    "constraints": context.constraints,
                    "request": "Generate a proposal for this task",
                },
            )

            await self.send_message(request_msg)

            # Simulate agent processing
            proposal = await self._generate_proposal(agent, context)
            proposal_id = f"proposal-{agent.agent_id}"
            proposals[proposal_id] = proposal
            self._proposals[proposal_id] = proposal
            self._mark_task_completed(agent.agent_id)

        return proposals

    async def _conduct_voting(
        self,
        voting_agents: list[Agent],
        proposals: dict[str, dict[str, Any]],
        context: CoordinationContext,
    ) -> VoteResult:
        """Conduct voting on the collected proposals.

        Args:
            voting_agents: Agents that will vote.
            proposals: Available proposals to vote on.
            context: The coordination context.

        Returns:
            VoteResult with tallied votes.
        """
        votes: list[Vote] = []
        proposal_ids = list(proposals.keys())

        for agent in voting_agents:
            # Create vote request
            vote_request = AgentMessage(
                message_id=self._generate_message_id(),
                message_type=MessageType.VOTE_REQUEST,
                sender_id="system",
                recipient_id=agent.agent_id,
                content={
                    "task_id": context.task_id,
                    "proposals": {
                        pid: p.get("summary", "No summary")
                        for pid, p in proposals.items()
                    },
                    "request": "Vote for the best proposal",
                },
            )

            await self.send_message(vote_request)

            # Simulate agent voting
            vote = await self._cast_vote(agent, proposal_ids, context)
            votes.append(vote)
            self._votes.append(vote)

        return VoteResult.from_votes(votes, threshold=self._config.voting_threshold)

    async def _generate_proposal(
        self,
        agent: Agent,
        context: CoordinationContext,
    ) -> dict[str, Any]:
        """Generate a proposal (simulated).

        Args:
            agent: The agent generating the proposal.
            context: The coordination context.

        Returns:
            Proposal dict with content.
        """
        # In a real implementation, this would call the LLM
        return {
            "agent_id": agent.agent_id,
            "summary": f"Proposal from {agent.agent_id} for '{context.goal}'",
            "details": f"Detailed plan from {agent.agent_id}",
            "approach": f"Approach suggested by {agent.agent_id}",
        }

    async def _cast_vote(
        self,
        agent: Agent,
        proposal_ids: list[str],
        context: CoordinationContext,  # noqa: ARG002
    ) -> Vote:
        """Cast a vote (simulated).

        In a real implementation, the agent would evaluate all proposals
        and vote based on criteria.

        Args:
            agent: The voting agent.
            proposal_ids: Available proposals to vote for.
            context: The coordination context.

        Returns:
            Vote from the agent.
        """
        # Simulate voting - in reality, agent would evaluate proposals
        # For simulation, agents vote for their own proposal if available,
        # otherwise the first proposal
        own_proposal = f"proposal-{agent.agent_id}"
        if own_proposal in proposal_ids:
            choice = own_proposal
            confidence = 0.9
        else:
            choice = proposal_ids[0] if proposal_ids else ""
            confidence = 0.7

        return Vote(
            agent_id=agent.agent_id,
            choice=choice,
            confidence=confidence,
            reasoning=f"{agent.agent_id} voted for {choice}",
        )

    def _get_voting_agents(self) -> list[Agent]:
        """Get all agents that can vote.

        Returns:
            List of voting-capable agents.
        """
        # In voting mode, generic agents and primary can vote
        # Exclude critics as they review rather than propose
        return [
            agent for agent in self.get_active_agents()
            if agent.role in (AgentRole.GENERIC, AgentRole.PRIMARY, AgentRole.PLANNER)
        ]

    def _compile_reasoning(
        self,
        vote_result: VoteResult,
        proposals: dict[str, dict[str, Any]],
    ) -> str:
        """Compile reasoning from votes and proposals.

        Args:
            vote_result: The voting result.
            proposals: The proposals that were voted on.

        Returns:
            Combined reasoning string.
        """
        parts = []

        # Summarize vote counts
        parts.append("Vote Summary:")
        for choice, count in vote_result.vote_counts.items():
            parts.append(f"  {choice}: {count} votes")

        # Add winning proposal details
        if vote_result.winner:
            winning = proposals.get(vote_result.winner, {})
            parts.append(f"\nWinning proposal: {vote_result.winner}")
            if summary := winning.get("summary"):
                parts.append(f"Summary: {summary}")
            parts.append(f"Total confidence: {vote_result.total_confidence:.2f}")

        # Add vote reasoning
        parts.append("\nIndividual votes:")
        for vote in vote_result.votes:
            if vote.reasoning:
                parts.append(f"  {vote.agent_id}: {vote.reasoning}")

        return "\n".join(parts)
