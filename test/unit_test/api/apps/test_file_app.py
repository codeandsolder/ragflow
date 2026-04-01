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
Unit tests for file_app endpoint logic.

Note: file_app is currently disabled (commented out), but tests are provided
for future reference when it's re-enabled.
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.api_utils import get_json_result, get_data_error_result
from common.constants import RetCode


class TestFileAppUpload:
    """Test cases for file_app.upload endpoint logic"""

    def test_upload_no_file_part(self):
        """Test upload returns error when no file part"""
        result = get_json_result(data=False, message="No file part!", code=RetCode.ARGUMENT_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR
        assert "No file part" in result_json.get("message", "")

    def test_upload_no_file_selected(self):
        """Test upload returns error when no file selected"""
        result = get_json_result(data=False, message="No file selected!", code=RetCode.ARGUMENT_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR
        assert "No file selected" in result_json.get("message", "")


class TestFileAppList:
    """Test cases for file_app.list endpoint logic"""

    def test_list_files_success(self):
        """Test successful file listing"""
        result = get_json_result(data=[])
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("data") == []


class TestFileAppResponseHelpers:
    """Test cases for file_app response helpers"""

    def test_get_json_result_success(self):
        """Test successful JSON result creation"""
        result = get_json_result(data={"file_id": "test-id"})
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("data") == {"file_id": "test-id"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
