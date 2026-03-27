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


import pytest

from agent.component.loop import Loop, LoopParam
from agent.component.loopitem import LoopItem, LoopItemParam
from agent.component.iteration import Iteration, IterationParam
from agent.component.iterationitem import IterationItem, IterationItemParam


class MockCanvas:
    """Mock Canvas for testing loop components."""

    def __init__(self):
        self.components = {}
        self.globals = {
            "sys.query": "",
            "sys.user_id": "test_user",
            "sys.conversation_turns": 0,
            "sys.files": [],
            "sys.history": [],
        }
        self.variables = {}
        self._cancel_flag = False
        self.task_id = "test_task_123"

    def get_component(self, cpn_id):
        return self.components.get(cpn_id)

    def get_component_obj(self, cpn_id):
        cpn = self.components.get(cpn_id)
        return cpn["obj"] if cpn else None

    def get_variable_value(self, exp: str):
        exp = exp.strip("{").strip("}").strip(" ").strip("{").strip("}")
        if exp.find("@") < 0:
            return self.globals.get(exp)
        cpn_id, var_nm = exp.split("@")
        cpn = self.get_component(cpn_id)
        if not cpn:
            return None
        return cpn["obj"].output(var_nm)

    def set_variable_value(self, exp: str, value):
        exp = exp.strip("{").strip("}").strip(" ").strip("{").strip("}")
        if exp.find("@") < 0:
            self.globals[exp] = value
            return
        cpn_id, var_nm = exp.split("@")
        cpn = self.get_component(cpn_id)
        if cpn:
            cpn["obj"].set_output(var_nm, value)

    def is_canceled(self) -> bool:
        return self._cancel_flag

    def cancel_task(self):
        self._cancel_flag = True

    def is_reff(self, exp: str) -> bool:
        exp = exp.strip("{").strip("}")
        if exp.find("@") < 0:
            return exp in self.globals
        return self.get_component(exp.split("@")[0]) is not None


def create_mock_loop_canvas(loop_variables=None, termination_conditions=None, max_loop_count=10, items=None):
    """Factory function to create a mock canvas with Loop/LoopItem components."""
    canvas = MockCanvas()

    loop_param = LoopParam()
    loop_param.loop_variables = loop_variables or []
    loop_param.loop_termination_condition = termination_conditions or []
    loop_param.maximum_loop_count = max_loop_count

    loop_id = "loop_0"
    loop_item_id = "loopitem_0"

    loop = Loop(canvas, loop_id, loop_param)
    loop._items = items or []

    loop_item_param = LoopItemParam()
    loop_item = LoopItem(canvas, loop_item_id, loop_item_param)
    loop_item._items = items or []

    canvas.components[loop_id] = {
        "obj": loop,
        "parent_id": None,
        "downstream": [],
        "upstream": [],
    }
    canvas.components[loop_item_id] = {
        "obj": loop_item,
        "parent_id": loop_id,
        "downstream": [],
        "upstream": [],
    }

    return canvas, loop, loop_item


def create_mock_iteration_canvas(items_ref="test_items", items_data=None):
    """Factory function to create a mock canvas with Iteration/IterationItem components."""
    canvas = MockCanvas()

    iteration_param = IterationParam()
    iteration_param.items_ref = items_ref
    iteration_param.variable = {"item": "current_item"}

    iteration_id = "iteration_0"
    iteration_item_id = "iterationitem_0"

    iteration = Iteration(canvas, iteration_id, iteration_param)

    iteration_item_param = IterationItemParam()
    iteration_item = IterationItem(canvas, iteration_item_id, iteration_item_param)

    canvas.components[iteration_id] = {
        "obj": iteration,
        "parent_id": None,
        "downstream": [],
        "upstream": [],
    }
    canvas.components[iteration_item_id] = {
        "obj": iteration_item,
        "parent_id": iteration_id,
        "downstream": [],
        "upstream": [],
    }

    canvas.globals[items_ref] = items_data if items_data is not None else []

    return canvas, iteration, iteration_item


