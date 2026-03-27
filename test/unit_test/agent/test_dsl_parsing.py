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

import sys
import types
import json
import pytest


def create_stub(name, attrs=None):
    """Create a stub module and add it to sys.modules."""
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        mod_name = ".".join(parts[:i])
        if mod_name not in sys.modules:
            stub = types.ModuleType(mod_name)
            sys.modules[mod_name] = stub

    if attrs:
        for k, v in attrs.items():
            setattr(sys.modules[name], k, v)


create_stub("api.db.services.task_service")
sys.modules["api.db.services.task_service"].has_canceled = lambda *_args, **_kwargs: False

create_stub("api.db.joint_services.tenant_model_service")
sys.modules["api.db.joint_services.tenant_model_service"].get_model_config_by_type_and_name = lambda *args, **kwargs: None
sys.modules["api.db.joint_services.tenant_model_service"].get_tenant_default_model_by_type = lambda *args, **kwargs: None

create_stub("rag.llm.chat_model")
sys.modules["rag.llm.chat_model"].ERROR_PREFIX = "ERROR:"

create_stub("common")
create_stub("common.constants")
sys.modules["common.constants"].LLMType = types.SimpleNamespace(CHAT="chat")

create_stub("rag.nlp")
sys.modules["rag.nlp"].is_english = lambda x: True

create_stub("rag.utils.redis_conn")
sys.modules["rag.utils.redis_conn"].REDIS_CONN = types.SimpleNamespace(
    get=lambda *args, **kwargs: None,
    set=lambda *args, **kwargs: None,
    set_obj=lambda *args, **kwargs: None,
    delete=lambda *args, **kwargs: None,
)

create_stub("rag.graphrag.entity_resolution_prompt")
sys.modules["rag.graphrag.entity_resolution_prompt"].ENTITY_RESOLUTION_PROMPT = "Test prompt"

create_stub("rag.graphrag.utils")
sys.modules["rag.graphrag.utils"].perform_variable_replacements = lambda text, **kwargs: text
sys.modules["rag.graphrag.utils"].chat_limiter = types.SimpleNamespace(__enter__=lambda s: None, __exit__=lambda s, *args: None)
sys.modules["rag.graphrag.utils"].GraphChange = type("GraphChange", (), {})

create_stub("rag.graphrag.memory")
sys.modules["rag.graphrag.memory"].GraphMemoryMonitor = type("GraphMemoryMonitor", (), {})
sys.modules["rag.graphrag.memory"].stream_pagerank = lambda *args, **kwargs: {}

create_stub("rag.graphrag.llm_protocol")
sys.modules["rag.graphrag.llm_protocol"].GraphRAGCompletionLLM = type("GraphRAGCompletionLLM", (), {})

create_stub("rag.graphrag.general.extractor")
sys.modules["rag.graphrag.general.extractor"].Extractor = type("Extractor", (), {})

create_stub("common.exceptions")
sys.modules["common.exceptions"].TaskCanceledException = type("TaskCanceledException", (Exception,), {})

create_stub("rag")
create_stub("rag.utils")
create_stub("rag.utils.es_conn")
create_stub("rag.prompts")
create_stub("rag.prompts.generator")
sys.modules["rag.prompts.generator"].chunks_format = lambda x: []

create_stub("api")
create_stub("api.db")
create_stub("api.db.services")
create_stub("api.db.services.llm_service")
sys.modules["api.db.services.llm_service"].LLMBundle = type("LLMBundle", (), {})

create_stub("api.db.services.file_service")
sys.modules["api.db.services.file_service"].FileService = type("FileService", (), {"get_blob": lambda *args, **kwargs: b"", "parse": lambda *args, **kwargs: None})

from agent.canvas import Canvas, Graph


class TestDSLParsing:
    """Tests for DSL JSON parsing and component graph conversion."""

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

    def test_parse_minimal_dsl(self):
        minimal_dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(minimal_dsl), tenant_id="test_tenant")
        assert "begin" in canvas.components
        assert canvas.components["begin"]["obj"].component_name == "Begin"

    def test_parse_dsl_with_globals(self):
        dsl = self._create_minimal_dsl()
        dsl["globals"] = {
            "sys.query": "test query",
            "sys.user_id": "user123",
            "sys.conversation_turns": 5,
        }
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert canvas.globals["sys.query"] == "test query"
        assert canvas.globals["sys.user_id"] == "user123"

    def test_parse_dsl_with_history(self):
        dsl = self._create_minimal_dsl()
        dsl["history"] = [
            ("user", "Hello"),
            ("assistant", "Hi there!"),
        ]
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert len(canvas.history) == 2
        assert canvas.history[0] == ("user", "Hello")

    def test_parse_dsl_invalid_json_raises_error(self):
        with pytest.raises(json.JSONDecodeError):
            Canvas("{invalid json}", tenant_id="test_tenant")

    def test_parse_dsl_missing_components_raises_error(self):
        dsl = {"history": [], "path": [], "retrieval": {}}
        with pytest.raises(KeyError):
            Canvas(json.dumps(dsl), tenant_id="test_tenant")


