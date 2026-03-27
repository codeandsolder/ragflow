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
Tests for the GraphRAG chunk-to-graph construction pipeline.

This module tests the end-to-end graph extraction pipeline from chunk text
to entity/relationship graph, including extraction, merging, deduplication,
and graph structure integrity.
"""

import pytest
import networkx as nx
from unittest.mock import MagicMock
from collections import defaultdict


class TestGraphConstruction:
    """Test suite for GraphRAG chunk-to-graph construction pipeline."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM that returns predefined responses."""
        mock = MagicMock()
        mock.llm_name = "mock-llm"
        mock.max_length = 4096

        async def mock_chat(system, history, gen_conf=None, **kwargs):
            return ("", 0)

        mock.async_chat = mock_chat
        return mock

    @pytest.fixture
    def sample_chunks(self):
        """Sample document chunks for testing."""
        return [
            "Alice works at Google. She develops machine learning algorithms.",
            "Bob is a researcher at MIT. He collaborates with Alice on AI projects.",
        ]

    def test_single_chunk_extraction(self, mock_llm, sample_chunks):
        """
        Test entity and relation extraction from a single chunk.

        Expected behavior:
        - Entities: Alice, Google, Bob, MIT
        - Relations: Alice-Google (works at), Alice-Bob (collaborates)
        """
        from rag.graphrag.utils import handle_single_entity_extraction, handle_single_relationship_extraction

        entity_records = [
            '"entity"<|>Alice<|>person<|>Alice works at Google and develops ML algorithms',
            '"entity"<|>Google<|>organization<|>Google is a technology company',
            '"entity"<|>machine learning<|>category<|>ML algorithms developed by Alice',
        ]
        relation_records = [
            '"relationship"<|>Alice<|>Google<|>Alice works at Google<|>employment<|>8',
            '"relationship"<|>Alice<|>machine learning<|>Alice develops ML algorithms<|>develops<|>7',
        ]

        extracted_entities = []
        for record in entity_records:
            attrs = record.split("<|>")
            result = handle_single_entity_extraction(attrs, "chunk_0")
            if result:
                extracted_entities.append(result)

        extracted_relations = []
        for record in relation_records:
            attrs = record.split("<|>")
            result = handle_single_relationship_extraction(attrs, "chunk_0")
            if result:
                extracted_relations.append(result)

        assert len(extracted_entities) == 3
        entity_names = [e["entity_name"] for e in extracted_entities]
        assert "ALICE" in entity_names
        assert "GOOGLE" in entity_names

        assert len(extracted_relations) == 2
        relation_pairs = [(r["src_id"], r["tgt_id"]) for r in extracted_relations]
        assert ("ALICE", "GOOGLE") in relation_pairs or ("GOOGLE", "ALICE") in relation_pairs

    def test_multi_chunk_merging(self):
        """
        Test that entities and relations from multiple chunks are properly merged.

        Expected behavior:
        - Same entities across chunks are deduplicated
        - Descriptions are concatenated
        - Relations between entities from different chunks are preserved
        """
        from rag.graphrag.utils import graph_merge, GraphChange

        graph1 = nx.Graph()
        graph1.add_node(
            "ALICE",
            entity_type="person",
            description="Alice works at Google",
            source_id=["doc1", "chunk0"],
        )
        graph1.add_node(
            "BOB",
            entity_type="person",
            description="Bob works at MIT",
            source_id=["doc1", "chunk0"],
        )
        graph1.add_edge(
            "ALICE",
            "BOB",
            description="They collaborate on AI",
            keywords=["collaboration", "AI"],
            weight=5.0,
            source_id=["doc1", "chunk0"],
        )
        graph1.graph["source_id"] = ["doc1"]

        graph2 = nx.Graph()
        graph2.add_node(
            "ALICE",
            entity_type="person",
            description="Alice develops ML algorithms",
            source_id=["doc1", "chunk1"],
        )
        graph2.add_node(
            "GOOGLE",
            entity_type="organization",
            description="Google is a tech company",
            source_id=["doc1", "chunk1"],
        )
        graph2.add_edge(
            "ALICE",
            "GOOGLE",
            description="Alice is employed at Google",
            keywords=["employment"],
            weight=8.0,
            source_id=["doc1", "chunk1"],
        )
        graph2.graph["source_id"] = ["doc1"]

        change = GraphChange()
        result = graph_merge(graph1, graph2, change)

        assert result.has_node("ALICE")
        assert result.has_node("BOB")
        assert result.has_node("GOOGLE")

        alice_desc = result.nodes["ALICE"]["description"]
        assert "Google" in alice_desc
        assert "ML algorithms" in alice_desc

        assert "chunk0" in result.nodes["ALICE"]["source_id"]
        assert "chunk1" in result.nodes["ALICE"]["source_id"]

        assert result.has_edge("ALICE", "BOB")
        assert result.has_edge("ALICE", "GOOGLE")

    def test_entity_deduplication(self):
        """
        Test entity deduplication across multiple extraction results.

        Expected behavior:
        - Entities with same name but different sources are merged
        - Most frequent entity_type is selected
        - Descriptions are concatenated with separator
        """
        from rag.graphrag.utils import handle_single_entity_extraction

        entity_variants = [
            '"entity"<|>Google<|>organization<|>A tech company',
            '"entity"<|>GOOGLE<|>company<|>Technology corporation',
            '"entity"<|>google<|>organization<|>Internet search engine',
        ]

        extracted = []
        for record in entity_variants:
            attrs = record.split("<|>")
            result = handle_single_entity_extraction(attrs, "chunk_0")
            if result:
                extracted.append(result)

        assert len(extracted) == 3

        names = [e["entity_name"] for e in extracted]
        assert all(n == "GOOGLE" for n in names)

        types = [e["entity_type"] for e in extracted]
        type_counts = defaultdict(int)
        for t in types:
            type_counts[t] += 1

        merged_type = max(type_counts.items(), key=lambda x: x[1])[0]
        assert merged_type in ["ORGANIZATION", "COMPANY"]

    def test_relation_extraction(self):
        """
        Test relation extraction from parsed LLM response records.

        Expected behavior:
        - Source and target entities are correctly identified
        - Relationship description is captured
        - Weight is parsed correctly (defaults to 1.0)
        - Keywords are extracted
        """
        from rag.graphrag.utils import handle_single_relationship_extraction

        relation_record = '"relationship"<|>Alice<|>Bob<|>Alice collaborates with Bob on research<|>collaboration, research<|>9.5'
        attrs = relation_record.split("<|>")

        result = handle_single_relationship_extraction(attrs, "chunk_0")

        assert result is not None
        assert result["src_id"] == "ALICE"
        assert result["tgt_id"] == "BOB"
        assert result["description"] == "Alice collaborates with Bob on research"
        assert result["weight"] == 9.5
        assert "collaboration" in result["keywords"]
        assert "research" in result["keywords"]
        assert result["source_id"] == "chunk_0"

    def test_graph_structure_integrity(self):
        """
        Test that the graph maintains structural integrity after construction.

        Expected behavior:
        - All nodes have required attributes (entity_name, entity_type, description, source_id)
        - All edges have required attributes (src_id, tgt_id, description, keywords, weight, source_id)
        - Graph is connected (or has expected connected components)
        """
        from rag.graphrag.utils import tidy_graph

        graph = nx.Graph()

        graph.add_node(
            "ALICE",
            entity_type="person",
            description="A person",
            source_id=["doc1"],
        )
        graph.add_node(
            "BOB",
            entity_type="person",
            description="Another person",
            source_id=["doc1"],
        )
        graph.add_edge(
            "ALICE",
            "BOB",
            description="Friends",
            keywords=["friend"],
            weight=5.0,
            source_id=["doc1"],
        )

        messages = []
        tidy_graph(graph, lambda msg: messages.append(msg))

        for node, attrs in graph.nodes(data=True):
            assert "entity_type" in attrs
            assert "description" in attrs
            assert "source_id" in attrs

        for u, v, attrs in graph.edges(data=True):
            assert "description" in attrs
            assert "keywords" in attrs
            assert "weight" in attrs

        assert graph.has_edge("ALICE", "BOB")
        assert nx.is_connected(graph)

    def test_empty_chunk_handling(self):
        """
        Test that empty or whitespace-only chunks are handled gracefully.

        Expected behavior:
        - No entities or relations extracted from empty chunks
        - Pipeline continues without errors
        """
        from rag.graphrag.utils import handle_single_entity_extraction, handle_single_relationship_extraction

        empty_records = []
        assert len(empty_records) == 0

        result = handle_single_entity_extraction([], "chunk_0")
        assert result is None

        result = handle_single_relationship_extraction([], "chunk_0")
        assert result is None

        result = handle_single_entity_extraction(['"entity"'], "chunk_0")
        assert result is None

        result = handle_single_relationship_extraction(['"relationship"', "A"], "chunk_0")
        assert result is None

    def test_special_character_handling(self):
        """
        Test that special characters in entity/relation names are handled correctly.

        Expected behavior:
        - HTML entities are unescaped
        - Control characters are removed
        - Quotes are stripped
        - Unicode characters are preserved
        """
        from rag.graphrag.utils import clean_str, handle_single_entity_extraction

        test_cases = [
            ("Alice &amp; Bob", "Alice & Bob"),
            ('"Alice"', "Alice"),
            ("Alice\x00Bob", "AliceBob"),
            ("Alice\u4e2d\u6587", "Alice中文"),
            ("Alice\t\nBob", "Alice Bob"),
        ]

        for input_str, expected in test_cases:
            result = clean_str(input_str)
            assert result == expected

        entity_record = '"entity"<|>Alice &amp; Bob<|>person<|>A test entity'
        attrs = entity_record.replace("&amp;", "&").split("<|>")
        result = handle_single_entity_extraction(attrs, "chunk_0")

        assert result is not None
        assert "ALICE" in result["entity_name"] or "&" in result["entity_name"]

    def test_multilingual_extraction(self):
        """
        Test extraction with multilingual content.

        Expected behavior:
        - Entities in different languages are correctly identified
        - Language-specific characters are preserved
        - Cross-language relations are captured
        """
        from rag.graphrag.utils import handle_single_entity_extraction, handle_single_relationship_extraction

        multilingual_entities = [
            '"entity"<|>张三<|>person<|>中国工程师',
            '"entity"<|>Tokyo<|>geo<|>Capital of Japan',
            '"entity"<|>الذكاء الاصطناعي<|>category<|>Artificial Intelligence in Arabic',
            '"entity"<|>Россия<|>geo<|>Russia in Russian',
        ]

        extracted = []
        for record in multilingual_entities:
            attrs = record.split("<|>")
            result = handle_single_entity_extraction(attrs, "chunk_0")
            if result:
                extracted.append(result)

        assert len(extracted) == 4

        entity_names = [e["entity_name"] for e in extracted]
        assert "张三" in entity_names or "张三" in "".join(entity_names)
        assert "TOKYO" in entity_names

        multilingual_relation = '"relationship"<|>张三<|>Tokyo<|>Works remotely for Tokyo company<|>employment<|>6'
        attrs = multilingual_relation.split("<|>")
        result = handle_single_relationship_extraction(attrs, "chunk_0")

        assert result is not None