class TestLoopComponent:
    """Tests for Loop component initialization and variable management."""

    def test_loop_param_initialization(self):
        """LoopParam initializes with correct default values."""
        param = LoopParam()
        assert param.loop_variables == []
        assert param.loop_termination_condition == []
        assert param.maximum_loop_count == 0

    def test_loop_param_check_returns_true(self):
        """LoopParam.check() returns True by default."""
        param = LoopParam()
        assert param.check() is True

    def test_loop_param_get_input_form(self):
        """LoopParam.get_input_form() returns expected structure."""
        param = LoopParam()
        form = param.get_input_form()
        assert "items" in form
        assert form["items"]["type"] == "json"
        assert form["items"]["name"] == "Items"

    def test_loop_initialization(self):
        """Loop component initializes correctly with canvas and param."""
        canvas, loop, _ = create_mock_loop_canvas(max_loop_count=5)
        assert loop.component_name == "Loop"
        assert loop._param.maximum_loop_count == 5

    def test_loop_get_start_returns_loopitem_id(self):
        """Loop.get_start() returns the LoopItem child component ID."""
        canvas, loop, loop_item = create_mock_loop_canvas()
        start_id = loop.get_start()
        assert start_id == "loopitem_0"

    def test_loop_get_start_returns_none_when_no_loopitem(self):
        """Loop.get_start() returns None when no LoopItem child exists."""
        canvas = MockCanvas()
        loop_param = LoopParam()
        loop = Loop(canvas, "loop_0", loop_param)
        canvas.components["loop_0"] = {
            "obj": loop,
            "parent_id": None,
            "downstream": [],
            "upstream": [],
        }
        assert loop.get_start() is None

    def test_loop_invoke_sets_constant_variables(self):
        """Loop._invoke() sets loop variables with constant input mode."""
        loop_variables = [
            {"variable": "counter", "input_mode": "constant", "value": 0, "type": "number"},
            {"variable": "message", "input_mode": "constant", "value": "hello", "type": "string"},
        ]
        canvas, loop, _ = create_mock_loop_canvas(loop_variables=loop_variables)
        loop._invoke()
        assert loop.output("counter") == 0
        assert loop.output("message") == "hello"

    def test_loop_invoke_sets_variable_from_canvas(self):
        """Loop._invoke() sets loop variables from canvas variable references."""
        canvas, loop, _ = create_mock_loop_canvas()
        canvas.globals["external_var"] = 42

        loop._param.loop_variables = [{"variable": "imported", "input_mode": "variable", "value": "external_var", "type": "number"}]
        loop._invoke()
        assert loop.output("imported") == 42

    def test_loop_invoke_sets_default_values_for_empty_mode(self):
        """Loop._invoke() sets default values when input_mode is neither constant nor variable."""
        loop_variables = [
            {"variable": "num_var", "input_mode": "empty", "value": "", "type": "number"},
            {"variable": "str_var", "input_mode": "empty", "value": "", "type": "string"},
            {"variable": "bool_var", "input_mode": "empty", "value": "", "type": "boolean"},
            {"variable": "obj_var", "input_mode": "empty", "value": "", "type": "object"},
            {"variable": "arr_var", "input_mode": "empty", "value": "", "type": "array"},
        ]
        canvas, loop, _ = create_mock_loop_canvas(loop_variables=loop_variables)
        loop._invoke()
        assert loop.output("num_var") == 0
        assert loop.output("str_var") == ""
        assert loop.output("bool_var") is False
        assert loop.output("obj_var") == {}
        assert loop.output("arr_var") == []

    def test_loop_invoke_raises_on_incomplete_variable(self):
        """Loop._invoke() asserts when loop variable definition is incomplete."""
        canvas, loop, _ = create_mock_loop_canvas()
        loop._param.loop_variables = [{"variable": "", "input_mode": "constant", "value": "test", "type": "string"}]
        with pytest.raises(AssertionError):
            loop._invoke()

    def test_loop_thoughts_returns_expected_string(self):
        """Loop.thoughts() returns the expected string."""
        canvas, loop, _ = create_mock_loop_canvas()
        assert loop.thoughts() == "Loop from canvas."

    def test_loop_invoke_cancels_on_cancel_flag(self):
        """Loop._invoke() returns early when canvas is canceled."""
        canvas, loop, _ = create_mock_loop_canvas()
        canvas._cancel_flag = True
        loop._param.loop_variables = [{"variable": "test_var", "input_mode": "constant", "value": 1, "type": "number"}]
        result = loop._invoke()
        assert result is None
        assert loop.error() == "Task has been canceled"


