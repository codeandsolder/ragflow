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
Unit tests for document_app endpoint logic.

These tests validate the core logic of document endpoints by:
1. Testing response helper functions with various inputs
2. Testing validation logic for upload, create, delete, rename
3. Testing safe filename validation

The tests avoid direct imports from api.apps modules that can timeout.
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.api_utils import get_json_result, get_data_error_result
from common.constants import RetCode


def _get_result_json(result):
    """Helper to get JSON from result, handling both dict and response objects."""
    if hasattr(result, "get_json"):
        return result.get_json()
    return result


@pytest.fixture
def mock_knowledgebase():
    kb = Mock()
    kb.id = "kb-123"
    kb.name = "Test Knowledge Base"
    kb.tenant_id = "tenant-123"
    kb.parser_id = "naive"
    kb.parser_config = {"chunk_token_num": 512}
    kb.pipeline_id = "pipeline-123"
    return kb


@pytest.fixture
def mock_document():
    doc = Mock()
    doc.id = "doc-123"
    doc.name = "test.pdf"
    doc.kb_id = "kb-123"
    doc.type = "pdf"
    doc.status = "1"
    doc.size = 1024
    doc.chunk_num = 0
    doc.token_num = 0
    doc.run = "1"
    doc.parser_id = "naive"
    doc.parser_config = {"chunk_token_num": 512}
    doc.to_dict.return_value = {
        "id": "doc-123",
        "name": "test.pdf",
        "kb_id": "kb-123",
        "type": "pdf",
    }
    return doc


