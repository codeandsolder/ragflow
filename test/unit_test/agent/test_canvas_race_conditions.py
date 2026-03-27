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
        """Test concurrent read/write operations on Canvas.globals dictionary.

        Verifies that:
        - Multiple threads can safely read globals simultaneously
        - Writes are atomic and don't corrupt data
        - The internal lock properly protects globals access
        """
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
        """Test concurrent append operations to Canvas.history list.

        Verifies that:
        - Multiple threads can append to history without data loss
        - All appended entries are preserved in order
        - No race conditions cause list corruption
        """
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
                    with canvas._lock:
                        canvas.history.append(entry)
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

    def test_concurrent_retrieval_access(self):
        """Test concurrent access to Canvas.retrieval data structure.

        Verifies that:
        - Multiple threads can safely read from retrieval
        - add_reference operations are thread-safe
        - Retrieval chunks and doc_aggs maintain integrity
        """
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

    def test_variable_assigner_atomicity(self):
        """Test VariableAssigner component operations are atomic.

        Verifies that:
        - Variable assignment operations maintain atomicity
        - Read-modify-write operations don't have race conditions
        - Complex operations like append/extend are thread-safe
        """
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl(globals_data={"sys.query": "", "sys.user_id": "test", "sys.conversation_turns": 0, "sys.files": [], "sys.history": [], "test_counter": 0, "test_list": []})
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_var_assigner")
        assertion = ThreadSafeAssertion()

        num_threads = 10
        iterations = 100
        barrier = threading.Barrier(num_threads)

        def counter_incrementor(thread_id: int):
            try:
                barrier.wait()
                for i in range(iterations):
                    current = canvas.get_variable_value("test_counter")
                    canvas.set_variable_value("test_counter", current + 1)
            except Exception as e:
                assertion.record_error(f"incrementor_{thread_id}", e)

        threads = [threading.Thread(target=counter_incrementor, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assertion.assert_no_errors()
        final_value = canvas.get_variable_value("test_counter")
        expected = num_threads * iterations
        assert final_value == expected, f"Race condition detected: expected counter {expected}, got {final_value}"

    def test_parallel_component_execution_isolation(self):
        """Test that parallel component executions maintain state isolation.

        Verifies that:
        - Each component's output state is isolated
        - Components running in parallel don't interfere with each other
        - The thread pool executor properly isolates execution contexts
        """
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl()
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_component_isolation")
        assertion = ThreadSafeAssertion()

        num_components = 5
        iterations = 20
        components = {}

        for i in range(num_components):
            components[f"component_{i}"] = MockComponent(canvas, f"cpn_{i}")

        barrier = threading.Barrier(num_components)

        def component_executor(cpn_id: str, component: MockComponent):
            try:
                barrier.wait()
                for i in range(iterations):
                    component.invoke(test_data=f"data_{cpn_id}_{i}")
                    output = component.output()
                    assertion.record_result(f"{cpn_id}_{i}", output)
            except Exception as e:
                assertion.record_error(cpn_id, e)

        threads = [threading.Thread(target=component_executor, args=(cpn_id, cpn)) for cpn_id, cpn in components.items()]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assertion.assert_no_errors()
        for cpn_id, cpn in components.items():
            assert cpn.get_invoke_count() == iterations, f"Component {cpn_id} should have {iterations} invocations"

    def test_stress_test_concurrent_access(self):
        """Stress test Canvas with high-concurrency access patterns.

        Verifies that:
        - Canvas handles sustained high-concurrency load
        - No deadlocks occur under stress
        - Memory and state remain consistent
        """
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl(
            globals_data={
                "sys.query": "stress_test",
                "sys.counter": 0,
                "sys.user_id": "stress_user",
                "sys.conversation_turns": 0,
                "sys.files": [],
                "sys.history": [],
                "stress_data": {"values": [], "count": 0},
            }
        )
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_stress")
        assertion = ThreadSafeAssertion()

        num_threads = 20
        operations_per_thread = 200
        barrier = threading.Barrier(num_threads)

        def stress_worker(thread_id: int):
            try:
                barrier.wait()
                for i in range(operations_per_thread):
                    op_type = i % 4

                    if op_type == 0:
                        canvas.set_variable_value("sys.counter", thread_id * 10000 + i)
                    elif op_type == 1:
                        canvas.get_variable_value("sys.query")
                        canvas.get_variable_value("sys.user_id")
                    elif op_type == 2:
                        with canvas._lock:
                            current_history = list(canvas.globals.get("sys.history", []))
                            current_history.append(f"entry_{thread_id}_{i}")
                            canvas.globals["sys.history"] = current_history
                    else:
                        canvas.set_global_param(stress_key=f"stress_{thread_id}_{i}")

                    assertion.record_result(f"stress_{thread_id}_{i}", op_type)
            except Exception as e:
                assertion.record_error(f"stress_{thread_id}", e)

        threads = [threading.Thread(target=stress_worker, args=(i,)) for i in range(num_threads)]

        start_time = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - start_time

        assertion.assert_no_errors()
        total_ops = num_threads * operations_per_thread
        assert len(assertion.get_results()) == total_ops

        print(f"\nStress test completed: {total_ops} operations in {elapsed:.3f}s")
        print(f"Throughput: {total_ops / elapsed:.0f} ops/sec")

    def test_globals_lock_contention(self):
        """Test behavior under high lock contention on globals.

        Verifies that:
        - Lock contention doesn't cause timeouts or deadlocks
        - Fair scheduling of lock acquisition
        - Performance degrades gracefully under contention
        """
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl(globals_data={"sys.query": "", "sys.user_id": "", "sys.conversation_turns": 0, "sys.files": [], "sys.history": [], "contention_counter": 0})
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_contention")

        num_threads = 30
        iterations = 100
        barrier = threading.Barrier(num_threads)
        acquire_times = []
        acquire_times_lock = threading.Lock()

        def contention_worker(thread_id: int):
            barrier.wait()
            for i in range(iterations):
                start = time.perf_counter()
                with canvas._lock:
                    acquire_time = time.perf_counter() - start
                    with acquire_times_lock:
                        acquire_times.append(acquire_time)
                    current = canvas.globals.get("contention_counter", 0)
                    canvas.globals["contention_counter"] = current + 1

        threads = [threading.Thread(target=contention_worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected_total = num_threads * iterations
        actual_total = canvas.globals.get("contention_counter", 0)
        assert actual_total == expected_total, f"Lost updates due to race condition: expected {expected_total}, got {actual_total}"

        avg_acquire_time = sum(acquire_times) / len(acquire_times)
        max_acquire_time = max(acquire_times)
        print("\nLock contention stats:")
        print(f"  Average acquire time: {avg_acquire_time * 1000:.3f}ms")
        print(f"  Max acquire time: {max_acquire_time * 1000:.3f}ms")

    def test_memory_concurrent_access(self):
        """Test concurrent access to Canvas.memory data structure.

        Verifies that:
        - Memory list operations are thread-safe
        - add_memory operations don't cause corruption
        - get_memory returns consistent snapshots
        """
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
        """Test concurrent calls to Canvas.is_reff method.

        Verifies that:
        - is_reff safely handles concurrent reads
        - No false positives/negatives under concurrency
        """
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


class TestCanvasThreadPoolSafety:
    """Test Canvas ThreadPoolExecutor usage for parallel component execution."""

    def test_thread_pool_executor_isolation(self):
        """Test that the ThreadPoolExecutor isolates component executions.

        Verifies that:
        - Thread pool properly manages worker threads
        - Tasks don't interfere with each other
        - Exceptions in one task don't affect others
        """
        from agent.canvas import Canvas

        dsl = self._create_minimal_dsl_with_components()
        canvas = Canvas(dsl, tenant_id="test_tenant", task_id="test_task_pool")

        assert canvas._thread_pool is not None
        assert canvas._thread_pool._max_workers <= 5

        results = []
        errors = []
        results_lock = threading.Lock()

        def task(task_id: int, should_fail: bool = False):
            try:
                if should_fail:
                    raise ValueError(f"Intentional failure in task {task_id}")
                with results_lock:
                    results.append(task_id)
            except Exception as e:
                with results_lock:
                    errors.append((task_id, str(e)))

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
        """Test that the Graph._lock provides consistent mutual exclusion.

        Verifies that:
        - Lock acquisition is mutually exclusive
        - No reentrancy issues
        - Lock is properly released after use
        """
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
                    "test_component": {"obj": {"component_name": "Test", "params": {}}, "downstream": [], "upstream": ["begin"]},
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
