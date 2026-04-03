#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
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
Unit tests for rag/svr/task_executor module.
Tests task execution orchestration logic.
These tests read module content to verify expected patterns.
"""

import ast
from pathlib import Path
import pytest


_test_dir = Path(__file__).parent
_project_root = _test_dir.parent.parent.parent.parent
_module_path = _project_root / "rag" / "svr" / "task_executor.py"


@pytest.fixture(scope="class")
def module_content():
    return _module_path.read_text()


@pytest.fixture(scope="class")
def module_ast():
    return ast.parse(_module_path.read_text())


class TestTaskExecutorModuleStructure:
    """Test module structure by reading source code."""

    def test_task_executor_file_exists(self):
        """Test that task_executor.py exists."""
        assert _module_path.exists()

    def test_task_executor_has_required_functions(self, module_content):
        """Test that key functions are defined in the module."""
        assert "def set_progress(" in module_content
        assert "async def collect(" in module_content
        assert "async def build_chunks(" in module_content
        assert "async def do_handle_task(" in module_content
        assert "async def handle_task(" in module_content
        assert "async def insert_chunks(" in module_content
        assert "async def embedding(" in module_content

    def test_task_executor_has_task_type_mapping(self, module_content):
        """Test that TASK_TYPE_TO_PIPELINE_TASK_TYPE is defined."""
        assert "TASK_TYPE_TO_PIPELINE_TASK_TYPE" in module_content
        assert '"dataflow"' in module_content
        assert '"raptor"' in module_content
        assert '"graphrag"' in module_content

    def test_task_executor_has_parser_factory(self, module_content):
        """Test that FACTORY (parser factory) is defined."""
        assert "FACTORY = {" in module_content or "FACTORY =" in module_content
        assert '"general"' in module_content

    def test_task_executor_has_constants(self, module_content):
        """Test that module has expected constants."""
        assert "BATCH_SIZE" in module_content
        assert "MAX_CONCURRENT_TASKS" in module_content

    def test_task_executor_handles_signal(self, module_content):
        """Test that signal handler is defined."""
        assert "def signal_handler(" in module_content

    def test_task_executor_has_redis_integration(self, module_content):
        """Test that Redis connections are used."""
        assert "REDIS_CONN" in module_content
        assert "RedisDistributedLock" in module_content

    def test_task_executor_handles_raptor(self, module_content):
        """Test that RAPTOR processing is handled."""
        assert "run_raptor_for_kb" in module_content
        assert "should_skip_raptor" in module_content

    def test_task_executor_handles_graphrag(self, module_content):
        """Test that GraphRAG processing is handled."""
        assert "graphrag" in module_content.lower()
        assert "run_graphrag" in module_content

    def test_task_executor_handles_dataflow(self, module_content):
        """Test that dataflow tasks are handled."""
        assert "run_dataflow" in module_content

    def test_task_executor_handles_memory(self, module_content):
        """Test that memory tasks are handled."""
        assert "handle_save_to_memory_task" in module_content

    def test_task_executor_progress_tracking(self, module_content):
        """Test that progress tracking is implemented."""
        assert "progress" in module_content
        assert "progress_msg" in module_content


class TestTaskExecutorConstants:
    """Test constants by parsing AST."""

    def test_parse_task_executor_ast(self, module_ast):
        """Test that task_executor.py can be parsed as valid Python."""
        assert module_ast is not None
        assert isinstance(module_ast, ast.Module)

    def test_find_assignments_in_module(self, module_ast):
        """Test that module contains expected assignments."""
        names = [node.id for node in ast.walk(module_ast) if isinstance(node, ast.Name)]
        assert "FACTORY" in names or "asyncio" in names


class TestTaskExecutorConfiguration:
    """Test configuration loading."""

    def test_task_type_to_pipeline_type_mapping_exists(self, module_content):
        """Test task type to pipeline task type mapping is defined in module."""
        assert "TASK_TYPE_TO_PIPELINE_TASK_TYPE" in module_content
        assert '"dataflow"' in module_content or "'dataflow'" in module_content


class TestTaskExecutorImports:
    """Test that required imports are present."""

    def test_has_required_standard_imports(self, module_content):
        """Test that required standard library imports exist."""
        assert "import asyncio" in module_content
        assert "import time" in module_content
        assert "import logging" in module_content

    def test_has_api_imports(self, module_content):
        """Test that API imports are present."""
        assert "from api.db" in module_content

    def test_has_rag_imports(self, module_content):
        """Test that RAG imports are present."""
        assert "from rag." in module_content

    def test_has_common_imports(self, module_content):
        """Test that common imports are present."""
        assert "from common" in module_content