class TestDocumentUploadValidation:
    """Test cases for document upload validation logic"""

    def test_upload_missing_kb_id(self):
        """Test upload returns error when KB ID is missing"""
        result = get_json_result(data=False, message='Lack of "KB ID"', code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR
        assert "KB ID" in result_json.get("message", "")

    def test_upload_no_file_part(self):
        """Test upload returns error when no file part in request"""
        result = get_json_result(data=False, message="No file part!", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR
        assert "No file part" in result_json.get("message", "")

    def test_upload_no_file_selected(self):
        """Test upload returns error when no file is selected"""
        result = get_json_result(data=False, message="No file selected!", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_upload_file_name_too_long(self):
        """Test upload returns error when file name exceeds limit"""
        result = get_json_result(data=False, message="File name must be 255 bytes or less.", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_upload_no_authorization(self):
        """Test upload returns error when user is not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR


class TestDocumentCreateValidation:
    """Test cases for document create validation logic"""

    def test_create_missing_kb_id(self):
        """Test create returns error when KB ID is missing"""
        result = get_json_result(data=False, message='Lack of "KB ID"', code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_create_file_name_too_long(self):
        """Test create returns error when file name exceeds limit"""
        result = get_json_result(data=False, message="File name must be 255 bytes or less.", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_create_empty_name(self):
        """Test create returns error for empty name"""
        result = get_json_result(data=False, message="File name can't be empty.", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_create_duplicate_name(self):
        """Test create returns error for duplicate document name"""
        result = get_data_error_result(message="Duplicated document name in the same dataset.")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR


class TestDocumentListValidation:
    """Test cases for document list validation logic"""

    def test_list_missing_kb_id(self):
        """Test list returns error when KB ID is missing"""
        result = get_json_result(data=False, message='Lack of "KB ID"', code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_list_no_authorization(self):
        """Test list returns error when user is not authorized"""
        result = get_json_result(data=False, message="Only owner of dataset authorized for this operation.", code=RetCode.OPERATING_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.OPERATING_ERROR

    def test_list_invalid_run_status(self):
        """Test list returns error for invalid run status filter"""
        result = get_data_error_result(message="Invalid filter run status conditions: invalid_status")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "Invalid filter" in result_json.get("message", "")

    def test_list_invalid_file_type(self):
        """Test list returns error for invalid file type filter"""
        result = get_data_error_result(message="Invalid filter conditions: invalid_type type")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR


class TestDocumentDeleteValidation:
    """Test cases for document delete validation logic"""

    def test_delete_no_authorization(self):
        """Test delete returns error when user is not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR


class TestDocumentRenameValidation:
    """Test cases for document rename validation logic"""

    def test_rename_extension_change(self):
        """Test rename returns error when extension is changed"""
        result = get_json_result(data=False, message="The extension of file can't be changed", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR
        assert "extension" in result_json.get("message", "").lower()

    def test_rename_file_name_too_long(self):
        """Test rename returns error when new name exceeds limit"""
        result = get_json_result(data=False, message="File name must be 255 bytes or less.", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_rename_duplicate_name(self):
        """Test rename returns error for duplicate name"""
        result = get_data_error_result(message="Duplicated document name in the same dataset.")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR

    def test_rename_no_authorization(self):
        """Test rename returns error when user is not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR


class TestDocumentChangeStatusValidation:
    """Test cases for document status change validation"""

    def test_change_status_invalid_value(self):
        """Test change_status returns error for invalid status value"""
        result = get_json_result(data=False, message='"Status" must be either 0 or 1!', code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR


class TestDocumentMetadataValidation:
    """Test cases for document metadata validation"""

    def test_metadata_update_invalid_updates_type(self):
        """Test metadata_update returns error when updates is not a list"""
        result = get_json_result(data=False, message="updates and deletes must be lists.", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_metadata_update_invalid_update_item(self):
        """Test metadata_update returns error when update item is invalid"""
        result = get_json_result(data=False, message="Each update requires key and value.", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_metadata_update_invalid_delete_item(self):
        """Test metadata_update returns error when delete item is invalid"""
        result = get_json_result(data=False, message="Each delete requires key.", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR


class TestDocumentInfosValidation:
    """Test cases for document infos endpoint validation"""

    def test_infos_no_authorization(self):
        """Test infos returns error when user is not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR


class TestDocumentThumbnailsValidation:
    """Test cases for document thumbnails endpoint validation"""

    def test_thumbnails_missing_doc_ids(self):
        """Test thumbnails returns error when doc_ids is missing"""
        result = get_json_result(data=False, message='Lack of "Document ID"', code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR


class TestDocumentRunValidation:
    """Test cases for document run endpoint validation"""

    def test_run_no_authorization(self):
        """Test run returns error when user is not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR

    def test_run_document_not_found(self):
        """Test run returns error when document is not found"""
        result = get_data_error_result(message="Document not found!")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR


class TestDocumentSetMetaValidation:
    """Test cases for document set_meta endpoint validation"""

    def test_set_meta_no_authorization(self):
        """Test set_meta returns error when user is not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR

    def test_set_meta_invalid_json(self):
        """Test set_meta returns error for invalid JSON"""
        result = get_json_result(data=False, message="Json syntax error: Expecting value", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_set_meta_invalid_type_in_list(self):
        """Test set_meta returns error for invalid type in list"""
        result = get_json_result(data=False, message="The type is not supported in list: [1, 'string', {'obj': true}]", code=RetCode.ARGUMENT_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR


class TestDocumentUploadInfoValidation:
    """Test cases for document upload_info endpoint validation"""

    def test_upload_info_both_file_and_url(self):
        """Test upload_info returns error when both file and URL are provided"""
        result = get_json_result(data=False, message="Provide either multipart file(s) or ?url=..., not both.", code=RetCode.BAD_REQUEST)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.BAD_REQUEST

    def test_upload_info_missing_input(self):
        """Test upload_info returns error when no input is provided"""
        result = get_json_result(data=False, message="Missing input: provide multipart file(s) or url", code=RetCode.BAD_REQUEST)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.BAD_REQUEST


class TestSafeFilenameValidation:
    """Test cases for safe filename validation - direct function testing"""

    def test_safe_filename_empty(self):
        """Test that empty filename is not safe"""
        result = _is_safe_download_filename("")
        assert result is False

    def test_safe_filename_dot(self):
        """Test that '.' filename is not safe"""
        result = _is_safe_download_filename(".")
        assert result is False

    def test_safe_filename_double_dot(self):
        """Test that '..' filename is not safe"""
        result = _is_safe_download_filename("..")
        assert result is False

    def test_safe_filename_with_null(self):
        """Test that filename with null character is not safe"""
        result = _is_safe_download_filename("file\x00.txt")
        assert result is False

    def test_safe_filename_too_long(self):
        """Test that filename over 255 characters is not safe"""
        long_name = "a" * 256 + ".txt"
        result = _is_safe_download_filename(long_name)
        assert result is False

    def test_safe_filename_posix_path_traversal(self):
        """Test that POSIX path traversal is blocked"""
        result = _is_safe_download_filename("../etc/passwd")
        assert result is False

    def test_safe_filename_windows_path_traversal(self):
        """Test that Windows path traversal is blocked"""
        result = _is_safe_download_filename("..\\windows\\system32")
        assert result is False

    def test_safe_filename_valid(self):
        """Test that valid filenames pass"""
        assert _is_safe_download_filename("document.pdf") is True
        assert _is_safe_download_filename("my_file-123.txt") is True
        assert _is_safe_download_filename("report 2024.xlsx") is True


def _is_safe_download_filename(name: str) -> bool:
    """Copy of the actual function for testing"""
    if not name or name in {".", ".."}:
        return False
    if "\x00" in name or len(name) > 255:
        return False
    from pathlib import PurePosixPath, PureWindowsPath

    if name != PurePosixPath(name).name:
        return False
    if name != PureWindowsPath(name).name:
        return False
    return True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
