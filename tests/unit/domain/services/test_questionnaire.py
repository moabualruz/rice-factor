"""Unit tests for Questionnaire system."""


from rice_factor.domain.services.questionnaire import (
    INIT_QUESTIONS,
    Question,
    QuestionnaireResponse,
    QuestionnaireRunner,
)


class TestQuestion:
    """Tests for Question model."""

    def test_question_creation(self) -> None:
        """Question should be creatable with required fields."""
        q = Question(key="test", prompt="Test question?")
        assert q.key == "test"
        assert q.prompt == "Test question?"

    def test_question_defaults(self) -> None:
        """Question should have sensible defaults."""
        q = Question(key="test", prompt="Test?")
        assert q.required is True
        assert q.multiline is False
        assert q.validator is None
        assert q.hint is None

    def test_question_with_all_fields(self) -> None:
        """Question should accept all fields."""
        validator = lambda x: None if x else "Required"  # noqa: E731
        q = Question(
            key="test",
            prompt="Test?",
            required=False,
            multiline=True,
            validator=validator,
            hint="This is a hint",
        )
        assert q.required is False
        assert q.multiline is True
        assert q.validator is validator
        assert q.hint == "This is a hint"


class TestQuestionnaireResponse:
    """Tests for QuestionnaireResponse model."""

    def test_empty_responses(self) -> None:
        """QuestionnaireResponse should start empty."""
        r = QuestionnaireResponse()
        assert r.responses == {}

    def test_get_returns_default_for_missing_key(self) -> None:
        """get() should return default for missing keys."""
        r = QuestionnaireResponse()
        assert r.get("missing") == ""
        assert r.get("missing", "default") == "default"

    def test_set_stores_value(self) -> None:
        """set() should store a value."""
        r = QuestionnaireResponse()
        r.set("key", "value")
        assert r.get("key") == "value"

    def test_get_returns_stored_value(self) -> None:
        """get() should return stored values."""
        r = QuestionnaireResponse()
        r.responses["key"] = "stored"
        assert r.get("key") == "stored"

    def test_set_overwrites_existing(self) -> None:
        """set() should overwrite existing values."""
        r = QuestionnaireResponse()
        r.set("key", "original")
        r.set("key", "updated")
        assert r.get("key") == "updated"


class TestInitQuestions:
    """Tests for INIT_QUESTIONS default questions."""

    def test_has_four_questions(self) -> None:
        """INIT_QUESTIONS should have 4 questions."""
        assert len(INIT_QUESTIONS) == 4

    def test_problem_question(self) -> None:
        """INIT_QUESTIONS should include problem question."""
        q = next(q for q in INIT_QUESTIONS if q.key == "problem")
        assert "problem" in q.prompt.lower()
        assert q.required is True
        assert q.multiline is True

    def test_failures_question(self) -> None:
        """INIT_QUESTIONS should include failures question."""
        q = next(q for q in INIT_QUESTIONS if q.key == "failures")
        assert "failure" in q.prompt.lower()
        assert q.required is True
        assert q.multiline is True

    def test_architecture_question(self) -> None:
        """INIT_QUESTIONS should include architecture question."""
        q = next(q for q in INIT_QUESTIONS if q.key == "architecture")
        assert "architect" in q.prompt.lower()
        assert q.required is True

    def test_languages_question(self) -> None:
        """INIT_QUESTIONS should include languages question."""
        q = next(q for q in INIT_QUESTIONS if q.key == "languages")
        assert "language" in q.prompt.lower()
        assert q.required is True


class TestQuestionnaireRunnerInit:
    """Tests for QuestionnaireRunner initialization."""

    def test_init_uses_default_questions(self) -> None:
        """QuestionnaireRunner should use INIT_QUESTIONS by default."""
        runner = QuestionnaireRunner()
        assert runner.questions == INIT_QUESTIONS

    def test_init_accepts_custom_questions(self) -> None:
        """QuestionnaireRunner should accept custom questions."""
        custom = [Question(key="q1", prompt="Question 1?")]
        runner = QuestionnaireRunner(questions=custom)
        assert runner.questions == custom

    def test_init_accepts_prompt_func(self) -> None:
        """QuestionnaireRunner should accept custom prompt function."""

        def prompt_func(p: str, m: bool, h: str | None) -> str:  # noqa: ARG001
            return "response"

        runner = QuestionnaireRunner(prompt_func=prompt_func)
        assert runner._prompt_func is prompt_func


