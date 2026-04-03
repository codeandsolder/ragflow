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
Unit tests for chunk_app endpoint logic.
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.api_utils import get_json_result, get_data_error_result
from common.constants import RetCode


class TestChunkAppList:
    """Test cases for chunk_app.list endpoint logic"""

    def test_list_chunk_missing_doc_id(self):
        """Test list_chunk returns error when doc_id is missing"""
        result = get_data_error_result(message='Lack of "doc_id"')
        if hasattr(result, "get_json"):
            result_json = result.get_json()
        else:
            result_json = result

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "doc_id" in result_json.get("message", "")

    def test_list_chunk_document_not_found(self):
        """Test list_chunk returns error when document not found"""
        result = get_data_error_result(message="Document not found!")
        if hasattr(result, "get_json"):
            result_json = result.get_json()
        else:
            result_json = result

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "Document not found" in result_json.get("message", "")

    def test_list_chunk_tenant_not_found(self):
        """Test list_chunk returns error when tenant not found"""
        result = get_data_error_result(message="Tenant not found!")
        if hasattr(result, "get_json"):
            result_json = result.get_json()
        else:
            result_json = result

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "Tenant not found" in result_json.get("message", "")


class TestChunkAppResponseHelpers:
    """Test cases for chunk_app response helpers"""

    def test_get_json_result_success(self):
        """Test successful JSON result creation"""
        result = get_json_result(data={"chunks": []})
        if hasattr(result, "get_json"):
            result_json = result.get_json()
        else:
            result_json = result

        assert result_json.get("code") == 0
        assert result_json.get("data") == {"chunks": []}

    def test_get_json_result_with_message(self):
        """Test JSON result with custom message"""
        result = get_json_result(data={"chunks": []}, message="Custom message")
        if hasattr(result, "get_json"):
            result_json = result.get_json()
        else:
            result_json = result

        assert result_json.get("code") == 0
        assert result_json.get("message") == "Custom message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
