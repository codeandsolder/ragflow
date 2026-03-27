# Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the memory-efficient graph processing module."""

import sys
from dataclasses import dataclass
from unittest.mock import MagicMock

import networkx as nx
import pytest

pytest.importorskip("networkx")

MODULES_TO_MOCK = [
    "quart",
    "common.connection_utils",
    "common.settings",
    "common.doc_store",
    "common.doc_store.doc_store_base",
    "rag.nlp",
    "rag.nlp.search",
    "rag.nlp.rag_tokenizer",
    "rag.utils.redis_conn",
    "common.misc_utils",
]

for mod_name in MODULES_TO_MOCK:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

sys.modules["common.connection_utils"].timeout = lambda *a, **kw: lambda fn: fn


@dataclass
class MockMemoryStats:
    used_mb: float = 0.0
    available_mb: float = 1024.0
    peak_mb: float = 0.0


@dataclass
class MockGraphSizeLimits:
    max_nodes: int = 10000
    max_edges: int = 50000
    max_memory_mb: int = 512
    chunk_size: int = 1000


def create_large_graph(num_nodes: int, avg_edges_per_node: int = 5) -> nx.Graph:
    import random

    graph = nx.Graph()
    for i in range(num_nodes):
        graph.add_node(
            f"ENTITY_{i}",
            description=f"Description for entity {i}" * 10,
            source_id=[f"doc_{i % 10}"],
            entity_type="PERSON" if i % 3 == 0 else ("ORG" if i % 3 == 1 else "GEO"),
        )

    for i in range(num_nodes):
        for _ in range(min(avg_edges_per_node, num_nodes - 1)):
            target = random.randint(0, num_nodes - 1)
            if target != i:
                graph.add_edge(
                    f"ENTITY_{i}",
                    f"ENTITY_{target}",
                    description=f"Relation between {i} and {target}",
                    weight=float(random.randint(1, 10)),
                    keywords=[f"keyword_{i}"],
                    source_id=[f"doc_{i % 10}"],
                )
    return graph


