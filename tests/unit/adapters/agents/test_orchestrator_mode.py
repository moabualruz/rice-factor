"""Unit tests for orchestrator mode coordinator."""

import pytest

from rice_factor.adapters.agents.orchestrator_mode import OrchestratorCoordinator
from rice_factor.config.run_mode_config import CoordinationRule, RunMode, RunModeConfig
from rice_factor.domain.models.agent import AgentConfig, AgentRole
from rice_factor.domain.ports.coordinator import CoordinationContext


@pytest.fixture
def orchestrator_config() -> RunModeConfig:
    """Create an orchestrator mode configuration with multiple agents."""
    return RunModeConfig(
        mode=RunMode.ORCHESTRATOR,
        authority_agent="orchestrator",
        agents=(
            AgentConfig(agent_id="orchestrator", role=AgentRole.ORCHESTRATOR),
            AgentConfig(agent_id="planner", role=AgentRole.PLANNER),
            AgentConfig(agent_id="critic", role=AgentRole.CRITIC),
        ),
        rules=frozenset({CoordinationRule.ONLY_PRIMARY_EMITS_ARTIFACTS}),
    )


@pytest.fixture
def config_with_mandatory_review() -> RunModeConfig:
    """Create config with mandatory critic review."""
    return RunModeConfig(
        mode=RunMode.ORCHESTRATOR,
        authority_agent="orchestrator",
        agents=(
            AgentConfig(agent_id="orchestrator", role=AgentRole.ORCHESTRATOR),
            AgentConfig(agent_id="planner", role=AgentRole.PLANNER),
            AgentConfig(agent_id="critic", role=AgentRole.CRITIC),
        ),
        rules=frozenset({
            CoordinationRule.ONLY_PRIMARY_EMITS_ARTIFACTS,
            CoordinationRule.MANDATORY_CRITIC_REVIEW,
        }),
    )


@pytest.fixture
def coordinator(orchestrator_config: RunModeConfig) -> OrchestratorCoordinator:
    """Create an orchestrator coordinator for testing."""
    return OrchestratorCoordinator(orchestrator_config)


@pytest.fixture
def context() -> CoordinationContext:
    """Create a coordination context for testing."""
    return CoordinationContext(
        task_id="task-001",
        task_type="plan_project",
        goal="Design a microservices architecture",
        inputs={"services": ["auth", "users", "orders"]},
        constraints=["Use Kubernetes", "Event-driven"],
    )


class TestOrchestratorCoordinatorInit:
    """Tests for OrchestratorCoordinator initialization."""

    def test_mode_name(self, coordinator: OrchestratorCoordinator) -> None:
        """Test that mode name is 'orchestrator'."""
        assert coordinator.mode_name == "orchestrator"

    def test_multiple_agents_initialized(self, coordinator: OrchestratorCoordinator) -> None:
        """Test that all agents are initialized."""
        agents = coordinator.get_active_agents()
        assert len(agents) == 3

    def test_authority_agent_is_orchestrator(self, coordinator: OrchestratorCoordinator) -> None:
        """Test that authority agent is the orchestrator."""
        authority = coordinator.get_authority_agent()
        assert authority.agent_id == "orchestrator"
        assert authority.role == AgentRole.ORCHESTRATOR


class TestOrchestratorCoordinatorCoordinate:
    """Tests for coordination execution."""

    @pytest.mark.asyncio
    async def test_coordinate_success(
        self, coordinator: OrchestratorCoordinator, context: CoordinationContext
    ) -> None:
        """Test successful coordination."""
        result = await coordinator.coordinate(context)

        assert result.success is True
        assert result.session_id.startswith("session-")
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_all_agents_participate(
        self, coordinator: OrchestratorCoordinator, context: CoordinationContext
    ) -> None:
        """Test that all agents participate."""
        result = await coordinator.coordinate(context)

        # All agents should be in participating list
        assert "orchestrator" in result.participating_agents
        assert "planner" in result.participating_agents
        assert "critic" in result.participating_agents

    @pytest.mark.asyncio
    async def test_multiple_messages_exchanged(
        self, coordinator: OrchestratorCoordinator, context: CoordinationContext
    ) -> None:
        """Test that multiple messages are exchanged."""
        result = await coordinator.coordinate(context)

        # Should have at least: initial task + delegation + synthesis
        assert result.messages_exchanged >= 3

    @pytest.mark.asyncio
    async def test_has_decision(
        self, coordinator: OrchestratorCoordinator, context: CoordinationContext
    ) -> None:
        """Test that coordination produces a decision."""
        result = await coordinator.coordinate(context)

        assert result.final_decision is not None
        assert "microservices" in result.final_decision

    @pytest.mark.asyncio
    async def test_has_reasoning(
        self, coordinator: OrchestratorCoordinator, context: CoordinationContext
    ) -> None:
        """Test that coordination includes reasoning from helpers."""
        result = await coordinator.coordinate(context)

        assert result.reasoning is not None
        # Should include contributions from helpers
        assert "planner" in result.reasoning


