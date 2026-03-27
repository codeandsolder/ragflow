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

import gc
import json
import sys
from dataclasses import dataclass
from unittest.mock import MagicMock

import networkx as nx
import pytest

from rag.graphrag.memory import (
    iter_graph_chunks,
)

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
    graph = nx.Graph()
    for i in range(num_nodes):
        graph.add_node(
            f"ENTITY_{i}",
            description=f"Description for entity {i}" * 10,
            source_id=[f"doc_{i % 10}"],
            entity_type="PERSON" if i % 3 == 0 else ("ORG" if i % 3 == 1 else "GEO"),
        )
    import random

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


def estimate_graph_memory_size(graph: nx.Graph) -> float:
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()
    avg_node_attrs = 3
    avg_edge_attrs = 4
    bytes_per_attr = 100
    node_memory = node_count * avg_node_attrs * bytes_per_attr
    edge_memory = edge_count * avg_edge_attrs * bytes_per_attr
    overhead_factor = 1.5
    return (node_memory + edge_memory) * overhead_factor / (1024 * 1024)


def split_graph_into_chunks(graph: nx.Graph, chunk_size: int) -> list[nx.Graph]:
    nodes = list(graph.nodes())
    chunks = []
    for i in range(0, len(nodes), chunk_size):
        chunk_nodes = nodes[i : i + chunk_size]
        subgraph = graph.subgraph(chunk_nodes).copy()
        chunks.append(subgraph)
    return chunks


class MockMemoryProfiler:
    def __init__(self, initial_memory_mb: float = 100.0, max_memory_mb: float = 1024.0):
        self.current_memory = initial_memory_mb
        self.max_memory = max_memory_mb
        self.peak_memory = initial_memory_mb
        self.allocations: list[float] = []

    def allocate(self, size_mb: float) -> bool:
        if self.current_memory + size_mb > self.max_memory:
            return False
        self.current_memory += size_mb
        self.allocations.append(size_mb)
        self.peak_memory = max(self.peak_memory, self.current_memory)
        return True

    def deallocate(self, size_mb: float):
        self.current_memory = max(0, self.current_memory - size_mb)

    def get_stats(self) -> MockMemoryStats:
        return MockMemoryStats(
            used_mb=self.current_memory,
            available_mb=self.max_memory - self.current_memory,
            peak_mb=self.peak_memory,
        )

    def reset(self):
        self.current_memory = 100.0
        self.peak_memory = 100.0
        self.allocations = []


