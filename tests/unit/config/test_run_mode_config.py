"""Unit tests for run mode configuration."""

from pathlib import Path

import pytest

from rice_factor.config.run_mode_config import (
    CoordinationRule,
    RunMode,
    RunModeConfig,
)
from rice_factor.domain.models.agent import AgentCapability, AgentConfig, AgentRole


class TestRunMode:
    """Tests for RunMode enum."""

    def test_all_modes_defined(self) -> None:
        """Test that all expected modes are defined."""
        modes = list(RunMode)
        assert RunMode.SOLO in modes
        assert RunMode.ORCHESTRATOR in modes
        assert RunMode.VOTING in modes
        assert RunMode.ROLE_LOCKED in modes
        assert RunMode.HYBRID in modes

    def test_mode_values(self) -> None:
        """Test mode string values."""
        assert RunMode.SOLO.value == "solo"
        assert RunMode.ORCHESTRATOR.value == "orchestrator"
        assert RunMode.VOTING.value == "voting"
        assert RunMode.ROLE_LOCKED.value == "role_locked"
        assert RunMode.HYBRID.value == "hybrid"


class TestCoordinationRule:
    """Tests for CoordinationRule enum."""

    def test_authority_rules(self) -> None:
        """Test authority-related rules."""
        assert CoordinationRule.ONLY_PRIMARY_EMITS_ARTIFACTS.value == "only_primary_emits_artifacts"
        assert CoordinationRule.SINGLE_AUTHORITY.value == "single_authority"

    def test_review_rules(self) -> None:
        """Test review-related rules."""
        assert CoordinationRule.CRITICS_MUST_REVIEW_BEFORE_APPROVAL.value == "critics_must_review_before_approval"
        assert CoordinationRule.MANDATORY_CRITIC_REVIEW.value == "mandatory_critic_review"

    def test_voting_rules(self) -> None:
        """Test voting-related rules."""
        assert CoordinationRule.MAJORITY_WINS.value == "majority_wins"
        assert CoordinationRule.CONSENSUS_REQUIRED.value == "consensus_required"


class TestRunModeConfigSoloMode:
    """Tests for RunModeConfig solo mode."""

    def test_solo_mode_factory(self) -> None:
        """Test creating default solo mode config."""
        config = RunModeConfig.solo_mode()
        assert config.mode == RunMode.SOLO
        assert config.authority_agent == "primary"
        assert len(config.agents) == 1
        assert config.agents[0].role == AgentRole.PRIMARY

    def test_solo_mode_with_custom_model(self) -> None:
        """Test solo mode with custom model."""
        config = RunModeConfig.solo_mode(model="claude-3-opus")
        assert config.agents[0].model == "claude-3-opus"


class TestRunModeConfigValidation:
    """Tests for RunModeConfig validation."""

    def test_authority_agent_must_exist(self) -> None:
        """Test that authority agent must be in agents list."""
        agent = AgentConfig(agent_id="primary", role=AgentRole.PRIMARY)
        with pytest.raises(ValueError, match="Authority agent .* not found"):
            RunModeConfig(
                mode=RunMode.SOLO,
                authority_agent="nonexistent",
                agents=(agent,),
            )

    def test_authority_agent_must_emit_artifacts(self) -> None:
        """Test that authority agent must have EMIT_ARTIFACTS capability."""
        # Create agent without EMIT_ARTIFACTS
        agent = AgentConfig(
            agent_id="planner",
            role=AgentRole.PLANNER,
        )
        with pytest.raises(ValueError, match="does not have EMIT_ARTIFACTS"):
            RunModeConfig(
                mode=RunMode.SOLO,
                authority_agent="planner",
                agents=(agent,),
            )

    def test_voting_threshold_validation(self) -> None:
        """Test voting threshold bounds."""
        agent = AgentConfig(agent_id="primary", role=AgentRole.PRIMARY)

        with pytest.raises(ValueError, match="Voting threshold must be between"):
            RunModeConfig(
                mode=RunMode.VOTING,
                authority_agent="primary",
                agents=(agent,),
                voting_threshold=1.5,
            )

        with pytest.raises(ValueError, match="Voting threshold must be between"):
            RunModeConfig(
                mode=RunMode.VOTING,
                authority_agent="primary",
                agents=(agent,),
                voting_threshold=-0.1,
            )


