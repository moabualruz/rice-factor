"""Unit tests for role-locked mode coordinator."""

import pytest

from rice_factor.adapters.agents.role_locked_mode import (
    ROLE_WORKFLOW_ORDER,
    RoleLockedCoordinator,
)
from rice_factor.config.run_mode_config import RunMode, RunModeConfig
from rice_factor.domain.models.agent import AgentConfig, AgentRole
from rice_factor.domain.ports.coordinator import CoordinationContext


@pytest.fixture
def full_config() -> RunModeConfig:
    """Create a role-locked mode configuration with all roles."""
    return RunModeConfig(
        mode=RunMode.ROLE_LOCKED,
        authority_agent="primary",
        agents=(
            AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            AgentConfig(agent_id="planner", role=AgentRole.PLANNER),
            AgentConfig(agent_id="domain-expert", role=AgentRole.DOMAIN_SPECIALIST),
            AgentConfig(agent_id="refactor-analyst", role=AgentRole.REFACTOR_ANALYST),
            AgentConfig(agent_id="test-strategist", role=AgentRole.TEST_STRATEGIST),
            AgentConfig(agent_id="critic", role=AgentRole.CRITIC),
        ),
    )


@pytest.fixture
def minimal_config() -> RunModeConfig:
    """Create a minimal role-locked config with just primary and critic."""
    return RunModeConfig(
        mode=RunMode.ROLE_LOCKED,
        authority_agent="primary",
        agents=(
            AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            AgentConfig(agent_id="critic", role=AgentRole.CRITIC),
        ),
    )


@pytest.fixture
def coordinator(full_config: RunModeConfig) -> RoleLockedCoordinator:
    """Create a role-locked coordinator for testing."""
    return RoleLockedCoordinator(full_config)


@pytest.fixture
def context() -> CoordinationContext:
    """Create a coordination context for testing."""
    return CoordinationContext(
        task_id="task-001",
        task_type="implementation",
        goal="Implement feature X",
        inputs={"requirements": ["req1", "req2"]},
        constraints=["Must be backward compatible"],
    )


class TestRoleLockedCoordinatorInit:
    """Tests for RoleLockedCoordinator initialization."""

    def test_mode_name(self, coordinator: RoleLockedCoordinator) -> None:
        """Test that mode name is 'role_locked'."""
        assert coordinator.mode_name == "role_locked"

    def test_all_agents_initialized(self, coordinator: RoleLockedCoordinator) -> None:
        """Test that all agents are initialized."""
        agents = coordinator.get_active_agents()
        assert len(agents) == 6

    def test_workflow_order_defined(self) -> None:
        """Test that workflow order is defined."""
        assert len(ROLE_WORKFLOW_ORDER) > 0
        assert AgentRole.PLANNER in ROLE_WORKFLOW_ORDER
        assert AgentRole.CRITIC in ROLE_WORKFLOW_ORDER
        assert AgentRole.PRIMARY in ROLE_WORKFLOW_ORDER

    def test_get_workflow_order(self, coordinator: RoleLockedCoordinator) -> None:
        """Test getting workflow order."""
        order = coordinator.get_workflow_order()
        assert order == ROLE_WORKFLOW_ORDER


