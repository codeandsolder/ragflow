import pytest
from typing import Any

from agent.component.switch import Switch, SwitchParam


class MockCanvas:
    """Mock Canvas class for testing Switch component."""

    def __init__(self):
        self.components = {}
        self.variables = {}

    def get_variable_value(self, exp: str) -> Any:
        if exp in self.variables:
            return self.variables[exp]
        return None

    def get_component_name(self, cpn_id: str) -> str:
        return f"Component_{cpn_id}"

    def get_component(self, cpn_id: str) -> dict:
        return self.components.get(cpn_id, {})

    def is_canceled(self) -> bool:
        return False


class TestSwitchComponent:
    """Comprehensive tests for Switch component."""

    @pytest.fixture
    def mock_canvas(self):
        return MockCanvas()

    @pytest.fixture
    def switch_param(self):
        return SwitchParam()

    @pytest.fixture
    def switch_instance(self, mock_canvas, switch_param):
        switch = Switch(mock_canvas, "switch_0", switch_param)
        return switch

    def test_process_operator_contains(self, switch_instance):
        assert switch_instance.process_operator("Hello World", "contains", "hello") is True
        assert switch_instance.process_operator("Hello World", "contains", "world") is True
        assert switch_instance.process_operator("Hello World", "contains", "test") is False

    def test_process_operator_not_contains(self, switch_instance):
        assert switch_instance.process_operator("Hello World", "not contains", "test") is True
        assert switch_instance.process_operator("Hello World", "not contains", "hello") is False

    def test_process_operator_starts_with(self, switch_instance):
        assert switch_instance.process_operator("Hello World", "start with", "hello") is True
        assert switch_instance.process_operator("Hello World", "start with", "world") is False

    def test_process_operator_ends_with(self, switch_instance):
        assert switch_instance.process_operator("Hello World", "end with", "world") is True
        assert switch_instance.process_operator("Hello World", "end with", "hello") is False

    def test_process_operator_empty(self, switch_instance):
        assert switch_instance.process_operator("", "empty", "") is True
        assert switch_instance.process_operator("Hello", "empty", "") is False
        assert switch_instance.process_operator(None, "empty", "") is True

    def test_process_operator_not_empty(self, switch_instance):
        assert switch_instance.process_operator("Hello", "not empty", "") is True
        assert switch_instance.process_operator("", "not empty", "") is False
        assert switch_instance.process_operator(None, "not empty", "") is False

    def test_process_operator_equals(self, switch_instance):
        assert switch_instance.process_operator("Hello", "=", "Hello") is True
        assert switch_instance.process_operator("Hello", "=", "hello") is False
        assert switch_instance.process_operator(123, "=", 123) is True
        assert switch_instance.process_operator(123, "=", "123") is False

    def test_process_operator_not_equals(self, switch_instance):
        assert switch_instance.process_operator("Hello", "≠", "hello") is True
        assert switch_instance.process_operator("Hello", "≠", "Hello") is False
        assert switch_instance.process_operator(123, "≠", 456) is True

    def test_process_operator_greater_than_numeric(self, switch_instance):
        assert switch_instance.process_operator(10, ">", 5) is True
        assert switch_instance.process_operator(5, ">", 10) is False
        assert switch_instance.process_operator("10", ">", "5") is True
        assert switch_instance.process_operator("5", ">", "10") is False

    def test_process_operator_greater_than_string(self, switch_instance):
        assert switch_instance.process_operator("b", ">", "a") is True
        assert switch_instance.process_operator("a", ">", "b") is False

    def test_process_operator_less_than_numeric(self, switch_instance):
        assert switch_instance.process_operator(5, "<", 10) is True
        assert switch_instance.process_operator(10, "<", 5) is False
        assert switch_instance.process_operator("5", "<", "10") is True

    def test_process_operator_less_than_string(self, switch_instance):
        assert switch_instance.process_operator("a", "<", "b") is True
        assert switch_instance.process_operator("b", "<", "a") is False

    def test_process_operator_greater_equal_numeric(self, switch_instance):
        assert switch_instance.process_operator(10, "≥", 10) is True
        assert switch_instance.process_operator(10, "≥", 5) is True
        assert switch_instance.process_operator(5, "≥", 10) is False

    def test_process_operator_greater_equal_string(self, switch_instance):
        assert switch_instance.process_operator("b", "≥", "a") is True
        assert switch_instance.process_operator("a", "≥", "a") is True

    def test_process_operator_less_equal_numeric(self, switch_instance):
        assert switch_instance.process_operator(10, "≤", 10) is True
        assert switch_instance.process_operator(5, "≤", 10) is True
        assert switch_instance.process_operator(10, "≤", 5) is False

    def test_process_operator_less_equal_string(self, switch_instance):
        assert switch_instance.process_operator("a", "≤", "b") is True
        assert switch_instance.process_operator("a", "≤", "a") is True

    def test_multiple_conditions_and_logic(self, mock_canvas):
        mock_canvas.variables = {"categorize:0": "Hello World", "other:0": "test data"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "and",
                "items": [
                    {"cpn_id": "categorize:0", "operator": "contains", "value": "hello"},
                    {"cpn_id": "other:0", "operator": "contains", "value": "test"},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_multiple_conditions_or_logic(self, mock_canvas):
        mock_canvas.variables = {"categorize:0": "Hello World", "other:0": "test data"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "categorize:0", "operator": "contains", "value": "hello"},
                    {"cpn_id": "other:0", "operator": "contains", "value": "missing"},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_case_insensitivity(self, mock_canvas):
        mock_canvas.variables = {"categorize:0": "Hello World"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "categorize:0", "operator": "contains", "value": "HELLO"},
                    {"cpn_id": "categorize:0", "operator": "start with", "value": "HELLO"},
                    {"cpn_id": "categorize:0", "operator": "end with", "value": "WORLD"},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_numeric_string_coercion(self, mock_canvas):
        mock_canvas.variables = {"categorize:0": 10.5, "other:0": "15"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "categorize:0", "operator": ">", "value": "5"},
                    {"cpn_id": "other:0", "operator": "<", "value": "20"},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_empty_input_handling(self, mock_canvas):
        mock_canvas.variables = {"categorize:0": ""}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "categorize:0", "operator": "empty", "value": ""},
                    {"cpn_id": "categorize:0", "operator": "contains", "value": "test"},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_null_value_handling(self, mock_canvas):
        mock_canvas.variables = {"categorize:0": None}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "categorize:0", "operator": "empty", "value": ""},
                    {"cpn_id": "categorize:0", "operator": "not empty", "value": ""},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_switch_selects_correct_branch(self, mock_canvas):
        mock_canvas.variables = {"input:0": "Category A", "input:1": "123"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "input:0", "operator": "contains", "value": "A"},
                    {"cpn_id": "input:1", "operator": "=", "value": "123"},
                ],
                "to": ["branchA"],
            },
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "input:0", "operator": "contains", "value": "B"},
                    {"cpn_id": "input:1", "operator": "=", "value": "456"},
                ],
                "to": ["branchB"],
            },
        ]
        switch_param.end_cpn_ids = ["default"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branchA"]
        assert switch.output("_next") == ["branchA"]

    def test_cascade_fallback_behavior(self, mock_canvas):
        mock_canvas.variables = {"input:0": "Category C", "input:1": "789"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "input:0", "operator": "contains", "value": "A"},
                    {"cpn_id": "input:1", "operator": "=", "value": "123"},
                ],
                "to": ["branchA"],
            },
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "input:0", "operator": "contains", "value": "B"},
                    {"cpn_id": "input:1", "operator": "=", "value": "456"},
                ],
                "to": ["branchB"],
            },
        ]
        switch_param.end_cpn_ids = ["default"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_default"]
        assert switch.output("_next") == ["default"]

    def test_param_validation(self):
        param = SwitchParam()

        param.conditions = []
        with pytest.raises(ValueError, match=r"\[Switch\] conditions"):
            param.check()

        param.conditions = [{"cpn_id": "test", "operator": "contains", "value": "test", "to": ""}]
        with pytest.raises(ValueError, match=r"\[Switch\] 'To' can not be empty!"):
            param.check()

        param.conditions = [{"cpn_id": "test", "operator": "contains", "value": "test", "to": ["branch"]}]
        param.end_cpn_ids = []
        with pytest.raises(ValueError, match=r"\[Switch\] the ELSE/Other destination can not be empty."):
            param.check()

    def test_get_input_form(self, switch_instance):
        form = switch_instance.get_input_form()
        assert form == {"urls": {"name": "URLs", "type": "line"}}

    def test_unsupported_operator(self, switch_instance):
        with pytest.raises(ValueError, match="Not supported operator"):
            switch_instance.process_operator("test", "invalid_op", "value")

    def test_invoke_operator_not_contains(self, mock_canvas):
        mock_canvas.variables = {"input:0": "Hello World"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "input:0", "operator": "not contains", "value": "test"},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_invoke_operator_not_equals(self, mock_canvas):
        mock_canvas.variables = {"input:0": "Hello", "input:1": 123}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "input:0", "operator": "≠", "value": "world"},
                    {"cpn_id": "input:1", "operator": "≠", "value": 456},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_invoke_operator_greater_equal(self, mock_canvas):
        mock_canvas.variables = {"num1": 10, "num2": 10, "num3": 5}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "num1", "operator": "≥", "value": 10},
                    {"cpn_id": "num2", "operator": "≥", "value": 5},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_invoke_operator_less_equal(self, mock_canvas):
        mock_canvas.variables = {"num1": 10, "num2": 5, "num3": 10}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "num1", "operator": "≤", "value": 10},
                    {"cpn_id": "num2", "operator": "≤", "value": 10},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_empty_whitespace_only_input(self, switch_instance):
        assert switch_instance.process_operator("   ", "empty", "") is True
        assert switch_instance.process_operator("   ", "not empty", "") is False

    def test_numeric_zero_for_empty(self, switch_instance):
        assert switch_instance.process_operator(0, "empty", "") is True
        assert switch_instance.process_operator(0, "not empty", "") is False

    def test_empty_value_parameter_contains(self, switch_instance):
        assert switch_instance.process_operator("hello", "contains", "") is True
        assert switch_instance.process_operator("", "contains", "") is True
        assert switch_instance.process_operator("hello", "start with", "") is True
        assert switch_instance.process_operator("hello", "end with", "") is True

    def test_invoke_empty_value_parameter(self, mock_canvas):
        mock_canvas.variables = {"input:0": "Hello World"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "input:0", "operator": "contains", "value": ""},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_empty_items_array(self, mock_canvas):
        mock_canvas.variables = {"input:0": "test"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_fallback"]
        assert switch.output("_next") == ["fallback"]

    def test_single_item_condition(self, mock_canvas):
        mock_canvas.variables = {"input:0": "Hello World"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "and",
                "items": [
                    {"cpn_id": "input:0", "operator": "contains", "value": "hello"},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]

    def test_short_circuit_evaluation_and(self, mock_canvas):
        mock_canvas.variables = {"input:0": "Hello", "input:1": "World"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "and",
                "items": [
                    {"cpn_id": "input:0", "operator": "contains", "value": "xyz"},
                    {"cpn_id": "input:1", "operator": "contains", "value": "missing"},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_fallback"]
        assert switch.output("_next") == ["fallback"]

    def test_short_circuit_evaluation_or(self, mock_canvas):
        mock_canvas.variables = {"input:0": "Hello", "input:1": "World"}

        switch_param = SwitchParam()
        switch_param.conditions = [
            {
                "logical_operator": "or",
                "items": [
                    {"cpn_id": "input:0", "operator": "contains", "value": "hello"},
                    {"cpn_id": "input:1", "operator": "contains", "value": "missing"},
                ],
                "to": ["branch1"],
            }
        ]
        switch_param.end_cpn_ids = ["fallback"]

        switch = Switch(mock_canvas, "switch_0", switch_param)
        switch._invoke()

        assert switch.output("next") == ["Component_branch1"]
        assert switch.output("_next") == ["branch1"]
