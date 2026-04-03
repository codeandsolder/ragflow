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


class TestDSLLoopIteration:
    """Tests for loop/iteration component parsing."""

    def _create_loop_dsl(self) -> dict:
        return {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {}},
                    "downstream": ["loop_0"],
                    "upstream": [],
                },
                "loop_0": {
                    "obj": {
                        "component_name": "Loop",
                        "params": {
                            "loop_variables": [
                                {
                                    "variable": "item",
                                    "input_mode": "variable",
                                    "value": "items",
                                    "type": "string",
                                }
                            ],
                            "loop_termination_condition": [],
                            "maximum_loop_count": 10,
                        },
                    },
                    "downstream": ["loopitem_0"],
                    "upstream": ["begin"],
                },
                "loopitem_0": {
                    "obj": {"component_name": "LoopItem", "params": {}},
                    "downstream": ["generate_0"],
                    "upstream": ["loop_0"],
                    "parent_id": "loop_0",
                },
                "generate_0": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": [],
                    "upstream": ["loopitem_0"],
                },
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }

    def test_loop_parsing(self):
        dsl = self._create_loop_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "loop_0" in canvas.components
        loop = canvas.components["loop_0"]["obj"]
        assert loop.component_name == "Loop"
        assert loop._param.maximum_loop_count == 10

    def test_loop_variables_parsing(self):
        dsl = self._create_loop_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        loop = canvas.components["loop_0"]["obj"]
        assert len(loop._param.loop_variables) == 1
        assert loop._param.loop_variables[0]["variable"] == "item"
        assert loop._param.loop_variables[0]["input_mode"] == "variable"

    def test_loopitem_parsing(self):
        dsl = self._create_loop_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "loopitem_0" in canvas.components
        loopitem = canvas.components["loopitem_0"]["obj"]
        assert loopitem.component_name == "LoopItem"

    def test_loopitem_parent_relationship(self):
        dsl = self._create_loop_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        loopitem = canvas.components["loopitem_0"]
        assert loopitem.get("parent_id") == "loop_0"

    def test_loop_get_start_finds_child(self):
        dsl = self._create_loop_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        loop = canvas.components["loop_0"]["obj"]
        start_cid = loop.get_start()
        assert start_cid == "loopitem_0"

    def _create_iteration_dsl(self) -> dict:
        return {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {}},
                    "downstream": ["iteration_0"],
                    "upstream": [],
                },
                "iteration_0": {
                    "obj": {
                        "component_name": "Iteration",
                        "params": {
                            "items_ref": "items",
                            "variable": {"data_type": "string"},
                        },
                    },
                    "downstream": ["iterationitem_0"],
                    "upstream": ["begin"],
                },
                "iterationitem_0": {
                    "obj": {"component_name": "IterationItem", "params": {}},
                    "downstream": ["generate_0"],
                    "upstream": ["iteration_0"],
                    "parent_id": "iteration_0",
                },
                "generate_0": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": [],
                    "upstream": ["iterationitem_0"],
                },
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }

    def test_iteration_parsing(self):
        dsl = self._create_iteration_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "iteration_0" in canvas.components
        iteration = canvas.components["iteration_0"]["obj"]
        assert iteration.component_name == "Iteration"
        assert iteration._param.items_ref == "items"

    def test_iterationitem_parsing(self):
        dsl = self._create_iteration_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "iterationitem_0" in canvas.components
        iterationitem = canvas.components["iterationitem_0"]["obj"]
        assert iterationitem.component_name == "IterationItem"

    def test_iterationitem_parent_relationship(self):
        dsl = self._create_iteration_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        iterationitem = canvas.components["iterationitem_0"]
        assert iterationitem.get("parent_id") == "iteration_0"

    def test_iteration_get_start_finds_child(self):
        dsl = self._create_iteration_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        iteration = canvas.components["iteration_0"]["obj"]
        start_cid = iteration.get_start()
        assert start_cid == "iterationitem_0"
