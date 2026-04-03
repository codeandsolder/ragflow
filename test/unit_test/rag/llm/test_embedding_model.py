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

from rag.llm import EmbeddingModel
import rag.llm.embedding_model as embedding_model


class TestEmbeddingModelFactoryRegistration:
    def test_openai_embed_registered(self):
        assert "OpenAI" in EmbeddingModel

    def test_ollama_embed_registered(self):
        assert "Ollama" in EmbeddingModel

    def test_xinference_embed_registered(self):
        assert "Xinference" in EmbeddingModel

    def test_cohere_embed_registered(self):
        assert "Cohere" in EmbeddingModel


class TestBaseEmbeddingModel:
    def test_base_is_abstract(self):
        base = embedding_model.Base("key", "model")
        with pytest.raises(NotImplementedError):
            base.encode(["text"])

    def test_base_encode_queries_raises(self):
        base = embedding_model.Base("key", "model")
        with pytest.raises(NotImplementedError):
            base.encode_queries("text")


class TestOpenAIEmbed:
    def test_openai_embed_factory_name(self):
        assert embedding_model.OpenAIEmbed._FACTORY_NAME == "OpenAI"

    @patch("rag.llm.embedding_model.OpenAI")
    def test_openai_embed_init_default_url(self, mock_openai):
        model = embedding_model.OpenAIEmbed("sk-test", "text-embedding-ada-002")
        assert model.model_name == "text-embedding-ada-002"

    @patch("rag.llm.embedding_model.OpenAI")
    def test_openai_embed_init_custom_url(self, mock_openai):
        model = embedding_model.OpenAIEmbed("sk-test", "model", base_url="https://custom.api.com/v1")
        assert model.base_url == "https://custom.api.com/v1"

    @patch("rag.llm.embedding_model.OpenAI")
    def test_openai_embed_empty_base_url_uses_default(self, mock_openai):
        model = embedding_model.OpenAIEmbed("sk-test", "model", base_url="")
        assert model.base_url == "https://api.openai.com/v1"


class TestOpenAIEmbedEncode:
    @patch("rag.llm.embedding_model.OpenAI")
    def test_encode_returns_numpy_array(self, mock_openai):
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_response.usage = MagicMock(total_tokens=10)
        mock_openai.return_value.embeddings.create.return_value = mock_response

        model = embedding_model.OpenAIEmbed("key", "text-embedding-ada-002")
        result, tokens = model.encode(["hello world"])

        assert isinstance(result, np.ndarray)
        assert tokens == 10

    @patch("rag.llm.embedding_model.OpenAI")
    def test_encode_batches_large_input(self, mock_openai):
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1])]
        mock_response.usage = MagicMock(total_tokens=5)
        mock_openai.return_value.embeddings.create.return_value = mock_response

        model = embedding_model.OpenAIEmbed("key", "model")
        model.encode(["text1", "text2", "text3"] * 10)

        assert mock_openai.return_value.embeddings.create.call_count > 1


class TestOllamaEmbed:
    def test_ollama_embed_factory_name(self):
        assert embedding_model.OllamaEmbed._FACTORY_NAME == "Ollama"

    @patch("rag.llm.embedding_model.Client")
    def test_ollama_embed_init_with_base_url(self, mock_client):
        model = embedding_model.OllamaEmbed("key", "model", base_url="http://localhost:11434")
        assert model.model_name == "model"


