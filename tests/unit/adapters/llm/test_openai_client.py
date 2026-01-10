"""Unit tests for OpenAIClient."""

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.domain.failures.llm_errors import (
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
)


@pytest.fixture(autouse=True)
def mock_openai_module() -> Any:
    """Mock the openai module before importing OpenAIClient."""
    mock_module = MagicMock()

    # Create mock exception classes
    mock_module.APIConnectionError = type("APIConnectionError", (Exception,), {})
    mock_module.APITimeoutError = type("APITimeoutError", (Exception,), {})
    mock_module.RateLimitError = type("RateLimitError", (Exception,), {})
    mock_module.APIStatusError = type(
        "APIStatusError", (Exception,), {"message": "", "status_code": 0}
    )

    # Insert into sys.modules before import
    sys.modules["openai"] = mock_module

    yield mock_module

    # Cleanup
    if "openai" in sys.modules:
        del sys.modules["openai"]

    # Clear cached imports
    for mod_name in list(sys.modules.keys()):
        if "openai_client" in mod_name:
            del sys.modules[mod_name]


class TestOpenAIClientInstantiation:
    """Tests for OpenAIClient instantiation."""

    def test_instantiation_with_defaults(
        self, mock_openai_module: Any  # noqa: ARG002
    ) -> None:
        """Should instantiate with default parameters."""
        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient()
            assert client._timeout == 120.0
            assert client._max_retries == 3
            assert client._azure_endpoint is None

    def test_instantiation_with_custom_params(
        self, mock_openai_module: Any  # noqa: ARG002
    ) -> None:
        """Should instantiate with custom parameters."""
        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient(
                api_key="test-key",
                timeout=60.0,
                max_retries=5,
            )
            assert client._api_key == "test-key"
            assert client._timeout == 60.0
            assert client._max_retries == 5

    def test_instantiation_with_azure_config(
        self, mock_openai_module: Any  # noqa: ARG002
    ) -> None:
        """Should instantiate with Azure OpenAI configuration."""
        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient(
                api_key="test-key",
                azure_endpoint="https://myresource.openai.azure.com/",
                azure_api_version="2024-02-15-preview",
            )
            assert client._azure_endpoint == "https://myresource.openai.azure.com/"
            assert client._azure_api_version == "2024-02-15-preview"

    def test_raises_if_openai_not_available(
        self, mock_openai_module: Any  # noqa: ARG002
    ) -> None:
        """Should raise error if openai SDK not available."""
        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", False
        ):
            from rice_factor.adapters.llm.openai_client import (
                OpenAIClient,
                OpenAIClientError,
            )

            with pytest.raises(OpenAIClientError) as exc_info:
                OpenAIClient()
            assert "openai SDK is not installed" in str(exc_info.value)


class TestOpenAIClientProperty:
    """Tests for OpenAIClient.client property."""

    def test_client_property_creates_openai_client(
        self, mock_openai_module: Any
    ) -> None:
        """client property creates OpenAI client on first access."""
        mock_client_instance = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client_instance

        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient(api_key="test-key", timeout=60.0)
            result = client.client

            assert result is mock_client_instance
            mock_openai_module.OpenAI.assert_called_once_with(
                api_key="test-key", timeout=60.0
            )

    def test_client_property_creates_azure_client(
        self, mock_openai_module: Any
    ) -> None:
        """client property creates Azure OpenAI client when endpoint configured."""
        mock_client_instance = MagicMock()
        mock_openai_module.AzureOpenAI.return_value = mock_client_instance

        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient(
                api_key="test-key",
                timeout=60.0,
                azure_endpoint="https://myresource.openai.azure.com/",
            )
            result = client.client

            assert result is mock_client_instance
            mock_openai_module.AzureOpenAI.assert_called_once()

    def test_is_azure_property(
        self, mock_openai_module: Any  # noqa: ARG002
    ) -> None:
        """is_azure returns True when Azure endpoint is configured."""
        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            standard_client = OpenAIClient()
            assert standard_client.is_azure is False

            azure_client = OpenAIClient(
                azure_endpoint="https://myresource.openai.azure.com/"
            )
            assert azure_client.is_azure is True


