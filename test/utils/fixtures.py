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
"""Shared pytest fixtures for testing."""

import os
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_env():
    """Fixture for isolated environment variables."""
    original_env = os.environ.copy()
    yield os.environ
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_embedding_response():
    """Fixture for mock embedding response."""
    from test.utils.llm_mocks import create_mock_embedding_response

    return create_mock_embedding_response()


@pytest.fixture
def mock_chat_response():
    """Fixture for mock chat response."""
    from test.utils.llm_mocks import create_mock_chat_response

    return create_mock_chat_response()


@pytest.fixture
def sample_texts():
    """Fixture providing sample text data."""
    return {
        "english": "The quick brown fox jumps over the lazy dog.",
        "chinese": "人工智能正在改变我们的生活方式。",
        "japanese": "機械学習はAIの重要な部分です。",
        "mixed": "Hello 世界！AI 人工智能 Machine Learning 机器学习。",
        "code": "def add(a, b):\n    return a + b\n",
        "long": "Sample text. " * 100,
        "empty": "",
        "whitespace": "   \n\t   ",
    }


@pytest.fixture
def sample_chunks():
    """Fixture providing sample chunk data."""
    return [
        {"text": "First chunk of content."},
        {"text": "Second chunk with more text."},
        {"text": "Third and final chunk."},
    ]


@pytest.fixture
def temp_text_file(tmp_path):
    """Fixture creating a temporary text file."""
    file_path = tmp_path / "test_input.txt"
    file_path.write_text("Test content for processing.")
    return file_path


@pytest.fixture
def temp_json_file(tmp_path):
    """Fixture creating a temporary JSON file."""
    import json

    file_path = tmp_path / "test_data.json"
    data = {"key": "value", "list": [1, 2, 3], "nested": {"a": "b"}}
    file_path.write_text(json.dumps(data))
    return file_path, data


@pytest.fixture
def mock_settings():
    """Fixture for mock settings."""
    settings = MagicMock()
    settings.STORAGE_IMPL = MagicMock()
    settings.STORAGE_IMPL.put = MagicMock(return_value="test_id")
    settings.STORAGE_IMPL.get = MagicMock(return_value=b"test_content")
    settings.PARAM_MAXDEPTH = 10
    settings.FLOAT_ZERO = 1e-6
    return settings


@pytest.fixture
def mock_storage():
    """Fixture for mock storage implementation."""
    storage = MagicMock()
    storage.put = MagicMock(return_value="stored_id")
    storage.get = MagicMock(return_value=b"file_content")
    storage.delete = MagicMock(return_value=True)
    storage.list = MagicMock(return_value=[])
    return storage


@pytest.fixture
def mock_database():
    """Fixture for mock database."""
    db = MagicMock()
    db.query = MagicMock(return_value=[])
    db.add = MagicMock(return_value=True)
    db.commit = MagicMock(return_value=True)
    db.rollback = MagicMock(return_value=True)
    return db


@pytest.fixture
def mock_redis():
    """Fixture for mock Redis."""
    redis = MagicMock()
    redis.get = MagicMock(return_value=None)
    redis.set = MagicMock(return_value=True)
    redis.delete = MagicMock(return_value=True)
    redis.exists = MagicMock(return_value=False)
    return redis


@pytest.fixture
def mock_es_client():
    """Fixture for mock Elasticsearch client."""
    es = MagicMock()
    es.search = MagicMock(return_value={"hits": {"hits": []}})
    es.index = MagicMock(return_value={"result": "created"})
    es.get = MagicMock(return_value={"found": False})
    es.delete = MagicMock(return_value={"result": "deleted"})
    return es


@pytest.fixture
def mock_tiktoken():
    """Fixture providing a mock tiktoken encoder.

    Use this fixture for tests that need deterministic token counts.
    For real tokenization testing, use @pytest.mark.real_tokenizer.
    """
    mock_encoding = MagicMock()
    mock_encoding.encode = MagicMock(return_value=[1, 2, 3, 4, 5])
    mock_encoding.decode = MagicMock(return_value="decoded text")
    mock_encoding.encode_batch = MagicMock(return_value=[[1, 2, 3], [4, 5, 6]])

    mock_tiktoken = MagicMock()
    mock_tiktoken.get_encoding = MagicMock(return_value=mock_encoding)

    return mock_tiktoken


@pytest.fixture
def mock_openai_client():
    """Fixture providing a mock OpenAI client.

    Use this fixture for tests that need mock API responses.
    """
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Mock response"))]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)

    mock_embedding = MagicMock()
    mock_embedding.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    mock_embedding.usage = MagicMock(total_tokens=10)
    mock_client.embeddings.create = MagicMock(return_value=mock_embedding)

    return mock_client


@pytest.fixture
def reset_circuit_breaker():
    """Fixture to reset circuit breaker state."""
    from rag.utils.circuit_breaker import LLMCircuitBreaker

    LLMCircuitBreaker.reset_all()
    yield
    LLMCircuitBreaker.reset_all()


@pytest.fixture
def mock_circuit_breaker():
    """Fixture for mock circuit breaker."""
    breaker = MagicMock()
    breaker.call_sync = MagicMock(side_effect=lambda fn, *a, **kw: fn(*a, **kw))
    breaker.call = MagicMock(side_effect=lambda fn, *a, **kw: fn(*a, **kw))
    breaker.state = "closed"
    return breaker
