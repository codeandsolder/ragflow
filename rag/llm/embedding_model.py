#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
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
import json
import os
import threading
from abc import ABC
from urllib.parse import urljoin

import dashscope
import numpy as np
import httpx
from ollama import Client
from openai import OpenAI
from zhipuai import ZhipuAI
from google import genai
from google.genai import types

from common.log_utils import log_exception
from common.token_utils import num_tokens_from_string, truncate, total_token_count_from_response
from common import settings
import logging
import base64
import requests
import voyageai
from rag.llm.remote_model_base import RemoteModelBase

try:
    import boto3
except Exception:
    boto3 = None

try:
    from openai.lib.azure import AzureOpenAI
except Exception:
    AzureOpenAI = None

try:
    from mistralai.client import MistralClient
except Exception:
    MistralClient = None

try:
    import replicate
except Exception:
    class _ReplicateStub:
        class Client:  # pragma: no cover - test patch target fallback
            pass

    replicate = _ReplicateStub()


class Base(RemoteModelBase, ABC):
    def __init__(self, key, model_name, **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name

    def encode(self, texts: list):
        raise NotImplementedError("Please implement encode method!")

    def encode_queries(self, text: str):
        raise NotImplementedError("Please implement encode method!")


class BuiltinEmbed(Base):
    _FACTORY_NAME = "Builtin"
    MAX_TOKENS = {"Qwen/Qwen3-Embedding-0.6B": 30000, "BAAI/bge-m3": 8000, "BAAI/bge-small-en-v1.5": 500}
    DEFAULT_MAX_TOKENS = 500
    OPENAI_TRUNCATION_LIMIT = 8191
    BAICHUN_TRUNCATION_LIMIT = 2048
    JINA_TRUNCATION_LIMIT = 8196
    XINFERENCE_TRUNCATION_LIMIT = 4096
    _model = None
    _model_name = ""
    _max_tokens = 500
    _model_lock = threading.Lock()

    def __init__(self, key, model_name, **kwargs):
        logging.info(f"Initialize BuiltinEmbed according to settings.EMBEDDING_CFG: {settings.EMBEDDING_CFG}")
        embedding_cfg = settings.EMBEDDING_CFG
        if not BuiltinEmbed._model and "tei-" in os.getenv("COMPOSE_PROFILES", ""):
            with BuiltinEmbed._model_lock:
                BuiltinEmbed._model_name = settings.EMBEDDING_MDL
                BuiltinEmbed._max_tokens = BuiltinEmbed.MAX_TOKENS.get(settings.EMBEDDING_MDL, 500)
                BuiltinEmbed._model = HuggingFaceEmbed(embedding_cfg["api_key"], settings.EMBEDDING_MDL, base_url=embedding_cfg["base_url"])
        self._model = BuiltinEmbed._model
        self._model_name = BuiltinEmbed._model_name
        self._max_tokens = BuiltinEmbed._max_tokens

    def encode(self, texts: list):
        batch_size = 16
        # TEI is able to auto truncate inputs according to https://github.com/huggingface/text-embeddings-inference.
        token_count = 0
        ress = None
        for i in range(0, len(texts), batch_size):
            embeddings, token_count_delta = self._model.encode(texts[i : i + batch_size])
            token_count += token_count_delta
            if ress is None:
                ress = embeddings
            else:
                ress = np.concatenate((ress, embeddings), axis=0)
        return ress, token_count

    def encode_queries(self, text: str):
        return self._model.encode_queries(text)


class OpenAIEmbed(Base):
    _FACTORY_NAME = "OpenAI"

    def __init__(self, key, model_name="text-embedding-ada-002", base_url="https://api.openai.com/v1", **kwargs):
        super().__init__(key, model_name, **kwargs)
        if not base_url:
            base_url = "https://api.openai.com/v1"
        use_litellm_proxy = os.environ.get("USE_LITELLM_PROXY", "false").lower() == "true"
        if use_litellm_proxy:
            litellm_proxy_url = os.environ.get("LITELLM_PROXY_URL", "http://litellm:4000")
            base_url = f"{litellm_proxy_url}/v1"
        self.base_url = base_url
        self.client = OpenAI(api_key=key, base_url=base_url)

    def encode(self, texts: list):
        batch_size = 16
        texts = [truncate(t, 8191) for t in texts]

        def encode_batch(batch):
            res = self.client.embeddings.create(input=batch, model=self.model_name, encoding_format="float", extra_body={"drop_params": True})
            return [d.embedding for d in res.data], total_token_count_from_response(res)

        return self._run_in_batches(texts, batch_size, encode_batch)

    def encode_queries(self, text):
        def encode_query():
            res = self.client.embeddings.create(input=[truncate(text, 8191)], model=self.model_name, encoding_format="float", extra_body={"drop_params": True})
            return np.array(res.data[0].embedding), total_token_count_from_response(res)

        return self._run_with_retry(encode_query)


class LocalAIEmbed(Base):
    _FACTORY_NAME = "LocalAI"

    def __init__(self, key, model_name, base_url=None, **kwargs):
        super().__init__(key, model_name, **kwargs)
        if not base_url:
            raise ValueError("Local embedding model url cannot be None")
        base_url = urljoin(base_url, "v1")
        self.base_url = base_url
        self.client = OpenAI(api_key="empty", base_url=base_url)
        self.model_name = model_name.split("___")[0]

    def encode(self, texts: list):
        batch_size = 16
        ress = []
        token_count = 0
        for i in range(0, len(texts), batch_size):
            res = self.client.embeddings.create(input=texts[i : i + batch_size], model=self.model_name)
            try:
                ress.extend([d.embedding for d in res.data])
                token_count += total_token_count_from_response(res)
            except Exception as _e:
                log_exception(_e, res)
                raise Exception(f"Error: {res}")
        return np.array(ress), token_count

    def encode_queries(self, text):
        embds, cnt = self.encode([text])
        return np.array(embds[0]), cnt


class AzureEmbed(OpenAIEmbed):
    _FACTORY_NAME = "Azure-OpenAI"

    def __init__(self, key, model_name, **kwargs):
        if AzureOpenAI is None:
            raise ImportError("AzureOpenAI is not installed")
        super().__init__(key, model_name, kwargs["base_url"])
        api_key = json.loads(key).get("api_key", "")
        api_version = json.loads(key).get("api_version", "2024-02-01")
        self.client = AzureOpenAI(api_key=api_key, azure_endpoint=kwargs["base_url"], api_version=api_version)
        self.model_name = model_name


class BaiChuanEmbed(OpenAIEmbed):
    _FACTORY_NAME = "BaiChuan"

    def __init__(self, key, model_name="Baichuan-Text-Embedding", base_url="https://api.baichuan-ai.com/v1"):
        if not base_url:
            base_url = "https://api.baichuan-ai.com/v1"
        super().__init__(key, model_name, base_url)


class QWenEmbed(Base):
    _FACTORY_NAME = "Tongyi-Qianwen"

    def __init__(self, key, model_name="text_embedding_v2", **kwargs):
        super().__init__(key=key, model_name=model_name, **kwargs)
        self.key = key
        self.model_name = model_name

    def encode(self, texts: list):
        import dashscope

        batch_size = 4
        texts = [truncate(t, 2048) for t in texts]

        def encode_batch(batch):
            resp = dashscope.TextEmbedding.call(model=self.model_name, input=batch, api_key=self.key, text_type="document")
            if resp["output"] is None or resp["output"].get("embeddings") is None:
                if resp.get("message"):
                    raise ValueError(f"Calling embedding model failed: {resp['message']}")
                raise ValueError("Calling embedding model failed")
            return [d["embedding"] for d in resp["output"]["embeddings"]], total_token_count_from_response(resp)

        return self._run_in_batches(texts, batch_size, encode_batch)

    def encode_queries(self, text: str):
        def encode_query():
            resp = dashscope.TextEmbedding.call(model=self.model_name, input=text[:2048], api_key=self.key, text_type="query")
            if resp["output"] is None or resp["output"].get("embeddings") is None:
                if resp.get("message"):
                    raise ValueError(f"Calling embedding model failed: {resp['message']}")
                raise ValueError("Calling embedding model failed")
            return np.array(resp["output"]["embeddings"][0]["embedding"]), total_token_count_from_response(resp)
        return self._run_with_retry(encode_query)


class ZhipuEmbed(Base):
    _FACTORY_NAME = "ZHIPU-AI"

    def __init__(self, key, model_name="embedding-2", **kwargs):
        super().__init__(key=key, model_name=model_name, **kwargs)
        self.client = ZhipuAI(api_key=key)
        self.model_name = model_name

    def encode(self, texts: list) -> tuple[np.ndarray, int]:
        arr = []
        tks_num = 0
        MAX_LEN = -1
        if self.model_name.lower() == "embedding-2":
            MAX_LEN = 512
        if self.model_name.lower() == "embedding-3":
            MAX_LEN = 3072
        if MAX_LEN > 0:
            texts = [truncate(t, MAX_LEN) for t in texts]

        for txt in texts:

            def encode_one():
                res = self.client.embeddings.create(input=txt, model=self.model_name)
                return res.data[0].embedding, total_token_count_from_response(res)

            try:
                embedding, tokens = self._run_with_retry(encode_one)
                arr.append(embedding)
                tks_num += tokens
            except Exception as e:
                log_exception(e)
                raise
        return np.array(arr), tks_num

    def encode_queries(self, text):
        res = self.client.embeddings.create(input=text, model=self.model_name)
        try:
            return np.array(res.data[0].embedding), total_token_count_from_response(res)
        except Exception as _e:
            log_exception(_e, res)
            raise Exception(f"Error: {res}")


class OllamaEmbed(Base):
    _FACTORY_NAME = "Ollama"

    _special_tokens = ["<|endoftext|>", "&lt;|endoftext|&gt;"]

    def __init__(self, key, model_name, **kwargs):
        super().__init__(key=key, model_name=model_name, **kwargs)
        self.client = Client(host=kwargs["base_url"]) if not key or key == "x" else Client(host=kwargs["base_url"], headers={"Authorization": f"Bearer {key}"})
        self.model_name = model_name
        self.keep_alive = kwargs.get("ollama_keep_alive", int(os.environ.get("OLLAMA_KEEP_ALIVE", -1)))

    def encode(self, texts: list) -> tuple[np.ndarray, int]:
        arr = []
        tks_num = 0
        for txt in texts:
            for token in OllamaEmbed._special_tokens:
                txt = txt.replace(token, "")

            def encode_one():
                res = self.client.embeddings(prompt=txt, model=self.model_name, options={"use_mmap": True}, keep_alive=self.keep_alive)
                return res["embedding"]

            try:
                arr.append(self._run_with_retry(encode_one))
            except Exception as e:
                log_exception(e)
                raise
            tks_num += 128
        return np.array(arr), tks_num

    def encode_queries(self, text: str):
        for token in OllamaEmbed._special_tokens:
            text = text.replace(token, "")

        def encode_query():
            res = self.client.embeddings(prompt=text, model=self.model_name, options={"use_mmap": True}, keep_alive=self.keep_alive)
            return np.array(res["embedding"]), 128

        try:
            return self._run_with_retry(encode_query)
        except Exception as e:
            log_exception(e)
            raise


class XinferenceEmbed(Base):
    _FACTORY_NAME = "Xinference"

    def __init__(self, key, model_name="", base_url="", **kwargs):
        super().__init__(key, model_name, **kwargs)
        base_url = urljoin(base_url, "v1")
        self.base_url = base_url
        self.client = OpenAI(api_key=key, base_url=base_url)
        self.model_name = model_name

    def encode(self, texts: list) -> tuple[np.ndarray, int]:
        batch_size = 16
        ress = []
        total_tokens = 0
        for i in range(0, len(texts), batch_size):

            def encode_batch():
                res = self.client.embeddings.create(input=texts[i : i + batch_size], model=self.model_name)
                return [d.embedding for d in res.data], total_token_count_from_response(res)

            try:
                embeddings, tokens = self._run_with_retry(encode_batch)
                ress.extend(embeddings)
                total_tokens += tokens
            except Exception as e:
                log_exception(e)
                raise
        return np.array(ress), total_tokens

    def encode_queries(self, text: str):
        def encode_query():
            res = self.client.embeddings.create(input=[text], model=self.model_name)
            return np.array(res.data[0].embedding), total_token_count_from_response(res)

        try:
            return self._run_with_retry(encode_query)
        except Exception as e:
            log_exception(e)
            raise


class YoudaoEmbed(Base):
    _FACTORY_NAME = "Youdao"
    _client = None

    def __init__(self, key=None, model_name="maidalun1020/bce-embedding-base_v1", **kwargs):
        pass

    def encode(self, texts: list) -> tuple[np.ndarray, int]:
        batch_size = 10
        res = []
        token_count = 0
        for t in texts:
            token_count += num_tokens_from_string(t)
        for i in range(0, len(texts), batch_size):

            def encode_batch():
                embds = YoudaoEmbed._client.encode(texts[i : i + batch_size])
                return embds

            try:
                embds = self._run_with_retry(encode_batch)
                res.extend(embds)
            except Exception as e:
                log_exception(e)
                raise
        return np.array(res), token_count

    def encode_queries(self, text: str):
        def encode_query():
            embds = YoudaoEmbed._client.encode([text])
            return np.array(embds[0]), num_tokens_from_string(text)

        try:
            return self._run_with_retry(encode_query)
        except Exception as e:
            log_exception(e)
            raise


class JinaMultiVecEmbed(Base):
    _FACTORY_NAME = "Jina"

    def __init__(self, key, model_name="jina-embeddings-v4", base_url="https://api.jina.ai/v1/embeddings"):
        super().__init__(key, model_name)
        self.base_url = "https://api.jina.ai/v1/embeddings"
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
        self.model_name = model_name

    def encode(self, texts: list[str | bytes], task="retrieval.passage") -> tuple[np.ndarray, int]:
        batch_size = 16
        ress = []
        token_count = 0
        input = []
        for text in texts:
            if isinstance(text, str):
                input.append({"text": text})
            elif isinstance(text, bytes):
                img_b64s = None
                try:
                    base64.b64decode(text, validate=True)
                    img_b64s = text.decode("utf8")
                except Exception:
                    img_b64s = base64.b64encode(text).decode("utf8")
                input.append({"image": img_b64s})  # base64 encoded image
        for i in range(0, len(texts), batch_size):
            data = {"model": self.model_name, "input": input[i : i + batch_size]}
            if "v4" in self.model_name:
                data["return_multivector"] = True

            if "v3" in self.model_name or "v4" in self.model_name:
                data["task"] = task
                data["truncate"] = True

            def encode_batch():
                response = requests.post(self.base_url, headers=self.headers, json=data)
                return response.json()

            try:
                res = self._run_with_retry(encode_batch)
                for d in res["data"]:
                    if data.get("return_multivector", False):  # v4
                        token_embs = np.asarray(d["embeddings"], dtype=np.float32)
                        if token_embs.ndim == 2:
                            ress.extend(token_embs)
                            continue
                        chunk_emb = token_embs.mean(axis=0)
                    else:
                        # v2/v3
                        chunk_emb = np.asarray(d["embedding"], dtype=np.float32)
                    ress.append(chunk_emb)
                token_count += total_token_count_from_response(res)
            except Exception as e:
                log_exception(e)
                raise
        return np.array(ress), token_count

    def encode_queries(self, text: str):
        embds, cnt = self.encode([text], task="retrieval.query")
        return np.array(embds[0]), cnt


class MistralEmbed(Base):
    _FACTORY_NAME = "Mistral"

    def __init__(self, key, model_name="mistral-embed", base_url=None, **kwargs):
        super().__init__(key=key, model_name=model_name, **kwargs)
        if MistralClient is None:
            raise ImportError("mistralai is not installed")
        self.client = MistralClient(api_key=key)
        self.model_name = model_name


class NvidiaEmbed(OpenAIEmbed):
    _FACTORY_NAME = "NVIDIA"

    def __init__(self, key, model_name, **kwargs):
        if "embed-qa-4" in model_name:
            base_url = "https://ai.api.nvidia.com/v1/retrieval/nvidia/embeddings"
        else:
            base_url = "https://integrate.api.nvidia.com/v1/embeddings"
        super().__init__(key, model_name, base_url=base_url, **kwargs)

    def encode(self, texts: list) -> tuple[np.ndarray, int]:

        texts = [truncate(t, 8196) for t in texts]
        batch_size = 16
        ress = []
        token_count = 0
        for i in range(0, len(texts), batch_size):

            def encode_batch():
                res = self.client.embeddings(input=texts[i : i + batch_size], model=self.model_name)
                return [d.embedding for d in res.data], total_token_count_from_response(res)

            try:
                embeddings, tokens = self._run_with_retry(encode_batch)
                ress.extend(embeddings)
                token_count += tokens
            except Exception as e:
                log_exception(e)
                raise
        return np.array(ress), token_count

    def encode_queries(self, text: str):

        def encode_query():
            res = self.client.embeddings(input=[truncate(text, 8196)], model=self.model_name)
            return np.array(res.data[0].embedding), total_token_count_from_response(res)

        try:
            return self._run_with_retry(encode_query)
        except Exception as e:
            log_exception(e)
            raise


class GeminiEmbed(Base):
    _FACTORY_NAME = "Gemini"

    def __init__(self, key, model_name, **kwargs):
        super().__init__(key=key, model_name=model_name, **kwargs)
        self.api_key = key
        if model_name.startswith("models/"):
            model_name = model_name[len("models/") :]
        self.model_name = model_name

    def _parse_embedding_vector(self, data):
        if isinstance(data, dict):
            if "values" in data:
                return data["values"]
            if "embedding" in data:
                return data["embedding"]
        return data

    def encode(self, texts: list):
        client = genai.Client(api_key=self.api_key)
        result = client.embed_content(model=self.model_name, contents=texts)
        embeddings = [np.array(r.embeddings) for r in (result if isinstance(result, list) else [result])]
        tokens = sum([len(t) for t in texts])  # rough estimate
        return np.array(embeddings), tokens

    def encode_queries(self, text: str):
        emb, tokens = self.encode([text])
        return emb[0], tokens


class BedrockEmbed(Base):
    _FACTORY_NAME = "Bedrock"

    def __init__(self, key, model_name, **kwargs):
        super().__init__(key=key, model_name=model_name, **kwargs)
        if boto3 is None:
            raise ImportError("boto3 is not installed")
        # `key` protocol (backend stores as JSON string in `api_key`):
        # - Must decode into a dict.
        # - Required: `auth_mode`, `bedrock_region`.
        # - Supported auth modes:
        #   - "access_key_secret": requires `bedrock_ak` + `bedrock_sk`.
        #   - "iam_role": requires `aws_role_arn` and assumes role via STS.
        #   - else: treated as "assume_role" (default AWS credential chain).
        key = json.loads(key)
        mode = key.get("auth_mode")
        if not mode:
            logging.error("Bedrock auth_mode is not provided in the key")
            raise ValueError("Bedrock auth_mode must be provided in the key")

        self.bedrock_region = key.get("bedrock_region")

        self.model_name = model_name
        self.is_amazon = self.model_name.split(".")[0] == "amazon"
        self.is_cohere = self.model_name.split(".")[0] == "cohere"

        if mode == "access_key_secret":
            self.bedrock_ak = key.get("bedrock_ak")
            self.bedrock_sk = key.get("bedrock_sk")
            self.client = boto3.client(service_name="bedrock-runtime", region_name=self.bedrock_region, aws_access_key_id=self.bedrock_ak, aws_secret_access_key=self.bedrock_sk)
        elif mode == "iam_role":
            self.aws_role_arn = key.get("aws_role_arn")
            sts_client = boto3.client("sts", region_name=self.bedrock_region)
            resp = sts_client.assume_role(RoleArn=self.aws_role_arn, RoleSessionName="BedrockSession")
            creds = resp["Credentials"]

            self.client = boto3.client(
                service_name="bedrock-runtime",
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds["SessionToken"],
            )
        else:  # assume_role
            self.client = boto3.client("bedrock-runtime", region_name=self.bedrock_region)

    def encode(self, texts: list) -> tuple[np.ndarray, int]:
        texts = [truncate(t, 8196) for t in texts]
        embeddings = []
        token_count = 0
        for text in texts:
            if self.is_amazon:
                body = {"inputText": text}
            elif self.is_cohere:
                body = {"texts": [text], "input_type": "search_document"}

            def encode_one():
                response = self.client.invoke_model(modelId=self.model_name, body=json.dumps(body))
                model_response = json.loads(response["body"].read())
                if self.is_amazon:
                    return np.asarray(model_response["embedding"]), total_token_count_from_response(model_response)
                elif self.is_cohere:
                    return np.asarray(model_response["embeddings"][0]["embedding"]), total_token_count_from_response(model_response)

            try:
                embedding, tokens = self._run_with_retry(encode_one)
                embeddings.append(embedding)
                token_count += tokens
            except Exception as e:
                log_exception(e)
                raise
        return np.array(embeddings), token_count

    def encode_queries(self, text: str):
        def encode_query():
            if self.is_amazon:
                body = {"inputText": truncate(text, 8196)}
            elif self.is_cohere:
                body = {"texts": [truncate(text, 8196)], "input_type": "search_query"}
            response = self.client.invoke_model(modelId=self.model_name, body=json.dumps(body))
            model_response = json.loads(response["body"].read())
            if self.is_amazon:
                return np.asarray(model_response["embedding"]), num_tokens_from_string(text)
            elif self.is_cohere:
                return np.asarray(model_response["embeddings"][0]["embedding"]), num_tokens_from_string(text)

        try:
            return self._run_with_retry(encode_query)
        except Exception as e:
            log_exception(e)
            raise

    def encode_queries(self, text: str):
        embds, cnt = self.encode([text])
        return np.array(embds[0]), cnt


class LmStudioEmbed(LocalAIEmbed):
    _FACTORY_NAME = "LM-Studio"

    def __init__(self, key, model_name, base_url):
        if not base_url:
            raise ValueError("Local llm url cannot be None")
        super().__init__(key, model_name, base_url=base_url)
        self.client = OpenAI(api_key="lm-studio", base_url=self.base_url)
        self.model_name = model_name


class OpenAI_APIEmbed(OpenAIEmbed):
    _FACTORY_NAME = ["VLLM", "OpenAI-API-Compatible"]

    def __init__(self, key, model_name, base_url):
        if not base_url:
            raise ValueError("url cannot be None")
        base_url = urljoin(base_url, "v1")
        super().__init__(key, model_name.split("___")[0], base_url=base_url)
        self.base_url = base_url
        self.client = OpenAI(api_key=key, base_url=base_url)
        self.model_name = model_name.split("___")[0]


class CoHereEmbed(Base):
    _FACTORY_NAME = "Cohere"

    def __init__(self, key, model_name, base_url=None, **kwargs):
        super().__init__(key=key, model_name=model_name, **kwargs)
        from cohere import Client

        self.client = Client(api_key=key)
        self.model_name = model_name

    def encode(self, texts: list):
        batch_size = 16
        ress = []
        token_count = 0
        for i in range(0, len(texts), batch_size):

            def encode_batch():
                res = self.client.embed(
                    texts=texts[i : i + batch_size],
                    model=self.model_name,
                    input_type="search_document",
                    embedding_types=["float"],
                )
                try:
                    return [d for d in res.embeddings.float], total_token_count_from_response(res)
                except Exception as _e:
                    log_exception(_e, res)
                    raise Exception(f"Error: {res}")

            try:
                batch_res, batch_tokens = self._run_with_retry(encode_batch)
                ress.extend(batch_res)
                token_count += batch_tokens
            except Exception as e:
                log_exception(e)
                raise
        return np.array(ress), token_count

    def encode_queries(self, text):
        res = self.client.embed(
            texts=[text],
            model=self.model_name,
            input_type="search_query",
            embedding_types=["float"],
        )
        try:
            return np.array(res.embeddings.float[0]), int(total_token_count_from_response(res))
        except Exception as _e:
            log_exception(_e, res)
            raise Exception(f"Error: {res}")


class TogetherAIEmbed(OpenAIEmbed):
    _FACTORY_NAME = "TogetherAI"

    def __init__(self, key, model_name, base_url="https://api.together.xyz/v1"):
        if not base_url:
            base_url = "https://api.together.xyz/v1"
        super().__init__(key, model_name, base_url=base_url)


class PerfXCloudEmbed(OpenAIEmbed):
    _FACTORY_NAME = "PerfXCloud"

    def __init__(self, key, model_name, base_url="https://cloud.perfxlab.cn/v1"):
        if not base_url:
            base_url = "https://cloud.perfxlab.cn/v1"
        super().__init__(key, model_name, base_url)


class UpstageEmbed(OpenAIEmbed):
    _FACTORY_NAME = "Upstage"

    def __init__(self, key, model_name, base_url="https://api.upstage.ai/v1/solar"):
        if not base_url:
            base_url = "https://api.upstage.ai/v1/solar"
        super().__init__(key, model_name, base_url)


class SILICONFLOWEmbed(Base):
    _FACTORY_NAME = "SILICONFLOW"

    def __init__(self, key, model_name, base_url="https://api.siliconflow.cn/v1/embeddings"):
        normalized_base_url = (base_url or "").strip()
        if not normalized_base_url:
            normalized_base_url = "https://api.siliconflow.cn/v1/embeddings"
        if "/embeddings" not in normalized_base_url:
            normalized_base_url = urljoin(f"{normalized_base_url.rstrip('/')}/", "embeddings").rstrip("/")
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {key}",
        }
        self.base_url = normalized_base_url
        self.model_name = model_name

    def encode(self, texts: list):
        batch_size = 16
        ress = []
        token_count = 0
        for i in range(0, len(texts), batch_size):
            texts_batch = texts[i : i + batch_size]
            if self.model_name in ["BAAI/bge-large-zh-v1.5", "BAAI/bge-large-en-v1.5"]:
                # limit 512, 340 is almost safe
                texts_batch = [" " if not text.strip() else truncate(text, 256) for text in texts_batch]
            else:
                texts_batch = [" " if not text.strip() else text for text in texts_batch]

            payload = {
                "model": self.model_name,
                "input": texts_batch,
                "encoding_format": "float",
            }
            response = httpx.post(self.base_url, json=payload, headers=self.headers)
            try:
                res = response.json()
                ress.extend([d["embedding"] for d in res["data"]])
                token_count += total_token_count_from_response(res)
            except Exception as _e:
                log_exception(_e, response)
                raise Exception(f"Error: {response}")

        return np.array(ress), token_count

    def encode_queries(self, text):
        payload = {
            "model": self.model_name,
            "input": text,
            "encoding_format": "float",
        }
        response = httpx.post(self.base_url, json=payload, headers=self.headers)
        try:
            res = response.json()
            return np.array(res["data"][0]["embedding"]), total_token_count_from_response(res)
        except Exception as _e:
            log_exception(_e, response)
            raise Exception(f"Error: {response}")


