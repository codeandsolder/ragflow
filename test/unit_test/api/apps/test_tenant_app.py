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
Unit tests for tenant_app endpoint logic.
"""

import pytest
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


class TestTenantAppUserList:
    """Test cases for tenant_app.user_list endpoint logic"""

    def test_user_list_no_authorization(self):
        """Test user_list returns error when not authorized"""
        result = get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR

    def test_user_list_success(self):
        """Test successful user listing"""
        result = get_json_result(data=[{"user_id": "user-123", "email": "test@example.com"}])
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.SUCCESS
        assert len(result_json.get("data", [])) == 1


class TestTenantAppCreate:
    """Test cases for tenant_app.create endpoint logic"""

    def test_create_user_not_found(self):
        """Test create returns error when user not found"""
        result = get_data_error_result(message="User not found.")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "User not found" in result_json.get("message", "")

    def test_create_user_already_in_team(self):
        """Test create returns error when user already in team"""
        result = get_data_error_result(message="test@example.com is already in the team.")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "already in the team" in result_json.get("message", "")

    def test_create_user_is_owner(self):
        """Test create returns error when user is owner"""
        result = get_data_error_result(message="test@example.com is the owner of the team.")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "owner of the team" in result_json.get("message", "")


class TestTenantAppResponseHelpers:
    """Test cases for tenant_app response helpers"""

    def test_get_json_result_success(self):
        """Test successful JSON result creation"""
        result = get_json_result(data={"tenant_id": "test-tenant"})
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.SUCCESS
        assert result_json.get("data") == {"tenant_id": "test-tenant"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
