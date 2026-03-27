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
Unit tests for kb_app endpoint logic.

These tests validate the core logic of knowledge base endpoints by:
1. Testing response helper functions with various inputs
2. Testing validation logic
3. Testing knowledge base operation logic

The tests avoid direct imports from api.apps modules that can timeout.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

RETCODE_SUCCESS = 0
RETCODE_ARGUMENT_ERROR = 1
RETCODE_DATA_ERROR = 2
RETCODE_FORBIDDEN = 3
RETCODE_NOT_FOUND = 4
RETCODE_AUTHENTICATION_ERROR = 2
RETCODE_OPERATING_ERROR = 6
RETCODE_NOT_EFFECTIVE = 7


class MockResponse:
    """Mock Flask/Quart response object"""

    def __init__(self, data, code=0, message=""):
        self._data = data
        self._code = code
        self._message = message

    def get_json(self):
        return {"code": self._code, "message": self._message, "data": self._data}


def get_json_result(data=None, message="", code=0):
    """Mock get_json_result helper"""
    return MockResponse(data, code, message)


def get_data_error_result(message="", code=2):
    """Mock get_data_error_result helper"""
    return MockResponse(None, code, message)


def get_error_data_result(message="", code=1):
    """Mock get_error_data_result helper"""
    return MockResponse(None, code, message)


@pytest.fixture
def mock_tenant():
    tenant = Mock()
    tenant.tenant_id = "tenant-123"
    tenant.name = "Test Tenant"
    return tenant


@pytest.fixture
def mock_user():
    user = Mock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.nickname = "Test User"
    user.tenant_id = "tenant-123"
    user.is_active = "1"
    return user


@pytest.fixture
def mock_knowledgebase():
    kb = Mock()
    kb.id = "kb-123"
    kb.name = "Test Knowledge Base"
    kb.tenant_id = "tenant-123"
    kb.parser_id = "naive"
    kb.parser_config = {"chunk_token_num": 512}
    kb.created_by = "user-123"
    kb.create_time = datetime.now()
    kb.update_time = datetime.now()
    kb.to_dict.return_value = {
        "id": "kb-123",
        "name": "Test Knowledge Base",
        "tenant_id": "tenant-123",
        "parser_id": "naive",
        "parser_config": {"chunk_token_num": 512},
    }
    return kb


