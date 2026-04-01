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
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ragflow_sdk.ragflow import RAGFlow


from .base import Base
from .session import Session
from .exceptions import RAGFlowError, APIError


class Chat(Base):
    """Represents a chat assistant in RAGFlow.

    A chat provides conversational interface to query the knowledge base
    using RAG (Retrieval-Augmented Generation).

    Attributes:
        id: Unique identifier of the chat.
        name: Name of the chat assistant.
        avatar: Avatar URL or base64 string.
        llm: LLM configuration for this chat.
        prompt: Prompt configuration for generating responses.

    Example:
        >>> chats = ragflow.list_chats()
        >>> chat = chats[0]
        >>> session = chat.create_session("New Session")
    """

    def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
        self.id = ""
        self.name = "assistant"
        self.avatar = "path/to/avatar"
        self.llm = Chat.LLM(rag, None)
        self.prompt = Chat.Prompt(rag, None)
        super().__init__(rag, res_dict)

    class LLM(Base):
        """LLM (Large Language Model) configuration for a chat.

        Attributes:
            model_name: Name of the LLM model to use.
            temperature: Sampling temperature for response generation (default: 0.1).
            top_p: Nucleus sampling parameter (default: 0.3).
            presence_penalty: Penalty for token presence (default: 0.4).
            frequency_penalty: Penalty for token frequency (default: 0.7).
            max_tokens: Maximum number of tokens in response (default: 512).
        """

        def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
            self.model_name = None
            self.temperature = 0.1
            self.top_p = 0.3
            self.presence_penalty = 0.4
            self.frequency_penalty = 0.7
            self.max_tokens = 512
            super().__init__(rag, res_dict)

    class Prompt(Base):
        """Prompt configuration for generating responses.

        Attributes:
            similarity_threshold: Minimum similarity for retrieved chunks (default: 0.2).
            keywords_similarity_weight: Weight of keyword vs vector similarity (default: 0.7).
            top_n: Number of top chunks to consider (default: 8).
            top_k: Maximum tokens to retrieve (default: 1024).
            variables: List of prompt variables with their optional status.
            rerank_model: Rerank model ID for result reranking.
            empty_response: Response template for empty results.
            opener: Opening message for the chat.
            show_quote: Whether to show citations/quotes in responses (default: True).
            prompt: The actual prompt template string.
        """

        def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
            self.similarity_threshold = 0.2
            self.keywords_similarity_weight = 0.7
            self.top_n = 8
            self.top_k = 1024
            self.variables = [{"key": "knowledge", "optional": True}]
            self.rerank_model = ""
            self.empty_response = None
            self.opener = "Hi! I'm your assistant. What can I do for you?"
            self.show_quote = True
            self.prompt = (
                "You are an intelligent assistant. Your primary function is to answer questions based strictly on the provided knowledge base."
                "**Essential Rules:**"
                "- Your answer must be derived **solely** from this knowledge base: `{knowledge}`."
                "- **When information is available**: Summarize the content to give a detailed answer."
                "- **When information is unavailable**: Your response must contain this exact sentence: 'The answer you are looking for is not found in the knowledge base!' "
                "- **Always consider** the entire conversation history."
            )
            super().__init__(rag, res_dict)

    def update(self, update_message: dict) -> "Chat":
        """Update the chat configuration.

        Args:
            update_message: Dictionary containing fields to update (must include 'llm' and/or 'prompt').

        Returns:
            Chat: The updated Chat object.

        Raises:
            RAGFlowError: If update_message is not a dict or has empty llm/prompt.
            APIError: If the update fails.
        """
        if not isinstance(update_message, dict):
            raise RAGFlowError("`update_message` must be a dict")
        if update_message.get("llm") == {}:
            raise RAGFlowError("`llm` cannot be empty")
        if update_message.get("prompt") == {}:
            raise RAGFlowError("`prompt` cannot be empty")
        res = self.put(f"/chats/{self.id}", update_message)
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])
        self._update_from_dict(self.rag, res.get("data", {}))
        return self

    def create_session(self, name: str = "New session") -> Session:
        """Create a new chat session.

        Args:
            name: Name for the new session (default: "New session").

        Returns:
            Session: The created Session object.

        Raises:
            APIError: If session creation fails.
        """
        res = self.post(f"/chats/{self.id}/sessions", {"name": name})
        res = res.json()
        if res.get("code") == 0:
            return Session(self.rag, res["data"])
        raise APIError(res["message"])

    def list_sessions(self, page: int = 1, page_size: int = 30, orderby: str = "create_time", desc: bool = True, id: str = None, name: str = None) -> list[Session]:
        """List chat sessions with pagination and filtering.

        Args:
            page: Page number (default: 1).
            page_size: Number of items per page (default: 30).
            orderby: Field to order by (default: 'create_time').
            desc: Sort in descending order (default: True).
            id: Filter by session ID.
            name: Filter by session name.

        Returns:
            list[Session]: List of Session objects.

        Raises:
            APIError: If listing fails.
        """
        res = self.get(f"/chats/{self.id}/sessions", {"page": page, "page_size": page_size, "orderby": orderby, "desc": desc, "id": id, "name": name})
        res = res.json()
        if res.get("code") == 0:
            result_list = []
            for data in res["data"]:
                result_list.append(Session(self.rag, data))
            return result_list
        raise APIError(res["message"])

    def delete_sessions(self, ids: list[str] | None = None, delete_all: bool = False):
        """Delete chat sessions.

        Args:
            ids: List of session IDs to delete.
            delete_all: If True, delete all sessions (ignores ids).

        Raises:
            APIError: If deletion fails.
        """
        res = self.rm(f"/chats/{self.id}/sessions", {"ids": ids, "delete_all": delete_all})
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res.get("message"))
