#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
conftest.py for agent tools tests.

Sets up mocks for heavy dependencies to allow tests to run quickly without
loading the full application stack.
"""

import asyncio
import sys
import types
import enum
from pathlib import Path
from unittest.mock import MagicMock


def _setup_mocks():
    """Set up mock modules before importing the real modules."""

    def create_stub(name, attrs=None):
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            mod_name = ".".join(parts[:i])
            if mod_name not in sys.modules:
                stub = types.ModuleType(mod_name)
                sys.modules[mod_name] = stub

        if attrs:
            for k, v in attrs.items():
                setattr(sys.modules[name], k, v)

    # Create common stubs
    create_stub("common")
    create_stub("common.constants")

    # Add constants
    class RetCode(enum.Enum):
        SUCCESS = 0
        DEFAULT_ERROR = 1

    class LLMType(enum.Enum):
        Chat = "chat"
        Embedding = "embedding"
        Rerank = "rerank"

    sys.modules["common.constants"].RetCode = RetCode
    sys.modules["common.constants"].LLMType = LLMType
    sys.modules["common.constants"].SANDBOX_ARTIFACT_BUCKET = "test"
    sys.modules["common.constants"].SANDBOX_ARTIFACT_EXPIRE_DAYS = 7

    # Connection utils timeout decorator
    def timeout_decorator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    create_stub("common.connection_utils", {"timeout": timeout_decorator})

    # Misc utils
    create_stub("common.misc_utils")
    sys.modules["common.misc_utils"].hash_str2int = lambda x: hash(x)
    sys.modules["common.misc_utils"].thread_pool_exec = lambda func, *args, **kwargs: func(*args, **kwargs)

    # Settings
    create_stub("common.settings")

    # Create rag stubs
    create_stub("rag")
    create_stub("rag.utils")
    create_stub("rag.utils.es_conn")
    create_stub("rag.prompts")
    create_stub("rag.prompts.generator")
    sys.modules["rag.prompts.generator"].kb_prompt = lambda *args, **kwargs: ""

    # Create api stubs
    create_stub("api")
    create_stub("api.db")
    create_stub("api.db.services")
    create_stub("api.db.services.file_service")

    # Mock FileService
    class MockFileService:
        @staticmethod
        def upload(*args, **kwargs):
            return {"url": "http://test.url"}

    sys.modules["api.db.services.file_service"].FileService = MockFileService

    # DocMetadataService
    create_stub("api.db.services.doc_metadata_service")

    class MockDocMetadataService:
        @staticmethod
        def get_by_ids(*args, **kwargs):
            return []

    sys.modules["api.db.services.doc_metadata_service"].DocMetadataService = MockDocMetadataService

    # KnowledgebaseService
    create_stub("api.db.services.knowledgebase_service")
    sys.modules["api.db.services.knowledgebase_service"].KnowledgebaseService = MagicMock

    # LLMBundle
    create_stub("api.db.services.llm_service")
    sys.modules["api.db.services.llm_service"].LLMBundle = MagicMock

    # MemoryService
    create_stub("api.db.services.memory_service")
    sys.modules["api.db.services.memory_service"].MemoryService = MagicMock

    # Joint services
    create_stub("api.db.joint_services")
    create_stub("api.db.joint_services.memory_message_service")
    sys.modules["api.db.joint_services.memory_message_service"].memory_message_service = MagicMock

    create_stub("api.db.joint_services.tenant_model_service")
    sys.modules["api.db.joint_services.tenant_model_service"].get_model_config_by_type_and_name = MagicMock
    sys.modules["api.db.joint_services.tenant_model_service"].get_tenant_default_model_by_type = MagicMock

    # metadata_utils
    create_stub("common.metadata_utils")
    sys.modules["common.metadata_utils"].apply_meta_data_filter = MagicMock

    # rag.app.tag
    create_stub("rag.app")
    create_stub("rag.app.tag")
    sys.modules["rag.app.tag"].label_question = MagicMock

    # rag.prompts.generator additional stubs
    sys.modules["rag.prompts.generator"].cross_languages = MagicMock
    sys.modules["rag.prompts.generator"].memory_prompt = MagicMock

    # Create agent stubs
    create_stub("agent")
    create_stub("agent.settings")
    sys.modules["agent.settings"].FLOAT_ZERO = 1e-8
    sys.modules["agent.settings"].PARAM_MAXDEPTH = 5

    # Create agent.component stubs
    create_stub("agent.component")
    create_stub("agent.component.base")

    class ComponentParamBase:
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

        def set_name(self, name):
            self._name = name
            return self

        def check(self):
            raise NotImplementedError("Parameter Object should be checked.")

        def get_input_form(self):
            return {}

    class ComponentBase:
        def __init__(self, canvas, id, param):
            self._canvas = canvas
            self._id = id
            self._param = param
            self._outputs = {}

        def output(self, key):
            return self._outputs.get(key)

        def thoughts(self):
            return ""

    sys.modules["agent.component.base"].ComponentParamBase = ComponentParamBase
    sys.modules["agent.component.base"].ComponentBase = ComponentBase

    # Create agent.tools.base stubs (needed before code_exec imports)
    create_stub("agent.tools")
    create_stub("agent.tools.base")

    from typing import TypedDict, List

    class ToolParameter(TypedDict):
        type: str
        description: str
        displayDescription: str
        enum: List[str]
        required: bool

    class ToolMeta(TypedDict):
        name: str
        displayName: str
        description: str
        displayDescription: str
        parameters: dict

    class ToolParamBase(ComponentParamBase):
        def __init__(self):
            super().__init__()
            # Don't overwrite meta if it's already set as a class attribute
            if not hasattr(self, "meta"):
                self.meta = {}
            self._init_inputs()

        def _init_inputs(self):
            self.inputs = {}
            for k, p in self.meta.get("parameters", {}).items():
                self.inputs[k] = p.copy()

        def get_input_form(self):
            form = {}
            for key, value in getattr(self, "arguments", {}).items():
                form[key] = {"type": "line", "description": value}
            return form

        def get_meta(self):
            params = {}
            meta_params = self.meta.get("parameters", {})
            for k, p in meta_params.items():
                params[k] = {"type": p.get("type", "string"), "description": p.get("description", "")}
                if "enum" in p:
                    params[k]["enum"] = p["enum"]

            desc = getattr(self, "description", None) or self.meta.get("description", "")
            function_name = getattr(self, "function_name", None) or self.meta.get("name", "")

            return {
                "type": "function",
                "function": {
                    "name": function_name,
                    "description": desc,
                    "parameters": {"type": "object", "properties": params, "required": [k for k, p in meta_params.items() if p.get("required", False)]},
                },
            }

    class ToolBase:
        def __init__(self, canvas, id, param):
            self._canvas = canvas
            self._id = id
            self._param = param
            self._outputs = {}
            self.component_name = self.__class__.__name__

        def output(self, key=None):
            if key:
                return self._outputs.get(key)
            return {k: v for k, v in self._outputs.items()}

        def set_output(self, key, value):
            if key not in self._outputs:
                self._outputs[key] = None
            self._outputs[key] = value

        def get_meta(self):
            return self._param.get_meta()

        def is_canceled(self):
            return getattr(self._canvas, "_canceled", False)

        def check_if_canceled(self, task_name):
            if self.is_canceled():
                self._outputs["_ERROR"] = "Task has been canceled"
                return True
            return False

        def invoke(self, **kwargs):
            if self.check_if_canceled("Tool processing"):
                return None

            try:
                res = self._invoke(**kwargs)
            except Exception as e:
                self._outputs["_ERROR"] = str(e)
                res = str(e)
            return res

        def _invoke(self, **kwargs):
            raise NotImplementedError("_invoke must be implemented by subclass")

        async def invoke_async(self, **kwargs):
            if self.check_if_canceled("Tool processing"):
                return None

            try:
                # Check if subclass defined _invoke_async (not the default stub)
                # Check in instance dict first, then class hierarchy (excluding our stub base)
                has_custom_async = False
                for cls in type(self).__mro__:
                    if cls.__name__ == "ToolBase":
                        break
                    if "_invoke_async" in cls.__dict__:
                        has_custom_async = True
                        break

                if has_custom_async and asyncio.iscoroutinefunction(self._invoke_async):
                    res = await self._invoke_async(**kwargs)
                elif asyncio.iscoroutinefunction(self._invoke):
                    res = await self._invoke(**kwargs)
                else:
                    res = self._invoke(**kwargs)
            except Exception as e:
                self._outputs["_ERROR"] = str(e)
                res = str(e)
            return res

        async def _invoke_async(self, **kwargs):
            raise NotImplementedError("_invoke_async must be implemented by subclass")

        def _retrieve_chunks(self, res_list, get_title, get_url, get_content, get_score=None):
            chunks = []
            aggs = []
            for r in res_list:
                if not r.get("content"):
                    continue
                chunks.append({"content": get_content(r), "doc_id": r.get("doc_id", ""), "docnm_kwd": get_title(r), "url": get_url(r), "similarity": get_score(r) if get_score else 0})
                aggs.append({"doc_name": get_title(r), "doc_id": r.get("doc_id", ""), "count": 1, "url": get_url(r)})
            # Also add references to canvas like the real implementation
            if hasattr(self._canvas, "add_reference"):
                self._canvas.add_reference(chunks, aggs)
            # Set the formalized_content output like the real implementation does
            from rag.prompts.generator import kb_prompt

            self._outputs["formalized_content"] = kb_prompt({"chunks": chunks, "doc_aggs": aggs}, 200000, True)
            return chunks, aggs

        def thoughts(self):
            return ""

    sys.modules["agent.tools.base"].ToolParameter = ToolParameter
    sys.modules["agent.tools.base"].ToolMeta = ToolMeta
    sys.modules["agent.tools.base"].ToolParamBase = ToolParamBase
    sys.modules["agent.tools.base"].ToolBase = ToolBase

    # Create mcp_tool_call_conn stub
    create_stub("common.mcp_tool_call_conn")

    class ToolCallSession:
        pass

    class MCPToolCallSession:
        pass

    sys.modules["common.mcp_tool_call_conn"].ToolCallSession = ToolCallSession
    sys.modules["common.mcp_tool_call_conn"].MCPToolCallSession = MCPToolCallSession


# Set up mocks before any test imports
_setup_mocks()

# Import code_exec and retrieval modules directly to avoid __init__.py auto-import of all tools
# which causes timeout issues due to heavy dependencies
import importlib.util

_conftest_dir = Path(__file__).parent
_project_root = _conftest_dir.parent.parent.parent.parent
_code_exec_path = _project_root / "agent" / "tools" / "code_exec.py"
_spec = importlib.util.spec_from_file_location("agent.tools.code_exec", str(_code_exec_path))
_code_exec = importlib.util.module_from_spec(_spec)
sys.modules["agent.tools.code_exec"] = _code_exec
_spec.loader.exec_module(_code_exec)

_retrieval_path = _project_root / "agent" / "tools" / "retrieval.py"
_spec = importlib.util.spec_from_file_location("agent.tools.retrieval", str(_retrieval_path))
_retrieval = importlib.util.module_from_spec(_spec)
sys.modules["agent.tools.retrieval"] = _retrieval
_spec.loader.exec_module(_retrieval)
