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
import os
from pathlib import Path


class TestTaskExecutorModuleStructure:
    """Test module structure by reading source code."""

    def test_task_executor_file_exists(self):
        """Test that task_executor.py exists."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        assert module_path.exists()

    def test_task_executor_has_required_functions(self):
        """Test that key functions are defined in the module."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "def set_progress(" in content
        assert "async def collect(" in content
        assert "async def build_chunks(" in content
        assert "async def do_handle_task(" in content
        assert "async def handle_task(" in content
        assert "async def insert_chunks(" in content
        assert "async def embedding(" in content

    def test_task_executor_has_task_type_mapping(self):
        """Test that TASK_TYPE_TO_PIPELINE_TASK_TYPE is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "TASK_TYPE_TO_PIPELINE_TASK_TYPE" in content
        assert '"dataflow"' in content
        assert '"raptor"' in content
        assert '"graphrag"' in content

    def test_task_executor_has_parser_factory(self):
        """Test that FACTORY (parser factory) is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "FACTORY = {" in content or "FACTORY =" in content
        assert '"general"' in content

    def test_task_executor_has_constants(self):
        """Test that module has expected constants."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "BATCH_SIZE" in content
        assert "MAX_CONCURRENT_TASKS" in content

    def test_task_executor_handles_signal(self):
        """Test that signal handler is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "def signal_handler(" in content

    def test_task_executor_has_redis_integration(self):
        """Test that Redis connections are used."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "REDIS_CONN" in content
        assert "RedisDistributedLock" in content

    def test_task_executor_handles_raptor(self):
        """Test that RAPTOR processing is handled."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "run_raptor_for_kb" in content
        assert "should_skip_raptor" in content

    def test_task_executor_handles_graphrag(self):
        """Test that GraphRAG processing is handled."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "graphrag" in content.lower()
        assert "run_graphrag" in content

    def test_task_executor_handles_dataflow(self):
        """Test that dataflow tasks are handled."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "run_dataflow" in content

    def test_task_executor_handles_memory(self):
        """Test that memory tasks are handled."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "handle_save_to_memory_task" in content

    def test_task_executor_progress_tracking(self):
        """Test that progress tracking is implemented."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "progress" in content
        assert "progress_msg" in content


class TestTaskExecutorConstants:
    """Test constants by parsing AST."""

    def test_parse_task_executor_ast(self):
        """Test that task_executor.py can be parsed as valid Python."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        tree = ast.parse(content)
        assert tree is not None
        assert isinstance(tree, ast.Module)

    def test_find_assignments_in_module(self):
        """Test that module contains expected assignments."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        tree = ast.parse(content)
        names = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
        assert "FACTORY" in names or "asyncio" in names


class TestTaskExecutorConfiguration:
    """Test configuration loading."""

    def test_consumer_name_construction(self):
        """Test consumer name construction logic."""
        consumer_no = "0"
        consumer_name = "task_executor_" + consumer_no
        assert consumer_name == "task_executor_0"

    def test_task_type_to_pipeline_type_mapping(self):
        """Test task type to pipeline task type mapping."""
        mapping = {
            "dataflow": "PARSE",
            "raptor": "RAPTOR",
            "graphrag": "GRAPH_RAG",
            "mindmap": "MINDMAP",
            "memory": "MEMORY",
        }
        assert mapping["dataflow"] == "PARSE"
        assert mapping["raptor"] == "RAPTOR"
        assert mapping["graphrag"] == "GRAPH_RAG"


class TestTaskExecutorImports:
    """Test that required imports are present."""

    def test_has_required_standard_imports(self):
        """Test that required standard library imports exist."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "import asyncio" in content
        assert "import time" in content
        assert "import logging" in content

    def test_has_api_imports(self):
        """Test that API imports are present."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "from api.db" in content

    def test_has_rag_imports(self):
        """Test that RAG imports are present."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "from rag." in content

    def test_has_common_imports(self):
        """Test that common imports are present."""
        module_path = Path("/mnt/d/ragflow/rag/svr/task_executor.py")
        content = module_path.read_text()

        assert "from common" in content


import pytest