class TestGraphMemoryMonitor:
    """Tests for GraphMemoryMonitor class."""

    def test_initialization_with_defaults(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor()
        assert monitor.max_nodes > 0
        assert monitor.max_edges > 0
        assert monitor.max_memory_mb > 0
        assert monitor.chunk_size > 0

    def test_initialization_with_custom_values(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor(
            max_nodes=5000,
            max_edges=25000,
            max_memory_mb=256,
            chunk_size=500,
        )
        assert monitor.max_nodes == 5000
        assert monitor.max_edges == 25000
        assert monitor.max_memory_mb == 256
        assert monitor.chunk_size == 500

    def test_estimate_graph_memory_empty_graph(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor()
        empty_graph = nx.Graph()
        estimated = monitor.estimate_graph_memory_mb(empty_graph)
        assert estimated == 0.0

    def test_estimate_graph_memory_single_node(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor()
        graph = nx.Graph()
        graph.add_node("A", description="Test", source_id=["doc1"])
        estimated = monitor.estimate_graph_memory_mb(graph)
        assert estimated > 0

    def test_estimate_graph_memory_with_edges(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor()
        graph = create_large_graph(10, avg_edges_per_node=2)
        estimated = monitor.estimate_graph_memory_mb(graph)
        assert estimated > 0

    def test_check_memory_limits_empty_graph(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor()
        graph = nx.Graph()
        is_safe, msg = monitor.check_memory_limits(graph)
        assert is_safe is True
        assert msg == "OK"

    def test_check_memory_limits_within_limits(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor(max_nodes=100, max_edges=500, max_memory_mb=10)
        graph = create_large_graph(10, avg_edges_per_node=3)
        is_safe, msg = monitor.check_memory_limits(graph)
        assert is_safe is True

    def test_check_memory_limits_exceeds_nodes(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor(max_nodes=10, max_edges=500, max_memory_mb=1000)
        graph = create_large_graph(50, avg_edges_per_node=2)
        is_safe, msg = monitor.check_memory_limits(graph)
        assert is_safe is False
        assert "nodes" in msg

    def test_should_stream_small_graph(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor(chunk_size=100)
        graph = create_large_graph(10, avg_edges_per_node=2)
        assert monitor.should_stream(graph) is False

    def test_should_stream_large_graph(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor(chunk_size=100)
        graph = create_large_graph(500, avg_edges_per_node=3)
        assert monitor.should_stream(graph) is True


class TestIterGraphNodes:
    """Tests for iter_graph_nodes function."""

    def test_empty_graph(self):
        from rag.graphrag.memory import iter_graph_nodes

        graph = nx.Graph()
        chunks = list(iter_graph_nodes(graph, chunk_size=10))
        assert len(chunks) == 0

    def test_single_chunk(self):
        from rag.graphrag.memory import iter_graph_nodes

        graph = create_large_graph(10, avg_edges_per_node=2)
        chunks = list(iter_graph_nodes(graph, chunk_size=100))
        assert len(chunks) == 1
        assert len(chunks[0]) == 10

    def test_multiple_chunks(self):
        from rag.graphrag.memory import iter_graph_nodes

        graph = create_large_graph(100, avg_edges_per_node=2)
        chunks = list(iter_graph_nodes(graph, chunk_size=30))
        assert len(chunks) == 4
        assert sum(len(c) for c in chunks) == 100


class TestIterGraphChunks:
    """Tests for iter_graph_chunks function."""

    def test_empty_graph(self):
        from rag.graphrag.memory import iter_graph_chunks

        graph = nx.Graph()
        chunks = list(iter_graph_chunks(graph, chunk_size=10))
        assert len(chunks) == 0

    def test_chunks_are_subgraphs(self):
        from rag.graphrag.memory import iter_graph_chunks

        graph = create_large_graph(50, avg_edges_per_node=2)
        for chunk in iter_graph_chunks(graph, chunk_size=20):
            assert isinstance(chunk, nx.Graph)


class TestIterSubgraphsBySource:
    """Tests for iter_subgraphs_by_source function."""

    def test_empty_graph(self):
        from rag.graphrag.memory import iter_subgraphs_by_source

        graph = nx.Graph()
        results = list(iter_subgraphs_by_source(graph))
        assert len(results) == 0

    def test_single_source(self):
        from rag.graphrag.memory import iter_subgraphs_by_source

        graph = nx.Graph()
        for i in range(10):
            graph.add_node(f"ENTITY_{i}", description=f"Entity {i}", source_id=["doc1"])

        results = list(iter_subgraphs_by_source(graph))
        assert len(results) == 1
        source_id, subgraph = results[0]
        assert source_id == "doc1"
        assert subgraph.number_of_nodes() == 10

    def test_multiple_sources(self):
        from rag.graphrag.memory import iter_subgraphs_by_source

        graph = nx.Graph()
        for i in range(20):
            source = f"doc_{i % 3}"
            graph.add_node(f"ENTITY_{i}", description=f"Entity {i}", source_id=[source])

        results = list(iter_subgraphs_by_source(graph))
        assert len(results) == 3

    def test_filter_doc_ids(self):
        from rag.graphrag.memory import iter_subgraphs_by_source

        graph = nx.Graph()
        for i in range(30):
            source = f"doc_{i % 3}"
            graph.add_node(f"ENTITY_{i}", description=f"Entity {i}", source_id=[source])

        results = list(iter_subgraphs_by_source(graph, filter_doc_ids={"doc_0"}))
        assert len(results) == 1
        source_id, subgraph = results[0]
        assert source_id == "doc_0"
        assert subgraph.number_of_nodes() == 10

        results = list(iter_subgraphs_by_source(graph, filter_doc_ids={"doc_0", "doc_2"}))
        assert len(results) == 2
        source_ids = {s for s, _ in results}
        assert source_ids == {"doc_0", "doc_2"}

    def test_filter_doc_ids_empty_set(self):
        from rag.graphrag.memory import iter_subgraphs_by_source

        graph = nx.Graph()
        for i in range(10):
            graph.add_node(f"ENTITY_{i}", description=f"Entity {i}", source_id=[f"doc_{i % 3}"])

        results = list(iter_subgraphs_by_source(graph, filter_doc_ids=set()))
        assert len(results) == 0


class TestStreamPagerank:
    """Tests for stream_pagerank function."""

    def test_empty_graph(self):
        from rag.graphrag.memory import stream_pagerank

        graph = nx.Graph()
        ranks = stream_pagerank(graph)
        assert len(ranks) == 0

    def test_small_graph(self):
        from rag.graphrag.memory import stream_pagerank

        graph = create_large_graph(10, avg_edges_per_node=2)
        ranks = stream_pagerank(graph)
        assert len(ranks) == graph.number_of_nodes()

    def test_large_graph_with_monitor(self):
        from rag.graphrag.memory import stream_pagerank, GraphMemoryMonitor

        monitor = GraphMemoryMonitor(max_nodes=50, max_edges=200)
        graph = create_large_graph(100, avg_edges_per_node=3)
        ranks = stream_pagerank(graph, chunk_size=20, monitor=monitor)
        assert isinstance(ranks, dict)


class TestTruncateGraph:
    """Tests for truncate_graph function."""

    def test_no_truncation_needed(self):
        from rag.graphrag.memory import truncate_graph

        graph = create_large_graph(10, avg_edges_per_node=2)
        truncated = truncate_graph(graph, max_nodes=100, max_edges=500)
        assert truncated.number_of_nodes() == graph.number_of_nodes()

    def test_truncate_nodes(self):
        from rag.graphrag.memory import truncate_graph

        graph = create_large_graph(100, avg_edges_per_node=3)
        truncated = truncate_graph(graph, max_nodes=20, max_edges=1000)
        assert truncated.number_of_nodes() <= 20

    def test_truncate_preserves_high_degree_nodes(self):
        from rag.graphrag.memory import truncate_graph

        graph = create_large_graph(100, avg_edges_per_node=5)
        truncated = truncate_graph(graph, max_nodes=50, max_edges=1000, preserve_high_degree=True)
        assert truncated.number_of_nodes() <= 50


class TestIterConnectedComponents:
    """Tests for iter_connected_components function."""

    def test_empty_graph(self):
        from rag.graphrag.memory import iter_connected_components

        graph = nx.Graph()
        components = list(iter_connected_components(graph))
        assert len(components) == 0

    def test_single_component(self):
        from rag.graphrag.memory import iter_connected_components

        graph = nx.Graph()
        for i in range(10):
            graph.add_node(f"N_{i}", description=f"Node {i}", source_id=["doc1"])
        for i in range(9):
            graph.add_edge(f"N_{i}", f"N_{i + 1}", weight=1.0)

        components = list(iter_connected_components(graph))
        assert len(components) == 1

    def test_multiple_components(self):
        from rag.graphrag.memory import iter_connected_components

        graph = nx.Graph()
        for comp_id in range(3):
            for i in range(5):
                node = f"COMP_{comp_id}_NODE_{i}"
                graph.add_node(node, description=f"Node {node}", source_id=[f"doc_{comp_id}"])
            for i in range(4):
                graph.add_edge(
                    f"COMP_{comp_id}_NODE_{i}",
                    f"COMP_{comp_id}_NODE_{i + 1}",
                    weight=1.0,
                )

        components = list(iter_connected_components(graph))
        assert len(components) == 3


class TestStreamNodeIteration:
    """Tests for stream_node_iteration function."""

    def test_empty_graph(self):
        from rag.graphrag.memory import stream_node_iteration

        graph = nx.Graph()
        nodes = list(stream_node_iteration(graph))
        assert len(nodes) == 0

    def test_small_graph(self):
        from rag.graphrag.memory import stream_node_iteration

        graph = create_large_graph(10, avg_edges_per_node=2)
        nodes = list(stream_node_iteration(graph, chunk_size=5))
        assert len(nodes) == 10

    def test_node_attributes(self):
        from rag.graphrag.memory import stream_node_iteration

        graph = nx.Graph()
        graph.add_node("A", description="Node A", source_id=["doc1"])
        graph.add_node("B", description="Node B", source_id=["doc2"])

        nodes = list(stream_node_iteration(graph))
        assert len(nodes) == 2
        for node, attrs in nodes:
            assert "description" in attrs


class TestStreamEdgeIteration:
    """Tests for stream_edge_iteration function."""

    def test_empty_graph(self):
        from rag.graphrag.memory import stream_edge_iteration

        graph = nx.Graph()
        edges = list(stream_edge_iteration(graph))
        assert len(edges) == 0

    def test_graph_with_edges(self):
        from rag.graphrag.memory import stream_edge_iteration

        graph = create_large_graph(10, avg_edges_per_node=2)
        edges = list(stream_edge_iteration(graph, chunk_size=5))
        assert len(edges) == graph.number_of_edges()


class TestMergeGraphsStreaming:
    """Tests for merge_graphs_streaming function."""

    def test_empty_iterator(self):
        from rag.graphrag.memory import merge_graphs_streaming

        result = merge_graphs_streaming(iter([]))
        assert result is None

    def test_single_graph(self):
        from rag.graphrag.memory import merge_graphs_streaming

        graph = create_large_graph(10, avg_edges_per_node=2)
        result = merge_graphs_streaming(iter([graph]))
        assert result is not None
        assert result.number_of_nodes() == 10

    def test_multiple_graphs(self):
        from rag.graphrag.memory import merge_graphs_streaming

        graphs = [create_large_graph(5, avg_edges_per_node=1) for _ in range(3)]
        result = merge_graphs_streaming(iter(graphs))
        assert result is not None


class TestGraphSizeEstimation:
    """Tests for graph size estimation accuracy."""

    def test_size_scales_with_nodes(self):
        from rag.graphrag.memory import GraphMemoryMonitor

        monitor = GraphMemoryMonitor()
        small = create_large_graph(10, avg_edges_per_node=2)
        medium = create_large_graph(50, avg_edges_per_node=2)
        large = create_large_graph(100, avg_edges_per_node=2)

        small_est = monitor.estimate_graph_memory_mb(small)
        medium_est = monitor.estimate_graph_memory_mb(medium)
        large_est = monitor.estimate_graph_memory_mb(large)

        assert 0 < small_est < medium_est < large_est
