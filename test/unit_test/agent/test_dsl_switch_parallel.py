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

from agent.canvas import Canvas


class TestDSLSwitchParsing:
    """Tests for Switch component parsing in DSL."""

    def _create_switch_dsl(self) -> dict:
        return {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {}},
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
                                    "items": [
                                        {"cpn_id": "categorize_0@category_name", "operator": "contains", "value": "technical"},
                                    ],
                                    "to": ["exitloop_0"],
                                },
                            ],
                            "end_cpn_ids": ["exitloop_1"],
                        },
                    },
                    "downstream": ["exitloop_0", "exitloop_1"],
                    "upstream": ["begin"],
                },
                "exitloop_0": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": [],
                    "upstream": ["switch_0"],
                },
                "exitloop_1": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": [],
                    "upstream": ["switch_0"],
                },
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }

    def test_switch_parsing(self):
        dsl = self._create_switch_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "switch_0" in canvas.components
        switch = canvas.components["switch_0"]["obj"]
        assert switch.component_name == "Switch"
        assert len(switch._param.conditions) == 1
        assert switch._param.conditions[0]["logical_operator"] == "and"

    def test_switch_condition_parsing(self):
        dsl = self._create_switch_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        switch = canvas.components["switch_0"]["obj"]
        condition = switch._param.conditions[0]
        assert condition["items"][0]["cpn_id"] == "categorize_0@category_name"
        assert condition["items"][0]["operator"] == "contains"
        assert condition["items"][0]["value"] == "technical"
        assert condition["to"] == ["exitloop_0"]

    def test_switch_else_route_parsing(self):
        dsl = self._create_switch_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        switch = canvas.components["switch_0"]["obj"]
        assert switch._param.end_cpn_ids == ["exitloop_1"]


class TestDSLParallelExecution:
    """Tests for parallel execution configuration in DSL."""

    def test_thread_pool_executor_initialized(self):
        dsl = {
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
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert canvas._thread_pool is not None

    def test_multiple_components_parallel_ready(self):
        dsl = {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {}},
                    "downstream": ["exit1", "exit2", "exit3"],
                    "upstream": [],
                },
                "exit1": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": [],
                    "upstream": ["begin"],
                },
                "exit2": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": [],
                    "upstream": ["begin"],
                },
                "exit3": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": [],
                    "upstream": ["begin"],
                },
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert len(canvas.components) == 4
        begin_downstream = canvas.components["begin"]["downstream"]
        assert len(begin_downstream) == 3
