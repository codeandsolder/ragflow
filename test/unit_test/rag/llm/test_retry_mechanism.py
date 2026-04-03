#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
"""Tests for LLM retry mechanism in RemoteModelBase."""

import time
import pytest
from unittest.mock import patch

try:
    from rag.llm.remote_model_base import RemoteModelBase, LLMErrorCode
    from rag.utils.circuit_breaker import CircuitState, CircuitBreakerError, LLMCircuitBreaker

    _RETRY_IMPORT_OK = True
except (ImportError, ModuleNotFoundError, SyntaxError, AttributeError):
    _RETRY_IMPORT_OK = False
    pytestmark = pytest.mark.skip(reason="rag.llm modules cannot be imported due to dependency issues")


class ConcreteRemoteModel(RemoteModelBase):
    """Concrete implementation for testing."""

    def _invoke(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset circuit breakers before each test to ensure isolation."""
    LLMCircuitBreaker.reset_all()
    yield
    LLMCircuitBreaker.reset_all()


class TestLLMRetryMechanism:
    """Test cases for LLM retry mechanism."""

    @pytest.fixture
    def model(self):
        """Create a model instance for testing."""
        return ConcreteRemoteModel(max_retries=3, retry_interval=0.1)

    def test_error_classification_rate_limit(self, model):
        """Test that 429 errors are classified as rate limit."""
        error = LLMErrorCode.ERROR_RATE_LIMIT
        assert model._should_retry(error) is True

    def test_error_classification_server_error(self, model):
        """Test that 5xx errors are classified as server error."""
        error = LLMErrorCode.ERROR_SERVER
        assert model._should_retry(error) is True

    def test_error_classification_timeout(self, model):
        """Test that timeout errors are retryable."""
        error = LLMErrorCode.ERROR_TIMEOUT
        assert model._should_retry(error) is True

    def test_error_classification_connection_error(self, model):
        """Test that connection errors are retryable."""
        error = LLMErrorCode.ERROR_CONNECTION
        assert model._should_retry(error) is True

    def test_error_classification_auth_error_not_retryable(self, model):
        """Test that auth errors are NOT retryable."""
        error = LLMErrorCode.ERROR_AUTHENTICATION
        assert model._should_retry(error) is False

    def test_error_classification_quota_error_not_retryable(self, model):
        """Test that quota errors are NOT retryable."""
        error = LLMErrorCode.ERROR_QUOTA
        assert model._should_retry(error) is False

    def test_error_classification_from_exception_429(self, model):
        """Test error classification from exception message with 429."""
        error_str = "Rate limit exceeded: 429 Too Many Requests"
        error_code = model._classify_error(error_str)
        assert error_code == LLMErrorCode.ERROR_RATE_LIMIT

    def test_error_classification_from_exception_server_500(self, model):
        """Test error classification from server error message."""
        error_str = "Internal server error: 500"
        error_code = model._classify_error(error_str)
        assert error_code == LLMErrorCode.ERROR_SERVER

    def test_error_classification_from_exception_timeout(self, model):
        """Test error classification from timeout message."""
        error_str = "Request timed out after 30 seconds"
        error_code = model._classify_error(error_str)
        assert error_code == LLMErrorCode.ERROR_TIMEOUT

    def test_error_classification_from_exception_auth(self, model):
        """Test error classification from auth error message."""
        error_str = "Invalid API key: 401 Unauthorized"
        error_code = model._classify_error(error_str)
        assert error_code == LLMErrorCode.ERROR_AUTHENTICATION

    def test_error_classification_from_exception_quota(self, model):
        """Test error classification from quota message."""
        error_str = "Insufficient credits: quota exceeded"
        error_code = model._classify_error(error_str)
        assert error_code == LLMErrorCode.ERROR_QUOTA

    def test_error_classification_generic_fallback(self, model):
        """Test that unknown errors fall back to generic."""
        error_str = "Some unknown error occurred"
        error_code = model._classify_error(error_str)
        assert error_code == LLMErrorCode.ERROR_GENERIC


class TestRetryConfiguration:
    """Test retry configuration from environment variables."""

    def test_default_max_retries(self):
        """Test default max_retries value."""
        model = ConcreteRemoteModel()
        assert model.max_retries == 5

    def test_default_base_delay(self):
        """Test default base_delay value."""
        model = ConcreteRemoteModel()
        assert model.base_delay == 2.0

    def test_custom_max_retries(self):
        """Test custom max_retries setting."""
        model = ConcreteRemoteModel(max_retries=10)
        assert model.max_retries == 10

    def test_custom_retry_interval(self):
        """Test custom retry_interval setting."""
        model = ConcreteRemoteModel(retry_interval=5.0)
        assert model.base_delay == 5.0

    @patch.dict("os.environ", {"LLM_MAX_RETRIES": "3"})
    def test_max_retries_from_env(self):
        """Test max_retries from environment variable."""
        model = ConcreteRemoteModel()
        assert model.max_retries == 3

    @patch.dict("os.environ", {"LLM_BASE_DELAY": "1.0"})
    def test_base_delay_from_env(self):
        """Test base_delay from environment variable."""
        model = ConcreteRemoteModel()
        assert model.base_delay == 1.0


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with retry mechanism."""

    def test_circuit_breaker_property_exists(self):
        """Test that circuit_breaker property exists."""
        model = ConcreteRemoteModel()
        assert hasattr(model, "circuit_breaker")

    def test_circuit_breaker_has_failure_threshold(self):
        """Test circuit breaker has configurable failure threshold."""
        model = ConcreteRemoteModel(failure_threshold=10)
        assert model.failure_threshold == 10

    def test_circuit_breaker_has_recovery_timeout(self):
        """Test circuit breaker has configurable recovery timeout."""
        model = ConcreteRemoteModel(recovery_timeout=60)
        assert model.recovery_timeout == 60


class TestRetryWaitCalculation:
    """Test retry wait time calculation."""

    @pytest.fixture
    def model(self):
        """Create model for testing."""
        return ConcreteRemoteModel(max_retries=3, base_delay=1.0)

    def test_retry_wait_has_jitter(self, model):
        """Test that retry wait includes random jitter."""
        from unittest.mock import MagicMock

        retry_state = MagicMock()
        retry_state.attempt_number = 1
        retry_state.outcome = MagicMock()
        retry_state.outcome.exception = lambda: None

        wait1 = model._get_retry_wait(retry_state)
        wait2 = model._get_retry_wait(retry_state)

        assert wait1 != wait2


class TestRetryableErrorDetection:
    """Test detection of retryable errors."""

    @pytest.fixture
    def model(self):
        """Create model for testing."""
        return ConcreteRemoteModel()

    def test_is_retryable_error_rate_limit(self, model):
        """Test that rate limit errors are detected as retryable."""
        error = Exception("Rate limit exceeded: 429")
        assert model._is_retryable_error(error) is True

    def test_is_retryable_error_server(self, model):
        """Test that server errors are detected as retryable."""
        error = Exception("Server error: 500 Internal Server Error")
        assert model._is_retryable_error(error) is True

    def test_is_retryable_error_timeout(self, model):
        """Test that timeout errors are detected as retryable."""
        error = Exception("Request timed out")
        assert model._is_retryable_error(error) is True

    def test_is_retryable_error_auth(self, model):
        """Test that auth errors are NOT detected as retryable."""
        error = Exception("Invalid API key: 401")
        assert model._is_retryable_error(error) is False


class TestRetryLogicWithMock:
    """Test retry logic with mocked function calls."""

    @pytest.fixture
    def model(self):
        """Create model for testing."""
        return ConcreteRemoteModel(max_retries=3, retry_interval=0.001)

    def test_run_with_retry_success_first_attempt(self, model):
        """Test successful call on first attempt."""
        call_count = 0

        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = model._run_with_retry(successful_func)
        assert result == "success"
        assert call_count == 1

    def test_run_with_retry_success_after_failures(self, model):
        """Test successful call after transient failures."""
        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Rate limit exceeded: 429")
            return "success"

        result = model._run_with_retry(flaky_func)
        assert result == "success"
        assert call_count == 3


class TestBackoffTiming:
    """Test backoff timing calculations."""

    @pytest.fixture
    def model(self):
        """Create model for testing."""
        return ConcreteRemoteModel(max_retries=3, base_delay=2.0)

    def test_wait_time_within_expected_range(self, model):
        """Test that wait times are within expected exponential backoff range."""
        from unittest.mock import MagicMock

        for attempt in range(1, 4):
            retry_state = MagicMock()
            retry_state.attempt_number = attempt
            retry_state.outcome = MagicMock()
            retry_state.outcome.exception = lambda: None

            wait_time = model._get_retry_wait(retry_state)

            min_expected = model.base_delay * 1.0
            max_expected = model.base_delay * 2.0
            assert min_expected <= wait_time <= max_expected

    def test_jitter_produces_varied_wait_times(self, model):
        """Test that jitter produces varied wait times."""
        from unittest.mock import MagicMock

        retry_state = MagicMock()
        retry_state.attempt_number = 1
        retry_state.outcome = MagicMock()
        retry_state.outcome.exception = lambda: None

        wait_times = [model._get_retry_wait(retry_state) for _ in range(50)]

        unique_values = set(wait_times)
        assert len(unique_values) > 1

    def test_wait_time_uses_random_uniform(self, model):
        """Test that wait time uses random.uniform for jitter."""
        from unittest.mock import MagicMock, patch

        retry_state = MagicMock()
        retry_state.attempt_number = 1
        retry_state.outcome = MagicMock()
        retry_state.outcome.exception = lambda: None

        with patch("rag.llm.remote_model_base.random.uniform") as mock_uniform:
            mock_uniform.return_value = 1.5

            wait_time = model._get_retry_wait(retry_state)

            mock_uniform.assert_called_once_with(1.0, 2.0)
            assert wait_time == model.base_delay * 1.5


class TestCircuitBreakerStateTransitions:
    """Test circuit breaker state transitions."""

    def test_circuit_breaker_closed_on_success(self):
        """Test circuit breaker remains closed on successful calls."""
        LLMCircuitBreaker.reset_all()

        model = ConcreteRemoteModel(max_retries=1, base_delay=0.001)

        def success_func():
            return "success"

        for _ in range(5):
            model._run_with_retry(success_func)

        assert model.circuit_breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_rejects_when_open(self):
        """Test that circuit breaker rejects calls when open."""
        LLMCircuitBreaker.reset_all()

        model = ConcreteRemoteModel(max_retries=1, base_delay=0.001)
        model.circuit_breaker._breaker.open()
        model.circuit_breaker._last_failure_time = time.time()

        def success_func():
            return "success"

        with pytest.raises(CircuitBreakerError):
            model._run_with_retry(success_func)

    def test_circuit_breaker_transitions_to_half_open_after_timeout(self):
        """Test circuit breaker transitions to half-open after recovery timeout."""
        LLMCircuitBreaker.reset_all()

        model = ConcreteRemoteModel(max_retries=1, base_delay=0.001, recovery_timeout=60)
        model.circuit_breaker._breaker.open()
        model.circuit_breaker._last_failure_time = time.time() - model.recovery_timeout - 1

        assert model.circuit_breaker.state == CircuitState.HALF_OPEN


class TestEdgeCaseConfiguration:
    """Test edge case configurations."""

    def test_max_retries_zero_single_attempt(self):
        """Test that max_retries=0 results in single attempt."""
        model = ConcreteRemoteModel(max_retries=0, base_delay=0.001)
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Server error: 500")

        with pytest.raises(Exception):
            model._run_with_retry(failing_func)

        assert call_count == 1

    def test_max_retries_zero_success_on_first_attempt(self):
        """Test that max_retries=0 works for successful call."""
        LLMCircuitBreaker.reset_all()
        model = ConcreteRemoteModel(max_retries=0, base_delay=0.001)

        def success_func():
            return "success"

        result = model._run_with_retry(success_func)
        assert result == "success"

    def test_very_large_max_retries(self):
        """Test behavior with very large max_retries."""
        model = ConcreteRemoteModel(max_retries=1000, base_delay=0.001)
        call_count = 0

        def succeed_on_5th():
            nonlocal call_count
            call_count += 1
            if call_count < 5:
                raise Exception("Server error: 500")
            return "success"

        result = model._run_with_retry(succeed_on_5th)
        assert result == "success"
        assert call_count == 5


class TestProviderFallbackBehavior:
    """Tests for provider fallback behavior when retries are exhausted.

    These tests document the current behavior: RemoteModelBase retries on
    transient errors (429, 5xx, timeouts) but does NOT automatically
    failover to secondary providers. The `allow_fallbacks` flag in
    litellm integration is explicitly set to False.
    """

    @pytest.fixture
    def model(self):
        """Create model for testing."""
        return ConcreteRemoteModel(max_retries=3, retry_interval=0.0)

    def test_retry_exhaustion_raises_exception(self, model):
        """Verify that exhausting retries raises the final exception."""
        call_count = 0

        def always_fail():
            nonlocal call_count
            call_count += 1
            raise Exception("429 Too Many Requests")

        with pytest.raises(Exception) as exc_info:
            model._run_with_retry(always_fail)

        assert "429 Too Many Requests" in str(exc_info.value)

    def test_circuit_breaker_prevents_further_calls_after_open(self):
        """Verify circuit breaker prevents calls when in OPEN state."""
        LLMCircuitBreaker.reset_all()
        model = ConcreteRemoteModel(
            max_retries=2,
            retry_interval=0.0,
            failure_threshold=2,
            recovery_timeout=60,
        )

        def fail_once_then_succeed():
            raise Exception("429")

        with pytest.raises((Exception, CircuitBreakerError)):
            for _ in range(model.failure_threshold + 2):
                try:
                    model._run_with_retry(fail_once_then_succeed)
                except CircuitBreakerError:
                    raise
                except Exception:
                    pass

        assert model.circuit_breaker.state == CircuitState.OPEN
