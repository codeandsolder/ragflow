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

import os

os.environ["RAGFLOW_TESTING"] = "1"

import sys
import types
import importlib
import importlib.util
from pathlib import Path


# Patch sqlglot BEFORE any other imports that depend on pyobvector
try:
    import sqlglot

    if not hasattr(sqlglot, "Expression"):
        from sqlglot import exp as sqlglot_exp

        sqlglot.Expression = sqlglot_exp.Expression
except Exception:
    pass

_conftest_dir = Path(__file__).parent
_project_root = _conftest_dir.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def _check_import(module_name):
    """Check if a module can be imported without side effects."""
    if module_name in sys.modules:
        return True
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False


def _create_stub(name, attrs=None):
    """Create a stub module and add it to sys.modules - only if not already importable."""
    if _check_import(name):
        return
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
    """Set up mock modules for dependencies that can't be imported."""

    # Mock scholarly package (has SyntaxError in broken dependency)
    if "scholarly" not in sys.modules:
        scholarly_stub = types.ModuleType("scholarly")
        scholarly_stub.search_pubs = lambda *args, **kwargs: []
        sys.modules["scholarly"] = scholarly_stub

    # Only stub modules that truly can't be imported
    # Stub agent.settings if needed
    if not _check_import("agent.settings"):
        _create_stub("agent.settings")
        sys.modules["agent.settings"].FLOAT_ZERO = 1e-8
        sys.modules["agent.settings"].PARAM_MAXDEPTH = 5

    # Stub common.mcp_tool_call_conn if missing
    if not _check_import("common.mcp_tool_call_conn"):
        _create_stub("common.mcp_tool_call_conn")

        class ToolCallSession:
            pass

        class MCPToolCallSession:
            pass

        sys.modules["common.mcp_tool_call_conn"].ToolCallSession = ToolCallSession
        sys.modules["common.mcp_tool_call_conn"].MCPToolCallSession = MCPToolCallSession

    # Stub common.exceptions if missing
    if not _check_import("common.exceptions"):
        _create_stub("common.exceptions")
        sys.modules["common.exceptions"].TaskCanceledException = type("TaskCanceledException", (Exception,), {})

    # Stub rag.utils.redis_conn if missing
    if not _check_import("rag.utils.redis_conn"):
        _create_stub("rag.utils.redis_conn")
        sys.modules["rag.utils.redis_conn"].REDIS_CONN = types.SimpleNamespace(
            __getitem__=lambda s, k: None,
            __setitem__=lambda s, k, v: None,
            get=lambda k, **kw: None,
            set=lambda k, v, **kw: None,
            delete=lambda k: None,
            queue_consumer=lambda *a, **kw: None,
            queue_producer=lambda *a, **kw: None,
        )

    # Stub rag.prompts.generator if missing
    if not _check_import("rag.prompts.generator"):
        _create_stub("rag.prompts.generator")
        sys.modules["rag.prompts.generator"].chunks_format = lambda x: []
        sys.modules["rag.prompts.generator"].kb_prompt = lambda *args, **kwargs: ""

    # Stub agent.tools.retrieval if missing
    if not _check_import("agent.tools.retrieval"):
        _create_stub("agent.tools.retrieval")

        class MockRetrieval:
            pass

        sys.modules["agent.tools.retrieval"].Retrieval = MockRetrieval


# Run stub setup at import time
_setup_mocks()
