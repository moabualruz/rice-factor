"""Unit tests for solo mode coordinator."""

import pytest

from rice_factor.adapters.agents.solo_mode import SoloCoordinator
from rice_factor.config.run_mode_config import RunMode, RunModeConfig
from rice_factor.domain.models.agent import AgentConfig, AgentRole
from rice_factor.domain.ports.coordinator import CoordinationContext


@pytest.fixture
def solo_config() -> RunModeConfig:
    """Create a solo mode configuration."""
    return RunModeConfig.solo_mode()


@pytest.fixture
def coordinator(solo_config: RunModeConfig) -> SoloCoordinator:
    """Create a solo coordinator for testing."""
    return SoloCoordinator(solo_config)


@pytest.fixture
def context() -> CoordinationContext:
    """Create a coordination context for testing."""
    return CoordinationContext(
        task_id="task-001",
        task_type="plan_project",
        goal="Create a new REST API",
        inputs={"language": "python"},
        constraints=["Use FastAPI"],
    )


class TestSoloCoordinatorInit:
    """Tests for SoloCoordinator initialization."""

    def test_mode_name(self, coordinator: SoloCoordinator) -> None:
        """Test that mode name is 'solo'."""
        assert coordinator.mode_name == "solo"

    def test_config_stored(self, coordinator: SoloCoordinator, solo_config: RunModeConfig) -> None:
        """Test that config is stored."""
        assert coordinator.config == solo_config

    def test_agents_initialized(self, coordinator: SoloCoordinator) -> None:
        """Test that agents are initialized from config."""
        agents = coordinator.get_active_agents()
        assert len(agents) == 1
        assert agents[0].role == AgentRole.PRIMARY

    def test_authority_agent(self, coordinator: SoloCoordinator) -> None:
        """Test getting the authority agent."""
        authority = coordinator.get_authority_agent()
        assert authority.agent_id == "primary"
        assert authority.role == AgentRole.PRIMARY


class TestSoloCoordinatorValidation:
    """Tests for authority validation."""

    def test_validate_authority_correct(self, coordinator: SoloCoordinator) -> None:
        """Test authority validation for correct agent."""
        assert coordinator.validate_authority("primary") is True

    def test_validate_authority_incorrect(self, coordinator: SoloCoordinator) -> None:
        """Test authority validation for incorrect agent."""
        assert coordinator.validate_authority("other") is False


class TestSoloCoordinatorCoordinate:
    """Tests for coordination execution."""

    @pytest.mark.asyncio
    async def test_coordinate_success(
        self, coordinator: SoloCoordinator, context: CoordinationContext
    ) -> None:
        """Test successful coordination."""
        result = await coordinator.coordinate(context)

        assert result.success is True
        assert result.session_id.startswith("session-")
        assert "primary" in result.participating_agents
        assert result.messages_exchanged >= 1
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_coordinate_has_decision(
        self, coordinator: SoloCoordinator, context: CoordinationContext
    ) -> None:
        """Test that coordination produces a decision."""
        result = await coordinator.coordinate(context)

        assert result.final_decision is not None
        assert "REST API" in result.final_decision

    @pytest.mark.asyncio
    async def test_coordinate_has_reasoning(
        self, coordinator: SoloCoordinator, context: CoordinationContext
    ) -> None:
        """Test that coordination includes reasoning."""
        result = await coordinator.coordinate(context)

        assert result.reasoning is not None
        assert "Solo" in result.reasoning


class TestSoloCoordinatorMessaging:
    """Tests for message handling."""

    @pytest.mark.asyncio
    async def test_messages_sent(
        self, coordinator: SoloCoordinator, context: CoordinationContext
    ) -> None:
        """Test that messages are recorded."""
        await coordinator.coordinate(context)

        # At minimum: task assignment + task result
        messages_sent = coordinator._get_messages_sent()
        assert messages_sent >= 1

    @pytest.mark.asyncio
    async def test_task_marked_completed(
        self, coordinator: SoloCoordinator, context: CoordinationContext
    ) -> None:
        """Test that agent's task is marked completed."""
        # Get initial task count
        initial_count = coordinator._agents["primary"].task_count

        await coordinator.coordinate(context)

        # Task count should increment
        final_count = coordinator._agents["primary"].task_count
        assert final_count == initial_count + 1


class TestSoloCoordinatorWithCustomConfig:
    """Tests with custom configurations."""

    @pytest.mark.asyncio
    async def test_with_custom_model(self) -> None:
        """Test coordinator with custom model in config."""
        config = RunModeConfig.solo_mode(model="claude-3-opus")
        coordinator = SoloCoordinator(config)
        context = CoordinationContext(
            task_id="task-002",
            task_type="refactor",
            goal="Refactor module",
        )

        result = await coordinator.coordinate(context)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_with_explicit_config(self) -> None:
        """Test coordinator with explicit agent config."""
        agent = AgentConfig(
            agent_id="custom-primary",
            role=AgentRole.PRIMARY,
            model="gpt-4",
        )
        config = RunModeConfig(
            mode=RunMode.SOLO,
            authority_agent="custom-primary",
            agents=(agent,),
        )
        coordinator = SoloCoordinator(config)
        context = CoordinationContext(
            task_id="task-003",
            task_type="test",
            goal="Generate tests",
        )

        result = await coordinator.coordinate(context)
        assert result.success is True
        assert "custom-primary" in result.participating_agents
