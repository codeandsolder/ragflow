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


class ChunkUpdateError(Exception):
    """Exception raised when chunk update fails.

    Attributes:
        code: Error code from the API.
        message: Error message.
        details: Additional error details.
    """

    def __init__(self, code=None, message=None, details=None):
        """Initialize ChunkUpdateError.

        Args:
            code: Error code from the API.
            message: Error message.
            details: Additional error details.
        """
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class Chunk(Base):
    """Represents a chunk extracted from a document.

    A chunk is a piece of text extracted from a document during parsing.
    Chunks are used for retrieval and can have associated metadata like
    important keywords and questions.

    Attributes:
        id: Unique identifier of the chunk.
        content: The text content of the chunk.
        important_keywords: Keywords associated with this chunk.
        questions: Questions this chunk can answer.
        create_time: Creation timestamp string.
        create_timestamp: Creation timestamp as Unix time.
        dataset_id: ID of the parent dataset.
        document_name: Name of the source document.
        document_keyword: Keyword identifier for the document.
        document_id: ID of the source document.
        available: Whether the chunk is available for retrieval.
        similarity: Overall similarity score from retrieval.
        vector_similarity: Vector-based similarity score.
        term_similarity: Keyword-based similarity score.
        positions: Positions in the document.
        doc_type: Document type.

    Example:
        >>> chunks = document.list_chunks()
        >>> chunk = chunks[0]
        >>> chunk.update({"content": "Updated content"})
    """

    def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
        self.id = ""
        self.content = ""
        self.important_keywords = []
        self.questions = []
        self.create_time = ""
        self.create_timestamp = 0.0
        self.dataset_id = None
        self.document_name = ""
        self.document_keyword = ""
        self.document_id = ""
        self.available = True
        # Additional fields for retrieval results
        self.similarity = 0.0
        self.vector_similarity = 0.0
        self.term_similarity = 0.0
        self.positions = []
        self.doc_type = ""
        for k in list(res_dict.keys()):
            if k not in self.__dict__:
                res_dict.pop(k)
        super().__init__(rag, res_dict)

        # for backward compatibility
        if not self.document_name:
            self.document_name = self.document_keyword

    def update(self, update_message: dict):
        """Update the chunk with new information.

        Args:
            update_message: Dictionary containing fields to update.

        Raises:
            ChunkUpdateError: If the update fails.
        """
        res = self.put(f"/datasets/{self.dataset_id}/documents/{self.document_id}/chunks/{self.id}", update_message)
        res = res.json()
        if res.get("code") != 0:
            raise ChunkUpdateError(code=res.get("code"), message=res.get("message"), details=res.get("details"))
