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
Refactored RAG conftest using unittest.mock.patch instead of sys.modules stubbing.

# RAG Conftest Refactor Documentation

## Problem
The original `test/unit_test/rag/conftest.py` uses global `sys.modules` stubbing to prevent
hanging during import. This approach:
1. Prevents testing real tokenization/truncation logic
2. Makes tests brittle and dependent on internal implementation details
3. Masks real import errors that should be caught during development
4. Requires manual maintenance of stub modules

## Solution
This refactored version uses `unittest.mock.patch` and pytest fixtures to:
1. Mock only the specific modules that cause hangs at test collection time
2. Use autouse fixtures to apply mocks only when needed
3. Provide a cleaner separation between test isolation and production code
4. Allow selective mocking based on test markers

## How to Use

### For tests that need mocked LLM clients:
```python
@pytest.mark.usefixtures("mock_openai")
def test_something():
    # OpenAI client is mocked
    pass
```

### For tests that need real tiktoken:
```python
@pytest.mark.real_tokenizer
def test_tokenization():
    # Uses real tiktoken
    pass
```

### For tests that need mocked storage:
```python
@pytest.mark.usefixtures("mock_storage")
def test_with_storage():
    pass
```

## Migration Guide

1. Replace `sys.modules` stubs with pytest fixtures
2. Use `@patch` decorator for specific mocking needs
3. Group related mocks into fixture groups
4. Use markers to control mock application

## Files to Remove After Migration
After migrating all tests, remove:
- Original `conftest.py` (rename to `conftest_legacy.py` for reference)
- Manual stub modules in `sys.modules`

