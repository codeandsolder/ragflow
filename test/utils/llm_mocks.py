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
"""Shared test utilities for LLM mocking."""

from unittest.mock import MagicMock, patch


def create_mock_embedding_response(embeddings=None, total_tokens=10):
    """Create a mock embedding response.

    Args:
        embeddings: List of embedding vectors. Default: [[0.1, 0.2, 0.3]]
        total_tokens: Total tokens used.

    Returns:
        Mock response object.
    """
    if embeddings is None:
        embeddings = [[0.1, 0.2, 0.3]]

    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=emb) for emb in embeddings]
    mock_response.usage = MagicMock(total_tokens=total_tokens)
    return mock_response


def create_mock_chat_response(content="Test response", model="gpt-4"):
    """Create a mock chat completion response.

    Args:
        content: Response content.
        model: Model name.

    Returns:
        Mock response object.
    """
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    mock_response.choices[0].message.model = model
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    return mock_response


def create_mock_stream_chunk(content="Chunk text", delta_content=None):
    """Create a mock streaming chunk.

    Args:
        content: Full content or delta.
        delta_content: Delta content for streaming (if None, uses content).

    Returns:
        Mock chunk object.
    """
    mock_chunk = MagicMock()
    if delta_content is not None:
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = delta_content
        mock_chunk.choices[0].delta.role = "assistant"
    else:
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].message.content = content
        mock_chunk.choices[0].message.role = "assistant"
    return mock_chunk


def patch_llm_client(client_name, mock_response=None):
    """Create a patcher for LLM client.

    Args:
        client_name: Client module path (e.g., 'rag.llm.chat_model.OpenAI')
        mock_response: Response to return. Default: create_mock_chat_response()

    Returns:
        Context manager for patching.
    """
    if mock_response is None:
        mock_response = create_mock_chat_response()

    return patch(client_name, return_value=MagicMock(**{"chat.completions.create.return_value": mock_response}))


def patch_embedding_client(client_name, mock_response=None):
    """Create a patcher for embedding client.

    Args:
        client_name: Client module path (e.g., 'rag.llm.embedding_model.OpenAI')
        mock_response: Response to return. Default: create_mock_embedding_response()

    Returns:
        Context manager for patching.
    """
    if mock_response is None:
        mock_response = create_mock_embedding_response()

    return patch(client_name, return_value=MagicMock(**{"embeddings.create.return_value": mock_response}))


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, response_content="Mock response", embeddings=None):
        self.response_content = response_content
        self.embeddings = embeddings or [0.1, 0.2, 0.3]
        self.call_count = 0

    def chat_completions_create(self, *args, **kwargs):
        """Mock chat.completions.create."""
        self.call_count += 1
        return create_mock_chat_response(self.response_content)

    def embeddings_create(self, *args, **kwargs):
        """Mock embeddings.create."""
        self.call_count += 1
        return create_mock_embedding_response([self.embeddings])

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class AsyncMockLLMClient:
    """Async mock LLM client for testing."""

    def __init__(self, response_content="Mock response", embeddings=None):
        self.response_content = response_content
        self.embeddings = embeddings or [0.1, 0.2, 0.3]
        self.call_count = 0

    async def chat_completions_create(self, *args, **kwargs):
        """Mock async chat.completions.create."""
        self.call_count += 1
        return create_mock_chat_response(self.response_content)

    async def embeddings_create(self, *args, **kwargs):
        """Mock async embeddings.create."""
        self.call_count += 1
        return create_mock_embedding_response([self.embeddings])

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def create_failing_llm_client(failure_exception, fail_after_n_calls=1):
    """Create a client that fails after N calls.

    Args:
        failure_exception: Exception to raise.
        fail_after_n_calls: Number of successful calls before failing.

    Returns:
        Mock client class.
    """

    class FailingClient:
        def __init__(self, *args, **kwargs):
            self.call_count = 0

        def chat_completions_create(self, *args, **kwargs):
            self.call_count += 1
            if self.call_count > fail_after_n_calls:
                raise failure_exception
            return create_mock_chat_response("Success before failure")

    return FailingClient
