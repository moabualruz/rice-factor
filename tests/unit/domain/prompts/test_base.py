"""Unit tests for base system prompt."""

import json

from rice_factor.domain.prompts.base import (
    BASE_SYSTEM_PROMPT,
    FAILURE_FORMAT_INVALID_REQUEST,
    FAILURE_FORMAT_MISSING_INFO,
    HARD_CONTRACT_RULES,
)


class TestBaseSystemPrompt:
    """Tests for BASE_SYSTEM_PROMPT."""

    def test_contains_artifact_builder_role(self) -> None:
        """Should identify the LLM as an Artifact Builder."""
        assert "Artifact Builder" in BASE_SYSTEM_PROMPT

    def test_contains_compiler_stage_description(self) -> None:
        """Should describe the LLM as a compiler stage."""
        assert "compiler stage" in BASE_SYSTEM_PROMPT

    def test_contains_no_source_code_rule(self) -> None:
        """Should prohibit source code generation."""
        assert "do not generate source code" in BASE_SYSTEM_PROMPT

    def test_contains_no_explanations_rule(self) -> None:
        """Should prohibit explanations."""
        assert "do not explain decisions" in BASE_SYSTEM_PROMPT

    def test_contains_no_reasoning_rule(self) -> None:
        """Should prohibit reasoning or commentary."""
        assert "do not include reasoning" in BASE_SYSTEM_PROMPT

    def test_contains_json_only_rule(self) -> None:
        """Should require valid JSON only."""
        assert "valid JSON only" in BASE_SYSTEM_PROMPT

    def test_contains_one_artifact_rule(self) -> None:
        """Should require exactly one artifact."""
        assert "exactly one artifact" in BASE_SYSTEM_PROMPT

    def test_contains_schema_conformance_rule(self) -> None:
        """Should require schema conformance."""
        assert "conform exactly to the provided JSON Schema" in BASE_SYSTEM_PROMPT

    def test_contains_failure_instruction(self) -> None:
        """Should instruct on how to fail."""
        assert "missing_information" in BASE_SYSTEM_PROMPT
        assert '"error"' in BASE_SYSTEM_PROMPT

    def test_contains_deviation_warning(self) -> None:
        """Should warn about deviations."""
        assert "deviation from these rules is a failure" in BASE_SYSTEM_PROMPT


class TestFailureFormats:
    """Tests for failure format templates."""

    def test_missing_info_format_is_valid_json_template(self) -> None:
        """FAILURE_FORMAT_MISSING_INFO should be a valid JSON structure."""
        # Replace placeholder with actual value
        formatted = FAILURE_FORMAT_MISSING_INFO.replace("<description>", "test error")
        parsed = json.loads(formatted)
        assert parsed["error"] == "missing_information"
        assert parsed["details"] == "test error"

    def test_invalid_request_format_is_valid_json_template(self) -> None:
        """FAILURE_FORMAT_INVALID_REQUEST should be a valid JSON structure."""
        formatted = FAILURE_FORMAT_INVALID_REQUEST.replace(
            "<description>", "test error"
        )
        parsed = json.loads(formatted)
        assert parsed["error"] == "invalid_request"
        assert parsed["details"] == "test error"


class TestHardContractRules:
    """Tests for HARD_CONTRACT_RULES."""

    def test_has_seven_rules(self) -> None:
        """Should have exactly 7 hard contract rules."""
        assert len(HARD_CONTRACT_RULES) == 7

    def test_includes_json_output_rule(self) -> None:
        """Should include JSON output rule."""
        assert any("JSON" in rule for rule in HARD_CONTRACT_RULES)

    def test_includes_one_artifact_rule(self) -> None:
        """Should include one artifact rule."""
        assert any("one artifact" in rule for rule in HARD_CONTRACT_RULES)

    def test_includes_no_explanations_rule(self) -> None:
        """Should include no explanations rule."""
        assert any("explanation" in rule.lower() for rule in HARD_CONTRACT_RULES)

    def test_includes_no_code_rule(self) -> None:
        """Should include no code rule."""
        assert any("no code" in rule.lower() for rule in HARD_CONTRACT_RULES)

    def test_includes_no_reasoning_rule(self) -> None:
        """Should include no reasoning rule."""
        assert any("reasoning" in rule.lower() for rule in HARD_CONTRACT_RULES)

    def test_includes_schema_rule(self) -> None:
        """Should include schema conformance rule."""
        assert any("schema" in rule.lower() for rule in HARD_CONTRACT_RULES)

    def test_includes_failure_rule(self) -> None:
        """Should include explicit failure rule."""
        assert any("fail" in rule.lower() for rule in HARD_CONTRACT_RULES)
