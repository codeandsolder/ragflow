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

import logging
import time
import asyncio
import threading
from enum import Enum
import pybreaker


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30, expected_exceptions=(Exception,)):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._expected_exceptions = expected_exceptions
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=failure_threshold,
            reset_timeout=recovery_timeout,
        )
        for exc in expected_exceptions:
            if exc is not Exception:
                self._breaker.add_exception(exc)
        self._failure_count = 0
        self._last_failure_time = 0
        self._lock = asyncio.Lock()
        self._sync_lock = threading.Lock()

    @property
    def state(self):
        current = self._breaker.current_state
        if current == "closed":
            return CircuitState.CLOSED
        elif current == "open":
            if self._last_failure_time > 0:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self._recovery_timeout:
                    return CircuitState.HALF_OPEN
            return CircuitState.OPEN
        elif current == "half-open":
            return CircuitState.HALF_OPEN
        return CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        state = self.state
        if state == CircuitState.OPEN:
            raise CircuitBreakerError("Circuit is OPEN. Service unavailable.")

        async with self._lock:
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(None, lambda: func(*args, **kwargs))
                self._failure_count = 0
                if self.state == CircuitState.HALF_OPEN:
                    logging.info("Circuit breaker: CLOSED - service recovered")
                return result
            except self._expected_exceptions:
                self._failure_count += 1
                self._last_failure_time = time.time()
                if self._failure_count >= self._failure_threshold:
                    self._breaker.open()
                    logging.warning(f"Circuit breaker: OPEN - {self._failure_count} failures reached threshold")
                raise
            except Exception:
                self._failure_count += 1
                self._last_failure_time = time.time()
                if self._failure_count >= self._failure_threshold:
                    self._breaker.open()
                    logging.warning(f"Circuit breaker: OPEN - {self._failure_count} failures reached threshold")
                raise

    def call_sync(self, func, *args, **kwargs):
        state = self.state
        if state == CircuitState.OPEN:
            raise CircuitBreakerError("Circuit is OPEN. Service unavailable.")

        with self._sync_lock:
            try:
                result = func(*args, **kwargs)
                self._failure_count = 0
                if self.state == CircuitState.HALF_OPEN:
                    logging.info("Circuit breaker: CLOSED - service recovered")
                return result
            except self._expected_exceptions:
                self._failure_count += 1
                self._last_failure_time = time.time()
                if self._failure_count >= self._failure_threshold:
                    self._breaker.open()
                    logging.warning(f"Circuit breaker: OPEN - {self._failure_count} failures reached threshold")
                raise
            except Exception:
                self._failure_count += 1
                self._last_failure_time = time.time()
                if self._failure_count >= self._failure_threshold:
                    self._breaker.open()
                    logging.warning(f"Circuit breaker: OPEN - {self._failure_count} failures reached threshold")
                raise


class LLMCircuitBreaker:
    _breakers = {}

    @classmethod
    def get_breaker(cls, provider: str, **kwargs) -> CircuitBreaker:
        if provider not in cls._breakers:
            cls._breakers[provider] = CircuitBreaker(**kwargs)
        return cls._breakers[provider]

    @classmethod
    async def call(cls, provider: str, func, *args, **kwargs):
        breaker = cls.get_breaker(provider)
        return await breaker.call(func, *args, **kwargs)

    @classmethod
    def get_state(cls, provider: str) -> CircuitState:
        breaker = cls._breakers.get(provider)
        if breaker:
            return breaker.state
        return CircuitState.CLOSED

    @classmethod
    def reset_all(cls):
        cls._breakers.clear()
