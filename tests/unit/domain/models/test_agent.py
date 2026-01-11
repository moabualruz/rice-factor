"""Unit tests for agent models."""

import pytest

from rice_factor.domain.models.agent import (
    Agent,
    AgentCapability,
    AgentConfig,
    AgentRole,
    ROLE_CAPABILITIES,
)


class TestAgentRole:
    """Tests for AgentRole enum."""

    def test_all_roles_defined(self) -> None:
        """Test that all expected roles are defined."""
        roles = list(AgentRole)
        assert AgentRole.PRIMARY in roles
        assert AgentRole.PLANNER in roles
        assert AgentRole.CRITIC in roles
        assert AgentRole.DOMAIN_SPECIALIST in roles
        assert AgentRole.REFACTOR_ANALYST in roles
        assert AgentRole.TEST_STRATEGIST in roles
        assert AgentRole.GENERIC in roles
        assert AgentRole.ORCHESTRATOR in roles

    def test_role_values(self) -> None:
        """Test role string values."""
        assert AgentRole.PRIMARY.value == "primary"
        assert AgentRole.ORCHESTRATOR.value == "orchestrator"
        assert AgentRole.CRITIC.value == "critic"


class TestAgentCapability:
    """Tests for AgentCapability enum."""

    def test_all_capabilities_defined(self) -> None:
        """Test that expected capabilities are defined."""
        caps = list(AgentCapability)
        assert AgentCapability.EMIT_ARTIFACTS in caps
        assert AgentCapability.PROPOSE_ARTIFACTS in caps
        assert AgentCapability.REVIEW_ARTIFACTS in caps
        assert AgentCapability.DELEGATE_TASKS in caps
        assert AgentCapability.VOTE in caps

    def test_capability_values(self) -> None:
        """Test capability string values."""
        assert AgentCapability.EMIT_ARTIFACTS.value == "emit_artifacts"
        assert AgentCapability.VOTE.value == "vote"


