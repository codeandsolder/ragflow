import asyncio
import collections
import sys
import types
from unittest.mock import MagicMock


class MockGraph:
    """Minimal mock for networkx.Graph that provides the required interface."""

    def __init__(self, incoming_graph_data=None, **attr):
        self.graph = attr or {}
        self._node = {}
        self._adj = {}
        if incoming_graph_data:
            for node in incoming_graph_data.get("nodes", []):
                self.add_node(node.get("id", node.get("name")))
            for edge in incoming_graph_data.get("edges", incoming_graph_data.get("links", [])):
                src = edge.get("source", edge.get("src"))
                tgt = edge.get("target", edge.get("tgt"))
                if src and tgt:
                    self.add_edge(src, tgt)

    def add_node(self, node_for_adding, **attr):
        self._node[node_for_adding] = attr

    def add_edge(self, edge_for_adding, **attr):
        u, v = edge_for_adding if isinstance(edge_for_adding, tuple) else (edge_for_adding, None)
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
                g._node[n] = self._node[n]
        return g

    def copy(self):
        g = MockGraph()
        g._node = dict(self._node)
        g._adj = {k: dict(v) for k, v in self._adj.items()}
        g.graph = dict(self.graph)
        return g


def _get_or_create_mock_module(module_name: str):
    """Get existing module or create a minimal mock."""
    if module_name in sys.modules:
        return sys.modules[module_name]
    mock = MagicMock()
    sys.modules[module_name] = mock
    return mock


networkx_mock = _get_or_create_mock_module("networkx")
if not hasattr(networkx_mock, "Graph") or not callable(getattr(networkx_mock.Graph, "add_node", None)):
    networkx_mock.Graph = MockGraph

_get_or_create_mock_module("networkx.readwrite")
_get_or_create_mock_module("networkx.readwrite.json_graph")

for mod_name in [
    "numpy",
    "xxhash",
    "json_repair",
    "markdown_to_json",
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
    "api",
    "api.db",
    "api.db.services",
    "api.db.services.task_service",
]:
    _get_or_create_mock_module(mod_name)

sys.modules["common.connection_utils"].timeout = lambda *a, **kw: lambda fn: fn
sys.modules["api.db.services.task_service"].has_canceled = lambda *args, **kwargs: False

import rag.graphrag.general.extractor as extractor_module
import rag.graphrag.general.mind_map_extractor as mind_map_extractor_module
from rag.graphrag.general.mind_map_extractor import MindMapExtractor


class FakeLLM:
    llm_name = "fake-llm"
    max_length = 4096

    async def async_chat(self, system, history: list[dict[str, str]], gen_conf=None, **kwargs):
        return "{}"


class TupleLLM:
    llm_name = "tuple-llm"
    max_length = 4096

    async def async_chat(self, system, history: list[dict[str, str]], gen_conf=None, **kwargs):
        return "{}", 0


def test_mind_map_extractor_accepts_protocol_based_llm():
    extractor = MindMapExtractor(FakeLLM())

    assert extractor._llm.llm_name == "fake-llm"
    assert extractor._llm.max_length == 4096


def test_mind_map_extractor_accepts_tuple_chat_response(monkeypatch):
    extractor = MindMapExtractor(TupleLLM())
    monkeypatch.setattr(extractor_module, "get_llm_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(extractor_module, "set_llm_cache", lambda *args, **kwargs: None)

    assert extractor._chat("system", [{"role": "user", "content": "Output:"}], {}) == "{}"


def test_mind_map_extractor_todict_supports_list_leaves():
    extractor = MindMapExtractor(FakeLLM())
    layer = collections.OrderedDict(
        {
            "顶层": collections.OrderedDict(
                {
                    "部分A": [
                        "点1",
                        "点2",
                    ]
                }
            )
        }
    )

    assert extractor._todict(layer) == {"顶层": {"部分A": ["点1", "点2"]}}


def test_mind_map_extractor_be_children_supports_list_leaves():
    extractor = MindMapExtractor(FakeLLM())

    assert extractor._be_children(["点1", "点2"], {"顶层"}) == [
        {"id": "点1", "children": []},
        {"id": "点2", "children": []},
    ]


def test_mind_map_extractor_process_document_returns_none(monkeypatch):
    extractor = MindMapExtractor(FakeLLM())
    out_res = []

    async def fake_thread_pool_exec(*args, **kwargs):
        return "# 顶层\n## 部分A\n- 点1\n- 点2"

    monkeypatch.setattr(mind_map_extractor_module, "thread_pool_exec", fake_thread_pool_exec)
    monkeypatch.setattr(mind_map_extractor_module, "markdown_to_json", types.SimpleNamespace(dictify=lambda x: collections.OrderedDict({"顶层": {"部分A": ["点1", "点2"]}})))

    result = asyncio.run(extractor._process_document("课堂纪要", {}, out_res))

    assert result is None
    assert out_res == [{"顶层": {"部分A": ["点1", "点2"]}}]