class ReplicateEmbed(Base):
    _FACTORY_NAME = "Replicate"

    def __init__(self, key, model_name, base_url=None):
        super().__init__(key, model_name)
        self.model_name = model_name
        self.client = replicate.Client(api_token=key)

    def encode(self, texts: list):
        batch_size = 16
        token_count = sum([num_tokens_from_string(text) for text in texts])
        ress = []
        for i in range(0, len(texts), batch_size):

            def encode_batch():
                return self.client.run(self.model_name, input={"texts": texts[i : i + batch_size]})

            try:
                batch_res = self._run_with_retry(encode_batch)
                ress.extend(batch_res)
            except Exception as e:
                log_exception(e)
                raise
        return np.array(ress), token_count

    def encode_queries(self, text):
        res = self.client.embed(self.model_name, input={"texts": [text]})
        return np.array(res), num_tokens_from_string(text)


class BaiduYiyanEmbed(Base):
    _FACTORY_NAME = "BaiduYiyan"

    def __init__(self, key, model_name, base_url=None):
        import qianfan

        key = json.loads(key)
        ak = key.get("yiyan_ak", "")
        sk = key.get("yiyan_sk", "")
        self.client = qianfan.Embedding(ak=ak, sk=sk)
        self.model_name = model_name

    def encode(self, texts: list, batch_size=16):
        res = self.client.do(model=self.model_name, texts=texts).body
        try:
            return (
                np.array([r["embedding"] for r in res["data"]]),
                total_token_count_from_response(res),
            )
        except Exception as _e:
            log_exception(_e, res)
            raise Exception(f"Error: {res}")

    def encode_queries(self, text):
        res = self.client.do(model=self.model_name, texts=[text]).body
        try:
            return (
                np.array([r["embedding"] for r in res["data"]]),
                total_token_count_from_response(res),
            )
        except Exception as _e:
            log_exception(_e, res)
            raise Exception(f"Error: {res}")