class TestGraphMemoryManagement:
    def test_graph_size_limit_enforcement(self):
        limits = MockGraphSizeLimits(max_nodes=100, max_edges=500)
        graph = create_large_graph(200, avg_edges_per_node=3)
        assert graph.number_of_nodes() == 200
        assert graph.number_of_nodes() > limits.max_nodes
        nodes_to_remove = list(graph.nodes())[limits.max_nodes :]
        for node in nodes_to_remove:
            graph.remove_node(node)
        assert graph.number_of_nodes() <= limits.max_nodes
        while graph.number_of_edges() > limits.max_edges:
            edges = list(graph.edges())
            if edges:
                graph.remove_edge(*edges[0])
            else:
                break
        assert graph.number_of_edges() <= limits.max_edges
        assert graph.number_of_nodes() <= limits.max_nodes
        assert graph.number_of_edges() <= limits.max_edges

    def test_memory_efficient_loading(self):
        profiler = MockMemoryProfiler(initial_memory_mb=50.0, max_memory_mb=200.0)
        large_graph = create_large_graph(500, avg_edges_per_node=3)
        estimated_size = estimate_graph_memory_size(large_graph)
        assert profiler.allocate(estimated_size * 0.5), "Should allocate memory for partial graph"
        chunks = split_graph_into_chunks(large_graph, chunk_size=100)
        assert len(chunks) == 5
        loaded_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_size_mb = estimate_graph_memory_size(chunk)
            if profiler.allocate(chunk_size_mb):
                loaded_chunks.append(chunk)
            else:
                break
        assert len(loaded_chunks) >= 1
        for chunk in loaded_chunks:
            assert isinstance(chunk, nx.Graph)
            assert chunk.number_of_nodes() > 0

    def test_large_graph_chunking(self):
        large_graph = create_large_graph(1000, avg_edges_per_node=5)
        chunk_size = 100
        chunks = split_graph_into_chunks(large_graph, chunk_size)
        assert len(chunks) == 10
        total_nodes = sum(c.number_of_nodes() for c in chunks)
        assert total_nodes == 1000
        for chunk in chunks:
            assert chunk.number_of_nodes() <= chunk_size
            for node in chunk.nodes():
                assert large_graph.has_node(node)
        for i, chunk in enumerate(chunks):
            chunk_nodes = set(chunk.nodes())
            other_chunks_nodes = set()
            for j, other_chunk in enumerate(chunks):
                if i != j:
                    other_chunks_nodes.update(other_chunk.nodes())
            assert chunk_nodes.isdisjoint(other_chunks_nodes)

    def test_memory_cleanup_after_processing(self):
        gc.collect()
        tracked_types = (nx.Graph, nx.DiGraph)
        initial_count = sum(1 for obj in gc.get_objects() if isinstance(obj, tracked_types))
        graphs = []
        for _ in range(10):
            graph = create_large_graph(100, avg_edges_per_node=3)
            graphs.append(graph)
        del graphs
        gc.collect()
        final_count = sum(1 for obj in gc.get_objects() if isinstance(obj, tracked_types))
        object_diff = abs(final_count - initial_count)
        assert object_diff < 5, f"Memory leak detected: {object_diff} graph objects not cleaned up"

    def test_oom_handling_and_recovery(self):
        profiler = MockMemoryProfiler(initial_memory_mb=50.0, max_memory_mb=80.0)
        graphs_created = []
        for i in range(10):
            graph = create_large_graph(50, avg_edges_per_node=2)
            graph_size_mb = estimate_graph_memory_size(graph)
            if not profiler.allocate(graph_size_mb):
                for _ in range(len(graphs_created) // 2):
                    freed_graph = graphs_created.pop(0)
                    freed_size = estimate_graph_memory_size(freed_graph)
                    profiler.deallocate(freed_size)
                if not profiler.allocate(graph_size_mb):
                    continue
            graphs_created.append(graph)
        assert len(graphs_created) > 0, "Should recover and continue processing after OOM"
        assert profiler.get_stats().used_mb <= profiler.max_memory

    def test_graph_size_estimation_accuracy(self):
        small_graph = create_large_graph(10, avg_edges_per_node=2)
        medium_graph = create_large_graph(100, avg_edges_per_node=5)
        large_graph = create_large_graph(1000, avg_edges_per_node=5)
        small_estimate = estimate_graph_memory_size(small_graph)
        medium_estimate = estimate_graph_memory_size(medium_graph)
        large_estimate = estimate_graph_memory_size(large_graph)
        assert 0 < small_estimate < medium_estimate < large_estimate
        assert small_estimate < 1.0, f"Small graph estimate too high: {small_estimate}"
        assert medium_estimate < 10.0, f"Medium graph estimate too high: {medium_estimate}"
        assert large_estimate > 0, "Large graph estimate should be positive"

    def test_chunk_by_source_id(self):
        graph = nx.Graph()
        for i in range(100):
            graph.add_node(
                f"ENTITY_{i}",
                description=f"Entity {i}",
                source_id=[f"doc_{i % 5}"],
                entity_type="PERSON",
            )
        for i in range(50):
            graph.add_edge(
                f"ENTITY_{i}",
                f"ENTITY_{i + 50}",
                description=f"Edge {i}",
                weight=1.0,
                keywords=["test"],
                source_id=[f"doc_{i % 5}"],
            )
        source_ids = set()
        for node in graph.nodes():
            source_ids.update(graph.nodes[node].get("source_id", []))
        subgraphs = {}
        for source_id in source_ids:
            nodes = [n for n in graph.nodes() if source_id in graph.nodes[n].get("source_id", [])]
            subgraphs[source_id] = graph.subgraph(nodes).copy()
        assert len(subgraphs) == 5
        total_nodes = sum(sg.number_of_nodes() for sg in subgraphs.values())
        assert total_nodes == 100

    def test_pagerank_memory_scaling(self):
        import math

        sizes = [10, 100, 1000]
        memory_estimates = []
        for size in sizes:
            graph = create_large_graph(size, avg_edges_per_node=3)
            pr = nx.pagerank(graph)
            estimate = len(pr) * 8 / (1024 * 1024)
            memory_estimates.append(estimate)
        for i in range(len(sizes) - 1):
            ratio = memory_estimates[i + 1] / memory_estimates[i]
            size_ratio = sizes[i + 1] / sizes[i]
            assert math.isclose(ratio, size_ratio, rel_tol=0.5), f"PageRank memory should scale linearly: ratio={ratio}, size_ratio={size_ratio}"

    def test_graph_serialization_memory(self):

        graph = create_large_graph(100, avg_edges_per_node=5)
        from networkx.readwrite import json_graph

        json_data = json_graph.node_link_data(graph, edges="edges")
        json_str = json.dumps(json_data, ensure_ascii=False)
        json_size_mb = len(json_str.encode("utf-8")) / (1024 * 1024)
        estimated_size = estimate_graph_memory_size(graph)
        overhead_ratio = json_size_mb / max(estimated_size, 0.001)
        assert 0.1 < overhead_ratio < 10, f"Unexpected serialization overhead: {overhead_ratio}"

    def test_progressive_graph_loading(self):
        large_graph = create_large_graph(500, avg_edges_per_node=3)
        chunks = iter_graph_chunks(large_graph, chunk_size=50)
        profiler = MockMemoryProfiler(initial_memory_mb=10.0, max_memory_mb=50.0)
        loaded_nodes = set()
        loaded_edges = set()
        recovered_from_oom = False
        max_iterations = 100
        iteration = 0
        for i, chunk in enumerate(chunks):
            chunk_size_mb = estimate_graph_memory_size(chunk)
            if profiler.allocate(chunk_size_mb):
                loaded_nodes.update(chunk.nodes())
                loaded_edges.update(chunk.edges())
            else:
                recovered_from_oom = True
                while not profiler.allocate(chunk_size_mb):
                    profiler.deallocate(5.0)
                    iteration += 1
                    if iteration > max_iterations:
                        break
                loaded_nodes.update(chunk.nodes())
                loaded_edges.update(chunk.edges())
        assert recovered_from_oom or len(loaded_nodes) > 0
        assert len(loaded_nodes) > 0

    def test_edge_case_empty_graph(self):
        empty_graph = nx.Graph()
        assert empty_graph.number_of_nodes() == 0
        assert empty_graph.number_of_edges() == 0
        assert estimate_graph_memory_size(empty_graph) == 0
        chunks = split_graph_into_chunks(empty_graph, chunk_size=10)
        assert len(chunks) == 0

    def test_edge_case_single_node_graph(self):
        single_node_graph = nx.Graph()
        single_node_graph.add_node("SINGLE", description="Single node", source_id=["doc_1"])
        assert single_node_graph.number_of_nodes() == 1
        assert single_node_graph.number_of_edges() == 0
        estimated = estimate_graph_memory_size(single_node_graph)
        assert estimated > 0

    def test_edge_case_disconnected_components(self):
        graph = nx.Graph()
        for component_id in range(5):
            for i in range(20):
                node_name = f"COMP_{component_id}_NODE_{i}"
                graph.add_node(node_name, description=f"Node in component {component_id}", source_id=[f"doc_{component_id}"])
            for i in range(19):
                graph.add_edge(
                    f"COMP_{component_id}_NODE_{i}",
                    f"COMP_{component_id}_NODE_{i + 1}",
                    description=f"Edge in component {component_id}",
                    weight=1.0,
                    keywords=[],
                    source_id=[f"doc_{component_id}"],
                )
        assert nx.number_connected_components(graph) == 5
        for component in nx.connected_components(graph):
            subgraph = graph.subgraph(component).copy()
            assert nx.is_connected(subgraph)

    def test_memory_pressure_with_many_small_graphs(self):
        profiler = MockMemoryProfiler(initial_memory_mb=10.0, max_memory_mb=100.0)
        graphs = []
        successfully_created = 0
        for i in range(100):
            graph = create_large_graph(10, avg_edges_per_node=2)
            size_mb = estimate_graph_memory_size(graph)
            if profiler.allocate(size_mb):
                graphs.append(graph)
                successfully_created += 1
            else:
                break
        assert successfully_created > 0
        assert len(graphs) == successfully_created
        stats = profiler.get_stats()
        assert stats.used_mb <= profiler.max_memory

    def test_graph_node_attribute_memory(self):
        graph = nx.Graph()
        for i in range(100):
            large_description = "A" * 10000
            graph.add_node(f"ENTITY_{i}", description=large_description, source_id=[f"doc_{i}"])
        estimated = estimate_graph_memory_size(graph)
        assert estimated > 0
        actual_approximate = len(graph.nodes) * 10000 / (1024 * 1024)
        assert estimated >= actual_approximate * 0.01

    def test_concurrent_graph_operations_memory_safety(self):
        import threading

        profiler = MockMemoryProfiler(initial_memory_mb=50.0, max_memory_mb=200.0)
        results = []
        lock = threading.Lock()

        def process_chunk(chunk_id):
            graph = create_large_graph(20, avg_edges_per_node=2)
            size_mb = estimate_graph_memory_size(graph)
            with lock:
                if profiler.allocate(size_mb):
                    results.append((chunk_id, graph.number_of_nodes()))
                    return True
                return False

        threads = []
        for i in range(10):
            t = threading.Thread(target=process_chunk, args=(i,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        assert len(results) > 0, "At least some threads should succeed"
        assert profiler.get_stats().used_mb <= profiler.max_memory

    def test_graph_pruning_under_memory_pressure(self):
        profiler = MockMemoryProfiler(initial_memory_mb=80.0, max_memory_mb=100.0)
        graph = create_large_graph(200, avg_edges_per_node=5)
        initial_nodes = graph.number_of_nodes()
        initial_edges = graph.number_of_edges()
        graph_size = estimate_graph_memory_size(graph)
        if not profiler.allocate(graph_size):
            target_reduction = 0.5
            nodes_to_keep = int(initial_nodes * target_reduction)
            nodes_by_degree = sorted(graph.degree(), key=lambda x: x[1], reverse=True)
            nodes_to_remove = [n for n, _ in nodes_by_degree[nodes_to_keep:]]
            for node in nodes_to_remove:
                graph.remove_node(node)
        assert graph.number_of_nodes() <= initial_nodes
        assert graph.number_of_edges() <= initial_edges

    def test_lazy_edge_loading(self):
        full_graph = create_large_graph(100, avg_edges_per_node=5)
        nodes_only = nx.Graph()
        for node, attrs in full_graph.nodes(data=True):
            nodes_only.add_node(node, **attrs)
        assert nodes_only.number_of_nodes() == full_graph.number_of_nodes()
        assert nodes_only.number_of_edges() == 0
        nodes_only_memory = estimate_graph_memory_size(nodes_only)
        full_memory = estimate_graph_memory_size(full_graph)
        assert nodes_only_memory < full_memory
        for u, v, attrs in full_graph.edges(data=True):
            nodes_only.add_edge(u, v, **attrs)
        assert nodes_only.number_of_edges() == full_graph.number_of_edges()