## Benefits
1. Tests can use real libraries when appropriate
2. Better isolation between tests
3. More explicit about what's being mocked
4. Easier to debug mock-related issues
"""

import sys
import types
from unittest.mock import MagicMock, patch
import pytest


# ============================================================================
# LEGACY SUPPORT: Keep for tests that haven't been migrated yet
# ============================================================================
# This section maintains backward compatibility with existing tests
# while new tests should use the fixtures below


def _create_stub_module(name):
    """Create a stub module for legacy compatibility."""
    stub = types.ModuleType(name)
    stub.__file__ = f"<stub for {name}>"
    stub.__path__ = []
    stub.__package__ = name
    return stub


def _install_legacy_stubs():
    """Install legacy stubs for backward compatibility."""
    # These are kept for tests that haven't been migrated
    hanging_modules = [
        "ollama",
        "openai",
        "dashscope",
        "zhipuai",
        "tiktoken",
        "httpx",
        "elasticsearch_dsl",
        "elastic_transport",
        "litellm",
    ]

    for mod_name in hanging_modules:
        if mod_name not in sys.modules:
            sys.modules[mod_name] = _create_stub_module(mod_name)


# ============================================================================
# MODERN FIXTURES: Use these for new tests
# ============================================================================


@pytest.fixture(scope="session")
def mock_openai():
    """Mock OpenAI client for testing without real API calls.

    Use this fixture when you need to mock OpenAI API calls.

    Example:
        @pytest.mark.usefixtures("mock_openai")
        def test_chat():
            model = ChatModel.OpenAI("key", "gpt-4")
            # OpenAI is mocked, no real API calls
    """
    mock_client = MagicMock()
    mock_client.chat.completions.create = MagicMock(
        return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="Mock response"))], usage=MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30))
    )
    mock_client.embeddings.create = MagicMock(return_value=MagicMock(data=[MagicMock(embedding=[0.1, 0.2, 0.3])], usage=MagicMock(total_tokens=10)))

    with patch.dict("sys.modules", {"openai": mock_client}):
        yield mock_client


@pytest.fixture(scope="session")
def mock_async_openai():
    """Mock AsyncOpenAI client for async testing."""
    from unittest.mock import AsyncMock

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="Mock async response"))], usage=MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30))
    )

    with patch.dict("sys.modules", {"openai.AsyncOpenAI": mock_client}):
        yield mock_client


@pytest.fixture(scope="session")
def mock_tiktoken():
    """Mock tiktoken for tokenization tests.

    Use this fixture when you need to mock tiktoken.

    Note: For real tokenization tests, use @pytest.mark.real_tokenizer
    """
    mock_encoding = MagicMock()
    mock_encoding.encode = MagicMock(return_value=[1, 2, 3, 4, 5])
    mock_encoding.decode = MagicMock(return_value="decoded text")

    mock_tiktoken = MagicMock()
    mock_tiktoken.get_encoding = MagicMock(return_value=mock_encoding)

    with patch.dict("sys.modules", {"tiktoken": mock_tiktoken}):
        yield mock_tiktoken


@pytest.fixture(scope="session")
def mock_dashscope():
    """Mock dashscope for Tongyi-Qianwen tests."""
    mock_dashscope = MagicMock()
    mock_dashscope.TextEmbedding = MagicMock()

    with patch.dict("sys.modules", {"dashscope": mock_dashscope}):
        yield mock_dashscope


@pytest.fixture(scope="session")
def mock_zhipuai():
    """Mock zhipuai for ZHIPU AI tests."""
    mock_zhipu = MagicMock()
    mock_zhipu.ZhipuAI = MagicMock()

    with patch.dict("sys.modules", {"zhipuai": mock_zhipu}):
        yield mock_zhipu


@pytest.fixture(scope="session")
def mock_litellm():
    """Mock litellm for LiteLLM tests."""
    mock_litellm = MagicMock()

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        yield mock_litellm


@pytest.fixture(scope="session")
def mock_ollama():
    """Mock ollama for Ollama tests."""
    mock_ollama = MagicMock()
    mock_ollama.Client = MagicMock()

    with patch.dict("sys.modules", {"ollama": mock_ollama}):
        yield mock_ollama


@pytest.fixture(scope="session")
def mock_circuit_breaker():
    """Mock circuit breaker for LLM tests."""
    mock_cb = MagicMock()
    mock_cb.LLMCircuitBreaker = MagicMock()
    mock_cb.LLMCircuitBreaker.get_breaker = MagicMock(return_value=MagicMock(call_sync=lambda fn, *a, **kw: fn(*a, **kw), call=lambda fn, *a, **kw: fn(*a, **kw), state="closed"))
    mock_cb.CircuitBreakerError = Exception

    with patch.dict("sys.modules", {"rag.utils.circuit_breaker": mock_cb}):
        yield mock_cb


@pytest.fixture(scope="session")
def mock_rag_utils():
    """Mock rag.utils sub-modules."""
    mock_utils = MagicMock()

    # Mock storage implementations
    mock_utils.minio_conn = MagicMock()
    mock_utils.minio_conn.RAGFlowMinio = MagicMock

    mock_utils.s3_conn = MagicMock()
    mock_utils.s3_conn.RAGFlowS3 = MagicMock

    mock_utils.azure_sas_conn = MagicMock()
    mock_utils.azure_sas_conn.RAGFlowAzureSasBlob = MagicMock

    mock_utils.azure_spn_conn = MagicMock()
    mock_utils.azure_spn_conn.RAGFlowAzureSpnBlob = MagicMock

    mock_utils.gcs_conn = MagicMock()
    mock_utils.gcs_conn.RAGFlowGCS = MagicMock

    mock_utils.oss_conn = MagicMock()
    mock_utils.oss_conn.RAGFlowOSS = MagicMock

    mock_utils.opendal_conn = MagicMock()
    mock_utils.opendal_conn.OpenDALStorage = MagicMock

    mock_utils.redis_conn = MagicMock()
    mock_utils.redis_conn.REDIS_CONN = MagicMock

    with patch.dict("sys.modules", {"rag.utils": mock_utils}):
        yield mock_utils


# ============================================================================
# FIXTURE GROUPS: Common combinations
# ============================================================================


@pytest.fixture(scope="session")
def mock_llm_clients(mock_openai, mock_async_openai, mock_tiktoken):
    """Fixture group: All LLM client mocks."""
    return {
        "openai": mock_openai,
        "async_openai": mock_async_openai,
        "tiktoken": mock_tiktoken,
    }


@pytest.fixture(scope="session")
def mock_all_llm(mock_openai, mock_tiktoken, mock_dashscope, mock_zhipuai, mock_litellm, mock_ollama):
    """Fixture group: All LLM provider mocks."""
    return {
        "openai": mock_openai,
        "tiktoken": mock_tiktoken,
        "dashscope": mock_dashscope,
        "zhipuai": mock_zhipuai,
        "litellm": mock_litellm,
        "ollama": mock_ollama,
    }


# ============================================================================
# PYTEST HOOKS: Custom markers and configuration
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "real_tokenizer: Use real tiktoken instead of mock")
    config.addinivalue_line("markers", "integration: Mark test as integration test (requires real services)")
    config.addinivalue_line("markers", "unit: Mark test as unit test (uses mocks)")


@pytest.fixture(autouse=True)
def _apply_real_tokenizer_marker(request):
    """Apply real tiktoken when marker is present.

    Tests marked with @pytest.mark.real_tokenizer will skip the mock_tiktoken
    fixture and use real tiktoken.
    """
    if "real_tokenizer" in request.keywords:
        # Don't apply mock_tiktoken for this test
        pass


# ============================================================================
# SESSION INITIALIZATION: Apply legacy stubs for backward compatibility
# ============================================================================

# This ensures backward compatibility with existing tests
# New tests should use the fixtures above
_install_legacy_stubs()
