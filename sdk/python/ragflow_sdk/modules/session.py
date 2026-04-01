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

import json
import requests
from .base import Base
from ..exceptions import RAGFlowError, APIError


class Session(Base):
    """Represents a conversation session.

    A session maintains conversation history and provides methods for
    sending messages and receiving responses from a chat or agent.

    Attributes:
        id: Unique identifier of the session.
        name: Name of the session.
        messages: List of messages in the session.
        chat_id: ID of the parent chat (if this is a chat session).
        agent_id: ID of the parent agent (if this is an agent session).

    Example:
        >>> session = chat.create_session("My Session")
        >>> for message in session.ask("Hello!"):
        ...     print(message.content)
    """

    def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
        """Initialize a Session object.

        Args:
            rag: The RAGFlow client instance.
            res_dict: Dictionary containing session data from API response.
        """
        self.id = None
        self.name = "New session"
        self.messages = None
        self.chat_id = None
        self.agent_id = None
        self.__session_type = None
        super().__init__(rag, res_dict)

    def ask(self, question: str = "", stream: bool = False, **kwargs):
        """Ask a question to the session.

        If stream=True, yields Message objects as they arrive (SSE streaming).
        If stream=False, returns a single Message object for the final answer.

        Args:
            question: The question to ask the session.
            stream: Whether to use streaming mode. Default is False.
            **kwargs: Additional keyword arguments to pass to the API.

        Yields:
            Message: When stream=True, yields Message objects as they arrive.

        Returns:
            Message: When stream=False, returns a Message object with the final answer.

        Raises:
            RAGFlowError: If the session type is unknown or if streaming fails.
            APIError: If the API returns an error.
        """
        if self.__session_type == "agent":
            res = self._ask_agent(question, stream, **kwargs)
        elif self.__session_type == "chat":
            res = self._ask_chat(question, stream, **kwargs)
        else:
            raise RAGFlowError(f"Unknown session type: {self.__session_type}")

        if stream:
            try:
                for line in res.iter_lines(decode_unicode=True):
                    if not line:
                        continue  # Skip empty lines
                    line = line.strip()
                    if line.startswith("data:"):
                        content = line[len("data:") :].strip()
                        if content == "[DONE]":
                            break  # End of stream
                    else:
                        content = line

                    try:
                        json_data = json.loads(content)
                    except json.JSONDecodeError:
                        continue  # Skip lines that are not valid JSON

                    event = json_data.get("event", None)
                    if event and event != "message":
                        continue

                    if (self.__session_type == "agent" and event == "message_end") or (self.__session_type == "chat" and json_data.get("data") is True):
                        return
                    if self.__session_type == "agent":
                        yield self._structure_answer(json_data)
                    else:
                        yield self._structure_answer(json_data["data"])
            except (OSError, IOError, TimeoutError) as e:
                raise RAGFlowError(f"Stream failed: {str(e)}") from e
            finally:
                res.close()
        else:
            try:
                json_data = res.json()
            except ValueError:
                raise RAGFlowError(f"Invalid response {res}")
            yield self._structure_answer(json_data["data"])

    def _structure_answer(self, json_data: dict) -> Message:
        """Structure API response data into a Message object.

        Args:
            json_data: JSON data from the API response.

        Returns:
            Message: A Message object with the answer and optional reference.
        """
        answer = ""
        if self.__session_type == "agent":
            answer = json_data["data"]["content"]
        elif self.__session_type == "chat":
            answer = json_data["answer"]
        reference = json_data.get("reference", {})
        temp_dict = {"content": answer, "role": "assistant"}
        if reference and "chunks" in reference:
            chunks = reference["chunks"]
            temp_dict["reference"] = chunks
        message = Message(self.rag, temp_dict)
        return message

    def _ask_chat(self, question: str, stream: bool, **kwargs) -> requests.Response:
        """Send a question to a chat session.

        Args:
            question: The question to ask.
            stream: Whether to use streaming mode.
            **kwargs: Additional arguments for the API.

        Returns:
            requests.Response: The HTTP response from the API.
        """
        json_data = {"question": question, "stream": stream, "session_id": self.id}
        json_data.update(kwargs)
        res = self.post(f"/chats/{self.chat_id}/completions", json_data, stream=stream)
        return res

    def _ask_agent(self, question: str, stream: bool, **kwargs) -> requests.Response:
        """Send a question to an agent session.

        Args:
            question: The question to ask.
            stream: Whether to use streaming mode.
            **kwargs: Additional arguments for the API.

        Returns:
            requests.Response: The HTTP response from the API.
        """
        json_data = {"question": question, "stream": stream, "session_id": self.id}
        json_data.update(kwargs)
        res = self.post(f"/agents/{self.agent_id}/completions", json_data, stream=stream)
        return res

    def update(self, update_message: dict) -> None:
        """Update the session.

        Args:
            update_message: Dictionary containing fields to update.

        Raises:
            APIError: If update fails.
        """
        res = self.put(f"/chats/{self.chat_id}/sessions/{self.id}", update_message)
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res.get("message"))


class Message(Base):
    """Represents a message in a conversation.

    Attributes:
        content: The text content of the message.
        reference: Reference data (chunks) associated with the message.
        role: Role of the message sender ('user' or 'assistant').
        prompt: Optional prompt data.
        id: Unique identifier of the message.
    """

    def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
        """Initialize a Message object.

        Args:
            rag: The RAGFlow client instance.
            res_dict: Dictionary containing message data from API response.
        """
        self.content = "Hi! I am your assistant, can I help you?"
        self.reference = None
        self.role = "assistant"
        self.prompt = None
        self.id = None
        super().__init__(rag, res_dict)

    def _structure_answer(self, json_data: dict) -> "Message":
        """Structure API response data into a Message object.

        Args:
            json_data: JSON data from the API response.

        Returns:
            Message: A Message object with the answer and optional reference.
        """
        answer = ""
        if self.__session_type == "agent":
            answer = json_data["data"]["content"]
        elif self.__session_type == "chat":
            answer = json_data["answer"]
        reference = json_data.get("reference", {})
        temp_dict = {"content": answer, "role": "assistant"}
        if reference and "chunks" in reference:
            chunks = reference["chunks"]
            temp_dict["reference"] = chunks
        message = Message(self.rag, temp_dict)
        return message

    def _ask_chat(self, question: str, stream: bool, **kwargs) -> requests.Response:
        """Send a question to a chat session.

        Args:
            question: The question to ask.
            stream: Whether to use streaming mode.
            **kwargs: Additional arguments for the API.

        Returns:
            requests.Response: The HTTP response from the API.
        """
        json_data = {"question": question, "stream": stream, "session_id": self.id}
        json_data.update(kwargs)
        res = self.post(f"/chats/{self.chat_id}/completions", json_data, stream=stream)
        return res

    def _ask_agent(self, question: str, stream: bool, **kwargs) -> requests.Response:
        """Send a question to an agent session.

        Args:
            question: The question to ask.
            stream: Whether to use streaming mode.
            **kwargs: Additional arguments for the API.

        Returns:
            requests.Response: The HTTP response from the API.
        """
        json_data = {"question": question, "stream": stream, "session_id": self.id}
        json_data.update(kwargs)
        res = self.post(f"/agents/{self.agent_id}/completions", json_data, stream=stream)
        return res

    def update(self, update_message: dict) -> None:
        """Update the session.

        Args:
            update_message: Dictionary containing fields to update.

        Raises:
            APIError: If update fails.
        """
        res = self.put(f"/chats/{self.chat_id}/sessions/{self.id}", update_message)
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res.get("message"))


