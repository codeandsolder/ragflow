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

from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from rag.llm import rerank_model


class TestRerankModelFactoryRegistration:
    def test_jina_rerank_registered(self):
        assert "Jina" in rerank_model.RerankModel

    def test_xinference_rerank_registered(self):
        assert "Xinference" in rerank_model.RerankModel

    def test_cohere_rerank_registered(self):
        assert "Cohere" in rerank_model.RerankModel


class TestBaseRerankModel:
    def test_base_is_abstract(self):
        base = rerank_model.Base("key", "model")
        with pytest.raises(NotImplementedError):
            base.similarity("query", ["text"])

    def test_normalize_rank_all_same(self):
        ranks = np.array([5.0, 5.0, 5.0])
        normalized = rerank_model.Base._normalize_rank(ranks)
        np.testing.assert_array_equal(normalized, np.array([0.0, 0.0, 0.0]))

    def test_normalize_rank_different_values(self):
        ranks = np.array([1.0, 5.0, 10.0])
        normalized = rerank_model.Base._normalize_rank(ranks)
        assert normalized[0] == 0.0
        assert normalized[2] == 1.0
        assert 0.0 < normalized[1] < 1.0


class TestJinaRerank:
    def test_jina_rerank_factory_name(self):
        assert rerank_model.JinaRerank._FACTORY_NAME == "Jina"

    def test_jina_rerank_default_url(self):
        model = rerank_model.JinaRerank("key", "jina-reranker-v2-base-multilingual")
        assert model.base_url == "https://api.jina.ai/v1/rerank"

    @patch("rag.llm.rerank_model.requests.post")
    def test_jina_rerank_similarity(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 0.9},
                {"index": 1, "relevance_score": 0.1},
                {"index": 2, "relevance_score": 0.5},
            ],
            "usage": {"total_tokens": 10},
        }
        mock_post.return_value = mock_response

        model = rerank_model.JinaRerank("key", "model")
        rank, tokens = model.similarity("query", ["doc1", "doc2", "doc3"])

        assert isinstance(rank, np.ndarray)
        assert len(rank) == 3
        assert tokens == 10


class TestXInferenceRerank:
    def test_xinference_rerank_factory_name(self):
        assert rerank_model.XInferenceRerank._FACTORY_NAME == "Xinference"

    @patch("rag.llm.rerank_model.requests.post")
    def test_xinference_rerank_appends_v1_rerank(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [], "usage": {}}
        mock_post.return_value = mock_response

        model = rerank_model.XInferenceRerank("key", "model", base_url="http://localhost:9999")
        model.similarity("query", ["doc1"])

        call_url = mock_post.call_args[0][0]
        assert "/v1/rerank" in call_url

    @patch("rag.llm.rerank_model.requests.post")
    def test_xinference_empty_texts_returns_empty_array(self, mock_post):
        model = rerank_model.XInferenceRerank("key", "model", base_url="http://localhost:9999")
        rank, tokens = model.similarity("query", [])

        assert len(rank) == 0
        assert tokens == 0


class TestLocalAIRerank:
    def test_localai_rerank_factory_name(self):
        assert rerank_model.LocalAIRerank._FACTORY_NAME == "LocalAI"

    @patch("rag.llm.rerank_model.requests.post")
    def test_localai_rerank_normalizes_output(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 10.0},
                {"index": 1, "relevance_score": 5.0},
                {"index": 2, "relevance_score": 1.0},
            ]
        }
        mock_post.return_value = mock_response

        model = rerank_model.LocalAIRerank("key", "model", base_url="http://localhost:8080")
        rank, tokens = model.similarity("query", ["doc1", "doc2", "doc3"])

        assert rank[0] == 1.0
        assert rank[2] == 0.0
        assert 0.0 < rank[1] < 1.0