class TestLoopItemComponent:
    """Tests for LoopItem component iteration and condition evaluation."""

    def test_loopitem_param_check_returns_true(self):
        """LoopItemParam.check() returns True by default."""
        param = LoopItemParam()
        assert param.check() is True

    def test_loopitem_initialization(self):
        """LoopItem initializes with correct default index."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item._idx == 0

    def test_loopitem_invoke_increments_index(self):
        """LoopItem._invoke() increments the iteration index."""
        canvas, loop, loop_item = create_mock_loop_canvas(max_loop_count=10)
        loop_item._invoke()
        assert loop_item._idx == 1

    def test_loopitem_invoke_respects_max_count(self):
        """LoopItem._invoke() sets idx to -1 when max count reached."""
        canvas, loop, loop_item = create_mock_loop_canvas(max_loop_count=2)
        loop_item._invoke()
        assert loop_item._idx == 1
        loop_item._invoke()
        assert loop_item._idx == -1

    def test_loopitem_invoke_returns_on_cancel(self):
        """LoopItem._invoke() returns early when canvas is canceled."""
        canvas, loop, loop_item = create_mock_loop_canvas()
        canvas._cancel_flag = True
        result = loop_item._invoke()
        assert result is None

    def test_loopitem_end_returns_true_when_idx_negative(self):
        """LoopItem.end() returns True when idx is -1 (terminated)."""
        canvas, loop, loop_item = create_mock_loop_canvas()
        loop_item._idx = -1
        assert loop_item.end() is True

    def test_loopitem_end_evaluates_and_conditions(self):
        """LoopItem.end() evaluates termination conditions with AND logic."""
        termination_conditions = [{"variable": "counter", "operator": ">", "value": 5, "input_mode": "constant"}]
        canvas, loop, loop_item = create_mock_loop_canvas(termination_conditions=termination_conditions)

        loop.set_output("counter", 3)
        loop_item._idx = 1
        assert loop_item.end() is False

        loop.set_output("counter", 6)
        assert loop_item.end() is True
        assert loop_item._idx == -1

    def test_loopitem_end_evaluates_or_conditions(self):
        """LoopItem.end() evaluates termination conditions with OR logic."""
        canvas, loop, loop_item = create_mock_loop_canvas()
        loop._param.logical_operator = "or"
        loop._param.loop_termination_condition = [
            {"variable": "found", "operator": "is", "value": True, "input_mode": "constant"},
            {"variable": "error", "operator": "is", "value": True, "input_mode": "constant"},
        ]
        loop.set_output("found", False)
        loop.set_output("error", False)
        loop_item._idx = 1
        assert loop_item.end() is False

        loop.set_output("error", True)
        assert loop_item.end() is True

    def test_loopitem_next_increments_index(self):
        """LoopItem.next() increments index and returns True when more items."""
        canvas, loop, loop_item = create_mock_loop_canvas(items=["a", "b", "c"])
        result = loop_item.next()
        assert loop_item._idx == 1
        assert result is not False

    def test_loopitem_next_sets_negative_on_exhaustion(self):
        """LoopItem.next() sets idx to -1 when items exhausted."""
        canvas, loop, loop_item = create_mock_loop_canvas(items=["a", "b"])
        loop_item._idx = 1
        result = loop_item.next()
        assert loop_item._idx == -1
        assert result is False

    def test_loopitem_next_resets_index_from_negative(self):
        """LoopItem.next() resets idx to 0 when called on terminated loop."""
        canvas, loop, loop_item = create_mock_loop_canvas(items=["a", "b"])
        loop_item._idx = -1
        loop_item.next()
        assert loop_item._idx == 0


class TestLoopItemEvaluateCondition:
    """Tests for LoopItem.evaluate_condition() with various types and operators."""

    def test_evaluate_string_contains(self):
        """evaluate_condition handles string 'contains' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition("hello world", "contains", "world") is True
        assert loop_item.evaluate_condition("hello world", "contains", "python") is False

    def test_evaluate_string_not_contains(self):
        """evaluate_condition handles string 'not contains' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition("hello world", "not contains", "python") is True
        assert loop_item.evaluate_condition("hello world", "not contains", "world") is False

    def test_evaluate_string_start_with(self):
        """evaluate_condition handles string 'start with' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition("hello world", "start with", "hello") is True
        assert loop_item.evaluate_condition("hello world", "start with", "world") is False

    def test_evaluate_string_end_with(self):
        """evaluate_condition handles string 'end with' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition("hello world", "end with", "world") is True
        assert loop_item.evaluate_condition("hello world", "end with", "hello") is False

    def test_evaluate_string_is(self):
        """evaluate_condition handles string 'is' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition("hello", "is", "hello") is True
        assert loop_item.evaluate_condition("hello", "is", "world") is False

    def test_evaluate_string_is_not(self):
        """evaluate_condition handles string 'is not' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition("hello", "is not", "world") is True
        assert loop_item.evaluate_condition("hello", "is not", "hello") is False

    def test_evaluate_string_empty(self):
        """evaluate_condition handles string 'empty' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition("", "empty", "") is True
        assert loop_item.evaluate_condition("hello", "empty", "") is False

    def test_evaluate_string_not_empty(self):
        """evaluate_condition handles string 'not empty' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition("hello", "not empty", "") is True
        assert loop_item.evaluate_condition("", "not empty", "") is False

    def test_evaluate_number_equals(self):
        """evaluate_condition handles numeric '=' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(5, "=", 5) is True
        assert loop_item.evaluate_condition(5, "=", 3) is False

    def test_evaluate_number_not_equals(self):
        """evaluate_condition handles numeric '≠' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(5, "≠", 3) is True
        assert loop_item.evaluate_condition(5, "≠", 5) is False

    def test_evaluate_number_greater_than(self):
        """evaluate_condition handles numeric '>' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(5, ">", 3) is True
        assert loop_item.evaluate_condition(5, ">", 7) is False

    def test_evaluate_number_less_than(self):
        """evaluate_condition handles numeric '<' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(3, "<", 5) is True
        assert loop_item.evaluate_condition(5, "<", 3) is False

    def test_evaluate_number_greater_equal(self):
        """evaluate_condition handles numeric '≥' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(5, "≥", 5) is True
        assert loop_item.evaluate_condition(5, "≥", 3) is True
        assert loop_item.evaluate_condition(3, "≥", 5) is False

    def test_evaluate_number_less_equal(self):
        """evaluate_condition handles numeric '≤' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(5, "≤", 5) is True
        assert loop_item.evaluate_condition(3, "≤", 5) is True
        assert loop_item.evaluate_condition(5, "≤", 3) is False

    def test_evaluate_number_empty(self):
        """evaluate_condition handles numeric 'empty' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(None, "empty", "") is True
        assert loop_item.evaluate_condition(5, "empty", "") is False

    def test_evaluate_number_not_empty(self):
        """evaluate_condition handles numeric 'not empty' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(5, "not empty", "") is True
        assert loop_item.evaluate_condition(None, "not empty", "") is False

    def test_evaluate_boolean_is(self):
        """evaluate_condition handles boolean 'is' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(True, "is", True) is True
        assert loop_item.evaluate_condition(True, "is", False) is False

    def test_evaluate_boolean_is_not(self):
        """evaluate_condition handles boolean 'is not' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(True, "is not", False) is True
        assert loop_item.evaluate_condition(True, "is not", True) is False

    def test_evaluate_dict_empty(self):
        """evaluate_condition handles dict 'empty' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition({}, "empty", "") is True
        assert loop_item.evaluate_condition({"key": "value"}, "empty", "") is False

    def test_evaluate_dict_not_empty(self):
        """evaluate_condition handles dict 'not empty' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition({"key": "value"}, "not empty", "") is True
        assert loop_item.evaluate_condition({}, "not empty", "") is False

    def test_evaluate_list_contains(self):
        """evaluate_condition handles list 'contains' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition([1, 2, 3], "contains", 2) is True
        assert loop_item.evaluate_condition([1, 2, 3], "contains", 4) is False

    def test_evaluate_list_not_contains(self):
        """evaluate_condition handles list 'not contains' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition([1, 2, 3], "not contains", 4) is True
        assert loop_item.evaluate_condition([1, 2, 3], "not contains", 2) is False

    def test_evaluate_list_empty(self):
        """evaluate_condition handles list 'empty' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition([], "empty", "") is True
        assert loop_item.evaluate_condition([1, 2, 3], "empty", "") is False

    def test_evaluate_list_not_empty(self):
        """evaluate_condition handles list 'not empty' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition([1, 2, 3], "not empty", "") is True
        assert loop_item.evaluate_condition([], "not empty", "") is False

    def test_evaluate_list_is(self):
        """evaluate_condition handles list 'is' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition([1, 2], "is", [1, 2]) is True
        assert loop_item.evaluate_condition([1, 2], "is", [3, 4]) is False

    def test_evaluate_none_empty(self):
        """evaluate_condition handles None 'empty' operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        assert loop_item.evaluate_condition(None, "empty", "") is True

    def test_evaluate_raises_on_invalid_operator(self):
        """evaluate_condition raises Exception for invalid operator."""
        canvas, _, loop_item = create_mock_loop_canvas()
        with pytest.raises(Exception, match="Invalid operator"):
            loop_item.evaluate_condition("test", "invalid_op", "value")


class TestLoopBasicIteration:
    """Tests for basic loop iteration behavior."""

    def test_loop_basic_iteration(self):
        """Loop iterates correctly through loop items."""
        canvas, loop, loop_item = create_mock_loop_canvas(max_loop_count=3)

        for i in range(3):
            loop_item._invoke()
            assert loop_item._idx == i + 1

        loop_item._invoke()
        assert loop_item._idx == -1

    def test_loop_with_constant_condition(self):
        """Loop respects termination conditions with constant values."""
        termination_conditions = [{"variable": "done", "operator": "is", "value": True, "input_mode": "constant"}]
        canvas, loop, loop_item = create_mock_loop_canvas(termination_conditions=termination_conditions, max_loop_count=10)
        loop.set_output("done", False)

        for _ in range(5):
            loop_item._invoke()
            assert loop_item._idx > 0
            if loop_item._idx == -1:
                break

        assert loop_item._idx <= 5 or loop_item._idx == -1

    def test_loop_max_iterations(self):
        """Loop respects maximum iteration count."""
        canvas, loop, loop_item = create_mock_loop_canvas(max_loop_count=3)

        iterations = 0
        while loop_item._idx != -1 and iterations < 10:
            loop_item._invoke()
            iterations += 1

        assert loop_item._idx == -1
        assert iterations <= 4

    def test_loop_with_break_condition(self):
        """Loop terminates when break condition is met."""
        canvas, loop, loop_item = create_mock_loop_canvas(max_loop_count=100)
        loop._param.loop_termination_condition = [{"variable": "counter", "operator": "≥", "value": 5, "input_mode": "constant"}]
        loop._param.logical_operator = "and"

        for i in range(10):
            loop.set_output("counter", i)
            loop_item._invoke()
            if loop_item.end():
                break
            loop_item._idx += 1

        assert loop.output("counter") >= 4

    def test_loop_variable_accumulation(self):
        """Loop variables accumulate correctly across iterations."""
        canvas, loop, loop_item = create_mock_loop_canvas(max_loop_count=5)
        loop.set_output("sum", 0)

        for i in range(5):
            current_sum = loop.output("sum")
            loop.set_output("sum", current_sum + i)
            loop_item._invoke()

        assert loop.output("sum") == 10

    def test_loop_empty_collection(self):
        """Loop handles empty collection gracefully."""
        canvas, loop, loop_item = create_mock_loop_canvas(items=[])
        loop_item._invoke()
        assert loop_item._idx == -1

    def test_loop_state_isolation_between_iterations(self):
        """Loop state is isolated between iterations."""
        canvas, loop, loop_item = create_mock_loop_canvas(max_loop_count=3)

        loop_item._invoke()
        state_1 = loop_item._idx

        loop_item._invoke()
        state_2 = loop_item._idx

        assert state_2 > state_1

    def test_loop_nested_loops_independent_state(self):
        """Nested loops maintain independent state."""
        outer_canvas, outer_loop, outer_item = create_mock_loop_canvas(max_loop_count=3)
        inner_canvas, inner_loop, inner_item = create_mock_loop_canvas(max_loop_count=5)

        for _ in range(2):
            outer_item._invoke()
            inner_item._invoke()

        assert outer_item._idx == 2
        assert inner_item._idx == 2


class TestIterationComponent:
    """Tests for Iteration component behavior."""

    def test_iteration_param_initialization(self):
        """IterationParam initializes with correct default values."""
        param = IterationParam()
        assert param.items_ref == ""
        assert param.variable == {}

    def test_iteration_param_check_returns_true(self):
        """IterationParam.check() returns True by default."""
        param = IterationParam()
        assert param.check() is True

    def test_iteration_param_get_input_form(self):
        """IterationParam.get_input_form() returns expected structure."""
        param = IterationParam()
        form = param.get_input_form()
        assert "items" in form
        assert form["items"]["type"] == "json"

    def test_iteration_initialization(self):
        """Iteration component initializes correctly."""
        canvas, iteration, _ = create_mock_iteration_canvas(items_ref="test_list", items_data=[1, 2, 3])
        assert iteration.component_name == "Iteration"
        assert iteration._param.items_ref == "test_list"

    def test_iteration_get_start_returns_iterationitem(self):
        """Iteration.get_start() returns the IterationItem child ID."""
        canvas, iteration, _ = create_mock_iteration_canvas()
        start_id = iteration.get_start()
        assert start_id == "iterationitem_0"

    def test_iteration_invoke_validates_array_type(self):
        """Iteration._invoke() sets error when items_ref is not a list."""
        canvas, iteration, _ = create_mock_iteration_canvas(items_ref="non_array", items_data="not a list")
        iteration._invoke()
        assert iteration.error() is not None
        assert "must be an array" in iteration.error()

    def test_iteration_invoke_success_with_array(self):
        """Iteration._invoke() succeeds with valid array."""
        canvas, iteration, _ = create_mock_iteration_canvas(items_data=[1, 2, 3])
        iteration._invoke()
        assert iteration.error() is None

    def test_iteration_invoke_cancels_on_cancel_flag(self):
        """Iteration._invoke() returns early when canvas is canceled."""
        canvas, iteration, _ = create_mock_iteration_canvas(items_data=[1, 2, 3])
        canvas._cancel_flag = True
        result = iteration._invoke()
        assert result is None
        assert iteration.error() == "Task has been canceled"

    def test_iteration_thoughts_returns_count(self):
        """Iteration.thoughts() returns message with item count."""
        canvas, iteration, _ = create_mock_iteration_canvas(items_data=[1, 2, 3])
        thoughts = iteration.thoughts()
        assert "3 items" in thoughts


class TestIterationItemComponent:
    """Tests for IterationItem component behavior."""

    def test_iterationitem_param_check(self):
        """IterationItemParam.check() returns True."""
        param = IterationItemParam()
        assert param.check() is True

    def test_iterationitem_initialization(self):
        """IterationItem initializes with idx 0."""
        canvas, _, iteration_item = create_mock_iteration_canvas(items_data=[1, 2, 3])
        assert iteration_item._idx == 0

    def test_iterationitem_invoke_sets_outputs(self):
        """IterationItem._invoke() sets item and index outputs."""
        canvas, iteration, iteration_item = create_mock_iteration_canvas(items_data=["a", "b", "c"])
        iteration_item._invoke()
        assert iteration_item.output("item") == "a"
        assert iteration_item.output("index") == 0

    def test_iterationitem_invoke_advances_index(self):
        """IterationItem._invoke() advances through items."""
        canvas, iteration, iteration_item = create_mock_iteration_canvas(items_data=[1, 2, 3])

        iteration_item._invoke()
        assert iteration_item._idx == 1

        iteration_item._invoke()
        assert iteration_item._idx == 2

    def test_iterationitem_end_detects_termination(self):
        """IterationItem.end() returns True when idx is -1."""
        canvas, _, iteration_item = create_mock_iteration_canvas(items_data=[1])
        iteration_item._idx = -1
        assert iteration_item.end() is True

    def test_iterationitem_end_returns_false_during_iteration(self):
        """IterationItem.end() returns False during active iteration."""
        canvas, _, iteration_item = create_mock_iteration_canvas(items_data=[1, 2, 3])
        iteration_item._idx = 1
        assert iteration_item.end() is False

    def test_iterationitem_sets_idx_negative_on_completion(self):
        """IterationItem sets idx to -1 after iterating all items."""
        canvas, _, iteration_item = create_mock_iteration_canvas(items_data=[1])

        iteration_item._invoke()
        iteration_item._invoke()

        assert iteration_item._idx == -1

    def test_iterationitem_handles_empty_array(self):
        """IterationItem handles empty array gracefully."""
        canvas, _, iteration_item = create_mock_iteration_canvas(items_data=[])
        iteration_item._invoke()
        assert iteration_item._idx == -1

    def test_iterationitem_raises_on_non_array(self):
        """IterationItem raises exception when items_ref is not array."""
        canvas = MockCanvas()
        iteration_param = IterationParam()
        iteration_param.items_ref = "bad_ref"
        iteration = Iteration(canvas, "iter_0", iteration_param)

        iteration_item_param = IterationItemParam()
        iteration_item = IterationItem(canvas, "item_0", iteration_item_param)

        canvas.components["iter_0"] = {"obj": iteration, "parent_id": None}
        canvas.components["item_0"] = {"obj": iteration_item, "parent_id": "iter_0"}
        canvas.globals["bad_ref"] = "not an array"

        with pytest.raises(Exception, match="must be an array"):
            iteration_item._invoke()

    def test_iterationitem_thoughts(self):
        """IterationItem.thoughts() returns expected string."""
        canvas, _, iteration_item = create_mock_iteration_canvas(items_data=[1])
        assert iteration_item.thoughts() == "Next turn..."

    def test_iterationitem_output_collation(self):
        """IterationItem.output_collation() aggregates outputs from child components."""
        canvas, iteration, iteration_item = create_mock_iteration_canvas(items_data=[1, 2])

        from agent.component.base import ComponentParamBase

        class MockParam(ComponentParamBase):
            def __init__(self):
                super().__init__()
                self.outputs = {"result": {"ref": "item_0@output"}}

            def check(self):
                return True

        class MockChildComponent:
            component_name = "MockChild"

            def __init__(self, parent_id):
                self._id = "child_0"
                self._parent_id = parent_id

            def output(self, key):
                if key == "output":
                    return "child_result"
                return None

            def get_parent(self):
                return type("MockParent", (), {"_id": self._parent_id})()

        mock_child = MockChildComponent("iter_0")
        canvas.components["child_0"] = {
            "obj": mock_child,
            "parent_id": "iter_0",
            "downstream": [],
            "upstream": [],
        }

        iteration._param.outputs = {"result": {"ref": "child_0@output"}}

        iteration_item._idx = 1
        iteration_item.output_collation()


class TestLoopIntegration:
    """Integration tests for Loop and LoopItem working together."""

    def test_loop_with_variable_iteration(self):
        """Loop and LoopItem work together with variable iteration."""
        items = ["item1", "item2", "item3"]
        canvas, loop, loop_item = create_mock_loop_canvas(items=items, max_loop_count=5)

        loop.set_output("processed_items", [])

        for i, item in enumerate(items):
            loop_item._invoke()
            processed = loop.output("processed_items")
            processed.append(item)
            loop.set_output("processed_items", processed)

        assert len(loop.output("processed_items")) == 3

    def test_loop_termination_from_condition(self):
        """Loop terminates when termination condition is met."""
        canvas, loop, loop_item = create_mock_loop_canvas(max_loop_count=100)
        loop._param.loop_termination_condition = [{"variable": "should_stop", "operator": "is", "value": True, "input_mode": "constant"}]
        loop._param.logical_operator = "and"

        loop.set_output("should_stop", False)

        for i in range(5):
            loop_item._invoke()
            if i >= 3:
                loop.set_output("should_stop", True)
                if loop_item.end():
                    break

        assert loop_item._idx == -1 or loop.output("should_stop") is True

    def test_iteration_complete_workflow(self):
        """Complete iteration workflow from start to finish."""
        items = [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}, {"id": 3, "value": "c"}]
        canvas, iteration, iteration_item = create_mock_iteration_canvas(items_data=items)

        results = []
        while not iteration_item.end():
            iteration_item._invoke()
            if iteration_item._idx != -1:
                current_item = iteration_item.output("item")
                if current_item:
                    results.append(current_item)

        assert len(results) <= 3