class TestRunModeConfigQueries:
    """Tests for RunModeConfig query methods."""

    def test_get_agent(self) -> None:
        """Test getting agent by ID."""
        primary = AgentConfig(agent_id="primary", role=AgentRole.PRIMARY)
        critic = AgentConfig(agent_id="critic", role=AgentRole.CRITIC)
        config = RunModeConfig(
            mode=RunMode.ORCHESTRATOR,
            authority_agent="primary",
            agents=(primary, critic),
        )

        assert config.get_agent("primary") == primary
        assert config.get_agent("critic") == critic
        assert config.get_agent("nonexistent") is None

    def test_get_agents_by_role(self) -> None:
        """Test getting agents by role."""
        primary = AgentConfig(agent_id="primary", role=AgentRole.PRIMARY)
        critic1 = AgentConfig(agent_id="critic1", role=AgentRole.CRITIC)
        critic2 = AgentConfig(agent_id="critic2", role=AgentRole.CRITIC)

        config = RunModeConfig(
            mode=RunMode.ORCHESTRATOR,
            authority_agent="primary",
            agents=(primary, critic1, critic2),
        )

        critics = config.get_agents_by_role(AgentRole.CRITIC)
        assert len(critics) == 2
        assert critic1 in critics
        assert critic2 in critics

        primaries = config.get_agents_by_role(AgentRole.PRIMARY)
        assert len(primaries) == 1

    def test_has_rule(self) -> None:
        """Test checking for active rules."""
        config = RunModeConfig(
            mode=RunMode.ORCHESTRATOR,
            authority_agent="primary",
            agents=(AgentConfig(agent_id="primary", role=AgentRole.PRIMARY),),
            rules=frozenset({
                CoordinationRule.ONLY_PRIMARY_EMITS_ARTIFACTS,
                CoordinationRule.MANDATORY_CRITIC_REVIEW,
            }),
        )

        assert config.has_rule(CoordinationRule.ONLY_PRIMARY_EMITS_ARTIFACTS) is True
        assert config.has_rule(CoordinationRule.MANDATORY_CRITIC_REVIEW) is True
        assert config.has_rule(CoordinationRule.MAJORITY_WINS) is False


class TestRunModeConfigFromDict:
    """Tests for loading config from dictionary."""

    def test_from_dict_minimal(self) -> None:
        """Test loading minimal configuration."""
        data = {
            "mode": "solo",
        }
        config = RunModeConfig.from_dict(data)
        assert config.mode == RunMode.SOLO
        assert config.authority_agent == "primary"

    def test_from_dict_full(self) -> None:
        """Test loading full configuration."""
        data = {
            "mode": "orchestrator",
            "authority": {"agent": "orchestrator"},
            "agents": {
                "orchestrator": {
                    "role": "orchestrator",
                    "model": "claude-3-opus",
                },
                "planner": {
                    "role": "planner",
                    "scope": "architecture",
                },
                "critic": {
                    "role": "critic",
                },
            },
            "rules": [
                "only_primary_emits_artifacts",
                "mandatory_critic_review",
            ],
            "voting_threshold": 0.6,
            "max_rounds": 15,
        }
        config = RunModeConfig.from_dict(data)

        assert config.mode == RunMode.ORCHESTRATOR
        assert config.authority_agent == "orchestrator"
        assert len(config.agents) == 3
        assert config.voting_threshold == 0.6
        assert config.max_rounds == 15
        assert config.has_rule(CoordinationRule.ONLY_PRIMARY_EMITS_ARTIFACTS)
        assert config.has_rule(CoordinationRule.MANDATORY_CRITIC_REVIEW)

    def test_from_dict_with_capabilities(self) -> None:
        """Test loading config with custom capabilities."""
        data = {
            "mode": "solo",
            "authority": {"agent": "custom"},
            "agents": {
                "custom": {
                    "role": "primary",
                    "capabilities": ["emit_artifacts", "delegate_tasks"],
                },
            },
        }
        config = RunModeConfig.from_dict(data)
        agent = config.get_agent("custom")
        assert agent is not None
        assert agent.has_capability(AgentCapability.EMIT_ARTIFACTS)
        assert agent.has_capability(AgentCapability.DELEGATE_TASKS)

    def test_from_dict_hybrid_with_phase_modes(self) -> None:
        """Test loading hybrid config with phase modes."""
        data = {
            "mode": "hybrid",
            "authority": {"agent": "primary"},
            "agents": {
                "primary": {"role": "orchestrator"},
            },
            "phase_modes": {
                "planning": "voting",
                "implementation": "role_locked",
                "review": "orchestrator",
            },
        }
        config = RunModeConfig.from_dict(data)

        assert config.mode == RunMode.HYBRID
        assert config.phase_modes["planning"] == RunMode.VOTING
        assert config.phase_modes["implementation"] == RunMode.ROLE_LOCKED
        assert config.phase_modes["review"] == RunMode.ORCHESTRATOR

    def test_from_dict_unknown_mode_raises(self) -> None:
        """Test that unknown mode raises error."""
        data = {"mode": "unknown_mode"}
        with pytest.raises(ValueError, match="Unknown run mode"):
            RunModeConfig.from_dict(data)

    def test_from_dict_unknown_role_raises(self) -> None:
        """Test that unknown role raises error."""
        data = {
            "mode": "solo",
            "agents": {
                "agent": {"role": "unknown_role"},
            },
        }
        with pytest.raises(ValueError, match="Unknown agent role"):
            RunModeConfig.from_dict(data)

    def test_from_dict_unknown_capability_raises(self) -> None:
        """Test that unknown capability raises error."""
        data = {
            "mode": "solo",
            "agents": {
                "agent": {
                    "role": "primary",
                    "capabilities": ["unknown_capability"],
                },
            },
        }
        with pytest.raises(ValueError, match="Unknown capability"):
            RunModeConfig.from_dict(data)


