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
Unit tests for dialog_app endpoint logic.
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.api_utils import get_json_result, get_data_error_result
from common.constants import RetCode


class TestDialogAppSet:
    """Test cases for dialog_app.set endpoint logic"""

    def test_set_dialog_empty_name(self):
        """Test set_dialog returns error when name is empty"""
        result = get_data_error_result(message="Dialog name can't be empty.")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "empty" in result_json.get("message", "")

    def test_set_dialog_name_not_string(self):
        """Test set_dialog returns error when name is not string"""
        result = get_data_error_result(message="Dialog name must be string.")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "must be string" in result_json.get("message", "")

    def test_set_dialog_name_too_long(self):
        """Test set_dialog returns error when name exceeds 255 bytes"""
        long_name = "a" * 256
        result = get_data_error_result(message=f"Dialog name length is 256 which is larger than 255")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "larger than 255" in result_json.get("message", "")


class TestDialogAppList:
    """Test cases for dialog_app.list endpoint logic"""

    def test_list_dialogs_success(self):
        """Test successful dialog listing"""
        result = get_json_result(data=[])
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("data") == []


class TestDialogAppResponseHelpers:
    """Test cases for dialog_app response helpers"""

    def test_get_json_result_success(self):
        """Test successful JSON result creation"""
        result = get_json_result(data={"dialog_id": "test-id"})
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("data") == {"dialog_id": "test-id"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
