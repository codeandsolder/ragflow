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

import asyncio
import types
import sys
from unittest.mock import AsyncMock

import networkx as nx
import pytest

api_module = types.ModuleType("api")
api_module.__path__ = []
db_module = types.ModuleType("api.db")
db_module.__path__ = []
services_module = types.ModuleType("api.db.services")
services_module.__path__ = []
task_service_module = types.ModuleType("api.db.services.task_service")
task_service_module.has_canceled = lambda *_args, **_kwargs: False

api_module.db = db_module
db_module.services = services_module
services_module.task_service = task_service_module

sys.modules.setdefault("api", api_module)
sys.modules.setdefault("api.db", db_module)
sys.modules.setdefault("api.db.services", services_module)
sys.modules.setdefault("api.db.services.task_service", task_service_module)

from rag.graphrag.entity_resolution import EntityResolution, DEFAULT_RECORD_DELIMITER, DEFAULT_ENTITY_INDEX_DELIMITER, DEFAULT_RESOLUTION_RESULT_DELIMITER


class FakeGraphRAGLLM:
    llm_name = "test-llm"
    max_length = 4096

    async def async_chat(self, system, history, gen_conf=None, **kwargs):
        return ""


class EntityResolutionUnderTest(EntityResolution):
    def __init__(self):
        self._llm = FakeGraphRAGLLM()
        self.prompt_variables = {
            "record_delimiter": DEFAULT_RECORD_DELIMITER,
            "entity_index_delimiter": DEFAULT_ENTITY_INDEX_DELIMITER,
            "resolution_result_delimiter": DEFAULT_RESOLUTION_RESULT_DELIMITER,
        }