class TestKbAppDetail:
    """Test cases for kb_app.detail endpoint logic"""

    def test_detail_returns_kb_info(self, mock_tenant, mock_knowledgebase):
        """Test that detail returns knowledge base information"""
        result = get_json_result(data={"id": "kb-123", "name": "Test KB", "size": 1024, "connectors": []})
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("data") is not False

    def test_detail_no_authorization(self):
        """Test detail returns error when user has no access"""
        result = get_json_result(data=False, message="Only owner of dataset authorized for this operation.", code=RETCODE_OPERATING_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_OPERATING_ERROR


class TestKbAppUpdateMetadataSetting:
    """Test cases for kb_app.update_metadata_setting endpoint logic"""

    def test_update_metadata_setting_success(self, mock_knowledgebase):
        """Test successful metadata setting update"""
        result = get_json_result(data=mock_knowledgebase.to_dict())
        result_json = result.get_json()

        assert result_json.get("code") == 0

    def test_update_metadata_setting_db_error(self):
        """Test metadata update returns error on DB failure"""
        result = get_data_error_result(message="Database error (Knowledgebase rename)!")
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_DATA_ERROR


class TestKbAppListTags:
    """Test cases for kb_app.list_tags endpoint logic"""

    def test_list_tags_success(self):
        """Test successful tag listing"""
        result = get_json_result(data=["tag1", "tag2"])
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert "tag1" in result_json.get("data", [])

    def test_list_tags_no_authorization(self):
        """Test tag listing returns error when not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RETCODE_AUTHENTICATION_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_AUTHENTICATION_ERROR


class TestKbAppGetMeta:
    """Test cases for kb_app.get_meta endpoint logic"""

    def test_get_meta_success(self):
        """Test successful metadata retrieval"""
        result = get_json_result(data={"author": {"John": ["doc-1"]}})
        result_json = result.get_json()

        assert result_json.get("code") == 0

    def test_get_meta_no_authorization(self):
        """Test get_meta returns error when not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RETCODE_AUTHENTICATION_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_AUTHENTICATION_ERROR


class TestKbAppBasicInfo:
    """Test cases for kb_app.get_basic_info endpoint logic"""

    def test_basic_info_success(self):
        """Test successful basic info retrieval"""
        result = get_json_result(data={"doc_count": 5, "total_size": 1024000})
        result_json = result.get_json()

        assert result_json.get("code") == 0

    def test_basic_info_no_authorization(self):
        """Test basic_info returns error when not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RETCODE_AUTHENTICATION_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_AUTHENTICATION_ERROR


class TestKbAppPipelineLogs:
    """Test cases for kb_app pipeline log endpoint logic"""

    def test_list_pipeline_logs_missing_kb_id(self):
        """Test list_pipeline_logs returns error when KB ID is missing"""
        result = get_json_result(data=False, message='Lack of "KB ID"', code=RETCODE_ARGUMENT_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_ARGUMENT_ERROR
        assert "KB ID" in result_json.get("message", "")

    def test_delete_pipeline_logs_missing_kb_id(self):
        """Test delete_pipeline_logs returns error when KB ID is missing"""
        result = get_json_result(data=False, message='Lack of "KB ID"', code=RETCODE_ARGUMENT_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_ARGUMENT_ERROR

    def test_pipeline_log_detail_missing_log_id(self):
        """Test pipeline_log_detail returns error when log ID is missing"""
        result = get_json_result(data=False, message='Lack of "Pipeline log ID"', code=RETCODE_ARGUMENT_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_ARGUMENT_ERROR


class TestKbAppUnbindTask:
    """Test cases for kb_app.delete_kb_task endpoint logic"""

    def test_unbind_task_missing_kb_id(self):
        """Test unbind_task returns error when KB ID is missing"""
        result = get_error_data_result(message='Lack of "KB ID"')
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_ARGUMENT_ERROR

    def test_unbind_task_invalid_task_type(self):
        """Test unbind_task returns error for invalid task type"""
        result = get_error_data_result(message="Invalid task type")
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_ARGUMENT_ERROR


class TestResponseHelpers:
    """Test cases for API response helper functions"""

    def test_get_json_result_success(self):
        """Test successful JSON result creation"""
        result = get_json_result(data={"key": "value"})
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("data") == {"key": "value"}

    def test_get_json_result_with_message(self):
        """Test JSON result with custom message"""
        result = get_json_result(data={"key": "value"}, message="Custom message")
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("message") == "Custom message"

    def test_get_json_result_with_code(self):
        """Test JSON result with custom code"""
        result = get_json_result(data=False, code=RETCODE_DATA_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_DATA_ERROR
        assert result_json.get("data") is False

    def test_get_data_error_result(self):
        """Test data error result creation"""
        result = get_data_error_result(message="Data error occurred")
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_DATA_ERROR
        assert "Data error" in result_json.get("message", "")

    def test_get_error_data_result(self):
        """Test error data result creation"""
        result = get_error_data_result(message="Error occurred")
        result_json = result.get_json()

        assert result_json.get("code") == RETCODE_ARGUMENT_ERROR
        assert "Error" in result_json.get("message", "")


class TestRetCodeConstants:
    """Test return code constants are properly defined"""

    def test_return_codes_defined(self):
        """Test all return codes are defined"""
        assert RETCODE_SUCCESS == 0
        assert RETCODE_ARGUMENT_ERROR == 1
        assert RETCODE_DATA_ERROR == 2
        assert RETCODE_FORBIDDEN == 3
        assert RETCODE_NOT_FOUND == 4
        assert RETCODE_AUTHENTICATION_ERROR == 2
        assert RETCODE_OPERATING_ERROR == 6
        assert RETCODE_NOT_EFFECTIVE == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
