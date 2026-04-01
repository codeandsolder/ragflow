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
import importlib.util
from pathlib import Path


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

create_stub("common.misc_utils")
sys.modules["common.misc_utils"].hash_str2int = lambda x: hash(x)
sys.modules["common.misc_utils"].get_uuid = lambda: "test-uuid"

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

create_stub("common.exceptions")
sys.modules["common.exceptions"].TaskCanceledException = Exception

create_stub("agent")
create_stub("agent.component")
sys.modules["agent.component"].component_class = lambda name: type(name, (), {})

create_stub("agent.component.base")


class StubComponentParamBase:
    def __init__(self):
        self.message_history_window_size = 13
        self.inputs = {}
        self.outputs = {}
        self.description = ""
        self.max_retries = 0
        self.delay_after_error = 2.0
        self._is_raw_conf = True

    def update(self, conf, allow_redundant=False):
        for key, value in conf.items():
            setattr(self, key, value)

    def check(self):
        pass


sys.modules["agent.component.base"].ComponentBase = type("ComponentBase", (), {})
sys.modules["agent.component.base"].ComponentParamBase = StubComponentParamBase

_original_component_class = sys.modules["agent.component"].component_class


def _wrapped_component_class(class_name):
    if class_name.endswith("Param"):

        class DynamicParam(StubComponentParamBase):
            pass

        DynamicParam.__name__ = class_name
        return DynamicParam
    else:

        class DynamicComponent:
            def __init__(self, canvas, id, param):
                self._canvas = canvas
                self._id = id
                self._param = param
                self.component_name = class_name

            def output(self, key):
                return None

            def thoughts(self):
                return ""

        DynamicComponent.__name__ = class_name
        return DynamicComponent


sys.modules["agent.component"].component_class = _wrapped_component_class

create_stub("api")
create_stub("api.db")
create_stub("api.db.services")
create_stub("api.db.services.llm_service")
sys.modules["api.db.services.llm_service"].LLMBundle = type("LLMBundle", (), {})

create_stub("api.db.services.file_service")
sys.modules["api.db.services.file_service"].FileService = type("FileService", (), {"get_blob": lambda *args, **kwargs: b"", "parse": lambda *args, **kwargs: None})

_test_dir = Path(__file__).parent
_project_root = _test_dir.parent.parent.parent
_canvas_path = _project_root / "agent" / "canvas.py"
_canvas_spec = importlib.util.spec_from_file_location("agent.canvas", str(_canvas_path))
_canvas_mod = importlib.util.module_from_spec(_canvas_spec)
sys.modules["agent.canvas"] = _canvas_mod
_canvas_spec.loader.exec_module(_canvas_mod)
Canvas = _canvas_mod.Canvas
Graph = _canvas_mod.Graph


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
