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

import json
import pytest

from agent.canvas import Canvas


class TestComponentGraphConversion:
    """Tests for DSL to component graph conversion."""

    def _create_linear_dsl(self) -> dict:
        return {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {"prologue": "Hello"}},
                    "downstream": ["switch_0"],
                    "upstream": [],
                },
                "switch_0": {
                    "obj": {
                        "component_name": "Switch",
                        "params": {
                            "conditions": [
                                {
                                    "logical_operator": "and",
                                    "items": [{"cpn_id": "begin", "operator": "contains", "value": "test"}],
                                    "to": ["exitloop_0"],
                                }
                            ],
                            "end_cpn_ids": ["exitloop_0"],
                        },
                    },
                    "downstream": ["exitloop_0"],
                    "upstream": ["begin"],
                },
                "exitloop_0": {
                    "obj": {
                        "component_name": "ExitLoop",
                        "params": {},
                    },
                    "downstream": [],
                    "upstream": ["switch_0"],
                },
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }

    def test_linear_graph_parsing(self):
        dsl = self._create_linear_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert len(canvas.components) == 3
        assert canvas.components["begin"]["downstream"] == ["switch_0"]
        assert canvas.components["switch_0"]["upstream"] == ["begin"]

    def test_component_downstream_navigation(self):
        dsl = self._create_linear_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        begin_downstream = canvas.components["begin"]["downstream"]
        assert begin_downstream == ["switch_0"]
        switch_downstream = canvas.components["switch_0"]["downstream"]
        assert switch_downstream == ["exitloop_0"]

    def test_component_upstream_navigation(self):
        dsl = self._create_linear_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        exit_upstream = canvas.components["exitloop_0"]["upstream"]
        assert exit_upstream == ["switch_0"]

    def test_get_component_by_id(self):
        dsl = self._create_linear_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        switch = canvas.get_component("switch_0")
        assert switch is not None
        assert switch["obj"].component_name == "Switch"

    def test_get_nonexistent_component_returns_none(self):
        dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert canvas.get_component("nonexistent") is None

    def _create_minimal_dsl(self) -> dict:
        return {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {}},
                    "downstream": [],
                    "upstream": [],
                }
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }


class TestDSLCyclicalReferences:
    """Tests for handling cyclical references in DSL."""

    def _create_cyclic_dsl(self) -> dict:
        return {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {}},
                    "downstream": ["a"],
                    "upstream": [],
                },
                "a": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": ["b"],
                    "upstream": ["begin"],
                },
                "b": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": ["a"],
                    "upstream": ["a"],
                },
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }

    def test_cyclic_reference_allowed(self):
        dsl = self._create_cyclic_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "a" in canvas.components
        assert "b" in canvas.components


class TestDSLComponentValidation:
    """Tests for component validation during DSL parsing."""

    def test_invalid_component_type_raises_error(self):
        dsl = {
            "components": {
                "begin": {
                    "obj": {"component_name": "NonexistentComponent", "params": {}},
                    "downstream": [],
                    "upstream": [],
                }
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }
        with pytest.raises(Exception):
            Canvas(json.dumps(dsl), tenant_id="test_tenant")

    def test_component_nesting_too_deep(self):
        deeply_nested = {"component_name": "Begin", "params": {}}
        current = deeply_nested
        for _ in range(25):
            current["nested"] = {"component_name": "Begin", "params": {}}
            current = current["nested"]
        dsl = {
            "components": {"begin": {"obj": deeply_nested, "downstream": [], "upstream": []}},
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }
        with pytest.raises(ValueError, match="nesting too deep"):
            Canvas(json.dumps(dsl), tenant_id="test_tenant")