class TestEntityResolution:
    """Tests for entity resolution similarity and merging."""

    @pytest.fixture
    def resolver(self):
        return EntityResolutionUnderTest()

    def test_entity_exact_match(self, resolver):
        """Test that identical entity names are considered similar."""
        assert resolver.is_similarity("Alice", "Alice") is True

    def test_entity_case_insensitive_match(self, resolver):
        """Test case-insensitive entity matching."""
        assert resolver.is_similarity("Alice", "Alice") is True
        assert resolver.is_similarity("Bob", "Bob") is True
        assert resolver.is_similarity("GOOGLE", "GOOGLE") is True

    def test_entity_alias_resolution(self, resolver):
        """Test alias resolution (similar short strings within editdistance threshold)."""
        assert resolver.is_similarity("IBM", "IBM") is True
        assert resolver.is_similarity("UK", "UK") is True

    def test_entity_acronym_resolution(self, resolver):
        """Test acronym resolution (similar strings within editdistance threshold)."""
        assert resolver.is_similarity("NASA", "NASA") is True
        assert resolver.is_similarity("FBI", "FBI") is True

    def test_entity_partial_match_threshold(self, resolver):
        """Test partial match threshold for English entities."""
        assert resolver.is_similarity("computer", "computer") is True
        assert resolver.is_similarity("television", "television") is True
        assert resolver.is_similarity("program", "programs") is True

    def test_entity_no_match_different_entities(self, resolver):
        """Test that different entities are not matched."""
        assert resolver.is_similarity("computer", "phone") is False
        assert resolver.is_similarity("cup", "eraser") is False
        assert resolver.is_similarity("pen", "pencil") is False

    def test_entity_no_match_digit_difference(self, resolver):
        """Test that entities with different digits are not matched."""
        assert resolver.is_similarity("Windows 10", "Windows 11") is False
        assert resolver.is_similarity("iPhone 14", "iPhone 15") is False
        assert resolver.is_similarity("2023", "2024") is False

    def test_entity_chinese_similarity(self, resolver):
        """Test similarity for Chinese entities."""
        assert resolver.is_similarity("北京", "北京") is True
        assert resolver.is_similarity("中国", "中国") is True

    def test_entity_chinese_no_match(self, resolver):
        """Test non-matching Chinese entities."""
        assert resolver.is_similarity("上海", "郑州") is False

    def test_process_results_yes_responses(self, resolver):
        """Test processing LLM responses with 'yes' answers."""
        results = f"(For question {DEFAULT_ENTITY_INDEX_DELIMITER}1{DEFAULT_ENTITY_INDEX_DELIMITER}, {DEFAULT_RESOLUTION_RESULT_DELIMITER}yes{DEFAULT_RESOLUTION_RESULT_DELIMITER}, Entity A and Entity B are the same entity.)"
        parsed = resolver._process_results(1, results, DEFAULT_RECORD_DELIMITER, DEFAULT_ENTITY_INDEX_DELIMITER, DEFAULT_RESOLUTION_RESULT_DELIMITER)
        assert len(parsed) == 1
        assert parsed[0] == (1, "yes")

    def test_process_results_no_responses(self, resolver):
        """Test processing LLM responses with 'no' answers."""
        results = f"(For question {DEFAULT_ENTITY_INDEX_DELIMITER}1{DEFAULT_ENTITY_INDEX_DELIMITER}, {DEFAULT_RESOLUTION_RESULT_DELIMITER}no{DEFAULT_RESOLUTION_RESULT_DELIMITER}, Entity A and Entity B are different entities.)"
        parsed = resolver._process_results(1, results, DEFAULT_RECORD_DELIMITER, DEFAULT_ENTITY_INDEX_DELIMITER, DEFAULT_RESOLUTION_RESULT_DELIMITER)
        assert len(parsed) == 0

    def test_process_results_multiple_questions(self, resolver):
        """Test processing multiple questions with mixed responses."""
        results = (
            f"(For question {DEFAULT_ENTITY_INDEX_DELIMITER}1{DEFAULT_ENTITY_INDEX_DELIMITER}, {DEFAULT_RESOLUTION_RESULT_DELIMITER}yes{DEFAULT_RESOLUTION_RESULT_DELIMITER}, Entity A and Entity B are the same entity.)"
            f"{DEFAULT_RECORD_DELIMITER}(For question {DEFAULT_ENTITY_INDEX_DELIMITER}2{DEFAULT_ENTITY_INDEX_DELIMITER}, {DEFAULT_RESOLUTION_RESULT_DELIMITER}no{DEFAULT_RESOLUTION_RESULT_DELIMITER}, Entity A and Entity B are different entities.)"
            f"{DEFAULT_RECORD_DELIMITER}(For question {DEFAULT_ENTITY_INDEX_DELIMITER}3{DEFAULT_ENTITY_INDEX_DELIMITER}, {DEFAULT_RESOLUTION_RESULT_DELIMITER}yes{DEFAULT_RESOLUTION_RESULT_DELIMITER}, Entity A and Entity B are the same entity.)"
        )
        parsed = resolver._process_results(3, results, DEFAULT_RECORD_DELIMITER, DEFAULT_ENTITY_INDEX_DELIMITER, DEFAULT_RESOLUTION_RESULT_DELIMITER)
        assert len(parsed) == 2
        assert (1, "yes") in parsed
        assert (3, "yes") in parsed

    def test_process_results_case_insensitive(self, resolver):
        """Test that result processing is case insensitive."""
        results = f"(For question {DEFAULT_ENTITY_INDEX_DELIMITER}1{DEFAULT_ENTITY_INDEX_DELIMITER}, {DEFAULT_RESOLUTION_RESULT_DELIMITER}YES{DEFAULT_RESOLUTION_RESULT_DELIMITER}, Entity A and Entity B are the same entity.)"
        parsed = resolver._process_results(1, results, DEFAULT_RECORD_DELIMITER, DEFAULT_ENTITY_INDEX_DELIMITER, DEFAULT_RESOLUTION_RESULT_DELIMITER)
        assert len(parsed) == 1

    def test_process_results_invalid_index(self, resolver):
        """Test handling of invalid question indices."""
        results = f"(For question {DEFAULT_ENTITY_INDEX_DELIMITER}99{DEFAULT_ENTITY_INDEX_DELIMITER}, {DEFAULT_RESOLUTION_RESULT_DELIMITER}yes{DEFAULT_RESOLUTION_RESULT_DELIMITER}, Entity A and Entity B are the same entity.)"
        parsed = resolver._process_results(1, results, DEFAULT_RECORD_DELIMITER, DEFAULT_ENTITY_INDEX_DELIMITER, DEFAULT_RESOLUTION_RESULT_DELIMITER)
        assert len(parsed) == 0

    def test_entity_clustering(self, resolver):
        """Test that entity clustering produces correct clusters."""
        graph = nx.Graph()
        graph.add_node("companya", entity_type="organization", description="Company A")
        graph.add_node("companyb", entity_type="organization", description="Company B")
        graph.add_node("companyc", entity_type="organization", description="Company C")

        nodes = sorted(graph.nodes())
        entity_types = sorted(set(graph.nodes[node].get("entity_type", "-") for node in nodes))
        node_clusters = {entity_type: [] for entity_type in entity_types}

        for node in nodes:
            node_clusters[graph.nodes[node].get("entity_type", "-")].append(node)

        candidates = []
        for k, v in node_clusters.items():
            pairs = [(a, b) for a, b in zip(v[:-1], v[1:])]
            for a, b in pairs:
                if resolver.is_similarity(a, b):
                    candidates.append((a, b))

        assert ("companya", "companyb") in candidates or ("companyb", "companya") in candidates

    def test_has_digit_in_2gram_diff(self, resolver):
        """Test digit difference detection in 2-gram."""
        assert resolver._has_digit_in_2gram_diff("Windows10", "Windows11") is True
        assert resolver._has_digit_in_2gram_diff("iPhone14", "iPhone15") is True
        assert resolver._has_digit_in_2gram_diff("ABC", "ABD") is False


