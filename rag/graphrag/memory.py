# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Memory-efficient graph processing utilities.

Provides memory monitoring and streaming/pagination for large graphs
to prevent OOM issues.
"""

import logging
import os
from typing import Iterator

import networkx as nx

DEFAULT_MAX_NODES = int(os.environ.get("GRAPH_MAX_NODES", 100000))
DEFAULT_MAX_EDGES = int(os.environ.get("GRAPH_MAX_EDGES", 500000))
DEFAULT_MAX_MEMORY_MB = int(os.environ.get("GRAPH_MAX_MEMORY_MB", 2048))
DEFAULT_CHUNK_SIZE = int(os.environ.get("GRAPH_CHUNK_SIZE", 5000))


class GraphMemoryMonitor:
    """Monitor memory usage for graph operations."""

    def __init__(
        self,
        max_nodes: int = DEFAULT_MAX_NODES,
        max_edges: int = DEFAULT_MAX_EDGES,
        max_memory_mb: int = DEFAULT_MAX_MEMORY_MB,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        self.max_nodes = max_nodes
        self.max_edges = max_edges
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size

    def estimate_graph_memory_mb(self, graph: nx.Graph) -> float:
        """Estimate memory usage of a graph in MB."""
        if graph.number_of_nodes() == 0:
            return 0.0
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()

        avg_node_attrs = sum(len(attrs) for _, attrs in graph.nodes(data=True)) / max(node_count, 1)
        avg_edge_attrs = sum(len(attrs) for _, _, attrs in graph.edges(data=True)) / max(edge_count, 1)
        bytes_per_attr = 100

        node_memory = node_count * avg_node_attrs * bytes_per_attr
        edge_memory = edge_count * avg_edge_attrs * bytes_per_attr
        overhead_factor = 1.5

        return (node_memory + edge_memory) * overhead_factor / (1024 * 1024)

    def check_memory_limits(self, graph: nx.Graph) -> tuple[bool, str]:
        """Check if graph exceeds memory limits. Returns (is_safe, message)."""
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()

        if node_count > self.max_nodes:
            return False, f"Graph has {node_count} nodes, exceeds limit of {self.max_nodes}"

        if edge_count > self.max_edges:
            return False, f"Graph has {edge_count} edges, exceeds limit of {self.max_edges}"

        estimated_memory = self.estimate_graph_memory_mb(graph)
        if estimated_memory > self.max_memory_mb:
            return False, f"Graph estimated memory {estimated_memory:.1f}MB exceeds limit of {self.max_memory_mb}MB"

        return True, "OK"

    def should_stream(self, graph: nx.Graph) -> bool:
        """Determine if graph should be processed in streaming mode."""
        return graph.number_of_nodes() > self.chunk_size or graph.number_of_edges() > self.chunk_size * 5

    def get_current_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1]) / 1024
        except Exception:
            pass
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            pass
        return 0.0

    def is_memory_pressure(self, threshold_percent: float = 80.0) -> bool:
        """Check if system is under memory pressure."""
        try:
            import psutil

            return psutil.virtual_memory().percent > threshold_percent
        except ImportError:
            pass
        return False


def iter_graph_nodes(graph: nx.Graph, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Iterator[list[str]]:
    """Iterate over graph nodes in chunks."""
    nodes = list(graph.nodes())
    for i in range(0, len(nodes), chunk_size):
        yield nodes[i : i + chunk_size]


def iter_graph_chunks(
    graph: nx.Graph,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Iterator[nx.Graph]:
    """Iterate over graph as subgraphs in chunks."""
    for node_chunk in iter_graph_nodes(graph, chunk_size):
        yield graph.subgraph(node_chunk).copy()


def iter_subgraphs_by_source(
    graph: nx.Graph,
    filter_doc_ids: set[str] | None = None,
) -> Iterator[tuple[str, nx.Graph]]:
    """Iterate over subgraphs grouped by source_id.

    Args:
        graph: The graph to iterate over
        filter_doc_ids: Optional set of document IDs to filter. If provided, only
                       subgraphs for these documents will be yielded. This enables
                       O(N) incremental updates instead of O(N²) full re-indexing.

    Yields:
        Tuples of (source_id, subgraph) for each document's subgraph.
    """
    source_to_nodes: dict[str, list[str]] = {}
    for node, attrs in graph.nodes(data=True):
        node_source_ids = attrs.get("source_id", [])
        for src_id in node_source_ids:
            if src_id not in source_to_nodes:
                source_to_nodes[src_id] = []
            source_to_nodes[src_id].append(node)

    for source_id, nodes in source_to_nodes.items():
        if filter_doc_ids is not None and source_id not in filter_doc_ids:
            continue
        if nodes:
            subgraph = graph.subgraph(nodes).copy()
            subgraph.graph["source_id"] = [source_id]
            for n in subgraph.nodes:
                subgraph.nodes[n]["source_id"] = [source_id]
            yield source_id, subgraph


def iter_connected_components(
    graph: nx.Graph,
    max_component_size: int = DEFAULT_CHUNK_SIZE,
) -> Iterator[nx.Graph]:
    """Iterate over connected components, splitting large ones."""
    for component in nx.connected_components(graph):
        subgraph = graph.subgraph(component).copy()
        if subgraph.number_of_nodes() <= max_component_size:
            yield subgraph
        else:
            for chunk in iter_graph_chunks(subgraph, max_component_size):
                yield chunk


def stream_pagerank(
    graph: nx.Graph,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    monitor: GraphMemoryMonitor | None = None,
) -> dict[str, float]:
    """Compute PageRank in a memory-efficient manner for large graphs."""
    if monitor is None:
        monitor = GraphMemoryMonitor()

    is_safe, msg = monitor.check_memory_limits(graph)
    if is_safe:
        return nx.pagerank(graph)

    logging.warning(f"Graph exceeds limits, using streaming PageRank: {msg}")
    all_pageranks = {}

    for i, subgraph in enumerate(iter_connected_components(graph, chunk_size)):
        if subgraph.number_of_nodes() == 0:
            continue

        chunk_ranks = nx.pagerank(subgraph, alpha=0.85)
        all_pageranks.update(chunk_ranks)

        del chunk_ranks
        if monitor.is_memory_pressure():
            logging.warning("Memory pressure detected during PageRank computation")

    return all_pageranks


def stream_node_iteration(
    graph: nx.Graph,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    callback=None,
) -> Iterator[tuple[str, dict]]:
    """Iterate over nodes in a memory-efficient manner."""
    for i, node_chunk in enumerate(iter_graph_nodes(graph, chunk_size)):
        for node in node_chunk:
            yield node, graph.nodes[node]
        if callback and i % 10 == 0:
            callback(msg=f"Processed {i * chunk_size}/{graph.number_of_nodes()} nodes")


def stream_edge_iteration(
    graph: nx.Graph,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    callback=None,
) -> Iterator[tuple[str, str, dict]]:
    """Iterate over edges in a memory-efficient manner."""
    edges = list(graph.edges(data=True))
    for i in range(0, len(edges), chunk_size):
        for edge in edges[i : i + chunk_size]:
            yield edge[0], edge[1], edge[2]
        if callback and i % (chunk_size * 10) == 0:
            callback(msg=f"Processed {i}/{len(edges)} edges")


def merge_graphs_streaming(
    graphs: Iterator[nx.Graph],
    monitor: GraphMemoryMonitor | None = None,
) -> nx.Graph | None:
    """Merge multiple graphs in a streaming manner to reduce peak memory."""
    if monitor is None:
        monitor = GraphMemoryMonitor()

    result = None
    for i, graph in enumerate(graphs):
        if graph.number_of_nodes() == 0:
            continue

        is_safe, msg = monitor.check_memory_limits(graph)
        if not is_safe:
            logging.warning(f"Graph chunk {i} exceeds memory limits: {msg}")

        if result is None:
            result = graph
        else:
            result = nx.compose(result, graph)
            merged_source = {n: result.nodes[n]["source_id"] + graph.nodes[n]["source_id"] for n in result.nodes & graph.nodes}
            if merged_source:
                nx.set_node_attributes(result, merged_source, "source_id")

    return result


def truncate_graph(
    graph: nx.Graph,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_edges: int = DEFAULT_MAX_EDGES,
    preserve_high_degree: bool = True,
) -> nx.Graph:
    """Truncate graph to fit within memory limits."""
    if graph.number_of_nodes() <= max_nodes and graph.number_of_edges() <= max_edges:
        return graph

    truncated = graph.copy()

    if preserve_high_degree:
        nodes_by_degree = sorted(truncated.degree(), key=lambda x: x[1], reverse=True)
        nodes_to_keep = set(n for n, _ in nodes_by_degree[:max_nodes])
    else:
        nodes_to_keep = set(list(truncated.nodes())[:max_nodes])

    nodes_to_remove = set(truncated.nodes()) - nodes_to_keep
    for node in nodes_to_remove:
        truncated.remove_node(node)

    edges_to_remove = [(u, v) for u, v in truncated.edges() if u not in nodes_to_keep or v not in nodes_to_keep]
    for u, v in edges_to_remove:
        try:
            truncated.remove_edge(u, v)
        except nx.NetworkXError:
            pass

    if truncated.number_of_edges() > max_edges:
        edges_to_keep = list(truncated.edges(data=True))[:max_edges]
        truncated = nx.Graph()
        for u, v, attrs in edges_to_keep:
            truncated.add_edge(u, v, **attrs)
            if u in graph.nodes:
                truncated.nodes[u].update(graph.nodes[u])
            if v in graph.nodes:
                truncated.nodes[v].update(graph.nodes[v])
        truncated.graph["source_id"] = graph.graph.get("source_id", [])

    return truncated
