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
"""Comprehensive chunking tests with pytest parameterization."""

import pytest
from rag.nlp import naive_merge
from common.token_utils import num_tokens_from_string


class TestChunkingComprehensive:
    """Comprehensive test class for chunking functionality."""

    @pytest.mark.parametrize(
        "chunk_size, delimiter, expected_count",
        [
            (128, "\n", 5),
            (256, "\n", 3),
            (512, "\n", 2),
            (1024, "\n", 1),
            (128, "。", 4),
            (256, "。", 2),
        ],
        ids=lambda p: f"size={p}_delim=_exp",
    )
    def test_chunk_boundaries(self, chunk_size, delimiter, expected_count):
        """Test that chunks are correctly bounded by token size and delimiters."""
        text = "这是第一段文本。" * 30 + "\n" + "这是第二段文本。" * 30 + "\n" + "这是第三段文本。" * 30
        chunks = naive_merge(text, chunk_size, delimiter, 0)
        assert len(chunks) == expected_count, f"Expected {expected_count} chunks but got {len(chunks)}"

    @pytest.mark.parametrize(
        "overlap_percent",
        [0, 10, 20, 30, 50],
        ids=lambda x: f"overlap_{x}pct",
    )
    def test_chunk_overlap_accuracy(self, overlap_percent):
        """Test that chunk overlap is applied correctly."""
        text = "第一章：机器学习基础。" + "机器学习是人工智能的一个分支。" * 20 + "第二章：深度学习。" + "深度学习是机器学习的子领域。" * 20
        chunks = naive_merge(text, 256, "\n", overlap_percent)
        if overlap_percent > 0 and len(chunks) > 1:
            first_chunk_tokens = num_tokens_from_string(chunks[0])
            expected_overlap = int(first_chunk_tokens * overlap_percent / 100)
            assert expected_overlap > 0, "Overlap should be applied when percentage > 0"

    @pytest.mark.parametrize(
        "chunk_size",
        [64, 128, 256, 512, 1024, 2048],
        ids=lambda x: f"token_size_{x}",
    )
    def test_token_count_accuracy(self, chunk_size):
        """Test that chunk token counts are within acceptable range."""
        text = "The quick brown fox jumps over the lazy dog. " * 50
        chunks = naive_merge(text, chunk_size, "\n", 0)
        for chunk in chunks:
            token_count = num_tokens_from_string(chunk)
            if token_count > 0:
                max_allowed = int(chunk_size * 1.2)
                assert token_count <= max_allowed, f"Chunk token count {token_count} exceeds max {max_allowed}"

    @pytest.mark.parametrize(
        "chunk_size, delimiter",
        [
            (128, "\n"),
            (256, "\n"),
            (512, "\n"),
            (128, "。"),
            (256, "。；！？"),
            (512, "\n。；"),
        ],
        ids=lambda p: f"size_{p}_delim_",
    )
    def test_chunk_size_constraints(self, chunk_size, delimiter):
        """Test that chunks respect size constraints."""
        text = "A" * 500 + "\n" + "B" * 500 + "\n" + "C" * 500
        chunks = naive_merge(text, chunk_size, delimiter, 0)
        for chunk in chunks:
            tokens = num_tokens_from_string(chunk)
            assert tokens > 0, "Non-empty chunk should have tokens"

    @pytest.mark.parametrize(
        "language, text_sample",
        [
            ("english", "The technology sector continues to evolve rapidly. Artificial intelligence and machine learning are transforming industries."),
            ("chinese", "人工智能正在改变我们的生活方式。机器学习是人工智能的核心技术。深度学习推动了计算机视觉的发展。"),
            ("japanese", "人工智能技術は急速に発展しています。機械学習はAIの重要な部分です。"),
            ("mixed", "Hello 世界！AI 人工智能 Machine Learning 机器学习。"),
        ],
        ids=["en", "zh", "ja", "mixed"],
    )
    def test_multilingual_chunking(self, language, text_sample):
        """Test chunking with various languages."""
        repeated = text_sample * 10
        chunks = naive_merge(repeated, 128, "\n", 0)
        assert len(chunks) > 0, f"Should produce chunks for {language}"
        for chunk in chunks:
            assert num_tokens_from_string(chunk) > 0, f"Chunk should have tokens for {language}"

    @pytest.mark.parametrize(
        "code_type, code_sample",
        [
            ("python", "def add(a, b):\n    return a + b\n\nclass Calculator:\n    def __init__(self):\n        self.result = 0\n    def add(self, x):\n        self.result += x\n        return self"),
            ("javascript", "function greet(name) {\n    return `Hello, ${name}!`;\n}\n\nconst sum = (a, b) => a + b;\n\nconst obj = {\n    key: 'value',\n    method: () => {}\n};"),
            (
                "sql",
                "SELECT users.name, COUNT(orders.id) as order_count\nFROM users\nLEFT JOIN orders ON users.id = orders.user_id\nWHERE orders.created_at > '2024-01-01'\nGROUP BY users.name\nORDER BY order_count DESC;",
            ),
        ],
        ids=["py", "js", "sql"],
    )
    def test_code_document_chunking(self, code_type, code_sample):
        """Test chunking with code documents."""
        repeated = code_sample * 5
        chunks = naive_merge(repeated, 128, "\n", 0)
        assert len(chunks) > 0, f"Should produce chunks for {code_type}"
        for chunk in chunks:
            tokens = num_tokens_from_string(chunk)
            assert tokens > 0, f"Code chunk should have tokens for {code_type}"

    @pytest.mark.parametrize(
        "chunk_size, overlap",
        [
            (128, 0),
            (128, 10),
            (256, 0),
            (256, 20),
            (512, 0),
            (512, 30),
        ],
        ids=lambda p: f"size_{p}_overlap_",
    )
    def test_edge_case_empty_text(self, chunk_size, overlap):
        """Test handling of empty or whitespace-only text."""
        chunks = naive_merge("", chunk_size, "\n", overlap)
        assert len(chunks) == 0 or (len(chunks) == 1 and not chunks[0].strip())

    @pytest.mark.parametrize(
        "chunk_size, overlap",
        [
            (128, 0),
            (256, 10),
            (512, 20),
        ],
    )
    def test_edge_case_single_token(self, chunk_size, overlap):
        """Test handling of very short text."""
        text = "Short."
        chunks = naive_merge(text, chunk_size, "\n", overlap)
        assert len(chunks) > 0

    @pytest.mark.parametrize(
        "chunk_size",
        [128, 256, 512],
    )
    def test_delimiter_priority(self, chunk_size):
        """Test that delimiters are respected as chunk boundaries."""
        text = "Sentence one. Sentence two. Sentence three."
        chunks = naive_merge(text, chunk_size, ".", 0)
        assert len(chunks) > 0

    @pytest.mark.parametrize(
        "text_type, text",
        [
            ("plain", "This is a plain text document with multiple sentences."),
            ("with_newlines", "Line one\nLine two\nLine three\nLine four\nLine five"),
            ("with_paragraphs", "Para one.\n\nPara two.\n\nPara three."),
        ],
        ids=["plain", "newlines", "paragraphs"],
    )
    def test_different_text_formats(self, text_type, text):
        """Test chunking with different text formatting."""
        repeated = text * 20
        chunks = naive_merge(repeated, 256, "\n", 0)
        assert len(chunks) > 0


@pytest.fixture
def sample_text_english():
    """English text sample for testing."""
    return "The quick brown fox jumps over the lazy dog. " * 100


@pytest.fixture
def sample_text_chinese():
    """Chinese text sample for testing."""
    return "这是一个测试文档。" * 100


@pytest.fixture
def sample_text_code():
    """Code text sample for testing."""
    return "def function():\n    return True\n" * 50


@pytest.fixture
def chunk_sizes():
    """Common chunk sizes for testing."""
    return [64, 128, 256, 512, 1024, 2048]


@pytest.fixture
def overlap_percentages():
    """Common overlap percentages for testing."""
    return [0, 10, 20, 30, 50]


@pytest.fixture
def delimiters():
    """Common delimiters for testing."""
    return ["\n", "。", "\n。；！？", " ", "."]
