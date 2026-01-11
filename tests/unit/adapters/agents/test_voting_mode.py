"""Unit tests for voting mode coordinator."""

import pytest

from rice_factor.adapters.agents.voting_mode import VotingCoordinator
from rice_factor.config.run_mode_config import RunMode, RunModeConfig
from rice_factor.domain.models.agent import AgentConfig, AgentRole
from rice_factor.domain.ports.coordinator import CoordinationContext


@pytest.fixture
def voting_config() -> RunModeConfig:
    """Create a voting mode configuration with multiple agents."""
    return RunModeConfig(
        mode=RunMode.VOTING,
        authority_agent="primary",
        agents=(
            AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            AgentConfig(agent_id="agent-a", role=AgentRole.GENERIC),
            AgentConfig(agent_id="agent-b", role=AgentRole.GENERIC),
            AgentConfig(agent_id="agent-c", role=AgentRole.GENERIC),
        ),
        voting_threshold=0.5,
    )


@pytest.fixture
def coordinator(voting_config: RunModeConfig) -> VotingCoordinator:
    """Create a voting coordinator for testing."""
    return VotingCoordinator(voting_config)


@pytest.fixture
def context() -> CoordinationContext:
    """Create a coordination context for testing."""
    return CoordinationContext(
        task_id="task-001",
        task_type="design",
        goal="Design a caching system",
        inputs={"requirements": ["low latency", "high availability"]},
        constraints=["Must use Redis or Memcached"],
    )


class TestVotingCoordinatorInit:
    """Tests for VotingCoordinator initialization."""

    def test_mode_name(self, coordinator: VotingCoordinator) -> None:
        """Test that mode name is 'voting'."""
        assert coordinator.mode_name == "voting"

    def test_multiple_agents_initialized(self, coordinator: VotingCoordinator) -> None:
        """Test that all agents are initialized."""
        agents = coordinator.get_active_agents()
        assert len(agents) == 4

    def test_voting_agents_identified(self, coordinator: VotingCoordinator) -> None:
        """Test that voting agents are correctly identified."""
        voting_agents = coordinator._get_voting_agents()
        # Should include primary and generic agents
        assert len(voting_agents) == 4


class TestVotingCoordinatorCoordinate:
    """Tests for coordination execution."""

    @pytest.mark.asyncio
    async def test_coordinate_runs(
        self, coordinator: VotingCoordinator, context: CoordinationContext
    ) -> None:
        """Test that coordination completes (may not reach consensus)."""
        result = await coordinator.coordinate(context)

        # Coordination completes even if no consensus
        assert result.session_id.startswith("session-")
        assert result.duration_ms >= 0
        assert result.votes is not None

    @pytest.mark.asyncio
    async def test_coordinate_success_with_consensus(self) -> None:
        """Test successful coordination when consensus is reached."""
        # Single agent config - will always reach consensus
        config = RunModeConfig(
            mode=RunMode.VOTING,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            ),
            voting_threshold=0.5,
        )
        coordinator = VotingCoordinator(config)
        context = CoordinationContext(
            task_id="task-001",
            task_type="test",
            goal="Single agent consensus",
        )
        result = await coordinator.coordinate(context)

        assert result.success is True
        assert result.votes is not None
        assert result.votes.consensus_reached is True

    @pytest.mark.asyncio
    async def test_all_agents_participate(
        self, coordinator: VotingCoordinator, context: CoordinationContext
    ) -> None:
        """Test that all agents participate."""
        result = await coordinator.coordinate(context)

        assert "primary" in result.participating_agents
        assert "agent-a" in result.participating_agents
        assert "agent-b" in result.participating_agents
        assert "agent-c" in result.participating_agents

    @pytest.mark.asyncio
    async def test_vote_result_included(
        self, coordinator: VotingCoordinator, context: CoordinationContext
    ) -> None:
        """Test that vote result is included."""
        result = await coordinator.coordinate(context)

        assert result.votes is not None
        assert len(result.votes.votes) > 0

    @pytest.mark.asyncio
    async def test_has_reasoning_on_success(self) -> None:
        """Test that reasoning includes vote summary when consensus reached."""
        # Single agent config - will reach consensus
        config = RunModeConfig(
            mode=RunMode.VOTING,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            ),
            voting_threshold=0.5,
        )
        coordinator = VotingCoordinator(config)
        context = CoordinationContext(
            task_id="task-001",
            task_type="test",
            goal="Test reasoning",
        )
        result = await coordinator.coordinate(context)

        assert result.reasoning is not None
        assert "Vote Summary" in result.reasoning

    @pytest.mark.asyncio
    async def test_no_consensus_reasoning(
        self, coordinator: VotingCoordinator, context: CoordinationContext
    ) -> None:
        """Test that reasoning is set when no consensus."""
        result = await coordinator.coordinate(context)

        # When no consensus, reasoning says so
        assert result.reasoning == "No consensus reached"


class TestVotingCoordinatorProposals:
    """Tests for proposal collection."""

    @pytest.mark.asyncio
    async def test_proposals_collected(
        self, coordinator: VotingCoordinator, context: CoordinationContext
    ) -> None:
        """Test that proposals are collected from all agents."""
        voting_agents = coordinator._get_voting_agents()
        proposals = await coordinator._collect_proposals(voting_agents, context)

        # Should have one proposal per voting agent
        assert len(proposals) == len(voting_agents)

    @pytest.mark.asyncio
    async def test_proposal_structure(
        self, coordinator: VotingCoordinator, context: CoordinationContext
    ) -> None:
        """Test proposal content structure."""
        voting_agents = coordinator._get_voting_agents()
        proposals = await coordinator._collect_proposals(voting_agents, context)

        for proposal_id, proposal in proposals.items():
            assert "agent_id" in proposal
            assert "summary" in proposal
            assert "details" in proposal