class TestQuestionnaireRunnerRun:
    """Tests for QuestionnaireRunner.run() method."""

    def test_run_collects_all_responses(self) -> None:
        """run() should collect responses for all questions."""
        questions = [
            Question(key="q1", prompt="Question 1?"),
            Question(key="q2", prompt="Question 2?"),
        ]
        responses_iter = iter(["Answer 1", "Answer 2"])
        prompt_func = lambda p, m, h: next(responses_iter)  # noqa: E731, ARG005

        runner = QuestionnaireRunner(questions=questions, prompt_func=prompt_func)
        result = runner.run()

        assert result.get("q1") == "Answer 1"
        assert result.get("q2") == "Answer 2"

    def test_run_returns_questionnaire_response(self) -> None:
        """run() should return a QuestionnaireResponse object."""
        questions = [Question(key="q", prompt="Q?", required=False)]
        prompt_func = lambda p, m, h: ""  # noqa: E731, ARG005

        runner = QuestionnaireRunner(questions=questions, prompt_func=prompt_func)
        result = runner.run()

        assert isinstance(result, QuestionnaireResponse)


class TestQuestionnaireRunnerValidation:
    """Tests for QuestionnaireRunner validation behavior."""

    def test_required_question_re_asks_on_empty(self) -> None:
        """Required questions should re-ask if empty response given."""
        questions = [Question(key="q", prompt="Q?", required=True)]
        call_count = [0]

        def prompt_func(p: str, m: bool, h: str | None) -> str:  # noqa: ARG001
            call_count[0] += 1
            # Return empty first time, then valid response
            if call_count[0] == 1:
                return ""
            return "valid"

        runner = QuestionnaireRunner(questions=questions, prompt_func=prompt_func)
        result = runner.run()

        assert call_count[0] == 2
        assert result.get("q") == "valid"

    def test_optional_question_accepts_empty(self) -> None:
        """Optional questions should accept empty responses."""
        questions = [Question(key="q", prompt="Q?", required=False)]
        prompt_func = lambda p, m, h: ""  # noqa: E731, ARG005

        runner = QuestionnaireRunner(questions=questions, prompt_func=prompt_func)
        result = runner.run()

        assert result.get("q") == ""

    def test_custom_validator_re_asks_on_error(self) -> None:
        """Questions with validators should re-ask if validation fails."""
        def validator(response: str) -> str | None:
            if response != "valid":
                return "Must be 'valid'"
            return None

        questions = [
            Question(key="q", prompt="Q?", required=False, validator=validator)
        ]
        call_count = [0]

        def prompt_func(p: str, m: bool, h: str | None) -> str:  # noqa: ARG001
            call_count[0] += 1
            if call_count[0] == 1:
                return "invalid"
            return "valid"

        runner = QuestionnaireRunner(questions=questions, prompt_func=prompt_func)
        result = runner.run()

        assert call_count[0] == 2
        assert result.get("q") == "valid"

    def test_strips_whitespace_from_responses(self) -> None:
        """Responses should have whitespace stripped."""
        questions = [Question(key="q", prompt="Q?")]
        prompt_func = lambda p, m, h: "  answer  "  # noqa: E731, ARG005

        runner = QuestionnaireRunner(questions=questions, prompt_func=prompt_func)
        result = runner.run()

        assert result.get("q") == "answer"


class TestQuestionnaireRunnerDefaultPrompt:
    """Tests for QuestionnaireRunner default prompt function."""

    def test_default_prompt_exists(self) -> None:
        """QuestionnaireRunner should have a default prompt function."""
        runner = QuestionnaireRunner()
        assert runner._prompt_func is not None
        assert callable(runner._prompt_func)
