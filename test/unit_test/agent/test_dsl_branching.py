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
from unittest.mock import patch

from agent.canvas import Canvas


def _mock_categorize_init(self, canvas, component_id, param):
    from agent.component.base import ComponentBase

    ComponentBase.__init__(self, canvas, component_id, param)


class TestDSLBranchingFlow:
    """Tests for branching flow (Categorize/Switch) parsing."""

    def _create_categorize_dsl(self) -> dict:
        return {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {}},
                    "downstream": ["categorize_0"],
                    "upstream": [],
                },
                "categorize_0": {
                    "obj": {
                        "component_name": "Categorize",
                        "params": {
                            "category_description": {
                                "technical": {"to": ["exitloop_0"], "description": "Tech questions"},
                                "general": {"to": ["exitloop_1"], "description": "General questions"},
                            },
                            "query": "sys.query",
                            "llm_id": "llm1",
                        },
                    },
                    "downstream": ["exitloop_0", "exitloop_1"],
                    "upstream": ["begin"],
                },
                "exitloop_0": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": [],
                    "upstream": ["categorize_0"],
                },
                "exitloop_1": {
                    "obj": {"component_name": "ExitLoop", "params": {}},
                    "downstream": [],
                    "upstream": ["categorize_0"],
                },
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }

    @patch("agent.component.categorize.Categorize.__init__", _mock_categorize_init)
    def test_categorize_parsing(self):
        dsl = self._create_categorize_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "categorize_0" in canvas.components
        categorize = canvas.components["categorize_0"]["obj"]
        assert categorize.component_name == "Categorize"
        assert "technical" in categorize._param.category_description
        assert "general" in categorize._param.category_description

    @patch("agent.component.categorize.Categorize.__init__", _mock_categorize_init)
    def test_categorize_routing_parsing(self):
        dsl = self._create_categorize_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        categorize = canvas.components["categorize_0"]["obj"]
        assert categorize._param.category_description["technical"]["to"] == ["exitloop_0"]
        assert categorize._param.category_description["general"]["to"] == ["exitloop_1"]

    @patch("agent.component.categorize.Categorize.__init__", _mock_categorize_init)
    def test_categorize_downstream_routes(self):
        dsl = self._create_categorize_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert set(canvas.components["categorize_0"]["downstream"]) == {"exitloop_0", "exitloop_1"}
