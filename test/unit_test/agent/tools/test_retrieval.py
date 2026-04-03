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
from unittest.mock import patch, MagicMock, AsyncMock

from agent.canvas import Canvas
from agent.tools.retrieval import Retrieval, RetrievalParam


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
        return "retrieval"

    def add_reference(self, chunks, aggs):
        self._references.extend(chunks)

    def get_variable_value(self, var_name):
        return self.variables.get(var_name)

    def set_variable_value(self, var_name, value):
        self.variables[var_name] = value

    def get_tenant_id(self):
        return self._tenant_id


class TestRetrievalParam:
    """Tests for RetrievalParam class."""

    def test_retrieval_param_init(self):
        param = RetrievalParam()

        assert param.meta["name"] == "search_my_dateset"
        assert param.similarity_threshold == 0.2
        assert param.keywords_similarity_weight == 0.5
        assert param.top_n == 8
        assert param.top_k == 1024
        assert param.kb_ids == []
        assert param.memory_ids == []
        assert param.empty_response == ""

    def test_retrieval_param_check_valid(self):
        param = RetrievalParam()
        param.check()

        assert param.similarity_threshold == 0.2

    def test_retrieval_param_check_invalid_threshold(self):
        param = RetrievalParam()
        param.similarity_threshold = 1.5

        with pytest.raises(ValueError):
            param.check()

    def test_retrieval_param_check_invalid_top_n(self):
        param = RetrievalParam()
        param.top_n = -1

        with pytest.raises(ValueError):
            param.check()

    def test_retrieval_param_get_input_form(self):
        param = RetrievalParam()
        input_form = param.get_input_form()

        assert "query" in input_form
        assert input_form["query"]["type"] == "line"