class TestOpenAIClientCreateChatCompletion:
    """Tests for OpenAIClient.create_chat_completion method."""

    def test_create_chat_completion_returns_dict(
        self,
        mock_openai_module: Any,
    ) -> None:
        """create_chat_completion returns response as dict."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.id = "chatcmpl-123"
        mock_response.object = "chat.completion"
        mock_response.model = "gpt-4-turbo"

        mock_choice = MagicMock()
        mock_choice.index = 0
        mock_choice.message.role = "assistant"
        mock_choice.message.content = '{"result": "success"}'
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]

        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        mock_openai_module.OpenAI.return_value.chat.completions.create.return_value = (
            mock_response
        )

        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient()
            result = client.create_chat_completion(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": "Hello"}],
            )
            assert isinstance(result, dict)
            assert result["id"] == "chatcmpl-123"
            assert result["choices"][0]["message"]["role"] == "assistant"

    def test_create_chat_completion_passes_parameters(
        self,
        mock_openai_module: Any,
    ) -> None:
        """create_chat_completion passes all parameters to API."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.id = "chatcmpl-123"
        mock_response.object = "chat.completion"
        mock_response.model = "gpt-4-turbo"

        mock_choice = MagicMock()
        mock_choice.index = 0
        mock_choice.message.role = "assistant"
        mock_choice.message.content = '{"result": "success"}'
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]

        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        mock_openai_module.OpenAI.return_value.chat.completions.create.return_value = (
            mock_response
        )

        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient()
            client.create_chat_completion(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1000,
                temperature=0.1,
                top_p=0.2,
                response_format={"type": "json_object"},
            )

            api_call = mock_openai_module.OpenAI.return_value.chat.completions.create
            api_call.assert_called_once()
            call_kwargs = api_call.call_args[1]

            assert call_kwargs["model"] == "gpt-4-turbo"
            assert call_kwargs["max_tokens"] == 1000
            assert call_kwargs["temperature"] == 0.1
            assert call_kwargs["top_p"] == 0.2
            assert call_kwargs["response_format"] == {"type": "json_object"}


class TestOpenAIClientErrorHandling:
    """Tests for OpenAIClient error handling."""

    def test_timeout_raises_llm_timeout_error(
        self, mock_openai_module: Any
    ) -> None:
        """Timeout should raise LLMTimeoutError."""
        mock_timeout = mock_openai_module.APITimeoutError

        mock_openai_module.OpenAI.return_value.chat.completions.create.side_effect = (
            mock_timeout("timeout")
        )

        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ), patch(
            "rice_factor.adapters.llm.openai_client.APITimeoutError", mock_timeout
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient(max_retries=0)  # No retries
            with pytest.raises(LLMTimeoutError):
                client.create_chat_completion(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                )

    def test_rate_limit_raises_llm_rate_limit_error(
        self, mock_openai_module: Any
    ) -> None:
        """Rate limit should raise LLMRateLimitError."""
        mock_rate_limit = mock_openai_module.RateLimitError

        mock_error = mock_rate_limit("Rate limited")
        mock_error.response = None
        mock_openai_module.OpenAI.return_value.chat.completions.create.side_effect = (
            mock_error
        )

        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ), patch(
            "rice_factor.adapters.llm.openai_client.RateLimitError", mock_rate_limit
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient()
            with pytest.raises(LLMRateLimitError):
                client.create_chat_completion(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                )

    def test_connection_error_raises_llm_api_error(
        self, mock_openai_module: Any
    ) -> None:
        """Connection error should raise LLMAPIError."""
        mock_conn_error = mock_openai_module.APIConnectionError

        mock_openai_module.OpenAI.return_value.chat.completions.create.side_effect = (
            mock_conn_error("Connection failed")
        )

        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ), patch(
            "rice_factor.adapters.llm.openai_client.APIConnectionError", mock_conn_error
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient()
            with pytest.raises(LLMAPIError):
                client.create_chat_completion(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                )

    def test_api_status_error_raises_llm_api_error(
        self, mock_openai_module: Any
    ) -> None:
        """API status error should raise LLMAPIError with status code."""
        mock_error = mock_openai_module.APIStatusError("Bad request")
        mock_error.status_code = 400
        mock_error.message = "Bad request"
        mock_openai_module.OpenAI.return_value.chat.completions.create.side_effect = (
            mock_error
        )

        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient()
            with pytest.raises(LLMAPIError) as exc_info:
                client.create_chat_completion(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                )
            assert exc_info.value.status_code == 400


class TestOpenAIClientRetryAfterParsing:
    """Tests for retry-after header parsing."""

    def test_parses_retry_after_from_response(
        self, mock_openai_module: Any
    ) -> None:
        """Should parse retry_after from response headers."""
        mock_rate_limit = mock_openai_module.RateLimitError

        mock_error = mock_rate_limit("Rate limited")
        mock_error.response = MagicMock()
        mock_error.response.headers = {"retry-after": "30"}
        mock_openai_module.OpenAI.return_value.chat.completions.create.side_effect = (
            mock_error
        )

        with patch(
            "rice_factor.adapters.llm.openai_client.OPENAI_AVAILABLE", True
        ), patch(
            "rice_factor.adapters.llm.openai_client.RateLimitError", mock_rate_limit
        ):
            from rice_factor.adapters.llm.openai_client import OpenAIClient

            client = OpenAIClient()
            with pytest.raises(LLMRateLimitError) as exc_info:
                client.create_chat_completion(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                )
            assert exc_info.value.retry_after == 30