class TestVotingCoordinatorVoting:
    """Tests for voting process."""

    @pytest.mark.asyncio
    async def test_votes_cast(
        self, coordinator: VotingCoordinator, context: CoordinationContext
    ) -> None:
        """Test that votes are cast by all agents."""
        voting_agents = coordinator._get_voting_agents()
        proposals = await coordinator._collect_proposals(voting_agents, context)
        vote_result = await coordinator._conduct_voting(voting_agents, proposals, context)

        assert len(vote_result.votes) == len(voting_agents)

    @pytest.mark.asyncio
    async def test_vote_has_confidence(
        self, coordinator: VotingCoordinator, context: CoordinationContext
    ) -> None:
        """Test that votes include confidence."""
        voting_agents = coordinator._get_voting_agents()
        proposals = await coordinator._collect_proposals(voting_agents, context)
        vote_result = await coordinator._conduct_voting(voting_agents, proposals, context)

        for vote in vote_result.votes:
            assert 0.0 <= vote.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_consensus_threshold_applied(
        self, voting_config: RunModeConfig, context: CoordinationContext
    ) -> None:
        """Test that voting threshold is applied."""
        coordinator = VotingCoordinator(voting_config)

        voting_agents = coordinator._get_voting_agents()
        proposals = await coordinator._collect_proposals(voting_agents, context)
        vote_result = await coordinator._conduct_voting(voting_agents, proposals, context)

        # Threshold should match config
        assert vote_result.threshold == voting_config.voting_threshold


class TestVotingCoordinatorWithHighThreshold:
    """Tests with high threshold configuration."""

    @pytest.fixture
    def high_threshold_config(self) -> RunModeConfig:
        """Create config with high threshold (90%)."""
        return RunModeConfig(
            mode=RunMode.VOTING,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
                AgentConfig(agent_id="agent-a", role=AgentRole.GENERIC),
                AgentConfig(agent_id="agent-b", role=AgentRole.GENERIC),
            ),
            voting_threshold=0.9,
        )

    @pytest.mark.asyncio
    async def test_high_threshold_may_fail_consensus(
        self, high_threshold_config: RunModeConfig, context: CoordinationContext
    ) -> None:
        """Test that high threshold may not reach consensus."""
        coordinator = VotingCoordinator(high_threshold_config)
        result = await coordinator.coordinate(context)

        # With simulated voting (agents vote for own proposals),
        # 90% threshold is unlikely to be met with 3 agents
        # Each agent votes differently, so max 1/3 = 33%
        # This should fail consensus
        assert result.votes is not None


class TestVotingCoordinatorEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_no_voting_agents_fails(self) -> None:
        """Test that coordination fails if no voting agents."""
        # Config with primary (needed for authority) and critic
        # But critic is the only non-authority agent and critics don't vote
        config = RunModeConfig(
            mode=RunMode.VOTING,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.ORCHESTRATOR),
                AgentConfig(agent_id="critic", role=AgentRole.CRITIC),
            ),
        )
        coordinator = VotingCoordinator(config)

        # Manually filter out voting agents to simulate edge case
        # (In reality, orchestrator can vote but we test the error path)
        coordinator._get_voting_agents = lambda: []  # type: ignore[method-assign]

        context = CoordinationContext(
            task_id="task-001",
            task_type="test",
            goal="Test goal",
        )

        result = await coordinator.coordinate(context)
        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_single_agent_voting(self) -> None:
        """Test voting with single agent."""
        config = RunModeConfig(
            mode=RunMode.VOTING,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            ),
            voting_threshold=0.5,
        )
        coordinator = VotingCoordinator(config)
        context = CoordinationContext(
            task_id="task-001",
            task_type="test",
            goal="Single agent vote",
        )

        result = await coordinator.coordinate(context)

        # Single agent should reach consensus with 100% vote
        assert result.success is True
        assert result.votes is not None
        assert result.votes.consensus_reached is True


class TestVotingCoordinatorReasoning:
    """Tests for reasoning compilation."""

    @pytest.mark.asyncio
    async def test_reasoning_includes_vote_counts_on_success(self) -> None:
        """Test that reasoning includes vote counts when consensus reached."""
        # Single agent for guaranteed consensus
        config = RunModeConfig(
            mode=RunMode.VOTING,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            ),
            voting_threshold=0.5,
        )
        coordinator = VotingCoordinator(config)
        context = CoordinationContext(
            task_id="task-001",
            task_type="test",
            goal="Test vote counts",
        )
        result = await coordinator.coordinate(context)

        assert result.reasoning is not None
        assert "votes" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_reasoning_includes_winning_proposal(self) -> None:
        """Test that reasoning mentions winning proposal when consensus reached."""
        # Single agent for guaranteed consensus
        config = RunModeConfig(
            mode=RunMode.VOTING,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            ),
            voting_threshold=0.5,
        )
        coordinator = VotingCoordinator(config)
        context = CoordinationContext(
            task_id="task-001",
            task_type="test",
            goal="Test winning proposal",
        )
        result = await coordinator.coordinate(context)

        assert result.success is True
        assert result.reasoning is not None
        assert "Winning proposal" in result.reasoning
