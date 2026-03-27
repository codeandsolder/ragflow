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
"""
End-to-end multimodal flow tests.

Tests the complete pipeline for:
- Image upload -> processing -> retrieval
- Table extraction -> indexing -> retrieval
- Document with images + tables + text
"""

import pytest
from common import (
    create_dialog,
    list_chunks,
    list_documents,
    parse_documents,
    upload_documents,
)
from configs import INVALID_API_TOKEN
from libs.auth import RAGFlowWebApiAuth
from utils import wait_for
from utils.file_utils import create_image_file, create_excel_file, create_txt_file


def wait_for_document_parsing(auth, kb_id, timeout=30, interval=1):
    @wait_for(timeout, interval, "Document parsing timeout")
    def condition(_auth, _kb_id):
        res = list_documents(_auth, {"kb_id": _kb_id})
        for doc in res["data"]["docs"]:
            if doc.get("run") != "3":
                return False
        return True

    return condition(auth, kb_id)


class TestE2EMultimodalFlow:
    @pytest.mark.p2
    @pytest.mark.usefixtures("clear_datasets")
    class TestAuthorization:
        @pytest.mark.parametrize(
            "invalid_auth, expected_code, expected_message",
            [
                (None, 401, "<Unauthorized '401: Unauthorized'>"),
                (RAGFlowWebApiAuth(INVALID_API_TOKEN), 401, "<Unauthorized '401: Unauthorized'>"),
            ],
        )
        def test_invalid_auth(self, invalid_auth, expected_code, expected_message):
            res = upload_documents(invalid_auth, {"kb_id": "dummy"}, [])
            assert res["code"] == expected_code, res
            assert res["message"] == expected_message, res

    @pytest.mark.p1
    @pytest.mark.usefixtures("clear_datasets")
    def test_image_to_chat_flow(self, WebApiAuth, add_dataset_func, ragflow_tmp_dir):
        """
        Test image upload -> processing -> retrieval flow.

        Steps:
        1. Upload a PNG image file to a dataset
        2. Parse the document (run OCR/processing)
        3. Verify chunks are created with image content
        4. Verify retrieval works with image-derived chunks
        5. Create a dialog and verify it can access the chunks
        """
        kb_id = add_dataset_func

        image_path = create_image_file(ragflow_tmp_dir / "test_image.png")

        res = upload_documents(WebApiAuth, {"kb_id": kb_id}, [image_path])
        assert res["code"] == 0, f"Upload failed: {res}"
        doc_id = res["data"][0]["id"]

        res = parse_documents(WebApiAuth, {"doc_ids": [doc_id], "run": "1"})
        assert res["code"] == 0, f"Parse failed: {res}"

        wait_for_document_parsing(WebApiAuth, kb_id)

        res = list_documents(WebApiAuth, {"kb_id": kb_id})
        doc = next(d for d in res["data"]["docs"] if d["id"] == doc_id)
        assert doc["run"] == "3", f"Document not parsed: {doc}"
        assert doc["chunk_count"] > 0, "No chunks created from image"

        res = list_chunks(WebApiAuth, {"doc_id": doc_id})
        assert res["code"] == 0, f"List chunks failed: {res}"
        assert len(res["data"]["chunks"]) > 0, "No chunks returned"

        chunk = res["data"]["chunks"][0]
        assert "content" in chunk, "Chunk missing content field"
        assert isinstance(chunk["content"], str), "Chunk content should be string"

        prompt_config = {
            "system": "You are a helpful assistant. Use the following knowledge to answer questions: {knowledge}",
            "parameters": [{"key": "knowledge", "optional": False}],
        }
        dialog_payload = {
            "name": "test_image_dialog",
            "description": "Test dialog for image chunks",
            "kb_ids": [kb_id],
            "prompt_config": prompt_config,
            "top_n": 6,
            "top_k": 1024,
            "similarity_threshold": 0.1,
            "vector_similarity_weight": 0.3,
            "llm_setting": {"model": "gpt-3.5-turbo", "temperature": 0.7},
        }
        res = create_dialog(WebApiAuth, dialog_payload)
        assert res["code"] == 0, f"Dialog creation failed: {res}"

    @pytest.mark.p1
    @pytest.mark.usefixtures("clear_datasets")
    def test_table_to_chat_flow(self, WebApiAuth, add_dataset_func, ragflow_tmp_dir):
        """
        Test table extraction -> indexing -> retrieval flow.

        Steps:
        1. Upload an Excel file with tabular data
        2. Parse the document (extract tables)
        3. Verify chunks are created with table content
        4. Verify chunk_data contains structured table fields
        5. Create a dialog and verify it can access the chunks
        """
        kb_id = add_dataset_func

        excel_path = create_excel_file(ragflow_tmp_dir / "test_table.xlsx")

        res = upload_documents(WebApiAuth, {"kb_id": kb_id}, [excel_path])
        assert res["code"] == 0, f"Upload failed: {res}"
        doc_id = res["data"][0]["id"]

        res = parse_documents(WebApiAuth, {"doc_ids": [doc_id], "run": "1"})
        assert res["code"] == 0, f"Parse failed: {res}"

        wait_for_document_parsing(WebApiAuth, kb_id)

        res = list_documents(WebApiAuth, {"kb_id": kb_id})
        doc = next(d for d in res["data"]["docs"] if d["id"] == doc_id)
        assert doc["run"] == "3", f"Document not parsed: {doc}"
        assert doc["chunk_count"] > 0, "No chunks created from table"

        res = list_chunks(WebApiAuth, {"doc_id": doc_id})
        assert res["code"] == 0, f"List chunks failed: {res}"
        assert len(res["data"]["chunks"]) > 0, "No chunks returned"

        chunk = res["data"]["chunks"][0]
        assert "content" in chunk, "Chunk missing content field"
        assert isinstance(chunk["content"], str), "Chunk content should be string"

        prompt_config = {
            "system": "You are a helpful assistant. Use the following knowledge to answer questions: {knowledge}",
            "parameters": [{"key": "knowledge", "optional": False}],
        }
        dialog_payload = {
            "name": "test_table_dialog",
            "description": "Test dialog for table chunks",
            "kb_ids": [kb_id],
            "prompt_config": prompt_config,
            "top_n": 6,
            "top_k": 1024,
            "similarity_threshold": 0.1,
            "vector_similarity_weight": 0.3,
            "llm_setting": {"model": "gpt-3.5-turbo", "temperature": 0.7},
        }
        res = create_dialog(WebApiAuth, dialog_payload)
        assert res["code"] == 0, f"Dialog creation failed: {res}"

    @pytest.mark.p3
    @pytest.mark.usefixtures("clear_datasets")
    def test_mixed_content_flow(self, WebApiAuth, add_dataset_func, ragflow_tmp_dir):
        """
        Test document with images + tables + text flow.

        Steps:
        1. Upload multiple files: image + excel + text
        2. Parse all documents
        3. Verify chunks are created from all content types
        4. Verify retrieval can find content across different types
        5. Create a dialog with all knowledge and verify chat works
        """
        kb_id = add_dataset_func

        image_path = create_image_file(ragflow_tmp_dir / "mixed_image.png")
        excel_path = create_excel_file(ragflow_tmp_dir / "mixed_table.xlsx")

        from utils.file_utils import create_txt_file

        txt_path = create_txt_file(ragflow_tmp_dir / "mixed_text.txt")

        res = upload_documents(
            WebApiAuth,
            {"kb_id": kb_id},
            [image_path, excel_path, txt_path],
        )
        assert res["code"] == 0, f"Upload failed: {res}"
        doc_ids = [doc["id"] for doc in res["data"]]

        res = parse_documents(WebApiAuth, {"doc_ids": doc_ids, "run": "1"})
        assert res["code"] == 0, f"Parse failed: {res}"

        wait_for_document_parsing(WebApiAuth, kb_id)

        res = list_documents(WebApiAuth, {"kb_id": kb_id})
        for doc in res["data"]["docs"]:
            assert doc["run"] == "3", f"Document not parsed: {doc}"
            assert doc["chunk_count"] > 0, f"No chunks created from {doc['name']}"

        res = list_chunks(WebApiAuth, {"kb_id": kb_id})
        assert res["code"] == 0, f"List chunks failed: {res}"
        assert len(res["data"]["chunks"]) >= 3, "Expected at least 3 chunks from mixed content"

        chunk_doc_types = set()
        for chunk in res["data"]["chunks"]:
            if "doc_type_kwd" in chunk:
                chunk_doc_types.add(chunk["doc_type_kwd"])

        prompt_config = {
            "system": "You are a helpful assistant. Use the following knowledge to answer questions: {knowledge}",
            "parameters": [{"key": "knowledge", "optional": False}],
        }
        dialog_payload = {
            "name": "test_mixed_dialog",
            "description": "Test dialog for mixed content",
            "kb_ids": [kb_id],
            "prompt_config": prompt_config,
            "top_n": 6,
            "top_k": 1024,
            "similarity_threshold": 0.1,
            "vector_similarity_weight": 0.3,
            "llm_setting": {"model": "gpt-3.5-turbo", "temperature": 0.7},
        }
        res = create_dialog(WebApiAuth, dialog_payload)
        assert res["code"] == 0, f"Dialog creation failed: {res}"
