"""Interactive questionnaire system for project initialization.

This module provides:
- Question: Model for questionnaire questions
- QuestionnaireRunner: Manages question flow and response collection
"""

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Question:
    """A questionnaire question.

    Attributes:
        key: Unique identifier for the question response
        prompt: The question text to display
        required: Whether the question must be answered (no empty responses)
        multiline: Whether to allow multiline input
        validator: Optional validation function
        hint: Optional hint text to display below the question
    """

    key: str
    prompt: str
    required: bool = True
    multiline: bool = False
    validator: Callable[[str], str | None] | None = None
    hint: str | None = None


@dataclass
class QuestionnaireResponse:
    """Collected responses from a questionnaire.

    Attributes:
        responses: Dictionary mapping question keys to answers
    """

    responses: dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: str = "") -> str:
        """Get a response by key.

        Args:
            key: The question key
            default: Default value if key not found

        Returns:
            The response value or default
        """
        return self.responses.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Set a response.

        Args:
            key: The question key
            value: The response value
        """
        self.responses[key] = value


# Default questions for project initialization
INIT_QUESTIONS: list[Question] = [
    Question(
        key="problem",
        prompt="What problem does this system solve?",
        required=True,
        multiline=True,
        hint="Describe the core problem your project addresses.",
    ),
    Question(
        key="failures",
        prompt="What failures are unacceptable?",
        required=True,
        multiline=True,
        hint="List critical failures that must never occur.",
    ),
    Question(
        key="architecture",
        prompt="What architectural style must be enforced?",
        required=True,
        hint="e.g., hexagonal, microservices, monolith, layered",
    ),
    Question(
        key="languages",
        prompt="What languages are allowed?",
        required=True,
        hint="e.g., Python, TypeScript, Go",
    ),
]


class QuestionnaireRunner:
    """Runs an interactive questionnaire and collects responses.

    This class manages the flow of questions and collects responses.
    The actual prompting is handled by an injected prompt function to
    allow for testing and different UI implementations.
    """

    def __init__(
        self,
        questions: list[Question] | None = None,
        prompt_func: Callable[[str, bool, str | None], str] | None = None,
    ) -> None:
        """Initialize the questionnaire runner.

        Args:
            questions: List of questions to ask. Defaults to INIT_QUESTIONS.
            prompt_func: Function to prompt for input. Takes (prompt, multiline, hint)
                        and returns the user's response. Defaults to basic input().
        """
        self.questions = questions if questions is not None else INIT_QUESTIONS
        self._prompt_func = prompt_func or self._default_prompt

    def _default_prompt(
        self, prompt: str, multiline: bool, hint: str | None  # noqa: ARG002
    ) -> str:
        """Default prompt function using basic input.

        Args:
            prompt: The question to ask
            multiline: Whether multiline input is allowed (ignored in default)
            hint: Hint text (ignored in default)

        Returns:
            User's response
        """
        return input(f"{prompt} ")

    def run(self) -> QuestionnaireResponse:
        """Run the questionnaire and collect responses.

        Returns:
            QuestionnaireResponse containing all answers
        """
        responses = QuestionnaireResponse()

        for question in self.questions:
            response = self._ask_question(question)
            responses.set(question.key, response)

        return responses

    def _ask_question(self, question: Question) -> str:
        """Ask a single question and validate the response.

        Args:
            question: The question to ask

        Returns:
            Validated response string
        """
        while True:
            response = self._prompt_func(question.prompt, question.multiline, question.hint)
            response = response.strip()

            # Check required
            if question.required and not response:
                continue  # Re-ask the question

            # Run custom validator if present
            if question.validator is not None:
                error = question.validator(response)
                if error is not None:
                    continue  # Re-ask on validation failure

            return response
