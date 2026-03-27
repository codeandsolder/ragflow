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
"""Shared test assertions and validation utilities."""


def assert_response_success(response):
    """Assert that API response indicates success.

    Args:
        response: Response dict from API.

    Raises:
        AssertionError: If response code is not 0.
    """
    assert response.get("code", -1) == 0, f"Expected success, got: {response}"
    assert "data" in response, f"Missing 'data' in response: {response}"


def assert_response_error(response, expected_code=None, expected_message=None):
    """Assert that API response indicates an error.

    Args:
        response: Response dict from API.
        expected_code: Expected error code (optional).
        expected_message: Expected error message substring (optional).

    Raises:
        AssertionError: If response doesn't match expectations.
    """
    assert response.get("code", 0) != 0, f"Expected error, got success: {response}"

    if expected_code is not None:
        assert response.get("code") == expected_code, f"Expected code {expected_code}, got {response.get('code')}"

    if expected_message is not None:
        message = response.get("message", "")
        assert expected_message in message, f"Expected '{expected_message}' in '{message}'"


def assert_valid_embedding(embedding):
    """Assert that embedding is valid.

    Args:
        embedding: Embedding vector.

    Raises:
        AssertionError: If embedding is invalid.
    """
    import numpy as np

    assert embedding is not None, "Embedding should not be None"
    assert len(embedding) > 0, "Embedding should have non-zero length"

    if isinstance(embedding, np.ndarray):
        assert embedding.ndim == 1, f"Embedding should be 1D, got {embedding.ndim}D"
    else:
        assert isinstance(embedding, (list, tuple)), f"Embedding should be list/tuple/ndarray, got {type(embedding)}"


def assert_valid_embeddings(embeddings, expected_count=None):
    """Assert that embeddings list is valid.

    Args:
        embeddings: List of embedding vectors.
        expected_count: Expected number of embeddings (optional).

    Raises:
        AssertionError: If embeddings are invalid.
    """
    import numpy as np

    assert embeddings is not None, "Embeddings should not be None"
    assert len(embeddings) > 0, "Embeddings should not be empty"

    if expected_count is not None:
        assert len(embeddings) == expected_count, f"Expected {expected_count} embeddings, got {len(embeddings)}"

    if isinstance(embeddings, np.ndarray):
        assert embeddings.ndim == 2, f"Embeddings should be 2D, got {embeddings.ndim}D"

    for emb in embeddings:
        assert_valid_embedding(emb)


def assert_chunks_valid(chunks, min_count=1, max_count=None):
    """Assert that chunk list is valid.

    Args:
        chunks: List of chunks.
        min_count: Minimum expected chunks.
        max_count: Maximum expected chunks (optional).

    Raises:
        AssertionError: If chunks are invalid.
    """
    assert chunks is not None, "Chunks should not be None"
    assert len(chunks) >= min_count, f"Expected at least {min_count} chunks, got {len(chunks)}"

    if max_count is not None:
        assert len(chunks) <= max_count, f"Expected at most {max_count} chunks, got {len(chunks)}"

    for i, chunk in enumerate(chunks):
        assert "text" in chunk, f"Chunk {i} missing 'text' field"
        assert chunk["text"], f"Chunk {i} has empty text"


def assert_token_count_approx(actual, expected, tolerance=0.2):
    """Assert token count is approximately as expected.

    Args:
        actual: Actual token count.
        expected: Expected token count.
        tolerance: Tolerance as fraction (default: 0.2 = 20%).

    Raises:
        AssertionError: If token count is outside tolerance.
    """
    lower = expected * (1 - tolerance)
    upper = expected * (1 + tolerance)

    assert lower <= actual <= upper, f"Token count {actual} outside range [{lower:.0f}, {upper:.0f}]"


def assert_dict_contains(d, required_keys):
    """Assert dict contains required keys.

    Args:
        d: Dict to check.
        required_keys: Set/list of required keys.

    Raises:
        AssertionError: If any required key is missing.
    """
    missing = set(required_keys) - set(d.keys())
    assert not missing, f"Missing required keys: {missing}"


def assert_status_code(response, expected_code=200):
    """Assert HTTP status code.

    Args:
        response: Flask/Quart response object.
        expected_code: Expected status code.

    Raises:
        AssertionError: If status code doesn't match.
    """
    actual_code = getattr(response, "status_code", None)
    assert actual_code == expected_code, f"Expected status {expected_code}, got {actual_code}"


class ResponseAssertions:
    """Mixin class providing response assertions."""

    def assert_success(self, response):
        """Assert response is successful."""
        assert_response_success(response)

    def assert_error(self, response, code=None, message=None):
        """Assert response is an error."""
        assert_response_error(response, expected_code=code, expected_message=message)

    def assert_valid_embeddings(self, embeddings, count=None):
        """Assert embeddings are valid."""
        assert_valid_embeddings(embeddings, expected_count=count)


class ChunkAssertions:
    """Mixin class providing chunk-related assertions."""

    def assert_chunks_valid(self, chunks, min_count=1, max_count=None):
        """Assert chunks are valid."""
        assert_chunks_valid(chunks, min_count=min_count, max_count=max_count)

    def assert_token_count_approx(self, actual, expected, tolerance=0.2):
        """Assert token count is approximate."""
        assert_token_count_approx(actual, expected, tolerance=tolerance)
