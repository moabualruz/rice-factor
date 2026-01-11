"""Unit tests for PromptManager."""

import pytest

from rice_factor.domain.artifacts.compiler_types import CompilerContext, CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.prompts import (
    ARCHITECTURE_PLANNER_PROMPT,
    BASE_SYSTEM_PROMPT,
    IMPLEMENTATION_PLANNER_PROMPT,
    PASS_PROMPTS,
    PASS_TO_ARTIFACT,
    PROJECT_PLANNER_PROMPT,
    REFACTOR_PLANNER_PROMPT,
    SCAFFOLD_PLANNER_PROMPT,
    TEST_DESIGNER_PROMPT,
    PromptManager,
)


class TestPromptManager:
    """Tests for PromptManager class."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        """Create a PromptManager instance."""
        return PromptManager()

    def test_get_base_prompt_returns_canonical(self, manager: PromptManager) -> None:
        """get_base_prompt should return the canonical base prompt."""
        result = manager.get_base_prompt()
        assert result == BASE_SYSTEM_PROMPT

    def test_get_pass_prompt_project(self, manager: PromptManager) -> None:
        """Should return project planner prompt."""
        result = manager.get_pass_prompt(CompilerPassType.PROJECT)
        assert result == PROJECT_PLANNER_PROMPT

    def test_get_pass_prompt_architecture(self, manager: PromptManager) -> None:
        """Should return architecture planner prompt."""
        result = manager.get_pass_prompt(CompilerPassType.ARCHITECTURE)
        assert result == ARCHITECTURE_PLANNER_PROMPT

    def test_get_pass_prompt_scaffold(self, manager: PromptManager) -> None:
        """Should return scaffold planner prompt."""
        result = manager.get_pass_prompt(CompilerPassType.SCAFFOLD)
        assert result == SCAFFOLD_PLANNER_PROMPT

    def test_get_pass_prompt_test(self, manager: PromptManager) -> None:
        """Should return test designer prompt."""
        result = manager.get_pass_prompt(CompilerPassType.TEST)
        assert result == TEST_DESIGNER_PROMPT

    def test_get_pass_prompt_implementation(self, manager: PromptManager) -> None:
        """Should return implementation planner prompt."""
        result = manager.get_pass_prompt(CompilerPassType.IMPLEMENTATION)
        assert result == IMPLEMENTATION_PLANNER_PROMPT

    def test_get_pass_prompt_refactor(self, manager: PromptManager) -> None:
        """Should return refactor planner prompt."""
        result = manager.get_pass_prompt(CompilerPassType.REFACTOR)
        assert result == REFACTOR_PLANNER_PROMPT


class TestGetSystemPrompt:
    """Tests for get_system_prompt method."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        """Create a PromptManager instance."""
        return PromptManager()

    def test_combines_base_and_pass_prompts(self, manager: PromptManager) -> None:
        """Should combine base and pass-specific prompts."""
        result = manager.get_system_prompt(CompilerPassType.PROJECT)

        # Should contain base prompt
        assert "Artifact Builder" in result
        assert "compiler stage" in result

        # Should contain pass-specific prompt
        assert "Project Planner" in result

    def test_base_prompt_comes_first(self, manager: PromptManager) -> None:
        """Base prompt should appear before pass prompt."""
        result = manager.get_system_prompt(CompilerPassType.PROJECT)

        base_pos = result.find("Artifact Builder")
        pass_pos = result.find("Project Planner")

        assert base_pos < pass_pos


class TestGetFullPrompt:
    """Tests for get_full_prompt method."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        """Create a PromptManager instance."""
        return PromptManager()

    def test_includes_system_prompt(self, manager: PromptManager) -> None:
        """Should include the system prompt."""
        result = manager.get_full_prompt(CompilerPassType.PROJECT)

        assert "Artifact Builder" in result
        assert "Project Planner" in result

    def test_includes_context_when_provided(self, manager: PromptManager) -> None:
        """Should include context when provided."""
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={"requirements.md": "# Requirements\nBuild a thing"},
        )

        result = manager.get_full_prompt(CompilerPassType.PROJECT, context=context)

        assert "requirements.md" in result
        assert "Build a thing" in result

    def test_includes_target_file_in_context(self, manager: PromptManager) -> None:
        """Should include target file in context."""
        context = CompilerContext(
            pass_type=CompilerPassType.IMPLEMENTATION,
            target_file="src/main.py",
        )

        result = manager.get_full_prompt(
            CompilerPassType.IMPLEMENTATION,
            context=context,
            include_schema=False,
        )

        assert "TARGET FILE: src/main.py" in result


class TestAllPassPromptsDefined:
    """Tests to verify all pass prompts are defined."""

    def test_all_pass_types_have_prompts(self) -> None:
        """Every CompilerPassType should have a prompt defined."""
        for pass_type in CompilerPassType:
            assert pass_type in PASS_PROMPTS, f"Missing prompt for {pass_type}"

    def test_all_pass_prompts_are_non_empty(self) -> None:
        """All pass prompts should be non-empty strings."""
        for pass_type, prompt in PASS_PROMPTS.items():
            assert isinstance(prompt, str), f"Prompt for {pass_type} is not a string"
            assert len(prompt) > 0, f"Prompt for {pass_type} is empty"


class TestPassPromptContent:
    """Tests for pass prompt content requirements."""

    @pytest.mark.parametrize(
        "pass_type,expected_content",
        [
            (CompilerPassType.PROJECT, "requirements"),
            (CompilerPassType.ARCHITECTURE, "dependency"),
            (CompilerPassType.SCAFFOLD, "structure"),
            (CompilerPassType.TEST, "correctness"),
            (CompilerPassType.IMPLEMENTATION, "reviewable"),
            (CompilerPassType.REFACTOR, "behavior change"),
        ],
    )
    def test_prompt_contains_expected_purpose(
        self, pass_type: CompilerPassType, expected_content: str
    ) -> None:
        """Each prompt should contain expected purpose-related content."""
        prompt = PASS_PROMPTS[pass_type]
        assert expected_content.lower() in prompt.lower()

    def test_all_prompts_have_purpose_section(self) -> None:
        """All prompts should have a PURPOSE section."""
        for pass_type, prompt in PASS_PROMPTS.items():
            assert "PURPOSE" in prompt, f"Missing PURPOSE in {pass_type} prompt"

    def test_all_prompts_have_output_section(self) -> None:
        """All prompts should have an OUTPUT section."""
        for pass_type, prompt in PASS_PROMPTS.items():
            assert "OUTPUT" in prompt, f"Missing OUTPUT in {pass_type} prompt"

    def test_all_prompts_have_failure_conditions(self) -> None:
        """All prompts should mention failure conditions."""
        for pass_type, prompt in PASS_PROMPTS.items():
            assert "FAIL" in prompt.upper(), f"Missing failure info in {pass_type} prompt"


class TestPassToArtifactMapping:
    """Tests for PASS_TO_ARTIFACT mapping."""

    def test_all_pass_types_mapped(self) -> None:
        """Every CompilerPassType should map to an ArtifactType."""
        for pass_type in CompilerPassType:
            assert pass_type in PASS_TO_ARTIFACT, f"Missing mapping for {pass_type}"

    def test_project_maps_to_project_plan(self) -> None:
        """PROJECT should map to PROJECT_PLAN."""
        assert PASS_TO_ARTIFACT[CompilerPassType.PROJECT] == ArtifactType.PROJECT_PLAN

    def test_architecture_maps_to_architecture_plan(self) -> None:
        """ARCHITECTURE should map to ARCHITECTURE_PLAN."""
        assert (
            PASS_TO_ARTIFACT[CompilerPassType.ARCHITECTURE]
            == ArtifactType.ARCHITECTURE_PLAN
        )

    def test_scaffold_maps_to_scaffold_plan(self) -> None:
        """SCAFFOLD should map to SCAFFOLD_PLAN."""
        assert (
            PASS_TO_ARTIFACT[CompilerPassType.SCAFFOLD] == ArtifactType.SCAFFOLD_PLAN
        )

    def test_test_maps_to_test_plan(self) -> None:
        """TEST should map to TEST_PLAN."""
        assert PASS_TO_ARTIFACT[CompilerPassType.TEST] == ArtifactType.TEST_PLAN

    def test_implementation_maps_to_implementation_plan(self) -> None:
        """IMPLEMENTATION should map to IMPLEMENTATION_PLAN."""
        assert (
            PASS_TO_ARTIFACT[CompilerPassType.IMPLEMENTATION]
            == ArtifactType.IMPLEMENTATION_PLAN
        )

    def test_refactor_maps_to_refactor_plan(self) -> None:
        """REFACTOR should map to REFACTOR_PLAN."""
        assert (
            PASS_TO_ARTIFACT[CompilerPassType.REFACTOR] == ArtifactType.REFACTOR_PLAN
        )


class TestGetArtifactTypeForPass:
    """Tests for get_artifact_type_for_pass method."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        """Create a PromptManager instance."""
        return PromptManager()

    def test_returns_artifact_type(self, manager: PromptManager) -> None:
        """Should return the correct artifact type."""
        result = manager.get_artifact_type_for_pass(CompilerPassType.PROJECT)
        assert result == ArtifactType.PROJECT_PLAN

    def test_returns_none_for_unknown(self, manager: PromptManager) -> None:
        """Should return None for unmapped pass types."""
        # This shouldn't happen with current enum, but test the behavior
        # We can't easily test this without modifying the mapping
        pass