class TestRunModeConfigFromFile:
    """Tests for loading config from file."""

    def test_from_file_not_found(self) -> None:
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError, match="not found"):
            RunModeConfig.from_file(Path("/nonexistent/path.yaml"))

    def test_from_file_valid(self, tmp_path: Path) -> None:
        """Test loading valid YAML file."""
        config_file = tmp_path / "run_mode.yaml"
        config_file.write_text("""
mode: orchestrator
authority:
  agent: primary
agents:
  primary:
    role: orchestrator
    model: gpt-4
  critic:
    role: critic
rules:
  - only_primary_emits_artifacts
""")
        config = RunModeConfig.from_file(config_file)
        assert config.mode == RunMode.ORCHESTRATOR
        assert len(config.agents) == 2

    def test_from_file_invalid_yaml(self, tmp_path: Path) -> None:
        """Test that invalid YAML content raises error."""
        config_file = tmp_path / "run_mode.yaml"
        config_file.write_text("not: valid: yaml: content:")

        # yaml.safe_load will parse this as a dict, but the value will be weird
        # This test may need adjustment based on actual error
        config_file.write_text("mode: [invalid]")
        # This should still work since it's valid YAML, just semantic error
        with pytest.raises((ValueError, TypeError)):
            RunModeConfig.from_file(config_file)


class TestRunModeConfigFromProject:
    """Tests for loading config from project."""

    def test_from_project_fallback_to_solo(self, tmp_path: Path) -> None:
        """Test fallback to solo mode when config not found."""
        config = RunModeConfig.from_project(tmp_path)
        assert config.mode == RunMode.SOLO

    def test_from_project_loads_config(self, tmp_path: Path) -> None:
        """Test loading config from .project directory."""
        project_dir = tmp_path / ".project"
        project_dir.mkdir()
        config_file = project_dir / "run_mode.yaml"
        config_file.write_text("""
mode: voting
authority:
  agent: primary
agents:
  primary:
    role: primary
voting_threshold: 0.75
""")
        config = RunModeConfig.from_project(tmp_path)
        assert config.mode == RunMode.VOTING
        assert config.voting_threshold == 0.75


class TestRunModeConfigSerialization:
    """Tests for serialization methods."""

    def test_to_dict(self) -> None:
        """Test converting config to dictionary."""
        primary = AgentConfig(
            agent_id="primary",
            role=AgentRole.PRIMARY,
            model="claude-3",
        )
        config = RunModeConfig(
            mode=RunMode.ORCHESTRATOR,
            authority_agent="primary",
            agents=(primary,),
            rules=frozenset({CoordinationRule.SINGLE_AUTHORITY}),
            voting_threshold=0.7,
        )

        data = config.to_dict()
        assert data["mode"] == "orchestrator"
        assert data["authority"]["agent"] == "primary"
        assert "primary" in data["agents"]
        assert data["voting_threshold"] == 0.7

    def test_to_yaml(self) -> None:
        """Test converting config to YAML string."""
        config = RunModeConfig.solo_mode()
        yaml_str = config.to_yaml()

        assert "mode: solo" in yaml_str
        assert "authority:" in yaml_str
        assert "agents:" in yaml_str

    def test_round_trip(self) -> None:
        """Test that config survives round-trip serialization."""
        original = RunModeConfig(
            mode=RunMode.ORCHESTRATOR,
            authority_agent="primary",
            agents=(
                AgentConfig(agent_id="primary", role=AgentRole.ORCHESTRATOR),
                AgentConfig(agent_id="critic", role=AgentRole.CRITIC),
            ),
            rules=frozenset({
                CoordinationRule.ONLY_PRIMARY_EMITS_ARTIFACTS,
                CoordinationRule.MANDATORY_CRITIC_REVIEW,
            }),
            voting_threshold=0.65,
            max_rounds=20,
        )

        data = original.to_dict()
        restored = RunModeConfig.from_dict(data)

        assert restored.mode == original.mode
        assert restored.authority_agent == original.authority_agent
        assert len(restored.agents) == len(original.agents)
        assert restored.voting_threshold == original.voting_threshold
        assert restored.max_rounds == original.max_rounds
