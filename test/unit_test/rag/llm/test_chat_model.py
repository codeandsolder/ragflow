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

from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from rag.llm import chat_model


class TestChatModelFactoryRegistration:
    def test_openai_chat_registered(self):
        assert "OpenAI" in chat_model.ChatModel

    def test_xinference_chat_registered(self):
        assert "Xinference" in chat_model.ChatModel

    def test_huggingface_chat_registered(self):
        assert "HuggingFace" in chat_model.ChatModel

    def test_baiChuan_chat_registered(self):
        assert "BaiChuan" in chat_model.ChatModel

    def test_mistral_chat_registered(self):
        assert "Mistral" in chat_model.ChatModel


class TestBaseChatModelInit:
    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_base_init_creates_clients(self, mock_async_openai, mock_openai):
        model = chat_model.Base("test-key", "gpt-4", "https://api.openai.com/v1")
        assert model.model_name == "gpt-4"
        assert model.max_retries == 5

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_base_init_custom_retries(self, mock_async_openai, mock_openai):
        model = chat_model.Base("test-key", "gpt-4", "https://api.openai.com/v1", max_retries=10)
        assert model.max_retries == 10


class TestBaseChatModelErrorClassification:
    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_classify_rate_limit_error(self, mock_async_openai, mock_openai):
        model = chat_model.Base("key", "model", "url")
        error_code = model._classify_error("Rate limit exceeded 429")
        assert error_code == chat_model.LLMErrorCode.ERROR_RATE_LIMIT

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_classify_auth_error(self, mock_async_openai, mock_openai):
        model = chat_model.Base("key", "model", "url")
        error_code = model._classify_error("Invalid API key 401")
        assert error_code == chat_model.LLMErrorCode.ERROR_AUTHENTICATION

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_classify_server_error(self, mock_async_openai, mock_openai):
        model = chat_model.Base("key", "model", "url")
        error_code = model._classify_error("Server error 500")
        assert error_code == chat_model.LLMErrorCode.ERROR_SERVER

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_classify_timeout_error(self, mock_async_openai, mock_openai):
        model = chat_model.Base("key", "model", "url")
        error_code = model._classify_error("Request timed out")
        assert error_code == chat_model.LLMErrorCode.ERROR_TIMEOUT

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_classify_quota_error(self, mock_async_openai, mock_openai):
        model = chat_model.Base("key", "model", "url")
        error_code = model._classify_error("Quota exceeded")
        assert error_code == chat_model.LLMErrorCode.ERROR_QUOTA


class TestOpenAIChat:
    def test_openai_chat_factory_name(self):
        assert chat_model.OpenAIChat._FACTORY_NAME == "OpenAI"

    @patch("rag.llm.chat_model.OpenAI")
    def test_openai_chat_init_default_url(self, mock_openai):
        model = chat_model.OpenAIChat("sk-test", "gpt-4")
        assert model.model_name == "gpt-4"

    @patch("rag.llm.chat_model.OpenAI")
    def test_openai_chat_init_custom_url(self, mock_openai):
        model = chat_model.OpenAIChat("sk-test", "gpt-4", base_url="https://custom.api.com/v1")
        assert model.base_url == "https://custom.api.com/v1"


class TestXinferenceChat:
    def test_xinference_chat_factory_name(self):
        assert chat_model.XinferenceChat._FACTORY_NAME == "Xinference"

    def test_xinference_chat_requires_base_url(self):
        with pytest.raises(ValueError, match="Local llm url cannot be None"):
            chat_model.XinferenceChat("key", "model")

    @patch("rag.llm.chat_model.OpenAI")
    def test_xinference_chat_appends_v1(self, mock_openai):
        model = chat_model.XinferenceChat("key", "model", base_url="http://localhost:9999")
        assert model.base_url == "http://localhost:9999/v1"


class TestBaiChuanChat:
    def test_baiChuan_chat_factory_name(self):
        assert chat_model.BaiChuanChat._FACTORY_NAME == "BaiChuan"

    def test_baiChuan_chat_default_url(self):
        with patch("rag.llm.chat_model.OpenAI"):
            model = chat_model.BaiChuanChat("key")
            assert model.base_url == "https://api.baichuan-ai.com/v1"


class TestMistralChat:
    def test_mistral_chat_factory_name(self):
        assert chat_model.MistralChat._FACTORY_NAME == "Mistral"

    @patch("rag.llm.chat_model.MistralClient")
    def test_mistral_chat_uses_mistral_client(self, mock_mistral):
        model = chat_model.MistralChat("key", "mistral-small")
        assert model.model_name == "mistral-small"


class TestLiteLLMBase:
    @patch("rag.llm.chat_model.litellm")
    def test_litellm_base_factory_name(self, mock_litellm):
        assert chat_model.LiteLLMBase._FACTORY_NAME == "LiteLLM"

    @patch("rag.llm.chat_model.litellm")
    def test_litellm_base_init(self, mock_litellm):
        model = chat_model.LiteLLMBase("key", "gpt-4", provider="OpenAI")
        assert model.model_name == "gpt-4"
        assert model.provider == "OpenAI"


class TestLocalAIChat:
    def test_localai_chat_factory_name(self):
        assert chat_model.LocalAIChat._FACTORY_NAME == "LocalAI"

    def test_localai_chat_requires_base_url(self):
        with pytest.raises(ValueError, match="Local llm url cannot be None"):
            chat_model.LocalAIChat("key", "model")

    @patch("rag.llm.chat_model.OpenAI")
    def test_localai_chat_appends_v1(self, mock_openai):
        model = chat_model.LocalAIChat("key", "model", base_url="http://localhost:8080")
        assert model.base_url == "http://localhost:8080/v1"