class TestNvidiaRerank:
    def test_nvidia_rerank_factory_name(self):
        assert rerank_model.NvidiaRerank._FACTORY_NAME == "NVIDIA"

    def test_nvidia_rerank_default_url(self):
        model = rerank_model.NvidiaRerank("key", "model")
        assert "ai.api.nvidia.com" in model.base_url

    def test_nvidia_rerank_special_model_mappings(self):
        model1 = rerank_model.NvidiaRerank("key", "nvidia/nv-rerankqa-mistral-4b-v3")
        assert "nv-rerankqa-mistral-4b-v3/reranking" in model1.base_url

        model2 = rerank_model.NvidiaRerank("key", "nvidia/rerank-qa-mistral-4b")
        assert model2.model_name == "nv-rerank-qa-mistral-4b:1"

    @patch("rag.llm.rerank_model.requests.post")
    def test_nvidia_rerank_similarity(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rankings": [
                {"index": 0, "logit": 5.0},
                {"index": 1, "logit": 2.0},
                {"index": 2, "logit": 1.0},
            ]
        }
        mock_post.return_value = mock_response

        model = rerank_model.NvidiaRerank("key", "model")
        rank, tokens = model.similarity("query", ["doc1", "doc2", "doc3"])

        assert isinstance(rank, np.ndarray)
        assert len(rank) == 3


class TestLmStudioRerank:
    def test_lmstudio_rerank_factory_name(self):
        assert rerank_model.LmStudioRerank._FACTORY_NAME == "LM-Studio"

    def test_lmstudio_rerank_raises_not_implemented(self):
        model = rerank_model.LmStudioRerank("key", "model", base_url="http://localhost:1234")
        with pytest.raises(NotImplementedError):
            model.similarity("query", ["doc1"])


class TestOpenAI_APIRerank:
    def test_openai_api_rerank_factory_name(self):
        assert rerank_model.OpenAI_APIRerank._FACTORY_NAME == "OpenAI-API-Compatible"

    def test_openai_api_rerank_normalizes_url(self):
        model = rerank_model.OpenAI_APIRerank("key", "model", base_url="http://localhost:8080/v1")
        assert "/rerank" in model.base_url

    @patch("rag.llm.rerank_model.requests.post")
    def test_openai_api_rerank_normalizes_output(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 100.0},
                {"index": 1, "relevance_score": 50.0},
                {"index": 2, "relevance_score": 10.0},
            ]
        }
        mock_post.return_value = mock_response

        model = rerank_model.OpenAI_APIRerank("key", "model", base_url="http://localhost:8080")
        rank, tokens = model.similarity("query", ["doc1", "doc2", "doc3"])

        assert rank[0] == 1.0
        assert rank[2] == 0.0


class TestCoHereRerank:
    def test_cohere_rerank_factory_name(self):
        assert "Cohere" in rerank_model.CoHereRerank._FACTORY_NAME

    @patch("rag.llm.rerank_model.cohere.Client")
    def test_cohere_rerank_init(self, mock_cohere):
        model = rerank_model.CoHereRerank("key", "rerank-multilingual-v3.0")
        assert model.model_name == "rerank-multilingual-v3.0"

    @patch("rag.llm.rerank_model.cohere.Client")
    def test_cohere_rerank_similarity(self, mock_cohere_class):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.results = [
            MagicMock(index=0, relevance_score=0.9),
            MagicMock(index=1, relevance_score=0.3),
            MagicMock(index=2, relevance_score=0.6),
        ]
        mock_result.usage = MagicMock()
        mock_client.rerank.return_value = mock_result
        mock_cohere_class.return_value = mock_client

        model = rerank_model.CoHereRerank("key", "model")
        rank, tokens = model.similarity("query", ["doc1", "doc2", "doc3"])

        assert isinstance(rank, np.ndarray)
        assert rank[0] == 0.9