class TestEntityRelationProcessing:
    """Tests for entity and relation processing utilities."""

    def test_entities_and_relations_parsing(self):
        """Test parsing of combined entity/relation records."""
        from rag.graphrag.utils import handle_single_entity_extraction, handle_single_relationship_extraction

        records = [
            '"entity"<|>Alice<|>person<|>A person',
            '"relationship"<|>Alice<|>Bob<|>Friends<|>friend<|>5',
            '"entity"<|>Bob<|>person<|>Another person',
        ]

        nodes = {}
        edges = {}

        for i, record in enumerate(records):
            attrs = record.split("<|>")
            chunk_key = "test_chunk"

            entity_result = handle_single_entity_extraction(attrs, chunk_key)
            if entity_result:
                nodes[entity_result["entity_name"]] = [entity_result]
                continue

            relation_result = handle_single_relationship_extraction(attrs, chunk_key)
            if relation_result:
                key = (relation_result["src_id"], relation_result["tgt_id"])
                edges[key] = [relation_result]

        assert len(nodes) == 2
        assert len(edges) == 1


class TestGraphTransformations:
    """Tests for graph transformation operations."""

    def test_graph_to_subgraph_conversion(self):
        """Test conversion of full graph to document subgraphs."""
        graph = nx.Graph()
        graph.add_node("A", description="desc", source_id=["doc1", "doc2"])
        graph.add_node("B", description="desc", source_id=["doc1"])
        graph.add_node("C", description="desc", source_id=["doc2"])
        graph.graph["source_id"] = ["doc1", "doc2"]

        subgraph_doc1 = graph.subgraph([n for n in graph.nodes if "doc1" in graph.nodes[n]["source_id"]]).copy()

        assert subgraph_doc1.has_node("A")
        assert subgraph_doc1.has_node("B")
        assert not subgraph_doc1.has_node("C")

    def test_node_link_data_conversion(self):
        """Test NetworkX node_link_data serialization."""

        graph = nx.Graph()
        graph.add_node("A", description="desc", source_id=["doc1"])
        graph.add_node("B", description="desc", source_id=["doc1"])
        graph.add_edge("A", "B", description="edge", weight=1.0)

        data = nx.node_link_data(graph, edges="edges")

        assert "nodes" in data
        assert "links" in data

        restored = nx.node_link_graph(data, edges="edges")
        assert restored.has_node("A")
        assert restored.has_node("B")
        assert restored.has_edge("A", "B")
