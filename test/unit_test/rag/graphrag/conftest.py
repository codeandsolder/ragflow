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
Fixtures for graphrag unit tests.
"""

import sys
from unittest.mock import MagicMock

import pytest


class MockGraph:
    """Minimal mock for networkx.Graph that provides the required interface."""

    def __init__(self, incoming_graph_data=None, **attr):
        self.graph = attr or {}
        self._node = {}
        self._adj = {}
        if incoming_graph_data:
            for node in incoming_graph_data.get("nodes", []):
                self.add_node(node.get("id", node.get("name", node.get("id"))))
            for edge in incoming_graph_data.get("edges", incoming_graph_data.get("links", [])):
                src = edge.get("source", edge.get("src"))
                tgt = edge.get("target", edge.get("tgt"))
                if src and tgt:
                    self.add_edge(src, tgt)

    def add_node(self, node_for_adding, **attr):
        self._node[node_for_adding] = attr

    def add_edge(self, u, v, **attr):
        if u not in self._adj:
            self._adj[u] = {}
        if v not in self._adj:
            self._adj[v] = {}
        self._adj[u][v] = attr

    def nodes(self, data=False):
        if data:
            return [(n, self._node.get(n, {})) for n in self._node]
        return list(self._node)

    def edges(self, data=False):
        result = []
        for u in self._adj:
            for v in self._adj[u]:
                if data:
                    result.append((u, v, self._adj[u][v]))
                else:
                    result.append((u, v))
        return result

    def number_of_nodes(self):
        return len(self._node)

    def number_of_edges(self):
        return sum(len(v) for v in self._adj.values())

    def has_node(self, n):
        return n in self._node

    def has_edge(self, u, v):
        return v in self._adj.get(u, {})

    def subgraph(self, nodes):
        g = MockGraph()
        for n in nodes:
            if n in self._node:
                g._node[n] = dict(self._node[n])
        return g

    def copy(self):
        g = MockGraph()
        g._node = dict(self._node)
        g._adj = {k: dict(v) for k, v in self._adj.items()}
        g.graph = dict(self.graph)
        return g

    def is_directed(self):
        return False

    def subgraph(self, nodes):
        g = MockGraph()
        for n in nodes:
            if n in self._node:
                g._node[n] = dict(self._node[n])
        for u in self._adj:
            for v in self._adj[u]:
                if u in nodes and v in nodes:
                    if u not in g._adj:
                        g._adj[u] = {}
                    g._adj[u][v] = dict(self._adj[u][v])
        return g

    def to_directed(self):
        return self.copy()

    def to_undirected(self):
        return self.copy()


def _setup_networkx_mock():
    """Setup networkx mock if not already available."""
    if "networkx" not in sys.modules:
        sys.modules["networkx"] = MagicMock()

    nx_module = sys.modules["networkx"]

    if not hasattr(nx_module, "Graph") or not callable(getattr(nx_module.Graph, "add_node", None)):
        nx_module.Graph = MockGraph

    for submod in ["networkx.readwrite", "networkx.readwrite.json_graph"]:
        if submod not in sys.modules:
            sys.modules[submod] = MagicMock()

    return nx_module


def _check_import(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except (ImportError, SyntaxError):
        return False


def pytest_configure(config):
    """Configure pytest with networkx mock."""
    _setup_networkx_mock()


skipif_no_quart = pytest.mark.skipif(not _check_import("quart"), reason="quart not installed")

skipif_no_redis = pytest.mark.skipif(not _check_import("redis"), reason="redis not installed")

skipif_no_elasticsearch = pytest.mark.skipif(not _check_import("elasticsearch"), reason="elasticsearch not installed")