class TestOllamaEmbedEncode:
    @patch("rag.llm.embedding_model.Client")
    def test_encode_returns_numpy_array(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_client_class.return_value = mock_client

        model = embedding_model.OllamaEmbed("key", "model", base_url="http://localhost:11434")
        result, tokens = model.encode(["hello"])

        assert isinstance(result, np.ndarray)
        assert tokens == 128

    @patch("rag.llm.embedding_model.Client")
    def test_encode_removes_special_tokens(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.embeddings.return_value = {"embedding": [0.1]}
        mock_client_class.return_value = mock_client

        model = embedding_model.OllamaEmbed("key", "model", base_url="http://localhost:11434")
        model.encode(["hello<|endoftext|>"])

        call_args = mock_client.embeddings.call_args
        assert "<|endoftext|>" not in call_args[1]["prompt"]


class TestXinferenceEmbed:
    def test_xinference_embed_factory_name(self):
        assert embedding_model.XinferenceEmbed._FACTORY_NAME == "Xinference"

    @patch("rag.llm.embedding_model.OpenAI")
    def test_xinference_embed_appends_v1(self, mock_openai):
        model = embedding_model.XinferenceEmbed("key", "model", base_url="http://localhost:9999")
        assert model.base_url == "http://localhost:9999/v1"


class TestLocalAIEmbed:
    def test_localai_embed_factory_name(self):
        assert embedding_model.LocalAIEmbed._FACTORY_NAME == "LocalAI"

    def test_localai_embed_requires_base_url(self):
        with pytest.raises(ValueError, match="Local embedding model url cannot be None"):
            embedding_model.LocalAIEmbed("key", "model", base_url=None)

    @patch("rag.llm.embedding_model.OpenAI")
    def test_localai_embed_appends_v1(self, mock_openai):
        model = embedding_model.LocalAIEmbed("key", "model", base_url="http://localhost:8080")
        assert model.base_url == "http://localhost:8080/v1"


class TestAzureEmbed:
    def test_azure_embed_factory_name(self):
        assert embedding_model.AzureEmbed._FACTORY_NAME == "Azure-OpenAI"


@patch("rag.llm.embedding_model.AzureOpenAI")
def test_azure_embed_parses_json_key(mock_azure):
    key = '{"api_key": "test-key", "api_version": "2024-02-01"}'
    embedding_model.AzureEmbed(key, "model", base_url="https://example.azure.com")


class TestBaiChuanEmbed:
    def test_baichuan_embed_factory_name(self):
        assert embedding_model.BaiChuanEmbed._FACTORY_NAME == "BaiChuan"

    @patch("rag.llm.embedding_model.OpenAI")
    def test_baichuan_embed_default_url(self, mock_openai):
        model = embedding_model.BaiChuanEmbed("key")
        assert model.base_url == "https://api.baichuan-ai.com/v1"


class TestQWenEmbed:
    def test_qwen_embed_factory_name(self):
        assert embedding_model.QWenEmbed._FACTORY_NAME == "Tongyi-Qianwen"

    @patch("rag.llm.embedding_model.dashscope.TextEmbedding")
    def test_qwen_embed_init(self, mock_dashscope):
        model = embedding_model.QWenEmbed("key", "text_embedding_v2")
        assert model.model_name == "text_embedding_v2"


class TestZhipuEmbed:
    def test_zhipu_embed_factory_name(self):
        assert embedding_model.ZhipuEmbed._FACTORY_NAME == "ZHIPU-AI"

    @patch("rag.llm.embedding_model.ZhipuAI")
    def test_zhipu_embed_init(self, mock_zhipu):
        model = embedding_model.ZhipuEmbed("key", "embedding-2")
        assert model.model_name == "embedding-2"


class TestCoHereEmbed:
    def test_cohere_embed_factory_name(self):
        assert embedding_model.CoHereEmbed._FACTORY_NAME == "Cohere"

    def test_cohere_embed_init(self):
        model = embedding_model.CoHereEmbed("key", "embed-english-v3.0")
        assert model.model_name == "embed-english-v3.0"


class TestJinaMultiVecEmbed:
    def test_jina_embed_factory_name(self):
        assert embedding_model.JinaMultiVecEmbed._FACTORY_NAME == "Jina"

    def test_jina_embed_default_url(self):
        model = embedding_model.JinaMultiVecEmbed("key", "jina-embeddings-v2")
        assert model.base_url == "https://api.jina.ai/v1/embeddings"

    @patch("rag.llm.embedding_model.requests.post")
    def test_jina_embed_encode_v4(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embeddings": [[0.1, 0.2], [0.3, 0.4]]}],
            "usage": {"total_tokens": 10},
        }
        mock_post.return_value = mock_response

        model = embedding_model.JinaMultiVecEmbed("key", "jina-embeddings-v4")
        result, tokens = model.encode(["text1", "text2"])

        assert isinstance(result, np.ndarray)
        assert result.shape[0] == 2


class TestMistralEmbed:
    def test_mistral_embed_factory_name(self):
        assert embedding_model.MistralEmbed._FACTORY_NAME == "Mistral"

    @patch("rag.llm.embedding_model.MistralClient")
    def test_mistral_embed_init(self, mock_mistral):
        model = embedding_model.MistralEmbed("key", "mistral-embed")
        assert model.model_name == "mistral-embed"


class TestNvidiaEmbed:
    def test_nvidia_embed_factory_name(self):
        assert embedding_model.NvidiaEmbed._FACTORY_NAME == "NVIDIA"

    def test_nvidia_embed_default_url(self):
        model = embedding_model.NvidiaEmbed("key", "model")
        assert model.base_url == "https://integrate.api.nvidia.com/v1/embeddings"

    def test_nvidia_embed_special_case_qa_4(self):
        model = embedding_model.NvidiaEmbed("key", "nvidia/embed-qa-4")
        assert model.base_url == "https://ai.api.nvidia.com/v1/retrieval/nvidia/embeddings"


class TestBedrockEmbed:
    def test_bedrock_embed_factory_name(self):
        assert embedding_model.BedrockEmbed._FACTORY_NAME == "Bedrock"

    @patch("rag.llm.embedding_model.boto3.client")
    def test_bedrock_embed_access_key_mode(self, mock_boto):
        key = '{"auth_mode": "access_key_secret", "bedrock_ak": "ak", "bedrock_sk": "sk", "bedrock_region": "us-east-1"}'
        model = embedding_model.BedrockEmbed(key, "amazon.titan-embed-text-v1")

        assert model.is_amazon is True
        assert model.is_cohere is False


class TestGeminiEmbed:
    def test_gemini_embed_factory_name(self):
        assert embedding_model.GeminiEmbed._FACTORY_NAME == "Gemini"

    @patch("rag.llm.embedding_model.genai.Client")
    def test_gemini_embed_strips_models_prefix(self, mock_genai):
        model = embedding_model.GeminiEmbed("key", "models/gemini-embedding-001")
        assert model.model_name == "gemini-embedding-001"

    @patch("rag.llm.embedding_model.genai.Client")
    def test_gemini_embed_preserves_non_prefixed_name(self, mock_genai):
        model = embedding_model.GeminiEmbed("key", "gemini-embedding-001")
        assert model.model_name == "gemini-embedding-001"


class TestGeminiEmbedParse:
    @patch("rag.llm.embedding_model.genai.Client")
    def test_parse_embedding_dict(self, mock_genai):
        model = embedding_model.GeminiEmbed("key", "model")
        embedding = model._parse_embedding_vector({"values": [0.1, 0.2]})
        assert embedding == [0.1, 0.2]

    @patch("rag.llm.embedding_model.genai.Client")
    def test_parse_embedding_fallback_to_embedding_key(self, mock_genai):
        model = embedding_model.GeminiEmbed("key", "model")
        embedding = model._parse_embedding_vector({"embedding": [0.1, 0.2]})
        assert embedding == [0.1, 0.2]


class TestYoudaoEmbed:
    def test_youdao_embed_factory_name(self):
        assert embedding_model.YoudaoEmbed._FACTORY_NAME == "Youdao"


class TestReplicateEmbed:
    def test_replicate_embed_factory_name(self):
        assert embedding_model.ReplicateEmbed._FACTORY_NAME == "Replicate"

    @patch("rag.llm.embedding_model.replicate.Client")
    def test_replicate_embed_init(self, mock_replicate):
        model = embedding_model.ReplicateEmbed("key", "model/version")
        assert model.model_name == "model/version"


class TestVoyageEmbed:
    def test_voyage_embed_factory_name(self):
        assert embedding_model.VoyageEmbed._FACTORY_NAME == "Voyage AI"

    @patch("rag.llm.embedding_model.voyageai.Client")
    def test_voyage_embed_init(self, mock_voyage):
        model = embedding_model.VoyageEmbed("key", "voyage-3")
        assert model.model_name == "voyage-3"


class TestHuggingFaceEmbed:
    def test_huggingface_embed_factory_name(self):
        assert embedding_model.HuggingFaceEmbed._FACTORY_NAME == "HuggingFace"

    def test_huggingface_embed_requires_model_name(self):
        with pytest.raises(ValueError, match="Model name cannot be None"):
            embedding_model.HuggingFaceEmbed("key", "")

    @patch("rag.llm.embedding_model.requests.post")
    def test_huggingface_embed_encode(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [[0.1, 0.2, 0.3]]
        mock_post.return_value = mock_response

        model = embedding_model.HuggingFaceEmbed("key", "model", base_url="http://localhost:8080")
        result, tokens = model.encode(["hello"])

        assert isinstance(result, np.ndarray)


class TestLmStudioEmbed:
    def test_lmstudio_embed_factory_name(self):
        assert embedding_model.LmStudioEmbed._FACTORY_NAME == "LM-Studio"

    def test_lmstudio_embed_requires_base_url(self):
        with pytest.raises(ValueError, match="Local llm url cannot be None"):
            embedding_model.LmStudioEmbed("key", "model", base_url=None)


class TestOpenAI_APIEmbed:
    def test_openai_api_embed_factory_name(self):
        assert "VLLM" in embedding_model.OpenAI_APIEmbed._FACTORY_NAME
        assert "OpenAI-API-Compatible" in embedding_model.OpenAI_APIEmbed._FACTORY_NAME

    def test_openai_api_embed_requires_url(self):
        with pytest.raises(ValueError, match="url cannot be None"):
            embedding_model.OpenAI_APIEmbed("key", "model", base_url=None)

    @patch("rag.llm.embedding_model.OpenAI")
    def test_openai_api_embed_splits_model_name(self, mock_openai):
        model = embedding_model.OpenAI_APIEmbed("key", "model___variant", base_url="http://localhost:8080")
        assert model.model_name == "model"


class TestSiliconFlowEmbed:
    def test_siliconflow_embed_factory_name(self):
        assert embedding_model.SILICONFLOWEmbed._FACTORY_NAME == "SILICONFLOW"

    def test_siliconflow_embed_default_url(self):
        model = embedding_model.SILICONFLOWEmbed("key", "model")
        assert model.base_url == "https://api.siliconflow.cn/v1/embeddings"

    def test_siliconflow_embed_handles_empty_url(self):
        model = embedding_model.SILICONFLOWEmbed("key", "model", base_url="")
        assert model.base_url == "https://api.siliconflow.cn/v1/embeddings"


class TestVolcEngineEmbed:
    def test_volcengine_embed_factory_name(self):
        assert embedding_model.VolcEngineEmbed._FACTORY_NAME == "VolcEngine"

    def test_volcengine_extract_embedding(self):
        model = embedding_model.VolcEngineEmbed('{"ark_api_key": "key"}', "model")
        result = model._extract_embedding({"data": [{"embedding": [0.1, 0.2]}]})
        assert result == [0.1, 0.2]


class TestEmbeddingModelEncodeQueries:
    @patch("rag.llm.embedding_model.OpenAI")
    def test_openai_encode_queries(self, mock_openai):
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_response.usage = MagicMock(total_tokens=5)
        mock_openai.return_value.embeddings.create.return_value = mock_response

        model = embedding_model.OpenAIEmbed("key", "model")
        result, tokens = model.encode_queries("search query")

        assert result.shape == (3,)
        assert tokens == 5


class TestEmbeddingModelCircuitBreaker:
    @patch("rag.llm.embedding_model.OpenAI")
    def test_circuit_breaker_uses_configurable_failure_threshold(self, mock_openai):
        model = embedding_model.OpenAIEmbed("key", "model", failure_threshold=10)
        assert model.failure_threshold == 10

    @patch("rag.llm.embedding_model.OpenAI")
    def test_circuit_breaker_uses_configurable_recovery_timeout(self, mock_openai):
        model = embedding_model.OpenAIEmbed("key", "model", recovery_timeout=60)
        assert model.recovery_timeout == 60

    @patch("rag.llm.embedding_model.OpenAI")
    def test_circuit_breaker_uses_default_failure_threshold(self, mock_openai):
        model = embedding_model.OpenAIEmbed("key", "model")
        assert model.failure_threshold == 5

    @patch("rag.llm.embedding_model.OpenAI")
    def test_circuit_breaker_uses_default_recovery_timeout(self, mock_openai):
        model = embedding_model.OpenAIEmbed("key", "model")
        assert model.recovery_timeout == 30

    @patch("rag.llm.embedding_model.OpenAI")
    def test_circuit_breaker_uses_env_failure_threshold(self, mock_openai):
        import os

        original = os.environ.get("LLM_FAILURE_THRESHOLD")
        os.environ["LLM_FAILURE_THRESHOLD"] = "3"
        try:
            model = embedding_model.OpenAIEmbed("key", "model")
            assert model.failure_threshold == 3
        finally:
            if original is None:
                os.environ.pop("LLM_FAILURE_THRESHOLD", None)
            else:
                os.environ["LLM_FAILURE_THRESHOLD"] = original

    @patch("rag.llm.embedding_model.OpenAI")
    def test_circuit_breaker_uses_env_recovery_timeout(self, mock_openai):
        import os

        original = os.environ.get("LLM_RECOVERY_TIMEOUT")
        os.environ["LLM_RECOVERY_TIMEOUT"] = "90"
        try:
            model = embedding_model.OpenAIEmbed("key", "model")
            assert model.recovery_timeout == 90
        finally:
            if original is None:
                os.environ.pop("LLM_RECOVERY_TIMEOUT", None)
            else:
                os.environ["LLM_RECOVERY_TIMEOUT"] = original

    @patch("rag.llm.embedding_model.OpenAI")
    def test_circuit_breaker_property_returns_breaker(self, mock_openai):
        model = embedding_model.OpenAIEmbed("key", "model")
        breaker = model.circuit_breaker
        assert breaker is not None

    @patch("rag.llm.embedding_model.OpenAI")
    def test_circuit_breaker_per_provider_isolation(self, mock_openai):
        model1 = embedding_model.OpenAIEmbed("key", "model")
        model2 = embedding_model.QWenEmbed("key", "text_embedding_v2")

        breaker1 = model1.circuit_breaker
        breaker2 = model2.circuit_breaker

        assert id(breaker1) != id(breaker2)


class TestEmbeddingModelUrlNormalization:
    @pytest.mark.parametrize(
        "base_url,expected",
        [
            ("http://localhost:8080", "http://localhost:8080/v1"),
            ("http://localhost:8080/", "http://localhost:8080/v1"),
            ("http://localhost:8080/v1", "http://localhost:8080/v1"),
        ],
    )
    @patch("rag.llm.embedding_model.OpenAI")
    def test_localai_url_normalization(self, mock_openai, base_url, expected):
        model = embedding_model.LocalAIEmbed("k", "model", base_url=base_url)
        assert model.base_url == expected

    @pytest.mark.parametrize(
        "base_url,expected",
        [
            ("http://localhost:8080", "http://localhost:8080/v1"),
            ("http://localhost:8080/", "http://localhost:8080/v1"),
            ("http://localhost:8080/v1", "http://localhost:8080/v1"),
        ],
    )
    @patch("rag.llm.embedding_model.OpenAI")
    def test_openai_api_url_normalization(self, mock_openai, base_url, expected):
        model = embedding_model.OpenAI_APIEmbed("k", "model", base_url=base_url)
        assert model.base_url == expected


class TestEmbeddingModelPatchability:
    def test_module_level_clients_are_patchable(self):
        assert hasattr(embedding_model, "AzureOpenAI")
        assert hasattr(embedding_model, "MistralClient")
        assert hasattr(embedding_model, "boto3")
        assert hasattr(embedding_model, "replicate")


class TestEmbeddingModelFactorySmoke:
    def test_embedding_factory_aliases(self):
        assert EmbeddingModel["OpenAI"] is embedding_model.OpenAIEmbed
        assert EmbeddingModel["Xinference"] is embedding_model.XinferenceEmbed
        assert EmbeddingModel["Cohere"] is embedding_model.CoHereEmbed

    @patch("rag.llm.embedding_model.OpenAI")
    def test_factory_instantiation_smoke(self, mock_openai):
        openai_embed = EmbeddingModel["OpenAI"]("k", "text-embedding-ada-002")
        xinference_embed = EmbeddingModel["Xinference"]("k", "model", base_url="http://localhost:9999")
        localai_embed = EmbeddingModel["LocalAI"]("k", "model", base_url="http://localhost:8080")
        assert openai_embed.model_name == "text-embedding-ada-002"
        assert xinference_embed.base_url.endswith("/v1")
        assert localai_embed.base_url.endswith("/v1")
