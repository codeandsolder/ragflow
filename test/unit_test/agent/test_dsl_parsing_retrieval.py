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

from agent.canvas import Canvas, Graph


class TestDSLRetrievalParsing:
    """Tests for retrieval section parsing in DSL."""

    def test_retrieval_initialization(self):
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
            "retrieval": {"chunks": {"c1": {"id": "c1"}}, "doc_aggs": {"d1": {"doc_name": "d1"}}},
        }
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert canvas.retrieval is not None

    def test_retrieval_default_empty(self):
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
            "retrieval": [],
        }
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert canvas.retrieval == []


class TestGraphDSLParsing:
    """Tests for Graph class DSL parsing."""

    def test_graph_load_components(self):
        dsl = json.dumps(
            {
                "components": {
                    "begin": {
                        "obj": {"component_name": "Begin", "params": {}},
                        "downstream": [],
                        "upstream": [],
                    }
                },
                "path": ["begin"],
            }
        )
        graph = Graph(dsl, tenant_id="test_tenant")
        assert "begin" in graph.components

    def test_graph_path_initialization(self):
        dsl = json.dumps(
            {
                "components": {
                    "begin": {
                        "obj": {"component_name": "Begin", "params": {}},
                        "downstream": [],
                        "upstream": [],
                    }
                },
                "path": ["begin", "next"],
            }
        )
        graph = Graph(dsl, tenant_id="test_tenant")
        assert graph.path == ["begin", "next"]

    def test_graph_reset(self):
        dsl = json.dumps(
            {
                "components": {
                    "begin": {
                        "obj": {"component_name": "Begin", "params": {}},
                        "downstream": [],
                        "upstream": [],
                    }
                },
                "path": ["begin", "next"],
            }
        )
        graph = Graph(dsl, tenant_id="test_tenant")
        graph.reset()
        assert graph.path == []


class TestDSLMemoryParsing:
    """Tests for memory section parsing in DSL."""

    def test_memory_initialization(self):
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
            "memory": [("user", "Hello", "Greeting")],
        }
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert len(canvas.memory) == 1
        assert list(canvas.memory[0]) == ["user", "Hello", "Greeting"]

    def test_memory_default_empty(self):
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
        assert canvas.memory == []