class TestRetrieval:
    """Tests for Retrieval class."""

    def test_retrieval_init(self):
        canvas = MockCanvas()
        param = RetrievalParam()

        retrieval = Retrieval(canvas, "test_id", param)

        assert retrieval._canvas == canvas
        assert retrieval._id == "test_id"
        assert retrieval.component_name == "Retrieval"

    def test_retrieval_thoughts(self):
        canvas = MockCanvas()
        param = RetrievalParam()

        retrieval = Retrieval(canvas, "test_id", param)
        retrieval.set_input_value("query", "test query")

        thoughts = retrieval.thoughts()

        assert "test query" in thoughts
        assert "Keywords" in thoughts

    def test_retrieval_thoughts_input_value_precedence(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.query = "param query"
        retrieval = Retrieval(canvas, "test_id", param)
        retrieval.set_input_value("query", "input value query")

        thoughts = retrieval.thoughts()

        assert "input value query" in thoughts
        assert "param query" not in thoughts

    def test_retrieval_thoughts_fallback_to_param_input(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.query = "param-only query"
        retrieval = Retrieval(canvas, "test_id", param)

        thoughts = retrieval.thoughts()

        assert "param-only query" in thoughts

    @pytest.mark.anyio
    async def test_retrieval_invoke_empty_query(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.empty_response = "No results found"

        retrieval = Retrieval(canvas, "test_id", param)

        with patch.object(retrieval, "_invoke_async", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "No results found"
            result = retrieval.invoke(query="")

        assert result == "No results found"

    @pytest.mark.anyio
    async def test_retrieval_set_output_formalized_content(self):
        canvas = MockCanvas()
        param = RetrievalParam()

        retrieval = Retrieval(canvas, "test_id", param)
        retrieval.set_output("formalized_content", "Test content")

        output = retrieval.output("formalized_content")
        assert output == "Test content"

    @pytest.mark.anyio
    async def test_retrieval_set_output_json(self):
        canvas = MockCanvas()
        param = RetrievalParam()

        retrieval = Retrieval(canvas, "test_id", param)
        test_chunks = [{"chunk_id": "1", "content": "test"}]
        retrieval.set_output("json", test_chunks)

        output = retrieval.output("json")
        assert output == test_chunks

    def test_retrieval_get_input_elements(self):
        canvas = MockCanvas()
        param = RetrievalParam()

        retrieval = Retrieval(canvas, "test_id", param)
        inputs = retrieval.get_input_elements()

        assert "query" in inputs


class TestRetrievalKBRetrieval:
    """Tests for KB retrieval functionality."""

    @pytest.mark.anyio
    async def test_retrieval_kb_no_kb_selected(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.kb_ids = []

        retrieval = Retrieval(canvas, "test_id", param)

        with patch("agent.tools.retrieval.KnowledgebaseService") as mock_kb_service:
            mock_kb_service.get_by_ids.return_value = []

            with pytest.raises(Exception, match="No dataset is selected"):
                await retrieval._retrieve_kb("test query")

    @patch("agent.tools.retrieval.settings")
    @pytest.mark.anyio
    async def test_retrieval_kb_with_mock_kb(self, mock_settings):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.kb_ids = ["kb1"]

        mock_kb = MagicMock()
        mock_kb.id = "kb1"
        mock_kb.tenant_id = "tenant1"
        mock_kb.embd_id = "embd1"

        with patch("agent.tools.retrieval.KnowledgebaseService") as mock_kb_service:
                with patch("agent.tools.retrieval.get_model_config_by_type_and_name") as mock_get_model:
                    with patch("agent.tools.retrieval.LLMBundle"):
                        with patch("agent.tools.retrieval.kb_prompt", return_value=["Test chunk"]):
                            mock_kb_service.get_by_ids.return_value = [mock_kb]
                            mock_get_model.return_value = MagicMock()

                            mock_settings.retriever = MagicMock()
                            mock_settings.retriever.retrieval = AsyncMock(
                        return_value={
                            "chunks": [
                                {
                                    "chunk_id": "1",
                                    "content": "Test chunk",
                                    "doc_id": "doc1",
                                    "docnm_kwd": "Test Doc",
                                    "similarity": 0.9,
                                    "url": "http://example.com",
                                }
                            ],
                            "doc_aggs": [{"doc_name": "Test Doc", "doc_id": "doc1", "count": 1}],
                        }
                    )

                            retrieval = Retrieval(canvas, "test_id", param)
                            await retrieval._retrieve_kb("test query")

                            output = retrieval.output("formalized_content")
                            assert output is not None
                            assert "Test chunk" in output


class TestRetrievalMemoryRetrieval:
    """Tests for memory retrieval functionality."""

    @pytest.mark.anyio
    async def test_retrieval_memory_no_memory_selected(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.memory_ids = []
        param.retrieval_from = "memory"

        retrieval = Retrieval(canvas, "test_id", param)
        with patch("agent.tools.retrieval.MemoryService") as mock_mem_service:
            mock_mem_service.get_by_ids.return_value = []
            with pytest.raises(Exception, match="No memory is selected"):
                await retrieval._retrieve_memory("test query")

    @patch("agent.tools.retrieval.settings")
    @pytest.mark.anyio
    async def test_retrieval_memory_with_mock(self, mock_settings):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.memory_ids = ["mem1"]
        param.retrieval_from = "memory"
        param.similarity_threshold = 0.2
        param.keywords_similarity_weight = 0.5
        param.top_n = 8

        mock_memory = MagicMock()
        mock_memory.id = "mem1"
        mock_memory.embd_id = "embd1"

        with patch("agent.tools.retrieval.MemoryService") as mock_mem_service:
            with patch("agent.tools.retrieval.memory_message_service") as mock_msg_service:
                mock_mem_service.get_by_ids.return_value = [mock_memory]
                mock_msg_service.query_message.return_value = [{"role": "user", "content": "Hello", "created_at": "2024-01-01"}]

                retrieval = Retrieval(canvas, "test_id", param)
                result = await retrieval._retrieve_memory("test query")

                assert result is not None


class TestRetrievalInvokeAsync:
    """Tests for invoke_async method."""

    @pytest.mark.anyio
    async def test_invoke_async_empty_query(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.empty_response = "No results"

        retrieval = Retrieval(canvas, "test_id", param)
        result = await retrieval.invoke_async(query="")

        assert result is None
        output = retrieval.output("formalized_content")
        assert output == "No results"

    @pytest.mark.anyio
    async def test_invoke_async_with_query(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.empty_response = "No results"
        param.kb_ids = ["kb1"]

        retrieval = Retrieval(canvas, "test_id", param)

        with patch.object(retrieval, "_retrieve_kb", new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = "Retrieved content"
            result = await retrieval.invoke_async(query="test")

            assert result == "Retrieved content"

    @pytest.mark.anyio
    async def test_invoke_async_prefers_dataset_when_both_configured(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.kb_ids = ["kb1"]
        param.memory_ids = ["mem1"]
        retrieval = Retrieval(canvas, "test_id", param)

        with patch.object(retrieval, "_retrieve_kb", new_callable=AsyncMock) as mock_retrieve_kb:
            with patch.object(retrieval, "_retrieve_memory", new_callable=AsyncMock) as mock_retrieve_memory:
                mock_retrieve_kb.return_value = "kb result"
                result = await retrieval.invoke_async(query="test")

                assert result == "kb result"
                mock_retrieve_kb.assert_awaited_once_with("test")
                mock_retrieve_memory.assert_not_awaited()

    @pytest.mark.anyio
    async def test_invoke_async_kb_prompt_failure_sets_error_output(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.kb_ids = ["kb1"]
        retrieval = Retrieval(canvas, "test_id", param)

        mock_kb = MagicMock()
        mock_kb.id = "kb1"
        mock_kb.tenant_id = "tenant1"
        mock_kb.embd_id = "embd1"

        with patch("agent.tools.retrieval.KnowledgebaseService") as mock_kb_service:
            with patch("agent.tools.retrieval.get_model_config_by_type_and_name") as mock_get_model:
                with patch("agent.tools.retrieval.LLMBundle"):
                    with patch("agent.tools.retrieval.settings") as mock_settings:
                        with patch("agent.tools.retrieval.kb_prompt", side_effect=RuntimeError("kb_prompt failed")):
                            mock_kb_service.get_by_ids.return_value = [mock_kb]
                            mock_get_model.return_value = MagicMock()
                            mock_settings.retriever = MagicMock()
                            mock_settings.retriever.retrieval = AsyncMock(
                                return_value={
                                    "chunks": [
                                        {
                                            "chunk_id": "1",
                                            "content": "Test chunk",
                                            "doc_id": "doc1",
                                            "docnm_kwd": "Test Doc",
                                            "similarity": 0.9,
                                            "url": "http://example.com",
                                        }
                                    ],
                                    "doc_aggs": [{"doc_name": "Test Doc", "doc_id": "doc1", "count": 1}],
                                }
                            )
                            mock_settings.retriever.retrieval_by_children.return_value = [
                                {
                                    "chunk_id": "1",
                                    "content": "Test chunk",
                                    "doc_id": "doc1",
                                    "docnm_kwd": "Test Doc",
                                    "similarity": 0.9,
                                    "url": "http://example.com",
                                }
                            ]

                            result = await retrieval.invoke_async(query="test")

                            assert result == "kb_prompt failed"
                            assert retrieval.output("_ERROR") == "kb_prompt failed"

    @pytest.mark.anyio
    async def test_invoke_async_timeout_error_sets_error_output(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.kb_ids = ["kb1"]
        retrieval = Retrieval(canvas, "test_id", param)

        with patch.object(retrieval, "_retrieve_kb", new_callable=AsyncMock) as mock_retrieve_kb:
            mock_retrieve_kb.side_effect = TimeoutError("timed out")

            result = await retrieval.invoke_async(query="test")

            assert isinstance(result, str)
            assert "Operation timed out after" in result
            assert retrieval.output("_ERROR") == result

    @pytest.mark.anyio
    async def test_invoke_async_cancelled(self):
        canvas = MockCanvas()
        canvas._canceled = True

        param = RetrievalParam()
        retrieval = Retrieval(canvas, "test_id", param)

        result = await retrieval.invoke_async(query="test")
        assert result is None


class TestRetrievalEdgeCases:
    """Tests for edge cases."""

    def test_retrieval_with_empty_kb_ids(self):
        canvas = MockCanvas()
        param = RetrievalParam()
        param.kb_ids = []
        param.memory_ids = []
        param.empty_response = "Empty"

        retrieval = Retrieval(canvas, "test_id", param)

        assert retrieval._param.kb_ids == []
        assert retrieval._param.empty_response == "Empty"

    def test_retrieval_parameter_defaults(self):
        param = RetrievalParam()

        assert param.use_kg is False
        assert param.cross_languages == []
        assert param.toc_enhance is False
        assert param.meta_data_filter == {}
        assert param.rerank_id == ""
        assert param.kb_vars == []

    def test_retrieval_with_meta_data_filter(self):
        param = RetrievalParam()
        param.meta_data_filter = {"method": "auto", "filters": []}

        assert param.meta_data_filter["method"] == "auto"
        param.check()

    def test_retrieval_string_format(self):
        canvas = MockCanvas()
        param = RetrievalParam()

        retrieval = Retrieval(canvas, "test_id", param)

        result = retrieval.string_format("Hello {name}", {"name": "World"})
        assert result == "Hello World"

    def test_retrieval_get_input_elements_from_text(self):
        canvas = MockCanvas()
        canvas.set_variable_value("sys.query_var", "test value")

        param = RetrievalParam()
        retrieval = Retrieval(canvas, "test_id", param)

        elements = retrieval.get_input_elements_from_text("{{sys.query_var}}")

        assert "sys.query_var" in elements

    def test_retrieval_get_input_elements_from_text_malformed_and_whitespace(self):
        canvas = MockCanvas()
        canvas.set_variable_value("sys.query_var", "test value")
        param = RetrievalParam()
        retrieval = Retrieval(canvas, "test_id", param)

        malformed = retrieval.get_input_elements_from_text("{{sys.query_var}")
        unsupported_whitespace = retrieval.get_input_elements_from_text("{{ sys.query_var }}")
        supported_spaced_braces = retrieval.get_input_elements_from_text("{ {sys.query_var} }")

        assert "sys.query_var" in malformed
        assert unsupported_whitespace == {}
        assert "sys.query_var" in supported_spaced_braces