class VoyageEmbed(Base):
    _FACTORY_NAME = "Voyage AI"

    def __init__(self, key, model_name, base_url=None):
        import voyageai

        self.client = voyageai.Client(api_key=key)
        self.model_name = model_name

    def encode(self, texts: list):
        batch_size = 16
        ress = []
        token_count = 0
        for i in range(0, len(texts), batch_size):

            def encode_batch():
                res = self.client.embed(texts=texts[i : i + batch_size], model=self.model_name, input_type="document")
                try:
                    return res.embeddings, res.total_tokens
                except Exception as _e:
                    log_exception(_e, res)
                    raise Exception(f"Error: {res}")

            try:
                batch_res, batch_tokens = self._run_with_retry(encode_batch)
                ress.extend(batch_res)
                token_count += batch_tokens
            except Exception as e:
                log_exception(e)
                raise
        return np.array(ress), token_count

    def encode_queries(self, text):
        res = self.client.embed(texts=text, model=self.model_name, input_type="query")
        try:
            return np.array(res.embeddings)[0], res.total_tokens
        except Exception as _e:
            log_exception(_e, res)
            raise Exception(f"Error: {res}")


class HuggingFaceEmbed(Base):
    _FACTORY_NAME = "HuggingFace"

    def __init__(self, key, model_name, base_url=None, **kwargs):
        super().__init__(key, model_name, **kwargs)
        if not model_name:
            raise ValueError("Model name cannot be None")
        self.key = key
        self.model_name = model_name.split("___")[0]
        self.base_url = base_url or "http://127.0.0.1:8080"

    def encode(self, texts: list):
        def encode_batch():
            response = requests.post(f"{self.base_url}/embed", json={"inputs": texts}, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Error: {response.status_code} - {response.text}")

        try:
            embeddings = self._run_with_retry(encode_batch)
            return np.array(embeddings), sum([num_tokens_from_string(text) for text in texts])
        except Exception as e:
            log_exception(e)
            raise

    def encode_queries(self, text: str):
        response = requests.post(f"{self.base_url}/embed", json={"inputs": text}, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            embedding = response.json()[0]
            return np.array(embedding), num_tokens_from_string(text)
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")


class VolcEngineEmbed(Base):
    _FACTORY_NAME = "VolcEngine"

    def __init__(self, key, model_name, base_url="https://ark.cn-beijing.volces.com/api/v3"):
        super().__init__(key, model_name)
        if not base_url:
            base_url = "https://ark.cn-beijing.volces.com/api/v3"
        self.base_url = base_url

        cfg = json.loads(key)
        self.ark_api_key = cfg.get("ark_api_key", "")
        self.model_name = model_name

    @staticmethod
    def _extract_embedding(result: dict) -> list[float]:
        if not isinstance(result, dict):
            raise TypeError(f"Unexpected response type: {type(result)}")

        data = result.get("data")
        if data is None:
            raise KeyError("Missing 'data' in response")

        if isinstance(data, list):
            if not data:
                raise ValueError("Empty 'data' in response")
            item = data[0]
        elif isinstance(data, dict):
            item = data
        else:
            raise TypeError(f"Unexpected 'data' type: {type(data)}")

        if not isinstance(item, dict):
            raise TypeError("Unexpected item shape in 'data'")
        if "embedding" not in item:
            raise KeyError("Missing 'embedding' in response item")
        return item["embedding"]

    def _encode_texts(self, texts: list[str]):
        from common.http_client import sync_request

        url = f"{self.base_url}/embeddings/multimodal"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.ark_api_key}"}

        ress: list[list[float]] = []
        total_tokens = 0
        for text in texts:
            request_body = {"model": self.model_name, "input": [{"type": "text", "text": text}]}
            response = sync_request(method="POST", url=url, headers=headers, json=request_body, timeout=60)
            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code} - {response.text}")
            result = response.json()
            try:
                ress.append(self._extract_embedding(result))
                total_tokens += total_token_count_from_response(result)
            except Exception as _e:
                log_exception(_e)

        return np.array(ress), total_tokens

    def encode(self, texts: list):
        return self._encode_texts(texts)

    def encode_queries(self, text: str):
        embeddings, tokens = self._encode_texts([text])
        return embeddings[0], tokens


