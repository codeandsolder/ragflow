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
import pytest
import requests
from common import (
    create_dataset,
    create_dialog,
    delete_dialogs,
    list_chunks,
    list_dialogs,
    list_documents,
    parse_documents,
    retrieval_chunks,
)
from configs import HOST_ADDRESS, VERSION
from utils import wait_for
from utils.file_utils import create_txt_file
from common import delete_datasets


@wait_for(60, 1, "Document parsing timeout")
def _wait_for_document_parsing(_auth, _kb_id, _document_ids=None):
    res = list_documents(_auth, {"kb_id": _kb_id})
    target_docs = res["data"]["docs"]

    if _document_ids is None:
        for doc in target_docs:
            if doc["run"] != "3":
                return False
        return True

    target_ids = set(_document_ids)
    for doc in target_docs:
        if doc["id"] in target_ids:
            if doc.get("run") != "3":
                return False
    return True


def _validate_document_parse_done(auth, kb_id, document_ids):
    res = list_documents(auth, {"kb_id": kb_id})
    for doc in res["data"]["docs"]:
        if doc["id"] not in document_ids:
            continue
        assert doc["run"] == "3"
        assert len(doc["process_begin_at"]) > 0
        assert doc["process_duration"] > 0
        assert doc["progress"] > 0
        assert "Task done" in doc["progress_msg"]


def _validate_chunks_created(auth, kb_id, document_ids):
    res = list_documents(auth, {"kb_id": kb_id})
    for doc in res["data"]["docs"]:
        if doc["id"] in document_ids:
            assert doc["chunk_count"] > 0, f"Document {doc['id']} has no chunks created"


def _validate_chunks_searchable(auth, kb_id, document_ids):
    res = list_chunks(auth, {"kb_id": kb_id})
    assert res["code"] == 0, f"Failed to list chunks: {res}"
    chunks = res["data"]["chunks"]
    assert len(chunks) > 0, "No chunks found for search test"

    if chunks:
        query = "test"
        search_payload = {"query": query, "top_k": 5, "filters": {"kb_id": kb_id}}
        res = retrieval_chunks(auth, search_payload)
        assert res["code"] == 0, f"Retrieval test failed: {res}"


def _validate_dialog_created(auth, dialog_id):
    res = list_dialogs(auth)
    assert res["code"] == 0, f"Failed to list dialogs: {res}"
    dialogs = res["data"]
    dialog_found = any(d["id"] == dialog_id for d in dialogs)
    assert dialog_found, f"Dialog {dialog_id} not found in list"