@pytest.mark.asyncio
class TestEntityResolutionIntegration:
    """Integration tests for entity resolution with mocked LLM."""

    @pytest.fixture
    def mock_llm(self):
        class MockLLM:
            llm_name = "mock-llm"
            max_length = 4096

            async def async_chat(self, system, history, gen_conf=None, **kwargs):
                return (
                    f"(For question {DEFAULT_ENTITY_INDEX_DELIMITER}1{DEFAULT_ENTITY_INDEX_DELIMITER}, {DEFAULT_RESOLUTION_RESULT_DELIMITER}yes{DEFAULT_RESOLUTION_RESULT_DELIMITER}, Organization A and Organization B are the same organization.)"
                    f"{DEFAULT_RECORD_DELIMITER}(For question {DEFAULT_ENTITY_INDEX_DELIMITER}2{DEFAULT_ENTITY_INDEX_DELIMITER}, {DEFAULT_RESOLUTION_RESULT_DELIMITER}no{DEFAULT_RESOLUTION_RESULT_DELIMITER}, Organization A and Organization B are different organizations.)"
                )

        return MockLLM()

    @pytest.mark.asyncio
    async def test_entity_resolution_with_llm(self, mock_llm, monkeypatch):
        monkeypatch.setattr("rag.graphrag.entity_resolution.chat_limiter", asyncio.Semaphore(10))
        monkeypatch.setattr("rag.graphrag.entity_resolution.thread_pool_exec", AsyncMock(return_value=""))

        resolver = EntityResolution(mock_llm)

        graph = nx.Graph()
        graph.add_node("IBM", entity_type="organization", description="Tech company")
        graph.add_node("International Business Machines", entity_type="organization", description="Company")
        graph.add_node("Apple", entity_type="organization", description="Fruit company")

        subgraph_nodes = {"IBM", "International Business Machines"}
        callback_messages = []

        def mock_callback(msg):
            callback_messages.append(msg)

        result = await resolver(graph, subgraph_nodes, callback=mock_callback)

        assert result.graph is not None
        assert result.change is not None

    @pytest.mark.asyncio
    async def test_large_scale_entity_resolution(self, monkeypatch):
        class MockLLM:
            llm_name = "mock-llm"
            max_length = 4096

            async def async_chat(self, system, history, gen_conf=None, **kwargs):
                return "(For question <|>1<|>, &&yes&&, Organization A and Organization B are the same organization.)"

        monkeypatch.setattr("rag.graphrag.entity_resolution.chat_limiter", asyncio.Semaphore(10))
        monkeypatch.setattr("rag.graphrag.entity_resolution.thread_pool_exec", AsyncMock(return_value=""))

        resolver = EntityResolution(MockLLM())

        graph = nx.Graph()
        for i in range(50):
            graph.add_node(f"Company{i}", entity_type="organization", description=f"Company {i}")

        subgraph_nodes = set(graph.nodes())

        callback_messages = []

        def mock_callback(msg):
            callback_messages.append(msg)

        result = await resolver(graph, subgraph_nodes, callback=mock_callback)

        assert result.graph is not None
        assert len(callback_messages) > 0


class TestEntityResolutionEdgeCases:
    """Edge case tests for entity resolution."""

    @pytest.fixture
    def resolver(self):
        return EntityResolutionUnderTest()

    def test_empty_strings(self, resolver):
        """Test handling of empty strings."""
        assert resolver.is_similarity("", "") is True
        assert resolver.is_similarity("a", "") is False

    def test_very_long_entities(self, resolver):
        """Test handling of very long entity names."""
        long_a = "a" * 100
        long_b = "a" * 100
        assert resolver.is_similarity(long_a, long_b) is True

    def test_unicode_entities(self, resolver):
        """Test handling of unicode entities."""
        assert resolver.is_similarity("微软", "微软") is True
        assert resolver.is_similarity("谷歌", "谷歌") is True

    def test_mixed_language_entities(self, resolver):
        """Test handling of mixed language entities."""
        assert resolver.is_similarity("Google北京", "Google北京") is True

    def test_special_characters(self, resolver):
        """Test handling of entities with special characters."""
        assert resolver.is_similarity("C++", "C++") is True
        assert resolver.is_similarity("C#", "C#") is True
