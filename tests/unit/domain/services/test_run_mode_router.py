"""Unit tests for run mode router service."""

from pathlib import Path

import pytest

from rice_factor.adapters.agents import (
    HybridCoordinator,
    OrchestratorCoordinator,
    RoleLockedCoordinator,
    SoloCoordinator,
    VotingCoordinator,
)
from rice_factor.config.run_mode_config import RunMode, RunModeConfig
from rice_factor.domain.models.agent import AgentConfig, AgentRole
from rice_factor.domain.ports.coordinator import CoordinationContext
from rice_factor.domain.services.run_mode_router import RunModeRouter


@pytest.fixture
def solo_config() -> RunModeConfig:
    """Create a solo mode configuration."""
    return RunModeConfig(
        mode=RunMode.SOLO,
        authority_agent="primary",
        agents=(
            AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
        ),
    )


@pytest.fixture
def orchestrator_config() -> RunModeConfig:
    """Create an orchestrator mode configuration."""
    return RunModeConfig(
        mode=RunMode.ORCHESTRATOR,
        authority_agent="orchestrator",
        agents=(
            AgentConfig(agent_id="orchestrator", role=AgentRole.ORCHESTRATOR),
            AgentConfig(agent_id="planner", role=AgentRole.PLANNER),
        ),
    )


@pytest.fixture
def context() -> CoordinationContext:
    """Create a coordination context."""
    return CoordinationContext(
        task_id="task-001",
        task_type="planning",
        goal="Test goal",
    )


class TestRunModeRouterInit:
    """Tests for router initialization."""

    def test_init_with_config(self, solo_config: RunModeConfig) -> None:
        """Test initialization with provided config."""
        router = RunModeRouter(config=solo_config)
        assert router.mode == RunMode.SOLO
        assert router.config == solo_config

    def test_init_with_mode_override(self, solo_config: RunModeConfig) -> None:
        """Test initialization with mode override."""
        router = RunModeRouter(
            config=solo_config,
            mode_override=RunMode.VOTING,
        )
        assert router.mode == RunMode.VOTING

    def test_mode_override_preserves_agents(self, solo_config: RunModeConfig) -> None:
        """Test that mode override preserves agent configuration."""
        router = RunModeRouter(
            config=solo_config,
            mode_override=RunMode.VOTING,
        )
        # Agents should be preserved
        assert len(router.config.agents) == len(solo_config.agents)


class TestRunModeRouterGetCoordinator:
    """Tests for coordinator creation."""

    def test_get_coordinator_solo(self, solo_config: RunModeConfig) -> None:
        """Test getting solo coordinator."""
        router = RunModeRouter(config=solo_config)
        coordinator = router.get_coordinator()
        assert isinstance(coordinator, SoloCoordinator)

    def test_get_coordinator_orchestrator(
        self, orchestrator_config: RunModeConfig
    ) -> None:
        """Test getting orchestrator coordinator."""
        router = RunModeRouter(config=orchestrator_config)
        coordinator = router.get_coordinator()
        assert isinstance(coordinator, OrchestratorCoordinator)

    def test_get_coordinator_voting(self, solo_config: RunModeConfig) -> None:
        """Test getting voting coordinator."""
        router = RunModeRouter(
            config=solo_config,
            mode_override=RunMode.VOTING,
        )
        coordinator = router.get_coordinator()
        assert isinstance(coordinator, VotingCoordinator)

    def test_get_coordinator_role_locked(self, solo_config: RunModeConfig) -> None:
        """Test getting role-locked coordinator."""
        router = RunModeRouter(
            config=solo_config,
            mode_override=RunMode.ROLE_LOCKED,
        )
        coordinator = router.get_coordinator()
        assert isinstance(coordinator, RoleLockedCoordinator)

    def test_get_coordinator_hybrid(self, solo_config: RunModeConfig) -> None:
        """Test getting hybrid coordinator."""
        router = RunModeRouter(
            config=solo_config,
            mode_override=RunMode.HYBRID,
        )
        coordinator = router.get_coordinator()
        assert isinstance(coordinator, HybridCoordinator)

    def test_coordinator_is_cached(self, solo_config: RunModeConfig) -> None:
        """Test that coordinator is cached."""
        router = RunModeRouter(config=solo_config)
        coord1 = router.get_coordinator()
        coord2 = router.get_coordinator()
        assert coord1 is coord2


