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

    @property
    def circuit_breaker(self):
        return LLMCircuitBreaker.get_breaker(
            self._FACTORY_NAME if hasattr(self, "_FACTORY_NAME") else "default",
            failure_threshold=5,
            recovery_timeout=30,
        )

    def _get_delay(self):
        return self.base_delay * random.uniform(1.0, 2.0)

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

    def _handle_exception(self, e, attempt):
        error_code = self._classify_error(e)
        if attempt >= self.max_retries:
            logging.error(f"Max retries reached: {error_code} - {str(e)}")
            return False

        if self._should_retry(error_code):
            delay = self._get_delay()
            logging.warning(f"Error: {error_code}. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{self.max_retries})")
            time.sleep(delay)
            return True

        logging.error(f"Non-retryable error: {error_code} - {str(e)}")
        return False

    def _run_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries + 1):
            try:
                return self.circuit_breaker.call_sync(func, *args, **kwargs)
            except CircuitBreakerError:
                raise
            except Exception as e:
                if not self._handle_exception(e, attempt):
                    raise e

    def _run_in_batches(self, items, batch_size, func, *args, **kwargs):
        results = []
        total_token_count = 0
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            res, tokens = self._run_with_retry(func, batch, *args, **kwargs)
            results.extend(res)
            total_token_count += tokens
        return np.array(results), total_token_count
