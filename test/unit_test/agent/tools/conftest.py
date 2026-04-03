#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
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
import importlib
import importlib.util
import sys
import types
import enum
from pathlib import Path
from unittest.mock import MagicMock


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
    """Set up mock modules before importing the real modules."""

    # Only stub modules that truly can't be imported

    # Create common stubs only if needed
    if not _check_import("common.constants"):
        _create_stub("common")
        _create_stub("common.constants")

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

    if not _check_import("common.connection_utils"):

        def timeout_decorator(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

        _create_stub("common.connection_utils", {"timeout": timeout_decorator})

    # DO NOT stub common.misc_utils - it's a real module that should be imported normally

    if not _check_import("common.settings"):
        _create_stub("common.settings")

    # DO NOT stub api, api.db, api.db.services etc. - they are real modules

    # Stub modules that may not exist
    if not _check_import("common.metadata_utils"):
        _create_stub("common.metadata_utils")
        sys.modules["common.metadata_utils"].apply_meta_data_filter = MagicMock

    if not _check_import("rag.app.tag"):
        _create_stub("rag.app")
        _create_stub("rag.app.tag")
        sys.modules["rag.app.tag"].label_question = MagicMock

    if not _check_import("rag.prompts.generator"):
        _create_stub("rag")
        _create_stub("rag.prompts")
        _create_stub("rag.prompts.generator")
        sys.modules["rag.prompts.generator"].kb_prompt = lambda *args, **kwargs: ""
        sys.modules["rag.prompts.generator"].cross_languages = MagicMock
        sys.modules["rag.prompts.generator"].memory_prompt = MagicMock

    if not _check_import("api.db.services.doc_metadata_service"):
        _create_stub("api.db.services.doc_metadata_service")

        class MockDocMetadataService:
            @staticmethod
            def get_by_ids(*args, **kwargs):
                return []

        sys.modules["api.db.services.doc_metadata_service"].DocMetadataService = MockDocMetadataService

    if not _check_import("api.db.services.memory_service"):
        _create_stub("api.db.services.memory_service")
        sys.modules["api.db.services.memory_service"].MemoryService = MagicMock

    if not _check_import("api.db.joint_services.memory_message_service"):
        _create_stub("api.db.joint_services")
        _create_stub("api.db.joint_services.memory_message_service")
        sys.modules["api.db.joint_services.memory_message_service"].memory_message_service = MagicMock

    if not _check_import("common.mcp_tool_call_conn"):
        _create_stub("common.mcp_tool_call_conn")

        class ToolCallSession:
            pass

        class MCPToolCallSession:
            pass

        sys.modules["common.mcp_tool_call_conn"].ToolCallSession = ToolCallSession
        sys.modules["common.mcp_tool_call_conn"].MCPToolCallSession = MCPToolCallSession


# Set up mocks before any test imports
_setup_mocks()
