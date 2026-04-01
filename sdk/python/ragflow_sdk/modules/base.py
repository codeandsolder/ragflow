#
# Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ragflow_sdk.ragflow import RAGFlow


class Base:
    """Base class for all RAGFlow SDK objects.

    Provides common functionality for API communication, serialization,
    and object initialization from API responses.

    Attributes:
        rag: Reference to the RAGFlow client instance.

    Example:
        >>> class MyObject(Base):
        ...     def __init__(self, rag: RAGFlow, res_dict: dict[str, Any]) -> None:
        ...         self.field = ""
        ...         super().__init__(rag, res_dict)
    """

    def __init__(self, rag: RAGFlow, res_dict: dict[str, Any]) -> None:
        """Initialize a Base object.

        Args:
            rag: Reference to the RAGFlow client.
            res_dict: Dictionary containing data from API response.
        """
        self.rag = rag
        self._update_from_dict(rag, res_dict)

    def _update_from_dict(self, rag: RAGFlow, res_dict: dict[str, Any]) -> None:
        """Update object attributes from a dictionary.

        Recursively converts nested dictionaries to Base objects.

        Args:
            rag: Reference to the RAGFlow client.
            res_dict: Dictionary containing attribute values.
        """
        for k, v in res_dict.items():
            if isinstance(v, dict):
                self.__dict__[k] = Base(rag, v)
            else:
                self.__dict__[k] = v

    def to_json(self) -> dict[str, Any]:
        """Convert the object to a JSON-serializable dictionary.

        Returns:
            dict: Dictionary representation of the object.
        """
        pr = {}
        for name in dir(self):
            value = getattr(self, name)
            if not name.startswith("__") and not callable(value) and name != "rag":
                if isinstance(value, Base):
                    pr[name] = value.to_json()
                else:
                    pr[name] = value
        return pr

    def post(self, path: str, json: Optional[dict[str, Any]] = None, stream: bool = False, files: Optional[list[tuple[str, Any]]] = None):
        """Send a POST request to the RAGFlow API.

        Args:
            path: API endpoint path.
            json: JSON payload.
            stream: Whether to stream the response.
            files: Files to upload.

        Returns:
            Response object from the server.
        """
        res = self.rag.post(path, json, stream=stream, files=files)
        return res

    def get(self, path: str, params: Optional[dict[str, Any]] = None):
        """Send a GET request to the RAGFlow API.

        Args:
            path: API endpoint path.
            params: Query parameters.

        Returns:
            Response object from the server.
        """
        res = self.rag.get(path, params)
        return res

    def rm(self, path: str, json: dict[str, Any]):
        """Send a DELETE request to the RAGFlow API.

        Args:
            path: API endpoint path.
            json: JSON payload.

        Returns:
            Response object from the server.
        """
        res = self.rag.delete(path, json)
        return res

    def put(self, path: str, json: dict[str, Any]):
        """Send a PUT request to the RAGFlow API.

        Args:
            path: API endpoint path.
            json: JSON payload.

        Returns:
            Response object from the server.
        """
        res = self.rag.put(path, json)
        return res

    def __str__(self) -> str:
        """Return string representation of the object.

        Returns:
            str: JSON string representation.
        """
        return str(self.to_json())
