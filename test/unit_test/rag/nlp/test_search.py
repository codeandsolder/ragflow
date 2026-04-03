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
Unit tests for search module (Dealer class).
"""

import pytest
from unittest.mock import Mock


@pytest.mark.filterwarnings("ignore")
class TestIndexName:
    """Test index_name function"""

    def test_index_name_basic(self):
        from rag.nlp.search import index_name

        result = index_name("user123")
        assert result == "ragflow_user123"

    def test_index_name_empty(self):
        from rag.nlp.search import index_name

        result = index_name("")
        assert result == "ragflow_"

    def test_index_name_special_chars(self):
        from rag.nlp.search import index_name

        result = index_name("user@domain")
        assert result == "ragflow_user@domain"

    def test_index_name_unicode(self):
        from rag.nlp.search import index_name

        result = index_name("用户123")
        assert result == "ragflow_用户123"


@pytest.mark.filterwarnings("ignore")
class TestDealerSearchResult:
    """Test SearchResult dataclass"""

    def test_search_result_creation(self):
        from rag.nlp.search import SearchResult

        result = SearchResult(
            total=10,
            ids=["id1", "id2"],
            query_vector=[0.1, 0.2],
            field={"id1": {"text": "hello"}},
            highlight={"id1": "hello"},
            aggregation={"doc1": 5},
            keywords=["test"],
            group_docs=[["id1", "id2"]],
        )
        assert result.total == 10
        assert len(result.ids) == 2

    def test_search_result_default_values(self):
        from rag.nlp.search import SearchResult

        result = SearchResult(total=0, ids=[])
        assert result.query_vector is None
        assert result.field is None
        assert result.highlight is None


@pytest.mark.filterwarnings("ignore")
class TestDealerTrans2Floats:
    """Test Dealer.trans2floats static method"""

    def test_trans2floats_basic(self):
        from rag.nlp.search import Dealer

        result = Dealer.trans2floats("1.0\t2.5\t3.0")
        assert len(result) == 3
        assert result[0] == 1.0

    def test_trans2floats_single_value(self):
        from rag.nlp.search import Dealer

        result = Dealer.trans2floats("3.14")
        assert len(result) == 1
        assert result[0] == 3.14


@pytest.mark.filterwarnings("ignore")
class TestDealerInstantiation:
    """Test Dealer class instantiation"""

    def test_dealer_init(self):
        from rag.nlp.search import Dealer

        mock_store = Mock()
        dealer = Dealer(mock_store)

        assert dealer.qryr is not None
        assert dealer.dataStore is mock_store


@pytest.mark.filterwarnings("ignore")
class TestDealerGetFilters:
    """Test Dealer.get_filters method"""

    def test_get_filters_basic(self):
        from rag.nlp.search import Dealer

        mock_store = Mock()
        dealer = Dealer(mock_store)

        req = {"kb_ids": ["kb1", "kb2"], "doc_ids": ["doc1"]}
        result = dealer.get_filters(req)

        assert result["kb_id"] == ["kb1", "kb2"]
        assert result["doc_id"] == ["doc1"]

    def test_get_filters_with_optional_fields(self):
        from rag.nlp.search import Dealer

        mock_store = Mock()
        dealer = Dealer(mock_store)

        req = {
            "kb_ids": ["kb1"],
            "knowledge_graph_kwd": "test",
            "available_int": 1,
            "entity_kwd": "entity",
        }
        result = dealer.get_filters(req)

        assert "kb_id" in result
        assert result["knowledge_graph_kwd"] == "test"
        assert result["available_int"] == 1

    def test_get_filters_empty(self):
        from rag.nlp.search import Dealer

        mock_store = Mock()
        dealer = Dealer(mock_store)

        result = dealer.get_filters({})
        assert len(result) == 0

    def test_filters_ignore_none_values(self):
        from rag.nlp.search import Dealer

        mock_store = Mock()
        dealer = Dealer(mock_store)

        req = {"kb_ids": None, "doc_ids": None}
        result = dealer.get_filters(req)
        assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
