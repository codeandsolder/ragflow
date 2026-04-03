# Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading
import time
from concurrent.futures import as_completed
from typing import Any
import pytest


class ThreadSafeAssertion:
    """Utility class for thread-safe assertions during concurrent testing."""

    def __init__(self):
        self._lock = threading.Lock()
        self._errors = []
        self._results = []

    def record_result(self, thread_id: str, result: Any):
        with self._lock:
            self._results.append((thread_id, result))

    def record_error(self, thread_id: str, error: Exception):
        with self._lock:
            self._errors.append((thread_id, str(error)))

    def get_results(self) -> list:
        with self._lock:
            return list(self._results)

    def get_errors(self) -> list:
        with self._lock:
            return list(self._errors)

    def has_errors(self) -> bool:
        with self._lock:
            return len(self._errors) > 0

    def assert_no_errors(self):
        errors = self.get_errors()
        if errors:
            error_msgs = "\n".join([f"Thread {tid}: {err}" for tid, err in errors])
            pytest.fail(f"Concurrent operations had errors:\n{error_msgs}")


class MockComponentParam:
    """Mock parameter class for testing components."""

    def __init__(self):
        self.message_history_window_size = 13
        self.inputs = {}
        self.outputs = {}
        self.description = ""
        self.max_retries = 0
        self.delay_after_error = 2.0
        self.exception_method = None
        self.exception_default_value = None
        self.exception_goto = None
        self.debug_inputs = {}

    def check(self):
        return True

    def get_input_form(self):
        return {}


class MockComponent:
    """Mock component for testing parallel execution isolation."""

    component_name = "MockComponent"

    def __init__(self, canvas, component_id: str, param: MockComponentParam = None):
        self._canvas = canvas
        self._id = component_id
        self._param = param or MockComponentParam()
        self._outputs = {}
        self._invoke_count = 0
        self._lock = threading.Lock()

    def output(self, key: str = None):
        if key:
            return self._outputs.get(key)
        return dict(self._outputs)

    def set_output(self, key: str, value: Any):
        with self._lock:
            self._outputs[key] = value

    def invoke(self, **kwargs):
        with self._lock:
            self._invoke_count += 1
        self.set_output("_created_time", time.perf_counter())
        return self.output()

    def reset(self, only_output=False):
        with self._lock:
            self._outputs.clear()

    def get_invoke_count(self) -> int:
        with self._lock:
            return self._invoke_count

    def thoughts(self):
        return ""


class TestCanvasRaceConditions:
    """Test class for verifying thread safety of Canvas.globals concurrent access."""

    def _create_minimal_dsl(self, globals_data: dict = None, history: list = None, retrieval: list = None, memory: list = None) -> str:
        """Create a minimal DSL JSON string for testing Canvas initialization."""
        import json

        dsl = {
            "components": {"begin": {"obj": {"component_name": "Begin", "params": {}}, "downstream": [], "upstream": []}},
            "history": history or [],
            "path": ["begin"],
            "retrieval": retrieval or {"chunks": [], "doc_aggs": []},
        }
        if globals_data:
            dsl["globals"] = globals_data
        if memory is not None:
            dsl["memory"] = memory
        return json.dumps(dsl)

    def test_concurrent_globals_read_write(self):
        """Test concurrent read/write operations on Canvas.globals dictionary."""
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl(globals_data={"sys.query": "initial", "sys.counter": 0, "sys.user_id": "test_user", "sys.conversation_turns": 0, "sys.files": [], "sys.history": []})

        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_concurrent_rw")
        assertion = ThreadSafeAssertion()

        num_threads = 10
        iterations_per_thread = 100
        barrier = threading.Barrier(num_threads)

        def reader_thread(thread_id: int):
            try:
                barrier.wait()
                for i in range(iterations_per_thread):
                    value = canvas.get_variable_value("sys.query")
                    canvas.get_variable_value("sys.user_id")
                    canvas.get_variable_value("sys.conversation_turns")
                    assertion.record_result(f"reader_{thread_id}_{i}", value)
            except Exception as e:
                assertion.record_error(f"reader_{thread_id}", e)

        def writer_thread(thread_id: int):
            try:
                barrier.wait()
                for i in range(iterations_per_thread):
                    canvas.set_variable_value("sys.counter", thread_id * 1000 + i)
                    canvas.set_variable_value("sys.query", f"query_{thread_id}_{i}")
                    assertion.record_result(f"writer_{thread_id}_{i}", "written")
            except Exception as e:
                assertion.record_error(f"writer_{thread_id}", e)

        threads = []
        for i in range(num_threads // 2):
            t = threading.Thread(target=reader_thread, args=(i,))
            threads.append(t)
            t = threading.Thread(target=writer_thread, args=(i + num_threads // 2,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assertion.assert_no_errors()
        assert len(assertion.get_results()) == num_threads * iterations_per_thread

    def test_concurrent_history_append(self):
        """Test concurrent append operations to Canvas.history list."""
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl(history=[])
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_history")
        assertion = ThreadSafeAssertion()

        num_threads = 10
        entries_per_thread = 50
        barrier = threading.Barrier(num_threads)

        def history_appender(thread_id: int):
            try:
                barrier.wait()
                for i in range(entries_per_thread):
                    entry = (f"user_{thread_id}", f"message_{thread_id}_{i}")
                    # Use Canvas methods instead of direct lock access
                    canvas.add_user_input(entry[1])
                    assertion.record_result(f"appender_{thread_id}_{i}", entry)
            except Exception as e:
                assertion.record_error(f"appender_{thread_id}", e)

        threads = [threading.Thread(target=history_appender, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assertion.assert_no_errors()
        expected_total = num_threads * entries_per_thread
        assert len(canvas.history) == expected_total, f"Expected {expected_total} history entries, got {len(canvas.history)}"
