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

from typing import Optional, Any

import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

from .exceptions import RAGFlowError, APIError, NetworkError, AuthenticationError
from .modules.agent import Agent
from .modules.chat import Chat
from .modules.chunk import Chunk


# HTTP status code constants
HTTP_OK_MIN = 200
HTTP_OK_MAX = 300
HTTP_AUTH_ERROR = 401
HTTP_SERVER_ERROR_MIN = 500

# Retry configuration defaults
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0

# API response codes
API_SUCCESS_CODE = 0
from .modules.dataset import DataSet
from .modules.memory import Memory


def _retry_with_backoff(max_retries=3, backoff_factor=1.0, retry_on_exceptions=(ConnectionError, Timeout, RequestException)):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retry_on_exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        import time

                        sleep_time = backoff_factor * (2**attempt)
                        time.sleep(sleep_time)
                    else:
                        raise NetworkError(f"Request failed after {max_retries} attempts: {str(e)}")
            raise last_exception

        return wrapper

    return decorator


class RAGFlow:
    """Main client class for interacting with the RAGFlow API.

    This class provides methods for managing datasets, chats, agents, and performing
    retrieval operations. It handles authentication, session management, and HTTP requests
    with automatic retry logic.

    Attributes:
        user_key: The API key used for authentication.
        api_url: The base URL for the RAGFlow API.
        authorization_header: Authorization header for API requests.
        _session: Internal requests Session object for connection pooling.

    Example:
        >>> from ragflow_sdk import RAGFlow
        >>> ragflow = RAGFlow(api_key='your-api-key', base_url='http://localhost:9380')
        >>> datasets = ragflow.list_datasets()
    """

    def __init__(self, api_key, base_url, version="v1"):
        """Initialize a RAGFlow client.

        Args:
            api_key: The API key for authentication.
            base_url: The base URL of the RAGFlow server (e.g., 'http://localhost:9380').
            version: API version to use (default: 'v1').
        """
        self.user_key = api_key
        self.api_url = f"{base_url}/api/{version}"
        self.authorization_header = {"Authorization": f"Bearer {self.user_key}"}
        self._session = None

    @property
    def session(self):
        """Get or create a requests Session for connection pooling.

        Returns:
            A requests Session object with authorization headers configured.
        """
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(self.authorization_header)
        return self._session

    def __enter__(self):
        """Context manager entry point.

        Returns:
            The RAGFlow instance.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point - closes the session."""
        self.close()
        return False

    def close(self):
        """Close the HTTP session and release resources."""
        if self._session is not None:
            self._session.close()
            self._session = None

    @_retry_with_backoff(max_retries=DEFAULT_MAX_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR)
    def post(self, path, json=None, stream=False, files=None):
        """Send a POST request to the RAGFlow API.

        Args:
            path: API endpoint path.
            json: JSON payload for the request.
            stream: Whether to stream the response.
            files: Files to upload.

        Returns:
            Response object from the server.

        Raises:
            AuthenticationError: If authentication fails.
            APIError: If the server returns an error.
            NetworkError: If the request fails after retries.
        """
        res = self.session.post(url=self.api_url + path, json=json, headers=self.authorization_header, stream=stream, files=files)
        if not (HTTP_OK_MIN <= res.status_code < HTTP_OK_MAX):
            if res.status_code == HTTP_AUTH_ERROR:
                raise AuthenticationError("Authentication failed. Please check your API key.", details={"status_code": res.status_code})
            elif res.status_code >= HTTP_SERVER_ERROR_MIN:
                raise APIError(f"Server error: {res.status_code}", status_code=res.status_code)
            else:
                try:
                    error_body = res.json()
                    raise APIError(error_body.get("message", f"Request failed with status {res.status_code}"), status_code=res.status_code, details=error_body)
                except requests.JSONDecodeError:
                    raise APIError(f"Request failed with status {res.status_code}", status_code=res.status_code)
        return res

    @_retry_with_backoff(max_retries=DEFAULT_MAX_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR)
    def get(self, path, params=None, json=None):
        """Send a GET request to the RAGFlow API.

        Args:
            path: API endpoint path.
            params: Query parameters for the request.
            json: Optional JSON payload.

        Returns:
            Response object from the server.

        Raises:
            AuthenticationError: If authentication fails.
            APIError: If the server returns an error.
            NetworkError: If the request fails after retries.
        """
        res = self.session.get(url=self.api_url + path, params=params, headers=self.authorization_header, json=json)
        if not (HTTP_OK_MIN <= res.status_code < HTTP_OK_MAX):
            if res.status_code == HTTP_AUTH_ERROR:
                raise AuthenticationError("Authentication failed. Please check your API key.", details={"status_code": res.status_code})
            elif res.status_code >= HTTP_SERVER_ERROR_MIN:
                raise APIError(f"Server error: {res.status_code}", status_code=res.status_code)
            else:
                try:
                    error_body = res.json()
                    raise APIError(error_body.get("message", f"Request failed with status {res.status_code}"), status_code=res.status_code, details=error_body)
                except requests.JSONDecodeError:
                    raise APIError(f"Request failed with status {res.status_code}", status_code=res.status_code)
        return res

    @_retry_with_backoff(max_retries=DEFAULT_MAX_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR)
    def delete(self, path, json):
        """Send a DELETE request to the RAGFlow API.

        Args:
            path: API endpoint path.
            json: JSON payload for the request.

        Returns:
            Response object from the server.

        Raises:
            AuthenticationError: If authentication fails.
            APIError: If the server returns an error.
            NetworkError: If the request fails after retries.
        """
        res = self.session.delete(url=self.api_url + path, json=json, headers=self.authorization_header)
        if not (HTTP_OK_MIN <= res.status_code < HTTP_OK_MAX):
            if res.status_code == HTTP_AUTH_ERROR:
                raise AuthenticationError("Authentication failed. Please check your API key.", details={"status_code": res.status_code})
            elif res.status_code >= HTTP_SERVER_ERROR_MIN:
                raise APIError(f"Server error: {res.status_code}", status_code=res.status_code)
            else:
                try:
                    error_body = res.json()
                    raise APIError(error_body.get("message", f"Request failed with status {res.status_code}"), status_code=res.status_code, details=error_body)
                except requests.JSONDecodeError:
                    raise APIError(f"Request failed with status {res.status_code}", status_code=res.status_code)
        return res

    @_retry_with_backoff(max_retries=DEFAULT_MAX_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR)
    def put(self, path, json):
        """Send a PUT request to the RAGFlow API.

        Args:
            path: API endpoint path.
            json: JSON payload for the request.

        Returns:
            Response object from the server.

        Raises:
            AuthenticationError: If authentication fails.
            APIError: If the server returns an error.
            NetworkError: If the request fails after retries.
        """
        res = self.session.put(url=self.api_url + path, json=json, headers=self.authorization_header)
        if not (HTTP_OK_MIN <= res.status_code < HTTP_OK_MAX):
            if res.status_code == HTTP_AUTH_ERROR:
                raise AuthenticationError("Authentication failed. Please check your API key.", details={"status_code": res.status_code})
            elif res.status_code >= HTTP_SERVER_ERROR_MIN:
                raise APIError(f"Server error: {res.status_code}", status_code=res.status_code)
            else:
                try:
                    error_body = res.json()
                    raise APIError(error_body.get("message", f"Request failed with status {res.status_code}"), status_code=res.status_code, details=error_body)
                except requests.JSONDecodeError:
                    raise APIError(f"Request failed with status {res.status_code}", status_code=res.status_code)
        return res

    def create_dataset(
        self,
        name: str,
        avatar: Optional[str] = None,
        description: Optional[str] = None,
        embedding_model: Optional[str] = None,
        permission: str = "me",
        chunk_method: str = "naive",
        parser_config: Optional[DataSet.ParserConfig] = None,
        auto_metadata_config: Optional[dict[str, Any]] = None,
    ) -> DataSet:
        """Create a new dataset.

        Args:
            name: Name of the dataset.
            avatar: Optional avatar URL or base64 string.
            description: Optional description of the dataset.
            embedding_model: Optional embedding model to use.
            permission: Access permission (default: 'me').
            chunk_method: Method for chunking documents (default: 'naive').
            parser_config: Optional parser configuration.
            auto_metadata_config: Optional auto-metadata configuration.

        Returns:
            DataSet: The created dataset object.

        Raises:
            APIError: If the creation fails.
        """
        payload = {
            "name": name,
            "avatar": avatar,
            "description": description,
            "embedding_model": embedding_model,
            "permission": permission,
            "chunk_method": chunk_method,
        }
        if parser_config is not None:
            payload["parser_config"] = parser_config.to_json()
        if auto_metadata_config is not None:
            payload["auto_metadata_config"] = auto_metadata_config

        res = self.post("/datasets", payload)
        res = res.json()
        if res.get("code") == API_SUCCESS_CODE:
            return DataSet(self, res["data"])
        raise APIError(res["message"])

    def delete_datasets(self, ids: list[str] | None = None, delete_all: bool = False):
        """Delete datasets by IDs or delete all datasets.

        Args:
            ids: List of dataset IDs to delete.
            delete_all: If True, delete all datasets (ignores ids).

        Raises:
            APIError: If deletion fails.
        """
        res = self.delete("/datasets", {"ids": ids, "delete_all": delete_all})
        res = res.json()
        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])

    def get_dataset(self, name: str):
        """Get a dataset by name.

        Args:
            name: Name of the dataset to retrieve.

        Returns:
            DataSet: The dataset object.

        Raises:
            RAGFlowError: If dataset is not found.
        """
        _list = self.list_datasets(name=name)
        if len(_list) > 0:
            return _list[0]
        raise RAGFlowError("Dataset %s not found" % name)

    def list_datasets(self, page: int = 1, page_size: int = 30, orderby: str = "create_time", desc: bool = True, id: str | None = None, name: str | None = None) -> list[DataSet]:
        """List datasets with pagination and filtering options.

        Args:
            page: Page number (default: 1).
            page_size: Number of items per page (default: 30).
            orderby: Field to order by (default: 'create_time').
            desc: Sort in descending order (default: True).
            id: Filter by dataset ID.
            name: Filter by dataset name (supports partial match).

        Returns:
            list[DataSet]: List of DataSet objects.
        """
        res = self.get(
            "/datasets",
            {
                "page": page,
                "page_size": page_size,
                "orderby": orderby,
                "desc": desc,
                "id": id,
                "name": name,
            },
        )
        res = res.json()
        result_list = []
        if res.get("code") == API_SUCCESS_CODE:
            for data in res["data"]:
                result_list.append(DataSet(self, data))
            return result_list
        raise APIError(res["message"])

    def create_chat(self, name: str, avatar: str = "", dataset_ids=None, llm: Chat.LLM | None = None, prompt: Chat.Prompt | None = None) -> Chat:
        """Create a new chat assistant.

        Args:
            name: Name of the chat assistant.
            avatar: Avatar URL or base64 string (default: empty string).
            dataset_ids: List of dataset IDs to attach to the chat.
            llm: Optional LLM configuration. If None, uses default settings.
            prompt: Optional prompt configuration. If None, uses default settings.

        Returns:
            Chat: The created Chat object.

        Raises:
            APIError: If creation fails.
        """
        if dataset_ids is None:
            dataset_ids = []
        dataset_list = []
        for id in dataset_ids:
            dataset_list.append(id)

        if llm is None:
            llm = Chat.LLM(
                self,
                {
                    "model_name": None,
                    "temperature": 0.1,
                    "top_p": 0.3,
                    "presence_penalty": 0.4,
                    "frequency_penalty": 0.7,
                    "max_tokens": 512,
                },
            )
        if prompt is None:
            prompt = Chat.Prompt(
                self,
                {
                    "similarity_threshold": 0.2,
                    "keywords_similarity_weight": 0.7,
                    "top_n": 8,
                    "top_k": 1024,
                    "variables": [{"key": "knowledge", "optional": True}],
                    "rerank_model": "",
                    "empty_response": None,
                    "opener": None,
                    "show_quote": True,
                    "prompt": None,
                },
            )
            if prompt.opener is None:
                prompt.opener = "Hi! I'm your assistant. What can I do for you?"
            if prompt.prompt is None:
                prompt.prompt = (
                    "You are an intelligent assistant. Your primary function is to answer questions based strictly on the provided knowledge base."
                    "**Essential Rules:**"
                    "- Your answer must be derived **solely** from this knowledge base: `{knowledge}`."
                    "- **When information is available**: Summarize the content to give a detailed answer."
                    "- **When information is unavailable**: Your response must contain this exact sentence: 'The answer you are looking for is not found in the knowledge base!' "
                    "- **Always consider** the entire conversation history."
                )

        temp_dict = {"name": name, "avatar": avatar, "dataset_ids": dataset_list if dataset_list else [], "llm": llm.to_json(), "prompt": prompt.to_json()}
        res = self.post("/chats", temp_dict)
        res = res.json()
        if res.get("code") == API_SUCCESS_CODE:
            return Chat(self, res["data"])
        raise APIError(res["message"])

    def delete_chats(self, ids: list[str] | None = None, delete_all: bool = False):
        """Delete chats by IDs or delete all chats.

        Args:
            ids: List of chat IDs to delete.
            delete_all: If True, delete all chats (ignores ids).

        Raises:
            APIError: If deletion fails.
        """
        res = self.delete("/chats", {"ids": ids, "delete_all": delete_all})
        res = res.json()
        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])

    def list_chats(self, page: int = 1, page_size: int = 30, orderby: str = "create_time", desc: bool = True, id: str | None = None, name: str | None = None) -> list[Chat]:
        """List chat assistants with pagination and filtering.

        Args:
            page: Page number (default: 1).
            page_size: Number of items per page (default: 30).
            orderby: Field to order by (default: 'create_time').
            desc: Sort in descending order (default: True).
            id: Filter by chat ID.
            name: Filter by chat name.

        Returns:
            list[Chat]: List of Chat objects.
        """
        res = self.get(
            "/chats",
            {
                "page": page,
                "page_size": page_size,
                "orderby": orderby,
                "desc": desc,
                "id": id,
                "name": name,
            },
        )
        res = res.json()
        result_list = []
        if res.get("code") == API_SUCCESS_CODE:
            for data in res["data"]:
                result_list.append(Chat(self, data))
            return result_list
        raise APIError(res["message"])

    def retrieve(
        self,
        dataset_ids,
        document_ids=None,
        question="",
        page=1,
        page_size=30,
        similarity_threshold=0.2,
        vector_similarity_weight=0.3,
        top_k=1024,
        rerank_id: str | None = None,
        keyword: bool = False,
        cross_languages: list[str] | None = None,
        metadata_condition: dict | None = None,
        use_kg: bool = False,
        toc_enhance: bool = False,
    ):
        """Perform retrieval-augmented generation over specified datasets.

        Args:
            dataset_ids: List of dataset IDs to search in.
            document_ids: Optional list of specific document IDs to search in.
            question: The query question to search for.
            page: Page number for pagination (default: 1).
            page_size: Number of results per page (default: 30).
            similarity_threshold: Minimum similarity threshold (default: 0.2).
            vector_similarity_weight: Weight of vector similarity vs keyword similarity (default: 0.3).
            top_k: Maximum number of chunks to retrieve (default: 1024).
            rerank_id: Optional rerank model ID to use for reranking results.
            keyword: Whether to use keyword search (default: False).
            cross_languages: Optional list of languages to search across.
            metadata_condition: Optional metadata filtering conditions.
            use_kg: Whether to use knowledge graph for retrieval (default: False).
            toc_enhance: Whether to enhance with table of contents (default: False).

        Returns:
            list[Chunk]: List of retrieved chunks with relevance scores.

        Raises:
            APIError: If retrieval fails.
        """
        if document_ids is None:
            document_ids = []
        data_json = {
            "page": page,
            "page_size": page_size,
            "similarity_threshold": similarity_threshold,
            "vector_similarity_weight": vector_similarity_weight,
            "top_k": top_k,
            "rerank_id": rerank_id,
            "keyword": keyword,
            "question": question,
            "dataset_ids": dataset_ids,
            "document_ids": document_ids,
            "cross_languages": cross_languages,
            "metadata_condition": metadata_condition,
            "use_kg": use_kg,
            "toc_enhance": toc_enhance,
        }
        # Send a POST request to the backend service (using requests library as an example, actual implementation may vary)
        res = self.post("/retrieval", json=data_json)
        res = res.json()
        if res.get("code") == API_SUCCESS_CODE:
            chunks = []
            for chunk_data in res["data"].get("chunks"):
                chunk = Chunk(self, chunk_data)
                chunks.append(chunk)
            return chunks
        raise APIError(res.get("message"))

    def list_agents(self, page: int = 1, page_size: int = 30, orderby: str = "update_time", desc: bool = True, id: str | None = None, title: str | None = None) -> list[Agent]:
        """List agents with pagination and filtering.

        Args:
            page: Page number (default: 1).
            page_size: Number of items per page (default: 30).
            orderby: Field to order by (default: 'update_time').
            desc: Sort in descending order (default: True).
            id: Filter by agent ID.
            title: Filter by agent title.

        Returns:
            list[Agent]: List of Agent objects.
        """
        res = self.get(
            "/agents",
            {
                "page": page,
                "page_size": page_size,
                "orderby": orderby,
                "desc": desc,
                "id": id,
                "title": title,
            },
        )
        res = res.json()
        result_list = []
        if res.get("code") == API_SUCCESS_CODE:
            for data in res["data"]:
                result_list.append(Agent(self, data))
            return result_list
        raise APIError(res["message"])

    def create_agent(self, title: str, dsl: dict, description: str | None = None) -> None:
        """Create a new agent.

        Args:
            title: Title/name of the agent.
            dsl: Agent definition specification (DSL) as a dictionary.
            description: Optional description of the agent.

        Raises:
            APIError: If creation fails.
        """
        req = {"title": title, "dsl": dsl}

        if description is not None:
            req["description"] = description

        res = self.post("/agents", req)
        res = res.json()

        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])

    def update_agent(self, agent_id: str, title: str | None = None, description: str | None = None, dsl: dict | None = None) -> None:
        """Update an existing agent.

        Args:
            agent_id: ID of the agent to update.
            title: New title for the agent (optional).
            description: New description for the agent (optional).
            dsl: New DSL specification for the agent (optional).

        Raises:
            APIError: If update fails.
        """
        req = {}

        if title is not None:
            req["title"] = title

        if description is not None:
            req["description"] = description

        if dsl is not None:
            req["dsl"] = dsl

        res = self.put(f"/agents/{agent_id}", req)
        res = res.json()

        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])

    def delete_agent(self, agent_id: str) -> None:
        """Delete an agent by ID.

        Args:
            agent_id: ID of the agent to delete.

        Raises:
            APIError: If deletion fails.
        """
        res = self.delete(f"/agents/{agent_id}", {})
        res = res.json()

        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])

    def create_memory(self, name: str, memory_type: list[str], embd_id: str, llm_id: str):
        """Create a new memory storage.

        Args:
            name: Name of the memory storage.
            memory_type: List of memory types (e.g., ['raw']).
            embd_id: Embedding model ID to use.
            llm_id: LLM model ID to use.

        Returns:
            Memory: The created Memory object.

        Raises:
            APIError: If creation fails.
        """
        payload = {"name": name, "memory_type": memory_type, "embd_id": embd_id, "llm_id": llm_id}
        res = self.post("/memories", payload)
        res = res.json()
        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])
        return Memory(self, res["data"])

    def list_memory(self, page: int = 1, page_size: int = 50, tenant_id: str | list[str] = None, memory_type: str | list[str] = None, storage_type: str = None, keywords: str = None) -> dict:
        """List memory storages with pagination and filtering.

        Args:
            page: Page number (default: 1).
            page_size: Number of items per page (default: 50).
            tenant_id: Filter by tenant ID(s).
            memory_type: Filter by memory type(s).
            storage_type: Filter by storage type.
            keywords: Filter by keywords in name/description.

        Returns:
            dict: Dictionary containing 'code', 'message', 'memory_list', and 'total_count'.
        """
        res = self.get(
            "/memories",
            {
                "page": page,
                "page_size": page_size,
                "tenant_id": tenant_id,
                "memory_type": memory_type,
                "storage_type": storage_type,
                "keywords": keywords,
            },
        )
        res = res.json()
        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])
        result_list = []
        for data in res["data"]["memory_list"]:
            result_list.append(Memory(self, data))
        return {"code": res.get("code", 0), "message": res.get("message"), "memory_list": result_list, "total_count": res["data"]["total_count"]}

    def delete_memory(self, memory_id: str):
        """Delete a memory storage by ID.

        Args:
            memory_id: ID of the memory storage to delete.

        Raises:
            APIError: If deletion fails.
        """
        res = self.delete(f"/memories/{memory_id}", {})
        res = res.json()
        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])

    def add_message(self, memory_id: str, agent_id: str, session_id: str, user_input: str, agent_response: str, user_id: str = "") -> str:
        """Add a message pair to memory.

        Args:
            memory_id: ID of the memory storage.
            agent_id: ID of the agent.
            session_id: ID of the session.
            user_input: User's input text.
            agent_response: Agent's response text.
            user_id: Optional user ID (default: empty string).

        Returns:
            str: Confirmation message from the server.

        Raises:
            APIError: If operation fails.
        """
        payload = {"memory_id": [memory_id], "agent_id": agent_id, "session_id": session_id, "user_input": user_input, "agent_response": agent_response, "user_id": user_id}
        res = self.post("/messages", payload)
        res = res.json()
        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])
        return res["message"]

    def search_message(
        self, query: str, memory_id: list[str], agent_id: str = None, session_id: str = None, similarity_threshold: float = 0.2, keywords_similarity_weight: float = 0.7, top_n: int = 10
    ) -> list[dict]:
        """Search messages in memory.

        Args:
            query: Search query text.
            memory_id: List of memory IDs to search in.
            agent_id: Filter by agent ID (optional).
            session_id: Filter by session ID (optional).
            similarity_threshold: Minimum similarity threshold (default: 0.2).
            keywords_similarity_weight: Weight of keywords vs vector similarity (default: 0.7).
            top_n: Number of results to return (default: 10).

        Returns:
            list[dict]: List of matching message data.

        Raises:
            APIError: If search fails.
        """
        params = {
            "query": query,
            "memory_id": memory_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "similarity_threshold": similarity_threshold,
            "keywords_similarity_weight": keywords_similarity_weight,
            "top_n": top_n,
        }
        res = self.get("/messages/search", params)
        res = res.json()
        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])
        return res["data"]

    def get_recent_messages(self, memory_id: list[str], agent_id: str = None, session_id: str = None, limit: int = 10) -> list[dict]:
        """Get recent messages from memory.

        Args:
            memory_id: List of memory IDs to retrieve from.
            agent_id: Filter by agent ID (optional).
            session_id: Filter by session ID (optional).
            limit: Maximum number of messages to return (default: 10).

        Returns:
            list[dict]: List of recent message data.

        Raises:
            APIError: If retrieval fails.
        """
        params = {"memory_id": memory_id, "agent_id": agent_id, "session_id": session_id, "limit": limit}
        res = self.get("/messages", params)
        res = res.json()
        if res.get("code") != API_SUCCESS_CODE:
            raise APIError(res["message"])
        return res["data"]