class TestTogetherAIRerank:
    def test_togetherai_rerank_factory_name(self):
        assert rerank_model.TogetherAIRerank._FACTORY_NAME == "TogetherAI"

    def test_togetherai_rerank_raises_not_implemented(self):
        model = rerank_model.TogetherAIRerank("key", "model", base_url="http://localhost:8080")
        with pytest.raises(NotImplementedError):
            model.similarity("query", ["doc1"])


class TestSiliconFlowRerank:
    def test_siliconflow_rerank_factory_name(self):
        assert rerank_model.SILICONFLOWRerank._FACTORY_NAME == "SILICONFLOW"

    def test_siliconflow_rerank_default_url(self):
        model = rerank_model.SILICONFLOWRerank("key", "model")
        assert model.base_url == "https://api.siliconflow.cn/v1/rerank"

    def test_siliconflow_rerank_handles_empty_url(self):
        model = rerank_model.SILICONFLOWRerank("key", "model", base_url="")
        assert model.base_url == "https://api.siliconflow.cn/v1/rerank"

    @patch("rag.llm.rerank_model.requests.post")
    def test_siliconflow_rerank_similarity(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 0.8},
                {"index": 1, "relevance_score": 0.2},
            ],
            "usage": {"total_tokens": 15},
        }
        mock_post.return_value = mock_response

        model = rerank_model.SILICONFLOWRerank("key", "model")
        rank, tokens = model.similarity("query", ["doc1", "doc2"])

        assert len(rank) == 2
        assert tokens == 15


class TestBaiduYiyanRerank:
    def test_baidu_yiyan_rerank_factory_name(self):
        assert rerank_model.BaiduYiyanRerank._FACTORY_NAME == "BaiduYiyan"

    @patch("rag.llm.rerank_model.qianfan.resources.Reranker")
    def test_baidu_yiyan_rerank_parses_json_key(self, mock_reranker):
        key = '{"yiyan_ak": "ak", "yiyan_sk": "sk"}'
        model = rerank_model.BaiduYiyanRerank(key, "model")
        assert model.model_name == "model"


class TestVoyageRerank:
    def test_voyage_rerank_factory_name(self):
        assert rerank_model.VoyageRerank._FACTORY_NAME == "Voyage AI"

    @patch("rag.llm.rerank_model.voyageai.Client")
    def test_voyage_rerank_init(self, mock_voyage):
        model = rerank_model.VoyageRerank("key", "voyage-rerank-2")
        assert model.model_name == "voyage-rerank-2"

    @patch("rag.llm.rerank_model.voyageai.Client")
    def test_voyage_rerank_empty_texts(self, mock_voyage_class):
        mock_client = MagicMock()
        mock_voyage_class.return_value = mock_client

        model = rerank_model.VoyageRerank("key", "model")
        rank, tokens = model.similarity("query", [])

        assert len(rank) == 0
        assert tokens == 0


class TestQWenRerank:
    def test_qwen_rerank_factory_name(self):
        assert rerank_model.QWenRerank._FACTORY_NAME == "Tongyi-Qianwen"

    @patch("rag.llm.rerank_model.dashscope.TextReRank")
    def test_qwen_rerank_uses_gte_rerank_default(self, mock_dashscope):
        model = rerank_model.QWenRerank("key", None)
        assert model.model_name is not None


class TestHuggingfaceRerank:
    def test_huggingface_rerank_factory_name(self):
        assert rerank_model.HuggingfaceRerank._FACTORY_NAME == "HuggingFace"

    @patch("rag.llm.rerank_model.requests.post")
    def test_huggingface_rerank_empty_texts(self, mock_post):
        model = rerank_model.HuggingfaceRerank("key", "model", base_url="http://localhost:8080")
        rank, tokens = model.similarity("query", [])

        assert len(rank) == 0
        assert tokens == 0

    @patch("rag.llm.rerank_model.requests.post")
    def test_huggingface_rerank_similarity(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"index": 0, "score": 0.9},
            {"index": 1, "score": 0.1},
        ]
        mock_post.return_value = mock_response

        model = rerank_model.HuggingfaceRerank("key", "model", base_url="http://localhost:8080")
        rank, tokens = model.similarity("query", ["doc1", "doc2"])

        assert isinstance(rank, np.ndarray)
        assert len(rank) == 2


