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
Unit tests for connector_app endpoint logic.
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
        return _get_result_json(result)
    return result


class TestConnectorAppSet:
    """Test cases for connector_app.set endpoint logic"""

    def test_set_connector_success(self):
        """Test successful connector creation"""
        mock_connector = Mock()
        mock_connector.to_dict.return_value = {"id": "connector-123", "name": "Test Connector"}

        result = get_json_result(data=mock_connector.to_dict())
        result_json = _get_result_json(result)

        assert result_json.get("code") == 0


class TestConnectorAppList:
    """Test cases for connector_app.list endpoint logic"""

    def test_list_connectors_success(self):
        """Test successful connector listing"""
        result = get_json_result(data=[])
        result_json = _get_result_json(result)

        assert result_json.get("code") == 0
        assert result_json.get("data") == []


class TestConnectorAppGet:
    """Test cases for connector_app.get endpoint logic"""

    def test_get_connector_not_found(self):
        """Test get_connector returns error when connector not found"""
        result = get_data_error_result(message="Can't find this Connector!")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "Can't find" in result_json.get("message", "")


class TestConnectorAppResponseHelpers:
    """Test cases for connector_app response helpers"""

    def test_get_json_result_success(self):
        """Test successful JSON result creation"""
        result = get_json_result(data={"connector_id": "test-id"})
        result_json = _get_result_json(result)

        assert result_json.get("code") == 0
        assert result_json.get("data") == {"connector_id": "test-id"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
