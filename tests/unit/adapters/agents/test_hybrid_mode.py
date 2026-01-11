"""Unit tests for hybrid mode coordinator."""

import pytest

from rice_factor.adapters.agents.hybrid_mode import (
    DEFAULT_PHASE_MODES,
    HybridCoordinator,
)
from rice_factor.adapters.agents.orchestrator_mode import OrchestratorCoordinator
from rice_factor.adapters.agents.role_locked_mode import RoleLockedCoordinator
from rice_factor.adapters.agents.solo_mode import SoloCoordinator
from rice_factor.adapters.agents.voting_mode import VotingCoordinator
from rice_factor.config.run_mode_config import RunMode, RunModeConfig
from rice_factor.domain.models.agent import AgentConfig, AgentRole
from rice_factor.domain.ports.coordinator import CoordinationContext


@pytest.fixture
def hybrid_config() -> RunModeConfig:
    """Create a hybrid mode configuration."""
    return RunModeConfig(
        mode=RunMode.HYBRID,
        authority_agent="primary",
        agents=(
            AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),
            AgentConfig(agent_id="planner", role=AgentRole.PLANNER),
            AgentConfig(agent_id="critic", role=AgentRole.CRITIC),
            AgentConfig(agent_id="generic", role=AgentRole.GENERIC),
        ),
        phase_modes={
            "custom_phase": RunMode.VOTING,
        },
    )


@pytest.fixture
def coordinator(hybrid_config: RunModeConfig) -> HybridCoordinator:
    """Create a hybrid coordinator for testing."""
    return HybridCoordinator(hybrid_config)


@pytest.fixture
def planning_context() -> CoordinationContext:
    """Create a planning phase context."""
    return CoordinationContext(
        task_id="task-001",
        task_type="planning",
        goal="Plan the feature implementation",
    )


@pytest.fixture
def design_context() -> CoordinationContext:
    """Create a design phase context."""
    return CoordinationContext(
        task_id="task-002",
        task_type="design",
        goal="Design the architecture",
    )


@pytest.fixture
def implementation_context() -> CoordinationContext:
    """Create an implementation phase context."""
    return CoordinationContext(
        task_id="task-003",
        task_type="implementation",
        goal="Implement the feature",
    )


class TestHybridCoordinatorInit:
    """Tests for HybridCoordinator initialization."""

    def test_mode_name(self, coordinator: HybridCoordinator) -> None:
        """Test that mode name is 'hybrid'."""
        assert coordinator.mode_name == "hybrid"

    def test_agents_initialized(self, coordinator: HybridCoordinator) -> None:
        """Test that agents are initialized."""
        agents = coordinator.get_active_agents()
        assert len(agents) == 4

    def test_default_phase_modes_defined(self) -> None:
        """Test that default phase modes are defined."""
        assert len(DEFAULT_PHASE_MODES) > 0
        assert "planning" in DEFAULT_PHASE_MODES
        assert "design" in DEFAULT_PHASE_MODES
        assert "implementation" in DEFAULT_PHASE_MODES


class TestHybridCoordinatorPhaseModes:
    """Tests for phase-to-mode mapping."""

    def test_get_phase_mode_from_config(self, coordinator: HybridCoordinator) -> None:
        """Test getting phase mode from config override."""
        mode = coordinator.get_phase_mode("custom_phase")
        assert mode == RunMode.VOTING

    def test_get_phase_mode_from_defaults(self, coordinator: HybridCoordinator) -> None:
        """Test getting phase mode from defaults."""
        mode = coordinator.get_phase_mode("planning")
        assert mode == RunMode.ORCHESTRATOR

    def test_get_phase_mode_unknown(self, coordinator: HybridCoordinator) -> None:
        """Test getting mode for unknown phase (defaults to SOLO)."""
        mode = coordinator.get_phase_mode("unknown_phase")
        assert mode == RunMode.SOLO

    def test_get_phase_mode_mapping(self, coordinator: HybridCoordinator) -> None:
        """Test getting complete phase-mode mapping."""
        mapping = coordinator.get_phase_mode_mapping()
        assert "planning" in mapping
        assert "custom_phase" in mapping
        assert mapping["custom_phase"] == RunMode.VOTING


