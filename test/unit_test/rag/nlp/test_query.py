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


@pytest.mark.filterwarnings("ignore")
class TestFulltextQueryerInit:
    """Test FulltextQueryer initialization"""

    def test_default_init(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        assert qryr.tw is not None
        assert qryr.syn is not None
        assert len(qryr.query_fields) > 0

    def test_query_fields_content(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        assert "title_tks^10" in qryr.query_fields
        assert "content_ltks^2" in qryr.query_fields
        assert "important_kwd^30" in qryr.query_fields


@pytest.mark.filterwarnings("ignore")
class TestFulltextQueryerEdgeCases:
    """Test edge cases for FulltextQueryer"""

    def test_question_empty_string(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()
        result, keywords = qryr.question("")

        assert isinstance(keywords, list)


@pytest.mark.filterwarnings("ignore")
class TestTokenSimilarityEdgeCases:
    """Test edge cases for token_similarity"""

    def test_token_similarity_empty_lists(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        result = qryr.token_similarity([], [])

        assert result == []


@pytest.mark.filterwarnings("ignore")
class TestSimilarityEdgeCases:
    """Test edge cases for similarity"""

    def test_similarity_no_overlap(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        qtwt = {"hello": 1.0, "world": 1.0}
        dtwt = {"test": 0.5, "other": 0.5}

        result = qryr.similarity(qtwt, dtwt)

        assert result >= 0


@pytest.mark.filterwarnings("ignore")
class TestParagraphEdgeCases:
    """Test paragraph method edge cases"""

    def test_paragraph_with_keywords(self):
        from rag.nlp.query import FulltextQueryer

        qryr = FulltextQueryer()

        result = qryr.paragraph("test content", keywords=["keyword"])

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