class GPUStackEmbed(OpenAIEmbed):
    _FACTORY_NAME = "GPUStack"

    def __init__(self, key, model_name, base_url):
        if not base_url:
            raise ValueError("url cannot be None")
        base_url = urljoin(base_url, "v1")
        super().__init__(key, model_name, base_url=base_url)
        self.base_url = base_url
        self.client = OpenAI(api_key=key, base_url=base_url)
        self.model_name = model_name


class NovitaEmbed(SILICONFLOWEmbed):
    _FACTORY_NAME = "NovitaAI"

    def __init__(self, key, model_name, base_url="https://api.novita.ai/v3/openai/embeddings"):
        if not base_url:
            base_url = "https://api.novita.ai/v3/openai/embeddings"
        super().__init__(key, model_name, base_url)


class GiteeEmbed(SILICONFLOWEmbed):
    _FACTORY_NAME = "GiteeAI"

    def __init__(self, key, model_name, base_url="https://ai.gitee.com/v1/embeddings"):
        if not base_url:
            base_url = "https://ai.gitee.com/v1/embeddings"
        super().__init__(key, model_name, base_url)


class DeepInfraEmbed(OpenAIEmbed):
    _FACTORY_NAME = "DeepInfra"

    def __init__(self, key, model_name, base_url="https://api.deepinfra.com/v1/openai"):
        if not base_url:
            base_url = "https://api.deepinfra.com/v1/openai"
        super().__init__(key, model_name, base_url)


