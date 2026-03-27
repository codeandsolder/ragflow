#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright 2025 The InfiniFlow Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import asyncio

import pytest
from rag.flow.file import File, FileParam


class MockCanvas:
    def __init__(self, doc_id=None):
        self._doc_id = doc_id
        self._callback_called = False

    def callback(self, progress, message):
        self._callback_called = True


class TestEdgeCaseDocuments:
    """Test class for edge case document processing."""

    def test_empty_document(self):
        """Test processing of empty document."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "file_1", param)

        with pytest.raises((TypeError, IndexError)):
            asyncio.run(file_processor.invoke())

    def test_whitespace_only_document(self):
        """Test processing of whitespace-only document."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "file_1", param)

        with pytest.raises((TypeError, IndexError)):
            asyncio.run(file_processor.invoke(file=[{"name": "test.txt", "content": "   \t\n  "}]))

    def test_extreme_utf8_characters(self):
        """Test processing of document with extreme UTF-8 characters."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        # Test with UTF-8 characters
        test_content = "🚀🌍👻🔥💀💥"
        asyncio.run(file_processor.invoke(file=[{"name": "test.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "test.txt"

    def test_emoji_only_document(self):
        """Test processing of emoji-only document."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        # Test with emoji-only content
        test_content = "🚀😊😍😎😏"
        asyncio.run(file_processor.invoke(file=[{"name": "emoji.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "emoji.txt"

    def test_mixed_encoding_document(self):
        """Test processing of document with mixed encoding."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        # Test with mixed encoding content
        test_content = "Hello 世界! 🚀 Welcome to 2024!"
        asyncio.run(file_processor.invoke(file=[{"name": "mixed.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "mixed.txt"

    def test_null_byte_handling(self):
        """Test processing of document containing null bytes."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        # Test with null bytes
        test_content = "Hello\x00World\x00Test"
        asyncio.run(file_processor.invoke(file=[{"name": "null.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "null.txt"

    def test_very_long_single_line(self):
        """Test processing of very long single line document."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        # Test with very long single line
        test_content = "A" * 100000
        asyncio.run(file_processor.invoke(file=[{"name": "long.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "long.txt"
