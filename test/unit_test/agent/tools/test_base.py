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

import json

import pytest

from agent.canvas import Canvas
from agent.tools.base import ToolParamBase, ToolBase, ToolMeta, ToolParameter


class MockCanvas(Canvas):
    def __init__(self):
        dsl = json.dumps({"components": {}, "path": [], "history": []})
        super().__init__(dsl, tenant_id="test_tenant")
        self._references = []
        self._canceled = False

    def load(self):
        pass

    def is_canceled(self):
        return self._canceled

    def get_component_name(self, component_id):
        return "test_tool"

    def add_reference(self, chunks, aggs):
        self._references.extend(chunks)

    def get_variable_value(self, var_name):
        return self.variables.get(var_name)

    def get_tenant_id(self):
        return self._tenant_id


class TestToolParameter:
    """Tests for ToolParameter TypedDict structure."""

    def test_tool_parameter_structure(self):
        param: ToolParameter = {
            "type": "string",
            "description": "Test parameter",
            "displayDescription": "Test parameter display",
            "enum": ["option1", "option2"],
            "required": True,
        }
        assert param["type"] == "string"
        assert param["required"] is True
        assert param["enum"] == ["option1", "option2"]


class TestToolMeta:
    """Tests for ToolMeta TypedDict structure."""

    def test_tool_meta_structure(self):
        meta: ToolMeta = {
            "name": "test_tool",
            "displayName": "Test Tool",
            "description": "A test tool",
            "displayDescription": "A test tool for testing",
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                    "displayDescription": "Search query",
                    "enum": [],
                    "required": True,
                }
            },
        }
        assert meta["name"] == "test_tool"
        assert "query" in meta["parameters"]


class TestToolParamBase:
    """Tests for ToolParamBase class."""

    def test_tool_param_base_init(self):
        class TestParam(ToolParamBase):
            def __init__(self):
                self.meta: ToolMeta = {
                    "name": "test_tool",
                    "description": "Test tool",
                    "parameters": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                            "default": "",
                            "required": True,
                        }
                    },
                }
                super().__init__()

            def check(self):
                pass

        param = TestParam()
        assert param.meta["name"] == "test_tool"
        assert "query" in param.inputs

    def test_tool_param_base_get_meta(self):
        class TestParam(ToolParamBase):
            def __init__(self):
                self.meta: ToolMeta = {
                    "name": "test_tool",
                    "description": "Test tool description",
                    "parameters": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                            "default": "",
                            "required": True,
                        }
                    },
                }
                super().__init__()
                self.function_name = "test_function"
                self.description = "Custom description"

            def check(self):
                pass

        param = TestParam()
        meta = param.get_meta()

        assert meta["type"] == "function"
        assert meta["function"]["name"] == "test_function"
        assert meta["function"]["description"] == "Custom description"
        assert "properties" in meta["function"]["parameters"]
        assert "query" in meta["function"]["parameters"]["properties"]
        assert "required" in meta["function"]["parameters"]

    def test_tool_param_base_with_enum(self):
        class TestParam(ToolParamBase):
            def __init__(self):
                self.meta: ToolMeta = {
                    "name": "test_tool",
                    "description": "Test tool",
                    "parameters": {
                        "lang": {
                            "type": "string",
                            "description": "Language",
                            "enum": ["python", "javascript"],
                            "required": True,
                        }
                    },
                }
                super().__init__()

            def check(self):
                pass

        param = TestParam()
        meta = param.get_meta()

        assert "enum" in meta["function"]["parameters"]["properties"]["lang"]
        assert meta["function"]["parameters"]["properties"]["lang"]["enum"] == ["python", "javascript"]


class MockToolParam(ToolParamBase):
    """Mock param for testing ToolBase."""

    def __init__(self):
        self.meta: ToolMeta = {
            "name": "mock_tool",
            "description": "Mock tool for testing",
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "Test query",
                    "default": "",
                    "required": True,
                }
            },
        }
        super().__init__()

    def check(self):
        pass


class MockToolBase(ToolBase):
    """Mock tool for testing ToolBase."""

    component_name = "MockTool"

    def _invoke(self, **kwargs):
        return f"processed: {kwargs.get('query', '')}"

    def thoughts(self) -> str:
        return "Mock tool is running..."


