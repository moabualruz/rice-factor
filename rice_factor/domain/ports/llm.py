"""LLM port for artifact compilation.

This module defines the abstract interface for LLM providers,
following the hexagonal architecture pattern. The LLM acts as a
compiler stage that transforms inputs into structured artifacts.
"""

from typing import Protocol

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)


class LLMPort(Protocol):
    """Protocol for LLM artifact compilation operations.

    Implementations handle communication with LLM providers (Claude, OpenAI, etc.)
    to generate structured artifact payloads.

    The LLM operates as a compiler stage with strict constraints:
    - Output valid JSON only
    - Output exactly one artifact per invocation
    - No explanations or reasoning
    - No source code
    - Conform exactly to provided JSON Schema
    - Fail explicitly if information is missing

    Contract (Non-Negotiable):
        1. generate() must return valid JSON or explicit error
        2. Temperature must be 0.0-0.2 for determinism
        3. top_p must be <= 0.3
        4. No streaming
        5. No function calling (artifacts ARE the output)
    """

    def generate(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> CompilerResult:
        """Generate an artifact for the given compiler pass.

        This is the core compilation operation. The LLM receives:
        - A system prompt defining its role as a compiler
        - The input context (project files, approved artifacts)
        - The JSON Schema for the expected output

        Args:
            pass_type: Which compiler pass to execute (PROJECT, ARCHITECTURE, etc.)
            context: Input context containing project files and approved artifacts
            schema: JSON Schema that the output must conform to

        Returns:
            CompilerResult with either:
            - success=True and payload containing the artifact
            - success=False with error_type and error_details

        Raises:
            LLMAPIError: Provider API failure (5xx, network errors)
            LLMTimeoutError: Request timeout
            LLMRateLimitError: Rate limiting response

        Example success response from LLM:
            {"goals": [...], "milestones": [...], ...}

        Example failure response from LLM:
            {"error": "missing_information", "details": "Domain 'User' not defined"}
        """
        ...