class TestLmStudioChat:
    def test_lmstudio_chat_factory_name(self):
        assert chat_model.LmStudioChat._FACTORY_NAME == "LM-Studio"

    def test_lmstudio_chat_requires_base_url(self):
        with pytest.raises(ValueError, match="Local llm url cannot be None"):
            chat_model.LmStudioChat("key", "model", base_url=None)

    @patch("rag.llm.chat_model.OpenAI")
    def test_lmstudio_chat_appends_v1(self, mock_openai):
        model = chat_model.LmStudioChat("key", "model", base_url="http://localhost:1234")
        assert model.base_url == "http://localhost:1234/v1"


class TestOpenAI_APIChat:
    def test_openai_api_chat_factory_name(self):
        assert "VLLM" in chat_model.OpenAI_APIChat._FACTORY_NAME
        assert "OpenAI-API-Compatible" in chat_model.OpenAI_APIChat._FACTORY_NAME

    def test_openai_api_chat_requires_url(self):
        with pytest.raises(ValueError, match="url cannot be None"):
            chat_model.OpenAI_APIChat("key", "model", base_url=None)


class TestLeptonAIChat:
    def test_lepton_ai_chat_factory_name(self):
        assert chat_model.LeptonAIChat._FACTORY_NAME == "LeptonAI"

    @patch("rag.llm.chat_model.OpenAI")
    def test_lepton_ai_constructs_url_from_model(self, mock_openai):
        model = chat_model.LeptonAIChat("key", "my-model")
        assert "my-model.lepton.run" in model.base_url


class TestReplicateChat:
    def test_replicate_chat_factory_name(self):
        assert chat_model.ReplicateChat._FACTORY_NAME == "Replicate"

    @patch("rag.llm.chat_model.ReplicateClient")
    def test_replicate_chat_uses_replicate_client(self, mock_replicate):
        model = chat_model.ReplicateChat("key", "model/version")
        assert model.model_name == "model/version"


class TestSparkChat:
    def test_spark_chat_factory_name(self):
        assert chat_model.SparkChat._FACTORY_NAME == "XunFei Spark"

    def test_spark_chat_supported_models(self):
        supported = ["Spark-Max", "Spark-Max-32K", "Spark-Lite", "Spark-Pro", "Spark-Pro-128K", "Spark-4.0-Ultra"]
        for model_name in supported:
            with patch("rag.llm.chat_model.OpenAI"):
                model = chat_model.SparkChat("key", model_name)
                assert model.model_name is not None

    def test_spark_chat_unsupported_model_raises(self):
        with pytest.raises(AssertionError):
            chat_model.SparkChat("key", "Unknown-Model")


class TestApplyModelFamilyPolicies:
    def test_qwen3_adds_enable_thinking_false(self):
        gen_conf, kwargs = chat_model._apply_model_family_policies("qwen3-8b", backend="base", gen_conf={}, request_kwargs={})
        assert kwargs["extra_body"]["enable_thinking"] is False

    def test_gpt5_clears_gen_conf(self):
        gen_conf, kwargs = chat_model._apply_model_family_policies("gpt-5-turbo", backend="base", gen_conf={"temperature": 0.5}, request_kwargs={})
        assert gen_conf == {}

    def test_empty_gen_conf_returns_copy(self):
        gen_conf, kwargs = chat_model._apply_model_family_policies("gpt-4", backend="base", gen_conf=None, request_kwargs={})
        assert gen_conf == {}


class TestVolcEngineChat:
    def test_volc_engine_chat_factory_name(self):
        assert chat_model.VolcEngineChat._FACTORY_NAME == "VolcEngine"

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_volc_engine_parses_json_key(self, mock_async, mock_sync):
        key = '{"ark_api_key": "test-key", "ep_id": "ep-", "endpoint_id": "123"}'
        model = chat_model.VolcEngineChat(key, "model")


class TestTokenPonyChat:
    def test_token_pony_chat_factory_name(self):
        assert chat_model.TokenPonyChat._FACTORY_NAME == "TokenPony"

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_token_pony_default_url(self, mock_async, mock_sync):
        model = chat_model.TokenPonyChat("key", "model")
        assert model.base_url == "https://ragflow.vip-api.tokenpony.cn/v1"


class TestChatModelRetryProperties:
    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_retryable_errors_includes_rate_limit(self, mock_async, mock_sync):
        model = chat_model.Base("key", "model", "url")
        assert chat_model.LLMErrorCode.ERROR_RATE_LIMIT in model._retryable_errors

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_retryable_errors_includes_server_error(self, mock_async, mock_sync):
        model = chat_model.Base("key", "model", "url")
        assert chat_model.LLMErrorCode.ERROR_SERVER in model._retryable_errors

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_should_retry_rate_limit(self, mock_async, mock_sync):
        model = chat_model.Base("key", "model", "url")
        assert model._should_retry(chat_model.LLMErrorCode.ERROR_RATE_LIMIT) is True

    @patch("rag.llm.chat_model.OpenAI")
    @patch("rag.llm.chat_model.AsyncOpenAI")
    def test_should_not_retry_auth_error(self, mock_async, mock_sync):
        model = chat_model.Base("key", "model", "url")
        assert model._should_retry(chat_model.LLMErrorCode.ERROR_AUTHENTICATION) is False
