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
Stub out problematic modules that hang during test collection.

Some dependencies have issues that cause them to hang during import.
This conftest pre-populates sys.modules with stub modules to prevent the hangs.
"""

import os
import sys
import types


def _create_stub_module(name, module_type="module"):
    """Create a stub module."""
    if module_type == "module":
        stub = types.ModuleType(name)
        stub.__file__ = f"<stub for {name}>"
        stub.__path__ = []
        stub.__package__ = name
        return stub
    return None


def _install_hanging_module_stubs():
    """Install stubs for modules that hang during import."""
    hanging_modules = [
        "ollama",
        "openai",
        "dashscope",
        "zhipuai",
        "tiktoken",
        "httpx",
        "elasticsearch_dsl",
        "elastic_transport",
    ]

    for mod_name in hanging_modules:
        if mod_name not in sys.modules:
            sys.modules[mod_name] = _create_stub_module(mod_name)

    # Stub classes for common imports
    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def embeddings(self, *args, **kwargs):
            return {}

    class OpenAI:
        def __init__(self, *args, **kwargs):
            pass

        class embeddings:
            @staticmethod
            def create(*args, **kwargs):
                class MockResponse:
                    def __init__(self):
                        self.data = [type("MockData", (), {"embedding": [0.1, 0.2, 0.3]})()]
                        self.usage = type("MockUsage", (), {"total_tokens": 10})()

                return MockResponse()

    class TextEmbedding:
        def __init__(self, *args, **kwargs):
            pass

    class ZhipuAI:
        def __init__(self, *args, **kwargs):
            pass

    class Tiktoken:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, *args, **kwargs):
            return [1, 2, 3]

    if "ollama" in sys.modules:
        sys.modules["ollama"].Client = Client
    if "openai" in sys.modules:
        sys.modules["openai"].OpenAI = OpenAI
        sys.modules["openai"]._version = type("MockVersion", (), {"__version__": "0.0.0"})()
    if "dashscope" in sys.modules:
        sys.modules["dashscope"].TextEmbedding = TextEmbedding
    if "zhipuai" in sys.modules:
        sys.modules["zhipuai"].ZhipuAI = ZhipuAI
    if "tiktoken" in sys.modules:
        sys.modules["tiktoken"].Tiktoken = Tiktoken
        sys.modules["tiktoken"].get_encoding = lambda *args, **kwargs: Tiktoken()


def _install_rag_utils_stub():
    """Create rag.utils stub that provides stub classes for all expected imports."""
    if "rag.utils" in sys.modules:
        return

    # Pre-create stubs for ALL rag.utils sub-modules to prevent import errors
    sub_modules = [
        "es_conn",
        "infinity_conn",
        "ob_conn",
        "opensearch_conn",
        "azure_sas_conn",
        "azure_spn_conn",
        "gcs_conn",
        "minio_conn",
        "opendal_conn",
        "redis_conn",
        "s3_conn",
        "oss_conn",
        "circuit_breaker",
    ]

    for sub_name in sub_modules:
        full_name = f"rag.utils.{sub_name}"
        if full_name not in sys.modules:
            stub = types.ModuleType(full_name)
            stub.__file__ = f"<stub for {full_name}>"
            stub.__path__ = []
            stub.__package__ = "rag.utils"
            sys.modules[full_name] = stub

    # Stub for circuit_breaker
    if "rag.utils.circuit_breaker" in sys.modules:

        class LLMCircuitBreaker:
            def __init__(self, *args, **kwargs):
                pass

            def call(self, fn, *args, **kwargs):
                return fn(*args, **kwargs)

            def is_open(self):
                return False

        class CircuitBreakerError(Exception):
            pass

        sys.modules["rag.utils.circuit_breaker"].LLMCircuitBreaker = LLMCircuitBreaker
        sys.modules["rag.utils.circuit_breaker"].CircuitBreakerError = CircuitBreakerError

    # For some modules, we need to provide stub classes

    # Stub for azure_sas_conn
    if "rag.utils.azure_sas_conn" in sys.modules:

        class RAGFlowAzureSasBlobStub:
            pass

        sys.modules["rag.utils.azure_sas_conn"].RAGFlowAzureSasBlob = RAGFlowAzureSasBlobStub

    # Stub for azure_spn_conn
    if "rag.utils.azure_spn_conn" in sys.modules:

        class RAGFlowAzureSpnBlobStub:
            pass

        sys.modules["rag.utils.azure_spn_conn"].RAGFlowAzureSpnBlob = RAGFlowAzureSpnBlobStub

    # Stub for gcs_conn
    if "rag.utils.gcs_conn" in sys.modules:

        class RAGFlowGCSStub:
            pass

        sys.modules["rag.utils.gcs_conn"].RAGFlowGCS = RAGFlowGCSStub

    # Stub for minio_conn
    if "rag.utils.minio_conn" in sys.modules:

        class RAGFlowMinioStub:
            pass

        sys.modules["rag.utils.minio_conn"].RAGFlowMinio = RAGFlowMinioStub

    # Stub for opendal_conn
    if "rag.utils.opendal_conn" in sys.modules:

        class OpenDALStorageStub:
            pass

        sys.modules["rag.utils.opendal_conn"].OpenDALStorage = OpenDALStorageStub

    # Stub for redis_conn (REDIS_CONN)
    if "rag.utils.redis_conn" in sys.modules:

        class REDIS_CONNStub:
            pass

        sys.modules["rag.utils.redis_conn"].REDIS_CONN = REDIS_CONNStub

    # Stub for s3_conn
    if "rag.utils.s3_conn" in sys.modules:

        class RAGFlowS3Stub:
            pass

        sys.modules["rag.utils.s3_conn"].RAGFlowS3 = RAGFlowS3Stub

    # Stub for oss_conn
    if "rag.utils.oss_conn" in sys.modules:

        class RAGFlowOSSStub:
            pass

        sys.modules["rag.utils.oss_conn"].RAGFlowOSS = RAGFlowOSSStub

    # Create a package-like stub for rag.utils itself
    rag_utils = types.ModuleType("rag.utils")
    rag_utils.__path__ = []
    rag_utils.__package__ = "rag.utils"
    sys.modules["rag.utils"] = rag_utils


def _install_memory_utils_stub():
    """Create memory.utils stub that provides stub modules."""
    if "memory.utils" in sys.modules:
        return

    # Pre-create stubs for memory.utils sub-modules
    sub_modules = [
        "memory.utils.es_conn",
        "memory.utils.infinity_conn",
        "memory.utils.ob_conn",
    ]
    for sub_name in sub_modules:
        if sub_name not in sys.modules:
            stub = types.ModuleType(sub_name)
            stub.__file__ = f"<stub for {sub_name}>"
            stub.__path__ = []
            stub.__package__ = "memory.utils"
            sys.modules[sub_name] = stub

    # Create a package-like stub for memory.utils itself
    memory_utils = types.ModuleType("memory.utils")
    memory_utils.__path__ = []
    memory_utils.__package__ = "memory.utils"
    sys.modules["memory.utils"] = memory_utils


def _install_rag_nlp_stub():
    """Stub out rag.nlp.search which is imported by settings."""
    if "rag.nlp" in sys.modules:
        return

    # Create rag.nlp package stub
    rag_nlp = types.ModuleType("rag.nlp")
    rag_nlp.__file__ = "<stub for rag.nlp>"
    rag_nlp.__path__ = []
    rag_nlp.__package__ = "rag.nlp"
    sys.modules["rag.nlp"] = rag_nlp

    # Create rag.nlp.search stub (needed by settings)
    rag_nlp_search = types.ModuleType("rag.nlp.search")
    rag_nlp_search.__file__ = "<stub for rag.nlp.search>"
    rag_nlp_search.__path__ = []
    rag_nlp_search.__package__ = "rag.nlp"

    # Provide stub classes/functions that are commonly used
    class rag_nlp_search_obj:
        @staticmethod
        def match_query(*args, **kwargs):
            return ""

        @staticmethod
        def query(*args, **kwargs):
            return ""

        @staticmethod
        def query_keywords(*args, **kwargs):
            return [], []

    rag_nlp_search.rag = rag_nlp_search_obj()
    sys.modules["rag.nlp.search"] = rag_nlp_search


def _install_rag_llm_stub():
    """Replace rag.llm with a minimal package stub if not yet loaded."""
    if "rag.llm" in sys.modules:
        return

    _RAGFLOW_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    _RAG_LLM_DIR = os.path.join(_RAGFLOW_ROOT, "rag", "llm")

    llm_pkg = types.ModuleType("rag.llm")
    llm_pkg.__path__ = [_RAG_LLM_DIR]
    llm_pkg.__package__ = "rag.llm"
    llm_pkg.EmbeddingModel = {}
    llm_pkg.ChatModel = {}
    llm_pkg.CvModel = {}
    llm_pkg.RerankModel = {}
    llm_pkg.Seq2txtModel = {}
    llm_pkg.TTSModel = {}
    llm_pkg.OcrModel = {}

    from strenum import StrEnum

    class SupportedLiteLLMProvider(StrEnum):
        OpenAI = "OpenAI"

    llm_pkg.SupportedLiteLLMProvider = SupportedLiteLLMProvider
    llm_pkg.FACTORY_DEFAULT_BASE_URL = {}
    llm_pkg.LITELLM_PROVIDER_PREFIX = {}
    llm_pkg.MODULE_MAPPING = {}
    llm_pkg.__all__ = [
        "ChatModel",
        "CvModel",
        "EmbeddingModel",
        "RerankModel",
        "Seq2txtModel",
        "TTSModel",
        "OcrModel",
    ]
    sys.modules["rag.llm"] = llm_pkg


_install_hanging_module_stubs()
_install_rag_utils_stub()
_install_memory_utils_stub()
_install_rag_nlp_stub()
_install_rag_llm_stub()