class TestRoleLockedCoordinatorCoordinate:
    """Tests for coordination execution."""

    @pytest.mark.asyncio
    async def test_coordinate_success(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test successful coordination with all roles."""
        result = await coordinator.coordinate(context)

        assert result.success is True
        assert result.session_id.startswith("session-")
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_all_agents_participate(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test that all agents participate in coordination."""
        result = await coordinator.coordinate(context)

        # All 6 agents should participate
        assert len(result.participating_agents) == 6
        assert "primary" in result.participating_agents
        assert "critic" in result.participating_agents

    @pytest.mark.asyncio
    async def test_messages_exchanged(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test that messages are exchanged during coordination."""
        result = await coordinator.coordinate(context)

        # Should have multiple messages (one per role + critic + finalize)
        assert result.messages_exchanged > 0

    @pytest.mark.asyncio
    async def test_reasoning_includes_workflow(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test that reasoning includes workflow information."""
        result = await coordinator.coordinate(context)

        assert result.reasoning is not None
        assert "Role-Locked" in result.reasoning
        assert "Handoff" in result.reasoning

    @pytest.mark.asyncio
    async def test_final_decision_set(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test that final decision is set on success."""
        result = await coordinator.coordinate(context)

        assert result.final_decision is not None
        assert "finalized" in result.final_decision.lower()


class TestRoleLockedCoordinatorWorkflow:
    """Tests for workflow execution."""

    @pytest.mark.asyncio
    async def test_handoff_log_recorded(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test that handoffs are logged."""
        await coordinator.coordinate(context)

        handoff_log = coordinator.get_handoff_log()
        assert len(handoff_log) > 0

    @pytest.mark.asyncio
    async def test_handoff_log_has_required_fields(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test that handoff log entries have required fields."""
        await coordinator.coordinate(context)

        handoff_log = coordinator.get_handoff_log()
        for entry in handoff_log:
            assert "from" in entry
            assert "to" in entry
            assert "role" in entry

    @pytest.mark.asyncio
    async def test_critic_handoff_recorded(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test that handoff to critic is recorded."""
        await coordinator.coordinate(context)

        handoff_log = coordinator.get_handoff_log()
        critic_handoffs = [h for h in handoff_log if h["role"] == "critic"]
        assert len(critic_handoffs) >= 1

    @pytest.mark.asyncio
    async def test_minimal_config_works(
        self, minimal_config: RunModeConfig, context: CoordinationContext
    ) -> None:
        """Test that minimal config (primary + critic) works."""
        coordinator = RoleLockedCoordinator(minimal_config)
        result = await coordinator.coordinate(context)

        assert result.success is True


class TestRoleLockedCoordinatorCriticReview:
    """Tests for mandatory critic review."""

    @pytest.mark.asyncio
    async def test_critic_review_occurs(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test that critic review is executed."""
        await coordinator.coordinate(context)

        handoff_log = coordinator.get_handoff_log()
        critic_entries = [h for h in handoff_log if h["to"] == "critic"]
        assert len(critic_entries) >= 1

    @pytest.mark.asyncio
    async def test_no_critic_fails(self, context: CoordinationContext) -> None:
        """Test that missing critic causes failure."""
        # Config without critic
        config = RunModeConfig(
            mode=RunMode.ROLE_LOCKED,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            ),
        )
        coordinator = RoleLockedCoordinator(config)
        result = await coordinator.coordinate(context)

        # Should fail due to missing critic
        assert result.success is False
        assert "critic" in result.reasoning.lower()


class TestRoleLockedCoordinatorRoleTasks:
    """Tests for role-specific task creation."""

    def test_get_agents_by_role(self, coordinator: RoleLockedCoordinator) -> None:
        """Test getting agents by role."""
        planners = coordinator._get_agents_by_role(AgentRole.PLANNER)
        assert len(planners) == 1
        assert planners[0].role == AgentRole.PLANNER

    def test_get_agents_by_role_empty(
        self, coordinator: RoleLockedCoordinator
    ) -> None:
        """Test getting agents for a role with no agents."""
        orchestrators = coordinator._get_agents_by_role(AgentRole.ORCHESTRATOR)
        assert len(orchestrators) == 0

    def test_create_role_task_planner(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test task creation for planner role."""
        task = coordinator._create_role_task(
            AgentRole.PLANNER, {}, context
        )
        assert "decompose" in task["instruction"].lower()
        assert task["task_id"] == context.task_id

    def test_create_role_task_domain_specialist(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test task creation for domain specialist role."""
        task = coordinator._create_role_task(
            AgentRole.DOMAIN_SPECIALIST, {}, context
        )
        assert "domain" in task["instruction"].lower()

    def test_create_role_task_refactor_analyst(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test task creation for refactor analyst role."""
        task = coordinator._create_role_task(
            AgentRole.REFACTOR_ANALYST, {}, context
        )
        assert "safety" in task["instruction"].lower()

    def test_create_role_task_test_strategist(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test task creation for test strategist role."""
        task = coordinator._create_role_task(
            AgentRole.TEST_STRATEGIST, {}, context
        )
        assert "test" in task["instruction"].lower()

    def test_create_role_task_primary(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test task creation for primary role."""
        task = coordinator._create_role_task(
            AgentRole.PRIMARY, {}, context
        )
        assert "synthesize" in task["instruction"].lower()


class TestRoleLockedCoordinatorErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_exception_returns_failure(
        self, context: CoordinationContext
    ) -> None:
        """Test that exceptions are handled gracefully."""
        config = RunModeConfig(
            mode=RunMode.ROLE_LOCKED,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
                AgentConfig(agent_id="critic", role=AgentRole.CRITIC),
            ),
        )
        coordinator = RoleLockedCoordinator(config)

        # Mock to raise exception
        async def raise_error(ctx: CoordinationContext) -> dict:
            raise RuntimeError("Test error")

        coordinator._execute_workflow = raise_error  # type: ignore[method-assign]

        result = await coordinator.coordinate(context)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Test error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_duration_recorded_on_failure(
        self, context: CoordinationContext
    ) -> None:
        """Test that duration is recorded even on failure."""
        config = RunModeConfig(
            mode=RunMode.ROLE_LOCKED,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            ),
        )
        coordinator = RoleLockedCoordinator(config)
        result = await coordinator.coordinate(context)

        assert result.duration_ms >= 0


class TestRoleLockedCoordinatorReasoning:
    """Tests for reasoning compilation."""

    @pytest.mark.asyncio
    async def test_reasoning_includes_handoff_log(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test that reasoning includes handoff log."""
        result = await coordinator.coordinate(context)

        assert "Handoff Log:" in result.reasoning

    @pytest.mark.asyncio
    async def test_reasoning_format(
        self, coordinator: RoleLockedCoordinator, context: CoordinationContext
    ) -> None:
        """Test reasoning format."""
        result = await coordinator.coordinate(context)

        # Should have structured format
        lines = result.reasoning.split("\n")
        assert lines[0] == "Role-Locked Workflow Execution:"
