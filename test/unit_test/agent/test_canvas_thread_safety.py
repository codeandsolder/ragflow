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


class TestCanvasThreadPoolSafety:
    """Test Canvas ThreadPoolExecutor usage for parallel component execution."""

    def test_thread_pool_executor_isolation(self):
        """Test that the ThreadPoolExecutor isolates component executions."""
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl_with_components()
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_pool")

        assert canvas._thread_pool is not None
        assert canvas._thread_pool._max_workers <= 5

        results = []
        errors = []
        results_lock = threading.Lock()

        def task(task_id: int, should_fail: bool = False):
            if should_fail:
                raise ValueError(f"Intentional failure in task {task_id}")
            with results_lock:
                results.append(task_id)

        futures = []
        for i in range(10):
            future = canvas._thread_pool.submit(task, i, should_fail=(i % 3 == 0))
            futures.append(future)

        completed = 0
        failed = 0
        for future in as_completed(futures):
            try:
                future.result()
                completed += 1
            except Exception:
                failed += 1

        assert failed == 4, f"Expected 4 failures, got {failed}"
        assert completed == 6, f"Expected 6 completions, got {completed}"

    def test_graph_lock_consistency(self):
        """Test that the Graph._lock provides consistent mutual exclusion."""
        from agent.canvas import Graph

        dsl = self._create_minimal_dsl()
        graph = Graph(dsl, tenant_id="test_tenant", task_id="test_task_lock")

        lock_order = []
        lock_order_lock = threading.Lock()
        barrier = threading.Barrier(5)

        def lock_acquirer(thread_id: int):
            barrier.wait()
            with graph._lock:
                with lock_order_lock:
                    lock_order.append(f"acquired_{thread_id}")
                time.sleep(0.01)
                with lock_order_lock:
                    lock_order.append(f"released_{thread_id}")

        threads = [threading.Thread(target=lock_acquirer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for i in range(0, len(lock_order), 2):
            acquired = lock_order[i]
            released = lock_order[i + 1]
            assert acquired.startswith("acquired_"), f"Expected acquired at index {i}"
            assert released.startswith("released_"), f"Expected released at index {i + 1}"

            acquired_id = acquired.split("_")[1]
            released_id = released.split("_")[1]
            assert acquired_id == released_id, f"Lock holder mismatch: acquired by {acquired_id}, released by {released_id}"

    def _create_minimal_dsl_with_components(self) -> str:
        """Create a DSL with minimal component setup."""
        import json

        return json.dumps(
            {
                "components": {"begin": {"obj": {"component_name": "Begin", "params": {}}, "downstream": [], "upstream": []}},
                "history": [],
                "path": ["begin"],
                "retrieval": {"chunks": [], "doc_aggs": []},
                "globals": {"sys.query": "", "sys.user_id": "", "sys.conversation_turns": 0, "sys.files": [], "sys.history": []},
            }
        )

    def _create_minimal_dsl(self) -> str:
        """Create a minimal DSL for testing."""
        import json

        return json.dumps(
            {
                "components": {"begin": {"obj": {"component_name": "Begin", "params": {}}, "downstream": [], "upstream": []}},
                "history": [],
                "path": ["begin"],
                "retrieval": {"chunks": [], "doc_aggs": []},
            }
        )


class TestCanvasGlobalsEdgeCases:
    """Test edge cases and boundary conditions for Canvas.globals access."""

    def test_empty_globals_handling(self):
        """Test handling of empty or missing globals."""
        from agent.canvas import Canvas

        import json

        dsl = json.dumps(
            {
                "components": {"begin": {"obj": {"component_name": "Begin", "params": {}}, "downstream": [], "upstream": []}},
                "history": [],
                "path": ["begin"],
                "retrieval": {"chunks": [], "doc_aggs": []},
            }
        )

        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_empty_globals")

        assert canvas.globals is not None
        assert "sys.query" in canvas.globals
        assert canvas.globals["sys.query"] == ""

    def test_nested_variable_access_concurrency(self):
        """Test concurrent access to nested variable paths."""
        from agent.canvas import Canvas

        import json

        dsl = json.dumps(
            {
                "components": {
                    "begin": {"obj": {"component_name": "Begin", "params": {}}, "downstream": [], "upstream": []},
                    "test_component": {"obj": {"component_name": "ExitLoop", "params": {}}, "downstream": [], "upstream": ["begin"]},
                },
                "history": [],
                "path": ["begin"],
                "retrieval": {"chunks": [], "doc_aggs": []},
                "globals": {"sys.query": "", "sys.user_id": "test", "sys.conversation_turns": 0, "sys.files": [], "sys.history": [], "nested": {"level1": {"level2": {"value": 0}}}},
            }
        )

        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_nested")
        assertion = ThreadSafeAssertion()

        num_threads = 10
        iterations = 50
        barrier = threading.Barrier(num_threads)

        def nested_accessor(thread_id: int):
            try:
                barrier.wait()
                for i in range(iterations):
                    canvas.set_variable_value("nested.level1.level2.value", thread_id * 100 + i)
                    value = canvas.get_variable_param_value(canvas.globals.get("nested", {}), "level1.level2.value")
                    assertion.record_result(f"nested_{thread_id}_{i}", value)
            except Exception as e:
                assertion.record_error(f"nested_{thread_id}", e)

        threads = [threading.Thread(target=nested_accessor, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assertion.assert_no_errors()