class Ai302Embed(Base):
    _FACTORY_NAME = "302.AI"

    def __init__(self, key, model_name, base_url="https://api.302.ai/v1/embeddings"):
        if not base_url:
            base_url = "https://api.302.ai/v1/embeddings"
        super().__init__(key, model_name)
        self.base_url = base_url


class CometAPIEmbed(OpenAIEmbed):
    _FACTORY_NAME = "CometAPI"

    def __init__(self, key, model_name, base_url="https://api.cometapi.com/v1"):
        if not base_url:
            base_url = "https://api.cometapi.com/v1"
        super().__init__(key, model_name, base_url)


class DeerAPIEmbed(OpenAIEmbed):
    _FACTORY_NAME = "DeerAPI"

    def __init__(self, key, model_name, base_url="https://api.deerapi.com/v1"):
        if not base_url:
            base_url = "https://api.deerapi.com/v1"
        super().__init__(key, model_name, base_url)


class JiekouAIEmbed(OpenAIEmbed):
    _FACTORY_NAME = "Jiekou.AI"

    def __init__(self, key, model_name, base_url="https://api.jiekou.ai/openai/v1/embeddings"):
        if not base_url:
            base_url = "https://api.jiekou.ai/openai/v1/embeddings"
        super().__init__(key, model_name, base_url)