class TestOrchestratorCoordinatorDelegation:
    """Tests for delegation functionality."""

    @pytest.mark.asyncio
    async def test_delegation_plan_created(
        self, coordinator: OrchestratorCoordinator, context: CoordinationContext
    ) -> None:
        """Test that delegation plan is created."""
        orchestrator = coordinator.get_authority_agent()
        plan = await coordinator._plan_delegation(orchestrator, context)

        assert "subtasks" in plan
        assert "assignments" in plan
        # Should have assignments for non-critic helpers
        assert "planner" in plan["assignments"]

    @pytest.mark.asyncio
    async def test_planner_gets_decompose_task(
        self, coordinator: OrchestratorCoordinator, context: CoordinationContext
    ) -> None:
        """Test that planner gets decomposition task."""
        planner = coordinator._agents["planner"]
        subtask = coordinator._create_subtask_for_helper(planner, context)

        assert subtask is not None
        assert subtask["type"] == "decompose"

    @pytest.mark.asyncio
    async def test_critic_excluded_from_initial_delegation(
        self, coordinator: OrchestratorCoordinator, context: CoordinationContext
    ) -> None:
        """Test that critic is excluded from initial delegation."""
        critic = coordinator._agents["critic"]
        subtask = coordinator._create_subtask_for_helper(critic, context)

        # Critic should not get subtask in delegation phase
        assert subtask is None


class TestOrchestratorCoordinatorCriticReview:
    """Tests for critic review functionality."""

    @pytest.mark.asyncio
    async def test_critic_review_when_mandatory(
        self, config_with_mandatory_review: RunModeConfig, context: CoordinationContext
    ) -> None:
        """Test that critic review happens when mandatory."""
        coordinator = OrchestratorCoordinator(config_with_mandatory_review)

        assert coordinator._requires_critic_review() is True

    @pytest.mark.asyncio
    async def test_no_critic_review_when_not_required(
        self, coordinator: OrchestratorCoordinator
    ) -> None:
        """Test that critic review is not required by default."""
        # Default config doesn't have mandatory review
        assert coordinator._requires_critic_review() is False


class TestOrchestratorCoordinatorHelpers:
    """Tests for helper-related functionality."""

    def test_get_helper_agents(self, coordinator: OrchestratorCoordinator) -> None:
        """Test getting non-orchestrator agents."""
        helpers = coordinator._get_helper_agents()

        # Should not include orchestrator
        helper_ids = [h.agent_id for h in helpers]
        assert "orchestrator" not in helper_ids
        assert "planner" in helper_ids
        assert "critic" in helper_ids

    @pytest.mark.asyncio
    async def test_tasks_marked_completed_for_helpers(
        self, coordinator: OrchestratorCoordinator, context: CoordinationContext
    ) -> None:
        """Test that helper tasks are marked completed."""
        await coordinator.coordinate(context)

        # Planner should have task count incremented
        planner_count = coordinator._agents["planner"].task_count
        assert planner_count >= 1


class TestOrchestratorWithSpecialists:
    """Tests with specialized agents."""

    @pytest.fixture
    def config_with_specialists(self) -> RunModeConfig:
        """Create config with specialist agents."""
        return RunModeConfig(
            mode=RunMode.ORCHESTRATOR,
            authority_agent="orchestrator",
            agents=(
                AgentConfig(agent_id="orchestrator", role=AgentRole.ORCHESTRATOR),
                AgentConfig(
                    agent_id="security-expert",
                    role=AgentRole.DOMAIN_SPECIALIST,
                    scope="security",
                ),
                AgentConfig(agent_id="refactor-analyst", role=AgentRole.REFACTOR_ANALYST),
                AgentConfig(agent_id="test-strategist", role=AgentRole.TEST_STRATEGIST),
            ),
        )

    @pytest.mark.asyncio
    async def test_specialist_gets_scoped_task(
        self, config_with_specialists: RunModeConfig
    ) -> None:
        """Test that specialist gets task matching their scope."""
        coordinator = OrchestratorCoordinator(config_with_specialists)
        context = CoordinationContext(
            task_id="task-001",
            task_type="refactor",
            goal="Refactor authentication module",
        )

        specialist = coordinator._agents["security-expert"]
        subtask = coordinator._create_subtask_for_helper(specialist, context)

        assert subtask is not None
        assert subtask["type"] == "analyze"
        assert "security" in subtask["instruction"]

    @pytest.mark.asyncio
    async def test_refactor_analyst_gets_safety_task(
        self, config_with_specialists: RunModeConfig
    ) -> None:
        """Test that refactor analyst gets safety analysis task."""
        coordinator = OrchestratorCoordinator(config_with_specialists)
        context = CoordinationContext(
            task_id="task-001",
            task_type="refactor",
            goal="Rename function",
        )

        analyst = coordinator._agents["refactor-analyst"]
        subtask = coordinator._create_subtask_for_helper(analyst, context)

        assert subtask is not None
        assert subtask["type"] == "safety_analysis"

    @pytest.mark.asyncio
    async def test_test_strategist_gets_test_task(
        self, config_with_specialists: RunModeConfig
    ) -> None:
        """Test that test strategist gets test evaluation task."""
        coordinator = OrchestratorCoordinator(config_with_specialists)
        context = CoordinationContext(
            task_id="task-001",
            task_type="implement",
            goal="Implement new feature",
        )

        strategist = coordinator._agents["test-strategist"]
        subtask = coordinator._create_subtask_for_helper(strategist, context)

        assert subtask is not None
        assert subtask["type"] == "test_evaluation"


class TestOrchestratorErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_missing_authority_agent_raises(self) -> None:
        """Test that missing authority agent raises error."""
        config = RunModeConfig(
            mode=RunMode.ORCHESTRATOR,
            authority_agent="orchestrator",
            agents=(
                AgentConfig(agent_id="orchestrator", role=AgentRole.ORCHESTRATOR),
            ),
        )
        coordinator = OrchestratorCoordinator(config)

        # Manually remove the agent to simulate issue
        del coordinator._agents["orchestrator"]

        context = CoordinationContext(
            task_id="task-001",
            task_type="test",
            goal="Test goal",
        )

        result = await coordinator.coordinate(context)
        assert result.success is False
        assert len(result.errors) > 0