class TestRoleCapabilities:
    """Tests for role-capability mappings."""

    def test_primary_can_emit_artifacts(self) -> None:
        """Test that PRIMARY role has EMIT_ARTIFACTS capability."""
        caps = ROLE_CAPABILITIES[AgentRole.PRIMARY]
        assert AgentCapability.EMIT_ARTIFACTS in caps

    def test_orchestrator_can_emit_and_delegate(self) -> None:
        """Test ORCHESTRATOR capabilities."""
        caps = ROLE_CAPABILITIES[AgentRole.ORCHESTRATOR]
        assert AgentCapability.EMIT_ARTIFACTS in caps
        assert AgentCapability.DELEGATE_TASKS in caps

    def test_planner_cannot_emit_artifacts(self) -> None:
        """Test that PLANNER cannot emit artifacts."""
        caps = ROLE_CAPABILITIES[AgentRole.PLANNER]
        assert AgentCapability.EMIT_ARTIFACTS not in caps
        assert AgentCapability.PROPOSE_ARTIFACTS in caps

    def test_critic_can_review(self) -> None:
        """Test CRITIC capabilities."""
        caps = ROLE_CAPABILITIES[AgentRole.CRITIC]
        assert AgentCapability.REVIEW_ARTIFACTS in caps
        assert AgentCapability.IDENTIFY_RISKS in caps

    def test_generic_can_vote(self) -> None:
        """Test GENERIC capabilities."""
        caps = ROLE_CAPABILITIES[AgentRole.GENERIC]
        assert AgentCapability.VOTE in caps
        assert AgentCapability.PROPOSE_ARTIFACTS in caps


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_minimal_config(self) -> None:
        """Test creating config with minimal arguments."""
        config = AgentConfig(
            agent_id="test-agent",
            role=AgentRole.PRIMARY,
        )
        assert config.agent_id == "test-agent"
        assert config.role == AgentRole.PRIMARY
        assert config.model == "default"
        assert config.scope is None
        assert config.system_prompt is None

    def test_default_capabilities_from_role(self) -> None:
        """Test that default capabilities are set from role."""
        config = AgentConfig(
            agent_id="primary",
            role=AgentRole.PRIMARY,
        )
        # Should have capabilities from ROLE_CAPABILITIES
        assert config.has_capability(AgentCapability.EMIT_ARTIFACTS)
        assert config.has_capability(AgentCapability.SYNTHESIZE_RESULTS)

    def test_custom_capabilities(self) -> None:
        """Test providing custom capabilities."""
        custom_caps = frozenset({AgentCapability.VOTE, AgentCapability.REVIEW_ARTIFACTS})
        config = AgentConfig(
            agent_id="custom",
            role=AgentRole.GENERIC,
            capabilities=custom_caps,
        )
        assert config.capabilities == custom_caps
        assert config.has_capability(AgentCapability.VOTE)
        assert config.has_capability(AgentCapability.REVIEW_ARTIFACTS)
        assert not config.has_capability(AgentCapability.EMIT_ARTIFACTS)

    def test_full_config(self) -> None:
        """Test creating config with all arguments."""
        config = AgentConfig(
            agent_id="expert",
            role=AgentRole.DOMAIN_SPECIALIST,
            model="claude-3-opus",
            scope="security",
            system_prompt="You are a security expert.",
        )
        assert config.agent_id == "expert"
        assert config.role == AgentRole.DOMAIN_SPECIALIST
        assert config.model == "claude-3-opus"
        assert config.scope == "security"
        assert config.system_prompt == "You are a security expert."

    def test_can_emit_artifacts_primary(self) -> None:
        """Test can_emit_artifacts for PRIMARY role."""
        config = AgentConfig(
            agent_id="primary",
            role=AgentRole.PRIMARY,
        )
        assert config.can_emit_artifacts() is True

    def test_can_emit_artifacts_planner(self) -> None:
        """Test can_emit_artifacts for PLANNER role."""
        config = AgentConfig(
            agent_id="planner",
            role=AgentRole.PLANNER,
        )
        assert config.can_emit_artifacts() is False

    def test_config_is_frozen(self) -> None:
        """Test that AgentConfig is immutable."""
        config = AgentConfig(
            agent_id="test",
            role=AgentRole.PRIMARY,
        )
        with pytest.raises(AttributeError):
            config.agent_id = "new-id"  # type: ignore[misc]


class TestAgent:
    """Tests for Agent dataclass."""

    def test_create_agent(self) -> None:
        """Test creating an Agent."""
        config = AgentConfig(
            agent_id="primary",
            role=AgentRole.PRIMARY,
        )
        agent = Agent(config=config)
        assert agent.config == config
        assert agent.is_active is True
        assert agent.task_count == 0

    def test_agent_properties(self) -> None:
        """Test Agent property accessors."""
        config = AgentConfig(
            agent_id="critic",
            role=AgentRole.CRITIC,
        )
        agent = Agent(config=config)
        assert agent.agent_id == "critic"
        assert agent.role == AgentRole.CRITIC

    def test_with_task_completed(self) -> None:
        """Test incrementing task count."""
        config = AgentConfig(
            agent_id="worker",
            role=AgentRole.PLANNER,
        )
        agent = Agent(config=config, task_count=5)
        new_agent = agent.with_task_completed()

        # Original unchanged
        assert agent.task_count == 5

        # New agent has incremented count
        assert new_agent.task_count == 6
        assert new_agent.config == agent.config
        assert new_agent.is_active == agent.is_active

    def test_deactivate(self) -> None:
        """Test deactivating an agent."""
        config = AgentConfig(
            agent_id="worker",
            role=AgentRole.PLANNER,
        )
        agent = Agent(config=config, is_active=True, task_count=3)
        deactivated = agent.deactivate()

        # Original unchanged
        assert agent.is_active is True

        # New agent is deactivated
        assert deactivated.is_active is False
        assert deactivated.task_count == 3
        assert deactivated.config == agent.config

    def test_agent_is_frozen(self) -> None:
        """Test that Agent is immutable."""
        config = AgentConfig(
            agent_id="test",
            role=AgentRole.PRIMARY,
        )
        agent = Agent(config=config)
        with pytest.raises(AttributeError):
            agent.is_active = False  # type: ignore[misc]