@pytest.mark.integration
class TestE2ERAGPipeline:
    @pytest.fixture(autouse=True)
    def cleanup(self, WebApiAuth, request):
        kb_ids = []

        def cleanup():
            delete_dialogs(WebApiAuth)
            res = list_documents(WebApiAuth, {"page_size": 1000})
            if res["code"] == 0 and res["data"]["docs"]:
                doc_ids = [doc["id"] for doc in res["data"]["docs"]]
                if doc_ids:
                    from common import delete_document

                    for doc_id in doc_ids:
                        delete_document(WebApiAuth, {"doc_id": doc_id})
            for kb_id in kb_ids:
                delete_datasets(WebApiAuth, {"id": kb_id})

        request.addfinalizer(cleanup)
        return kb_ids

    @pytest.mark.p3
    def test_full_rag_pipeline_kb_to_chat(self, WebApiAuth, tmp_path, cleanup):
        kb_res = create_dataset(WebApiAuth, {"name": "test_kb_e2e"})
        assert kb_res["code"] == 0, f"KB creation failed: {kb_res}"
        kb_id = kb_res["data"]["id"]
        cleanup.append(kb_id)

        test_file = tmp_path / "test_document.txt"
        test_file.write_text("This is a test document about Ragflow. Ragflow is an open-source RAG engine.")

        upload_res = upload_documents(WebApiAuth, {"kb_id": kb_id}, [str(test_file)])
        assert upload_res["code"] == 0, f"Upload failed: {upload_res}"
        document_ids = [doc["id"] for doc in upload_res["data"]]
        assert len(document_ids) == 1

        parse_res = parse_documents(WebApiAuth, {"doc_ids": document_ids, "run": "1"})
        assert parse_res["code"] == 0, f"Parse failed: {parse_res}"

        _wait_for_document_parsing(WebApiAuth, kb_id, document_ids)
        _validate_document_parse_done(WebApiAuth, kb_id, document_ids)
        _validate_chunks_created(WebApiAuth, kb_id, document_ids)
        _validate_chunks_searchable(WebApiAuth, kb_id, document_ids)

        dialog_payload = {
            "name": "test_dialog_e2e",
            "description": "Test dialog for E2E pipeline",
            "kb_ids": [kb_id],
            "prompt_config": {"system": "You are a helpful assistant. Use the following knowledge to answer questions: {knowledge}", "parameters": [{"key": "knowledge", "optional": False}]},
            "top_n": 6,
            "top_k": 1024,
            "similarity_threshold": 0.1,
            "vector_similarity_weight": 0.3,
            "llm_setting": {"model": "gpt-3.5-turbo", "temperature": 0.7},
        }

        dialog_res = create_dialog(WebApiAuth, dialog_payload)
        assert dialog_res["code"] == 0, f"Dialog creation failed: {dialog_res}"
        dialog_id = dialog_res["data"]["id"]
        _validate_dialog_created(WebApiAuth, dialog_id)

        url = f"{HOST_ADDRESS}/{VERSION}/conversation/completion"
        chat_payload = {"conversation_id": "", "messages": [{"role": "user", "content": "What is Ragflow?"}], "stream": False, "dialog_id": dialog_id, "is_new": True}

        chat_result = requests.post(url, headers={"Content-Type": "application/json"}, auth=WebApiAuth, json=chat_payload)
        assert chat_result.status_code == 200, f"Chat request failed: {chat_result.text}"

        chat_data = chat_result.json()
        assert chat_data["code"] == 0, f"Chat API error: {chat_data}"

        answer = chat_data["data"]["answer"]
        assert isinstance(answer, str), "Chat response should be a string"
        assert len(answer) > 0, "Chat response should not be empty"

        assert "Ragflow" in answer or "RAG" in answer, "Response should mention Ragflow or RAG"

    @pytest.mark.p3
    def test_full_rag_pipeline_with_multiple_documents(self, WebApiAuth, tmp_path, cleanup):
        kb_res = create_dataset(WebApiAuth, {"name": "test_kb_multi_e2e"})
        assert kb_res["code"] == 0, f"KB creation failed: {kb_res}"
        kb_id = kb_res["data"]["id"]
        cleanup.append(kb_id)

        document_contents = [
            "This is document one about Ragflow. Ragflow is an open-source RAG engine.",
            "Document two discusses retrieval augmented generation. RAG improves LLM responses.",
            "Third document covers deep document understanding and knowledge graphs.",
        ]

        test_files = []
        for i, content in enumerate(document_contents):
            f = tmp_path / f"test_document_{i}.txt"
            f.write_text(content)
            test_files.append(f)

        upload_res = upload_documents(WebApiAuth, {"kb_id": kb_id}, [str(f) for f in test_files])
        assert upload_res["code"] == 0, f"Upload failed: {upload_res}"
        document_ids = [doc["id"] for doc in upload_res["data"]]
        assert len(document_ids) == len(document_contents)

        parse_res = parse_documents(WebApiAuth, {"doc_ids": document_ids, "run": "1"})
        assert parse_res["code"] == 0, f"Parse failed: {parse_res}"

        _wait_for_document_parsing(WebApiAuth, kb_id, document_ids)
        _validate_document_parse_done(WebApiAuth, kb_id, document_ids)
        _validate_chunks_created(WebApiAuth, kb_id, document_ids)
        _validate_chunks_searchable(WebApiAuth, kb_id, document_ids)

        dialog_payload = {
            "name": "test_dialog_multi_e2e",
            "kb_ids": [kb_id],
            "prompt_config": {"system": "You are a helpful assistant. Use the following knowledge to answer questions: {knowledge}", "parameters": [{"key": "knowledge", "optional": False}]},
        }

        dialog_res = create_dialog(WebApiAuth, dialog_payload)
        assert dialog_res["code"] == 0, f"Dialog creation failed: {dialog_res}"
        dialog_id = dialog_res["data"]["id"]

        url = f"{HOST_ADDRESS}/{VERSION}/conversation/completion"
        chat_payload = {
            "conversation_id": "",
            "messages": [{"role": "user", "content": "Explain what Ragflow does and how it relates to RAG and knowledge graphs"}],
            "stream": False,
            "dialog_id": dialog_id,
            "is_new": True,
        }

        chat_result = requests.post(url, headers={"Content-Type": "application/json"}, auth=WebApiAuth, json=chat_payload)
        assert chat_result.status_code == 200, f"Chat request failed: {chat_result.text}"

        chat_data = chat_result.json()
        assert chat_data["code"] == 0, f"Chat API error: {chat_data}"

        answer = chat_data["data"]["answer"]
        assert isinstance(answer, str), "Chat response should be a string"
        assert len(answer) > 0, "Chat response should not be empty"

        assert "Ragflow" in answer or "RAG" in answer or "retrieval" in answer, "Response should mention Ragflow, RAG, or retrieval"


def upload_documents(auth, payload=None, files_path=None, **kwargs):
    from common import upload_documents as _upload

    return _upload(auth, payload, files_path, **kwargs)
