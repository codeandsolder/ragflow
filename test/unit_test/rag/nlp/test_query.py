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
Unit tests for query module (FulltextQueryer and hybrid_similarity).
"""

import pytest
from unittest.mock import patch


class TestFulltextQueryerInitialization:
    """Test FulltextQueryer initialization with proper assertions"""

    def test_default_initialization(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        # Test that essential components are initialized
        assert qryr.tw is not None, "Text tokenizer should be initialized"
        assert qryr.syn is not None, "Synonym handler should be initialized"
        assert isinstance(qryr.query_fields, list), "Query fields should be a list"
        assert len(qryr.query_fields) > 0, "Query fields should not be empty"

    def test_query_fields_have_expected_weights(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        # Test that query fields have proper boosting weights
        assert "title_tks^10" in qryr.query_fields, "Title field should have weight 10"
        assert "content_ltks^2" in qryr.query_fields, "Content field should have weight 2"
        assert "important_kwd^30" in qryr.query_fields, "Important keywords field should have weight 30"


class TestFulltextQueryerEdgeCases:
    """Test edge cases for FulltextQueryer with proper behavior"""

    def test_empty_question_returns_empty_keywords(self):
        from rag.nlp.query import FulltextQueryer
        from rag.nlp import query as query_module

        qryr = FulltextQueryer()
        with patch.object(query_module.settings, "DEFAULT_HYBRID_WEIGHT", "0.3,0.7", create=True):
            result, keywords = qryr.question("")

        assert isinstance(keywords, list), "Keywords should be a list"
        assert len(keywords) == 0, "Empty question should return empty keywords"

    def test_empty_token_similarity_returns_empty_list(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        result = qryr.token_similarity([], [])

        assert isinstance(result, list), "Result should be a list"
        assert len(result) == 0, "Empty input should return empty list"

    def test_similarity_with_no_overlap_returns_zero(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        qtwt = {"hello": 1.0, "world": 1.0}
        dtwt = {"test": 0.5, "other": 0.5}

        result = qryr.similarity(qtwt, dtwt)

        assert result == pytest.approx(0.0, abs=1e-8), "No overlap should be approximately zero similarity"

    def test_paragraph_with_empty_content_returns_empty(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        result = qryr.paragraph("", keywords=["keyword"])

        from common.doc_store.doc_store_base import MatchTextExpr

        assert isinstance(result, MatchTextExpr), "Paragraph query should return MatchTextExpr even for empty content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
