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
from .exceptions import APIError


# Default maximum memory size: 5 MB
DEFAULT_MEMORY_SIZE = 5 * 1024 * 1024


class Memory(Base):
    """Represents a memory storage in RAGFlow.

    Memory stores conversation history and messages that can be used
    for context-aware responses and message retrieval.

    Attributes:
        id: Unique identifier of the memory storage.
        name: Name of the memory storage.
        avatar: Avatar URL or base64 string.
        tenant_id: ID of the tenant who owns this memory.
        owner_name: Name of the owner.
        memory_type: Types of memory (e.g., ['raw']).
        storage_type: Storage backend type.
        embd_id: Embedding model ID.
        llm_id: LLM model ID.
        permissions: Access permissions.
        description: Description of the memory.
        memory_size: Maximum size in bytes.
        forgetting_policy: Policy for forgetting old messages.
        temperature: Temperature setting for generation.
        system_prompt: System prompt for the memory.
        user_prompt: User prompt template.

    Example:
        >>> memories = ragflow.list_memory()
        >>> memory = memories["memory_list"][0]
        >>> messages = memory.list_memory_messages()
    """

    def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
        self.id = ""
        self.name = ""
        self.avatar = None
        self.tenant_id = None
        self.owner_name = ""
        self.memory_type = ["raw"]
        self.storage_type = "table"
        self.embd_id = ""
        self.llm_id = ""
        self.permissions = "me"
        self.description = ""
        self.memory_size = DEFAULT_MEMORY_SIZE
        self.forgetting_policy = "FIFO"
        self.temperature = 0.5
        self.system_prompt = ""
        self.user_prompt = ""
        for k in list(res_dict.keys()):
            if k not in self.__dict__:
                res_dict.pop(k)
        super().__init__(rag, res_dict)

    def update(self, update_dict: dict):
        """Update the memory storage configuration.

        Args:
            update_dict: Dictionary containing fields to update.

        Returns:
            Memory: The updated Memory object.

        Raises:
            APIError: If update fails.
        """
        res = self.put(f"/memories/{self.id}", update_dict)
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])
        self._update_from_dict(self.rag, res.get("data", {}))
        return self

    def get_config(self):
        """Retrieve the current memory configuration.

        Returns:
            Memory: The Memory object with updated configuration.

        Raises:
            APIError: If retrieval fails.
        """
        res = self.get(f"/memories/{self.id}/config")
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])
        self._update_from_dict(self.rag, res.get("data", {}))
        return self

    def list_memory_messages(self, agent_id: str | list[str] = None, keywords: str = None, page: int = 1, page_size: int = 50):
        """List messages stored in memory.

        Args:
            agent_id: Filter by agent ID(s).
            keywords: Filter by keywords.
            page: Page number (default: 1).
            page_size: Number of items per page (default: 50).

        Returns:
            dict: Message data from the API.

        Raises:
            APIError: If listing fails.
        """
        params = {"agent_id": agent_id, "keywords": keywords, "page": page, "page_size": page_size}
        res = self.get(f"/memories/{self.id}", params)
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])
        return res["data"]

    def forget_message(self, message_id: int):
        """Mark a message as forgotten/deleted.

        Args:
            message_id: ID of the message to forget.

        Returns:
            bool: True if successful.

        Raises:
            APIError: If operation fails.
        """
        res = self.rm(f"/messages/{self.id}:{message_id}", {})
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])
        return True

    def update_message_status(self, message_id: int, status: bool):
        """Update the status of a message.

        Args:
            message_id: ID of the message to update.
            status: New status boolean value.

        Returns:
            bool: True if successful.

        Raises:
            APIError: If update fails.
        """
        update_message = {"status": status}
        res = self.put(f"/messages/{self.id}:{message_id}", update_message)
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])
        return True

    def get_message_content(self, message_id: int) -> dict:
        """Get the content of a specific message.

        Args:
            message_id: ID of the message to retrieve.

        Returns:
            dict: Message content data.

        Raises:
            APIError: If retrieval fails.
        """
        res = self.get(f"/messages/{self.id}:{message_id}/content")
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])
        return res["data"]
