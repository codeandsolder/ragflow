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
import os
import random
import time
import logging
import re
import numpy as np
from abc import ABC
from strenum import StrEnum
from tenacity import retry, stop_after_attempt, wait_fixed, RetryCallState
from rag.utils.circuit_breaker import LLMCircuitBreaker, CircuitBreakerError


class LLMErrorCode(StrEnum):
    ERROR_RATE_LIMIT = "RATE_LIMIT_EXCEEDED"
    ERROR_AUTHENTICATION = "AUTH_ERROR"
    ERROR_INVALID_REQUEST = "INVALID_REQUEST"
    ERROR_SERVER = "SERVER_ERROR"
    ERROR_TIMEOUT = "TIMEOUT"
    ERROR_CONNECTION = "CONNECTION_ERROR"
    ERROR_MODEL = "MODEL_ERROR"
    ERROR_MAX_ROUNDS = "ERROR_MAX_ROUNDS"
    ERROR_CONTENT_FILTER = "CONTENT_FILTERED"
    ERROR_QUOTA = "QUOTA_EXCEEDED"
    ERROR_MAX_RETRIES = "MAX_RETRIES_EXCEEDED"
    ERROR_GENERIC = "GENERIC_ERROR"


class RemoteModelBase(ABC):
    def __init__(self, **kwargs):
        self.max_retries = kwargs.get("max_retries", int(os.environ.get("LLM_MAX_RETRIES", 5)))
        self.base_delay = kwargs.get("retry_interval", float(os.environ.get("LLM_BASE_DELAY", 2.0)))
        self.failure_threshold = kwargs.get("failure_threshold", int(os.environ.get("LLM_FAILURE_THRESHOLD", 5)))
        self.recovery_timeout = kwargs.get("recovery_timeout", int(os.environ.get("LLM_RECOVERY_TIMEOUT", 30)))

    @property
    def circuit_breaker(self):
        return LLMCircuitBreaker.get_breaker(
            self._FACTORY_NAME if hasattr(self, "_FACTORY_NAME") else "default",
            failure_threshold=self.failure_threshold,
            recovery_timeout=self.recovery_timeout,
        )

    def _classify_error(self, error):
        error_str = str(error).lower()

        keywords_mapping = [
            (["quota", "capacity", "credit", "billing", "balance", "欠费"], LLMErrorCode.ERROR_QUOTA),
            (["rate limit", "429", "tpm limit", "too many requests", "requests per minute"], LLMErrorCode.ERROR_RATE_LIMIT),
            (["auth", "key", "apikey", "401", "forbidden", "permission"], LLMErrorCode.ERROR_AUTHENTICATION),
            (["invalid", "bad request", "400", "format", "malformed", "parameter"], LLMErrorCode.ERROR_INVALID_REQUEST),
            (["server", "503", "502", "504", "500", "unavailable"], LLMErrorCode.ERROR_SERVER),
            (["timeout", "timed out"], LLMErrorCode.ERROR_TIMEOUT),
            (["connect", "network", "unreachable", "dns"], LLMErrorCode.ERROR_CONNECTION),
            (["filter", "content", "policy", "blocked", "safety", "inappropriate"], LLMErrorCode.ERROR_CONTENT_FILTER),
            (["model", "not found", "does not exist", "not available"], LLMErrorCode.ERROR_MODEL),
            (["max rounds"], LLMErrorCode.ERROR_MODEL),
        ]
        for words, code in keywords_mapping:
            if re.search("({})".format("|".join(words)), error_str):
                return code

        return LLMErrorCode.ERROR_GENERIC

    def _should_retry(self, error_code: str) -> bool:
        return error_code in {
            LLMErrorCode.ERROR_RATE_LIMIT,
            LLMErrorCode.ERROR_SERVER,
            LLMErrorCode.ERROR_TIMEOUT,
            LLMErrorCode.ERROR_CONNECTION,
        }

    def _get_retry_wait(self, retry_state: RetryCallState) -> float:
        return self.base_delay * random.uniform(1.0, 2.0)

    def _before_retry(self, retry_state: RetryCallState):
        e = retry_state.outcome.exception()
        if e:
            error_code = self._classify_error(e)
            attempt = retry_state.attempt_number
            delay = self._get_retry_wait(retry_state)
            logging.warning(f"Error: {error_code}. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{self.max_retries})")
            time.sleep(delay)

    def _retry_if_retryable(self, retry_state: RetryCallState) -> bool:
        if retry_state.outcome is None:
            return False
        e = retry_state.outcome.exception()
        if e is None:
            return False
        if isinstance(e, CircuitBreakerError):
            return False
        return self._is_retryable_error(e)

    def _is_retryable_error(self, e: Exception) -> bool:
        error_code = self._classify_error(e)
        return self._should_retry(error_code)

    def _run_with_retry(self, func, *args, **kwargs):
        retry_decorator = retry(
            stop=stop_after_attempt(self.max_retries + 1),
            wait=wait_fixed(0),
            retry=self._retry_if_retryable,
            before_sleep=self._before_retry,
            reraise=True,
        )

        def wrapped_func(*args, **kwargs):
            return self.circuit_breaker.call_sync(func, *args, **kwargs)

        return retry_decorator(wrapped_func)(*args, **kwargs)

    def _run_in_batches(self, items, batch_size, func, *args, **kwargs):
        results = []
        total_token_count = 0
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            res, tokens = self._run_with_retry(func, batch, *args, **kwargs)
            results.extend(res)
            total_token_count += tokens
        return np.array(results), total_token_count
