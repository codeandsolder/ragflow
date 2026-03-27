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

import asyncio
import logging
import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30, expected_exceptions=(Exception,)):
        self._failure_count = 0
        self._success_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._expected_exceptions = expected_exceptions
        self._state = CircuitState.CLOSED
        self._last_failure_time = 0
        self._lock = asyncio.Lock()

    @property
    def state(self):
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self._recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

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
                await self._on_success()
                return result
            except self._expected_exceptions:
                await self._on_failure()
                raise

    async def _on_success(self):
        self._success_count += 1
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            logging.info("Circuit breaker: CLOSED - service recovered")

    async def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
            logging.warning(f"Circuit breaker: OPEN - {self._failure_count} failures reached threshold")


class CircuitBreakerError(Exception):
    pass


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