class TestHybridCoordinatorCoordinatorCreation:
    """Tests for coordinator creation."""

    def test_get_coordinator_for_solo(self, coordinator: HybridCoordinator) -> None:
        """Test getting solo coordinator."""
        solo = coordinator.get_coordinator_for_mode(RunMode.SOLO)
        assert isinstance(solo, SoloCoordinator)

    def test_get_coordinator_for_orchestrator(
        self, coordinator: HybridCoordinator
    ) -> None:
        """Test getting orchestrator coordinator."""
        orch = coordinator.get_coordinator_for_mode(RunMode.ORCHESTRATOR)
        assert isinstance(orch, OrchestratorCoordinator)

    def test_get_coordinator_for_voting(self, coordinator: HybridCoordinator) -> None:
        """Test getting voting coordinator."""
        voting = coordinator.get_coordinator_for_mode(RunMode.VOTING)
        assert isinstance(voting, VotingCoordinator)

    def test_get_coordinator_for_role_locked(
        self, coordinator: HybridCoordinator
    ) -> None:
        """Test getting role-locked coordinator."""
        role_locked = coordinator.get_coordinator_for_mode(RunMode.ROLE_LOCKED)
        assert isinstance(role_locked, RoleLockedCoordinator)

    def test_coordinator_caching(self, coordinator: HybridCoordinator) -> None:
        """Test that coordinators are cached."""
        solo1 = coordinator.get_coordinator_for_mode(RunMode.SOLO)
        solo2 = coordinator.get_coordinator_for_mode(RunMode.SOLO)
        assert solo1 is solo2


class TestHybridCoordinatorCoordinate:
    """Tests for coordination execution."""

    @pytest.mark.asyncio
    async def test_coordinate_planning_phase(
        self, coordinator: HybridCoordinator, planning_context: CoordinationContext
    ) -> None:
        """Test coordination for planning phase (uses orchestrator)."""
        result = await coordinator.coordinate(planning_context)

        assert result.success is True
        assert result.session_id.startswith("session-")
        assert coordinator.get_current_phase() == "planning"

    @pytest.mark.asyncio
    async def test_coordinate_design_phase(
        self, coordinator: HybridCoordinator, design_context: CoordinationContext
    ) -> None:
        """Test coordination for design phase (uses voting)."""
        result = await coordinator.coordinate(design_context)

        # Voting mode may not reach consensus with multiple agents
        # Just verify it runs
        assert result.session_id.startswith("session-")
        assert coordinator.get_current_phase() == "design"

    @pytest.mark.asyncio
    async def test_coordinate_implementation_phase(
        self, coordinator: HybridCoordinator, implementation_context: CoordinationContext
    ) -> None:
        """Test coordination for implementation phase (uses role-locked)."""
        result = await coordinator.coordinate(implementation_context)

        assert result.session_id.startswith("session-")
        assert coordinator.get_current_phase() == "implementation"

    @pytest.mark.asyncio
    async def test_reasoning_includes_hybrid_info(
        self, coordinator: HybridCoordinator, planning_context: CoordinationContext
    ) -> None:
        """Test that reasoning includes hybrid mode info."""
        result = await coordinator.coordinate(planning_context)

        assert result.reasoning is not None
        assert "Hybrid" in result.reasoning
        assert "Phase:" in result.reasoning
        assert "Mode:" in result.reasoning


class TestHybridCoordinatorPhaseDetermination:
    """Tests for phase determination from task type."""

    def test_determine_phase_planning(self, coordinator: HybridCoordinator) -> None:
        """Test phase determination for planning task."""
        context = CoordinationContext(
            task_id="t1",
            task_type="planning",
            goal="test",
        )
        phase = coordinator._determine_phase(context)
        assert phase == "planning"

    def test_determine_phase_design(self, coordinator: HybridCoordinator) -> None:
        """Test phase determination for design task."""
        context = CoordinationContext(
            task_id="t1",
            task_type="architecture",
            goal="test",
        )
        phase = coordinator._determine_phase(context)
        assert phase == "design"

    def test_determine_phase_implementation(
        self, coordinator: HybridCoordinator
    ) -> None:
        """Test phase determination for implementation task."""
        context = CoordinationContext(
            task_id="t1",
            task_type="code",
            goal="test",
        )
        phase = coordinator._determine_phase(context)
        assert phase == "implementation"

    def test_determine_phase_testing(self, coordinator: HybridCoordinator) -> None:
        """Test phase determination for testing task."""
        context = CoordinationContext(
            task_id="t1",
            task_type="test_plan",
            goal="test",
        )
        phase = coordinator._determine_phase(context)
        assert phase == "testing"

    def test_determine_phase_unknown_defaults_to_implementation(
        self, coordinator: HybridCoordinator
    ) -> None:
        """Test that unknown task types default to implementation."""
        context = CoordinationContext(
            task_id="t1",
            task_type="unknown_task",
            goal="test",
        )
        phase = coordinator._determine_phase(context)
        assert phase == "implementation"


