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
#  distributed on the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
Unit tests for rag_tokenizer module.
"""

import pytest


@pytest.mark.filterwarnings("ignore")
class TestIsEnglish:
    """Test is_english function from rag/nlp/__init__.py"""

    def test_english_text(self):
        from rag.nlp import is_english

        assert is_english("Hello world") is True

    def test_chinese_text(self):
        from rag.nlp import is_english

        assert is_english("你好世界") is False

    def test_mixed_text(self):
        from rag.nlp import is_english

        assert is_english("Hello 你好") is False

    def test_empty_input(self):
        from rag.nlp import is_english

        assert is_english("") is False

    def test_none_input(self):
        from rag.nlp import is_english

        assert is_english(None) is False

    def test_list_with_chinese(self):
        from rag.nlp import is_english

        assert is_english(["hello", "你好"]) is False


@pytest.mark.filterwarnings("ignore")
class TestIsChinese:
    """Test is_chinese function from rag/nlp/__init__.py"""

    def test_chinese_text(self):
        from rag.nlp import is_chinese

        assert is_chinese("你好世界") is True

    def test_english_text(self):
        from rag.nlp import is_chinese

        assert is_chinese("hello world") is False

    def test_empty_text(self):
        from rag.nlp import is_chinese

        assert is_chinese("") is False

    def test_numbers_only(self):
        from rag.nlp import is_chinese

        assert is_chinese("12345") is False


@pytest.mark.filterwarnings("ignore")
class TestTokenizerFunctions:
    """Test rag_tokenizer basic functions"""

    def test_is_chinese_char(self):
        from rag.nlp import rag_tokenizer

        assert rag_tokenizer.is_chinese("中") is True

    def test_is_number(self):
        from rag.nlp import rag_tokenizer

        assert rag_tokenizer.is_number("123") is True
        assert rag_tokenizer.is_number("abc") is False


@pytest.mark.filterwarnings("ignore")
class TestRandomChoices:
    """Test random_choices function"""

    def test_basic(self):
        from rag.nlp import random_choices

        arr = [1, 2, 3, 4, 5]
        result = random_choices(arr, 3)
        assert len(result) == 3
        assert all(x in arr for x in result)

    def test_k_larger_than_arr(self):
        from rag.nlp import random_choices

        arr = [1, 2]
        result = random_choices(arr, 5)
        assert len(result) == 2


@pytest.mark.filterwarnings("ignore")
class TestExtractBetween:
    """Test extract_between function"""

    def test_simple_extract(self):
        from rag.nlp import extract_between

        text = "startmiddleend"
        result = extract_between(text, "start", "end")
        assert "middle" in result

    def test_no_match(self):
        from rag.nlp import extract_between

        text = "hello world"
        result = extract_between(text, "foo", "bar")
        assert len(result) == 0


@pytest.mark.filterwarnings("ignore")
class TestNodeClass:
    """Test Node class for tree operations"""

    def test_node_creation(self):
        from rag.nlp import Node

        node = Node(level=1, depth=2, texts=["test"])
        assert node.level == 1
        assert node.depth == 2
        assert "test" in node.texts

    def test_add_child(self):
        from rag.nlp import Node

        parent = Node(level=0)
        child = Node(level=1)
        parent.add_child(child)
        assert len(parent.get_children()) == 1

    def test_set_texts(self):
        from rag.nlp import Node

        node = Node(level=0)
        node.set_texts(["a", "b"])
        assert node.get_texts() == ["a", "b"]

    def test_add_text(self):
        from rag.nlp import Node

        node = Node(level=0, texts=[])
        node.add_text("new text")
        assert "new text" in node.get_texts()

    def test_clear_text(self):
        from rag.nlp import Node

        node = Node(level=0, texts=["a", "b"])
        node.clear_text()
        assert node.get_texts() == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