class TestGPUStackRerank:
    def test_gpustack_rerank_factory_name(self):
        assert rerank_model.GPUStackRerank._FACTORY_NAME == "GPUStack"

    def test_gpustack_rerank_requires_url(self):
        with pytest.raises(ValueError, match="url cannot be None"):
            rerank_model.GPUStackRerank("key", "model", base_url=None)

    @patch("rag.llm.rerank_model.requests.post")
    def test_gpustack_rerank_similarity(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 0.8},
                {"index": 1, "relevance_score": 0.3},
            ]
        }
        mock_post.return_value = mock_response

        model = rerank_model.GPUStackRerank("key", "model", base_url="http://localhost:8080")
        rank, tokens = model.similarity("query", ["doc1", "doc2"])

        assert isinstance(rank, np.ndarray)


class TestNovitaRerank:
    def test_novita_rerank_factory_name(self):
        assert rerank_model.NovitaRerank._FACTORY_NAME == "NovitaAI"

    def test_novita_rerank_default_url(self):
        model = rerank_model.NovitaRerank("key", "model")
        assert model.base_url == "https://api.novita.ai/v3/openai/rerank"

    def test_novita_rerank_handles_empty_url(self):
        model = rerank_model.NovitaRerank("key", "model", base_url="")
        assert model.base_url == "https://api.novita.ai/v3/openai/rerank"


class TestGiteeRerank:
    def test_gitee_rerank_factory_name(self):
        assert rerank_model.GiteeRerank._FACTORY_NAME == "GiteeAI"

    def test_gitee_rerank_default_url(self):
        model = rerank_model.GiteeRerank("key", "model")
        assert model.base_url == "https://ai.gitee.com/v1/rerank"


class TestAi302Rerank:
    def test_ai302_rerank_factory_name(self):
        assert rerank_model.Ai302Rerank._FACTORY_NAME == "302.AI"

    def test_ai302_rerank_default_url(self):
        model = rerank_model.Ai302Rerank("key", "model")
        assert model.base_url == "https://api.302.ai/v1/rerank"


class TestJiekouAIRerank:
    def test_jiekou_ai_rerank_factory_name(self):
        assert rerank_model.JiekouAIRerank._FACTORY_NAME == "Jiekou.AI"

    def test_jiekou_ai_rerank_default_url(self):
        model = rerank_model.JiekouAIRerank("key", "model")
        assert model.base_url == "https://api.jiekou.ai/openai/v1/rerank"


class TestRAGconRerank:
    def test_ragcon_rerank_factory_name(self):
        assert rerank_model.RAGconRerank._FACTORY_NAME == "RAGcon"

    def test_ragcon_rerank_default_url(self):
        model = rerank_model.RAGconRerank("key", "model")
        assert model._base_url == "https://connect.ragcon.com/v1"

    @patch("rag.llm.rerank_model.requests.post")
    def test_ragcon_rerank_normalizes_output(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 100.0},
                {"index": 1, "relevance_score": 20.0},
            ]
        }
        mock_post.return_value = mock_response

        model = rerank_model.RAGconRerank("key", "model")
        rank, tokens = model.similarity("query", ["doc1", "doc2"])

        assert rank[0] == 1.0
        assert rank[1] == 0.0


class TestRerankModelTruncation:
    @patch("rag.llm.rerank_model.requests.post")
    def test_jina_rerank_truncates_long_texts(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [], "usage": {}}
        mock_post.return_value = mock_response

        long_text = "word " * 5000
        model = rerank_model.JinaRerank("key", "model")
        model.similarity("query", [long_text])

        payload = mock_post.call_args[1]["json"]
        assert len(payload["documents"][0]) <= 8196
