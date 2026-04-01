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

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ragflow_sdk.ragflow import RAGFlow
from .base import Base
from .document import Document
from .exceptions import APIError


class DataSet(Base):
    """Represents a dataset in RAGFlow.

    A dataset contains documents and their chunks, along with configuration
    for parsing, embedding, and metadata extraction.

    Attributes:
        id: Unique identifier of the dataset.
        name: Name of the dataset.
        avatar: Avatar URL or base64 string.
        tenant_id: ID of the tenant who owns this dataset.
        description: Description of the dataset.
        embedding_model: Embedding model used for this dataset.
        permission: Access permission setting.
        document_count: Number of documents in the dataset.
        chunk_count: Number of chunks in the dataset.
        chunk_method: Method used for chunking documents.
        parser_config: Parser configuration for document processing.
        pagerank: PageRank score for document ranking.

    Example:
        >>> datasets = ragflow.list_datasets()
        >>> dataset = datasets[0]
        >>> dataset.update({"name": "New Name"})
    """

    class ParserConfig(Base):
        """Configuration for document parsing.

        Attributes:
            rag: Reference to the RAGFlow client.
            res_dict: Dictionary containing parser configuration.
        """

        def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
            super().__init__(rag, res_dict)

    def __init__(self, rag: RAGFlow, res_dict: dict) -> None:
        """Initialize a DataSet object.

        Args:
            rag: Reference to the RAGFlow client.
            res_dict: Dictionary containing dataset data from API response.
        """
        self.id = ""
        self.name = ""
        self.avatar = ""
        self.tenant_id = None
        self.description = ""
        self.embedding_model = ""
        self.permission = "me"
        self.document_count = 0
        self.chunk_count = 0
        self.chunk_method = "naive"
        self.parser_config = None
        self.pagerank = 0
        for k in list(res_dict.keys()):
            if k not in self.__dict__:
                res_dict.pop(k)
        super().__init__(rag, res_dict)

    def update(self, update_message: dict):
        """Update the dataset with new information.

        Args:
            update_message: Dictionary containing fields to update.

        Returns:
            DataSet: The updated DataSet object.

        Raises:
            APIError: If the update fails.
        """
        res = self.put(f"/datasets/{self.id}", update_message)
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])

        self._update_from_dict(self.rag, res.get("data", {}))
        return self

    def upload_documents(self, document_list: list[dict]):
        """Upload documents to the dataset.

        Args:
            document_list: List of dictionaries, each containing 'display_name' and 'blob' keys.

        Returns:
            list[Document]: List of created Document objects.

        Raises:
            APIError: If upload fails.
        """
        url = f"/datasets/{self.id}/documents"
        files = [("file", (ele["display_name"], ele["blob"])) for ele in document_list]
        res = self.post(path=url, json=None, files=files)
        res = res.json()
        if res.get("code") == 0:
            doc_list = []
            for doc in res["data"]:
                document = Document(self.rag, doc)
                doc_list.append(document)
            return doc_list
        raise APIError(res.get("message"))

    def list_documents(
        self,
        id: str | None = None,
        name: str | None = None,
        keywords: str | None = None,
        page: int = 1,
        page_size: int = 30,
        orderby: str = "create_time",
        desc: bool = True,
        create_time_from: int = 0,
        create_time_to: int = 0,
    ):
        """List documents in the dataset with filtering and pagination.

        Args:
            id: Filter by document ID.
            name: Filter by document name (partial match).
            keywords: Filter by keywords in document.
            page: Page number (default: 1).
            page_size: Number of items per page (default: 30).
            orderby: Field to order by (default: 'create_time').
            desc: Sort in descending order (default: True).
            create_time_from: Filter documents created after this timestamp.
            create_time_to: Filter documents created before this timestamp.

        Returns:
            list[Document]: List of Document objects.

        Raises:
            APIError: If listing fails.
        """
        params = {
            "id": id,
            "name": name,
            "keywords": keywords,
            "page": page,
            "page_size": page_size,
            "orderby": orderby,
            "desc": desc,
            "create_time_from": create_time_from,
            "create_time_to": create_time_to,
        }
        res = self.get(f"/datasets/{self.id}/documents", params=params)
        res = res.json()
        documents = []
        if res.get("code") == 0:
            for document in res["data"].get("docs"):
                documents.append(Document(self.rag, document))
            return documents
        raise APIError(res["message"])

    def delete_documents(self, ids: list[str] | None = None, delete_all: bool = False):
        """Delete documents from the dataset.

        Args:
            ids: List of document IDs to delete.
            delete_all: If True, delete all documents (ignores ids).

        Raises:
            APIError: If deletion fails.
        """
        res = self.rm(f"/datasets/{self.id}/documents", {"ids": ids, "delete_all": delete_all})
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])

    def _get_documents_status(self, document_ids):
        import time

        terminal_states = {"DONE", "FAIL", "CANCEL"}
        interval_sec = 1
        pending = set(document_ids)
        finished = []
        while pending:
            for doc_id in list(pending):

                def fetch_doc(doc_id: str) -> Document | None:
                    try:
                        docs = self.list_documents(id=doc_id)
                        return docs[0] if docs else None
                    except Exception:
                        return None

                doc = fetch_doc(doc_id)
                if doc is None:
                    continue
                if isinstance(doc.run, str) and doc.run.upper() in terminal_states:
                    finished.append((doc_id, doc.run, doc.chunk_count, doc.token_count))
                    pending.discard(doc_id)
                elif float(doc.progress or 0.0) >= 1.0:
                    finished.append((doc_id, "DONE", doc.chunk_count, doc.token_count))
                    pending.discard(doc_id)
            if pending:
                time.sleep(interval_sec)
        return finished

    def async_parse_documents(self, document_ids):
        """Start asynchronous document parsing.

        Initiates parsing of documents to extract chunks. This method returns immediately
        while parsing continues in the background.

        Args:
            document_ids: List of document IDs to parse.

        Raises:
            APIError: If parsing initiation fails.
        """
        res = self.post(f"/datasets/{self.id}/chunks", {"document_ids": document_ids})
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res.get("message"))

    def parse_documents(self, document_ids):
        """Parse documents and wait for completion.

        Parses documents to extract chunks and waits for the parsing to complete.
        This is a blocking operation that polls for document status.

        Args:
            document_ids: List of document IDs to parse.

        Returns:
            list: List of tuples containing (document_id, status, chunk_count, token_count).

        Raises:
            APIError: If parsing fails.
        """
        try:
            self.async_parse_documents(document_ids)
            self._get_documents_status(document_ids)
        except KeyboardInterrupt:
            self.async_cancel_parse_documents(document_ids)

        return self._get_documents_status(document_ids)

    def async_cancel_parse_documents(self, document_ids):
        """Cancel ongoing document parsing.

        Args:
            document_ids: List of document IDs for which to cancel parsing.

        Raises:
            APIError: If cancellation fails.
        """
        res = self.rm(f"/datasets/{self.id}/chunks", {"document_ids": document_ids})
        res = res.json()
        if res.get("code") != 0:
            raise APIError(res["message"])

    def update_auto_metadata(self, **config: Any) -> dict[str, Any]:
        """
        Update auto-metadata configuration for a dataset via SDK.
        """
        res = self.put(f"/datasets/{self.id}/auto_metadata", config)
        res = res.json()
        if res.get("code") == 0:
            return res["data"]
        raise APIError(res["message"])