class TestRunModeRouterCoordinate:
    """Tests for coordination routing."""

    @pytest.mark.asyncio
    async def test_coordinate_solo(
        self, solo_config: RunModeConfig, context: CoordinationContext
    ) -> None:
        """Test coordination in solo mode."""
        router = RunModeRouter(config=solo_config)
        result = await router.coordinate(context)

        assert result.success is True
        assert result.session_id.startswith("session-")

    @pytest.mark.asyncio
    async def test_coordinate_orchestrator(
        self, orchestrator_config: RunModeConfig, context: CoordinationContext
    ) -> None:
        """Test coordination in orchestrator mode."""
        router = RunModeRouter(config=orchestrator_config)
        result = await router.coordinate(context)

        assert result.session_id.startswith("session-")


class TestRunModeRouterFromCliMode:
    """Tests for CLI mode parsing."""

    def test_from_cli_mode_solo(self) -> None:
        """Test parsing solo mode from CLI."""
        router = RunModeRouter.from_cli_mode("solo")
        assert router.mode == RunMode.SOLO

    def test_from_cli_mode_orchestrator(self) -> None:
        """Test parsing orchestrator mode from CLI."""
        router = RunModeRouter.from_cli_mode("orchestrator")
        assert router.mode == RunMode.ORCHESTRATOR

    def test_from_cli_mode_voting(self) -> None:
        """Test parsing voting mode from CLI."""
        router = RunModeRouter.from_cli_mode("voting")
        assert router.mode == RunMode.VOTING

    def test_from_cli_mode_role_locked(self) -> None:
        """Test parsing role_locked mode from CLI."""
        router = RunModeRouter.from_cli_mode("role_locked")
        assert router.mode == RunMode.ROLE_LOCKED

    def test_from_cli_mode_hybrid(self) -> None:
        """Test parsing hybrid mode from CLI."""
        router = RunModeRouter.from_cli_mode("hybrid")
        assert router.mode == RunMode.HYBRID

    def test_from_cli_mode_case_insensitive(self) -> None:
        """Test that mode parsing is case insensitive."""
        router = RunModeRouter.from_cli_mode("SOLO")
        assert router.mode == RunMode.SOLO

    def test_from_cli_mode_none_uses_default(self) -> None:
        """Test that None mode uses default config."""
        router = RunModeRouter.from_cli_mode(None)
        # Should use default solo mode
        assert router.mode == RunMode.SOLO

    def test_from_cli_mode_invalid_raises(self) -> None:
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            RunModeRouter.from_cli_mode("invalid_mode")

        assert "Invalid mode" in str(exc_info.value)
        assert "valid modes" in str(exc_info.value).lower()


class TestRunModeRouterDescribe:
    """Tests for mode description."""

    def test_describe_solo(self, solo_config: RunModeConfig) -> None:
        """Test solo mode description."""
        router = RunModeRouter(config=solo_config)
        description = router.describe()
        assert "solo" in description.lower()

    def test_describe_orchestrator(
        self, orchestrator_config: RunModeConfig
    ) -> None:
        """Test orchestrator mode description."""
        router = RunModeRouter(config=orchestrator_config)
        description = router.describe()
        assert "orchestrator" in description.lower()

    def test_describe_all_modes(self) -> None:
        """Test that all modes have descriptions."""
        config = RunModeConfig(
            mode=RunMode.SOLO,
            authority_agent="primary",
            agents=(AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),),
        )

        for mode in RunMode:
            router = RunModeRouter(config=config, mode_override=mode)
            description = router.describe()
            # Should have some description
            assert len(description) > 0