class RAGconEmbed(OpenAIEmbed):
    """
    RAGcon Embedding Provider - routes through LiteLLM proxy

    Default Base URL: https://connect.ragcon.ai/v1
    """

    _FACTORY_NAME = "RAGcon"

    def __init__(self, key, model_name="text-embedding-3-small", base_url=None):
        if not base_url:
            base_url = "https://connect.ragcon.com/v1"

        super().__init__(key, model_name, base_url)


class PerplexityEmbed(Base):
    _FACTORY_NAME = "Perplexity"

    def __init__(self, key, model_name="pplx-embed-v1-0.6b", base_url="https://api.perplexity.ai"):
        if not base_url:
            base_url = "https://api.perplexity.ai"
        self.base_url = base_url.rstrip("/")
        self.api_key = key
        self.model_name = model_name
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    @staticmethod
    def _decode_base64_int8(b64_str):
        raw = base64.b64decode(b64_str)
        return np.frombuffer(raw, dtype=np.int8).astype(np.float32)

    def _is_contextualized(self):
        return "context" in self.model_name

    def encode(self, texts: list):
        batch_size = 512
        ress = []
        token_count = 0

        if self._is_contextualized():
            url = f"{self.base_url}/v1/contextualizedembeddings"
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                payload = {
                    "model": self.model_name,
                    "input": [[chunk] for chunk in batch],
                    "encoding_format": "base64_int8",
                }
                response = httpx.post(url, headers=self.headers, json=payload)
                try:
                    res = response.json()
                    for doc in res["data"]:
                        for chunk_emb in doc["data"]:
                            ress.append(self._decode_base64_int8(chunk_emb["embedding"]))
                    token_count += res.get("usage", {}).get("total_tokens", 0)
                except Exception as _e:
                    log_exception(_e, response)
                    raise Exception(f"Error: {response.text}")
        else:
            url = f"{self.base_url}/v1/embeddings"
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                payload = {
                    "model": self.model_name,
                    "input": batch,
                    "encoding_format": "base64_int8",
                }
                response = httpx.post(url, headers=self.headers, json=payload)
                try:
                    res = response.json()
                    for d in res["data"]:
                        ress.append(self._decode_base64_int8(d["embedding"]))
                    token_count += res.get("usage", {}).get("total_tokens", 0)
                except Exception as _e:
                    log_exception(_e, response)
                    raise Exception(f"Error: {response.text}")

        return np.array(ress), token_count

    def encode_queries(self, text):
        embds, cnt = self.encode([text])
        return np.array(embds[0]), cnt