class TestHybridCoordinatorMultiPhase:
    """Tests for multi-phase coordination."""

    @pytest.mark.asyncio
    async def test_coordinate_multi_phase(
        self, coordinator: HybridCoordinator
    ) -> None:
        """Test coordinating multiple phases."""
        phases = [
            (
                "planning",
                CoordinationContext(
                    task_id="t1",
                    task_type="planning",
                    goal="Plan",
                ),
            ),
            (
                "deployment",
                CoordinationContext(
                    task_id="t2",
                    task_type="deployment",
                    goal="Deploy",
                ),
            ),
        ]

        results = await coordinator.coordinate_multi_phase(phases)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is True

    @pytest.mark.asyncio
    async def test_multi_phase_stops_on_failure(
        self, hybrid_config: RunModeConfig
    ) -> None:
        """Test that multi-phase stops when a phase fails."""
        from rice_factor.domain.models.messages import CoordinationResult

        coordinator = HybridCoordinator(hybrid_config)

        # Mock first phase to fail
        original_coord = coordinator.coordinate

        call_count = 0

        async def failing_coordinate(ctx: CoordinationContext) -> CoordinationResult:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First phase fails
                return CoordinationResult(
                    session_id="test",
                    success=False,
                    participating_agents=(),
                    messages_exchanged=0,
                    errors=("Test failure",),
                    duration_ms=0,
                )
            return await original_coord(ctx)

        # Patch the inner coordinator
        solo_coord = coordinator.get_coordinator_for_mode(RunMode.SOLO)
        solo_coord.coordinate = failing_coordinate  # type: ignore[method-assign]

        phases = [
            (
                "deployment",  # Uses solo mode
                CoordinationContext(
                    task_id="t1",
                    task_type="deployment",
                    goal="First",
                ),
            ),
            (
                "deployment",
                CoordinationContext(
                    task_id="t2",
                    task_type="deployment",
                    goal="Second",
                ),
            ),
        ]

        results = await coordinator.coordinate_multi_phase(phases)

        # Should stop after first failure
        assert len(results) == 1
        assert results[0].success is False

    @pytest.mark.asyncio
    async def test_get_phase_results(
        self, coordinator: HybridCoordinator
    ) -> None:
        """Test getting phase results after multi-phase coordination."""
        phases = [
            (
                "deployment",
                CoordinationContext(
                    task_id="t1",
                    task_type="deployment",
                    goal="Deploy",
                ),
            ),
        ]

        await coordinator.coordinate_multi_phase(phases)

        phase_results = coordinator.get_phase_results()
        assert len(phase_results) == 1
        assert phase_results[0]["phase"] == "deployment"
        assert phase_results[0]["mode"] == "solo"


class TestHybridCoordinatorErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_exception_returns_failure(
        self, hybrid_config: RunModeConfig
    ) -> None:
        """Test that exceptions are handled gracefully."""
        coordinator = HybridCoordinator(hybrid_config)

        # Mock to raise exception
        def raise_error(_: str) -> RunMode:
            raise RuntimeError("Test error")

        coordinator.get_phase_mode = raise_error  # type: ignore[method-assign]

        context = CoordinationContext(
            task_id="t1",
            task_type="test",
            goal="Test",
        )

        result = await coordinator.coordinate(context)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Test error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_duration_recorded(
        self, coordinator: HybridCoordinator, planning_context: CoordinationContext
    ) -> None:
        """Test that duration is always recorded."""
        result = await coordinator.coordinate(planning_context)
        assert result.duration_ms >= 0


class TestHybridCoordinatorAvailableModes:
    """Tests for available modes."""

    def test_get_available_modes(self, coordinator: HybridCoordinator) -> None:
        """Test getting available modes."""
        modes = coordinator.get_available_modes()

        assert RunMode.SOLO in modes
        assert RunMode.ORCHESTRATOR in modes
        assert RunMode.VOTING in modes
        assert RunMode.ROLE_LOCKED in modes

    def test_hybrid_not_in_available_modes(
        self, coordinator: HybridCoordinator
    ) -> None:
        """Test that HYBRID is not in available modes (prevents recursion)."""
        modes = coordinator.get_available_modes()
        assert RunMode.HYBRID not in modes
