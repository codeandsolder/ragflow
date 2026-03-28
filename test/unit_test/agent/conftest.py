# Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import types
import enum
import importlib
from pathlib import Path

_conftest_dir = Path(__file__).parent
_project_root = _conftest_dir.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


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


def _setup_mocks():
    """Set up mock modules before importing the real modules."""

    # Create common stubs
    create_stub("common")
    create_stub("common.constants")

    # Add constants
    class RetCode(enum.Enum):
        SUCCESS = 0
        DEFAULT_ERROR = 1

    sys.modules["common.constants"].RetCode = RetCode
    sys.modules["common.constants"].SANDBOX_ARTIFACT_BUCKET = "test"
    sys.modules["common.constants"].SANDBOX_ARTIFACT_EXPIRE_DAYS = 7

    class LLMType(str, enum.Enum):
        CHAT = "chat"
        EMBEDDING = "embedding"
        SPEECH2TEXT = "speech2text"
        IMAGE2TEXT = "image2text"
        RERANK = "rerank"
        TTS = "tts"
        OCR = "ocr"

    sys.modules["common.constants"].LLMType = LLMType

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
    # Make api a package so it can have submodules
    api = sys.modules["api"]
    api.__path__ = [str(_project_root / "api")]
    api.__package__ = "api"
    create_stub("api.db")
    # Make api.db a package so it can have submodules
    api_db = sys.modules["api.db"]
    api_db.__path__ = [str(_project_root / "api" / "db")]
    api_db.__package__ = "api.db"
    create_stub("api.db.services")
    # Make api.db.services a package so submodules can be imported
    api_db_services = sys.modules["api.db.services"]
    api_db_services.__path__ = [str(_project_root / "api" / "db" / "services")]
    api_db_services.__package__ = "api.db.services"
    create_stub("api.db.joint_services")
    create_stub("api.db.services.file_service")

    # Mock FileService
    class MockFileService:
        @staticmethod
        def upload(*args, **kwargs):
            return {"url": "http://test.url"}

    sys.modules["api.db.services.file_service"].FileService = MockFileService

    # Create agent stubs
    create_stub("agent")
    create_stub("agent.settings")
    sys.modules["agent.settings"].FLOAT_ZERO = 1e-8
    sys.modules["agent.settings"].PARAM_MAXDEPTH = 5

    # Create agent.component stubs
    # agent.component needs to be a package-like object to allow importing submodules
    create_stub("agent.component")
    agent_component_stub = sys.modules["agent.component"]
    agent_component_stub.__path__ = [str(_project_root / "agent" / "component")]
    agent_component_stub.__package__ = "agent.component"

    def component_class(class_name):
        class DynamicParam(ComponentParamBase):
            pass

        DynamicParam.__name__ = class_name
        return DynamicParam

    agent_component_stub.component_class = component_class

    create_stub("agent.component.base")

    class ComponentParamBase:
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

    # Create agent.tools.base stubs
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
            self.meta = {}
            self._init_inputs()

        def _init_inputs(self):
            pass

        def get_input_form(self):
            form = {}
            for key, value in getattr(self, "arguments", {}).items():
                form[key] = {"type": "line", "description": value}
            return form

    class ToolBase:
        def __init__(self, canvas, id, param):
            self._canvas = canvas
            self._id = id
            self._param = param
            self._outputs = {}
            self.component_name = self.__class__.__name__

        def output(self, key):
            return self._outputs.get(key)

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

# Import code_exec module directly to avoid __init__.py auto-import of all tools
# which causes timeout issues due to heavy dependencies
import importlib.util
from pathlib import Path

_conftest_dir = Path(__file__).parent
_project_root = _conftest_dir.parent.parent.parent
_code_exec_path = _project_root / "agent" / "tools" / "code_exec.py"
_spec = importlib.util.spec_from_file_location("agent.tools.code_exec", str(_code_exec_path))
_code_exec = importlib.util.module_from_spec(_spec)
sys.modules["agent.tools.code_exec"] = _code_exec
_spec.loader.exec_module(_code_exec)

# Create mock modules that were causing hangs
create_stub("agent.tools.retrieval")


# Add mock classes for component system
class MockRetrieval:
    pass


sys.modules["agent.tools.retrieval"].Retrieval = MockRetrieval