class TestToolBase:
    """Tests for ToolBase class."""

    def test_tool_base_init(self):
        canvas = MockCanvas()
        param = MockToolParam()

        tool = MockToolBase(canvas, "test_id", param)

        assert tool._canvas == canvas
        assert tool._id == "test_id"
        assert tool._param == param

    def test_tool_base_get_meta(self):
        canvas = MockCanvas()
        param = MockToolParam()

        tool = MockToolBase(canvas, "test_id", param)
        meta = tool.get_meta()

        assert meta["type"] == "function"
        assert meta["function"]["name"] == "mock_tool"

    def test_tool_base_invoke(self):
        canvas = MockCanvas()
        param = MockToolParam()

        tool = MockToolBase(canvas, "test_id", param)
        result = tool.invoke(query="test query")

        assert "processed: test query" == result

    def test_tool_base_invoke_with_cancel(self):
        canvas = MockCanvas()
        canvas._canceled = True

        param = MockToolParam()
        tool = MockToolBase(canvas, "test_id", param)
        result = tool.invoke(query="test query")

        assert result is None

    def test_tool_base_thoughts(self):
        canvas = MockCanvas()
        param = MockToolParam()

        tool = MockToolBase(canvas, "test_id", param)
        thoughts = tool.thoughts()

        assert "Mock tool is running..." == thoughts

    def test_tool_base_output(self):
        canvas = MockCanvas()
        param = MockToolParam()

        tool = MockToolBase(canvas, "test_id", param)
        tool.set_output("result", "test_value")

        assert tool.output("result") == "test_value"
        assert tool.output()["result"] == "test_value"

    def test_tool_base_invoke_catches_exception(self):
        canvas = MockCanvas()
        param = MockToolParam()

        class FailingTool(ToolBase):
            component_name = "FailingTool"

            def _invoke(self, **kwargs):
                raise ValueError("Test error")

            def thoughts(self) -> str:
                return "Failing tool"

        tool = FailingTool(canvas, "test_id", param)
        result = tool.invoke(query="test")

        assert "Test error" == result
        assert tool.output("_ERROR") == "Test error"


class TestToolBaseRetrieveChunks:
    """Tests for _retrieve_chunks method."""

    @pytest.fixture(autouse=True)
    def mock_kb_prompt(self, monkeypatch):
        """Mock kb_prompt to avoid database connection."""
        import agent.tools.base as base_mod

        monkeypatch.setattr(base_mod, "kb_prompt", lambda chunks, max_tokens, use_template: f"Prompt with {len(chunks.get('chunks', []))} chunks")

    def test_retrieve_chunks_basic(self):
        canvas = MockCanvas()
        param = MockToolParam()

        tool = MockToolBase(canvas, "test_id", param)

        mock_results = [
            {
                "content": "Test content 1",
                "doc_id": "doc1",
                "docnm_kwd": "Document 1",
                "url": "http://example.com/1",
                "score": 0.9,
            },
            {
                "content": "Test content 2",
                "doc_id": "doc2",
                "docnm_kwd": "Document 2",
                "url": "http://example.com/2",
                "score": 0.8,
            },
        ]

        tool._retrieve_chunks(
            mock_results,
            get_title=lambda r: r["docnm_kwd"],
            get_url=lambda r: r["url"],
            get_content=lambda r: r["content"],
            get_score=lambda r: r["score"],
        )

        output = tool.output("formalized_content")
        assert output is not None
        assert len(canvas._references) == 2

    def test_retrieve_chunks_filters_empty_content(self):
        canvas = MockCanvas()
        param = MockToolParam()

        tool = MockToolBase(canvas, "test_id", param)

        mock_results = [
            {"content": "", "doc_id": "doc1", "docnm_kwd": "Doc 1", "url": "http://example.com/1"},
            {"content": "Valid content", "doc_id": "doc2", "docnm_kwd": "Doc 2", "url": "http://example.com/2"},
        ]

        tool._retrieve_chunks(
            mock_results,
            get_title=lambda r: r["docnm_kwd"],
            get_url=lambda r: r["url"],
            get_content=lambda r: r["content"],
        )

        assert len(canvas._references) == 1
        assert canvas._references[0]["content"] == "Valid content"

    def test_retrieve_chunks_handles_base64_images(self):
        canvas = MockCanvas()
        param = MockToolParam()

        tool = MockToolBase(canvas, "test_id", param)

        mock_results = [
            {
                "content": "Text with ![img](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==)",
                "doc_id": "doc1",
                "docnm_kwd": "Doc 1",
                "url": "http://example.com/1",
            }
        ]

        tool._retrieve_chunks(
            mock_results,
            get_title=lambda r: r["docnm_kwd"],
            get_url=lambda r: r["url"],
            get_content=lambda r: r["content"],
        )

        output = tool.output("formalized_content")
        assert "data:image/png" not in output


class TestToolBaseAsync:
    """Tests for async invocation methods."""

    @pytest.mark.asyncio
    async def test_tool_base_invoke_async_sync_function(self):
        canvas = MockCanvas()
        param = MockToolParam()

        tool = MockToolBase(canvas, "test_id", param)
        result = await tool.invoke_async(query="async test")

        assert "processed: async test" == result

    @pytest.mark.asyncio
    async def test_tool_base_invoke_async_coroutine(self):
        canvas = MockCanvas()
        param = MockToolParam()

        class AsyncTool(ToolBase):
            component_name = "AsyncTool"

            async def _invoke_async(self, **kwargs):
                return f"async processed: {kwargs.get('query', '')}"

            def thoughts(self) -> str:
                return "Async tool"

        tool = AsyncTool(canvas, "test_id", param)
        result = await tool.invoke_async(query="async test")

        assert "async processed: async test" == result

    @pytest.mark.asyncio
    async def test_tool_base_invoke_async_catches_exception(self):
        canvas = MockCanvas()
        param = MockToolParam()

        class AsyncFailingTool(ToolBase):
            component_name = "AsyncFailingTool"

            async def _invoke_async(self, **kwargs):
                raise ValueError("Async test error")

            def thoughts(self) -> str:
                return "Async failing tool"

        tool = AsyncFailingTool(canvas, "test_id", param)
        result = await tool.invoke_async(query="test")

        assert "Async test error" == result
        assert tool.output("_ERROR") == "Async test error"
