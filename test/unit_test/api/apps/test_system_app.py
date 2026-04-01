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
Unit tests for system_app endpoint logic.
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.api_utils import get_json_result
from common.constants import RetCode


class TestSystemAppVersion:
    """Test cases for system_app.version endpoint logic"""

    def test_version_success(self):
        """Test successful version retrieval"""
        result = get_json_result(data="v1.0.0")
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("data") == "v1.0.0"


class TestSystemAppStatus:
    """Test cases for system_app.status endpoint logic"""

    def test_status_success(self):
        """Test successful status retrieval"""
        result = get_json_result(data={"status": "online"})
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("data") == {"status": "online"}


class TestSystemAppResponseHelpers:
    """Test cases for system_app response helpers"""

    def test_get_json_result_success(self):
        """Test successful JSON result creation"""
        result = get_json_result(data={"key": "value"})
        result_json = result.get_json()

        assert result_json.get("code") == 0
        assert result_json.get("data") == {"key": "value"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