class TestComponentGraphConversion:
    """Tests for DSL to component graph conversion."""

    def _create_linear_dsl(self) -> dict:
        return {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {"prologue": "Hello"}},
                    "downstream": ["retrieval_0"],
                    "upstream": [],
                },
                "retrieval_0": {
                    "obj": {
                        "component_name": "Retrieval",
                        "params": {"kb_ids": ["kb1"], "top_n": 10},
                    },
                    "downstream": ["generate_0"],
                    "upstream": ["begin"],
                },
                "generate_0": {
                    "obj": {
                        "component_name": "Generate",
                        "params": {"llm_id": "llm1"},
                    },
                    "downstream": [],
                    "upstream": ["retrieval_0"],
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
        assert canvas.components["begin"]["downstream"] == ["retrieval_0"]
        assert canvas.components["retrieval_0"]["upstream"] == ["begin"]

    def test_component_downstream_navigation(self):
        dsl = self._create_linear_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        begin_downstream = canvas.components["begin"]["downstream"]
        assert begin_downstream == ["retrieval_0"]
        retrieval_downstream = canvas.components["retrieval_0"]["downstream"]
        assert retrieval_downstream == ["generate_0"]

    def test_component_upstream_navigation(self):
        dsl = self._create_linear_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        gen_upstream = canvas.components["generate_0"]["upstream"]
        assert gen_upstream == ["retrieval_0"]

    def test_get_component_by_id(self):
        dsl = self._create_linear_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        retrieval = canvas.get_component("retrieval_0")
        assert retrieval is not None
        assert retrieval["obj"].component_name == "Retrieval"

    def test_get_nonexistent_component_returns_none(self):
        dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert canvas.get_component("nonexistent") is None


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
                    "obj": {"component_name": "Generate", "params": {}},
                    "downstream": ["b"],
                    "upstream": ["begin"],
                },
                "b": {
                    "obj": {"component_name": "Generate", "params": {}},
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


class TestDSLVariableResolution:
    """Tests for variable resolution in DSL parsing."""

    def _create_dsl_with_variables(self) -> dict:
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
            "globals": {"sys.query": "initial query", "custom_var": "value"},
            "variables": {"var1": {"type": "string", "value": "test"}},
        }

    def test_globals_initialization_from_dsl(self):
        dsl = self._create_dsl_with_variables()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert canvas.globals["sys.query"] == "initial query"
        assert canvas.globals["custom_var"] == "value"

    def test_variables_initialization_from_dsl(self):
        dsl = self._create_dsl_with_variables()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "var1" in canvas.variables

    def test_missing_globals_defaults(self):
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
        assert "sys.query" in canvas.globals
        assert canvas.globals["sys.query"] == ""
        assert "sys.history" in canvas.globals


class TestDSLSerialization:
    """Tests for DSL serialization back to JSON."""

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

    def test_serialize_to_json(self):
        dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        serialized = str(canvas)
        parsed = json.loads(serialized)
        assert "components" in parsed
        assert "begin" in parsed["components"]

    def test_serialize_preserves_history(self):
        dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        canvas.history.append(("user", "test message"))
        serialized = str(canvas)
        parsed = json.loads(serialized)
        assert parsed["history"] == [("user", "test message")]

    def test_serialize_preserves_path(self):
        dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        canvas.path.append("new_component")
        serialized = str(canvas)
        parsed = json.loads(serialized)
        assert "new_component" in parsed["path"]


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
        assert canvas.memory[0] == ("user", "Hello", "Greeting")

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
                                "technical": {"to": ["retrieval_0"], "description": "Tech questions"},
                                "general": {"to": ["generate_0"], "description": "General questions"},
                            },
                            "query": "sys.query",
                            "llm_id": "llm1",
                        },
                    },
                    "downstream": ["retrieval_0", "generate_0"],
                    "upstream": ["begin"],
                },
                "retrieval_0": {
                    "obj": {"component_name": "Retrieval", "params": {"kb_ids": ["kb1"]}},
                    "downstream": [],
                    "upstream": ["categorize_0"],
                },
                "generate_0": {
                    "obj": {"component_name": "Generate", "params": {"llm_id": "llm1"}},
                    "downstream": [],
                    "upstream": ["categorize_0"],
                },
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }

    def test_categorize_parsing(self):
        dsl = self._create_categorize_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "categorize_0" in canvas.components
        categorize = canvas.components["categorize_0"]["obj"]
        assert categorize.component_name == "Categorize"
        assert "technical" in categorize._param.category_description
        assert "general" in categorize._param.category_description

    def test_categorize_routing_parsing(self):
        dsl = self._create_categorize_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        categorize = canvas.components["categorize_0"]["obj"]
        assert categorize._param.category_description["technical"]["to"] == ["retrieval_0"]
        assert categorize._param.category_description["general"]["to"] == ["generate_0"]

    def test_categorize_downstream_routes(self):
        dsl = self._create_categorize_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert set(canvas.components["categorize_0"]["downstream"]) == {"retrieval_0", "generate_0"}

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
                                    "to": ["retrieval_0"],
                                },
                            ],
                            "end_cpn_ids": ["generate_0"],
                        },
                    },
                    "downstream": ["retrieval_0", "generate_0"],
                    "upstream": ["begin"],
                },
                "retrieval_0": {
                    "obj": {"component_name": "Retrieval", "params": {}},
                    "downstream": [],
                    "upstream": ["switch_0"],
                },
                "generate_0": {
                    "obj": {"component_name": "Generate", "params": {}},
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
        assert condition["to"] == ["retrieval_0"]

    def test_switch_else_route_parsing(self):
        dsl = self._create_switch_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        switch = canvas.components["switch_0"]["obj"]
        assert switch._param.end_cpn_ids == ["generate_0"]


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
                    "downstream": ["gen1", "gen2", "gen3"],
                    "upstream": [],
                },
                "gen1": {
                    "obj": {"component_name": "Generate", "params": {"llm_id": "llm1"}},
                    "downstream": [],
                    "upstream": ["begin"],
                },
                "gen2": {
                    "obj": {"component_name": "Generate", "params": {"llm_id": "llm2"}},
                    "downstream": [],
                    "upstream": ["begin"],
                },
                "gen3": {
                    "obj": {"component_name": "Generate", "params": {"llm_id": "llm3"}},
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
                    "obj": {"component_name": "Generate", "params": {}},
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
                    "obj": {"component_name": "Generate", "params": {}},
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
