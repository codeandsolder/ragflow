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

from .base import Base
from .chunk import Chunk
from .exceptions import RAGFlowError, APIError


class Document(Base):
    """Represents a document in a RAGFlow dataset.

    A document is a file that has been uploaded to a dataset and can be parsed
    into chunks for retrieval.

    Attributes:
        id: Unique identifier of the document.
        name: Name of the document file.
        thumbnail: Thumbnail image for preview.
        dataset_id: ID of the parent dataset.
        chunk_method: Method used for chunking this document.
        parser_config: Parser configuration specific to this document.
        source_type: Source type (e.g., 'local').
        type: Document type.
        created_by: User ID who created this document.
        size: Size of the document in bytes.
        token_count: Number of tokens in the document.
        chunk_count: Number of chunks extracted from the document.
        progress: Parsing progress (0.0 to 1.0).
        progress_msg: Human-readable parsing status message.
        process_begin_at: Timestamp when parsing started.
        process_duration: Duration of parsing in seconds.
        run: Running status.
        status: Document status code.
        meta_fields: Custom metadata fields.

    Example:
        >>> docs = dataset.list_documents()
        >>> doc = docs[0]
        >>> chunks = doc.list_chunks()
    """

    class ParserConfig(Base):
        """Parser configuration for document processing."""

        def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
            super().__init__(rag, res_dict)

    def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
        """Initialize a Document object.

        Args:
            rag: Reference to the RAGFlow client.
            res_dict: Dictionary containing document data from API response.
        """
        self.id = ""
        self.name = ""
        self.thumbnail = None
        self.dataset_id = None
        self.chunk_method = "naive"
        self.parser_config = None
        self.source_type = "local"
        self.type = ""
        self.created_by = ""
        self.size = 0
        self.token_count = 0
        self.chunk_count = 0
        self.progress = 0.0
        self.progress_msg = ""
        self.process_begin_at = None
        self.process_duration = 0.0
        self.run = "0"
        self.status = "1"
        self.meta_fields = None
        super().__init__(rag, res_dict)

    def update(self, update_message: dict) -> "Document":
        """Update the document with new information.

        Args:
            update_message: Dictionary containing fields to update.

        Returns:
            Document: The updated Document object.

        Raises:
            RAGFlowError: If meta_fields is not a dictionary.
            APIError: If the update fails.
        """
        if "meta_fields" in update_message:
            if not isinstance(update_message["meta_fields"], dict):
                raise RAGFlowError("meta_fields must be a dictionary")
        res = self.put(f"/datasets/{self.dataset_id}/documents/{self.id}", update_message)
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])

        self._update_from_dict(self.rag, res.get("data", {}))
        return self

    def download(self):
        """Download the original document file.

        Returns:
            bytes: The document file content as bytes.

        Raises:
            APIError: If download fails or document not found.
        """
        res = self.get(f"/datasets/{self.dataset_id}/documents/{self.id}")
        error_keys = set(["code", "message"])
        try:
            response = res.json()
            actual_keys = set(response.keys())
            if actual_keys == error_keys:
                raise APIError(response.get("message"))
            else:
                return res.content
        except json.JSONDecodeError:
            return res.content

    def list_chunks(self, page: int = 1, page_size: int = 30, keywords: str = "", id: str = "") -> list[Chunk]:
        """List chunks extracted from this document.

        Args:
            page: Page number (default: 1).
            page_size: Number of items per page (default: 30).
            keywords: Filter chunks by keywords.
            id: Filter by specific chunk ID.

        Returns:
            list[Chunk]: List of Chunk objects.

        Raises:
            APIError: If listing fails.
        """
        data = {"keywords": keywords, "page": page, "page_size": page_size, "id": id}
        res = self.get(f"/datasets/{self.dataset_id}/documents/{self.id}/chunks", data)
        res = res.json()
        if res.get("code") == 0:
            chunks = []
            for data in res["data"].get("chunks"):
                chunk = Chunk(self.rag, data)
                chunks.append(chunk)
            return chunks
        raise APIError(res.get("message"))

    def add_chunk(self, content: str, important_keywords: list[str] | None = None, questions: list[str] | None = None, image_base64: str | None = None) -> Chunk:
        """Add a new chunk to this document.

        Args:
            content: The text content of the chunk.
            important_keywords: List of important keywords for the chunk (optional).
            questions: List of questions that this chunk can answer (optional).
            image_base64: Base64 encoded image content (optional).

        Returns:
            Chunk: The created Chunk object.

        Raises:
            APIError: If chunk creation fails.
        """
        body = {"content": content}
        if important_keywords is not None:
            body["important_keywords"] = important_keywords
        if questions is not None:
            body["questions"] = questions
        if image_base64 is not None:
            body["image_base64"] = image_base64
        res = self.post(f"/datasets/{self.dataset_id}/documents/{self.id}/chunks", body)
        res = res.json()
        if res.get("code") == 0:
            return Chunk(self.rag, res["data"].get("chunk"))
        raise APIError(res.get("message"))

    def delete_chunks(self, ids: list[str] | None = None, delete_all: bool = False):
        """Delete chunks from this document.

        Args:
            ids: List of chunk IDs to delete.
            delete_all: If True, delete all chunks from this document.

        Raises:
            APIError: If deletion fails.
        """
        res = self.rm(f"/datasets/{self.dataset_id}/documents/{self.id}/chunks", {"chunk_ids": ids, "delete_all": delete_all})
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res.get("message"))
