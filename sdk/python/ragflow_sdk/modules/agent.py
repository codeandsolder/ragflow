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
from .exceptions import APIError


class Agent(Base):
    """Represents an agent in RAGFlow.

    An agent is a customizable workflow that can be designed using a DSL
    (Domain Specific Language) and executed to perform complex tasks.

    Attributes:
        id: Unique identifier of the agent.
        avatar: Avatar URL or base64 string.
        canvas_type: Type of canvas used for agent design.
        description: Description of the agent.
        dsl: Agent definition specification containing workflow and configuration.

    Example:
        >>> agents = ragflow.list_agents()
        >>> agent = agents[0]
        >>> session = agent.create_session()
    """

    def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
        """Initialize an Agent object.

        Args:
            rag: Reference to the RAGFlow client.
            res_dict: Dictionary containing agent data from API response.
        """
        self.id = None
        self.avatar = None
        self.canvas_type = None
        self.description = None
        self.dsl = None
        super().__init__(rag, res_dict)

    class Dsl(Base):
        """DSL (Domain Specific Language) configuration for an agent.

        Attributes:
            answer: List of answer components.
            components: Dictionary of workflow components.
            graph: Graph representation of the agent workflow.
            history: Conversation history.
            messages: List of messages.
            path: Execution path.
            reference: Reference data for retrieval.
        """

        def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
            self.answer = []
            self.components = {"begin": {"downstream": ["Answer:China"], "obj": {"component_name": "Begin", "params": {}}, "upstream": []}}
            self.graph = {
                "edges": [],
                "nodes": [{"data": {"label": "Begin", "name": "begin"}, "id": "begin", "position": {"x": 50, "y": 200}, "sourcePosition": "left", "targetPosition": "right", "type": "beginNode"}],
            }
            self.history = []
            self.messages = []
            self.path = []
            self.reference = []
            super().__init__(rag, res_dict)

    def create_session(self, **kwargs) -> Session:
        """Create a new agent session.

        Args:
            **kwargs: Additional parameters to pass when creating the session.

        Returns:
            Session: The created Session object.

        Raises:
            APIError: If session creation fails.
        """
        res = self.post(f"/agents/{self.id}/sessions", json=kwargs)
        res = res.json()
        if res.get("code") == 0:
            return Session(self.rag, res.get("data"))
        raise APIError(res.get("message"))

    def list_sessions(self, page: int = 1, page_size: int = 30, orderby: str = "create_time", desc: bool = True, id: str = None) -> list[Session]:
        """List agent sessions with pagination and filtering.

        Args:
            page: Page number (default: 1).
            page_size: Number of items per page (default: 30).
            orderby: Field to order by (default: 'create_time').
            desc: Sort in descending order (default: True).
            id: Filter by session ID.

        Returns:
            list[Session]: List of Session objects.

        Raises:
            APIError: If listing fails.
        """
        res = self.get(f"/agents/{self.id}/sessions", {"page": page, "page_size": page_size, "orderby": orderby, "desc": desc, "id": id})
        res = res.json()
        if res.get("code") == 0:
            result_list = []
            for data in res.get("data"):
                temp_agent = Session(self.rag, data)
                result_list.append(temp_agent)
            return result_list
        raise APIError(res.get("message"))

    def delete_sessions(self, ids: list[str] | None = None, delete_all: bool = False):
        """Delete agent sessions.

        Args:
            ids: List of session IDs to delete.
            delete_all: If True, delete all sessions (ignores ids).

        Raises:
            APIError: If deletion fails.
        """
        payload = {"ids": ids}
        if delete_all:
            payload["delete_all"] = True
        res = self.rm(f"/agents/{self.id}/sessions", payload)
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res.get("message"))
