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


class TestCanvasConcurrentAccess:
    """Test concurrent access to Canvas data structures."""

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

    def test_concurrent_retrieval_access(self):
        """Test concurrent access to Canvas.retrieval data structure."""
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl(retrieval=[{"chunks": {}, "doc_aggs": {}}])
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_retrieval")
        assertion = ThreadSafeAssertion()

        num_threads = 8
        operations_per_thread = 25
        barrier = threading.Barrier(num_threads)

        def retrieval_accessor(thread_id: int):
            try:
                barrier.wait()
                for i in range(operations_per_thread):
                    if i % 2 == 0:
                        chunk = {"id": f"chunk_{thread_id}_{i}", "content": f"content_{i}"}
                        doc_info = {"doc_name": f"doc_{thread_id}_{i}", "doc_id": f"id_{i}"}
                        canvas.add_reference([chunk], [doc_info])
                    else:
                        ref = canvas.get_reference()
                        assertion.record_result(f"retrieval_{thread_id}_{i}", ref)
            except Exception as e:
                assertion.record_error(f"retrieval_{thread_id}", e)

        threads = [threading.Thread(target=retrieval_accessor, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assertion.assert_no_errors()
        ref = canvas.get_reference()
        assert isinstance(ref, dict)
        assert "chunks" in ref
        assert "doc_aggs" in ref
        # Verify that the reference contains data from all threads
        assert len(ref["chunks"]) > 0, "Reference chunks should not be empty"
        assert len(ref["doc_aggs"]) > 0, "Reference doc_aggs should not be empty"

    def test_memory_concurrent_access(self):
        """Test concurrent access to Canvas.memory data structure."""
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl(memory=[])
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_memory")
        assertion = ThreadSafeAssertion()

        num_threads = 8
        memories_per_thread = 25
        barrier = threading.Barrier(num_threads)

        def memory_writer(thread_id: int):
            try:
                barrier.wait()
                for i in range(memories_per_thread):
                    user_msg = f"user_{thread_id}_{i}"
                    assist_msg = f"assist_{thread_id}_{i}"
                    summ_msg = f"summary_{thread_id}_{i}"
                    canvas.add_memory(user_msg, assist_msg, summ_msg)
                    assertion.record_result(f"memory_{thread_id}_{i}", (user_msg, assist_msg, summ_msg))
            except Exception as e:
                assertion.record_error(f"memory_{thread_id}", e)

        threads = [threading.Thread(target=memory_writer, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assertion.assert_no_errors()
        expected_total = num_threads * memories_per_thread
        actual_total = len(canvas.get_memory())
        assert actual_total == expected_total, f"Memory entries mismatch: expected {expected_total}, got {actual_total}"

    def test_is_reff_concurrent_safety(self):
        """Test concurrent calls to Canvas.is_reff method."""
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl(globals_data={"sys.query": "test", "sys.user_id": "user123", "sys.conversation_turns": 1, "sys.files": [], "sys.history": [], "custom_var": "value"})
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_is_reff")
        assertion = ThreadSafeAssertion()

        num_threads = 10
        iterations = 100
        barrier = threading.Barrier(num_threads)

        def is_reff_checker(thread_id: int):
            try:
                barrier.wait()
                for i in range(iterations):
                    result1 = canvas.is_reff("sys.query")
                    result2 = canvas.is_reff("sys.user_id")
                    result3 = canvas.is_reff("nonexistent_var")
                    assertion.record_result(f"is_reff_{thread_id}_{i}", (result1, result2, result3))
            except Exception as e:
                assertion.record_error(f"is_reff_{thread_id}", e)

        threads = [threading.Thread(target=is_reff_checker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assertion.assert_no_errors()
        for thread_id, results in assertion.get_results():
            assert results[0] is True, "sys.query should be a valid reference"
            assert results[1] is True, "sys.user_id should be a valid reference"
            assert results[2] is False, "nonexistent_var should not be a valid reference"
        # Additional verification of thread safety
        assert len(assertion.get_results()) == num_threads * iterations, "Expected results from all threads"
